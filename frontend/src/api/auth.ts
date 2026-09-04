import type { LoginCredentials, TokenPair, User } from '../types/auth'
import { apiClient } from './client'

export async function login(credentials: LoginCredentials): Promise<TokenPair> {
  const response = await apiClient.post<TokenPair>('/auth/login', credentials)
  return response.data
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

