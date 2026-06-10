import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { type AxiosError } from 'axios'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Field } from '@/components/ui/Field'
import { Card } from '@/components/ui/Card'
import { TabList, Tab } from '@/components/ui/Tabs'

import { useAuth } from '@/hooks/useAuth'

// ── Zod schemas ──────────────────────────────────────────────────────────────

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  password_confirm: z.string().min(8, 'Password must be at least 8 characters'),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Passwords do not match',
  path: ['password_confirm'],
})

type LoginFormData = z.infer<typeof loginSchema>
type RegisterFormData = z.infer<typeof registerSchema>

// ── Helper to extract a readable error message ────────────────────────────────

function getErrorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ detail?: string | { msg: string }[] }>
  if (axiosError.response?.data?.detail) {
    const detail = axiosError.response.data.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
  }
  if (axiosError.message) return axiosError.message
  return 'An unexpected error occurred.'
}

// ── Login sub-form ────────────────────────────────────────────────────────────

function LoginForm() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  })

  const onSubmit = async (values: LoginFormData) => {
    setError(null)
    try {
      await login(values.username, values.password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Username">
        <Input placeholder="your_username" autoComplete="username" {...register('username')} />
      </Field>
      {errors.username?.message && (
        <p className="text-sm text-red-500">{errors.username.message}</p>
      )}

      <Field label="Password">
        <Input
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          {...register('password')}
        />
      </Field>
      {errors.password?.message && (
        <p className="text-sm text-red-500">{errors.password.message}</p>
      )}

      {error && (
        <p className="text-sm font-medium text-red-600">{error}</p>
      )}

      <Button type="submit" appearance="primary" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Signing in…' : 'Sign in'}
      </Button>
    </form>
  )
}

// ── Register sub-form ─────────────────────────────────────────────────────────

function RegisterForm() {
  const { register: registerUser, login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: '', email: '', password: '', password_confirm: '' },
  })

  const onSubmit = async (values: RegisterFormData) => {
    setError(null)
    try {
      await registerUser(values.username, values.email, values.password, values.password_confirm)
      await login(values.username, values.password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Field label="Username">
        <Input placeholder="your_username" autoComplete="username" {...register('username')} />
      </Field>
      {errors.username?.message && (
        <p className="text-sm text-red-500">{errors.username.message}</p>
      )}

      <Field label="Email">
        <Input
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          {...register('email')}
        />
      </Field>
      {errors.email?.message && (
        <p className="text-sm text-red-500">{errors.email.message}</p>
      )}

      <Field label="Password">
        <Input
          type="password"
          placeholder="••••••••"
          autoComplete="new-password"
          {...register('password')}
        />
      </Field>
      {errors.password?.message && (
        <p className="text-sm text-red-500">{errors.password.message}</p>
      )}

      <Field label="Confirm password">
        <Input
          type="password"
          placeholder="••••••••"
          autoComplete="new-password"
          {...register('password_confirm')}
        />
      </Field>
      {errors.password_confirm?.message && (
        <p className="text-sm text-red-500">{errors.password_confirm.message}</p>
      )}

      {error && (
        <p className="text-sm font-medium text-red-600">{error}</p>
      )}

      <Button type="submit" appearance="primary" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Creating account…' : 'Create account'}
      </Button>
    </form>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState('login')
  const [checking, setChecking] = useState(true)
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
      return
    }

    const checkDb = async () => {
      try {
        const { data } = await api.get('/setup/status')
        if (!data.db_ready || data.state !== 'INITIALIZED') {
          navigate('/setup', { replace: true })
          return
        }
      } catch {
        /* Can't reach backend — show login as fallback */
      }
      setChecking(false)
    }
    checkDb()
  }, [isAuthenticated, navigate])

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <Card className="p-6">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold">ZeroWhisper</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Personal finance, made quiet.
            </p>
          </div>

          <TabList
            selectedTab={activeTab}
            onTabSelect={(tab) => setActiveTab(tab)}
            className="w-full mb-6"
          >
            <Tab id="login">Sign in</Tab>
            <Tab id="register">Register</Tab>
          </TabList>

          {activeTab === 'login' && <LoginForm />}
          {activeTab === 'register' && <RegisterForm />}

          <p className="mt-6 text-center text-xs text-muted-foreground">
            First time?{' '}
            <Link to="/setup" className="font-medium underline underline-offset-4 hover:text-foreground">
              Initialize the database
            </Link>{' '}
            first.
          </p>
        </Card>
      </div>
    </div>
  )
}
