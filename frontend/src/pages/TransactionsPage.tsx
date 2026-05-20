import { useEffect, useState } from 'react'
import { useTransactions } from '@/hooks/useTransactions'
import { TransactionForm } from '@/components/features/TransactionForm'
import { CsvImportDialog } from '@/components/features/CsvImportDialog'
import {
  Button,
  Badge,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  Select,
  Option,
  Input,
} from '@fluentui/react-components'
import { Pencil, Trash2, Upload, Plus } from 'lucide-react'
import type { Transaction, TransactionFormData } from '@/types/transaction'
import { VALID_CATEGORIES } from '@/types/transaction'
import { toast } from 'sonner'

const PAGE_SIZE = 20

function getCategoryColor(category: string): 'brand' | 'danger' | 'important' | 'informative' | 'severe' | 'subtle' | 'success' | 'warning' {
  switch (category) {
    case 'Income': return 'success'
    case 'Health': return 'danger'
    case 'Transport': return 'informative'
    case 'Entertainment': return 'important'
    default: return 'subtle'
  }
}

export default function TransactionsPage() {
  const { transactions, total, loading, error, fetchTransactions, createTransaction, updateTransaction, deleteTransaction } =
    useTransactions()

  const [page, setPage] = useState(1)
  const [filterCategory, setFilterCategory] = useState('')
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [pendingCategory, setPendingCategory] = useState('')
  const [pendingDateFrom, setPendingDateFrom] = useState('')
  const [pendingDateTo, setPendingDateTo] = useState('')

  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Transaction | null>(null)
  const [importOpen, setImportOpen] = useState(false)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const loadPage = (p: number) => {
    const filters: {
      page: number
      page_size: number
      category?: string
      date_from?: string
      date_to?: string
    } = { page: p, page_size: PAGE_SIZE }
    if (filterCategory) filters.category = filterCategory
    if (filterDateFrom) filters.date_from = filterDateFrom
    if (filterDateTo) filters.date_to = filterDateTo
    fetchTransactions(filters)
  }

  useEffect(() => {
    loadPage(page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filterCategory, filterDateFrom, filterDateTo])

  const handleApplyFilters = () => {
    setFilterCategory(pendingCategory)
    setFilterDateFrom(pendingDateFrom)
    setFilterDateTo(pendingDateTo)
    setPage(1)
  }

  const handleCreate = async (data: TransactionFormData) => {
    await createTransaction(data)
    toast.success('Transaction added')
    loadPage(page)
  }

  const handleUpdate = async (data: TransactionFormData) => {
    if (!editTarget) return
    await updateTransaction(editTarget.id, data)
    toast.success('Transaction updated')
    loadPage(page)
  }

  const handleDelete = async (tx: Transaction) => {
    if (!window.confirm(`Delete transaction from ${tx.transaction_date}?`)) return
    try {
      await deleteTransaction(tx.id)
      toast.success('Transaction deleted')
      loadPage(page)
    } catch {
      toast.error('Failed to delete transaction')
    }
  }

  const handleEditOpen = (tx: Transaction) => {
    setEditTarget(tx)
    setEditOpen(true)
  }

  const editInitialData: Partial<TransactionFormData> | undefined = editTarget
    ? {
        amount_original: parseFloat(editTarget.amount_original),
        currency_original: editTarget.currency_original as 'JOD' | 'USD',
        category: editTarget.category,
        description: editTarget.description ?? '',
        transaction_date: editTarget.transaction_date,
      }
    : undefined

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <div className="flex gap-2">
          <Button appearance="outline" icon={<Upload size={16} />} onClick={() => setImportOpen(true)} title="Import CSV" />
          <Button appearance="primary" icon={<Plus size={16} />} onClick={() => setAddOpen(true)} title="Add Transaction" />
        </div>
      </div>

      {/* Filters */}
      <div className="space-y-2">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Category</p>
          <Select
            value={pendingCategory}
            onChange={(_, data) => setPendingCategory(data.value)}
            style={{ width: '100%' }}
          >
            <Option value="">All categories</Option>
            {VALID_CATEGORIES.map((cat) => (
              <Option key={cat} value={cat}>{cat}</Option>
            ))}
          </Select>
        </div>
        <div className="flex gap-2">
          <div style={{ flex: 1, minWidth: 0 }}>
            <p className="text-xs text-muted-foreground mb-1">From</p>
            <Input
              type="date"
              value={pendingDateFrom}
              onChange={(e) => setPendingDateFrom(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p className="text-xs text-muted-foreground mb-1">To</p>
            <Input
              type="date"
              value={pendingDateTo}
              onChange={(e) => setPendingDateTo(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
        </div>
        <Button appearance="primary" onClick={handleApplyFilters} style={{ width: '100%' }}>
          Apply Filters
        </Button>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-md border border-red-500 p-4 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-8 text-muted-foreground">Loading...</div>
      )}

      {/* Transactions list */}
      {!loading && !error && (
        <>
          {transactions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No transactions found.
            </div>
          ) : (
            <>
              {/* Mobile cards */}
              <div className="md:hidden space-y-2">
                {transactions.map((tx) => (
                  <div key={tx.id} className="rounded-lg border p-3 space-y-1.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-muted-foreground shrink-0">{tx.transaction_date}</span>
                      <Badge color={getCategoryColor(tx.category)} appearance="tint" className="text-xs shrink-0">
                        {tx.category}
                      </Badge>
                    </div>
                    <p className="text-sm truncate">{tx.description ?? '—'}</p>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-semibold">
                          {parseFloat(tx.amount_original).toFixed(2)} {tx.currency_original}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          = {parseFloat(tx.amount_base).toFixed(2)} JOD
                        </span>
                      </div>
                      <div className="flex items-center gap-0.5">
                        <Button appearance="transparent" icon={<Pencil size={15} />} onClick={() => handleEditOpen(tx)} aria-label="Edit" />
                        <Button appearance="transparent" icon={<Trash2 size={15} />} onClick={() => handleDelete(tx)} aria-label="Delete" style={{ color: 'var(--colorStatusDangerForeground1)' }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop table */}
              <div className="hidden md:block rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHeaderCell>Date</TableHeaderCell>
                      <TableHeaderCell>Description</TableHeaderCell>
                      <TableHeaderCell>Category</TableHeaderCell>
                      <TableHeaderCell>Amount (orig)</TableHeaderCell>
                      <TableHeaderCell>Amount (JOD)</TableHeaderCell>
                      <TableHeaderCell>Actions</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((tx) => (
                      <TableRow key={tx.id}>
                        <TableCell>{tx.transaction_date}</TableCell>
                        <TableCell><span className="max-w-xs truncate block">{tx.description ?? '—'}</span></TableCell>
                        <TableCell><Badge color={getCategoryColor(tx.category)} appearance="tint">{tx.category}</Badge></TableCell>
                        <TableCell>{parseFloat(tx.amount_original).toFixed(2)} {tx.currency_original}</TableCell>
                        <TableCell>{parseFloat(tx.amount_base).toFixed(2)} JOD</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button appearance="transparent" icon={<Pencil size={16} />} onClick={() => handleEditOpen(tx)} aria-label="Edit transaction" />
                            <Button appearance="transparent" icon={<Trash2 size={16} />} onClick={() => handleDelete(tx)} aria-label="Delete transaction" style={{ color: 'var(--colorStatusDangerForeground1)' }} />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-center gap-3">
            <Button
              appearance="outline"
              size="small"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              ← Prev
            </Button>
            <span className="text-sm text-muted-foreground">
              {page} / {totalPages}
            </span>
            <Button
              appearance="outline"
              size="small"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next →
            </Button>
          </div>
        </>
      )}

      {/* Add Transaction Dialog */}
      <TransactionForm
        open={addOpen}
        onOpenChange={setAddOpen}
        onSubmit={handleCreate}
        title="Add Transaction"
      />

      {/* Edit Transaction Dialog */}
      <TransactionForm
        open={editOpen}
        onOpenChange={setEditOpen}
        initialData={editInitialData}
        onSubmit={handleUpdate}
        title="Edit Transaction"
      />

      {/* CSV Import Dialog */}
      <CsvImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => loadPage(page)}
      />
    </div>
  )
}
