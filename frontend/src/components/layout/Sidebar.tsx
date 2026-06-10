import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, Wallet, BarChart3, Settings, X } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Dashboard',      path: '/dashboard',      icon: LayoutDashboard },
  { label: 'Transactions',   path: '/transactions',   icon: ArrowLeftRight  },
  { label: 'Wallets',        path: '/wallets',        icon: Wallet          },
  { label: 'Visualizations', path: '/visualizations', icon: BarChart3       },
  { label: 'Settings',       path: '/settings',       icon: Settings        },
]

export function Sidebar({ onClose }: { onClose?: () => void }) {
  const { pathname } = useLocation()

  // Close drawer on navigation (mobile)
  useEffect(() => {
    onClose?.()
  }, [pathname]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <aside className="w-56 h-full bg-sidebar border-r border-sidebar-border flex flex-col shrink-0">
      <div className="px-5 py-4 border-b border-sidebar-border flex items-center justify-between">
        <span className="text-[15px] font-semibold tracking-tight text-foreground">
          ZeroWhisper
        </span>
        {/* Close button — only visible on mobile */}
        <button
          type="button"
          className="md:hidden p-1 rounded text-muted-foreground hover:text-foreground"
          onClick={onClose}
          aria-label="Close menu"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 py-3 px-3 space-y-0.5">
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => {
          const active = pathname === path
          return (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex items-center gap-2.5 px-3 py-2.5 rounded-md text-[13px] font-medium transition-colors',
                active
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-foreground'
              )}
            >
              <Icon
                className={cn(
                  'h-[16px] w-[16px] shrink-0',
                  active ? 'text-sidebar-accent-foreground' : 'text-sidebar-foreground'
                )}
              />
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
