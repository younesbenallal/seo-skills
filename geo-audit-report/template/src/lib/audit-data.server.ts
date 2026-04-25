import fs from "node:fs/promises"
import path from "node:path"

import {
  createDashboardLoadSuccess,
  type AuditFileRecord,
  type DashboardLoadResult,
  type TrackedPromptsRecord,
} from "@/src/lib/audit-data"

export async function loadAuditDashboardDataFromFiles({
  auditPath,
  trackedPromptsPath,
  baseDir,
}: {
  auditPath: string
  trackedPromptsPath: string
  baseDir: string
}): Promise<DashboardLoadResult> {
  try {
    const [auditRaw, trackedPromptsRaw] = await Promise.all([
      fs.readFile(resolveDataPath(baseDir, auditPath), "utf8"),
      fs.readFile(resolveDataPath(baseDir, trackedPromptsPath), "utf8"),
    ])

    return createDashboardLoadSuccess(
      JSON.parse(auditRaw) as AuditFileRecord,
      JSON.parse(trackedPromptsRaw) as TrackedPromptsRecord
    )
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown error",
    }
  }
}

function resolveDataPath(baseDir: string, targetPath: string) {
  const relativePath = targetPath.replace(/^\/+/, "")
  return path.join(baseDir, relativePath)
}
