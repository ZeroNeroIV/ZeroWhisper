import type { Category } from '@/types/category'

export function renderCategoryLabel(categoryName: string, categories: Category[]): React.ReactNode {
  const cat = categories.find((c) => c.name === categoryName)
  const color = cat?.color
  const icon = cat?.icon

  const textEl = (() => {
    if (!color) return <span className="text-xs font-medium text-muted-foreground">{categoryName}</span>
    if (color.startsWith('animated:')) {
      return (
        <span
          className="text-xs font-medium animate-gradient"
          style={{ background: color.slice('animated:'.length), WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}
        >
          {categoryName}
        </span>
      )
    }
    if (color.startsWith('linear-gradient') || color.startsWith('radial-gradient')) {
      return (
        <span
          className="text-xs font-medium"
          style={{ background: color, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}
        >
          {categoryName}
        </span>
      )
    }
    return <span className="text-xs font-medium" style={{ color }}>{categoryName}</span>
  })()

  if (icon) {
    return (
      <>
        <span className="inline md:hidden text-base">{icon}</span>
        <span className="hidden md:inline">{textEl}</span>
      </>
    )
  }
  return textEl
}
