import type {
  Order,
  OrderAction,
  OrderInput,
  OrderListResponse,
  OrderQuery,
} from '../types/order'
import { apiClient } from './client'

export async function getOrders(query: OrderQuery): Promise<OrderListResponse> {
  const response = await apiClient.get<OrderListResponse>('/orders', { params: query })
  return response.data
}

export async function getOrder(orderId: number): Promise<Order> {
  const response = await apiClient.get<Order>(`/orders/${orderId}`)
  return response.data
}

export async function createOrder(input: OrderInput): Promise<Order> {
  const response = await apiClient.post<Order>('/orders', input)
  return response.data
}

export async function transitionOrder(orderId: number, action: OrderAction): Promise<Order> {
  const response = await apiClient.post<Order>(`/orders/${orderId}/${action}`)
  return response.data
}
