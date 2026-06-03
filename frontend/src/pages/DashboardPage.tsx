import { useEffect, useState, useCallback } from 'react'
import { api } from '@/lib/api'
import { Card } from '@fluentui/react-components'
import { Wallet, TrendingDown, TrendingUp, PiggyBank } from 'lucide-react'
import { useCategories } from '@/hooks/useCategories'
import type { Category } from '@/types/category'

interface DashboardSummary {
  balance_jod: number
  month_spending_jod: number
  month_income_jod: number
  total_savings_jod: number
  month_savings_jod: number
  recent_transactions: Array<{
    id: string
    category: string
    description: string | null
    amount_original: number
    currency_original: string
    transaction_date: string
  }>
}

function renderCategoryLabel(categoryName: string, categories: Category[]): React.ReactNode {
  const cat = categories.find((c) => c.name === categoryName)
  const color = cat?.color
  const icon = cat?.icon

  const textEl = (() => {
    if (!color) return <span className="text-xs font-medium text-muted-foreground">{categoryName}</span>
    if (color.startsWith('animated:')) {
      const gradient = color.slice('animated:'.length)
      return (
        <span className="text-xs font-medium animate-gradient" style={{ background: gradient, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}>
          {categoryName}
        </span>
      )
    }
    if (color.startsWith('linear-gradient') || color.startsWith('radial-gradient')) {
      return (
        <span className="text-xs font-medium" style={{ background: color, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}>
          {categoryName}
        </span>
      )
    }
    return <span className="text-xs font-medium" style={{ color }}>{categoryName}</span>
  })()

  if (icon) {
    return (
      <>
        <span className="inline md:hidden text-base">{icon}</span>
        <span className="hidden md:inline">{textEl}</span>
      </>
    )
  }
  return textEl
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { categories, fetchCategories } = useCategories()

  useEffect(() => { fetchCategories() }, [fetchCategories])

  const fetchSummary = useCallback(() => {
    api
      .get<DashboardSummary>('/api/dashboard/summary')
      .then(({ data }) => setSummary(data))
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchSummary()
    const handler = () => fetchSummary()
    window.addEventListener('transaction-created', handler)
    return () => window.removeEventListener('transaction-created', handler)
  }, [fetchSummary])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-600">
        {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Balance</span>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold">
            {summary?.balance_jod.toFixed(2)} JOD
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">
              This Month Spending
            </span>
            <TrendingDown className="h-4 w-4 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-500">
            {summary?.month_spending_jod.toFixed(2)} JOD
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">
              This Month Income
            </span>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-green-500">
            {summary?.month_income_jod.toFixed(2)} JOD
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex flex-row items-center justify-between pb-2">
            <span className="text-sm font-medium text-muted-foreground">Total Savings</span>
            <PiggyBank className="h-4 w-4 text-cyan-500" />
          </div>
          <p className="text-2xl font-bold text-cyan-600">
            {summary?.total_savings_jod.toFixed(2)} JOD
          </p>
          {summary && summary.month_savings_jod > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              +{summary.month_savings_jod.toFixed(2)} JOD this month
            </p>
          )}
        </Card>
      </div>

      {/* Recent transactions */}
      <Card className="p-4">
        <h2 className="text-base font-semibold mb-4">Recent Transactions</h2>
        {!summary || summary.recent_transactions.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No transactions yet. Add some from the Transactions page.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {summary.recent_transactions.map((tx) => (
              <li key={tx.id} className="flex items-center gap-4 py-3 text-sm">
                <span className="w-24 shrink-0 text-muted-foreground">{tx.transaction_date}</span>
                {renderCategoryLabel(tx.category, categories)}
                <span className="flex-1 truncate text-foreground">
                  {tx.description ?? 'No description'}
                </span>
                <span className="shrink-0 font-medium">
                  {tx.amount_original.toFixed(2)} {tx.currency_original}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
