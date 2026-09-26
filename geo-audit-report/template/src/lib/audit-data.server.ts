import fs from "node:fs/promises"
import path from "node:path"

import {
  createDashboardLoadSuccess,
  type AuditFileRecord,
  type DashboardLoadResult,
  type ReportAnalysis,
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

export async function loadAuditDashboardDataFromRunDirectory(runDir: string): Promise<DashboardLoadResult> {
  try {
    const entries = await fs.readdir(runDir, { withFileTypes: true })
    const files = entries
      .filter((entry) => entry.isDirectory() && /^\d{4}-\d{2}-\d{2}(?:-\d{6}(?:-\d+)?)?$/.test(entry.name))
      .sort((left, right) => left.name.localeCompare(right.name))
      .map((entry) => path.join(runDir, entry.name, "results.json"))
    const runs: AuditFileRecord[] = []

    for (const file of files) {
      try {
        const parsed: unknown = JSON.parse(await fs.readFile(file, "utf8"))
        if (!isAuditFileRecord(parsed)) throw new Error(`Invalid audit data: ${file}`)
        runs.push(parsed)
      } catch (error) {
        if (error instanceof Error && "code" in error && error.code === "ENOENT") continue
        throw error
      }
    }

    if (!runs.length) throw new Error(`No completed results.json found in ${runDir}`)
    runs.sort((left, right) => left.run_at.localeCompare(right.run_at))
    const domains = new Set(runs.map((run) => JSON.stringify([...run.target_domains].sort())))
    if (domains.size > 1) throw new Error("Run directory contains multiple target domains")

    let trackedPrompts: TrackedPromptsRecord = { tracked_prompts: [] }
    for (const file of [
      path.join(runDir, "tracked-prompts.json"),
      path.join(path.dirname(files.at(-1) ?? runDir), "tracked-prompts.json"),
    ]) {
      try {
        const parsed: unknown = JSON.parse(await fs.readFile(file, "utf8"))
        if (isTrackedPromptsRecord(parsed)) {
          trackedPrompts = parsed
          break
        }
      } catch (error) {
        if (error instanceof Error && "code" in error && error.code === "ENOENT") continue
        throw error
      }
    }

    const latest = runs.at(-1)
    if (!latest) throw new Error(`No completed results.json found in ${runDir}`)
    const analysisRaw: unknown = JSON.parse(await fs.readFile(path.join(runDir, "report-analysis.json"), "utf8"))
    if (!isReportAnalysis(analysisRaw) || analysisRaw.through_run_at !== latest.run_at) {
      throw new Error(`report-analysis.json must cover the latest run (${latest.run_at}) and contain 3–6 evidenced recommendations`)
    }
    return createDashboardLoadSuccess(latest, trackedPrompts, runs, analysisRaw)
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : "Unknown error" }
  }
}

function isAuditFileRecord(value: unknown): value is AuditFileRecord {
  if (!value || typeof value !== "object") return false
  if (!("run_at" in value && typeof value.run_at === "string")) return false
  if (!("target_domains" in value && Array.isArray(value.target_domains) && value.target_domains.length > 0 && value.target_domains.every((item) => typeof item === "string"))) return false
  if (!("snapshots" in value && Array.isArray(value.snapshots))) return false
  const responses = "responses" in value && Array.isArray(value.responses)
    ? value.responses
    : "results" in value && Array.isArray(value.results) ? value.results : null
  return !!responses && responses.every((response) =>
    !!response && typeof response === "object" &&
    "prompt" in response && typeof response.prompt === "string" &&
    "chatbot" in response && typeof response.chatbot === "string"
  )
}

function isTrackedPromptsRecord(value: unknown): value is TrackedPromptsRecord {
  return !!value && typeof value === "object" && "tracked_prompts" in value && Array.isArray(value.tracked_prompts)
}

function isReportAnalysis(value: unknown): value is ReportAnalysis {
  if (!value || typeof value !== "object") return false
  if (!("through_run_at" in value && typeof value.through_run_at === "string")) return false
  if (!("overview" in value && typeof value.overview === "string" && value.overview.trim())) return false
  if (!("comparison_note" in value && typeof value.comparison_note === "string" && value.comparison_note.trim())) return false
  if (!("findings" in value && Array.isArray(value.findings) && value.findings.length > 0 && value.findings.every((item) => typeof item === "string" && item.trim()))) return false
  if (!("recommendations" in value && Array.isArray(value.recommendations) && value.recommendations.length >= 3 && value.recommendations.length <= 6)) return false
  return value.recommendations.every((item) =>
    !!item && typeof item === "object" &&
    typeof item.title === "string" && item.title.trim() &&
    typeof item.summary === "string" && item.summary.trim() &&
    typeof item.priority === "string" && item.priority.trim() &&
    typeof item.evidence === "string" && item.evidence.trim()
  )
}

function resolveDataPath(baseDir: string, targetPath: string) {
  const relativePath = targetPath.replace(/^\/+/, "")
  return path.join(baseDir, relativePath)
}
