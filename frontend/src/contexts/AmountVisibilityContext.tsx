import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'

interface AmountVisibilityContextValue {
  hidden: boolean
  toggle: () => void
}

const AmountVisibilityContext = createContext<AmountVisibilityContextValue>({
  hidden: false,
  toggle: () => {},
})

export function AmountVisibilityProvider({ children }: { children: ReactNode }) {
  const [hidden, setHidden] = useState(false)
  const toggle = () => setHidden(h => !h)
  return (
    <AmountVisibilityContext.Provider value={{ hidden, toggle }}>
      {children}
    </AmountVisibilityContext.Provider>
  )
}

export function useAmountVisibility() {
  return useContext(AmountVisibilityContext)
}
