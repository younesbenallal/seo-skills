import type { NextConfig } from "next"
import path from "node:path"
import { fileURLToPath } from "node:url"

const currentDirectory = path.dirname(fileURLToPath(import.meta.url))

const nextConfig: NextConfig = {
  assetPrefix: "./",
  output: "export",
  outputFileTracingRoot: currentDirectory,
  trailingSlash: true,
}

export default nextConfig
