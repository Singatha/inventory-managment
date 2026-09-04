export interface Product {
  id: number
  sku: string
  name: string
  description: string | null
  category: string
  price: number
  reorder_level: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductInput {
  sku: string
  name: string
  description?: string | null
  category: string
  price: number
  reorder_level: number
  is_active: boolean
}

export type ProductSortField = 'sku' | 'name' | 'category' | 'price' | 'reorder_level' | 'created_at'
export type SortOrder = 'asc' | 'desc'

export interface ProductQuery {
  page: number
  page_size: number
  search?: string
  category?: string
  is_active?: boolean
  sort_by?: ProductSortField
  sort_order?: SortOrder
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
}

