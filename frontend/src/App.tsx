import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { FluentProvider, webLightTheme, webDarkTheme } from '@fluentui/react-components'
import { AuthProvider } from '@/contexts/AuthContext'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import LoginPage from '@/pages/LoginPage'
import SetupPage from '@/pages/SetupPage'
import DashboardPage from '@/pages/DashboardPage'
import TransactionsPage from '@/pages/TransactionsPage'
import WhisperPage from '@/pages/WhisperPage'
import VisualizationsPage from '@/pages/VisualizationsPage'
import SettingsPage from '@/pages/SettingsPage'
import { useEffect, useState } from 'react'
import { Toaster } from 'sonner'

function ThemedApp() {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('theme')
    if (stored) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const handler = () => {
      const stored = localStorage.getItem('theme')
      if (stored) {
        setIsDark(stored === 'dark')
      }
    }
    window.addEventListener('storage', handler)
    // Also poll periodically to pick up same-tab changes
    const interval = setInterval(handler, 300)
    return () => {
      window.removeEventListener('storage', handler)
      clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  return (
    <FluentProvider theme={isDark ? webDarkTheme : webLightTheme}>
      <Toaster richColors position="top-right" />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/setup" element={<SetupPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="/whisper" element={<WhisperPage />} />
              <Route path="/visualizations" element={<VisualizationsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </FluentProvider>
  )
}

export default function App() {
  return <ThemedApp />
}
