import type { Category } from '@/types/category'
import { isAnimated, isGradient, stripAnimated } from '@/lib/colorStyle'

export function renderCategoryLabel(categoryName: string, categories: Category[]): React.ReactNode {
  const cat = categories.find((c) => c.name === categoryName)
  const color = cat?.color
  const icon = cat?.icon

  const textEl = (() => {
    if (!color) return <span className="text-xs font-medium text-muted-foreground">{categoryName}</span>
    if (isGradient(color) || isAnimated(color)) {
      return (
        <span
          className={`text-xs font-medium ${isAnimated(color) ? 'animate-gradient' : ''}`}
          style={{ background: stripAnimated(color), WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' } as React.CSSProperties}
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
