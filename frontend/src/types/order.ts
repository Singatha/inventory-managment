export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'COMPLETED'
  | 'CANCELLED'

export interface OrderItemInput {
  product_id: number
  warehouse_id: number
  quantity: number
}

export interface OrderInput {
  items: OrderItemInput[]
}

export interface OrderItem extends OrderItemInput {
  id: number
  unit_price: number
  product: { id: number; sku: string; name: string; is_active: boolean }
  warehouse: { id: number; code: string; name: string }
}

export interface Order {
  id: number
  order_number: string
  status: OrderStatus
  created_by: number
  created_at: string
  updated_at: string
  total: number
  creator: { id: number; first_name: string; last_name: string }
  items: OrderItem[]
}

export type OrderSortField = 'order_number' | 'status' | 'created_at' | 'updated_at'

export interface OrderQuery {
  page: number
  page_size: number
  search?: string
  order_status?: OrderStatus
  created_by?: number
  sort_by?: OrderSortField
  sort_order?: 'asc' | 'desc'
}

export interface OrderListResponse {
  items: Order[]
  total: number
  page: number
  page_size: number
}

export type OrderAction = 'confirm' | 'cancel' | 'process' | 'ship' | 'complete'
