import { App as AntApp } from 'antd'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { vi } from 'vitest'
import { TransferStockModal } from './TransferStockModal'

const apiMocks = vi.hoisted(() => ({ transferStock: vi.fn() }))
vi.mock('../../api/inventory', () => ({ transferStock: apiMocks.transferStock }))

const product = {
  id: 1,
  sku: 'RTR-001',
  name: 'Wi-Fi Router',
  description: null,
  category: 'Networking',
  price: 2499,
  reorder_level: 2,
  is_active: true,
  created_at: '2026-09-04T12:00:00Z',
  updated_at: '2026-09-04T12:00:00Z',
}
const warehouses = [
  { id: 2, code: 'JHB-01', name: 'Johannesburg DC', location: 'Midrand', created_at: '2026-09-04T12:00:00Z', updated_at: '2026-09-04T12:00:00Z' },
  { id: 3, code: 'CPT-01', name: 'Cape Town DC', location: 'Montague Gardens', created_at: '2026-09-04T12:00:00Z', updated_at: '2026-09-04T12:00:00Z' },
]

beforeEach(() => {
  vi.resetAllMocks()
  apiMocks.transferStock.mockResolvedValue({})
})

test('submits a transfer between different warehouses', async () => {
  const queryClient = new QueryClient()
  render(
    <AntApp>
      <QueryClientProvider client={queryClient}>
        <TransferStockModal
          open
          products={[product]}
          warehouses={warehouses}
          optionsLoading={false}
          onClose={vi.fn()}
        />
      </QueryClientProvider>
    </AntApp>,
  )
  const dialog = within(screen.getByRole('dialog'))

  fireEvent.mouseDown(dialog.getByLabelText('Product'))
  fireEvent.click(await screen.findByText('RTR-001 — Wi-Fi Router'))
  fireEvent.mouseDown(dialog.getByLabelText('Source warehouse'))
  fireEvent.click(await screen.findByText('JHB-01 — Johannesburg DC'))
  fireEvent.mouseDown(dialog.getByLabelText('Destination warehouse'))
  const destinationOptions = await screen.findAllByText('CPT-01 — Cape Town DC')
  fireEvent.click(destinationOptions[destinationOptions.length - 1])
  fireEvent.change(dialog.getByLabelText('Quantity'), { target: { value: '3' } })
  fireEvent.change(dialog.getByLabelText('Transfer notes'), { target: { value: 'Rebalance' } })
  fireEvent.click(dialog.getByRole('button', { name: 'Transfer stock' }))

  await waitFor(() => expect(apiMocks.transferStock).toHaveBeenCalled())
  expect(apiMocks.transferStock.mock.calls[0][0]).toEqual({
    product_id: 1,
    source_warehouse_id: 2,
    destination_warehouse_id: 3,
    quantity: 3,
    notes: 'Rebalance',
  })
}, 20_000)
