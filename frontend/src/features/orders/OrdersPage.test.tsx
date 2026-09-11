import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'
import { OrdersPage } from './OrdersPage'

const apiMocks = vi.hoisted(() => ({
  getOrders: vi.fn(), getOrder: vi.fn(), createOrder: vi.fn(), transitionOrder: vi.fn(),
  getProducts: vi.fn(), getWarehouses: vi.fn(),
}))

vi.mock('../../api/orders', () => ({
  getOrders: apiMocks.getOrders,
  getOrder: apiMocks.getOrder,
  createOrder: apiMocks.createOrder,
  transitionOrder: apiMocks.transitionOrder,
}))
vi.mock('../../api/products', () => ({ getProducts: apiMocks.getProducts }))
vi.mock('../../api/warehouses', () => ({ getWarehouses: apiMocks.getWarehouses }))
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, role: 'ADMIN' }, isAuthenticated: true, isLoading: false,
    login: vi.fn(), logout: vi.fn(),
  }),
}))

const order = {
  id: 8,
  order_number: 'SO-20260911-ABC12345',
  status: 'PENDING' as const,
  created_by: 2,
  created_at: '2026-09-11T08:00:00Z',
  updated_at: '2026-09-11T08:00:00Z',
  total: 153,
  creator: { id: 2, first_name: 'Nandi', last_name: 'Buyer' },
  items: [{
    id: 10,
    product_id: 3,
    warehouse_id: 4,
    quantity: 6,
    unit_price: 25.5,
    product: { id: 3, sku: 'ITEM-001', name: 'Order item', is_active: true },
    warehouse: { id: 4, code: 'JHB-01', name: 'Johannesburg' },
  }],
}
const response = { items: [order], total: 1, page: 1, page_size: 20 }

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  queryClient.setQueryData(
    ['orders', { page: 1, page_size: 20, sort_by: 'created_at', sort_order: 'desc' }],
    response,
  )
  return render(
    <AntApp>
      <QueryClientProvider client={queryClient}><OrdersPage /></QueryClientProvider>
    </AntApp>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getOrders.mockResolvedValue(response)
  apiMocks.getOrder.mockResolvedValue(order)
  apiMocks.getProducts.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100 })
  apiMocks.getWarehouses.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 100 })
  apiMocks.transitionOrder.mockResolvedValue({ ...order, status: 'CONFIRMED' })
})

test('renders orders and confirms a pending order from its details', async () => {
  renderPage()

  expect(screen.getByRole('button', { name: order.order_number })).toBeInTheDocument()
  expect(screen.getByText('Nandi Buyer')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: order.order_number }))

  const drawer = within(await screen.findByRole('dialog'))
  expect(await drawer.findByText('ITEM-001')).toBeInTheDocument()
  fireEvent.click(drawer.getByRole('button', { name: 'Confirm & reserve' }))

  await waitFor(() => expect(apiMocks.transitionOrder).toHaveBeenCalledWith(order.id, 'confirm'))
}, 20_000)
