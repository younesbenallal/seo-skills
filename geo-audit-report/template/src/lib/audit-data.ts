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
  fan_out_details?: AuditFanOutDetail[]
  fan_out_count?: number
  used_web_search?: boolean
  sources_count?: number
  ugc_sources_count?: number
  youtube_sources_count?: number
  competitor_domains?: string[]
  brands_mentioned?: string[]
  sources?: AuditSource[]
}

type AuditFanOutDetail = {
  query?: string
  brand_appeared_in_response?: boolean
  brand_cited_in_response?: boolean
  brand_found_in_search_results?: boolean
  matched_target_domains?: string[]
  search_results_count?: number
  search_results?: AuditSource[]
}

type AuditFanOutSummary = {
  query?: string
  count?: number
  appeared_in_responses?: number
  not_appeared_in_responses?: number
  cited_in_responses?: number
  found_in_search_results?: number
  prompts?: string[]
  chatbots?: string[]
  matched_target_domains?: string[]
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
  fan_out_details: FanOutDetailRecord[]
  fan_out_count: number
  used_web_search: boolean
  sources_count: number
  ugc_sources_count: number
  youtube_sources_count: number
  competitor_domains: string[]
  brands_mentioned: string[]
  sources: SourceRecord[]
}

export type FanOutDetailRecord = {
  query: string
  brand_appeared_in_response: boolean
  brand_cited_in_response: boolean
  brand_found_in_search_results: boolean
  matched_target_domains: string[]
  search_results_count: number
  search_results: SourceRecord[]
}

export type FanOutSummaryRecord = {
  query: string
  count: number
  appeared_in_responses: number
  not_appeared_in_responses: number
  cited_in_responses: number
  found_in_search_results: number
  prompts: string[]
  chatbots: string[]
  matched_target_domains: string[]
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
  fan_out_summary?: AuditFanOutSummary[]
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

function normalizeFanOutDetail(detail: AuditFanOutDetail): FanOutDetailRecord {
  return {
    query: detail.query ?? "",
    brand_appeared_in_response: Boolean(detail.brand_appeared_in_response),
    brand_cited_in_response: Boolean(detail.brand_cited_in_response),
    brand_found_in_search_results: Boolean(
      detail.brand_found_in_search_results
    ),
    matched_target_domains: safeArray(detail.matched_target_domains).filter(
      Boolean
    ),
    search_results_count:
      detail.search_results_count ?? safeArray(detail.search_results).length,
    search_results: safeArray(detail.search_results).map(normalizeSource),
  }
}

function normalizeFanOutSummary(
  summary: AuditFanOutSummary
): FanOutSummaryRecord {
  return {
    query: summary.query ?? "",
    count: summary.count ?? 0,
    appeared_in_responses: summary.appeared_in_responses ?? 0,
    not_appeared_in_responses: summary.not_appeared_in_responses ?? 0,
    cited_in_responses: summary.cited_in_responses ?? 0,
    found_in_search_results: summary.found_in_search_results ?? 0,
    prompts: safeArray(summary.prompts).filter(Boolean),
    chatbots: safeArray(summary.chatbots).filter(Boolean),
    matched_target_domains: safeArray(summary.matched_target_domains).filter(
      Boolean
    ),
  }
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
    fan_out_details: safeArray(response.fan_out_details)
      .map(normalizeFanOutDetail)
      .filter((detail) => detail.query),
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
    fan_out_summary: safeArray(audit.fan_out_summary).map(
      normalizeFanOutSummary
    ),
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

function buildFanOutSummaryFromResponses(responses: ResponseRecord[]) {
  const fanOutMap = new Map<string, FanOutSummaryRecord>()

  for (const response of responses) {
    const details =
      response.fan_out_details.length > 0
        ? response.fan_out_details
        : response.fan_out_queries.map((query) => ({
            query,
            brand_appeared_in_response: response.mentions > 0,
            brand_cited_in_response: response.cited,
            brand_found_in_search_results: false,
            matched_target_domains: [],
            search_results_count: 0,
            search_results: [],
          }))

    for (const detail of details) {
      const key = detail.query.toLowerCase()
      const current = fanOutMap.get(key) || {
        query: detail.query,
        count: 0,
        appeared_in_responses: 0,
        not_appeared_in_responses: 0,
        cited_in_responses: 0,
        found_in_search_results: 0,
        prompts: [],
        chatbots: [],
        matched_target_domains: [],
      }

      current.count += 1
      current.appeared_in_responses += detail.brand_appeared_in_response ? 1 : 0
      current.not_appeared_in_responses += detail.brand_appeared_in_response
        ? 0
        : 1
      current.cited_in_responses += detail.brand_cited_in_response ? 1 : 0
      current.found_in_search_results += detail.brand_found_in_search_results
        ? 1
        : 0
      current.prompts = [...new Set([...current.prompts, response.prompt])]
      current.chatbots = [...new Set([...current.chatbots, response.chatbot])]
      current.matched_target_domains = [
        ...new Set([
          ...current.matched_target_domains,
          ...detail.matched_target_domains,
        ]),
      ]

      fanOutMap.set(key, current)
    }
  }

  return [...fanOutMap.values()].sort(
    (left, right) =>
      right.count - left.count ||
      right.appeared_in_responses - left.appeared_in_responses ||
      left.query.localeCompare(right.query)
  )
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
  const fanOutSummary =
    safeArray(audit.fan_out_summary).length > 0
      ? safeArray(audit.fan_out_summary).map(normalizeFanOutSummary)
      : buildFanOutSummaryFromResponses(responses)
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
    fanOutSummary,
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
