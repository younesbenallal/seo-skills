"use client"

import { useDeferredValue, useState } from "react"
import {
  ArrowUpRight,
  Bot,
  ExternalLink,
  Globe,
  Link2,
  Search,
} from "lucide-react"

import { Gemini } from "@/src/components/ui/svgs/gemini"
import { Openai } from "@/src/components/ui/svgs/openai"
import { Perplexity } from "@/src/components/ui/svgs/perplexity"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/src/components/ui/accordion"
import { Badge } from "@/src/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/src/components/ui/card"
import { Input } from "@/src/components/ui/input"
import { Separator } from "@/src/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/src/components/ui/tabs"
import {
  buildAuditViewModel,
  formatDate,
  formatPercent,
  pluralize,
  sortByCountDesc,
  type DashboardLoadResult,
  type DomainGroup,
  type FanOutSummaryRecord,
  type PromptGroup,
} from "@/src/lib/audit-data"

function ChatbotLogo({
  chatbot,
  className,
}: {
  chatbot: string
  className?: string
}) {
  const normalized = chatbot.toLowerCase()

  if (
    normalized.includes("gpt") ||
    normalized.includes("openai") ||
    normalized.includes("chatgpt")
  ) {
    return <Openai className={className} />
  }

  if (normalized.includes("perplex")) {
    return <Perplexity className={className} />
  }

  if (normalized.includes("gemini")) {
    return <Gemini className={className} />
  }

  return <Bot className={className} />
}

function MetricCard({
  title,
  value,
  detail,
}: {
  title: string
  value: string
  detail: string
}) {
  return (
    <Card className="border-border/80 shadow-none">
      <CardHeader className="pb-3">
        <CardDescription className="text-xs text-muted-foreground">
          {title}
        </CardDescription>
        <CardTitle className="text-3xl font-semibold tracking-tight">
          {value}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0 text-sm text-muted-foreground">
        {detail}
      </CardContent>
    </Card>
  )
}

function MeterRow({
  label,
  value,
  meta,
}: {
  label: string
  value: number
  meta: string
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4 text-sm">
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{label}</p>
          <p className="truncate text-xs text-muted-foreground">{meta}</p>
        </div>
        <span className="shrink-0 font-medium text-foreground">
          {formatPercent(value)}
        </span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-foreground/80 transition-[width]"
          style={{ width: `${Math.max(value, 4)}%` }}
        />
      </div>
    </div>
  )
}

function ChatbotSummary({
  label,
  visibility,
  citationCount,
  averageRank,
}: {
  label: string
  visibility: number
  citationCount: number
  averageRank: number | null
}) {
  return (
    <div className="rounded-xl border border-border/80 bg-card p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex size-8 items-center justify-center rounded-md bg-muted/70">
            <ChatbotLogo
              chatbot={label}
              className="size-4 fill-current text-foreground"
            />
          </span>
          <div>
            <p className="text-sm font-medium text-foreground">{label}</p>
            <p className="text-xs text-muted-foreground">
              {citationCount} {pluralize(citationCount, "citation", "citations")}
            </p>
          </div>
        </div>
        <Badge variant="secondary" className="rounded-md px-2.5 py-1">
          {averageRank === null ? "no rank" : `avg rank #${averageRank}`}
        </Badge>
      </div>
      <div className="mt-4 h-2 rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-foreground"
          style={{ width: `${Math.max(visibility, 6)}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        visibility across tracked prompt responses
      </p>
    </div>
  )
}

function PromptPanel({ promptGroup }: { promptGroup: PromptGroup }) {
  return (
    <AccordionItem
      value={promptGroup.prompt}
      className="overflow-hidden rounded-xl border border-border/80 bg-background px-5"
    >
      <AccordionTrigger className="py-5 hover:no-underline">
        <div className="flex min-w-0 flex-1 flex-col gap-3 text-left">
          <div className="flex min-w-0 flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <p className="truncate text-base font-medium text-foreground">
                {promptGroup.prompt}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {promptGroup.responses.length}{" "}
                {pluralize(promptGroup.responses.length, "response", "responses")}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="rounded-md">
                visibility {formatPercent(promptGroup.visibility)}
              </Badge>
              <Badge variant="secondary" className="rounded-md">
                citations {promptGroup.citations}
              </Badge>
              <Badge variant="secondary" className="rounded-md">
                avg rank{" "}
                {promptGroup.averageRank === null
                  ? "n/a"
                  : `#${promptGroup.averageRank}`}
              </Badge>
              <Badge variant="secondary" className="rounded-md">
                search triggered{" "}
                {
                  promptGroup.responses.filter(
                    (response) => response.used_web_search
                  ).length
                }
                /{promptGroup.responses.length}
              </Badge>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            {promptGroup.models.map((model) => (
              <span
                key={model}
                className="inline-flex items-center gap-2 rounded-md border border-border/80 px-2.5 py-1"
              >
                <ChatbotLogo
                  chatbot={model}
                  className="size-3.5 fill-current text-foreground"
                />
                <span>{model}</span>
              </span>
            ))}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-4 pb-5">
        {promptGroup.responses.map((response) => (
          <Card
            key={`${response.chatbot}-${response.prompt}`}
            className="rounded-lg border-border/75 shadow-none"
          >
            <CardHeader className="gap-4 border-b border-border/70">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex size-9 items-center justify-center rounded-md bg-muted/70">
                    <ChatbotLogo
                      chatbot={response.chatbot}
                      className="size-4 fill-current text-foreground"
                    />
                  </span>
                  <div>
                    <CardTitle className="text-lg">
                      {response.model || response.chatbot}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      captured {formatDate(response.captured_at)}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="rounded-md">
                    visibility {response.cited ? "cited" : "mentioned only"}
                  </Badge>
                  <Badge variant="secondary" className="rounded-md">
                    {response.citations_count}{" "}
                    {pluralize(response.citations_count, "citation", "citations")}
                  </Badge>
                  <Badge variant="secondary" className="rounded-md">
                    fan-out {response.fan_out_queries.length}
                  </Badge>
                  <Badge variant="secondary" className="rounded-md">
                    search {response.used_web_search ? "triggered" : "not triggered"}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-5 pt-5">
              {response.brands_mentioned.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">brands mentioned</p>
                  <div className="flex flex-wrap gap-2">
                    {response.brands_mentioned.map((brand) => (
                      <Badge
                        key={`${response.prompt}-${brand}`}
                        variant="outline"
                        className="rounded-md"
                      >
                        {brand}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">response</p>
                <div className="rounded-lg bg-muted/40 p-4 text-sm leading-7 text-foreground">
                  <p className="whitespace-pre-wrap">
                    {response.answer_text_markdown || "No response body available."}
                  </p>
                </div>
              </div>

              {response.fan_out_queries.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">fan-out prompts</p>
                  <div className="space-y-2">
                    {(response.fan_out_details.length > 0
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
                    ).map((detail) => (
                      <div
                        key={`${response.prompt}-${detail.query}`}
                        className="rounded-lg border border-border/75 bg-muted/25 p-3"
                      >
                        <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                          <p className="text-sm font-medium text-foreground">
                            {detail.query}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            <Badge variant="secondary" className="rounded-md">
                              response{" "}
                              {detail.brand_appeared_in_response
                                ? "mentions us"
                                : "misses us"}
                            </Badge>
                            <Badge variant="secondary" className="rounded-md">
                              citation {detail.brand_cited_in_response ? "yes" : "no"}
                            </Badge>
                            <Badge variant="secondary" className="rounded-md">
                              serp{" "}
                              {detail.brand_found_in_search_results
                                ? "contains us"
                                : "misses us"}
                            </Badge>
                            <Badge variant="secondary" className="rounded-md">
                              {detail.search_results_count} search results
                            </Badge>
                          </div>
                        </div>
                        {detail.search_results.length > 0 ? (
                          <div className="mt-3 space-y-2">
                            {detail.search_results.slice(0, 5).map((result) => (
                              <a
                                key={`${detail.query}-${result.url}`}
                                href={result.url}
                                target="_blank"
                                rel="noreferrer"
                                className="flex items-center justify-between gap-3 rounded-md border border-border/70 px-3 py-2 text-xs transition-colors hover:bg-background"
                              >
                                <div className="min-w-0">
                                  <p className="truncate font-medium text-foreground">
                                    {result.title || result.url}
                                  </p>
                                  <p className="truncate text-muted-foreground">
                                    {result.domain}
                                  </p>
                                </div>
                                <ExternalLink className="size-3.5 shrink-0 text-muted-foreground" />
                              </a>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {response.sources.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">sources</p>
                  <div className="space-y-2">
                    {response.sources.slice(0, 8).map((source) => (
                      <a
                        key={source.url}
                        href={source.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center justify-between gap-4 rounded-lg border border-border/70 px-4 py-3 text-sm transition-colors hover:bg-muted/40"
                      >
                        <div className="min-w-0">
                          <p className="truncate font-medium text-foreground">
                            {source.title || source.url}
                          </p>
                          <p className="truncate text-xs text-muted-foreground">
                            {source.domain}
                          </p>
                        </div>
                        <ExternalLink className="size-4 shrink-0 text-muted-foreground" />
                      </a>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </AccordionContent>
    </AccordionItem>
  )
}

function FanOutSummaryPanel({ summary }: { summary: FanOutSummaryRecord }) {
  return (
    <div className="rounded-xl border border-border/80 bg-background p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">{summary.query}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {summary.count} {pluralize(summary.count, "time", "times")} across{" "}
            {summary.prompts.length} {pluralize(summary.prompts.length, "prompt", "prompts")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="rounded-md">
            appeared {summary.appeared_in_responses}
          </Badge>
          <Badge variant="secondary" className="rounded-md">
            missed {summary.not_appeared_in_responses}
          </Badge>
          <Badge variant="secondary" className="rounded-md">
            cited {summary.cited_in_responses}
          </Badge>
          <Badge variant="secondary" className="rounded-md">
            serp hits {summary.found_in_search_results}
          </Badge>
        </div>
      </div>
    </div>
  )
}

function SourcePanel({ domainGroup }: { domainGroup: DomainGroup }) {
  return (
    <AccordionItem
      value={domainGroup.domain}
      className="overflow-hidden rounded-xl border border-border/80 bg-background px-5"
    >
      <AccordionTrigger className="py-5 hover:no-underline">
        <div className="flex min-w-0 flex-1 items-start justify-between gap-6 text-left">
          <div className="min-w-0">
            <p className="truncate text-base font-medium text-foreground">
              {domainGroup.domain}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {domainGroup.uniquePages} {pluralize(domainGroup.uniquePages, "page", "pages")} across{" "}
              {domainGroup.responsesCount} {pluralize(domainGroup.responsesCount, "response", "responses")}
            </p>
          </div>
          <div className="hidden shrink-0 gap-6 text-sm text-muted-foreground md:flex">
            <span>{domainGroup.uniquePages} pages</span>
            <span>{domainGroup.responsesCount} responses</span>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="pb-5">
        <div className="space-y-3">
          {domainGroup.pages.map((page) => (
            <a
              key={page.url}
              href={page.url}
              target="_blank"
              rel="noreferrer"
              className="flex flex-col gap-3 rounded-lg border border-border/70 px-4 py-4 transition-colors hover:bg-muted/40 md:flex-row md:items-center md:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate font-medium text-foreground">
                  {page.title || page.url}
                </p>
                <p className="truncate text-sm text-muted-foreground">
                  {page.url}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3 text-xs text-muted-foreground">
                <span>{page.responseCount} responses</span>
                <ArrowUpRight className="size-4" />
              </div>
            </a>
          ))}
        </div>
      </AccordionContent>
    </AccordionItem>
  )
}

export function AuditDashboard({ loaded }: { loaded: DashboardLoadResult }) {
  const [sourceQuery, setSourceQuery] = useState("")
  const deferredSourceQuery = useDeferredValue(sourceQuery)

  if (!loaded.ok) {
    return (
      <main className="min-h-svh bg-background px-6 py-12">
        <div className="mx-auto max-w-3xl">
          <Card className="border-border/80 shadow-none">
            <CardHeader>
              <CardTitle>Unable to load audit data</CardTitle>
              <CardDescription>
                The dashboard could not read the configured JSON files.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>{loaded.error}</p>
              <p>
                Check <code>AUDIT_DATA_PATH</code> and <code>TRACKED_PROMPTS_PATH</code>,
                then restart the dev server.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    )
  }

  const { audit, trackedPrompts } = loaded
  const view = buildAuditViewModel(audit, trackedPrompts)
  const filteredDomainGroups = view.domainGroups.filter((domainGroup) => {
    if (!deferredSourceQuery.trim()) {
      return true
    }

    const query = deferredSourceQuery.trim().toLowerCase()
    return (
      domainGroup.domain.toLowerCase().includes(query) ||
      domainGroup.pages.some(
        (page) =>
          page.url.toLowerCase().includes(query) ||
          page.title.toLowerCase().includes(query)
      )
    )
  })

  return (
    <main className="min-h-svh bg-[linear-gradient(180deg,rgba(255,255,255,1),rgba(244,244,245,0.65))]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
        <header className="rounded-2xl border border-border/80 bg-background/95 p-6 shadow-[0_1px_0_rgba(0,0,0,0.03)] backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <p className="text-xs text-muted-foreground">geo audit dashboard</p>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                  {view.brandName}
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
                  Static-first Next dashboard for Bright Data GEO audits. Point
                  the build at a run JSON, export, and you get a shareable HTML bundle.
                </p>
              </div>
            </div>

            <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
              <div className="rounded-lg border border-border/70 px-4 py-3">
                <p className="text-xs">generated</p>
                <p className="mt-1 font-medium text-foreground">
                  {formatDate(audit.run_at)}
                </p>
              </div>
              <div className="rounded-lg border border-border/70 px-4 py-3">
                <p className="text-xs">site</p>
                <a
                  href={audit.check_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 flex items-center gap-2 font-medium text-foreground hover:text-muted-foreground"
                >
                  <span className="truncate">{audit.check_url}</span>
                  <ExternalLink className="size-4 shrink-0" />
                </a>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Mention rate"
            value={formatPercent(view.mentionRate)}
            detail="Percentage of responses that mention the brand at least once."
          />
          <MetricCard
            title="Citation rate"
            value={formatPercent(view.citationRate)}
            detail="Share of responses that directly cite one of the tracked domains."
          />
          <MetricCard
            title="Average rank"
            value={view.averageRank === null ? "n/a" : `#${view.averageRank}`}
            detail="Average first citation rank when the brand appears in the source list."
          />
          <MetricCard
            title="Sources"
            value={`${view.totalSources}`}
            detail="Unique links cited across all chatbot responses in this audit."
          />
        </section>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="w-full justify-start rounded-lg border border-border/70 bg-background p-1">
            <TabsTrigger value="overview" className="rounded-md px-4">
              Overview
            </TabsTrigger>
            <TabsTrigger value="prompts" className="rounded-md px-4">
              Prompts
            </TabsTrigger>
            <TabsTrigger value="sources" className="rounded-md px-4">
              Sources
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <section className="grid gap-6 xl:grid-cols-[1.45fr_1fr]">
              <Card className="border-border/80 shadow-none">
                <CardHeader>
                  <CardTitle>Visibility over time</CardTitle>
                  <CardDescription>
                    Derived from the tracked prompts history JSON.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  {view.visibilityTimeline.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Add entries to <code>tracked-prompts.json</code> to unlock
                      timeline tracking.
                    </p>
                  ) : (
                    view.visibilityTimeline.map((point) => (
                      <MeterRow
                        key={point.date}
                        label={formatDate(point.date)}
                        value={point.visibility}
                        meta={`${point.promptCount} tracked prompts`}
                      />
                    ))
                  )}
                </CardContent>
              </Card>

              <Card className="border-border/80 shadow-none">
                <CardHeader>
                  <CardTitle>Competitor mentions</CardTitle>
                  <CardDescription>
                    Domains surfaced in the answers next to the brand.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  {view.competitorMentions.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No competitor domains were detected in the current sample.
                    </p>
                  ) : (
                    sortByCountDesc(view.competitorMentions).map((item) => (
                      <MeterRow
                        key={item.label}
                        label={item.label}
                        value={item.share}
                        meta={`${item.count} mentions`}
                      />
                    ))
                  )}
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
              <Card className="border-border/80 shadow-none">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Bot className="size-4 text-muted-foreground" />
                    <CardTitle>Chatbot coverage</CardTitle>
                  </div>
                  <CardDescription>
                    Performance split by AI product for the current audit run.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                  {view.chatbotSummaries.map((chatbot) => (
                    <ChatbotSummary
                      key={chatbot.label}
                      label={chatbot.label}
                      visibility={chatbot.visibility}
                      citationCount={chatbot.citationCount}
                      averageRank={chatbot.averageRank}
                    />
                  ))}
                </CardContent>
              </Card>

              <Card className="border-border/80 shadow-none">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Link2 className="size-4 text-muted-foreground" />
                    <CardTitle>Top cited domains</CardTitle>
                  </div>
                  <CardDescription>
                    Most frequently cited sources grouped by domain.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5">
                  {view.topDomains.slice(0, 6).map((domain) => (
                    <MeterRow
                      key={domain.label}
                      label={domain.label}
                      value={domain.share}
                      meta={`${domain.count} cited pages`}
                    />
                  ))}
                </CardContent>
              </Card>
            </section>

            <Card className="border-border/80 shadow-none">
              <CardHeader>
                <CardTitle>Manual recommendations</CardTitle>
                <CardDescription>
                  Edit <code>manual_recommendations</code> in the audit JSON after
                  reviewing the results.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {view.recommendations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No manual recommendations yet.
                  </p>
                ) : (
                  view.recommendations.map((recommendation) => (
                    <div
                      key={recommendation.title}
                      className="rounded-xl border border-border/70 bg-muted/25 p-5"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="text-base font-medium text-foreground">
                          {recommendation.title}
                        </h3>
                        <Badge variant="secondary" className="rounded-md">
                          {recommendation.priority}
                        </Badge>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">
                        {recommendation.summary}
                      </p>
                      <p className="mt-4 text-xs text-muted-foreground">
                        {recommendation.owner}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card className="border-border/80 shadow-none">
              <CardHeader>
                <CardTitle>fan-out query summary</CardTitle>
                <CardDescription>
                  Every search query the AI models made, grouped and counted
                  with whether we appeared in the resulting response.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {view.fanOutSummary.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No search-engine fan-out queries were captured in this audit.
                  </p>
                ) : (
                  view.fanOutSummary.map((summary) => (
                    <FanOutSummaryPanel key={summary.query} summary={summary} />
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="prompts" className="space-y-6">
            <section className="grid gap-4 md:grid-cols-3">
              <MetricCard
                title="Tracked prompts"
                value={`${view.promptGroups.length}`}
                detail="Unique prompts represented in the current Bright Data run."
              />
              <MetricCard
                title="Responses"
                value={`${view.responses.length}`}
                detail="Total chatbot responses included in the audit JSON."
              />
              <MetricCard
                title="Tracked history"
                value={`${trackedPrompts.tracked_prompts.length}`}
                detail="Prompts listed in the separate over-time tracking JSON."
              />
            </section>

            <Card className="border-border/80 shadow-none">
              <CardHeader>
                <CardTitle>Prompt breakdown</CardTitle>
                <CardDescription>
                  Each prompt expands into the responses captured for every AI chatbot.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Accordion type="multiple" className="space-y-4">
                  {view.promptGroups.map((promptGroup) => (
                    <PromptPanel
                      key={promptGroup.prompt}
                      promptGroup={promptGroup}
                    />
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sources" className="space-y-6">
            <section className="grid gap-4 md:grid-cols-3">
              <MetricCard
                title="Source domains"
                value={`${view.domainGroups.length}`}
                detail="Distinct domains used by the AI products in the current file."
              />
              <MetricCard
                title="Unique pages"
                value={`${view.totalSources}`}
                detail="Unique cited URLs after deduplication across responses."
              />
              <MetricCard
                title="Responses with sources"
                value={`${view.responsesWithSources}`}
                detail="Responses that cite at least one source."
              />
            </section>

            <Card className="border-border/80 shadow-none">
              <CardHeader>
                <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                  <div>
                    <CardTitle>Source inventory</CardTitle>
                    <CardDescription>
                      Grouped by domain, then expanded into the exact pages cited by the chatbots.
                    </CardDescription>
                  </div>
                  <div className="w-full max-w-sm">
                    <label className="relative block">
                      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        value={sourceQuery}
                        onChange={(event) => setSourceQuery(event.target.value)}
                        placeholder="Search domains or URLs..."
                        className="pl-10"
                      />
                    </label>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Accordion type="multiple" className="space-y-4">
                  {filteredDomainGroups.map((domainGroup) => (
                    <SourcePanel
                      key={domainGroup.domain}
                      domainGroup={domainGroup}
                    />
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Separator />

        <footer className="flex flex-col gap-3 pb-4 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Globe className="size-4" />
            <span>
              Generated by{" "}
              <a
                href="https://holly-and-stick.com"
                target="_blank"
                rel="noreferrer"
                className="font-medium text-foreground hover:text-muted-foreground"
              >
                Holly&amp;Stick
              </a>
            </span>
          </div>
          <p>Bright Data JSON in, static export out.</p>
        </footer>
      </div>
    </main>
  )
}
