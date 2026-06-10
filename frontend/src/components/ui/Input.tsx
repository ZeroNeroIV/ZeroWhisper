import { forwardRef, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  appearance?: 'outline' | 'underline'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ appearance = 'outline', className = '', ...props }, ref) => {
    const base = 'w-full bg-[var(--elevation-1-bg)] text-[var(--on-surface)] font-mono text-sm px-3 py-2 outline-none transition-[border-color] duration-150 placeholder:text-[var(--on-surface-variant)] disabled:opacity-40'
    const border = appearance === 'underline'
      ? 'border-b border-[var(--elevation-1-border)] focus:border-b-[var(--primary)]'
      : 'border border-[var(--elevation-1-border)] focus:border-[var(--primary)]'
    return (
      <input
        ref={ref}
        className={`${base} ${border} ${className}`}
        {...props}
      />
    )
  },
)
Input.displayName = 'Input'
