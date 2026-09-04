import type {
  Warehouse,
  WarehouseInput,
  WarehouseListResponse,
  WarehouseQuery,
} from '../types/warehouse'
import { apiClient } from './client'

export async function getWarehouses(query: WarehouseQuery): Promise<WarehouseListResponse> {
  const response = await apiClient.get<WarehouseListResponse>('/warehouses', { params: query })
  return response.data
}

export async function getWarehouse(warehouseId: number): Promise<Warehouse> {
  const response = await apiClient.get<Warehouse>(`/warehouses/${warehouseId}`)
  return response.data
}

export async function createWarehouse(input: WarehouseInput): Promise<Warehouse> {
  const response = await apiClient.post<Warehouse>('/warehouses', input)
  return response.data
}

export async function updateWarehouse(
  warehouseId: number,
  input: WarehouseInput,
): Promise<Warehouse> {
  const response = await apiClient.put<Warehouse>(`/warehouses/${warehouseId}`, input)
  return response.data
}

export async function deleteWarehouse(warehouseId: number): Promise<void> {
  await apiClient.delete(`/warehouses/${warehouseId}`)
}
