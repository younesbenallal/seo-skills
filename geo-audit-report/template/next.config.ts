import type { NextConfig } from "next"
import path from "node:path"
import { fileURLToPath } from "node:url"

const currentDirectory = path.dirname(fileURLToPath(import.meta.url))

const nextConfig: NextConfig = {
  output: "export",
  outputFileTracingRoot: currentDirectory,
}

export default nextConfig
