import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, Badge } from '@fluentui/react-components'
import { Wallet, TrendingDown, TrendingUp } from 'lucide-react'

interface DashboardSummary {
  balance_jod: number
  month_spending_jod: number
  month_income_jod: number
  recent_transactions: Array<{
    id: string
    category: string
    description: string | null
    amount_original: number
    currency_original: string
    transaction_date: string
  }>
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<DashboardSummary>('/api/dashboard/summary')
      .then(({ data }) => setSummary(data))
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                <Badge appearance="outline" className="shrink-0">
                  {tx.category}
                </Badge>
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
