type AuditSource = {
  title?: string | null
  url?: string | null
  domain?: string | null
  type?: string | null
}

type AuditResponse = {
  chatbot: string
  model?: string | null
  prompt: string
  captured_at?: string
  answer_text_markdown?: string
  mentions?: number
  cited?: boolean
  first_citation_rank?: number | null
  citations_count?: number
  fan_out_queries?: string[]
  fan_out_count?: number
  used_web_search?: boolean
  sources_count?: number
  ugc_sources_count?: number
  youtube_sources_count?: number
  competitor_domains?: string[]
  brands_mentioned?: string[]
  sources?: AuditSource[]
}

export type SourceRecord = {
  title: string
  url: string
  domain: string
  type: string
}

export type ResponseRecord = {
  chatbot: string
  model: string
  prompt: string
  captured_at: string
  answer_text_markdown: string
  mentions: number
  cited: boolean
  first_citation_rank: number | null
  citations_count: number
  fan_out_queries: string[]
  fan_out_count: number
  used_web_search: boolean
  sources_count: number
  ugc_sources_count: number
  youtube_sources_count: number
  competitor_domains: string[]
  brands_mentioned: string[]
  sources: SourceRecord[]
}

type ManualRecommendation = {
  title: string
  summary: string
  priority: string
  owner: string
}

type AuditFile = {
  schema_version?: string
  run_at: string
  check_url: string
  target_domains: string[]
  brand_terms: string[]
  snapshots: Array<{ chatbot: string; status: string }>
  manual_recommendations?: ManualRecommendation[]
  responses?: AuditResponse[]
  results?: AuditResponse[]
}

type TrackedPromptHistory = {
  date: string
  visibility: number
  prompt_count?: number
  cited_count?: number
}

type TrackedPrompt = {
  prompt: string
  first_tracked_at?: string
  last_tracked_at?: string
  status?: string
  notes?: string
  history?: TrackedPromptHistory[]
}

type TrackedPromptsFile = {
  tracked_prompts: TrackedPrompt[]
}

type SuccessfulLoad = {
  ok: true
  audit: AuditFile
  trackedPrompts: TrackedPromptsFile
}

type FailedLoad = {
  ok: false
  error: string
}

export type PromptGroup = {
  prompt: string
  responses: ResponseRecord[]
  visibility: number
  citations: number
  averageRank: number | null
  models: string[]
}

export type DomainGroup = {
  domain: string
  responsesCount: number
  uniquePages: number
  pages: Array<{
    title: string
    url: string
    responseCount: number
  }>
}

function safeArray<T>(value: T[] | undefined | null) {
  return Array.isArray(value) ? value : []
}

function normalizeSource(source: AuditSource): SourceRecord {
  return {
    title: source.title ?? "",
    url: source.url ?? "",
    domain: normalizeDomain(source.domain ?? source.url ?? ""),
    type: source.type ?? "web",
  }
}

function normalizeResponse(response: AuditResponse): ResponseRecord {
  const normalizedSources = safeArray(response.sources).map(normalizeSource)
  return {
    chatbot: response.chatbot,
    model: response.model || response.chatbot,
    prompt: response.prompt,
    captured_at: response.captured_at || "",
    answer_text_markdown: response.answer_text_markdown || "",
    mentions: response.mentions || 0,
    cited: Boolean(response.cited),
    first_citation_rank: response.first_citation_rank ?? null,
    citations_count: response.citations_count ?? normalizedSources.length,
    fan_out_queries: safeArray(response.fan_out_queries).filter(Boolean),
    fan_out_count:
      response.fan_out_count ?? safeArray(response.fan_out_queries).length,
    used_web_search: Boolean(response.used_web_search),
    sources_count: response.sources_count ?? normalizedSources.length,
    ugc_sources_count: response.ugc_sources_count ?? 0,
    youtube_sources_count: response.youtube_sources_count ?? 0,
    competitor_domains: safeArray(response.competitor_domains).filter(Boolean),
    brands_mentioned: safeArray(response.brands_mentioned).filter(Boolean),
    sources: normalizedSources,
  }
}

function normalizeAudit(audit: AuditFile): AuditFile {
  const rawResponses = safeArray(audit.responses).length
    ? safeArray(audit.responses)
    : safeArray(audit.results)

  return {
    schema_version: audit.schema_version || "geo-audit-v1",
    run_at: audit.run_at,
    check_url: audit.check_url,
    target_domains: safeArray(audit.target_domains),
    brand_terms: safeArray(audit.brand_terms),
    snapshots: safeArray(audit.snapshots),
    manual_recommendations: safeArray(audit.manual_recommendations),
    responses: rawResponses.map(normalizeResponse),
    results: rawResponses.map(normalizeResponse),
  }
}

async function fetchJson<T>(path: string) {
  const response = await fetch(path)

  if (!response.ok) {
    throw new Error(`Unable to load ${path} (${response.status})`)
  }

  return (await response.json()) as T
}

export async function loadAuditDashboardData(): Promise<
  SuccessfulLoad | FailedLoad
> {
  const auditPath =
    import.meta.env.VITE_AUDIT_DATA_PATH || "/data/demo/brightdata-results.json"
  const trackedPromptsPath =
    import.meta.env.VITE_TRACKED_PROMPTS_PATH ||
    "/data/demo/tracked-prompts.json"

  try {
    const [audit, trackedPrompts] = await Promise.all([
      fetchJson<AuditFile>(auditPath),
      fetchJson<TrackedPromptsFile>(trackedPromptsPath),
    ])

    return {
      ok: true,
      audit: normalizeAudit(audit),
      trackedPrompts: {
        tracked_prompts: safeArray(trackedPrompts.tracked_prompts),
      },
    }
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown error",
    }
  }
}

function mean(values: number[]) {
  if (values.length === 0) {
    return null
  }

  return Math.round(
    values.reduce((sum, value) => sum + value, 0) / values.length
  )
}

function percentage(part: number, total: number) {
  if (total === 0) {
    return 0
  }

  return Math.round((part / total) * 100)
}

function groupByPrompt(responses: ResponseRecord[]) {
  const promptMap = new Map<string, ResponseRecord[]>()

  for (const response of responses) {
    const existing = promptMap.get(response.prompt) || []
    existing.push(response)
    promptMap.set(response.prompt, existing)
  }

  return [...promptMap.entries()].map(([prompt, promptResponses]) => ({
    prompt,
    responses: promptResponses,
    visibility: percentage(
      promptResponses.filter((response) => response.cited).length,
      promptResponses.length
    ),
    citations: promptResponses.reduce(
      (total, response) => total + response.citations_count,
      0
    ),
    averageRank: mean(
      promptResponses
        .map((response) => response.first_citation_rank)
        .filter((rank): rank is number => rank !== null)
    ),
    models: [
      ...new Set(
        promptResponses.map((response) => response.model || response.chatbot)
      ),
    ],
  }))
}

function buildDomainGroups(responses: ResponseRecord[]) {
  const groups = new Map<
    string,
    {
      responseIds: Set<string>
      pages: Map<
        string,
        { title: string; url: string; responseIds: Set<string> }
      >
    }
  >()

  for (const response of responses) {
    for (const source of response.sources) {
      if (!source.url || !source.domain) {
        continue
      }

      const responseId = `${response.chatbot}:${response.prompt}`
      const domainEntry = groups.get(source.domain) || {
        responseIds: new Set<string>(),
        pages: new Map<
          string,
          { title: string; url: string; responseIds: Set<string> }
        >(),
      }

      domainEntry.responseIds.add(responseId)

      const existingPage = domainEntry.pages.get(source.url) || {
        title: source.title || source.url,
        url: source.url,
        responseIds: new Set<string>(),
      }
      existingPage.responseIds.add(responseId)
      domainEntry.pages.set(source.url, existingPage)
      groups.set(source.domain, domainEntry)
    }
  }

  return [...groups.entries()]
    .map(([domain, entry]) => ({
      domain,
      responsesCount: entry.responseIds.size,
      uniquePages: entry.pages.size,
      pages: [...entry.pages.values()]
        .map((page) => ({
          title: page.title,
          url: page.url,
          responseCount: page.responseIds.size,
        }))
        .sort((left, right) => right.responseCount - left.responseCount),
    }))
    .sort((left, right) => right.responsesCount - left.responsesCount)
}

function buildTimeline(trackedPrompts: TrackedPromptsFile) {
  const points = new Map<
    string,
    { totalVisibility: number; promptCount: number }
  >()

  for (const prompt of trackedPrompts.tracked_prompts) {
    for (const point of safeArray(prompt.history)) {
      const existing = points.get(point.date) || {
        totalVisibility: 0,
        promptCount: 0,
      }
      existing.totalVisibility += point.visibility
      existing.promptCount += 1
      points.set(point.date, existing)
    }
  }

  return [...points.entries()]
    .map(([date, point]) => ({
      date,
      visibility: Math.round(point.totalVisibility / point.promptCount),
      promptCount: point.promptCount,
    }))
    .sort((left, right) => left.date.localeCompare(right.date))
}

export function buildAuditViewModel(
  audit: AuditFile,
  trackedPrompts: TrackedPromptsFile
) {
  const responses = safeArray(audit.responses).map(normalizeResponse)
  const citedResponses = responses.filter((response) => response.cited)
  const mentionedResponses = responses.filter(
    (response) => response.mentions > 0
  )
  const domainGroups = buildDomainGroups(responses)
  const topDomains = domainGroups.map((group) => ({
    label: group.domain,
    count: group.uniquePages,
    share: percentage(
      group.uniquePages,
      Math.max(domainGroups[0]?.uniquePages || 1, 1)
    ),
  }))
  const competitorMentionMap = new Map<string, number>()

  for (const response of responses) {
    for (const competitor of response.competitor_domains) {
      competitorMentionMap.set(
        competitor,
        (competitorMentionMap.get(competitor) || 0) + 1
      )
    }
  }

  const maxCompetitorCount = Math.max(...competitorMentionMap.values(), 1)
  const competitorMentions = [...competitorMentionMap.entries()].map(
    ([label, count]) => ({
      label,
      count,
      share: percentage(count, maxCompetitorCount),
    })
  )

  const chatbotMap = new Map<
    string,
    {
      total: number
      cited: number
      citations: number
      ranks: number[]
    }
  >()

  for (const response of responses) {
    const chatbot = chatbotMap.get(response.chatbot) || {
      total: 0,
      cited: 0,
      citations: 0,
      ranks: [],
    }
    chatbot.total += 1
    chatbot.cited += response.cited ? 1 : 0
    chatbot.citations += response.citations_count
    if (response.first_citation_rank !== null) {
      chatbot.ranks.push(response.first_citation_rank)
    }
    chatbotMap.set(response.chatbot, chatbot)
  }

  const chatbotSummaries = [...chatbotMap.entries()].map(
    ([label, chatbot]) => ({
      label,
      visibility: percentage(chatbot.cited, chatbot.total),
      citationCount: chatbot.citations,
      averageRank: mean(chatbot.ranks),
    })
  )

  return {
    audit,
    trackedPrompts,
    responses,
    brandName: audit.brand_terms[0] || audit.target_domains[0] || "Brand",
    mentionRate: percentage(mentionedResponses.length, responses.length),
    citationRate: percentage(citedResponses.length, responses.length),
    averageRank: mean(
      citedResponses
        .map((response) => response.first_citation_rank)
        .filter((rank): rank is number => rank !== null)
    ),
    totalSources: new Set(
      responses.flatMap((response) =>
        response.sources.map((source) => source.url).filter(Boolean)
      )
    ).size,
    responsesWithSources: responses.filter(
      (response) => response.sources.length > 0
    ).length,
    promptGroups: groupByPrompt(responses).sort(
      (left, right) =>
        right.responses.length - left.responses.length ||
        left.prompt.localeCompare(right.prompt)
    ),
    visibilityTimeline: buildTimeline(trackedPrompts),
    domainGroups,
    topDomains,
    competitorMentions,
    chatbotSummaries,
    recommendations: safeArray(audit.manual_recommendations),
  }
}

export function normalizeDomain(value: string) {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, "")
    .split("/")[0]

  const parts = cleaned.split(".").filter(Boolean)
  if (parts.length <= 2) {
    return cleaned
  }

  return parts.slice(-2).join(".")
}

export function formatDate(value: string) {
  if (!value) {
    return "Unknown date"
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date)
}

export function formatPercent(value: number) {
  return `${Math.round(value)}%`
}

export function pluralize(count: number, singular: string, plural: string) {
  return count === 1 ? singular : plural
}

export function sortByCountDesc<T extends { count: number }>(items: T[]) {
  return [...items].sort((left, right) => right.count - left.count)
}
