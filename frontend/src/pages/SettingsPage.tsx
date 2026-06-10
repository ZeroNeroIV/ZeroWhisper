import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import {
  TabList,
  Tab,
  Button,
  Input,
  Label,
  Card,
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  Field,
  Select,
} from '@fluentui/react-components'
import { Pencil, Trash2, Save } from 'lucide-react'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { PromptDialog } from '@/components/ui/PromptDialog'
import { useApiKeys, useExchangeRates, useExchangeRateSettings, type FxSettings } from '@/hooks/useSettings'
import { useBankConnections, type BankConnection } from '@/hooks/useBankConnections'
import { useCategories } from '@/hooks/useCategories'
import type { Category } from '@/types/category'
import { api, apiErrorDetail } from '@/lib/api'

// ─── API Keys Tab ─────────────────────────────────────────────────────────────

function ApiKeysTab() {
  const { keys, loading, fetchKeys, createKey, revokeKey } = useApiKeys()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchKeys()
  }, [fetchKeys])

  const handleOpenDialog = () => {
    setNewKeyName('')
    setGeneratedKey(null)
    setCopied(false)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setGeneratedKey(null)
    setCopied(false)
    fetchKeys()
  }

  const handleCreate = async () => {
    if (!newKeyName.trim()) {
      toast.error('Key name is required.')
      return
    }
    setCreating(true)
    try {
      const result = await createKey(newKeyName.trim())
      setGeneratedKey(result.key)
      toast.success('API key created.')
    } catch {
      toast.error('Failed to create API key.')
    } finally {
      setCreating(false)
    }
  }

  const handleCopy = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey).then(() => {
        setCopied(true)
        toast.success('Copied to clipboard!')
      })
    }
  }

  const handleRevoke = async (id: number, name: string) => {
    try {
      await revokeKey(id)
      toast.success(`API key "${name}" revoked.`)
    } catch {
      toast.error('Failed to revoke API key.')
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Your API Keys</h2>
        <Button appearance="primary" onClick={handleOpenDialog}>Generate New Key</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading keys…</p>
      ) : keys.length === 0 ? (
        <p className="text-sm text-muted-foreground">No API keys yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Key</TableHeaderCell>
                <TableHeaderCell>Created</TableHeaderCell>
                <TableHeaderCell>Last Used</TableHeaderCell>
                <TableHeaderCell></TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((k) => (
                <TableRow key={k.id}>
                  <TableCell className="font-medium">{k.name}</TableCell>
                  <TableCell>
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                      {k.prefix}***
                    </code>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(k.created_at)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDate(k.last_used_at)}
                  </TableCell>
                  <TableCell>
                    <Button
                      appearance="outline"
                      size="small"
                      onClick={() => handleRevoke(k.id, k.name)}
                      style={{ color: 'var(--colorStatusDangerForeground1)', borderColor: 'var(--colorStatusDangerForeground1)' }}
                    >
                      Revoke
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(_, data) => { if (!data.open) handleCloseDialog() }}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Generate New API Key</DialogTitle>
            <DialogContent>
              <p className="text-sm text-muted-foreground mb-4">
                Give your key a name to identify it later.
              </p>
              {!generatedKey ? (
                <Field label="Key Name">
                  <Input
                    id="key-name"
                    placeholder="e.g. My Script"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCreate()
                    }}
                    disabled={creating}
                  />
                </Field>
              ) : (
                <div className="space-y-4">
                  <p className="text-sm font-medium text-red-600">
                    Save this key — it won't be shown again.
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 overflow-x-auto rounded border bg-muted px-3 py-2 text-sm">
                      {generatedKey}
                    </code>
                    <Button appearance="outline" size="small" onClick={handleCopy}>
                      {copied ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
            <DialogActions>
              {!generatedKey ? (
                <>
                  <Button appearance="outline" onClick={handleCloseDialog} disabled={creating}>
                    Cancel
                  </Button>
                  <Button appearance="primary" onClick={handleCreate} disabled={creating}>
                    {creating ? 'Creating…' : 'Create'}
                  </Button>
                </>
              ) : (
                <Button appearance="primary" onClick={handleCloseDialog}>Done</Button>
              )}
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}

// ─── Categories Tab ─────────────────────────────────────────────────────────

const SOLID_COLORS = [
  '#ef4444', '#f97316', '#f59e0b', '#22c55e', '#14b8a6',
  '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#6b7280',
  '#dc2626', '#ea580c', '#ca8a04', '#16a34a', '#0d9488',
  '#2563eb', '#4f46e5', '#7c3aed', '#db2777', '#4b5563',
]

const GRADIENT_PRESETS = [
  { label: 'Sunset', value: 'linear-gradient(135deg, #ff6b6b, #feca57)' },
  { label: 'Ocean', value: 'linear-gradient(135deg, #48dbfb, #0abde3)' },
  { label: 'Forest', value: 'linear-gradient(135deg, #2ecc71, #26a65b)' },
  { label: 'Lavender', value: 'linear-gradient(135deg, #a29bfe, #6c5ce7)' },
  { label: 'Peach', value: 'linear-gradient(135deg, #fd79a8, #e84393)' },
  { label: 'Mint', value: 'linear-gradient(135deg, #55efc4, #00b894)' },
  { label: 'Coral', value: 'linear-gradient(135deg, #ff7675, #d63031)' },
  { label: 'Sky', value: 'linear-gradient(135deg, #74b9ff, #0984e3)' },
  { label: 'Neon', value: 'linear-gradient(135deg, #ffd93d, #ff6b6b)' },
  { label: 'Midnight', value: 'linear-gradient(135deg, #2d3436, #636e72)' },
  { label: 'Aurora', value: 'linear-gradient(135deg, #00b894, #00cec9, #0984e3)' },
  { label: 'Rose', value: 'linear-gradient(135deg, #e84393, #fd79a8, #fab1a0)' },
]

function ColorSwatch({ color, size = 10 }: { color: string | null; size?: number }) {
  if (!color) {
    return <span className={`inline-block rounded-full shrink-0 bg-gray-300`} style={{ width: size, height: size }} />
  }
  const isGradient = color.startsWith('linear-gradient') || color.startsWith('radial-gradient')
  const isAnimated = color.startsWith('animated:')
  const bg = isAnimated ? color.slice(9) : color

  if (isGradient || isAnimated) {
    return (
      <span
        className={`inline-block rounded-full shrink-0 ${isAnimated ? 'animate-gradient' : ''}`}
        style={{ width: size, height: size, background: bg, backgroundSize: isAnimated ? '200% 200%' : undefined }}
      />
    )
  }
  return <span className="inline-block rounded-full shrink-0" style={{ width: size, height: size, backgroundColor: color }} />
}

function parseGradient(gradient: string): { angle: number; colors: string[] } | null {
  const clean = gradient.replace('animated:', '')
  const match = clean.match(/linear-gradient\((\d+)deg,\s*(.*)\)/)
  if (!match) return null
  return { angle: parseInt(match[1]), colors: match[2].split(',').map(s => s.trim()) }
}

function buildGradient(angle: number, colors: string[]): string {
  return `linear-gradient(${angle}deg, ${colors.join(', ')})`
}

interface SavedTemplate {
  id: string
  label: string
  value: string
  type: 'solid' | 'gradient' | 'animated'
}

const STORAGE_KEY = 'zw-saved-color-templates'

function loadTemplates(): SavedTemplate[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch { return [] }
}

function saveTemplates(templates: SavedTemplate[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
}

function CategoriesTab() {
  const { categories, loading, fetchCategories, createCategory, updateCategory, deleteCategory } = useCategories()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState<'income' | 'expense' | 'savings'>('expense')
  const [formParent, setFormParent] = useState('')
  const [formColor, setFormColor] = useState('#6b7280')
  const [formIcon, setFormIcon] = useState('')
  const [colorTab, setColorTab] = useState<'solid' | 'gradient' | 'animated'>('solid')
  const [customHex, setCustomHex] = useState('#6b7280')
  const [gradientAngle, setGradientAngle] = useState(135)
  const [gradientColors, setGradientColors] = useState<string[]>(['#ff6b6b', '#feca57'])
  const [midColorCount, setMidColorCount] = useState(0)
  const [saving, setSaving] = useState(false)
  const [savedTemplates, setSavedTemplates] = useState<SavedTemplate[]>(loadTemplates)
  const [templatePromptOpen, setTemplatePromptOpen] = useState(false)
  const [deleteCatTarget, setDeleteCatTarget] = useState<Category | null>(null)

  useEffect(() => { fetchCategories() }, [fetchCategories])

  const initGradientBuilder = (color: string) => {
    const parsed = parseGradient(color)
    if (parsed) {
      setGradientAngle(parsed.angle)
      setGradientColors(parsed.colors)
      setMidColorCount(Math.max(0, parsed.colors.length - 2))
    }
  }

  const openCreate = () => {
    setEditingId(null)
    setFormName('')
    setFormType('expense')
    setFormParent('')
    setFormColor('#6b7280')
    setFormIcon('')
    setColorTab('solid')
    setCustomHex('#6b7280')
    setGradientAngle(135)
    setGradientColors(['#ff6b6b', '#feca57'])
    setMidColorCount(0)
    setDialogOpen(true)
  }

  const openEdit = (cat: Category) => {
    setEditingId(cat.id)
    setFormName(cat.name)
    setFormType(cat.type as 'income' | 'expense' | 'savings')
    setFormParent(cat.parent_id ?? '')
    const color = cat.color || '#6b7280'
    setFormColor(color)
    setFormIcon(cat.icon || '')
    setCustomHex(color.startsWith('#') ? color : '#6b7280')
    initGradientBuilder(color)
    if (color.startsWith('animated:')) setColorTab('animated')
    else if (color.startsWith('linear-gradient') || color.startsWith('radial-gradient')) setColorTab('gradient')
    else setColorTab('solid')
    setDialogOpen(true)
  }

  const pickColor = (c: string) => {
    setFormColor(c)
    if (c.startsWith('#')) setCustomHex(c)
  }

  const pickGradientPreset = (value: string) => {
    pickColor(value)
    initGradientBuilder(value)
  }

  const updateGradientColor = (index: number, hex: string) => {
    const next = [...gradientColors]
    next[index] = hex
    setGradientColors(next)
    const prefix = colorTab === 'animated' ? 'animated:' : ''
    setFormColor(prefix + buildGradient(gradientAngle, next))
  }

  const updateGradientAngle = (angle: number) => {
    setGradientAngle(angle)
    const prefix = colorTab === 'animated' ? 'animated:' : ''
    setFormColor(prefix + buildGradient(angle, gradientColors))
  }

  const adjustMidColors = (delta: number) => {
    const nextCount = midColorCount + delta
    if (nextCount < 0 || nextCount > 4) return
    setMidColorCount(nextCount)
    if (delta > 0) {
      const next = [...gradientColors, '#6b7280']
      setGradientColors(next)
      const prefix = colorTab === 'animated' ? 'animated:' : ''
      setFormColor(prefix + buildGradient(gradientAngle, next))
    } else {
      const next = gradientColors.slice(0, -1)
      setGradientColors(next)
      const prefix = colorTab === 'animated' ? 'animated:' : ''
      setFormColor(prefix + buildGradient(gradientAngle, next))
    }
  }

  const handleSaveTemplate = () => {
    setTemplatePromptOpen(true)
  }

  const confirmSaveTemplate = (label: string) => {
    if (!label.trim()) return
    const tpl: SavedTemplate = {
      id: Date.now().toString(36),
      label: label.trim(),
      value: formColor,
      type: colorTab,
    }
    const next = [...savedTemplates, tpl]
    setSavedTemplates(next)
    saveTemplates(next)
    toast.success('Template saved')
  }

  const handleDeleteTemplate = (id: string) => {
    const next = savedTemplates.filter((t) => t.id !== id)
    setSavedTemplates(next)
    saveTemplates(next)
  }

  const handleSave = async () => {
    if (!formName.trim()) { toast.error('Name is required'); return }
    setSaving(true)
    try {
      const icon = formIcon.trim() || undefined
      if (editingId) {
        await updateCategory(editingId, {
          name: formName.trim(), type: formType, color: formColor, icon,
          parent_id: formParent || undefined,
          ...(formParent ? {} : { clear_parent: true }),
        })
        toast.success('Category updated')
      } else {
        await createCategory({
          name: formName.trim(), type: formType, color: formColor, icon,
          parent_id: formParent || undefined,
        })
        toast.success('Category created')
      }
      setDialogOpen(false)
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Failed to save category')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (cat: Category) => {
    if (cat.is_default) {
      setDeleteCatTarget(cat)
    } else {
      confirmDeleteCat(cat)
    }
  }

  const confirmDeleteCat = async (cat: Category) => {
    try {
      await deleteCategory(cat.id)
      toast.success('Category deleted')
    } catch (err: unknown) {
      toast.error(apiErrorDetail(err) || 'Failed to delete category')
    }
    setDeleteCatTarget(null)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Categories</h2>
        <Button appearance="primary" onClick={openCreate}>Add Category</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : categories.length === 0 ? (
        <p className="text-sm text-muted-foreground">No categories yet.</p>
      ) : (
        <div className="space-y-2">
          {categories
            .filter((c) => !c.parent_id)
            .flatMap((root) => [root, ...categories.filter((c) => c.parent_id === root.id)])
            .map((cat) => (
            <div
              key={cat.id}
              className={`flex items-center justify-between rounded-lg border px-4 py-3 ${cat.parent_id ? 'ml-6' : ''}`}
            >
              <div className="flex items-center gap-3">
                <ColorSwatch color={cat.color} size={14} />
                {cat.icon && <span className="text-base">{cat.icon}</span>}
                <div>
                  <span className="text-sm font-medium">{cat.name}</span>
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                    cat.type === 'income' ? 'bg-green-100 text-green-700' : cat.type === 'savings' ? 'bg-cyan-100 text-cyan-700' : cat.type === 'transfer' ? 'bg-indigo-100 text-indigo-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {cat.type}
                  </span>
                  {cat.is_default && (
                    <span className="ml-1.5 text-xs text-muted-foreground">(default)</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button appearance="transparent" icon={<Pencil size={15} />} onClick={() => openEdit(cat)} aria-label="Edit category" />
                <Button appearance="transparent" icon={<Trash2 size={15} />} onClick={() => handleDelete(cat)} aria-label="Delete category" style={{ color: 'var(--colorStatusDangerForeground1)' }} />
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(_, data) => { if (!data.open) setDialogOpen(false) }}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>{editingId ? 'Edit Category' : 'Add Category'}</DialogTitle>
            <DialogContent>
              <div className="space-y-4 pt-2">
                <Field label="Name">
                  <Input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="e.g. Subscriptions"
                  />
                </Field>

                <Field label="Type">
                  <div className="grid grid-cols-3 gap-2">
                    {(['expense', 'income', 'savings'] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setFormType(t)}
                        className={`rounded-lg border-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
                          formType === t ? 'border-primary bg-primary/5 text-primary' : 'border-border'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </Field>

                <Field label="Parent category (optional)" hint="Nest this under a top-level category, e.g. Family Savings under Savings">
                  <Select value={formParent} onChange={(e) => setFormParent(e.target.value)}>
                    <option value="">None (top-level)</option>
                    {categories
                      .filter((c) => !c.parent_id && c.id !== editingId && c.type !== 'transfer')
                      .map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.icon ? `${c.icon} ` : ''}{c.name}
                        </option>
                      ))}
                  </Select>
                </Field>

                <Field label="Icon (emoji)">
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {['🍕', '🚗', '🏠', '💡', '🎬', '🛍️', '🏥', '📚', '📋', '💰', '☕', '🍔', '🍺', '🎮', '✈️', '👕', '💊', '🎓', '🐾', '🎵', '🏋️', '📱', '💻', '🌿', '🔧', '🎁', '👶', '💼', '🏦', '📈'].map((emoji) => (
                      <button
                        key={emoji}
                        type="button"
                        onClick={() => setFormIcon(formIcon === emoji ? '' : emoji)}
                        className={`h-8 w-8 rounded-md text-lg flex items-center justify-center transition-all ${
                          formIcon === emoji ? 'ring-2 ring-primary ring-offset-1 scale-110' : 'hover:bg-muted'
                        }`}
                        title={emoji}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                  <Input
                    value={formIcon}
                    onChange={(e) => setFormIcon(e.target.value)}
                    placeholder="Or type any emoji..."
                    maxLength={10}
                  />
                </Field>

                <Field label="Color">
                  {/* Preview */}
                  <div className="flex items-center gap-3 mb-3">
                    <ColorSwatch color={formColor} size={32} />
                    <code className="text-xs text-muted-foreground break-all flex-1">{formColor}</code>
                  </div>

                  {/* Color mode tabs */}
                  <div className="grid grid-cols-3 gap-1 mb-3">
                    {(['solid', 'gradient', 'animated'] as const).map((tab) => (
                      <button
                        key={tab}
                        type="button"
                        onClick={() => setColorTab(tab)}
                        className={`rounded-md px-2 py-1.5 text-xs font-medium capitalize transition-colors ${
                          colorTab === tab ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'
                        }`}
                      >
                        {tab === 'animated' ? 'Animated' : tab}
                      </button>
                    ))}
                  </div>

                  {/* Solid colors */}
                  {colorTab === 'solid' && (
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {SOLID_COLORS.map((c) => (
                          <button
                            key={c}
                            type="button"
                            onClick={() => pickColor(c)}
                            className={`h-8 w-8 rounded-full border-2 transition-all ${
                              formColor === c ? 'border-foreground scale-110' : 'border-transparent'
                            }`}
                            style={{ backgroundColor: c }}
                            aria-label={c}
                          />
                        ))}
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          value={customHex}
                          onChange={(e) => pickColor(e.target.value)}
                          className="h-8 w-10 rounded border cursor-pointer"
                        />
                        <input
                          type="text"
                          value={customHex}
                          onChange={(e) => {
                            const v = e.target.value
                            setCustomHex(v)
                            if (/^#[0-9a-fA-F]{6}$/.test(v)) pickColor(v)
                          }}
                          placeholder="#hex"
                          className="flex-1 rounded-md border border-input bg-background px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>

                      {/* Save button */}
                      <button
                        type="button"
                        onClick={handleSaveTemplate}
                        className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                      >
                        <Save size={13} /> Save current color as template
                      </button>

                      {/* Saved solid templates */}
                      {savedTemplates.filter(t => t.type === 'solid').length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-2">Saved</p>
                          <div className="flex flex-wrap gap-2">
                            {savedTemplates.filter(t => t.type === 'solid').map((tpl) => (
                              <div key={tpl.id} className="relative group">
                                <button
                                  type="button"
                                  onClick={() => pickColor(tpl.value)}
                                  className={`h-8 w-8 rounded-full border-2 transition-all ${
                                    formColor === tpl.value ? 'border-foreground scale-110' : 'border-transparent'
                                  }`}
                                  style={{ backgroundColor: tpl.value }}
                                  title={tpl.label}
                                />
                                <button
                                  type="button"
                                  onClick={() => handleDeleteTemplate(tpl.id)}
                                  className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-[10px] leading-none"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Gradient & Animated — presets + custom builder */}
                  {(colorTab === 'gradient' || colorTab === 'animated') && (
                    <div className="space-y-4">
                      {/* Presets row */}
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Presets</p>
                        <div className="flex flex-wrap gap-2">
                          {GRADIENT_PRESETS.map((g) => {
                            const val = colorTab === 'animated' ? `animated:${g.value}` : g.value
                            return (
                              <button
                                key={val}
                                type="button"
                                onClick={() => pickGradientPreset(val)}
                                className={`h-10 w-14 rounded-lg border-2 transition-all ${
                                  formColor === val ? 'border-foreground scale-110' : 'border-transparent'
                                }`}
                                style={{ background: g.value, backgroundSize: colorTab === 'animated' ? '200% 200%' : undefined }}
                                title={g.label}
                                aria-label={g.label}
                              />
                            )
                          })}
                        </div>
                      </div>

                      {/* Custom gradient builder */}
                      <div className="rounded-lg border p-3 space-y-3">
                        <p className="text-xs font-medium text-muted-foreground">Custom</p>

                        {/* Angle slider */}
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-muted-foreground shrink-0 w-10">Angle</span>
                          <input
                            type="range"
                            min="0"
                            max="360"
                            value={gradientAngle}
                            onChange={(e) => updateGradientAngle(Number(e.target.value))}
                            className="flex-1 h-1.5 rounded-full appearance-none cursor-pointer accent-foreground"
                            style={{ background: `linear-gradient(to right, #000 ${gradientAngle / 360 * 100}%, #e5e7eb ${gradientAngle / 360 * 100}%)` }}
                          />
                          <span className="text-xs font-mono w-8 text-right">{gradientAngle}°</span>
                        </div>

                        {/* Color stops */}
                        {gradientColors.map((hex, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground w-16 shrink-0">
                              {i === 0 ? 'Start' : i === gradientColors.length - 1 ? 'End' : `Mid ${i}`}
                            </span>
                            <input
                              type="color"
                              value={hex}
                              onChange={(e) => updateGradientColor(i, e.target.value)}
                              className="h-8 w-10 rounded border cursor-pointer shrink-0"
                            />
                            <input
                              type="text"
                              value={hex}
                              onChange={(e) => {
                                const v = e.target.value
                                if (/^#[0-9a-fA-F]{0,6}$/.test(v)) updateGradientColor(i, v)
                              }}
                              className="flex-1 rounded-md border border-input bg-background px-2 py-1 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-ring"
                            />
                          </div>
                        ))}

                        {/* Middle color controls */}
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => adjustMidColors(1)}
                            disabled={midColorCount >= 4}
                            className="text-xs text-primary hover:underline disabled:opacity-30 disabled:no-underline"
                          >
                            + Add middle color
                          </button>
                          {midColorCount > 0 && (
                            <>
                              <span className="text-xs text-muted-foreground">{midColorCount}/4</span>
                              <button
                                type="button"
                                onClick={() => adjustMidColors(-1)}
                                className="text-xs text-red-500 hover:underline"
                              >
                                – Remove
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Save template button */}
                      <button
                        type="button"
                        onClick={handleSaveTemplate}
                        className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                      >
                        <Save size={13} /> Save current as template
                      </button>

                      {/* Saved gradient/animated templates */}
                      {savedTemplates.filter(t => t.type === colorTab).length > 0 && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-2">Saved</p>
                          <div className="flex flex-wrap gap-2">
                            {savedTemplates.filter(t => t.type === colorTab).map((tpl) => {
                              const bg = tpl.value.startsWith('animated:') ? tpl.value.slice(9) : tpl.value
                              return (
                                <div key={tpl.id} className="relative group">
                                  <button
                                    type="button"
                                    onClick={() => pickGradientPreset(tpl.value)}
                                    className={`h-10 w-14 rounded-lg border-2 transition-all ${
                                      formColor === tpl.value ? 'border-foreground scale-110' : 'border-transparent'
                                    }`}
                                    style={{ background: bg, backgroundSize: tpl.value.startsWith('animated:') ? '200% 200%' : undefined }}
                                    title={tpl.label}
                                  />
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteTemplate(tpl.id)}
                                    className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-[10px] leading-none"
                                  >
                                    ×
                                  </button>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </Field>
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      {/* Template name prompt */}
      <PromptDialog
        open={templatePromptOpen}
        onOpenChange={setTemplatePromptOpen}
        title="Save template"
        message="Give this color template a name."
        defaultValue={colorTab === 'solid' ? customHex : colorTab}
        onConfirm={confirmSaveTemplate}
      />

      {/* Delete default category confirmation */}
      <ConfirmDialog
        open={deleteCatTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteCatTarget(null) }}
        title="Delete default category?"
        message={`"${deleteCatTarget?.name ?? ''}" is a default category. Delete anyway?`}
        confirmLabel="Delete"
        destructive
        onConfirm={() => deleteCatTarget && confirmDeleteCat(deleteCatTarget)}
      />
    </div>
  )
}

// ─── Exchange Rate API Settings (sub-component) ──────────────────────────────

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

// ─── Exchange Rates Tab ───────────────────────────────────────────────────────

function ExchangeRatesTab() {
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

// ─── Banks Tab ───────────────────────────────────────────────────────────

const BANK_NAMES = ['Etihad Bank', 'Bank of Jordan', 'Arab Bank', 'Jordan Islamic Bank', 'HBTF', 'Cairo Amman Bank', 'Other']

function BanksTab() {
  const { connections, loading, fetchConnections, createConnection, updateConnection, deleteConnection, syncConnection } = useBankConnections()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [formName, setFormName] = useState('')
  const [formAuthType, setFormAuthType] = useState<'api_key' | 'basic'>('api_key')
  const [formApiUrl, setFormApiUrl] = useState('')
  const [formApiKey, setFormApiKey] = useState('')
  const [formUsername, setFormUsername] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formAccount, setFormAccount] = useState('')
  const [saving, setSaving] = useState(false)
  const [syncingId, setSyncingId] = useState<number | null>(null)

  useEffect(() => {
    fetchConnections()
  }, [fetchConnections])

  const openCreate = () => {
    setFormName('')
    setFormAuthType('api_key')
    setFormApiUrl('')
    setFormApiKey('')
    setFormUsername('')
    setFormPassword('')
    setFormAccount('')
    setDialogOpen(true)
  }

  const handleCreate = async () => {
    if (!formName.trim()) { toast.error('Bank name is required.'); return }
    setSaving(true)
    try {
      const credentials: Record<string, string> = {}
      if (formAuthType === 'basic') {
        credentials.api_url = formApiUrl
        credentials.username = formUsername
        credentials.password = formPassword
      } else {
        credentials.api_url = formApiUrl
        credentials.api_key = formApiKey
      }
      await createConnection({
        bank_name: formName.trim(),
        auth_type: formAuthType,
        credentials,
        account_number: formAccount.trim(),
      })
      toast.success('Bank connection created.')
      setDialogOpen(false)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create connection.')
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (conn: BankConnection) => {
    try {
      await updateConnection(conn.id, { is_active: !conn.is_active })
      toast.success(conn.is_active ? 'Disabled.' : 'Enabled.')
    } catch {
      toast.error('Failed to update.')
    }
  }

  const handleDelete = async (conn: BankConnection) => {
    try {
      await deleteConnection(conn.id)
      toast.success('Connection removed.')
    } catch {
      toast.error('Failed to delete.')
    }
  }

  const handleSync = async (conn: BankConnection) => {
    setSyncingId(conn.id)
    try {
      const result = await syncConnection(conn.id)
      toast.success(`Synced: ${result.imported} imported, ${result.skipped} skipped.`)
      await fetchConnections()
    } catch {
      toast.error('Sync failed.')
    } finally {
      setSyncingId(null)
    }
  }

  const formatDate = (iso: string | null) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleDateString()
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Bank Connections</h2>
        <Button appearance="primary" onClick={openCreate}>Add Bank</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : connections.length === 0 ? (
        <p className="text-sm text-muted-foreground">No bank connections yet.</p>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => (
            <Card key={conn.id} className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{conn.bank_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {conn.account_number} · {conn.auth_type} · Last sync: {formatDate(conn.last_sync_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="small"
                    appearance="outline"
                    disabled={syncingId === conn.id}
                    onClick={() => handleSync(conn)}
                  >
                    {syncingId === conn.id ? 'Syncing…' : 'Sync'}
                  </Button>
                  <label className="relative inline-flex cursor-pointer items-center">
                    <input
                      type="checkbox"
                      className="peer sr-only"
                      checked={conn.is_active}
                      onChange={() => handleToggle(conn)}
                    />
                    <div className="peer h-5 w-9 rounded-full bg-muted after:absolute after:left-[1px] after:top-[1px] after:h-[18px] after:w-[18px] after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-primary peer-checked:after:translate-x-full peer-checked:after:border-white" />
                  </label>
                  <Button
                    size="small"
                    appearance="subtle"
                    style={{ color: 'var(--colorStatusDangerForeground1)' }}
                    onClick={() => handleDelete(conn)}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(_, data) => { if (!data.open) setDialogOpen(false) }}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Add Bank Connection</DialogTitle>
            <DialogContent>
              <div className="space-y-4 pt-2">
                <Field label="Bank Name">
                  <div className="flex flex-wrap gap-2 mb-2">
                    {BANK_NAMES.map((name) => (
                      <button
                        key={name}
                        type="button"
                        onClick={() => setFormName(name === formName ? '' : name)}
                        className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                          formName === name ? 'border-primary bg-primary/5 text-primary' : 'border-border hover:border-muted-foreground/50'
                        }`}
                      >
                        {name}
                      </button>
                    ))}
                  </div>
                  <Input
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="Or type a custom name…"
                  />
                </Field>

                <Field label="Account Number">
                  <Input
                    value={formAccount}
                    onChange={(e) => setFormAccount(e.target.value)}
                    placeholder="e.g. 1234567890"
                  />
                </Field>

                <Field label="Auth Type">
                  <div className="grid grid-cols-2 gap-2">
                    {(['api_key', 'basic'] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setFormAuthType(t)}
                        className={`rounded-lg border-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
                          formAuthType === t ? 'border-primary bg-primary/5 text-primary' : 'border-border'
                        }`}
                      >
                        {t === 'api_key' ? 'API Key' : 'Basic Auth'}
                      </button>
                    ))}
                  </div>
                </Field>

                <Field label="API URL">
                  <Input
                    value={formApiUrl}
                    onChange={(e) => setFormApiUrl(e.target.value)}
                    placeholder="https://api.bank.com/transactions"
                  />
                </Field>

                {formAuthType === 'basic' ? (
                  <>
                    <Field label="Username">
                      <Input
                        value={formUsername}
                        onChange={(e) => setFormUsername(e.target.value)}
                        autoComplete="off"
                      />
                    </Field>
                    <Field label="Password">
                      <Input
                        type="password"
                        value={formPassword}
                        onChange={(e) => setFormPassword(e.target.value)}
                        autoComplete="off"
                      />
                    </Field>
                  </>
                ) : (
                  <Field label="API Key">
                    <Input
                      type="password"
                      value={formApiKey}
                      onChange={(e) => setFormApiKey(e.target.value)}
                      autoComplete="off"
                    />
                  </Field>
                )}
              </div>
            </DialogContent>
            <DialogActions>
              <Button appearance="outline" onClick={() => setDialogOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button appearance="primary" onClick={handleCreate} disabled={saving}>
                {saving ? 'Saving…' : 'Add'}
              </Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  )
}

// ─── Security Tab ─────────────────────────────────────────────────────────────

function SecurityTab() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleChangePassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error('Please fill in all fields.')
      return
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      toast.info('Password change not yet available in this version.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <Card className="p-4">
        <h3 className="text-base font-semibold mb-1">Change Password</h3>
        <p className="text-sm text-muted-foreground mb-4">Update your account password.</p>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="current-password">Current Password</Label>
            <Input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-password">New Password</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm-password">Confirm New Password</Label>
            <Input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
            />
          </div>
          <Button type="submit" appearance="primary" disabled={submitting}>
            {submitting ? 'Saving…' : 'Change Password'}
          </Button>
        </form>
      </Card>

      {/* Recovery Phrase */}
      <Card className="p-4 opacity-60">
        <h3 className="text-base font-semibold mb-1">Recovery Phrase</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Recovery phrase can be viewed after entering your passphrase.
        </p>
        <p className="mb-4 text-sm text-muted-foreground">
          Recovery phrase display — coming soon.
        </p>
        <Button appearance="outline" disabled>
          View Recovery Phrase
        </Button>
      </Card>
    </div>
  )
}

// ─── AI Tab ───────────────────────────────────────────────────────────────────

type Provider = 'openai' | 'gemini' | 'groq'

interface AiSettings {
  ai_provider: Provider
  openai_api_key: string
  openai_model: string
  gemini_api_key: string
  gemini_model: string
  groq_api_key: string
  groq_model: string
  local_whisper_model: string
  ai_ready: boolean
  transcription_ready: boolean
  transcription_backend: string
  model: string
}

const OPENAI_MODELS = ['gpt-4o-mini', 'gpt-4o', 'gpt-4.1-mini', 'gpt-4.1', 'o3-mini', 'o4-mini']
const GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemma-3-27b-it', 'gemma-3-12b-it']
const GROQ_MODELS   = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it', 'gemma-7b-it']
const WHISPER_SIZES = ['tiny', 'base', 'small', 'medium', 'large-v3']

function ModelInput({ id, value, onChange, list }: {
  id: string
  value: string
  onChange: (v: string) => void
  list: string[]
}) {
  const listId = `${id}-list`
  return (
    <>
      <input
        id={id}
        type="text"
        list={listId}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Type or choose a model name"
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        autoComplete="off"
        spellCheck={false}
      />
      <datalist id={listId}>
        {list.map(m => <option key={m} value={m} />)}
      </datalist>
    </>
  )
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full shrink-0 ${ok ? 'bg-green-500' : 'bg-amber-400'}`} />
      <span className="text-sm">{label}</span>
    </div>
  )
}

function AiTab() {
  const [cfg, setCfg] = useState<AiSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Editable fields — keys left blank = keep current
  const [provider, setProvider] = useState<Provider>('openai')
  const [openaiKey, setOpenaiKey] = useState('')
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini')
  const [geminiKey, setGeminiKey] = useState('')
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash')
  const [groqKey, setGroqKey] = useState('')
  const [groqModel, setGroqModel] = useState('llama-3.3-70b-versatile')
  const [localModel, setLocalModel] = useState('small')

  const load = () => {
    setLoading(true)
    api.get<AiSettings>('/api/ai-settings')
      .then(r => {
        setCfg(r.data)
        setProvider(r.data.ai_provider)
        setOpenaiModel(r.data.openai_model)
        setGeminiModel(r.data.gemini_model)
        setGroqModel(r.data.groq_model)
        setLocalModel(r.data.local_whisper_model)
        // Don't pre-fill key fields — user types to update
      })
      .catch(() => toast.error('Failed to load AI settings.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      const patch: Record<string, string | null> = {
        ai_provider: provider,
        openai_model: openaiModel,
        gemini_model: geminiModel,
        groq_model: groqModel,
        local_whisper_model: localModel,
        // Only send key if user typed something; null = keep existing
        openai_api_key: openaiKey || null,
        gemini_api_key: geminiKey || null,
        groq_api_key: groqKey || null,
      }
      const { data } = await api.put<AiSettings>('/api/ai-settings', patch)
      setCfg(data)
      setOpenaiKey('')
      setGeminiKey('')
      setGroqKey('')
      toast.success('AI settings saved.')
    } catch {
      toast.error('Failed to save AI settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading…</p>

  return (
    <div className="space-y-6">

      {/* Status */}
      {cfg && (
        <Card className="p-4">
          <h3 className="text-base font-semibold mb-3">Status</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Active model</p>
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{cfg.model}</code>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Transcription</p>
              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">{cfg.transcription_backend}</code>
            </div>
            <StatusBadge ok={cfg.ai_ready} label={cfg.ai_ready ? 'Expense parsing ready' : 'Expense parsing — no API key'} />
            <StatusBadge ok={cfg.transcription_ready} label="Voice transcription ready" />
          </div>
        </Card>
      )}

      {/* Provider */}
      <Card className="p-4 space-y-4">
        <h3 className="text-base font-semibold">LLM Provider</h3>

        <div className="grid grid-cols-3 gap-2">
          {(['openai', 'gemini', 'groq'] as Provider[]).map(p => (
            <button
              key={p}
              type="button"
              onClick={() => setProvider(p)}
              className={`rounded-lg border-2 px-3 py-2.5 text-sm font-medium transition-colors capitalize ${
                provider === p ? 'border-primary bg-primary/5 text-primary' : 'border-border hover:border-muted-foreground/50'
              }`}
            >
              {p === 'openai' ? 'OpenAI' : p === 'gemini' ? 'Gemini' : 'Groq'}
            </button>
          ))}
        </div>

        {/* OpenAI */}
        {provider === 'openai' && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="openai-key">API Key</Label>
              <Input
                id="openai-key"
                type="password"
                placeholder={cfg?.openai_api_key || 'sk-… (leave blank to keep current)'}
                value={openaiKey}
                onChange={e => setOpenaiKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="openai-model">Model</Label>
              <ModelInput id="openai-model" value={openaiModel} onChange={setOpenaiModel} list={OPENAI_MODELS} />
            </div>
          </div>
        )}

        {/* Gemini */}
        {provider === 'gemini' && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="gemini-key">API Key</Label>
              <Input
                id="gemini-key"
                type="password"
                placeholder={cfg?.gemini_api_key || 'AIza… (leave blank to keep current)'}
                value={geminiKey}
                onChange={e => setGeminiKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="gemini-model">Model</Label>
              <ModelInput id="gemini-model" value={geminiModel} onChange={setGeminiModel} list={GEMINI_MODELS} />
            </div>
          </div>
        )}

        {/* Groq */}
        {provider === 'groq' && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              Groq provides a free tier. Get a key at console.groq.com. Uses <code className="bg-muted px-1 rounded">llama-3.3-70b-versatile</code> for expense parsing and <code className="bg-muted px-1 rounded">whisper-large-v3</code> for transcription.
            </p>
            <div className="space-y-1.5">
              <Label htmlFor="groq-key">API Key</Label>
              <Input
                id="groq-key"
                type="password"
                placeholder={cfg?.groq_api_key || 'gsk_… (leave blank to keep current)'}
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="groq-model">Model</Label>
              <ModelInput id="groq-model" value={groqModel} onChange={setGroqModel} list={GROQ_MODELS} />
            </div>
          </div>
        )}
      </Card>

      {/* Voice transcription */}
      <Card className="p-4 space-y-3">
        <div>
          <h3 className="text-base font-semibold">Voice Transcription</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Groq key → Groq (free). OpenAI key → OpenAI. Neither → local faster-whisper (offline, ~484 MB download on first use).
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="groq-transcription-key">Groq Key (for free cloud transcription)</Label>
          <Input
            id="groq-transcription-key"
            type="password"
            placeholder={cfg?.groq_api_key || 'gsk_… (leave blank to keep current)'}
            value={groqKey}
            onChange={e => setGroqKey(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="local-model">Local Whisper model (offline fallback)</Label>
          <ModelInput id="local-model" value={localModel} onChange={setLocalModel} list={WHISPER_SIZES} />
        </div>
      </Card>

      <Button appearance="primary" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving…' : 'Save Settings'}
      </Button>
    </div>
  )
}

// ─── About Tab ────────────────────────────────────────────────────────────────

function AboutTab() {
  return (
    <div className="space-y-6">
      <Card className="p-4">
        <h3 className="text-lg font-semibold mb-1">ZeroWhisper</h3>
        <p className="text-sm text-muted-foreground mb-4">Version 0.1.0</p>
        <p className="text-sm text-muted-foreground mb-4">
          Self-hosted personal financial manager with encrypted storage.
        </p>
        <div>
          <p className="mb-2 text-sm font-semibold">Tech Stack</p>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>FastAPI</li>
            <li>SQLCipher</li>
            <li>React</li>
            <li>Fluent UI v9</li>
            <li>OpenAI / Google Gemini</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const VALID_TABS = ['api-keys', 'categories', 'exchange-rates', 'banks', 'security', 'ai', 'about'] as const

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
          selectedValue={activeTab}
          onTabSelect={(_, d) => setActiveTab(d.value as string)}
          className="mb-4 flex-nowrap"
        >
          <Tab value="api-keys">API Keys</Tab>
          <Tab value="categories">Categories</Tab>
          <Tab value="exchange-rates">Rates</Tab>
          <Tab value="banks">Banks</Tab>
          <Tab value="security">Security</Tab>
          <Tab value="ai">AI</Tab>
          <Tab value="about">About</Tab>
        </TabList>
      </div>

      {activeTab === 'api-keys' && <ApiKeysTab />}
      {activeTab === 'categories' && <CategoriesTab />}
      {activeTab === 'exchange-rates' && <ExchangeRatesTab />}
      {activeTab === 'banks' && <BanksTab />}
      {activeTab === 'security' && <SecurityTab />}
      {activeTab === 'ai' && <AiTab />}
      {activeTab === 'about' && <AboutTab />}
    </div>
  )
}
