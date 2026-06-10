interface AvatarProps {
  name: string
  size?: number
}

export function Avatar({ name, size = 32 }: AvatarProps) {
  const initial = name.charAt(0).toUpperCase()
  return (
    <div
      className="inline-flex items-center justify-center bg-[var(--surface-container-high)] text-[var(--on-surface)] font-mono font-bold select-none"
      style={{ width: size, height: size, fontSize: size * 0.45 }}
    >
      {initial}
    </div>
  )
}
