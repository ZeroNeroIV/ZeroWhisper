import { useRef, useState } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@fluentui/react-components'
import { Upload } from 'lucide-react'

interface ImportResult {
  imported: number
  errors: Array<{ row: number; message: string }>
}

interface CsvImportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onImported: () => void
}

export function CsvImportDialog({ open, onOpenChange, onImported }: CsvImportDialogProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file)
    setResult(null)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0] ?? null
    if (file) handleFileChange(file)
  }

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('Please select a CSV file first')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setImporting(true)
    try {
      const { data } = await api.post<ImportResult>('/api/imports/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(data)
      toast.success(`Imported ${data.imported} transaction${data.imported !== 1 ? 's' : ''}`)
      onImported()
    } catch {
      toast.error('Failed to import CSV')
    } finally {
      setImporting(false)
    }
  }

  const handleClose = () => {
    setSelectedFile(null)
    setResult(null)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={(_, data) => { if (!data.open) handleClose() }}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>Import Transactions from CSV</DialogTitle>
          <DialogContent>
            <p className="text-sm text-muted-foreground mb-4">
              Upload a CSV file to import multiple transactions at once.
            </p>

            <div className="space-y-4">
              <Button
                appearance="outline"
                onClick={() => window.open('/api/imports/template')}
              >
                Download Template
              </Button>

              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  dragging
                    ? 'border-primary bg-primary/5'
                    : 'border-muted-foreground/25 hover:border-primary/50'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
                {selectedFile ? (
                  <p className="text-sm font-medium">{selectedFile.name}</p>
                ) : (
                  <>
                    <p className="text-sm font-medium">Click to upload or drag and drop</p>
                    <p className="text-xs text-muted-foreground mt-1">CSV files only</p>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                />
              </div>

              {result && (
                <div className="rounded-md border p-4 space-y-2">
                  <p className="text-sm font-medium text-green-700">
                    Successfully imported {result.imported} transaction{result.imported !== 1 ? 's' : ''}
                  </p>
                  {result.errors.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-red-700 mb-1">
                        {result.errors.length} error{result.errors.length !== 1 ? 's' : ''}:
                      </p>
                      <ul className="text-xs text-red-600 space-y-1">
                        {result.errors.map((err) => (
                          <li key={err.row}>
                            Row {err.row}: {err.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="outline" onClick={handleClose} disabled={importing}>
              Close
            </Button>
            <Button
              appearance="primary"
              onClick={handleImport}
              disabled={importing || !selectedFile}
            >
              {importing ? 'Importing...' : 'Import'}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
