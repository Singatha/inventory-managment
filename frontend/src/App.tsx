import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { ComingSoonPage } from './components/ComingSoonPage'
import { LoginPage } from './features/auth/LoginPage'
import { ProtectedRoute } from './features/auth/ProtectedRoute'
import { RoleRoute } from './features/auth/RoleRoute'
import { UsersPage } from './features/users/UsersPage'
import { ProductsPage } from './features/products/ProductsPage'
import { InventoryPage } from './features/inventory/InventoryPage'
import { WarehousesPage } from './features/warehouses/WarehousesPage'

const pages: Record<string, { title: string; milestone: number }> = {
  movements: { title: 'Stock movements', milestone: 5 },
  orders: { title: 'Orders', milestone: 6 },
  suppliers: { title: 'Suppliers', milestone: 7 },
  'purchase-orders': { title: 'Purchase orders', milestone: 7 },
  settings: { title: 'Settings', milestone: 12 },
}

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="warehouses" element={<WarehousesPage />} />
          <Route path="users" element={<RoleRoute roles={['ADMIN']}><UsersPage /></RoleRoute>} />
          {Object.entries(pages).map(([path, page]) => (
            <Route
              key={path}
              path={path}
              element={<ComingSoonPage title={page.title} milestone={page.milestone} />}
            />
          ))}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Route>
    </Routes>
  )
}
