import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
  ResponsiveContainer,
  Sankey,
} from 'recharts'

// ── Types ──────────────────────────────────────────────────────────────────

interface CashFlowDay {
  date: string
  income: number
  expenses: number
  balance: number
}

interface SankeyNode {
  name: string
}

interface SankeyLink {
  source: number
  target: number
  value: number
}

interface SankeyData {
  nodes: SankeyNode[]
  links: SankeyLink[]
  total_income: number
}

interface HeatmapRow {
  day: number
  category: string
  amount: number
}

interface NetWorthPoint {
  month: string
  net_worth: number
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })
}

// ── Sub-components ─────────────────────────────────────────────────────────

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-64 text-muted-foreground">
      Loading...
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-destructive">
      {message}
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-muted-foreground">
      {message}
    </div>
  )
}

// ── Cash Flow Tab ──────────────────────────────────────────────────────────

function CashFlowTab() {
  const [data, setData] = useState<CashFlowDay[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<CashFlowDay[]>('/api/analytics/cash-flow')
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!data || data.length === 0)
    return <EmptyState message="No transaction data for this period." />

  const chartData = data.map((d) => ({ ...d, date: formatDate(d.date) }))

  return (
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => [`${Number(value).toFixed(2)} JOD`]} />
        <Legend />
        <Bar dataKey="income" name="Income" fill="#22c55e" />
        <Bar dataKey="expenses" name="Expenses" fill="#ef4444" />
        <Line
          type="monotone"
          dataKey="balance"
          name="Balance"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

// ── Sankey Tab ─────────────────────────────────────────────────────────────

function SankeyTab() {
  const [data, setData] = useState<SankeyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<SankeyData>('/api/analytics/sankey')
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!data || data.links.length === 0)
    return <EmptyState message="No data for this month." />

  return (
    <div className="w-full">
      <p className="text-sm text-muted-foreground mb-4">
        Total income this month:{' '}
        <span className="font-semibold text-foreground">
          {data.total_income.toFixed(2)} JOD
        </span>
      </p>
      <ResponsiveContainer width="100%" height={400}>
        {/* @ts-ignore recharts Sankey has complex internal typing */}
        <Sankey
          data={{ nodes: data.nodes, links: data.links }}
          nodePadding={20}
          nodeWidth={10}
          margin={{ top: 10, right: 80, bottom: 10, left: 80 }}
          link={{ stroke: '#93c5fd', fill: '#93c5fd', fillOpacity: 0.4 }}
          node={{ fill: '#3b82f6', stroke: '#1d4ed8' }}
        >
          <Tooltip
            formatter={(value) => [`${Number(value).toFixed(2)} JOD`, 'Amount']}
          />
        </Sankey>
      </ResponsiveContainer>
    </div>
  )
}

// ── Burn Rate / Heatmap Tab ────────────────────────────────────────────────

function HeatmapTab() {
  const [data, setData] = useState<HeatmapRow[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<HeatmapRow[]>('/api/analytics/heatmap')
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!data || data.length === 0)
    return <EmptyState message="No spending data for this month." />

  // Build a lookup: category -> day -> amount
  const categories = [...new Set(data.map((r) => r.category))].sort()
  const days = Array.from({ length: 31 }, (_, i) => i + 1)

  const lookup = new Map<string, number>()
  for (const row of data) {
    lookup.set(`${row.category}:${row.day}`, row.amount)
  }

  const maxAmount = Math.max(...data.map((r) => r.amount), 1)

  function cellBackground(amount: number): string {
    if (amount === 0) return 'transparent'
    const intensity = (amount / maxAmount) * 60
    return `hsl(0, 70%, ${100 - intensity}%)`
  }

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse min-w-full">
        <thead>
          <tr>
            <th className="text-left px-2 py-1 font-medium text-muted-foreground sticky left-0 bg-background z-10">
              Category
            </th>
            {days.map((d) => (
              <th
                key={d}
                className="px-1 py-1 font-normal text-muted-foreground text-center min-w-[28px]"
              >
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {categories.map((cat) => (
            <tr key={cat}>
              <td className="px-2 py-1 font-medium whitespace-nowrap sticky left-0 bg-background z-10 border-r">
                {cat}
              </td>
              {days.map((d) => {
                const amount = lookup.get(`${cat}:${d}`) ?? 0
                return (
                  <td
                    key={d}
                    className="p-0.5"
                    title={amount > 0 ? `${amount.toFixed(2)} JOD` : undefined}
                  >
                    <div
                      className="w-6 h-6 rounded-sm mx-auto"
                      style={{ backgroundColor: cellBackground(amount) }}
                    />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-muted-foreground mt-3">
        Darker red = higher spending. Hover a cell to see the amount.
      </p>
    </div>
  )
}

// ── Net Worth Tab ──────────────────────────────────────────────────────────

function NetWorthTab() {
  const [data, setData] = useState<NetWorthPoint[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<NetWorthPoint[]>('/api/analytics/net-worth')
      .then((r) => setData(r.data))
      .catch(() => setError('Failed to load data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />
  if (!data || data.length === 0)
    return (
      <EmptyState message="No data yet. Add transactions to see net worth trend." />
    )

  return (
    <ResponsiveContainer width="100%" height={350}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
        <defs>
          <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => [`${Number(value).toFixed(2)} JOD`]} />
        <Area
          type="monotone"
          dataKey="net_worth"
          name="Net Worth"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#netWorthGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────

type TabKey = 'cash-flow' | 'sankey' | 'burn-rate' | 'net-worth'

const TAB_LABELS: Record<TabKey, string> = {
  'cash-flow': 'Cash Flow',
  sankey: 'Sankey',
  'burn-rate': 'Burn Rate',
  'net-worth': 'Net Worth',
}

const TAB_DESCRIPTIONS: Record<TabKey, string> = {
  'cash-flow': 'Daily income, expenses, and running balance',
  sankey: 'How income flows into spending categories this month',
  'burn-rate': 'Spending intensity by day and category this month',
  'net-worth': 'Cumulative net worth over time',
}

export default function VisualizationsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('cash-flow')
  // Track which tabs have been visited so we lazy-mount their data fetchers
  const [visited, setVisited] = useState<Set<TabKey>>(new Set(['cash-flow']))

  const handleTabChange = useCallback((value: string) => {
    const tab = value as TabKey
    setActiveTab(tab)
    setVisited((prev) => new Set([...prev, tab]))
  }, [])

  return (
    <div className="container mx-auto py-8 px-4 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Visualizations</h1>
        <p className="text-muted-foreground mt-1">
          {TAB_DESCRIPTIONS[activeTab]}
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-6">
          {(Object.keys(TAB_LABELS) as TabKey[]).map((key) => (
            <TabsTrigger key={key} value={key}>
              {TAB_LABELS[key]}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="cash-flow">
          <Card>
            <CardHeader>
              <CardTitle>Cash Flow</CardTitle>
            </CardHeader>
            <CardContent>
              {visited.has('cash-flow') && <CashFlowTab />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sankey">
          <Card>
            <CardHeader>
              <CardTitle>Income vs. Spending</CardTitle>
            </CardHeader>
            <CardContent>
              {visited.has('sankey') && <SankeyTab />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="burn-rate">
          <Card>
            <CardHeader>
              <CardTitle>Burn Rate Heatmap</CardTitle>
            </CardHeader>
            <CardContent>
              {visited.has('burn-rate') && <HeatmapTab />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="net-worth">
          <Card>
            <CardHeader>
              <CardTitle>Net Worth Trend</CardTitle>
            </CardHeader>
            <CardContent>
              {visited.has('net-worth') && <NetWorthTab />}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
