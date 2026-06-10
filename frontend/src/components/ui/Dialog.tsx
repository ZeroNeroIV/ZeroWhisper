import { useEffect, useRef, type ReactNode } from 'react'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
}

interface DialogSurfaceProps {
  children: ReactNode
}

interface DialogBodyProps {
  children: ReactNode
}

interface DialogTitleProps {
  children: ReactNode
}

interface DialogContentProps {
  children: ReactNode
}

interface DialogActionsProps {
  children: ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (open && !el.open) el.showModal()
    else if (!open && el.open) el.close()
  }, [open])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const handler = () => onOpenChange(false)
    el.addEventListener('close', handler)
    return () => el.removeEventListener('close', handler)
  }, [onOpenChange])

  if (!open) return null

  return (
    <dialog
      ref={ref}
      className="bg-[var(--elevation-2-bg)] border border-[var(--elevation-2-border)] p-0 backdrop:bg-black/60"
      onClick={(e) => { if (e.target === ref.current) onOpenChange(false) }}
    >
      {children}
    </dialog>
  )
}

export function DialogSurface({ children }: DialogSurfaceProps) {
  return <div className="min-w-[400px] max-w-[520px]">{children}</div>
}

export function DialogBody({ children }: DialogBodyProps) {
  return <div className="p-6 space-y-4">{children}</div>
}

export function DialogTitle({ children }: DialogTitleProps) {
  return <h2 className="headline-lg text-[var(--on-surface)]">{children}</h2>
}

export function DialogContent({ children }: DialogContentProps) {
  return <div className="text-[var(--on-surface-variant)] body-md">{children}</div>
}

export function DialogActions({ children }: DialogActionsProps) {
  return <div className="flex justify-end gap-3 pt-2">{children}</div>
}
