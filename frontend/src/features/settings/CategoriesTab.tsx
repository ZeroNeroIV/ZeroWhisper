import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { Select } from '@/components/ui/Select'
import { Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, DialogActions } from '@/components/ui/Dialog'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { PromptDialog } from '@/components/ui/PromptDialog'
import { ColorSwatch } from '@/components/ui/ColorSwatch'
import { Pencil, Trash2, Save } from 'lucide-react'
import { useCategories } from '@/hooks/useCategories'
import type { Category } from '@/types/category'
import { apiErrorDetail } from '@/lib/api'
import { ANIMATED_PREFIX, buildGradient, isAnimated, isGradient, parseGradient, stripAnimated } from '@/lib/colorStyle'
import { loadTemplates, saveTemplates, type SavedTemplate } from './colorTemplates'

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

export function CategoriesTab() {
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
    if (isAnimated(color)) setColorTab('animated')
    else if (isGradient(color)) setColorTab('gradient')
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
    const prefix = colorTab === 'animated' ? ANIMATED_PREFIX : ''
    setFormColor(prefix + buildGradient(gradientAngle, next))
  }

  const updateGradientAngle = (angle: number) => {
    setGradientAngle(angle)
    const prefix = colorTab === 'animated' ? ANIMATED_PREFIX : ''
    setFormColor(prefix + buildGradient(angle, gradientColors))
  }

  const adjustMidColors = (delta: number) => {
    const nextCount = midColorCount + delta
    if (nextCount < 0 || nextCount > 4) return
    setMidColorCount(nextCount)
    if (delta > 0) {
      const next = [...gradientColors, '#6b7280']
      setGradientColors(next)
      const prefix = colorTab === 'animated' ? ANIMATED_PREFIX : ''
      setFormColor(prefix + buildGradient(gradientAngle, next))
    } else {
      const next = gradientColors.slice(0, -1)
      setGradientColors(next)
      const prefix = colorTab === 'animated' ? ANIMATED_PREFIX : ''
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
                <Button appearance="ghost" onClick={() => openEdit(cat)} aria-label="Edit category">
                  <Pencil size={15} />
                </Button>
                <Button appearance="ghost" onClick={() => handleDelete(cat)} aria-label="Delete category" className="text-red-500">
                  <Trash2 size={15} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) setDialogOpen(false) }}>
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

                <Field label="Parent category (optional)">
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
                            const val = colorTab === 'animated' ? ANIMATED_PREFIX + g.value : g.value
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
                              const bg = stripAnimated(tpl.value)
                              return (
                                <div key={tpl.id} className="relative group">
                                  <button
                                    type="button"
                                    onClick={() => pickGradientPreset(tpl.value)}
                                    className={`h-10 w-14 rounded-lg border-2 transition-all ${
                                      formColor === tpl.value ? 'border-foreground scale-110' : 'border-transparent'
                                    }`}
                                    style={{ background: bg, backgroundSize: isAnimated(tpl.value) ? '200% 200%' : undefined }}
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
              <Button appearance="secondary" onClick={() => setDialogOpen(false)} disabled={saving}>
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
