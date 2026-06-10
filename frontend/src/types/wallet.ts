export type WalletType = 'cash' | 'digital' | 'savings' | 'credit' | 'other'

export interface Wallet {
  id: string
  name: string
  type: WalletType
  currency: 'JOD' | 'USD'
  balance: string
  initial_balance: string
  icon: string | null
  is_active: boolean
  created_at: string
}

export interface WalletFormData {
  name: string
  type: WalletType
  currency: 'JOD' | 'USD'
  initial_balance?: string
  icon?: string
}

export interface TransferFormData {
  from_wallet_id: string
  to_wallet_id: string
  amount_original: string
  currency_original: 'JOD' | 'USD'
  transaction_date?: string
  description?: string
}

export const WALLET_TYPE_LABELS: Record<WalletType, string> = {
  cash: 'Held Money',
  digital: 'Digital Money',
  savings: 'Savings',
  credit: 'Credit',
  other: 'Other',
}

export const WALLET_TYPE_ICONS: Record<WalletType, string> = {
  cash: '💵',
  digital: '💳',
  savings: '🏦',
  credit: '🧾',
  other: '👛',
}
