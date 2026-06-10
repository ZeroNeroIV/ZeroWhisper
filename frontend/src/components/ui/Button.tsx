import { forwardRef, type ButtonHTMLAttributes } from 'react'

type Appearance = 'primary' | 'secondary' | 'ghost'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  appearance?: Appearance
  size?: 'small' | 'medium'
}

const base = 'inline-flex items-center justify-center gap-1.5 font-mono text-sm font-medium transition-colors duration-150 disabled:opacity-40 disabled:pointer-events-none cursor-pointer'

const appearances: Record<Appearance, string> = {
  primary: 'bg-[var(--primary)] text-[var(--on-primary)] hover:brightness-110 active:brightness-90',
  secondary: 'bg-transparent text-[var(--primary)] border-2 border-[var(--primary)] hover:bg-[var(--primary)] hover:text-[var(--on-primary)]',
  ghost: 'bg-transparent text-[var(--on-surface)] border-2 border-transparent hover:text-[var(--primary)] active:text-[var(--secondary)]',
}

const sizes: Record<string, string> = {
  small: 'px-2.5 py-1.5 text-xs',
  medium: 'px-4 py-2 text-sm',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ appearance = 'primary', size = 'medium', className = '', ...props }, ref) => (
    <button
      ref={ref}
      className={`${base} ${appearances[appearance]} ${sizes[size]} ${className}`}
      {...props}
    />
  ),
)
Button.displayName = 'Button'
