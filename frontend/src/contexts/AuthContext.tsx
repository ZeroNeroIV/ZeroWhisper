import { useState, type ReactNode } from 'react'
import { api } from '@/lib/api'
import { AuthContext } from '@/contexts/auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(() =>
    localStorage.getItem('username')
  )
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => !!localStorage.getItem('access_token')
  )

  const login = async (username: string, password: string) => {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('username', username)
    setUsername(username)
    setIsAuthenticated(true)
  }

  const register = async (username: string, email: string, password: string, password_confirm: string) => {
    await api.post('/auth/register', { username, email, password, password_confirm })
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    setUsername(null)
    setIsAuthenticated(false)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
