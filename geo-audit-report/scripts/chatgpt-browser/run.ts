// Runs a list of prompts on chatgpt.com through a Chrome driven over CDP, then exports the
// matching Fanout Fox captures. Writes raw evidence only; normalize-chatgpt-browser.py builds results.json.
//
//   bun run.ts launch                                        # opens the dedicated Chrome profile
//   bun run.ts <prompts.txt> <run-dir> --workspace <name>    # writes <run-dir>/raw/answers.json + fanoutfox.json
//              [--concurrency 2]                             # waits while another collection runs
//   bun run.ts fanoutfox <run-dir>                           # re-exports the Fanout Fox captures of a run
//   bun run.ts citations <run-dir>                           # TEMPORARY: re-resolves cited pages of a run
//   bun run.ts conversations <run-dir>                       # re-saves raw/conversations/<id>.json of a run
//   bun run.ts workspaces                                    # lists Fanout Fox workspaces, the active one first
//   bun run.ts workspace <name>                              # makes a workspace active
//   bun run.ts workspace-create <name> [--domains a.com,b]   # creates a workspace (and makes it active)
//   bun run.ts move <workspace> <run-dir>                    # moves a run's captures to a workspace
//   bun run.ts move <workspace> --match "<prompt text>"      # moves captures whose prompt contains the text
import { chromium, type Page } from "playwright-core"
import { spawn } from "node:child_process"
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"
import { setTimeout as sleep } from "node:timers/promises"
import { parseArgs } from "node:util"

const PORT = 9333
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
const PROFILE = join(homedir(), ".chatgpt-runner-profile")
const LOCK = `${PROFILE}.lock`
const ANSWER_TIMEOUT = 5 * 60_000
const FANOUTFOX = "chrome-extension://efgemipiccaljhahdacjbbkcemelojlj/dashboard-v2/dist/index.html"

const { positionals, values } = parseArgs({
  allowPositionals: true,
  options: {
    concurrency: { type: "string", default: "2" },
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

// TEMPORARY workaround: remove once Fanout Fox resolves citations again.
// Fanout Fox marks a source as cited only through `content_references`, which current ChatGPT
// conversations leave empty: citations are inline `<Cite refs={["turn…search…"]}/>` markers instead.
// Until Fanout Fox handles that, map each marker to the search result carrying the same `ref_id`
// in the conversation JSON the page loads. Unresolved markers keep `url: null`.
type Citation = { code: string; url: string | null; title: string | null }
function citationsIn(raw: string) {
  const results = new Map<string, { url: string; title: string | null }>()
  const walk = (node: unknown) => {
    if (Array.isArray(node)) return node.forEach(walk)
    if (!node || typeof node !== "object") return
    const { ref_id: ref, url, title } = node as Record<string, unknown>
    if (ref && typeof ref === "object" && typeof url === "string") {
      const { turn_index, ref_type, ref_index } = ref as Record<string, unknown>
      results.set(`turn${turn_index}${ref_type}${ref_index}`, { url, title: typeof title === "string" ? title : null })
    }
    Object.values(node).forEach(walk)
  }
  walk(JSON.parse(raw))
  const markers = [...raw.matchAll(/<Cite refs=\{\[(.*?)\]\}/g)].map((m) => m[1] ?? "")
  const codes = [...new Set(markers.flatMap((m) => m.match(/turn\d+[a-z_]+\d+/g) ?? []))]
  return codes.map((code): Citation => ({ code, url: results.get(code)?.url ?? null, title: results.get(code)?.title ?? null }))
}

// ChatGPT's own JSON of a conversation, as the page loads it. It holds what Fanout Fox often misses
// (it skips most background tabs): the queries sent to search, every retrieved result and the model.
// Saved as raw/conversations/<id>.json; normalize-chatgpt-browser.py reads it when a capture is missing.
// Logged-out conversations (/uc/) cannot be reopened, so they have none.
async function saveConversation(page: Page, url: string, runDir: string) {
  const id = url.split("?")[0]!.replace(/\/$/, "").split("/").pop()!
  if (!url.includes("/c/")) throw new Error("not a saved conversation")
  let raw = ""
  for (let attempt = 1; attempt <= 3 && !raw; attempt++) {
    const response = page.waitForResponse(
      (r) => r.url().includes(`/backend-api/conversation/${id}`) || r.url().includes(`/backend-api/conversations/${id}`),
      { timeout: 30_000 },
    )
    await page.goto(url, { waitUntil: "domcontentloaded" })
    const text = await response.then((r) => (r.ok() ? r.text() : "")).catch(() => "")
    try {
      JSON.parse(text)
      raw = text
    } catch {
      if (attempt < 3) await page.waitForTimeout(5_000 * attempt)
    }
  }
  if (!raw) throw new Error("conversation JSON unavailable")
  mkdirSync(join(runDir, "raw", "conversations"), { recursive: true })
  writeFileSync(join(runDir, "raw", "conversations", `${id}.json`), raw)
  return raw
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
} else if (command === "citations" || command === "conversations") {
  const dir = rest[0] ?? ""
  const file = join(dir, "raw", "answers.json")
  const previous: { url?: string; citations?: Citation[] | null }[] = JSON.parse(readFileSync(file, "utf8"))
  const page = await backgroundPage()
  for (const answer of previous) {
    if (!answer.url) continue
    const raw = await saveConversation(page, answer.url, dir).catch((error) => {
      console.error(`${answer.url} → ${error.message}`)
      return null
    })
    if (command === "citations") answer.citations = raw === null ? null : citationsIn(raw)
    if (raw !== null) console.log(`${answer.url} → ${command === "citations" ? `${answer.citations?.length} citations` : "saved"}`)
  }
  await page.close()
  if (command === "citations") writeFileSync(file, JSON.stringify(previous, null, 2))
}
if (["workspaces", "workspace", "workspace-create", "move", "fanoutfox", "citations", "conversations"].includes(command)) {
  await browser.close()
  process.exit(0)
}

const [promptsFile = "", runDir = ""] = positionals
if (!promptsFile || !runDir || !values.workspace) {
  console.error("Usage: bun run.ts <prompts.txt> <run-dir> --workspace <name> [--concurrency 2]. See the header of run.ts for other commands.")
  process.exit(1)
}

// One collection at a time: parallel runs share this Chrome, its ChatGPT account and the active
// Fanout Fox workspace, so they overload the machine, time out and file captures in the wrong place.
type LockHolder = { pid: number; runDir: string; startedAt: string }
const lockHolder = (): LockHolder | null => {
  try {
    return JSON.parse(readFileSync(LOCK, "utf8"))
  } catch {
    return null
  }
}
const isAlive = (pid: number) => {
  try {
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

let waiting = false
while (true) {
  try {
    writeFileSync(LOCK, JSON.stringify({ pid: process.pid, runDir, startedAt: new Date().toISOString() }), { flag: "wx" })
    break
  } catch {}
  const holder = lockHolder()
  // A lock whose process is gone was left by a crashed or killed run.
  if (holder && !isAlive(holder.pid)) {
    rmSync(LOCK, { force: true })
    continue
  }
  if (holder && !waiting) {
    console.log(`Another collection is running (pid ${holder.pid}, ${holder.runDir}, since ${holder.startedAt}). Waiting for it to finish…`)
    waiting = true
  }
  await sleep(holder ? 15_000 : 500)
}
process.on("exit", () => {
  if (lockHolder()?.pid === process.pid) rmSync(LOCK, { force: true })
})
for (const signal of ["SIGINT", "SIGTERM", "SIGHUP"]) process.on(signal, () => process.exit(1))

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
  const raw = await saveConversation(page, page.url(), runDir).catch(() => null)
  const citations = raw === null ? null : citationsIn(raw)
  return { url: page.url(), text, links, citations }
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
      console.log(`[${++done}/${prompts.length}] ${prompt}\n  → ${res.text.length} chars, ${res.citations?.length ?? "?"} citations`)
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
