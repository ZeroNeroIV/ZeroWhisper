import { useState } from 'react'
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { Button } from '@/components/ui/Button'

interface PromptDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  message: string
  defaultValue?: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: (value: string) => void
}

export function PromptDialog({
  open,
  onOpenChange,
  title,
  message,
  defaultValue = '',
  confirmLabel = 'Save',
  cancelLabel = 'Cancel',
  onConfirm,
}: PromptDialogProps) {
  const [value, setValue] = useState(defaultValue)

  const handleOpenChange = (open: boolean) => {
    if (open) setValue(defaultValue)
    onOpenChange(open)
  }

  return (
    <Dialog open={open} onOpenChange={(open) => handleOpenChange(open)}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>
            <p className="text-sm text-foreground mb-3">{message}</p>
            <Field label="Name">
              <Input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Enter a name..."
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && value.trim()) {
                    onConfirm(value.trim())
                    handleOpenChange(false)
                  }
                }}
              />
            </Field>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={() => handleOpenChange(false)}>
              {cancelLabel}
            </Button>
            <Button
              appearance="primary"
              disabled={!value.trim()}
              onClick={() => { onConfirm(value.trim()); handleOpenChange(false) }}
            >
              {confirmLabel}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
