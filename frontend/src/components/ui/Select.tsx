import { forwardRef, type ReactNode, type SelectHTMLAttributes } from 'react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  children?: ReactNode
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', children, ...props }, ref) => (
    <select
      ref={ref}
      className={`w-full bg-[var(--elevation-1-bg)] text-[var(--on-surface)] font-mono text-sm px-3 py-2 border border-[var(--elevation-1-border)] focus:border-[var(--primary)] outline-none transition-[border-color] duration-150 disabled:opacity-40 ${className}`}
      {...props}
    >
      {children}
    </select>
  ),
)
Select.displayName = 'Select'
