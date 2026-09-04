import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'
import { InventoryPage } from './InventoryPage'

const apiMocks = vi.hoisted(() => ({
  getInventory: vi.fn(),
  receiveStock: vi.fn(),
  adjustStock: vi.fn(),
  getProducts: vi.fn(),
  getWarehouses: vi.fn(),
}))

vi.mock('../../api/inventory', () => ({
  getInventory: apiMocks.getInventory,
  receiveStock: apiMocks.receiveStock,
  adjustStock: apiMocks.adjustStock,
}))
vi.mock('../../api/products', () => ({ getProducts: apiMocks.getProducts }))
vi.mock('../../api/warehouses', () => ({ getWarehouses: apiMocks.getWarehouses }))
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'WAREHOUSE_MANAGER' }, isAuthenticated: true, isLoading: false }),
}))

const product = {
  id: 1,
  sku: 'SCN-001',
  name: 'Barcode Scanner',
  description: null,
  category: 'Equipment',
  price: 1499,
  reorder_level: 5,
  is_active: true,
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}
const warehouse = {
  id: 2,
  name: 'Johannesburg Distribution Centre',
  code: 'JHB-01',
  location: 'Midrand, Gauteng',
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}
const inventory = {
  id: 3,
  product_id: product.id,
  warehouse_id: warehouse.id,
  quantity_on_hand: 4,
  quantity_reserved: 0,
  available_quantity: 4,
  is_low_stock: true,
  updated_at: '2026-09-04T12:00:00Z',
  product,
  warehouse,
}
const inventoryResponse = {
  items: [inventory],
  total: 1,
  page: 1,
  page_size: 20,
  total_quantity_on_hand: 4,
  total_quantity_reserved: 0,
  total_available_quantity: 4,
  low_stock_count: 1,
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  queryClient.setQueryData(
    ['inventory', { page: 1, page_size: 20, sort_by: 'product', sort_order: 'asc' }],
    inventoryResponse,
  )
  queryClient.setQueryData(
    ['products', 'inventory-options'],
    { items: [product], total: 1, page: 1, page_size: 100 },
  )
  queryClient.setQueryData(
    ['warehouses', 'inventory-options'],
    { items: [warehouse], total: 1, page: 1, page_size: 100 },
  )
  return render(
    <AntApp>
      <QueryClientProvider client={queryClient}>
        <InventoryPage />
      </QueryClientProvider>
    </AntApp>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getInventory.mockResolvedValue(inventoryResponse)
  apiMocks.getProducts.mockResolvedValue({ items: [product], total: 1, page: 1, page_size: 100 })
  apiMocks.getWarehouses.mockResolvedValue({ items: [warehouse], total: 1, page: 1, page_size: 100 })
  apiMocks.adjustStock.mockResolvedValue({ inventory, movement: { id: 1 } })
})

test('shows low stock and submits a reasoned adjustment', async () => {
  renderPage()

  expect(screen.getByText('SCN-001')).toBeInTheDocument()
  expect(screen.getAllByText('Low stock').length).toBeGreaterThan(0)
  fireEvent.click(screen.getByRole('button', { name: 'Adjust' }))
  const dialog = within(screen.getByRole('dialog'))
  fireEvent.change(dialog.getByLabelText('Quantity change'), { target: { value: '-2' } })
  fireEvent.change(dialog.getByLabelText('Reason'), { target: { value: 'Damaged units' } })
  fireEvent.click(dialog.getByRole('button', { name: 'Apply adjustment' }))

  await waitFor(() => expect(apiMocks.adjustStock).toHaveBeenCalledWith({
    product_id: 1,
    warehouse_id: 2,
    quantity: -2,
    reason: 'Damaged units',
  }))
}, 20_000)
