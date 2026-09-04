import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { LoginPage } from './LoginPage'

const login = vi.fn().mockResolvedValue({ role: 'EMPLOYEE' })

vi.mock('./AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: false, isLoading: false, login, logout: vi.fn(), user: null }),
}))

test('submits valid credentials', async () => {
  render(<MemoryRouter><LoginPage /></MemoryRouter>)

  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'employee@example.com' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'CorrectHorse123!' } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))

  await waitFor(() => expect(login).toHaveBeenCalledWith({
    email: 'employee@example.com',
    password: 'CorrectHorse123!',
  }))
})

