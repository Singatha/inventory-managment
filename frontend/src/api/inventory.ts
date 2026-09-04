import type {
  InventoryListResponse,
  InventoryOperationResponse,
  InventoryQuery,
  StockAdjustmentInput,
  StockReceiveInput,
} from '../types/inventory'
import { apiClient } from './client'

export async function getInventory(query: InventoryQuery): Promise<InventoryListResponse> {
  const response = await apiClient.get<InventoryListResponse>('/inventory', { params: query })
  return response.data
}

export async function getProductInventory(
  productId: number,
  pageSize = 100,
): Promise<InventoryListResponse> {
  const response = await apiClient.get<InventoryListResponse>(`/inventory/${productId}`, {
    params: { page: 1, page_size: pageSize },
  })
  return response.data
}

export async function receiveStock(input: StockReceiveInput): Promise<InventoryOperationResponse> {
  const response = await apiClient.post<InventoryOperationResponse>('/inventory/receive', input)
  return response.data
}

export async function adjustStock(
  input: StockAdjustmentInput,
): Promise<InventoryOperationResponse> {
  const response = await apiClient.post<InventoryOperationResponse>('/inventory/adjust', input)
  return response.data
}
