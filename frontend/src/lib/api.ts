import axios from 'axios'

export const api = axios.create({ baseURL: '/' })

/** Extract the backend `detail` message from an unknown error, if present. */
export function apiErrorDetail(err: unknown): string | undefined {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return undefined
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    // DB not ready (vault locked / backend restarted) — send to setup
    if (
      error.response?.status === 503 &&
      error.response?.data?.detail?.includes('setup') &&
      !error.config?.url?.startsWith('/setup') &&
      !error.config?.url?.startsWith('/auth')
    ) {
      window.location.href = '/setup'
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post('/auth/refresh', { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
