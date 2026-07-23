type Source = {
  title?: string | null
  url?: string | null
  domain?: string | null
  display_domain?: string | null
  type?: string | null
  source_kind?: string | null
  cited?: boolean | null
  position?: number | null
  answer_position?: number | null
  description?: string | null
  date_published?: string | null
}

type MapResult = {
  name?: string | null
  category?: string | null
  rating?: number | null
  review_count?: number | null
  website_url?: string | null
  domain?: string | null
  position?: number | null
  phone_number?: string | null
  directions_url?: string | null
}

type CompetitorEntity = {
  name?: string | null
  domain?: string | null
  channels?: string[]
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
  used_web_search?: boolean
  fan_out_queries?: string[]
  target_found_in_search?: boolean
  target_found_in_maps?: boolean
  sources?: Source[]
  actual_citations?: Source[]
  citation_candidates?: Source[]
  uncited_citation_candidates?: Source[]
  search_sources?: Source[]
  attached_links?: Array<{
    text?: string | null
    url?: string | null
    domain?: string | null
    position?: number | null
  }>
  map_results?: MapResult[]
  competitor_entities?: CompetitorEntity[]
  evidence_status?: Record<
    string,
    {
      state?: "supported" | "missing" | "inferred" | "malformed"
      records?: number
      note?: string | null
    }
  >
  normalization?: {
    status?: string
    warnings?: Array<{
      code?: string
      field?: string
      message?: string
    }>
  }
}

type ManualRecommendation = {
  title: string
  summary: string
  priority: string
  owner?: string
}

export type AuditFileRecord = {
  schema_version?: string
  provider?: string
  provider_method?: string
  run_at: string
  check_url: string
  target_domains: string[]
  brand_terms: string[]
  snapshots: Array<{
    chatbot: string
    status: string
    collection_method?: string
  }>
  manual_recommendations?: ManualRecommendation[]
  collection_diagnostics?: {
    status?: string
    records_received?: number
    records_normalized?: number
    records_rejected?: number
    warning_count?: number
    warnings?: unknown[]
    rejected_records?: unknown[]
    unknown_provider_fields?: string[]
    capabilities?: Record<string, Record<string, number>>
  }
  responses?: AuditResponse[]
  results?: AuditResponse[]
}

export type TrackedPromptsRecord = {
  tracked_prompts: Array<{
    prompt: string
    history?: Array<{
      date: string
      visibility: number
      prompt_count?: number
      cited_count?: number
    }>
  }>
}

type SuccessfulLoad = {
  ok: true
  audit: AuditFileRecord
  trackedPrompts: TrackedPromptsRecord
}

export type DashboardLoadResult =
  | SuccessfulLoad
  | {
      ok: false
      error: string
    }

export type SourceRecord = ReturnType<typeof normalizeSource>
export type ResponseRecord = ReturnType<typeof normalizeResponse>

const safeArray = <T,>(value: T[] | undefined | null) =>
  Array.isArray(value) ? value : []

const domainFromUrl = (value: string) => {
  try {
    return new URL(value).hostname.replace(/^www\./, "").toLowerCase()
  } catch {
    return ""
  }
}

function normalizeSource(source: Source) {
  const url = source.url ?? ""
  return {
    title: source.title ?? "",
    url,
    domain: domainFromUrl(url) || source.domain || "",
    displayDomain: source.display_domain ?? "",
    type: source.type ?? "web",
    sourceKind: source.source_kind ?? "citation",
    cited: source.cited ?? null,
    position: source.position ?? null,
    answerPosition: source.answer_position ?? null,
    description: source.description ?? "",
    datePublished: source.date_published ?? "",
  }
}

function normalizeResponse(response: AuditResponse) {
  const candidates = safeArray(response.citation_candidates).map(normalizeSource)
  const actual = safeArray(
    response.actual_citations?.length ? response.actual_citations : response.sources
  ).map(normalizeSource)
  const uncited = response.uncited_citation_candidates
    ? response.uncited_citation_candidates.map(normalizeSource)
    : candidates.filter((source) => source.cited === false)
  const state = (
    channel: string,
    fallback: "supported" | "missing" = "missing"
  ) => response.evidence_status?.[channel]?.state ?? fallback

  return {
    chatbot: response.chatbot,
    model: response.model ?? "",
    prompt: response.prompt,
    capturedAt: response.captured_at ?? "",
    answerMarkdown: response.answer_text_markdown ?? "",
    mentions: response.mentions ?? 0,
    cited: Boolean(response.cited),
    firstCitationRank: response.first_citation_rank ?? null,
    usedWebSearch: Boolean(response.used_web_search),
    targetFoundInSearch: Boolean(response.target_found_in_search),
    targetFoundInMaps: Boolean(response.target_found_in_maps),
    fanOutQueries: safeArray(response.fan_out_queries),
    actualCitations: actual,
    citationCandidates: candidates.length ? candidates : actual,
    uncitedCitationCandidates: uncited,
    searchSources: safeArray(response.search_sources).map(normalizeSource),
    attachedLinks: safeArray(response.attached_links).map((link) => ({
      text: link.text ?? "",
      url: link.url ?? "",
      domain: domainFromUrl(link.url ?? "") || link.domain || "",
      position: link.position ?? null,
    })),
    mapResults: safeArray(response.map_results).map((result) => ({
      name: result.name ?? "",
      category: result.category ?? "",
      rating: result.rating ?? null,
      reviewCount: result.review_count ?? null,
      websiteUrl: result.website_url ?? "",
      domain: domainFromUrl(result.website_url ?? "") || result.domain || "",
      position: result.position ?? null,
      phoneNumber: result.phone_number ?? "",
      directionsUrl: result.directions_url ?? "",
    })),
    competitorEntities: safeArray(response.competitor_entities).map((entity) => ({
      name: entity.name ?? entity.domain ?? "Unknown",
      domain: entity.domain ?? "",
      channels: safeArray(entity.channels),
    })),
    evidenceStatus: {
      answer: state("answer", response.answer_text_markdown !== undefined ? "supported" : "missing"),
      webSearch: state(
        "web_search",
        response.used_web_search !== undefined ? "supported" : "missing"
      ),
      actualCitations: state(
        "actual_citations",
        response.actual_citations !== undefined || response.sources !== undefined
          ? "supported"
          : "missing"
      ),
      citationCandidates: state(
        "citation_candidates",
        response.citation_candidates !== undefined ? "supported" : "missing"
      ),
      searchSources: state(
        "search_sources",
        response.search_sources !== undefined ? "supported" : "missing"
      ),
      attachedLinks: state(
        "attached_links",
        response.attached_links !== undefined ? "supported" : "missing"
      ),
      maps: state("maps", response.map_results !== undefined ? "supported" : "missing"),
    },
    normalizationWarnings: safeArray(response.normalization?.warnings),
  }
}

const uniqueBy = <T,>(items: T[], key: (item: T) => string) =>
  [...new Map(items.filter((item) => key(item)).map((item) => [key(item), item])).values()]

export function buildAuditViewModel(
  audit: AuditFileRecord,
  trackedPrompts: TrackedPromptsRecord
) {
  const rawResponses =
    audit.responses?.length ? audit.responses : audit.results ?? []
  const responses = rawResponses.map(normalizeResponse)
  const isAvailable = (state: string) =>
    state === "supported" || state === "inferred"
  const prompts = [...new Set(responses.map((response) => response.prompt))]
  const searched = responses.filter((response) => response.usedWebSearch).length
  const retrieved = responses.filter((response) => response.searchSources.length > 0).length
  const mapped = responses.filter((response) => response.mapResults.length > 0).length
  const mentioned = responses.filter((response) => response.mentions > 0).length
  const cited = responses.filter((response) => response.cited).length
  const foundInSearch = responses.filter((response) => response.targetFoundInSearch).length
  const foundInMaps = responses.filter((response) => response.targetFoundInMaps).length
  const availability = {
    webSearch: responses.filter((response) =>
      isAvailable(response.evidenceStatus.webSearch)
    ).length,
    searchSources: responses.filter((response) =>
      isAvailable(response.evidenceStatus.searchSources)
    ).length,
    maps: responses.filter((response) => isAvailable(response.evidenceStatus.maps))
      .length,
    answers: responses.filter((response) =>
      isAvailable(response.evidenceStatus.answer)
    ).length,
    actualCitations: responses.filter((response) =>
      isAvailable(response.evidenceStatus.actualCitations)
    ).length,
    citationCandidates: responses.filter((response) =>
      isAvailable(response.evidenceStatus.citationCandidates)
    ).length,
  }
  const actualCitations = responses.flatMap((response) => response.actualCitations)
  const citationCandidates = responses.flatMap(
    (response) => response.citationCandidates
  )
  const searchSources = responses.flatMap((response) => response.searchSources)
  const mapResults = responses.flatMap((response) => response.mapResults)
  const uniqueCitedPages = uniqueBy(actualCitations, (source) => source.url)
  const uniqueCandidatePages = uniqueBy(citationCandidates, (source) => source.url)

  const promptGroups = prompts.map((prompt) => {
    const matches = responses.filter((response) => response.prompt === prompt)
    return {
      prompt,
      responses: matches,
      searched: matches.some((response) =>
        isAvailable(response.evidenceStatus.webSearch)
      )
        ? matches.some((response) => response.usedWebSearch)
        : null,
      retrieved: matches.some((response) =>
        isAvailable(response.evidenceStatus.searchSources)
      )
        ? matches.some((response) => response.searchSources.length > 0)
        : null,
      mapped: matches.some((response) => isAvailable(response.evidenceStatus.maps))
        ? matches.some((response) => response.mapResults.length > 0)
        : null,
      mentioned: matches.some((response) =>
        isAvailable(response.evidenceStatus.answer)
      )
        ? matches.some((response) => response.mentions > 0)
        : null,
      cited: matches.some((response) =>
        isAvailable(response.evidenceStatus.actualCitations)
      )
        ? matches.some((response) => response.cited)
        : null,
      foundInSearch: matches.some((response) =>
        isAvailable(response.evidenceStatus.searchSources)
      )
        ? matches.some((response) => response.targetFoundInSearch)
        : null,
      foundInMaps: matches.some((response) =>
        isAvailable(response.evidenceStatus.maps)
      )
        ? matches.some((response) => response.targetFoundInMaps)
        : null,
    }
  })

  const domainMap = new Map<
    string,
    { domain: string; appearances: number; pages: Map<string, SourceRecord> }
  >()
  for (const source of actualCitations) {
    if (!source.domain) continue
    const current = domainMap.get(source.domain) ?? {
      domain: source.domain,
      appearances: 0,
      pages: new Map(),
    }
    current.appearances += 1
    current.pages.set(source.url, source)
    domainMap.set(source.domain, current)
  }
  const citedDomains = [...domainMap.values()]
    .map((item) => ({ ...item, pages: [...item.pages.values()] }))
    .sort((left, right) => right.appearances - left.appearances)

  const competitorMap = new Map<
    string,
    { name: string; domain: string; channels: Set<string>; prompts: Set<string> }
  >()
  for (const response of responses) {
    for (const entity of response.competitorEntities) {
      const key = entity.domain || entity.name.toLowerCase()
      const current = competitorMap.get(key) ?? {
        name: entity.name,
        domain: entity.domain,
        channels: new Set(),
        prompts: new Set(),
      }
      entity.channels.forEach((channel) => current.channels.add(channel))
      current.prompts.add(response.prompt)
      competitorMap.set(key, current)
    }
  }
  const competitors = [...competitorMap.values()]
    .map((item) => ({
      ...item,
      channels: [...item.channels],
      promptCount: item.prompts.size,
    }))
    .sort((left, right) => right.promptCount - left.promptCount)

  const mapGroups = new Map<
    string,
    {
      name: string
      domain: string
      bestPosition: number | null
      rating: number | null
      reviewCount: number | null
      category: string
      promptCount: number
      websiteUrl: string
    }
  >()
  for (const response of responses) {
    for (const result of response.mapResults) {
      const key = result.domain || result.name.toLowerCase()
      const current = mapGroups.get(key)
      mapGroups.set(key, {
        name: result.name || current?.name || "Unknown",
        domain: result.domain || current?.domain || "",
        bestPosition:
          current?.bestPosition === null || current?.bestPosition === undefined
            ? result.position
            : result.position === null
              ? current.bestPosition
              : Math.min(current.bestPosition, result.position),
        rating: result.rating ?? current?.rating ?? null,
        reviewCount: result.reviewCount ?? current?.reviewCount ?? null,
        category: result.category || current?.category || "",
        promptCount: (current?.promptCount ?? 0) + 1,
        websiteUrl: result.websiteUrl || current?.websiteUrl || "",
      })
    }
  }

  const historyDates = new Set(
    safeArray(trackedPrompts.tracked_prompts).flatMap((item) =>
      safeArray(item.history).map((history) => history.date)
    )
  )

  return {
    brandName:
      audit.brand_terms?.[0] || audit.target_domains?.[0] || "Brand",
    responses,
    promptGroups,
    citedDomains,
    competitors,
    mapGroups: [...mapGroups.values()].sort(
      (left, right) =>
        right.promptCount - left.promptCount ||
        (left.bestPosition ?? 99) - (right.bestPosition ?? 99)
    ),
    metrics: {
      promptCount: prompts.length,
      searched,
      retrieved,
      mapped,
      mentioned,
      cited,
      foundInSearch,
      foundInMaps,
      actualCitationAppearances: actualCitations.length,
      uniqueCitedPages: uniqueCitedPages.length,
      candidateAppearances: citationCandidates.length,
      uniqueCandidatePages: uniqueCandidatePages.length,
      searchSourceAppearances: searchSources.length,
      mapPlacements: mapResults.length,
      availability,
    },
    recommendations: safeArray(audit.manual_recommendations),
    hasLongitudinalHistory: historyDates.size > 1,
    diagnostics: audit.collection_diagnostics,
  }
}

export function createDashboardLoadSuccess(
  audit: AuditFileRecord,
  trackedPrompts: TrackedPromptsRecord
): DashboardLoadResult {
  return { ok: true, audit, trackedPrompts }
}
