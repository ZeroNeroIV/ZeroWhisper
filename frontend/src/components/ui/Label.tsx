import type { LabelHTMLAttributes, ReactNode } from 'react'

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  children?: ReactNode
}

export function Label({ className = '', ...props }: LabelProps) {
  return (
    <label
      className={`label-caps block mb-1 ${className}`}
      {...props}
    />
  )
}
