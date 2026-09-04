import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { vi } from 'vitest'
import { MovementsPage } from './MovementsPage'

const apiMocks = vi.hoisted(() => ({
  getStockMovements: vi.fn(),
  getWarehouses: vi.fn(),
}))

vi.mock('../../api/inventory', () => ({ getStockMovements: apiMocks.getStockMovements }))
vi.mock('../../api/warehouses', () => ({ getWarehouses: apiMocks.getWarehouses }))

const warehouse = {
  id: 2,
  name: 'Johannesburg Distribution Centre',
  code: 'JHB-01',
  location: 'Midrand, Gauteng',
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}
const movement = {
  id: 9,
  product_id: 1,
  warehouse_id: warehouse.id,
  type: 'TRANSFER_OUT' as const,
  quantity: -4,
  reference_type: 'TRANSFER',
  reference_id: 9,
  notes: 'Regional replenishment',
  created_by: 3,
  created_at: '2026-09-04T12:00:00Z',
  product: {
    id: 1,
    sku: 'RTR-001',
    name: 'Wi-Fi Router',
    reorder_level: 2,
    is_active: true,
  },
  warehouse,
  creator: { id: 3, first_name: 'Thandi', last_name: 'Manager' },
}
const movementResponse = { items: [movement], total: 1, page: 1, page_size: 20 }

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  queryClient.setQueryData(
    ['stock-movements', { page: 1, page_size: 20, sort_order: 'desc' }],
    movementResponse,
  )
  queryClient.setQueryData(
    ['warehouses', 'movement-options'],
    { items: [warehouse], total: 1, page: 1, page_size: 100 },
  )
  return render(
    <AntApp>
      <QueryClientProvider client={queryClient}>
        <MovementsPage />
      </QueryClientProvider>
    </AntApp>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getStockMovements.mockResolvedValue(movementResponse)
  apiMocks.getWarehouses.mockResolvedValue({
    items: [warehouse], total: 1, page: 1, page_size: 100,
  })
})

test('renders movement history and opens audit details', () => {
  renderPage()

  expect(screen.getByText('Transfer out')).toBeInTheDocument()
  expect(screen.getByText('-4')).toBeInTheDocument()
  expect(screen.getByText('Thandi Manager')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Wi-Fi Router' }))

  const drawer = within(screen.getByRole('dialog'))
  expect(drawer.getByText('Regional replenishment')).toBeInTheDocument()
  expect(drawer.getByText('TRANSFER #9')).toBeInTheDocument()
  expect(drawer.getByText('RTR-001')).toBeInTheDocument()
}, 20_000)
