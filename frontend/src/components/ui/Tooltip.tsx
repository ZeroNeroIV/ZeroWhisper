import { useState, useRef, type ReactNode } from 'react'

interface TooltipProps {
  children: ReactNode
  content: string
}

export function Tooltip({ children, content }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  return (
    <div
      ref={ref}
      className="relative inline-block"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-[var(--elevation-2-bg)] border border-[var(--elevation-1-border)] whitespace-nowrap z-50 pointer-events-none">
          <span className="text-xs font-mono text-[var(--on-surface)]">{content}</span>
        </div>
      )}
    </div>
  )
}
