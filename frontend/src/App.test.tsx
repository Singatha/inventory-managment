import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import App from './App'

vi.mock('./hooks/useHealth', () => ({
  useHealth: () => ({ data: { status: 'ok', service: 'stockflow-api', version: '0.1.0' } }),
}))

test('renders the dashboard shell and milestone status', () => {
  const queryClient = new QueryClient()
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )

  expect(screen.getByText('StockFlow')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Good morning' })).toBeInTheDocument()
  expect(screen.getByText('Milestone 1 foundation is ready')).toBeInTheDocument()
  expect(screen.getByText('API operational')).toBeInTheDocument()
})

