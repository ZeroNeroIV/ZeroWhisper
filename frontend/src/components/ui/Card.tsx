import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export function Card({ className = '', children, ...props }: CardProps) {
  return (
    <div
      className={`bg-[var(--elevation-1-bg)] border border-[var(--elevation-1-border)] p-4 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
