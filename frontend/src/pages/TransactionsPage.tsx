import { useEffect, useState } from 'react'
import { useTransactions } from '@/hooks/useTransactions'
import { TransactionForm } from '@/components/features/TransactionForm'
import { CsvImportDialog } from '@/components/features/CsvImportDialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Pencil, Trash2, Upload, Plus } from 'lucide-react'
import type { Transaction, TransactionFormData } from '@/types/transaction'
import { VALID_CATEGORIES } from '@/types/transaction'
import { toast } from 'sonner'

const PAGE_SIZE = 20

function getCategoryClass(category: string): string {
  switch (category) {
    case 'Food':
      return 'bg-green-100 text-green-800'
    case 'Transport':
      return 'bg-blue-100 text-blue-800'
    case 'Housing':
      return 'bg-yellow-100 text-yellow-800'
    case 'Entertainment':
      return 'bg-purple-100 text-purple-800'
    case 'Income':
      return 'bg-emerald-100 text-emerald-800'
    case 'Health':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
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
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setImportOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            Import CSV
          </Button>
          <Button onClick={() => setAddOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Transaction
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={pendingCategory}
          onValueChange={setPendingCategory}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All Categories</SelectItem>
            {VALID_CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>
                {cat}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={pendingDateFrom}
          onChange={(e) => setPendingDateFrom(e.target.value)}
          className="w-44"
          placeholder="From date"
        />
        <Input
          type="date"
          value={pendingDateTo}
          onChange={(e) => setPendingDateTo(e.target.value)}
          className="w-44"
          placeholder="To date"
        />
        <Button onClick={handleApplyFilters}>Apply</Button>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-md border border-destructive p-4 text-destructive text-sm">
          {error}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-8 text-muted-foreground">Loading...</div>
      )}

      {/* Table */}
      {!loading && !error && (
        <>
          {transactions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No transactions found.
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Amount (orig)</TableHead>
                    <TableHead className="text-right">Amount (JOD)</TableHead>
                    <TableHead className="text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell className="whitespace-nowrap">{tx.transaction_date}</TableCell>
                      <TableCell className="max-w-xs truncate">
                        {tx.description ?? '—'}
                      </TableCell>
                      <TableCell>
                        <Badge className={getCategoryClass(tx.category)} variant="outline">
                          {tx.category}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        {parseFloat(tx.amount_original).toFixed(2)} {tx.currency_original}
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        {parseFloat(tx.amount_base).toFixed(2)} JOD
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEditOpen(tx)}
                            aria-label="Edit transaction"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(tx)}
                            aria-label="Delete transaction"
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next
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
