import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { ComingSoonPage } from './components/ComingSoonPage'

const pages: Record<string, { title: string; milestone: number }> = {
  products: { title: 'Products', milestone: 3 },
  inventory: { title: 'Inventory', milestone: 4 },
  warehouses: { title: 'Warehouses', milestone: 4 },
  movements: { title: 'Stock movements', milestone: 5 },
  orders: { title: 'Orders', milestone: 6 },
  suppliers: { title: 'Suppliers', milestone: 7 },
  'purchase-orders': { title: 'Purchase orders', milestone: 7 },
  users: { title: 'Users', milestone: 2 },
  settings: { title: 'Settings', milestone: 12 },
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        {Object.entries(pages).map(([path, page]) => (
          <Route
            key={path}
            path={path}
            element={<ComingSoonPage title={page.title} milestone={page.milestone} />}
          />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

