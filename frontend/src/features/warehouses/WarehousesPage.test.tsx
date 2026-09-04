import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'
import { WarehousesPage } from './WarehousesPage'

const apiMocks = vi.hoisted(() => ({
  getWarehouses: vi.fn(),
  createWarehouse: vi.fn(),
  updateWarehouse: vi.fn(),
  deleteWarehouse: vi.fn(),
}))

vi.mock('../../api/warehouses', () => apiMocks)
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'ADMIN' }, isAuthenticated: true, isLoading: false }),
}))

const warehouse = {
  id: 1,
  name: 'Johannesburg Distribution Centre',
  code: 'JHB-01',
  location: 'Midrand, Gauteng',
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  queryClient.setQueryData(
    ['warehouses', { page: 1, page_size: 20, sort_by: 'name', sort_order: 'asc' }],
    { items: [warehouse], total: 1, page: 1, page_size: 20 },
  )
  return render(
    <AntApp>
      <QueryClientProvider client={queryClient}>
        <WarehousesPage />
      </QueryClientProvider>
    </AntApp>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getWarehouses.mockResolvedValue({
    items: [warehouse], total: 1, page: 1, page_size: 20,
  })
  apiMocks.createWarehouse.mockResolvedValue(warehouse)
})

test('renders a warehouse and submits the create form', async () => {
  renderPage()

  expect(screen.getByText('JHB-01')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /Add warehouse/ }))
  const dialog = within(screen.getByRole('dialog'))
  fireEvent.change(dialog.getByLabelText('Warehouse name'), { target: { value: 'Cape Town DC' } })
  fireEvent.change(dialog.getByLabelText('Warehouse code'), { target: { value: 'cpt-01' } })
  fireEvent.change(dialog.getByLabelText('Location'), { target: { value: 'Montague Gardens' } })
  fireEvent.click(dialog.getByRole('button', { name: 'Create warehouse' }))

  await waitFor(() => expect(apiMocks.createWarehouse).toHaveBeenCalledWith({
    name: 'Cape Town DC',
    code: 'cpt-01',
    location: 'Montague Gardens',
  }))
}, 20_000)
