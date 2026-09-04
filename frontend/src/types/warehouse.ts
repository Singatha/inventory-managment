import type { SortOrder } from './product'

export interface Warehouse {
  id: number
  name: string
  code: string
  location: string
  created_at: string
  updated_at: string
}

export interface WarehouseInput {
  name: string
  code: string
  location: string
}

export type WarehouseSortField = 'code' | 'name' | 'location' | 'created_at'

export interface WarehouseQuery {
  page: number
  page_size: number
  search?: string
  sort_by?: WarehouseSortField
  sort_order?: SortOrder
}

export interface WarehouseListResponse {
  items: Warehouse[]
  total: number
  page: number
  page_size: number
}
