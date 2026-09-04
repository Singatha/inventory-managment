import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import App from './App'

vi.mock('./hooks/useHealth', () => ({
  useHealth: () => ({ data: { status: 'ok', service: 'stockflow-api', version: '0.1.0' } }),
}))

vi.mock('./api/products', () => ({
  getProducts: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1 }),
  getProductCategories: vi.fn().mockResolvedValue([]),
}))

vi.mock('./api/warehouses', () => ({
  getWarehouses: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 1 }),
}))

vi.mock('./api/inventory', () => ({
  getInventory: vi.fn().mockResolvedValue({
    items: [],
    total: 0,
    page: 1,
    page_size: 1,
    total_quantity_on_hand: 0,
    total_quantity_reserved: 0,
    total_available_quantity: 0,
    low_stock_count: 0,
  }),
  getProductInventory: vi.fn(),
  getStockMovements: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 5 }),
  receiveStock: vi.fn(),
  adjustStock: vi.fn(),
  transferStock: vi.fn(),
}))

vi.mock('./features/auth/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, email: 'admin@stockflow.dev', first_name: 'StockFlow', last_name: 'Admin', role: 'ADMIN', is_active: true },
    isLoading: false,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

test('renders the dashboard shell and milestone status', async () => {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )

  await act(async () => Promise.resolve())

  expect(screen.getByLabelText('StockFlow home')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Good morning' })).toBeInTheDocument()
  expect(screen.getByText('Milestone 5 stock movement flow is ready')).toBeInTheDocument()
  expect(screen.getByText('API operational')).toBeInTheDocument()
})
