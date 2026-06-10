/**
 * Category color protocol — the single parser/builder for color strings.
 *
 * A category color is one of:
 *   "#rrggbb"                          — solid
 *   "linear-gradient(45deg, a, b)"     — gradient
 *   "animated:linear-gradient(...)"    — gradient with the animate-gradient class
 */

export const ANIMATED_PREFIX = 'animated:'

export function isAnimated(color: string): boolean {
  return color.startsWith(ANIMATED_PREFIX)
}

export function isGradient(color: string): boolean {
  const value = stripAnimated(color)
  return value.startsWith('linear-gradient') || value.startsWith('radial-gradient')
}

/** The CSS background value, with the animated: marker removed. */
export function stripAnimated(color: string): string {
  return isAnimated(color) ? color.slice(ANIMATED_PREFIX.length) : color
}

export function parseGradient(gradient: string): { angle: number; colors: string[] } | null {
  const clean = stripAnimated(gradient)
  const match = clean.match(/linear-gradient\((\d+)deg,\s*(.*)\)/)
  if (!match) return null
  return { angle: parseInt(match[1]), colors: match[2].split(',').map((s) => s.trim()) }
}

export function buildGradient(angle: number, colors: string[]): string {
  return `linear-gradient(${angle}deg, ${colors.join(', ')})`
}
