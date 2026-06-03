import { useEffect, useState, useMemo } from 'react'
import { useTransactions } from '@/hooks/useTransactions'
import { TransactionForm } from '@/components/features/TransactionForm'
import { CsvImportDialog } from '@/components/features/CsvImportDialog'
import {
  Button,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  Input,
  Select,
} from '@fluentui/react-components'
import { Pencil, Trash2, Upload, Plus, Search, Filter, X } from 'lucide-react'
import type { Transaction, TransactionFormData } from '@/types/transaction'
import { useCategories } from '@/hooks/useCategories'
import type { Category } from '@/types/category'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'

const PAGE_SIZE = 20

function renderCategoryText(categoryName: string, categories: Category[]): React.ReactNode {
  const cat = categories.find((c) => c.name === categoryName)
  const color = cat?.color
  const icon = cat?.icon

  const textEl = (() => {
    if (!color) {
      return <span className="text-xs font-medium text-muted-foreground">{categoryName}</span>
    }
    if (color.startsWith('animated:')) {
      const gradient = color.slice('animated:'.length)
      return (
        <span
          className="text-xs font-medium animate-gradient"
          style={{ background: gradient, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}
        >
          {categoryName}
        </span>
      )
    }
    if (color.startsWith('linear-gradient') || color.startsWith('radial-gradient')) {
      return (
        <span
          className="text-xs font-medium"
          style={{ background: color, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}
        >
          {categoryName}
        </span>
      )
    }
    return (
      <span className="text-xs font-medium" style={{ color }}>
        {categoryName}
      </span>
    )
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

const SOURCE_TOOLTIPS: Record<string, string> = {
  manual: 'Added manually via the form',
  whisper: 'Added via Whisper AI assistant',
  csv: 'Imported from a CSV file',
}

function SourceBadge({ source }: { source: string }) {
  const styles: Record<string, { label: string; className: string }> = {
    manual: { label: 'Manual', className: 'bg-blue-100 text-blue-700' },
    whisper: { label: 'AI', className: 'bg-purple-100 text-purple-700' },
    csv: { label: 'CSV', className: 'bg-amber-100 text-amber-700' },
  }
  const s = styles[source] || { label: source, className: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium leading-tight ${s.className}`} title={SOURCE_TOOLTIPS[source] || ''}>
      {s.label}
    </span>
  )
}

export default function TransactionsPage() {
  const { transactions, total, loading, error, fetchTransactions, createTransaction, updateTransaction, deleteTransaction } =
    useTransactions()
  const { categories, fetchCategories } = useCategories()

  useEffect(() => { fetchCategories() }, [fetchCategories])

  const [page, setPage] = useState(1)
  const [filterCategory, setFilterCategory] = useState('')
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [pendingCategory, setPendingCategory] = useState('')
  const [pendingDateFrom, setPendingDateFrom] = useState('')
  const [pendingDateTo, setPendingDateTo] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [pendingSearch, setPendingSearch] = useState('')
  const [showMobileFilters, setShowMobileFilters] = useState(false)

  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Transaction | null>(null)
  const [importOpen, setImportOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Transaction | null>(null)

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
    if (pendingDateFrom && pendingDateTo && pendingDateTo < pendingDateFrom) {
      toast.error('"To" date must not be earlier than "From" date')
      return
    }
    setFilterCategory(pendingCategory)
    setFilterDateFrom(pendingDateFrom)
    setFilterDateTo(pendingDateTo)
    setSearchQuery(pendingSearch)
    setPage(1)
  }

  const handleClearFilters = () => {
    setPendingCategory('')
    setPendingDateFrom('')
    setPendingDateTo('')
    setPendingSearch('')
    setFilterCategory('')
    setFilterDateFrom('')
    setFilterDateTo('')
    setSearchQuery('')
    setPage(1)
  }

  const hasActiveFilters = filterCategory || filterDateFrom || filterDateTo || searchQuery

  // Client-side description filter on the current page
  const filteredTransactions = useMemo(() => {
    if (!searchQuery) return transactions
    const q = searchQuery.toLowerCase()
    return transactions.filter((tx) => tx.description?.toLowerCase().includes(q))
  }, [transactions, searchQuery])

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
    setDeleteTarget(tx)
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteTransaction(deleteTarget.id)
      toast.success('Transaction deleted')
      loadPage(page)
    } catch {
      toast.error('Failed to delete transaction')
    }
    setDeleteTarget(null)
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
          <Button appearance="outline" icon={<Upload size={16} />} onClick={() => setImportOpen(true)} title="Import CSV" aria-label="Import CSV" />
          <Button appearance="primary" icon={<Plus size={16} />} onClick={() => setAddOpen(true)} title="Add Transaction" aria-label="Add Transaction" />
        </div>
      </div>

      {/* ── Desktop Filters ── */}
      <div className="hidden md:flex md:items-end md:gap-3 md:flex-wrap">
        <div className="min-w-0 flex-1 max-w-[180px]">
          <p className="text-xs text-muted-foreground mb-1">Category</p>
          <Select
            value={pendingCategory}
            onChange={(e) => setPendingCategory(e.target.value)}
          >
            <option value="">All</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.name}>{cat.icon ? `${cat.icon} ${cat.name}` : cat.name}</option>
            ))}
          </Select>
        </div>
        <div className="min-w-0 flex-1 max-w-[160px]">
          <p className="text-xs text-muted-foreground mb-1">From</p>
          <Input
            type="date"
            value={pendingDateFrom}
            onChange={(e) => setPendingDateFrom(e.target.value)}
          />
        </div>
        <div className="min-w-0 flex-1 max-w-[160px]">
          <p className="text-xs text-muted-foreground mb-1">To</p>
          <Input
            type="date"
            value={pendingDateTo}
            onChange={(e) => setPendingDateTo(e.target.value)}
          />
        </div>
        <div className="min-w-0 flex-[2] max-w-[240px]">
          <p className="text-xs text-muted-foreground mb-1">
            <Search size={12} className="inline mr-1" />
            Description
          </p>
          <Input
            value={pendingSearch}
            onChange={(e) => setPendingSearch(e.target.value)}
            placeholder="Search descriptions..."
            onKeyDown={(e) => { if (e.key === 'Enter') handleApplyFilters() }}
          />
        </div>
        <div className="flex items-center gap-1.5 pb-px">
          <Button appearance="primary" onClick={handleApplyFilters}>
            Apply
          </Button>
          {hasActiveFilters && (
            <Button appearance="outline" onClick={handleClearFilters} title="Clear filters" aria-label="Clear filters">
              <X size={14} />
            </Button>
          )}
        </div>
      </div>

      {/* ── Mobile Filters ── */}
      <div className="md:hidden">
        <Button
          appearance="outline"
          icon={<Filter size={14} />}
          onClick={() => setShowMobileFilters((v) => !v)}
          style={{ width: '100%' }}
          size="small"
        >
          {showMobileFilters ? 'Hide Filters' : 'Filters'}{hasActiveFilters ? ' · Active' : ''}
        </Button>
        {showMobileFilters && (
          <div className="mt-2 space-y-2 border rounded-md p-3 bg-muted/20">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Category</p>
              <Select
                value={pendingCategory}
                onChange={(e) => setPendingCategory(e.target.value)}
                style={{ width: '100%' }}
              >
                <option value="">All categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.name}>{cat.icon ? `${cat.icon} ${cat.name}` : cat.name}</option>
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
                />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p className="text-xs text-muted-foreground mb-1">To</p>
                <Input
                  type="date"
                  value={pendingDateTo}
                  onChange={(e) => setPendingDateTo(e.target.value)}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div style={{ flex: 1, minWidth: 0 }}>
                <p className="text-xs text-muted-foreground mb-1">Search</p>
                <Input
                  value={pendingSearch}
                  onChange={(e) => setPendingSearch(e.target.value)}
                  placeholder="Description..."
                />
              </div>
              <div className="flex gap-1 pt-5">
                <Button appearance="primary" size="small" onClick={handleApplyFilters}>Go</Button>
                {hasActiveFilters && (
                  <Button appearance="outline" size="small" onClick={handleClearFilters} aria-label="Clear filters"><X size={12} /></Button>
                )}
              </div>
            </div>
          </div>
        )}
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
          {filteredTransactions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No transactions found.
            </div>
          ) : (
            <>
              {/* ── Mobile Cards ── */}
              <div className="md:hidden space-y-2">
                {filteredTransactions.map((tx) => (
                  <div key={tx.id} className="rounded-lg border p-3 space-y-1.5 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-muted-foreground shrink-0">{tx.transaction_date}</span>
                      {renderCategoryText(tx.category, categories)}
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

              {/* ── Desktop Table ── */}
              <div className="hidden md:block rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHeaderCell className="whitespace-nowrap">Date</TableHeaderCell>
                      <TableHeaderCell>Description</TableHeaderCell>
                      <TableHeaderCell>Category</TableHeaderCell>
                      <TableHeaderCell className="whitespace-nowrap">Source</TableHeaderCell>
                      <TableHeaderCell className="text-right whitespace-nowrap">Amount (orig)</TableHeaderCell>
                      <TableHeaderCell className="text-right whitespace-nowrap">Amount (JOD)</TableHeaderCell>
                      <TableHeaderCell className="w-20">Actions</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTransactions.map((tx) => (
                      <TableRow
                        key={tx.id}
                        className="hover:bg-muted/50 transition-colors"
                      >
                        <TableCell className="whitespace-nowrap text-sm">{tx.transaction_date}</TableCell>
                        <TableCell>
                          <span className="max-w-[260px] truncate block text-sm" title={tx.description ?? ''}>
                            {tx.description ?? '—'}
                          </span>
                        </TableCell>
                        <TableCell>{renderCategoryText(tx.category, categories)}</TableCell>
                        <TableCell><SourceBadge source={tx.source} /></TableCell>
                        <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                          {parseFloat(tx.amount_original).toFixed(2)}
                          <span className="text-muted-foreground ml-1 text-xs">{tx.currency_original}</span>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                          {parseFloat(tx.amount_base).toFixed(2)}
                          <span className="text-muted-foreground ml-1 text-xs">JOD</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-0.5 justify-end">
                            <Button appearance="transparent" icon={<Pencil size={15} />} onClick={() => handleEditOpen(tx)} aria-label="Edit transaction" />
                            <Button appearance="transparent" icon={<Trash2 size={15} />} onClick={() => handleDelete(tx)} aria-label="Delete transaction" style={{ color: 'var(--colorStatusDangerForeground1)' }} />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </>
          )}

          {/* ── Pagination ── */}
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted-foreground hidden md:inline">
              {total === 0
                ? 'No results'
                : filteredTransactions.length !== transactions.length
                  ? `${filteredTransactions.length} of ${total} transactions`
                  : `${total} transaction${total !== 1 ? 's' : ''}`
              }
            </span>
            {totalPages > 1 && (
              <div className="flex items-center gap-2 mx-auto md:mx-0 md:ml-auto">
                <Button
                  appearance="outline"
                  size="small"
                  onClick={() => setPage(1)}
                  disabled={page <= 1}
                  title="First page"
                  aria-label="First page"
                >
                  «
                </Button>
                <Button
                  appearance="outline"
                  size="small"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  aria-label="Previous page"
                >
                  ← Prev
                </Button>
                <span className="text-sm text-muted-foreground whitespace-nowrap">
                  <span className="hidden md:inline">Page </span>{page}<span className="hidden md:inline"> / {totalPages}</span>
                </span>
                <Button
                  appearance="outline"
                  size="small"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  aria-label="Next page"
                >
                  Next →
                </Button>
                <Button
                  appearance="outline"
                  size="small"
                  onClick={() => setPage(totalPages)}
                  disabled={page >= totalPages}
                  title="Last page"
                  aria-label="Last page"
                >
                  »
                </Button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Add Transaction Dialog */}
      <TransactionForm
        open={addOpen}
        onOpenChange={setAddOpen}
        onSubmit={handleCreate}
        title="Add Transaction"
        categories={categories}
      />

      {/* Edit Transaction Dialog */}
      <TransactionForm
        open={editOpen}
        onOpenChange={setEditOpen}
        initialData={editInitialData}
        onSubmit={handleUpdate}
        title="Edit Transaction"
        categories={categories}
      />

      {/* CSV Import Dialog */}
      <CsvImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => loadPage(page)}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title="Delete transaction?"
        message={`Are you sure you want to delete the transaction from ${deleteTarget?.transaction_date ?? 'unknown date'}?`}
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
      />
    </div>
  )
}
