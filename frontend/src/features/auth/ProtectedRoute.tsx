import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Flex, Spin } from 'antd'
import { useAuth } from './AuthContext'

export function ProtectedRoute() {
  const auth = useAuth()
  const location = useLocation()

  if (auth.isLoading) {
    return <Flex className="route-loader" align="center" justify="center"><Spin size="large" /></Flex>
  }
  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <Outlet />
}

