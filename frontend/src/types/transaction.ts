export interface Transaction {
  id: string
  user_id: string
  amount_original: string
  currency_original: string
  amount_base: string
  exchange_rate: string
  category: string
  description: string | null
  transaction_date: string
  source: string
  created_at: string
}

export interface TransactionFormData {
  amount_original: number
  currency_original: 'JOD' | 'USD'
  category: string
  description?: string
  transaction_date: string
}

export const VALID_CATEGORIES = [
  'Food', 'Transport', 'Housing', 'Utilities', 'Entertainment',
  'Shopping', 'Health', 'Education', 'Income', 'Other'
] as const

export const VALID_CURRENCIES = ['JOD', 'USD'] as const
