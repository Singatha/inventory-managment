import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'
import { ProductsPage } from './ProductsPage'

const apiMocks = vi.hoisted(() => ({
  getProducts: vi.fn(),
  getProductCategories: vi.fn(),
  createProduct: vi.fn(),
  updateProduct: vi.fn(),
  deactivateProduct: vi.fn(),
}))

vi.mock('../../api/products', () => apiMocks)
vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({
    user: { role: 'ADMIN' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

const product = {
  id: 1,
  sku: 'LAP-001',
  name: 'Latitude 7450',
  description: 'Business laptop',
  category: 'Laptops',
  price: 24999.95,
  reorder_level: 5,
  is_active: true,
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  queryClient.setQueryData(
    ['products', { page: 1, page_size: 20, is_active: true, sort_by: 'name', sort_order: 'asc' }],
    { items: [product], total: 1, page: 1, page_size: 20 },
  )
  queryClient.setQueryData(['product-categories'], ['Laptops'])
  return render(
    <AntApp>
      <QueryClientProvider client={queryClient}>
        <ProductsPage />
      </QueryClientProvider>
    </AntApp>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.getProducts.mockResolvedValue({ items: [product], total: 1, page: 1, page_size: 20 })
  apiMocks.getProductCategories.mockResolvedValue(['Laptops'])
  apiMocks.createProduct.mockResolvedValue(product)
})

test('renders products returned by the API', async () => {
  renderPage()

  expect(screen.getByRole('button', { name: 'Latitude 7450' })).toBeInTheDocument()
  expect(screen.getByText('LAP-001')).toBeInTheDocument()
  expect(screen.getByText('Laptops')).toBeInTheDocument()
}, 20_000)

test('submits the add-product form', async () => {
  renderPage()
  expect(screen.getByText('Latitude 7450')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: /Add product/ }))
  const dialog = within(screen.getByRole('dialog'))
  fireEvent.change(dialog.getByLabelText('SKU'), { target: { value: 'new-001' } })
  fireEvent.change(dialog.getByLabelText('Category'), { target: { value: 'Accessories' } })
  fireEvent.change(dialog.getByLabelText('Product name'), { target: { value: 'USB-C Dock' } })
  fireEvent.change(dialog.getByLabelText('Unit price'), { target: { value: '1899.95' } })
  fireEvent.change(dialog.getByLabelText('Reorder level'), { target: { value: '4' } })
  fireEvent.click(dialog.getByRole('button', { name: 'Create product' }))

  await waitFor(() => expect(apiMocks.createProduct).toHaveBeenCalledWith({
    sku: 'new-001',
    category: 'Accessories',
    name: 'USB-C Dock',
    description: null,
    price: 1899.95,
    reorder_level: 4,
    is_active: true,
  }))
}, 15_000)
