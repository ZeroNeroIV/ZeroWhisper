export type CategoryType = 'income' | 'expense' | 'savings'

export interface Category {
  id: string
  user_id: string
  name: string
  type: CategoryType
  color: string | null
  icon: string | null
  is_default: boolean
}

export interface CategoryFormData {
  name: string
  type: CategoryType
  color?: string
  icon?: string
}
