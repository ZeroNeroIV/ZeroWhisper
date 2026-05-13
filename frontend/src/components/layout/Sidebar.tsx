import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, ArrowLeftRight, MessageSquare, BarChart3, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Transactions', path: '/transactions', icon: ArrowLeftRight },
  { label: 'Whisper', path: '/whisper', icon: MessageSquare },
  { label: 'Visualizations', path: '/visualizations', icon: BarChart3 },
  { label: 'Settings', path: '/settings', icon: Settings },
]

export function Sidebar() {
  const { pathname } = useLocation()
  return (
    <aside className="w-56 bg-sidebar border-r border-sidebar-border flex flex-col shrink-0">
      <div className="px-4 py-5 border-b border-sidebar-border">
        <span className="text-lg font-semibold text-sidebar-foreground">ZeroWhisper</span>
      </div>
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV_ITEMS.map(({ label, path, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
              pathname === path
                ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                : 'text-sidebar-foreground hover:bg-sidebar-accent/60'
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
