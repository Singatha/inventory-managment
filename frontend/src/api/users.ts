import type { User, UserRole } from '../types/auth'
import { apiClient } from './client'

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  page_size: number
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  role?: UserRole
  is_active?: boolean
}

export async function getUsers(page: number, pageSize: number): Promise<UserListResponse> {
  const response = await apiClient.get<UserListResponse>('/users', { params: { page, page_size: pageSize } })
  return response.data
}

export async function updateUser(userId: number, changes: UserUpdate): Promise<User> {
  const response = await apiClient.patch<User>(`/users/${userId}`, changes)
  return response.data
}

