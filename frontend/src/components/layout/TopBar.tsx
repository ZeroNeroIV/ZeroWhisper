import { useAuth } from '@/hooks/useAuth'
import {
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Avatar,
} from '@fluentui/react-components'
import { LogOut, Menu as MenuIcon } from 'lucide-react'

export function TopBar({ onMenuClick }: { onMenuClick?: () => void }) {
  const { username, logout } = useAuth()
  return (
    <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background shrink-0">
      {/* Hamburger — mobile only */}
      <button
        type="button"
        className="md:hidden p-2 rounded text-muted-foreground hover:text-foreground"
        onClick={onMenuClick}
        aria-label="Open menu"
      >
        <MenuIcon size={20} />
      </button>

      {/* Spacer on desktop */}
      <div className="hidden md:block" />

      <Menu>
        <MenuTrigger disableButtonEnhancement>
          <button type="button" className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Avatar name={username ?? 'User'} size={32} color="brand" />
            <span className="text-sm hidden sm:inline">{username}</span>
          </button>
        </MenuTrigger>
        <MenuPopover>
          <MenuList>
            <MenuItem icon={<LogOut size={16} />} onClick={logout}>
              Logout
            </MenuItem>
          </MenuList>
        </MenuPopover>
      </Menu>
    </header>
  )
}
