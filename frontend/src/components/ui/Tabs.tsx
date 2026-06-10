import { useState, type ReactNode, type ReactElement, isValidElement } from 'react'

interface TabListProps {
  children: ReactNode
  selectedTab?: string
  onTabSelect?: (tab: string) => void
  className?: string
}

interface TabProps {
  id: string
  children: ReactNode
  className?: string
}

function isTab(el: ReactNode): el is ReactElement<TabProps> {
  return isValidElement<TabProps>(el) && el.type === Tab
}

export function TabList({ children, selectedTab, onTabSelect, className = '' }: TabListProps) {
  const tabs = (Array.isArray(children) ? children : [children]).filter(isTab)
  const [internalTab, setInternalTab] = useState<string>('')

  const activeTab = selectedTab ?? internalTab
  const setActive = onTabSelect ?? setInternalTab

  return (
    <>
      <div className={`flex gap-0 border-b border-[var(--elevation-1-border)] ${className}`}>
        {tabs.map((tab) => {
          const isActive = tab.props.id === activeTab
          return (
            <button
              key={tab.props.id}
              onClick={() => setActive(tab.props.id)}
              className={`label-caps px-4 py-2.5 transition-colors duration-150 ${
                isActive
                  ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                  : 'text-[var(--on-surface-variant)] hover:text-[var(--on-surface)] border-b-2 border-transparent'
              }`}
            >
              {tab.props.children}
            </button>
          )
        })}
      </div>
      {tabs.map((tab) =>
        tab.props.id === activeTab ? <div key={tab.props.id} className="pt-4">{tab.props.children}</div> : null
      )}
    </>
  )
}

export function Tab({ children }: TabProps) {
  return <>{children}</>
}
