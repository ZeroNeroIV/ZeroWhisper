interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
}

export function Switch({ checked, onChange, label }: SwitchProps) {
  return (
    <button
      aria-label={label}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 items-center transition-colors duration-150 ${
        checked ? 'bg-[var(--primary)]' : 'bg-[var(--surface-container-high)]'
      }`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 bg-[var(--on-primary)] transition-transform duration-150 ${
          checked ? 'translate-x-[18px]' : 'translate-x-[3px]'
        }`}
      />
    </button>
  )
}
