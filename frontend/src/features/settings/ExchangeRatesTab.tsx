import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import { Card } from '@/components/ui/Card'
import { Table, TableHeader, TableBody, TableRow, TableHeaderCell, TableCell } from '@/components/ui/Table'
import { useExchangeRates, useExchangeRateSettings, type FxSettings } from '@/hooks/useSettings'

function FxApiSettings() {
  const { settings, loading, fetchSettings, updateSettings } = useExchangeRateSettings()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  if (loading && !settings) return <p className="text-sm text-muted-foreground">Loading…</p>

  return settings ? <FxApiSettingsForm settings={settings} updateSettings={updateSettings} saving={saving} setSaving={setSaving} /> : null
}

function FxApiSettingsForm({ settings, updateSettings, saving, setSaving }: {
  settings: FxSettings
  updateSettings: (patch: Partial<FxSettings>) => Promise<FxSettings>
  saving: boolean
  setSaving: (v: boolean) => void
}) {
  const [url, setUrl] = useState(settings.fx_api_url)
  const [key, setKey] = useState(settings.fx_api_key)

  const handleSave = async () => {
    if (!url.trim()) {
      toast.error('API URL is required.')
      return
    }
    setSaving(true)
    try {
      const patch: Record<string, string> = { fx_api_url: url.trim() }
      if (key) patch.fx_api_key = key
      await updateSettings(patch)
      toast.success('Exchange rate API settings saved.')
    } catch {
      toast.error('Failed to save API settings.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <Label htmlFor="fx-api-url">API URL</Label>
        <Input
          id="fx-api-url"
          placeholder="https://api.frankfurter.app/latest"
          value={url}
          onChange={e => setUrl(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="fx-api-key">API Key (optional)</Label>
        <Input
          id="fx-api-key"
          type="password"
          placeholder={settings.fx_api_key ? '(key set)' : 'Optional API key'}
          value={key}
          onChange={e => setKey(e.target.value)}
          autoComplete="off"
        />
      </div>
      <Button appearance="primary" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving…' : 'Save'}
      </Button>
    </div>
  )
}

export function ExchangeRatesTab() {
  const { current, history, loading, fetch, setRate, toggleAutoFetch } = useExchangeRates()

  const [rateInput, setRateInput] = useState('')
  const [dateInput, setDateInput] = useState(() => new Date().toISOString().slice(0, 10))
  const [saving, setSaving] = useState(false)
  const [autoFetch, setAutoFetch] = useState(false)
  const [togglingAuto, setTogglingAuto] = useState(false)

  useEffect(() => {
    fetch()
  }, [fetch])

  const handleSetRate = async () => {
    const parsed = parseFloat(rateInput)
    if (isNaN(parsed) || parsed <= 0) {
      toast.error('Enter a valid positive rate.')
      return
    }
    setSaving(true)
    try {
      await setRate(parsed, dateInput)
      toast.success('Exchange rate saved.')
      await fetch()
      setRateInput('')
    } catch {
      toast.error('Failed to save exchange rate.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleAutoFetch = async (checked: boolean) => {
    setAutoFetch(checked)
    setTogglingAuto(true)
    try {
      await toggleAutoFetch(checked)
      toast.success(checked ? 'Auto-fetch enabled.' : 'Auto-fetch disabled.')
    } catch {
      setAutoFetch(!checked)
      toast.error('Failed to update auto-fetch setting.')
    } finally {
      setTogglingAuto(false)
    }
  }

  const displayedHistory = history.slice(0, 10)

  return (
    <div className="space-y-6">
      {/* Current rate */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-3">Current Rate</h3>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : current ? (
          <p className="text-lg font-semibold">
            1 USD = <span className="text-primary">{current.jod_per_usd}</span> JOD
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              ({current.date}, via {current.source})
            </span>
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">No rate set.</p>
        )}
      </Card>

      {/* Set rate form */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-1">Set Rate</h3>
        <p className="text-sm text-muted-foreground mb-4">Manually set a JOD per USD exchange rate.</p>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-1.5">
            <Label htmlFor="rate-input">Rate (JOD per USD)</Label>
            <Input
              id="rate-input"
              type="number"
              step="0.001"
              min="0"
              placeholder="0.709"
              value={rateInput}
              onChange={(e) => setRateInput(e.target.value)}
            />
          </div>
          <div className="flex-1 space-y-1.5">
            <Label htmlFor="date-input">Date</Label>
            <Input
              id="date-input"
              type="date"
              value={dateInput}
              onChange={(e) => setDateInput(e.target.value)}
            />
          </div>
          <Button appearance="primary" onClick={handleSetRate} disabled={saving} className="shrink-0">
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </div>
      </Card>

      {/* Auto-fetch toggle */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Auto-fetch from Frankfurter API</p>
            <p className="text-sm text-muted-foreground">
              Automatically update exchange rates daily.
            </p>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              type="checkbox"
              className="peer sr-only"
              checked={autoFetch}
              disabled={togglingAuto}
              onChange={(e) => handleToggleAutoFetch(e.target.checked)}
            />
            <div className="peer h-6 w-11 rounded-full bg-muted after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white peer-disabled:opacity-50" />
          </label>
        </div>
      </Card>

      {/* API configuration */}
      <Card className="p-4 space-y-4">
        <h3 className="text-base font-semibold">Exchange Rate API</h3>
        <p className="text-sm text-muted-foreground">
          Configure the API used to auto-fetch exchange rates. Defaults to Frankfurter.
        </p>
        <FxApiSettings />
      </Card>

      {/* Rate history */}
      <div>
        <h3 className="mb-3 font-semibold">Rate History</h3>
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : displayedHistory.length === 0 ? (
          <p className="text-sm text-muted-foreground">No history yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Date</TableHeaderCell>
                <TableHeaderCell>Rate (JOD/USD)</TableHeaderCell>
                <TableHeaderCell>Source</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayedHistory.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.date}</TableCell>
                  <TableCell>{r.jod_per_usd}</TableCell>
                  <TableCell className="text-muted-foreground">{r.source}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}
