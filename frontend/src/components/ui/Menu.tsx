import { useState, useRef, useEffect, type ReactNode, type ReactElement } from 'react'

interface MenuProps { children: ReactNode }
interface MenuTriggerProps { children: ReactNode }
interface MenuPopoverProps { children: ReactNode }
interface MenuListProps { children: ReactNode }
interface MenuItemProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { children: ReactNode }

export function Menu({ children }: MenuProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    if (open) document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const items = Array.isArray(children) ? children : [children]

  return (
    <div ref={ref} className="relative inline-block">
      {items.map((c) => {
        if (!c || typeof c !== 'object' || !('type' in c)) return null
        const child = c as ReactElement
        if (child.type === MenuTrigger) {
          return <div key="trigger" onClick={() => setOpen(!open)}>{child}</div>
        }
        if (open && child.type === MenuPopover) {
          return <div key="popover" className="absolute right-0 top-full mt-1 z-50 min-w-[160px] bg-[var(--elevation-2-bg)] border border-[var(--elevation-2-border)]">{child}</div>
        }
        return null
      })}
    </div>
  )
}

export function MenuTrigger({ children }: MenuTriggerProps) {
  return <>{children}</>
}

export function MenuPopover({ children }: MenuPopoverProps) {
  return <div className="py-1">{children}</div>
}

export function MenuList({ children }: MenuListProps) {
  return <>{children}</>
}

export function MenuItem({ className = '', children, ...props }: MenuItemProps) {
  return (
    <button
      className={`w-full text-left px-3 py-2 text-sm font-mono text-[var(--on-surface)] hover:bg-[var(--surface-container-high)] transition-colors duration-100 ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
