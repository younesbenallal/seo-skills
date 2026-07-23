import fs from "node:fs/promises"
import path from "node:path"

const outDir = path.resolve("out")

async function rewrite(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true })

  await Promise.all(
    entries.map(async (entry) => {
      const filePath = path.join(directory, entry.name)
      if (entry.isDirectory()) {
        await rewrite(filePath)
        return
      }

      if (
        !entry.name.endsWith(".html") &&
        !entry.name.endsWith(".js") &&
        !entry.name.endsWith(".css")
      ) {
        return
      }

      const source = await fs.readFile(filePath, "utf8")
      const rewritten = source
        .replaceAll('"/_next/', '"./_next/')
        .replaceAll("url(/_next/static/media/", "url(../media/")
      if (rewritten !== source) {
        await fs.writeFile(filePath, rewritten)
      }
    })
  )
}

await rewrite(outDir)
