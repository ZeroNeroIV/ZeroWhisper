import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '@/lib/api'
import { TabList, Tab, Card, Button, Input, Tooltip as FluentTooltip } from '@fluentui/react-components'
import { Play, Pause, Timer } from 'lucide-react'
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
    <div className="flex items-center justify-center h-64 text-red-600">
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

const TAB_TITLES: Record<TabKey, string> = {
  'cash-flow': 'Cash Flow',
  sankey: 'Income vs. Spending',
  'burn-rate': 'Burn Rate Heatmap',
  'net-worth': 'Net Worth Trend',
}

const TAB_KEYS = Object.keys(TAB_LABELS) as TabKey[]

export default function VisualizationsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('cash-flow')
  const [visited, setVisited] = useState<Set<TabKey>>(new Set(['cash-flow']))

  const [autoPlay, setAutoPlay] = useState(false)
  const [interval, setIntervalSecs] = useState(5)
  const [intervalInput, setIntervalInput] = useState('5')
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const goToTab = useCallback((tab: TabKey) => {
    setActiveTab(tab)
    setVisited(prev => new Set([...prev, tab]))
  }, [])

  const handleTabChange = useCallback((_: unknown, d: { value: unknown }) => {
    goToTab(d.value as TabKey)
  }, [goToTab])

  // Auto-advance timer
  useEffect(() => {
    if (!autoPlay) {
      if (intervalRef.current) clearTimeout(intervalRef.current)
      return
    }
    intervalRef.current = setTimeout(() => {
      setActiveTab(prev => {
        const idx = TAB_KEYS.indexOf(prev)
        const next = TAB_KEYS[(idx + 1) % TAB_KEYS.length]
        setVisited(v => new Set([...v, next]))
        return next
      })
    }, interval * 1000)
    return () => { if (intervalRef.current) clearTimeout(intervalRef.current) }
  }, [autoPlay, activeTab, interval])

  const handleIntervalChange = (val: string) => {
    setIntervalInput(val)
    const n = parseInt(val, 10)
    if (!isNaN(n) && n >= 1 && n <= 60) setIntervalSecs(n)
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-4 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Visualizations</h1>
          <p className="text-muted-foreground text-sm mt-0.5">{TAB_DESCRIPTIONS[activeTab]}</p>
        </div>

        {/* Auto-play controls */}
        <div className="flex items-center gap-2 shrink-0">
          <Timer size={15} className="text-muted-foreground" />
          <Input
            type="number"
            value={intervalInput}
            onChange={e => handleIntervalChange(e.target.value)}
            min={1}
            max={60}
            style={{ width: '60px' }}
            contentAfter={<span className="text-xs text-muted-foreground">s</span>}
            disabled={autoPlay}
          />
          <FluentTooltip content={autoPlay ? 'Stop auto-advance' : 'Auto-advance tabs'} relationship="label">
            <Button
              appearance={autoPlay ? 'primary' : 'outline'}
              icon={autoPlay ? <Pause size={15} /> : <Play size={15} />}
              onClick={() => setAutoPlay(p => !p)}
            >
              {autoPlay ? 'Stop' : 'Auto'}
            </Button>
          </FluentTooltip>
        </div>
      </div>

      <div className="overflow-x-auto -mx-1 px-1 mb-4">
        <TabList selectedValue={activeTab} onTabSelect={handleTabChange} className="flex-nowrap">
          {TAB_KEYS.map((key) => (
            <Tab key={key} value={key}>{TAB_LABELS[key]}</Tab>
          ))}
        </TabList>
      </div>

      <Card className="p-4">
        <h2 className="text-base font-semibold mb-4">{TAB_TITLES[activeTab]}</h2>
        {activeTab === 'cash-flow' && visited.has('cash-flow') && <CashFlowTab />}
        {activeTab === 'sankey' && visited.has('sankey') && <SankeyTab />}
        {activeTab === 'burn-rate' && visited.has('burn-rate') && <HeatmapTab />}
        {activeTab === 'net-worth' && visited.has('net-worth') && <NetWorthTab />}
      </Card>
    </div>
  )
}
