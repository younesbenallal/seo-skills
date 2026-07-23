"use client"

import {
  ArrowUpRight,
  Check,
  CircleAlert,
  ExternalLink,
  MapPin,
  Search,
  X,
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import {
  buildAuditViewModel,
  type DashboardLoadResult,
  type ResponseRecord,
  type SourceRecord,
} from "@/src/lib/audit-data"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/src/components/ui/accordion"
import { Badge } from "@/src/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/src/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/src/components/ui/tabs"

const percent = (value: number, total: number) =>
  `${Math.round((value / Math.max(total, 1)) * 100)}%`

const formatDate = (value: string) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(date)
}

function Signal({ value, label }: { value: boolean | null; label: string }) {
  if (value === null) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <CircleAlert className="size-3.5" />
        Not provided
      </span>
    )
  }
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium ${
        value ? "text-emerald-700" : "text-rose-700"
      }`}
    >
      {value ? <Check className="size-3.5" /> : <X className="size-3.5" />}
      {label}
    </span>
  )
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <Card className="border-border bg-card shadow-none">
      <CardContent className="p-5">
        <p className="text-xs font-medium text-zinc-500">{label}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight text-zinc-700">{value}</p>
        <p className="mt-2 text-xs font-medium leading-5 text-zinc-500">{detail}</p>
      </CardContent>
    </Card>
  )
}

function FunnelStep({
  label,
  count,
  total,
}: {
  label: string
  count: number
  total: number
}) {
  if (total === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border/75 bg-muted/20 p-4">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-medium">{label}</p>
          <span className="text-muted-foreground">n/a</span>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">Evidence not provided</p>
      </div>
    )
  }
  const healthy = count === total
  return (
    <div className="relative rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-zinc-600">{label}</p>
        <span className={`font-semibold ${healthy ? "text-emerald-700" : count ? "text-amber-700" : "text-rose-700"}`}>
          {count}/{total}
        </span>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className={healthy ? "h-full bg-emerald-500" : count ? "h-full bg-amber-500" : "h-full bg-rose-500"}
          style={{ width: percent(count, total) }}
        />
      </div>
    </div>
  )
}

function SourceList({
  title,
  sources,
  empty,
}: {
  title: string
  sources: SourceRecord[]
  empty: string
}) {
  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-medium">{title}</h4>
        <Badge variant="secondary">{sources.length}</Badge>
      </div>
      {sources.length ? (
        <div className="grid gap-2">
          {sources.map((source, index) => (
            <a
              key={`${source.url}-${index}`}
              href={source.url || "#"}
              target="_blank"
              rel="noreferrer"
              className="flex items-start justify-between gap-4 rounded-lg border border-border/70 p-3 text-sm transition-colors hover:bg-muted/40"
            >
              <span className="min-w-0">
                <span className="block truncate font-medium">
                  {source.title || source.url}
                </span>
                <span className="mt-1 block truncate text-xs font-medium text-zinc-500">
                  {source.domain}
                  {source.position ? ` · position ${source.position}` : ""}
                </span>
              </span>
              <ExternalLink className="mt-0.5 size-3.5 shrink-0 text-zinc-500" />
            </a>
          ))}
        </div>
      ) : (
        <p className="rounded-lg border border-dashed bg-zinc-50 p-4 text-sm font-medium text-zinc-500">{empty}</p>
      )}
    </section>
  )
}

function Evidence({ response }: { response: ResponseRecord }) {
  const citationsAvailable = ["supported", "inferred"].includes(
    response.evidenceStatus.actualCitations
  )
  const answerAvailable = ["supported", "inferred"].includes(
    response.evidenceStatus.answer
  )
  const status =
    !answerAvailable
      ? "Answer unavailable"
      : response.mentions > 0
      ? response.cited
        ? "Mentioned and cited"
        : "Mentioned, not cited"
      : "Brand absent"

  return (
    <AccordionItem value={`${response.chatbot}-${response.prompt}`} className="rounded-xl border px-5">
      <AccordionTrigger className="gap-4 py-5 hover:no-underline">
        <div className="min-w-0 flex-1 text-left">
          <p className="text-sm font-medium">{response.prompt}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant={response.mentions > 0 ? "secondary" : "destructive"}>{status}</Badge>
            <Badge variant="outline">
              {citationsAvailable
                ? `${response.actualCitations.length} actual citations`
                : "Citation status unavailable"}
            </Badge>
            <Badge variant="outline">
              {["supported", "inferred"].includes(response.evidenceStatus.maps)
                ? `${response.mapResults.length} map results`
                : "Map data unavailable"}
            </Badge>
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="space-y-7 pb-6">
        <section>
          <h4 className="mb-3 text-sm font-medium">Final answer</h4>
          <div className="prose max-w-none rounded-xl border bg-zinc-50 p-5 text-sm leading-7">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{response.answerMarkdown}</ReactMarkdown>
          </div>
        </section>

        <div className="grid gap-7 xl:grid-cols-2">
          <SourceList
            title="Actual cited pages"
            sources={response.actualCitations}
            empty={
              citationsAvailable
                ? "No pages were cited in this answer."
                : "The provider did not supply reliable actual-citation status."
            }
          />
          <SourceList
            title="Uncited citation candidates"
            sources={response.uncitedCitationCandidates}
            empty="No uncited citation candidates were captured."
          />
          <SourceList
            title="Captured search sources"
            sources={response.searchSources}
            empty="No structured search sources were captured."
          />
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Map placements</h4>
              <Badge variant="secondary">{response.mapResults.length}</Badge>
            </div>
            <div className="space-y-2">
              {response.mapResults.slice(0, 10).map((result) => (
                <div key={`${result.name}-${result.position}`} className="rounded-lg border p-3 text-sm">
                  <div className="flex items-start justify-between gap-3">
                    <span className="font-medium">#{result.position ?? "–"} {result.name}</span>
                    <span className="text-xs font-medium text-zinc-500">
                      {result.rating ?? "–"} ★ · {result.reviewCount ?? 0} reviews
                    </span>
                  </div>
                  <p className="mt-1 text-xs font-medium text-zinc-500">{result.category}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </AccordionContent>
    </AccordionItem>
  )
}

export function AuditDashboard({ loaded }: { loaded: DashboardLoadResult }) {
  if (!loaded.ok) {
    return (
      <main className="grid min-h-svh place-items-center bg-zinc-100 p-6">
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle>Unable to load audit data</CardTitle>
            <CardDescription>{loaded.error}</CardDescription>
          </CardHeader>
        </Card>
      </main>
    )
  }

  const { audit, trackedPrompts } = loaded
  const view = buildAuditViewModel(audit, trackedPrompts)
  const { metrics } = view
  const invisible =
    metrics.availability.answers === metrics.promptCount &&
    metrics.availability.actualCitations === metrics.promptCount &&
    metrics.availability.searchSources === metrics.promptCount &&
    metrics.availability.maps === metrics.promptCount &&
    metrics.mentioned === 0 &&
    metrics.cited === 0 &&
    metrics.foundInSearch === 0 &&
    metrics.foundInMaps === 0
  const automaticActions = [
    {
      title: "Win the pages assistants already retrieve",
      summary: `Study the ${metrics.uniqueCitedPages} pages assistants actually cite, then publish stronger service, comparison, and proof pages for the same buyer intents.`,
      priority: "P0",
    },
    {
      title: "Build local authority",
      summary:
        metrics.availability.maps > 0
          ? `The brand appeared in ${metrics.foundInMaps}/${metrics.availability.maps} available prompt-level map sets. Strengthen the Google Business Profile, reviews, categories, local citations, and Paris service pages.`
          : "Map evidence was not provided, so local visibility is unknown. Validate the map collection before drawing a local-search conclusion.",
      priority: "P0",
    },
    {
      title: "Close the retrieval-to-answer gap",
      summary:
        metrics.availability.searchSources > 0
          ? `The domain appeared in captured search sources for ${metrics.foundInSearch}/${metrics.availability.searchSources} available prompts. Prioritize prompts where retrieval is close but the final answer still omits the brand.`
          : "Structured search-source evidence was not provided. Treat retrieval visibility as unknown until it is collected.",
      priority: "P1",
    },
  ]
  const recommendations = view.recommendations.length
    ? view.recommendations
    : automaticActions

  return (
    <main className="min-h-svh bg-zinc-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-7 px-4 py-7 sm:px-6 lg:px-8">
        <header className="overflow-hidden rounded-3xl border border-zinc-200 bg-white p-7 text-zinc-700 shadow-none sm:p-10">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-medium text-zinc-500">Geo visibility audit</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-zinc-700 sm:text-5xl">{view.brandName}</h1>
              <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <CircleAlert className="mt-0.5 size-5 shrink-0 text-amber-700" />
                <p className="font-medium leading-7 text-zinc-600">
                  {invisible
                    ? `The brand is currently invisible across all ${metrics.promptCount} tested buying prompts: no final-answer mentions, citations, search-source appearances, or map placements.`
                    : `The brand appears in ${metrics.mentioned}/${metrics.availability.answers} available prompt answers and is cited in ${metrics.cited}/${metrics.availability.actualCitations} prompts with reliable citation evidence. Missing evidence is reported as unknown.`}
                </p>
              </div>
            </div>
            <div className="text-sm font-medium text-zinc-500">
              <p>{formatDate(audit.run_at)}</p>
              <a className="mt-2 inline-flex items-center gap-2 font-semibold text-zinc-700" href={audit.check_url} target="_blank" rel="noreferrer">
                {audit.target_domains?.[0] || audit.check_url}
                <ArrowUpRight className="size-4" />
              </a>
            </div>
          </div>
        </header>

        <section>
          <div className="mb-4">
            <h2 className="text-xl font-semibold">Priority action plan</h2>
            <p className="mt-1 text-sm font-medium text-zinc-500">What to do next, before the underlying evidence.</p>
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            {recommendations.slice(0, 3).map((item) => (
              <Card key={item.title} className="border-border/75 shadow-none">
                <CardHeader>
                  <Badge variant="secondary" className="w-fit">{item.priority.replace("P", "Priority ")}</Badge>
                  <CardTitle className="text-base">{item.title}</CardTitle>
                  <CardDescription className="leading-6">{item.summary}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold">Opportunity funnel</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <FunnelStep label="Web searched" count={metrics.searched} total={metrics.availability.webSearch} />
            <FunnelStep label="Sources retrieved" count={metrics.retrieved} total={metrics.availability.searchSources} />
            <FunnelStep label="Map set shown" count={metrics.mapped} total={metrics.availability.maps} />
            <FunnelStep label="Brand mentioned" count={metrics.mentioned} total={metrics.availability.answers} />
            <FunnelStep label="Brand cited" count={metrics.cited} total={metrics.availability.actualCitations} />
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Actual citation appearances" value={metrics.availability.actualCitations > 0 ? `${metrics.actualCitationAppearances}` : "n/a"} detail={metrics.availability.actualCitations > 0 ? `${metrics.uniqueCitedPages} unique pages were truly cited.` : "Citation status was not provided reliably."} />
          <Metric label="Citation candidates" value={metrics.availability.citationCandidates > 0 ? `${metrics.candidateAppearances}` : "n/a"} detail={metrics.availability.citationCandidates > 0 ? `${metrics.uniqueCandidatePages} unique pages were captured as candidates.` : "Citation candidates were not provided reliably."} />
          <Metric label="Search-source records" value={metrics.availability.searchSources > 0 ? `${metrics.searchSourceAppearances}` : "n/a"} detail={metrics.availability.searchSources > 0 ? "Structured pages retrieved during web search." : "Structured search-source evidence was not provided."} />
          <Metric label="Map placements" value={metrics.availability.maps > 0 ? `${metrics.mapPlacements}` : "n/a"} detail={metrics.availability.maps > 0 ? "Local listings captured across all prompts." : "Map evidence was not provided."} />
        </section>

        <Card className="border-border bg-card shadow-none">
          <CardHeader>
            <CardTitle>Prompt matrix</CardTitle>
            <CardDescription>One row per buyer question. Green means the signal was present; red means it was absent.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-80">Prompt</TableHead>
                  <TableHead>Search</TableHead>
                  <TableHead>Brand in search</TableHead>
                  <TableHead>Brand in maps</TableHead>
                  <TableHead>Mention</TableHead>
                  <TableHead>Citation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {view.promptGroups.map((group) => (
                  <TableRow key={group.prompt}>
                    <TableCell className="font-medium leading-6">{group.prompt}</TableCell>
                    <TableCell><Signal value={group.searched} label={group.searched ? "Yes" : "No"} /></TableCell>
                    <TableCell><Signal value={group.foundInSearch} label={group.foundInSearch ? "Brand found" : "Brand absent"} /></TableCell>
                    <TableCell><Signal value={group.foundInMaps} label={group.foundInMaps ? "Brand found" : "Brand absent"} /></TableCell>
                    <TableCell><Signal value={group.mentioned} label={group.mentioned ? "Mentioned" : "Absent"} /></TableCell>
                    <TableCell><Signal value={group.cited} label={group.cited ? "Cited" : "Not cited"} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Tabs defaultValue="competition" className="space-y-5">
          <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border bg-white p-1">
            <TabsTrigger className="data-[state=active]:bg-zinc-200 data-[state=active]:text-zinc-700" value="competition">Competitive landscape</TabsTrigger>
            <TabsTrigger className="data-[state=active]:bg-zinc-200 data-[state=active]:text-zinc-700" value="local">Local visibility</TabsTrigger>
            <TabsTrigger className="data-[state=active]:bg-zinc-200 data-[state=active]:text-zinc-700" value="citations">Actual citations</TabsTrigger>
            <TabsTrigger className="data-[state=active]:bg-zinc-200 data-[state=active]:text-zinc-700" value="evidence">Evidence viewer</TabsTrigger>
            <TabsTrigger className="data-[state=active]:bg-zinc-200 data-[state=active]:text-zinc-700" value="method">Methodology</TabsTrigger>
          </TabsList>

          <TabsContent value="competition">
            <Card className="shadow-none">
              <CardHeader>
                <CardTitle>Competitors by evidence channel</CardTitle>
                <CardDescription>Answer recommendations, actual citations, captured candidates, search retrieval, and map results stay separate.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table>
                  <TableHeader><TableRow><TableHead>Entity</TableHead><TableHead>Prompt coverage</TableHead><TableHead>Channels</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {view.competitors.slice(0, 50).map((item) => (
                      <TableRow key={item.domain || item.name}>
                        <TableCell>
                          <p className="font-medium">{item.name}</p>
                          <p className="text-xs font-medium text-zinc-500">{item.domain}</p>
                        </TableCell>
                        <TableCell>{item.promptCount}/{metrics.promptCount}</TableCell>
                        <TableCell><div className="flex flex-wrap gap-1">{item.channels.map((channel) => <Badge key={channel} variant="outline">{channel.replaceAll("_", " ")}</Badge>)}</div></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="local">
            <Card className="shadow-none">
              <CardHeader>
                <div className="flex items-center gap-2"><MapPin className="size-5" /><CardTitle>Local map landscape</CardTitle></div>
                <CardDescription>Best position and prompt coverage across structured map results.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <Table>
                  <TableHeader><TableRow><TableHead>Business</TableHead><TableHead>Best position</TableHead><TableHead>Coverage</TableHead><TableHead>Rating</TableHead><TableHead>Reviews</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {view.mapGroups.map((item) => (
                      <TableRow key={item.domain || item.name}>
                        <TableCell>
                          {item.websiteUrl ? <a href={item.websiteUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium hover:underline">{item.name}<ExternalLink className="size-3" /></a> : <span className="font-medium">{item.name}</span>}
                          <p className="text-xs font-medium text-zinc-500">{item.category}</p>
                        </TableCell>
                        <TableCell>#{item.bestPosition ?? "–"}</TableCell>
                        <TableCell>{item.promptCount}/{metrics.promptCount}</TableCell>
                        <TableCell>{item.rating ?? "–"} ★</TableCell>
                        <TableCell>{item.reviewCount ?? "–"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="citations">
            <Card className="shadow-none">
              <CardHeader><CardTitle>Domains actually cited</CardTitle><CardDescription>Only records explicitly marked cited by the provider are included.</CardDescription></CardHeader>
              <CardContent className="space-y-4">
                {view.citedDomains.map((group) => (
                  <div key={group.domain} className="rounded-xl border p-4">
                    <div className="flex items-center justify-between gap-3"><h3 className="font-medium">{group.domain}</h3><Badge variant="secondary">{group.appearances} appearances</Badge></div>
                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      {group.pages.map((page) => <a key={page.url} href={page.url} target="_blank" rel="noreferrer" className="truncate text-sm font-medium text-zinc-500 hover:text-zinc-700 hover:underline">{page.title || page.url}</a>)}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="evidence">
            <Accordion type="multiple" className="space-y-3">
              {view.responses.map((response) => <Evidence key={`${response.chatbot}-${response.prompt}`} response={response} />)}
            </Accordion>
          </TabsContent>

          <TabsContent value="method">
            <Card className="shadow-none">
              <CardHeader><CardTitle>Methodology and collection status</CardTitle></CardHeader>
              <CardContent className="grid gap-4 text-sm font-medium text-zinc-500 md:grid-cols-2">
                <div className="rounded-xl border p-4"><p className="font-medium text-foreground">Contract</p><p className="mt-2">{audit.schema_version || "legacy"} · {audit.provider || "unknown provider"} · {audit.provider_method || "unknown method"}</p></div>
                <div className="rounded-xl border p-4"><p className="font-medium text-foreground">Collection</p>{audit.snapshots.map((snapshot) => <p key={snapshot.chatbot} className="mt-2">{snapshot.chatbot}: {snapshot.status} ({snapshot.collection_method || "snapshot"})</p>)}</div>
                <div className="rounded-xl border p-4 md:col-span-2"><div className="flex items-center gap-2 font-medium text-foreground"><Search className="size-4" />Signal definitions</div><p className="mt-2 leading-6"><strong>Web searched</strong> uses the provider’s canonical <code>web_search_triggered</code> signal. <strong>Actual citations</strong> include only citation records marked <code>cited: true</code>. Search sources, attached links, uncited candidates, and maps are reported separately.</p></div>
                <div className="rounded-xl border p-4 md:col-span-2">
                  <p className="font-medium text-foreground">Normalization diagnostics</p>
                  <p className="mt-2 leading-6">
                    Status: {view.diagnostics?.status || "not reported"} ·{" "}
                    {view.diagnostics?.records_normalized ?? view.responses.length} normalized ·{" "}
                    {view.diagnostics?.records_rejected ?? 0} rejected ·{" "}
                    {view.diagnostics?.warning_count ?? 0} warnings.
                  </p>
                  {view.diagnostics?.unknown_provider_fields?.length ? (
                    <p className="mt-2 leading-6">
                      Preserved unknown provider fields:{" "}
                      {view.diagnostics.unknown_provider_fields.join(", ")}.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
