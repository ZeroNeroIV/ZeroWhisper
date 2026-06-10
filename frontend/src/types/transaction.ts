export type TransactionType = 'expense' | 'income' | 'transfer_out' | 'transfer_in'

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
  type: TransactionType
  wallet_id: string | null
  transfer_id: string | null
  created_at: string
}

export interface TransactionFormData {
  amount_original: number
  currency_original: 'JOD' | 'USD'
  category: string
  description?: string
  transaction_date: string
  wallet_id?: string | null
}

export const VALID_CURRENCIES = ['JOD', 'USD'] as const
