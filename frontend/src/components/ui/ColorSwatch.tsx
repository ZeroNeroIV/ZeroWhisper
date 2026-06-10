import { isAnimated, isGradient, stripAnimated } from '@/lib/colorStyle'

export function ColorSwatch({ color, size = 10 }: { color: string | null; size?: number }) {
  if (!color) {
    return <span className="inline-block rounded-full shrink-0 bg-gray-300" style={{ width: size, height: size }} />
  }
  if (isGradient(color) || isAnimated(color)) {
    return (
      <span
        className={`inline-block rounded-full shrink-0 ${isAnimated(color) ? 'animate-gradient' : ''}`}
        style={{
          width: size,
          height: size,
          background: stripAnimated(color),
          backgroundSize: isAnimated(color) ? '200% 200%' : undefined,
        }}
      />
    )
  }
  return <span className="inline-block rounded-full shrink-0" style={{ width: size, height: size, backgroundColor: color }} />
}
