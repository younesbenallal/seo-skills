// Runs a list of prompts on chatgpt.com through a Chrome driven over CDP, then exports the
// matching Fanout Fox captures. Writes raw evidence only; normalize-chatgpt-browser.py builds results.json.
//
//   bun run.ts launch                                        # opens the dedicated Chrome profile
//   bun run.ts <prompts.txt> <run-dir> --workspace <name>    # writes <run-dir>/raw/answers.json + fanoutfox.json
//              [--concurrency 3]
//   bun run.ts fanoutfox <run-dir>                           # re-exports the Fanout Fox captures of a run
//   bun run.ts workspaces                                    # lists Fanout Fox workspaces, the active one first
//   bun run.ts workspace <name>                              # makes a workspace active
//   bun run.ts workspace-create <name> [--domains a.com,b]   # creates a workspace (and makes it active)
//   bun run.ts move <workspace> <run-dir>                    # moves a run's captures to a workspace
//   bun run.ts move <workspace> --match "<prompt text>"      # moves captures whose prompt contains the text
import { chromium, type Page } from "playwright-core"
import { spawn } from "node:child_process"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"
import { parseArgs } from "node:util"

const PORT = 9333
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
const PROFILE = join(homedir(), ".chatgpt-runner-profile")
const ANSWER_TIMEOUT = 5 * 60_000
const FANOUTFOX = "chrome-extension://efgemipiccaljhahdacjbbkcemelojlj/dashboard-v2/dist/index.html"

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: {
    concurrency: { type: "string", default: "3" },
    workspace: { type: "string" },
    domains: { type: "string", default: "" },
    match: { type: "string" },
  },
})

if (positionals[0] === "launch") {
  // Background tabs keep full speed, so parallel answers are not throttled while the window is hidden.
  const flags = ["--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding"]
  spawn(CHROME, [`--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`, ...flags, "https://chatgpt.com/"], {
    detached: true,
    stdio: "ignore",
  }).unref()
  console.log(`Chrome launched on port ${PORT} with profile ${PROFILE}. Log in to ChatGPT if needed.`)
  process.exit(0)
}

const browser = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`).catch(() => {
  console.error(`No Chrome on port ${PORT}. Run: bun run.ts launch`)
  process.exit(1)
})
const context = browser.contexts()[0]!

// Playwright's newPage() and bringToFront() raise the Chrome window above the user's apps on macOS.
// Chrome's own command opens the tab in the background, and focus emulation lets it type unfocused.
async function targetIdOf(page: Page) {
  const session = await context.newCDPSession(page)
  const { targetInfo } = await session.send("Target.getTargetInfo")
  await session.detach()
  return targetInfo.targetId
}

async function backgroundPage() {
  const cdp = await browser.newBrowserCDPSession()
  const created = cdp.send("Target.createTarget", { url: "about:blank", background: true })
  // Other runs may share this Chrome, so pick our tab by its target id, not the next tab that opens.
  const page = await context.waitForEvent("page", {
    predicate: async (p) => (await targetIdOf(p)) === (await created).targetId,
  })
  await cdp.detach()
  const session = await context.newCDPSession(page)
  await session.send("Emulation.setFocusEmulationEnabled", { enabled: true })
  return page
}

type Workspace = { id: string; name: string; ownDomains: string[]; captures: number }

// Runs code against Fanout Fox's own store module inside an extension page, so the extension's
// workspace logic stays the source of truth. `s` is the module; the body must return JSON data.
async function fanoutFox<T>(body: string) {
  const page = await backgroundPage()
  try {
    await page.goto(FANOUTFOX)
    return await page.evaluate<T>(`(async () => {
      const s = await import(chrome.runtime.getURL("src/core/store.js"))
      ${body}
    })()`)
  } finally {
    await page.close()
  }
}

const listWorkspaces = () =>
  fanoutFox<{ activeId: string; workspaces: Workspace[] }>(`
    const { workspaces, activeId } = await s.ensureWorkspaces()
    const captures = await s.listCaptures()
    return {
      activeId,
      workspaces: workspaces.map((w) => ({
        id: w.id, name: w.name, ownDomains: w.ownDomains || [],
        captures: captures.filter((c) => s.inWorkspace(c, w.id)).length,
      })),
    }
  `)

async function findWorkspace(nameOrId: string) {
  const { workspaces } = await listWorkspaces()
  const found = workspaces.find((w) => w.id === nameOrId || w.name.toLowerCase() === nameOrId.trim().toLowerCase())
  if (!found) throw new Error(`No Fanout Fox workspace "${nameOrId}". Existing: ${workspaces.map((w) => w.name).join(", ")}`)
  return found
}

async function activateWorkspace(nameOrId: string) {
  const target = await findWorkspace(nameOrId)
  await fanoutFox(`await s.setActiveWorkspace(${JSON.stringify(target.id)}); return null`)
  const { activeId } = await listWorkspaces()
  if (activeId !== target.id) throw new Error(`Fanout Fox did not switch to "${target.name}"`)
  console.log(`Fanout Fox workspace: ${target.name} (${target.id})`)
  return target
}

// Moves the captures selected by `filter` (a JS expression on capture `c`) and returns how many moved.
const moveCaptures = (workspaceId: string, filter: string) =>
  fanoutFox<number>(`
    const moving = (await s.listCaptures()).filter((c) => !s.inWorkspace(c, ${JSON.stringify(workspaceId)}) && (${filter}))
    for (const c of moving) await s.moveCaptureToWorkspace(c.id, ${JSON.stringify(workspaceId)})
    return moving.length
  `)

const convKeys = (urls: string[]) => urls.map((u) => `chatgpt:${u.split("/").pop()}`)
const runUrls = (runDir: string): string[] =>
  JSON.parse(readFileSync(join(runDir, "raw", "answers.json"), "utf8")).flatMap((r: { url?: string }) => (r.url ? [r.url] : []))

// Fanout Fox keeps its parsed captures (fan-out searches, all sources, model...) in the extension storage.
async function exportFanoutFox(runDir: string, urls: string[]) {
  const ids = new Set(convKeys(urls))
  const captures = await fanoutFox<{ convKey: string }[]>("return s.listCaptures()")
  const own = captures.filter((c) => ids.has(c.convKey))
  writeFileSync(join(runDir, "raw", "fanoutfox.json"), JSON.stringify(own, null, 2))
  console.log(`Fanout Fox: ${own.length}/${ids.size} captures → ${join(runDir, "raw", "fanoutfox.json")}`)
}

const [command = "", ...rest] = positionals

if (command === "workspaces") {
  const { activeId, workspaces } = await listWorkspaces()
  for (const w of workspaces.sort((a, b) => Number(b.id === activeId) - Number(a.id === activeId)))
    console.log(`${w.id === activeId ? "* " : "  "}${w.name}  (${w.id}, ${w.captures} captures, domains: ${w.ownDomains.join(", ") || "none"})`)
} else if (command === "workspace") {
  await activateWorkspace(rest.join(" "))
} else if (command === "workspace-create") {
  const name = rest.join(" ")
  const domains = values.domains.split(",").map((d) => d.trim()).filter(Boolean)
  await fanoutFox(`
    const ws = await s.createWorkspace(${JSON.stringify(name)})
    await s.saveSettings({ ...(await s.loadSettings()), workspaceId: ws.id, ownDomains: ${JSON.stringify(domains)} })
    return null
  `)
  await activateWorkspace(name)
} else if (command === "move") {
  const target = await findWorkspace(rest[0] ?? "")
  const filter = values.match
    ? `(c.capture?.query || "").toLowerCase().includes(${JSON.stringify(values.match.toLowerCase())})`
    : `${JSON.stringify(convKeys(runUrls(rest[1] ?? "")))}.includes(c.convKey)`
  console.log(`Moved ${await moveCaptures(target.id, filter)} captures to ${target.name}`)
} else if (command === "fanoutfox") {
  await exportFanoutFox(rest[0] ?? "", runUrls(rest[0] ?? ""))
}
if (["workspaces", "workspace", "workspace-create", "move", "fanoutfox"].includes(command)) {
  await browser.close()
  process.exit(0)
}

const [promptsFile = "", runDir = ""] = positionals
if (!promptsFile || !runDir || !values.workspace) {
  console.error("Usage: bun run.ts <prompts.txt> <run-dir> --workspace <name> [--concurrency 3]. See the header of run.ts for other commands.")
  process.exit(1)
}
// Every capture is filed under the active workspace, so pin it before sending anything.
const workspace = await activateWorkspace(values.workspace)

const prompts = readFileSync(promptsFile, "utf8").split("\n").map((l) => l.trim()).filter(Boolean)

// Logged-in and logged-out ChatGPT ship different UIs, so each selector covers both.
const INPUT = '[contenteditable="true"][role="textbox"], textarea[name="prompt"]:visible'
const SEND = '[data-composer-submit]:visible, button[aria-label="Send"]'
const ANSWER = '[data-markdown-text-style="assistant-message"], [data-message-role="assistant"]'
const COMPLETE = '[data-talvt-turn-state="complete"], [data-message-role="assistant"][data-message-complete]'

async function ask(page: Page, prompt: string) {
  await page.goto("https://chatgpt.com/", { waitUntil: "domcontentloaded" })
  const input = page.locator(INPUT).first()
  await input.waitFor({ timeout: 30_000 })
  // ChatGPT restores unsent drafts shortly after load; let that happen before we clear the box.
  await page.waitForTimeout(1_500)
  await input.click()
  await page.keyboard.press("ControlOrMeta+A")
  await page.keyboard.press("Delete")
  await page.keyboard.insertText(prompt)
  const typed = (await input.innerText().catch(() => "")) || (await input.inputValue().catch(() => ""))
  if (typed.trim() !== prompt) throw new Error(`Composer holds unexpected text: ${typed.slice(0, 200)}`)
  await page.locator(SEND).first().click()

  const answer = page.locator(ANSWER).last()
  await answer.waitFor({ timeout: 60_000 })
  await page.locator(COMPLETE).last().waitFor({ timeout: ANSWER_TIMEOUT })

  const sent = (await page.locator("[data-user-message-bubble]").last().innerText()).trim()
  if (sent !== prompt) throw new Error(`Sent message differs from the prompt: ${sent.slice(0, 200)}`)

  const text = await answer.innerText()
  const links = await answer.locator("a[href]").evaluateAll((as) =>
    as.map((a) => ({ text: a.textContent?.trim() ?? "", href: (a as HTMLAnchorElement).href })),
  )
  return { url: page.url(), text, links }
}

mkdirSync(join(runDir, "raw"), { recursive: true })
type Answer = { prompt: string; at: string } & (Awaited<ReturnType<typeof ask>> | { error: string })
const answers: Answer[] = []
let next = 0
let done = 0
const save = () => writeFileSync(join(runDir, "raw", "answers.json"), JSON.stringify(answers.filter(Boolean), null, 2))

// Each worker owns a tab and pulls the next prompt until the list is empty.
async function worker() {
  const page = await backgroundPage()
  while (next < prompts.length) {
    const i = next++
    const prompt = prompts[i]!
    try {
      const res = await ask(page, prompt)
      answers[i] = { prompt, ...res, at: new Date().toISOString() }
      console.log(`[${++done}/${prompts.length}] ${prompt}\n  → ${res.text.length} chars, ${res.links.length} links`)
    } catch (error) {
      answers[i] = { prompt, error: String(error), at: new Date().toISOString() }
      console.error(`[${++done}/${prompts.length}] ${prompt}\n  ✗ ${error}`)
      await page.screenshot({ path: join(runDir, "raw", `error-${i + 1}.png`) }).catch(() => {})
    }
    save()
    // Space out prompts a bit so the session doesn't look like a bot burst.
    await page.waitForTimeout(3_000 + Math.random() * 4_000)
  }
  await page.close()
}

const concurrency = Math.max(1, Number(values.concurrency))
await Promise.all(Array.from({ length: Math.min(concurrency, prompts.length) }, worker))
save()
const urls = answers.flatMap((r) => ("url" in r ? [r.url] : []))
// Someone may switch workspace in the UI mid-run; bring any stray capture back.
const strays = await moveCaptures(workspace.id, `${JSON.stringify(convKeys(urls))}.includes(c.convKey)`)
if (strays) console.log(`Moved ${strays} captures filed elsewhere back to ${workspace.name}`)
await exportFanoutFox(runDir, urls)

await browser.close() // only disconnects from CDP, Chrome stays open
console.log(`Done → ${runDir}/raw`)
