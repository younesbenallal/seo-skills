import path from "node:path"

import { AuditDashboard } from "@/src/components/audit-dashboard"
import { loadAuditDashboardDataFromFiles, loadAuditDashboardDataFromRunDirectory } from "@/src/lib/audit-data.server"

const defaultAuditPath = "/data/demo/brightdata-results.json"
const defaultTrackedPromptsPath = "/data/demo/tracked-prompts.json"

export default async function Page() {
  const loaded = process.env.AUDIT_RUNS_DIR
    ? await loadAuditDashboardDataFromRunDirectory(process.env.AUDIT_RUNS_DIR)
    : await loadAuditDashboardDataFromFiles({
    auditPath:
      process.env.AUDIT_DATA_PATH ||
      process.env.NEXT_PUBLIC_AUDIT_DATA_PATH ||
      defaultAuditPath,
    trackedPromptsPath:
      process.env.TRACKED_PROMPTS_PATH ||
      process.env.NEXT_PUBLIC_TRACKED_PROMPTS_PATH ||
      defaultTrackedPromptsPath,
    baseDir: path.join(process.cwd(), "public"),
    })

  if (process.env.AUDIT_RUNS_DIR && !loaded.ok) {
    throw new Error(loaded.error)
  }

  return <AuditDashboard loaded={loaded} />
}
