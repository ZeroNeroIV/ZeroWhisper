import { useSearchParams } from 'react-router-dom'
import { TabList, Tab } from '@/components/ui/Tabs'
import { ApiKeysTab } from '@/features/settings/ApiKeysTab'
import { CategoriesTab } from '@/features/settings/CategoriesTab'
import { ExchangeRatesTab } from '@/features/settings/ExchangeRatesTab'
import { BanksTab } from '@/features/settings/BanksTab'
import { AiTab } from '@/features/settings/AiTab'
import { AboutTab } from '@/features/settings/AboutTab'

const VALID_TABS = ['api-keys', 'categories', 'exchange-rates', 'banks', 'ai', 'about'] as const

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = VALID_TABS.includes(searchParams.get('tab') as typeof VALID_TABS[number]) ? searchParams.get('tab')! : 'api-keys'

  const setActiveTab = (tab: string) => {
    setSearchParams({ tab }, { replace: true })
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <div className="overflow-x-auto -mx-1 px-1">
        <TabList
          selectedTab={activeTab}
          onTabSelect={setActiveTab}
        >
          <Tab id="api-keys">API Keys</Tab>
          <Tab id="categories">Categories</Tab>
          <Tab id="exchange-rates">Rates</Tab>
          <Tab id="banks">Banks</Tab>
          <Tab id="ai">AI</Tab>
          <Tab id="about">About</Tab>
        </TabList>
      </div>

      {activeTab === 'api-keys' && <ApiKeysTab />}
      {activeTab === 'categories' && <CategoriesTab />}
      {activeTab === 'exchange-rates' && <ExchangeRatesTab />}
      {activeTab === 'banks' && <BanksTab />}
      {activeTab === 'ai' && <AiTab />}
      {activeTab === 'about' && <AboutTab />}
    </div>
  )
}
