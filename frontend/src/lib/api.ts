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

// Single-flight token refresh: concurrent 401s share one refresh request
// instead of racing each other (the losers of that race would log the
// user out for no reason).
let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(refreshToken: string): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post('/auth/refresh', { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access_token)
        // The backend only rotates the refresh token if it sends a new one.
        if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
        return data.access_token as string
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (
      error.response?.status === 503 &&
      error.response?.data?.detail?.includes('setup') &&
      !error.config?.url?.startsWith('/setup')
    ) {
      window.location.href = '/setup'
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const accessToken = await refreshAccessToken(refresh)
          error.config.headers.Authorization = `Bearer ${accessToken}`
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
