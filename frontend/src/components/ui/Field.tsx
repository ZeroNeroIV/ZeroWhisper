import type { ReactNode } from 'react'
import { Label } from './Label'

interface FieldProps {
  label?: string
  children: ReactNode
  required?: boolean
  className?: string
}

export function Field({ label, children, required, className = '' }: FieldProps) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      {label && <Label>{label}{required && <span className="text-[var(--error)] ml-0.5">*</span>}</Label>}
      {children}
    </div>
  )
}
