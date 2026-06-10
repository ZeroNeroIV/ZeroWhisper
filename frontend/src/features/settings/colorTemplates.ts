export interface SavedTemplate {
  id: string
  label: string
  value: string
  type: 'solid' | 'gradient' | 'animated'
}

const STORAGE_KEY = 'zw-saved-color-templates'

export function loadTemplates(): SavedTemplate[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

export function saveTemplates(templates: SavedTemplate[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
}
