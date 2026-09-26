"use client"

import {
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleAlert,
  ExternalLink,
  MapPin,
  Search,
  X,
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Fragment, useState } from "react"

import {
  buildAuditViewModel,
  type AuditFileRecord,
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
    : new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }).format(date)
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
            empty={["supported", "inferred"].includes(response.evidenceStatus.citationCandidates) ? "No uncited citation candidates were captured." : "Citation candidate data was not provided."}
          />
          <SourceList
            title="Captured search sources"
            sources={response.searchSources}
            empty={["supported", "inferred"].includes(response.evidenceStatus.searchSources) ? "No structured search sources were captured." : "Search source data was not provided."}
          />
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Map placements</h4>
              <Badge variant="secondary">{["supported", "inferred"].includes(response.evidenceStatus.maps) ? response.mapResults.length : "n/a"}</Badge>
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
        {response.fanOutQueries.length > 0 && <section>
          <h4 className="mb-2 text-sm font-medium">Search queries generated by the assistant</h4>
          <ul className="list-inside list-disc space-y-1 text-sm text-zinc-600">{response.fanOutQueries.map((query, index) => <li key={`${query}-${index}`}>{query}</li>)}</ul>
        </section>}
        {response.attachedLinks.length > 0 && <section>
          <h4 className="mb-2 text-sm font-medium">Links attached to the answer</h4>
          <ul className="space-y-1 text-sm">{response.attachedLinks.map((link, index) => <li key={`${link.url}-${index}`}><a href={link.url} target="_blank" rel="noreferrer" className="text-zinc-600 underline">{link.text || link.url}</a></li>)}</ul>
        </section>}
      </AccordionContent>
    </AccordionItem>
  )
}

function MentionTrend({ history }: { history: Array<{ run: AuditFileRecord; view: ReturnType<typeof buildAuditViewModel> }> }) {
  const points = history.flatMap(({ run, view }, index) => {
    const total = view.metrics.availability.answers
    if (!total) return []
    return [{
      index,
      date: formatDate(run.run_at),
      mentions: view.metrics.mentioned,
      total,
      rate: view.metrics.mentioned / total,
    }]
  })
  const left = 56
  const right = 606
  const top = 36
  const bottom = 204
  const coordinates = points.map((point, pointIndex) => ({
    ...point,
    x: points.length === 1 ? (left + right) / 2 : left + (pointIndex / (points.length - 1)) * (right - left),
    y: bottom - point.rate * (bottom - top),
  }))
  const dateLabels = new Set([0, Math.floor((coordinates.length - 1) / 2), coordinates.length - 1])

  return (
    <Card className="h-full shadow-none">
      <CardHeader className="pb-1">
        <CardTitle className="text-base">Mention rate by run</CardTitle>
        <CardDescription>Share of answers with a brand mention. Hover a point for its count.</CardDescription>
      </CardHeader>
      <CardContent>
        {!coordinates.length ? <p className="py-16 text-center text-sm text-zinc-500">No runs have reliable answer evidence yet.</p> : <>
          <svg viewBox="0 0 640 260" className="w-full" role="img" aria-label={`Brand mention rate across ${points.length} runs`}>
            {[0, 0.5, 1].map((rate) => {
              const y = bottom - rate * (bottom - top)
              return <g key={rate}><line x1={left} y1={y} x2={right} y2={y} stroke="#e4e4e7" strokeDasharray={rate === 0 ? undefined : "4 5"} /><text x="4" y={y + 4} fill="#71717a" fontSize="12">{Math.round(rate * 100)}%</text></g>
            })}
            {coordinates.length > 1 && <polyline points={coordinates.map(({ x, y }) => `${x},${y}`).join(" ")} fill="none" stroke="#2563eb" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
            {coordinates.map((point, index) => <g key={`${point.date}-${index}`}>
              <circle cx={point.x} cy={point.y} r="6" fill="#2563eb" stroke="white" strokeWidth="2"><title>{point.date}: {point.mentions}/{point.total} answers ({Math.round(point.rate * 100)}%)</title></circle>
              {dateLabels.has(index) && <text x={point.x} y="235" fill="#71717a" fontSize="11" textAnchor="middle">{point.date}</text>}
              {coordinates.length <= 5 && <text x={point.x} y={Math.max(top - 8, point.y - 12)} fill="#3f3f46" fontSize="11" fontWeight="600" textAnchor="middle">{point.mentions}/{point.total}</text>}
            </g>)}
          </svg>
          {points.length === 1 && <p className="text-center text-xs text-zinc-500">One run so far. New audits will extend this trend.</p>}
        </>}
      </CardContent>
    </Card>
  )
}

const llmTab = (chatbot: string) => {
  const value = chatbot.toLowerCase()
  if (value === "gpt" || value.includes("chatgpt")) return "gpt"
  if (value.includes("perplexity")) return "perplexity"
  return value.replace(/[^a-z0-9-]+/g, "-")
}

const llmLabel = (key: string) => {
  if (key === "gpt") return "GPT"
  if (key === "perplexity") return "Perplexity"
  return key.charAt(0).toUpperCase() + key.slice(1)
}

function PromptLlmTabs({ group }: { group: ReturnType<typeof buildAuditViewModel>["promptGroups"][number] }) {
  const responsesByLlm = new Map<string, ResponseRecord[]>()
  for (const response of group.responses) {
    const key = llmTab(response.chatbot)
    responsesByLlm.set(key, [...(responsesByLlm.get(key) ?? []), response])
  }
  const llms = ["gpt", "perplexity", ...[...responsesByLlm.keys()].filter((key) => key !== "gpt" && key !== "perplexity")]

  return (
    <div className="space-y-4">
      <p className="text-sm font-medium text-zinc-700">{group.prompt}</p>
      <Tabs key={group.prompt} defaultValue="gpt" className="space-y-4">
        <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border bg-white p-1">
          {llms.map((llm) => <TabsTrigger key={llm} value={llm}>{llmLabel(llm)}</TabsTrigger>)}
        </TabsList>
        {llms.map((llm) => {
          const responses = responsesByLlm.get(llm) ?? []
          return <TabsContent key={llm} value={llm} className="space-y-6 rounded-xl border bg-white p-4 sm:p-6">
            {responses.length ? responses.map((response, index) => <div key={`${response.chatbot}-${index}`} className="space-y-6">
              {responses.length > 1 && <h4 className="font-medium">Response {index + 1}</h4>}
              <section>
                <h4 className="mb-2 text-sm font-semibold">Query</h4>
                <p className="rounded-lg bg-zinc-50 p-3 text-sm leading-6">{response.prompt}</p>
                <div className="mt-3">
                  <p className="text-sm font-medium">Fan queries <span className="text-zinc-500">({["supported", "inferred"].includes(response.evidenceStatus.fanOutQueries) ? response.fanOutQueries.length : "n/a"})</span></p>
                  {response.fanOutQueries.length ? <ul className="mt-2 list-inside list-disc space-y-1 text-sm leading-6 text-zinc-600">{response.fanOutQueries.map((query, queryIndex) => <li key={`${query}-${queryIndex}`}>{query}</li>)}</ul> : <p className="mt-1 text-sm text-zinc-500">{["supported", "inferred"].includes(response.evidenceStatus.fanOutQueries) ? "No fan queries were captured." : "Fan query data was not provided."}</p>}
                </div>
              </section>
              <section>
                <h4 className="mb-2 text-sm font-semibold">Citations</h4>
                <SourceList title="Confirmed citations" sources={response.actualCitations} empty={["supported", "inferred"].includes(response.evidenceStatus.actualCitations) ? "No confirmed citation in this answer." : "Citation status was not provided reliably."} />
                {response.citationCandidates.length > 0 && <details className="mt-3"><summary className="cursor-pointer text-sm font-medium">Citation candidates ({response.citationCandidates.length}, not all confirmed)</summary><div className="mt-3"><SourceList title="Candidates" sources={response.citationCandidates} empty="No citation candidates captured." /></div></details>}
              </section>
              <section>
                <h4 className="mb-2 text-sm font-semibold">Generated answer</h4>
                {response.answerMarkdown ? <div className="prose max-w-none rounded-xl border bg-zinc-50 p-5 text-sm leading-7"><ReactMarkdown remarkPlugins={[remarkGfm]}>{response.answerMarkdown}</ReactMarkdown></div> : <p className="text-sm text-zinc-500">The generated answer was not provided.</p>}
              </section>
            </div>) : <p className="py-8 text-center text-sm text-zinc-500">No {llmLabel(llm)} response was collected for this prompt in the selected run.</p>}
          </TabsContent>
        })}
      </Tabs>
    </div>
  )
}

export function AuditDashboard({ loaded }: { loaded: DashboardLoadResult }) {
  const [selectedRun, setSelectedRun] = useState(loaded.ok ? loaded.runs.length - 1 : 0)
  const [expandedPrompt, setExpandedPrompt] = useState<string | null>(null)
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

  const { trackedPrompts, runs, analysis } = loaded
  const audit = runs[selectedRun] ?? loaded.audit
  const view = buildAuditViewModel(audit, trackedPrompts)
  const history = runs.map((run) => ({ run, view: buildAuditViewModel(run, trackedPrompts) }))
  const historicalPrompts = [...new Set(history.flatMap(({ view: item }) => item.promptGroups.map((group) => group.prompt)))]
  const { metrics } = view
  const totals = history.reduce((sum, { view: item }) => ({
    responses: sum.responses + item.responses.length,
    answers: sum.answers + item.metrics.availability.answers,
    mentions: sum.mentions + item.metrics.mentioned,
  }), { responses: 0, answers: 0, mentions: 0 })
  const chatbotHistory = new Map<string, { responses: number; answers: number; mentions: number; citationEvidence: number; citations: number }>()
  for (const { view: item } of history) {
    for (const response of item.responses) {
      const current = chatbotHistory.get(response.chatbot) ?? { responses: 0, answers: 0, mentions: 0, citationEvidence: 0, citations: 0 }
      current.responses += 1
      if (["supported", "inferred"].includes(response.evidenceStatus.answer)) {
        current.answers += 1
        if (response.mentions > 0) current.mentions += 1
      }
      if (["supported", "inferred"].includes(response.evidenceStatus.actualCitations)) {
        current.citationEvidence += 1
        if (response.cited) current.citations += 1
      }
      chatbotHistory.set(response.chatbot, current)
    }
  }

  return (
    <main className="min-h-svh bg-zinc-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-7 px-4 py-7 sm:px-6 lg:px-8">
        <header className="overflow-hidden rounded-3xl border border-zinc-200 bg-white p-7 text-zinc-700 shadow-none sm:p-10">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-medium text-zinc-500">Geo visibility audit · {runs.length} {runs.length === 1 ? "run" : "runs"}</p>
              <h1 className="mt-4 text-4xl font-semibold tracking-tight text-zinc-700 sm:text-5xl">{view.brandName}</h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-600">{analysis?.overview ?? "Explore the audit results and evidence below."}</p>
            </div>
            <div className="text-sm font-medium text-zinc-500">
              <p>{formatDate(runs[0].run_at)} to {formatDate(runs[runs.length - 1].run_at)}</p>
              <a className="mt-2 inline-flex items-center gap-2 font-semibold text-zinc-700" href={loaded.audit.check_url} target="_blank" rel="noreferrer">
                {loaded.audit.target_domains?.[0] || loaded.audit.check_url}
                <ArrowUpRight className="size-4" />
              </a>
            </div>
          </div>
        </header>

        {analysis && <section>
          <div className="mb-4">
            <h2 className="text-xl font-semibold">Priority action plan</h2>
            <p className="mt-1 text-sm text-zinc-500">One plan, reviewed across all runs through {formatDate(analysis.through_run_at)}.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {analysis.recommendations.map((item) => <Card key={item.title} className="shadow-none"><CardHeader>
              <Badge variant="secondary" className="w-fit">{item.priority}</Badge>
              <CardTitle className="text-base">{item.title}</CardTitle>
              <CardDescription className="leading-6">{item.summary}</CardDescription>
              <p className="pt-2 text-xs leading-5 text-zinc-500">Evidence: {item.evidence}</p>
            </CardHeader></Card>)}
          </div>
        </section>}

        <section className="rounded-2xl border border-zinc-200 bg-white p-5 sm:p-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Across all runs</h2>
              <p className="mt-1 text-sm text-zinc-500">Measured history across the complete audit record.</p>
            </div>
          </div>
          <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
            <div className="grid gap-3 sm:grid-cols-2">
              <Metric label="Runs" value={`${runs.length}`} detail="Completed audits in this report." />
              <Metric label="Prompts tracked" value={`${historicalPrompts.length}`} detail="Distinct prompt texts across all runs." />
              <Metric label="Final answers" value={`${totals.answers}/${totals.responses}`} detail="Responses with answer evidence." />
              <Metric label="Brand mentions" value={`${totals.mentions}/${totals.answers}`} detail="Answer appearances across all runs." />
            </div>
            <MentionTrend history={history} />
          </div>
          {analysis && <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4"><h3 className="font-semibold">What changed</h3><ul className="mt-3 list-inside list-disc space-y-2 text-sm leading-6 text-zinc-600">{analysis.findings.map((finding) => <li key={finding}>{finding}</li>)}</ul></div>
            <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4"><h3 className="font-semibold">How to compare these runs</h3><p className="mt-3 text-sm leading-6 text-zinc-600">{analysis.comparison_note}</p></div>
          </div>}
          <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="border-b text-zinc-500"><tr><th className="py-2 pr-4">Run</th><th className="py-2 pr-4">Chatbots</th><th className="py-2 pr-4">Prompts</th><th className="py-2 pr-4">Search</th><th className="py-2 pr-4">Retrieval</th><th className="py-2 pr-4">Maps</th><th className="py-2 pr-4">Mentions</th><th className="py-2 pr-4">Brand cited</th><th className="py-2">Collection</th></tr></thead>
                <tbody>{history.map(({ run, view: item }, index) => <tr key={`${run.run_at}-${index}`} className="border-b last:border-0"><td className="py-3 pr-4">{formatDate(run.run_at)}</td><td className="py-3 pr-4">{[...new Set(item.responses.map((response) => response.chatbot))].join(", ")}</td><td className="py-3 pr-4">{item.metrics.promptCount}</td><td className="py-3 pr-4">{item.metrics.searched}/{item.metrics.availability.webSearch}</td><td className="py-3 pr-4">{item.metrics.retrieved}/{item.metrics.availability.searchSources}</td><td className="py-3 pr-4">{item.metrics.mapped}/{item.metrics.availability.maps}</td><td className="py-3 pr-4">{item.metrics.mentioned}/{item.metrics.availability.answers}</td><td className="py-3 pr-4">{item.metrics.cited}/{item.metrics.availability.actualCitations}</td><td className="py-3">{run.collection_diagnostics?.status ?? "Not reported"}</td></tr>)}</tbody>
              </table>
              <p className="mt-3 text-xs leading-5 text-zinc-500">Counts are response-level. Denominators include responses with available evidence.</p>
              <div className="mt-5 border-t pt-4"><h3 className="font-medium">By chatbot, all runs combined</h3><div className="mt-3 overflow-x-auto"><table className="w-full min-w-[500px] text-left text-sm"><thead className="border-b text-zinc-500"><tr><th className="py-2">Chatbot</th><th className="py-2">Responses</th><th className="py-2">Mentions</th><th className="py-2">Brand cited</th></tr></thead><tbody>{[...chatbotHistory].map(([chatbot, row]) => <tr key={chatbot} className="border-b last:border-0"><td className="py-2">{chatbot}</td><td className="py-2">{row.responses}</td><td className="py-2">{row.mentions}/{row.answers}</td><td className="py-2">{row.citations}/{row.citationEvidence}</td></tr>)}</tbody></table></div></div>
              {runs.length > 1 &&
              <details className="mt-5 border-t pt-4">
                <summary className="cursor-pointer font-medium">Prompt history</summary>
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-sm">
                    <thead className="border-b text-zinc-500"><tr><th className="min-w-80 py-2 pr-4">Prompt</th>{runs.map((run, index) => <th key={`${run.run_at}-${index}`} className="min-w-28 py-2 pr-4">{formatDate(run.run_at)}</th>)}</tr></thead>
                    <tbody>{historicalPrompts.map((prompt) => <tr key={prompt} className="border-b last:border-0"><td className="py-3 pr-4">{prompt}</td>{history.map(({ run, view: item }, index) => {
                      const group = item.promptGroups.find((candidate) => candidate.prompt === prompt)
                      return <td key={`${run.run_at}-${index}`} className="py-3 pr-4 whitespace-nowrap">{group ? `Mention ${group.mentioned === null ? "?" : group.mentioned ? "yes" : "no"} · Cite ${group.cited === null ? "?" : group.cited ? "yes" : "no"}` : "Not tested"}</td>
                    })}</tr>)}</tbody>
                  </table>
                </div>
              </details>}
          </div>
        </section>

        <section className="flex flex-wrap items-end justify-between gap-4 border-t border-zinc-300 pt-7">
          <div><p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Run detail</p><h2 className="mt-1 text-xl font-semibold">Evidence for {formatDate(audit.run_at)}</h2><p className="mt-1 text-sm text-zinc-500">The sections below show one run at a time.</p></div>
          <label className="text-sm font-medium">Choose a run <select className="ml-2 rounded-lg border border-zinc-300 bg-white px-3 py-2" value={selectedRun} onChange={(event) => setSelectedRun(Number(event.target.value))}>{runs.map((run, index) => <option key={`${run.run_at}-${index}`} value={index}>{formatDate(run.run_at)}</option>)}</select></label>
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
            <CardDescription>Click a prompt to inspect queries, citations, and the answer for each model.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-80">Prompt</TableHead>
                  <TableHead>Search</TableHead>
                  <TableHead>Fan queries</TableHead>
                  <TableHead>Brand in search</TableHead>
                  <TableHead>Brand in maps</TableHead>
                  <TableHead>Mention</TableHead>
                  <TableHead>Citation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {view.promptGroups.map((group) => {
                  const isExpanded = expandedPrompt === group.prompt
                  return <Fragment key={group.prompt}>
                    <TableRow aria-expanded={isExpanded}>
                      <TableCell className="min-w-80 whitespace-normal font-medium leading-6"><button type="button" aria-expanded={isExpanded} onClick={() => setExpandedPrompt(isExpanded ? null : group.prompt)} className="flex w-full items-start justify-between gap-3 text-left focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"><span>{group.prompt}</span><ChevronDown className={`mt-1 size-4 shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`} /></button></TableCell>
                      <TableCell><Signal value={group.searched} label={group.searched ? "Yes" : "No"} /></TableCell>
                      <TableCell className="text-center font-semibold">{group.fanOutQueryCount ?? "n/a"}</TableCell>
                      <TableCell><Signal value={group.foundInSearch} label={group.foundInSearch ? "Brand found" : "Brand absent"} /></TableCell>
                      <TableCell><Signal value={group.foundInMaps} label={group.foundInMaps ? "Brand found" : "Brand absent"} /></TableCell>
                      <TableCell><Signal value={group.mentioned} label={group.mentioned ? "Mentioned" : "Absent"} /></TableCell>
                      <TableCell><Signal value={group.cited} label={group.cited ? "Cited" : "Not cited"} /></TableCell>
                    </TableRow>
                    {isExpanded && <TableRow><TableCell colSpan={7} className="whitespace-normal bg-zinc-50 p-5"><PromptLlmTabs group={group} /></TableCell></TableRow>}
                  </Fragment>
                })}
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
        <footer className="pb-4 text-center text-xs text-zinc-500"><a href="https://holly-and-stick.com" className="hover:underline">holly-and-stick.com</a></footer>
      </div>
    </main>
  )
}
