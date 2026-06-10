import { useEffect, useState } from 'react'
import { useTransactions } from '@/hooks/useTransactions'
import { TransactionForm } from '@/components/features/TransactionForm'
import { CsvImportDialog } from '@/components/features/CsvImportDialog'
import { Button } from '@/components/ui/Button'
import { Table, TableHeader, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/ui/Table'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Pencil, Trash2, Upload, Plus, Search, Filter, X } from 'lucide-react'
import type { Transaction, TransactionFormData } from '@/types/transaction'
import { useCategories } from '@/hooks/useCategories'
import { useWallets } from '@/hooks/useWallets'
import { renderCategoryLabel } from '@/lib/category'
import { toast } from 'sonner'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'

function isTransfer(tx: Transaction) {
  return tx.type === 'transfer_in' || tx.type === 'transfer_out'
}

function amountPrefix(tx: Transaction) {
  if (tx.type === 'income' || tx.type === 'transfer_in') return '+'
  return '−'
}

const PAGE_SIZE = 20

const SOURCE_TOOLTIPS: Record<string, string> = {
  manual: 'Added manually via the form',
  whisper: 'Added via Whisper AI assistant',
  csv: 'Imported from a CSV file',
}

function TypeBadge({ tx }: { tx: Transaction }) {
  const styles: Record<string, { label: string; className: string }> = {
    income: { label: 'Income', className: 'bg-green-100 text-green-700' },
    expense: { label: 'Expense', className: 'bg-red-100 text-red-700' },
    transfer_in: { label: 'Transfer in', className: 'bg-indigo-100 text-indigo-700' },
    transfer_out: { label: 'Transfer out', className: 'bg-indigo-100 text-indigo-700' },
  }
  const s = styles[tx.type] ?? { label: tx.type, className: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium leading-tight ${s.className}`}>
      {s.label}
    </span>
  )
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
  const { wallets, fetchWallets } = useWallets()

  useEffect(() => { fetchCategories() }, [fetchCategories])
  useEffect(() => { fetchWallets(true) }, [fetchWallets])

  const [page, setPage] = useState(1)
  const [filterCategory, setFilterCategory] = useState('')
  const [filterDateFrom, setFilterDateFrom] = useState('')
  const [filterDateTo, setFilterDateTo] = useState('')
  const [filterWallet, setFilterWallet] = useState('')
  const [pendingCategory, setPendingCategory] = useState('')
  const [pendingDateFrom, setPendingDateFrom] = useState('')
  const [pendingDateTo, setPendingDateTo] = useState('')
  const [pendingWallet, setPendingWallet] = useState('')
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
    const filters: Record<string, string | number> = { page: p, page_size: PAGE_SIZE }
    if (filterCategory) filters.category = filterCategory
    if (filterDateFrom) filters.date_from = filterDateFrom
    if (filterDateTo) filters.date_to = filterDateTo
    if (filterWallet) filters.wallet_id = filterWallet
    if (searchQuery) filters.q = searchQuery
    fetchTransactions(filters)
  }

  useEffect(() => {
    loadPage(page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filterCategory, filterDateFrom, filterDateTo, filterWallet, searchQuery])

  const handleApplyFilters = () => {
    if (pendingDateFrom && pendingDateTo && pendingDateTo < pendingDateFrom) {
      toast.error('"To" date must not be earlier than "From" date')
      return
    }
    setFilterCategory(pendingCategory)
    setFilterDateFrom(pendingDateFrom)
    setFilterDateTo(pendingDateTo)
    setFilterWallet(pendingWallet)
    setSearchQuery(pendingSearch)
    setPage(1)
  }

  const handleClearFilters = () => {
    setPendingCategory('')
    setPendingDateFrom('')
    setPendingDateTo('')
    setPendingWallet('')
    setPendingSearch('')
    setFilterCategory('')
    setFilterDateFrom('')
    setFilterDateTo('')
    setFilterWallet('')
    setSearchQuery('')
    setPage(1)
  }

  const walletName = (id: string | null) => wallets.find((w) => w.id === id)?.name

  const hasActiveFilters = filterCategory || filterDateFrom || filterDateTo || filterWallet || searchQuery


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
        wallet_id: editTarget.wallet_id,
      }
    : undefined

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <div className="flex gap-2">
          <Button appearance="secondary" onClick={() => setImportOpen(true)} title="Import CSV" aria-label="Import CSV">
            <Upload size={16} />
          </Button>
          <Button appearance="primary" onClick={() => setAddOpen(true)} title="Add Transaction" aria-label="Add Transaction">
            <Plus size={16} />
          </Button>
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
        {wallets.length > 0 && (
          <div className="min-w-0 flex-1 max-w-[180px]">
            <p className="text-xs text-muted-foreground mb-1">Wallet</p>
            <Select value={pendingWallet} onChange={(e) => setPendingWallet(e.target.value)}>
              <option value="">All</option>
              {wallets.map((w) => (
                <option key={w.id} value={w.id}>{w.icon ? `${w.icon} ` : ''}{w.name}</option>
              ))}
            </Select>
          </div>
        )}
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
            <Button appearance="secondary" onClick={handleClearFilters} title="Clear filters" aria-label="Clear filters">
              <X size={14} />
            </Button>
          )}
        </div>
      </div>

      {/* ── Mobile Filters ── */}
      <div className="md:hidden">
        <Button
          appearance="secondary"
          onClick={() => setShowMobileFilters((v) => !v)}
          className="w-full"
          size="small"
        >
          <Filter size={14} />
          {showMobileFilters ? 'Hide Filters' : 'Filters'}{hasActiveFilters ? ' · Active' : ''}
        </Button>
        {showMobileFilters && (
          <div className="mt-2 space-y-2 border rounded-md p-3 bg-muted/20">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Category</p>
                <Select
                  value={pendingCategory}
                  onChange={(e) => setPendingCategory(e.target.value)}
                  className="w-full"
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
                  <Button appearance="secondary" size="small" onClick={handleClearFilters} aria-label="Clear filters"><X size={12} /></Button>
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
          {transactions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No transactions found.
            </div>
          ) : (
            <>
              {/* ── Mobile Cards ── */}
              <div className="md:hidden space-y-2">
                {transactions.map((tx) => (
                  <div key={tx.id} className="rounded-lg border p-3 space-y-1.5 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs text-muted-foreground shrink-0">{tx.transaction_date}</span>
                      <div className="flex items-center gap-1.5">
                        <TypeBadge tx={tx} />
                        {renderCategoryLabel(tx.category, categories)}
                      </div>
                    </div>
                    <p className="text-sm truncate">{tx.description ?? '—'}</p>
                    {tx.wallet_id && walletName(tx.wallet_id) && (
                      <p className="text-xs text-muted-foreground">👛 {walletName(tx.wallet_id)}</p>
                    )}
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-sm font-semibold">
                          {amountPrefix(tx)}{parseFloat(tx.amount_original).toFixed(2)} {tx.currency_original}
                        </span>
                        <span className="text-xs text-muted-foreground ml-2">
                          = {parseFloat(tx.amount_base).toFixed(2)} JOD
                        </span>
                      </div>
                      <div className="flex items-center gap-0.5">
                        {!isTransfer(tx) && (
                          <Button appearance="ghost" onClick={() => handleEditOpen(tx)} aria-label="Edit">
                            <Pencil size={15} />
                          </Button>
                        )}
                        <Button appearance="ghost" onClick={() => handleDelete(tx)} aria-label="Delete" className="text-red-500">
                          <Trash2 size={15} />
                        </Button>
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
                      <TableHeaderCell>Type</TableHeaderCell>
                      <TableHeaderCell>Wallet</TableHeaderCell>
                      <TableHeaderCell className="whitespace-nowrap">Source</TableHeaderCell>
                      <TableHeaderCell className="text-right whitespace-nowrap">Amount (orig)</TableHeaderCell>
                      <TableHeaderCell className="text-right whitespace-nowrap">Amount (JOD)</TableHeaderCell>
                      <TableHeaderCell className="w-20">Actions</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((tx) => (
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
                        <TableCell>{renderCategoryLabel(tx.category, categories)}</TableCell>
                        <TableCell><TypeBadge tx={tx} /></TableCell>
                        <TableCell className="text-sm whitespace-nowrap">
                          {walletName(tx.wallet_id) ?? <span className="text-muted-foreground">—</span>}
                        </TableCell>
                        <TableCell><SourceBadge source={tx.source} /></TableCell>
                        <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                          {amountPrefix(tx)}{parseFloat(tx.amount_original).toFixed(2)}
                          <span className="text-muted-foreground ml-1 text-xs">{tx.currency_original}</span>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm whitespace-nowrap">
                          {parseFloat(tx.amount_base).toFixed(2)}
                          <span className="text-muted-foreground ml-1 text-xs">JOD</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-0.5 justify-end">
                            {!isTransfer(tx) && (
                              <Button appearance="ghost" onClick={() => handleEditOpen(tx)} aria-label="Edit transaction">
                                <Pencil size={15} />
                              </Button>
                            )}
                            <Button appearance="ghost" onClick={() => handleDelete(tx)} aria-label="Delete transaction" className="text-red-500">
                              <Trash2 size={15} />
                            </Button>
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
                : transactions.length !== transactions.length
                  ? `${transactions.length} of ${total} transactions`
                  : `${total} transaction${total !== 1 ? 's' : ''}`
              }
            </span>
            {totalPages > 1 && (
              <div className="flex items-center gap-2 mx-auto md:mx-0 md:ml-auto">
                <Button
                  appearance="secondary"
                  size="small"
                  onClick={() => setPage(1)}
                  disabled={page <= 1}
                  title="First page"
                  aria-label="First page"
                >
                  «
                </Button>
                <Button
                  appearance="secondary"
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
                  appearance="secondary"
                  size="small"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  aria-label="Next page"
                >
                  Next →
                </Button>
                <Button
                  appearance="secondary"
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
        wallets={wallets}
      />

      {/* Edit Transaction Dialog */}
      <TransactionForm
        open={editOpen}
        onOpenChange={setEditOpen}
        initialData={editInitialData}
        onSubmit={handleUpdate}
        title="Edit Transaction"
        categories={categories}
        wallets={wallets}
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
        message={
          deleteTarget && isTransfer(deleteTarget)
            ? 'This is one leg of a wallet transfer — deleting it removes both legs and restores both wallet balances. Continue?'
            : `Are you sure you want to delete the transaction from ${deleteTarget?.transaction_date ?? 'unknown date'}?`
        }
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
      />
    </div>
  )
}
