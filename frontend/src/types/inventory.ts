import type { SortOrder } from './product'

export interface InventoryProduct {
  id: number
  sku: string
  name: string
  reorder_level: number
  is_active: boolean
}

export interface InventoryWarehouse {
  id: number
  code: string
  name: string
  location: string
}

export interface InventoryItem {
  id: number
  product_id: number
  warehouse_id: number
  quantity_on_hand: number
  quantity_reserved: number
  available_quantity: number
  is_low_stock: boolean
  updated_at: string
  product: InventoryProduct
  warehouse: InventoryWarehouse
}

export type InventorySortField =
  | 'product'
  | 'warehouse'
  | 'quantity_on_hand'
  | 'quantity_reserved'
  | 'available_quantity'

export interface InventoryQuery {
  page: number
  page_size: number
  search?: string
  product_id?: number
  warehouse_id?: number
  low_stock?: boolean
  sort_by?: InventorySortField
  sort_order?: SortOrder
}

export interface InventoryListResponse {
  items: InventoryItem[]
  total: number
  page: number
  page_size: number
  total_quantity_on_hand: number
  total_quantity_reserved: number
  total_available_quantity: number
  low_stock_count: number
}

export type StockMovementType =
  | 'RECEIVE'
  | 'ADJUSTMENT'
  | 'RESERVE'
  | 'RELEASE'
  | 'SHIPMENT'
  | 'TRANSFER_IN'
  | 'TRANSFER_OUT'
  | 'RETURN'

export interface StockMovement {
  id: number
  product_id: number
  warehouse_id: number
  type: StockMovementType
  quantity: number
  reference_type: string | null
  reference_id: number | null
  notes: string | null
  created_by: number
  created_at: string
}

export interface InventoryOperationResponse {
  inventory: InventoryItem
  movement: StockMovement
}

export interface StockReceiveInput {
  product_id: number
  warehouse_id: number
  quantity: number
  notes?: string | null
}

export interface StockAdjustmentInput {
  product_id: number
  warehouse_id: number
  quantity: number
  reason: string
}

export interface StockTransferInput {
  product_id: number
  source_warehouse_id: number
  destination_warehouse_id: number
  quantity: number
  notes?: string | null
}

export interface StockTransferResponse {
  source_inventory: InventoryItem
  destination_inventory: InventoryItem
  movements: StockMovement[]
}

export interface MovementUser {
  id: number
  first_name: string
  last_name: string
}

export interface StockMovementDetail extends StockMovement {
  product: InventoryProduct
  warehouse: InventoryWarehouse
  creator: MovementUser
}

export interface StockMovementQuery {
  page: number
  page_size: number
  search?: string
  product_id?: number
  warehouse_id?: number
  movement_type?: StockMovementType
  created_from?: string
  created_to?: string
  sort_order?: SortOrder
}

export interface StockMovementListResponse {
  items: StockMovementDetail[]
  total: number
  page: number
  page_size: number
}
