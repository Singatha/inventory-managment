export type UserRole = 'ADMIN' | 'WAREHOUSE_MANAGER' | 'EMPLOYEE'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

