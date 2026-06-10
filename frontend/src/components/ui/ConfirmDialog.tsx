import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { Button } from '@/components/ui/Button'

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel?: () => void
  destructive?: boolean
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  destructive,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(open) => onOpenChange(open)}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{title}</DialogTitle>
          <DialogContent>
            <p className="text-sm text-foreground">{message}</p>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={() => { onCancel?.(); onOpenChange(false) }}>
              {cancelLabel}
            </Button>
            <Button
              appearance="primary"
              className={destructive ? 'bg-red-600' : ''}
              onClick={() => { onConfirm(); onOpenChange(false) }}
            >
              {confirmLabel}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  )
}
