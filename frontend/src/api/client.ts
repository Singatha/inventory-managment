import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { TokenPair } from '../types/auth'
import { tokenStorage } from '../features/auth/tokenStorage'

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean
}

const baseURL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

apiClient.interceptors.request.use((config) => {
  const accessToken = tokenStorage.getAccessToken()
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

let refreshPromise: Promise<TokenPair> | null = null

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetryableRequest | undefined
    const isAuthRequest = request?.url?.includes('/auth/login') || request?.url?.includes('/auth/refresh')
    const refreshToken = tokenStorage.getRefreshToken()

    if (error.response?.status !== 401 || !request || request._retry || isAuthRequest || !refreshToken) {
      return Promise.reject(error)
    }

    request._retry = true
    refreshPromise ??= axios
      .post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token: refreshToken })
      .then(({ data }) => {
        tokenStorage.setTokens(data)
        return data
      })
      .finally(() => {
        refreshPromise = null
      })

    try {
      const tokens = await refreshPromise
      request.headers.Authorization = `Bearer ${tokens.access_token}`
      return apiClient(request)
    } catch (refreshError) {
      tokenStorage.clear()
      if (window.location.pathname !== '/login') window.location.assign('/login')
      return Promise.reject(refreshError)
    }
  },
)

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> }
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.error?.message || 'The request could not be completed.'
  }
  return 'An unexpected error occurred.'
}
