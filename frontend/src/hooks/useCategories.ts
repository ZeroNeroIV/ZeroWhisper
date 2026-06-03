import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Category, CategoryFormData } from '@/types/category'

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCategories = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<Category[]>('/api/categories')
      setCategories(data)
    } catch (err: any) {
      console.error('Failed to fetch categories:', err)
      const { toast } = await import('sonner')
      toast.error(err?.response?.data?.detail || 'Failed to load categories')
    } finally {
      setLoading(false)
    }
  }, [])

  const createCategory = async (body: CategoryFormData): Promise<Category> => {
    const { data } = await api.post<Category>('/api/categories', body)
    setCategories((prev) => [...prev, data])
    return data
  }

  const updateCategory = async (id: string, body: Partial<CategoryFormData>): Promise<Category> => {
    const { data } = await api.put<Category>(`/api/categories/${id}`, body)
    setCategories((prev) => prev.map((c) => (c.id === id ? data : c)))
    return data
  }

  const deleteCategory = async (id: string) => {
    await api.delete(`/api/categories/${id}`)
    setCategories((prev) => prev.filter((c) => c.id !== id))
  }

  return { categories, loading, fetchCategories, createCategory, updateCategory, deleteCategory }
}
