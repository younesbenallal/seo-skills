import path from "node:path"

import { AuditDashboard } from "@/src/components/audit-dashboard"
import { loadAuditDashboardDataFromFiles } from "@/src/lib/audit-data.server"

const defaultAuditPath = "/data/demo/brightdata-results.json"
const defaultTrackedPromptsPath = "/data/demo/tracked-prompts.json"

export default async function Page() {
  const loaded = await loadAuditDashboardDataFromFiles({
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

  return <AuditDashboard loaded={loaded} />
}
