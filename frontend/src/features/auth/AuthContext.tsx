import { createContext, type PropsWithChildren, useContext } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getCurrentUser, login } from '../../api/auth'
import type { LoginCredentials, User } from '../../types/auth'
import { tokenStorage } from './tokenStorage'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient()
  const sessionExists = tokenStorage.hasSession()
  const currentUser = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getCurrentUser,
    enabled: sessionExists,
    retry: false,
    staleTime: 60_000,
  })
  const loginMutation = useMutation({ mutationFn: login })

  async function signIn(credentials: LoginCredentials): Promise<User> {
    const tokens = await loginMutation.mutateAsync(credentials)
    tokenStorage.setTokens(tokens)
    queryClient.setQueryData(['auth', 'me'], tokens.user)
    return tokens.user
  }

  function signOut() {
    tokenStorage.clear()
    queryClient.removeQueries({ queryKey: ['auth'] })
  }

  const user = currentUser.data ?? null
  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading: sessionExists && currentUser.isLoading,
        isAuthenticated: Boolean(user),
        login: signIn,
        logout: signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// The hook intentionally shares this module with its provider as one public auth API.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
