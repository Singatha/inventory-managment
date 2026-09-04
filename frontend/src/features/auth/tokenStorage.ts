import type { TokenPair } from '../../types/auth'

const ACCESS_TOKEN_KEY = 'stockflow.access_token'
const REFRESH_TOKEN_KEY = 'stockflow.refresh_token'

export const tokenStorage = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  hasSession: () => Boolean(localStorage.getItem(ACCESS_TOKEN_KEY) || localStorage.getItem(REFRESH_TOKEN_KEY)),
  setTokens: (tokens: Pick<TokenPair, 'access_token' | 'refresh_token'>) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

