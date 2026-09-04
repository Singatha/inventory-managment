import { useState } from 'react'
import {
  AppstoreOutlined,
  BellOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  ShopOutlined,
  ShoppingCartOutlined,
  SwapOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Avatar, Badge, Breadcrumb, Button, Dropdown, Grid, Layout, Menu, Space, Typography } from 'antd'
import type { MenuProps } from 'antd'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../features/auth/AuthContext'

const { Header, Sider, Content } = Layout
const { useBreakpoint } = Grid

const menuItems: MenuProps['items'] = [
  { key: '/', icon: <AppstoreOutlined />, label: 'Dashboard' },
  {
    type: 'group',
    label: 'INVENTORY',
    children: [
      { key: '/products', icon: <ShopOutlined />, label: 'Products' },
      { key: '/inventory', icon: <DatabaseOutlined />, label: 'Inventory' },
      { key: '/warehouses', icon: <AppstoreOutlined />, label: 'Warehouses' },
      { key: '/movements', icon: <SwapOutlined />, label: 'Stock movements' },
    ],
  },
  {
    type: 'group',
    label: 'SALES',
    children: [{ key: '/orders', icon: <ShoppingCartOutlined />, label: 'Orders' }],
  },
  {
    type: 'group',
    label: 'PROCUREMENT',
    children: [
      { key: '/suppliers', icon: <TeamOutlined />, label: 'Suppliers' },
      { key: '/purchase-orders', icon: <ShoppingCartOutlined />, label: 'Purchase orders' },
    ],
  },
  {
    type: 'group',
    label: 'ADMINISTRATION',
    children: [
      { key: '/users', icon: <UserOutlined />, label: 'Users' },
      { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ],
  },
]

function titleForPath(pathname: string) {
  if (pathname === '/') return 'Dashboard'
  return pathname
    .slice(1)
    .split('-')
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(' ')
}

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const screens = useBreakpoint()
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = !screens.md
  const effectiveCollapsed = isMobile || collapsed
  const pageTitle = titleForPath(location.pathname)
  const { user, logout } = useAuth()
  const initials = `${user?.first_name[0] ?? ''}${user?.last_name[0] ?? ''}`

  function signOut() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Layout className="app-shell">
      <Sider
        className="app-sider"
        width={248}
        collapsedWidth={isMobile ? 0 : 76}
        collapsed={effectiveCollapsed}
        trigger={null}
        breakpoint="md"
      >
        <Link className="brand" to="/" aria-label="StockFlow home">
          <span className="brand-mark"><DatabaseOutlined /></span>
          {!effectiveCollapsed && <span>StockFlow</span>}
        </Link>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <Space size="middle">
            <Button
              type="text"
              aria-label={effectiveCollapsed ? 'Open navigation' : 'Close navigation'}
              icon={effectiveCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed((value) => !value)}
            />
            <Typography.Text className="header-context">Operations workspace</Typography.Text>
          </Space>
          <Space size="large">
            <Badge dot offset={[-2, 2]}>
              <Button type="text" aria-label="Notifications" icon={<BellOutlined />} />
            </Badge>
            <Dropdown
              trigger={['click']}
              menu={{
                items: [
                  { key: 'identity', label: <><Typography.Text strong>{user?.first_name} {user?.last_name}</Typography.Text><br /><Typography.Text type="secondary">{user?.email}</Typography.Text></>, disabled: true },
                  { type: 'divider' },
                  { key: 'logout', label: 'Sign out', danger: true, onClick: signOut },
                ],
              }}
            >
              <Button type="text" className="user-menu">
                <Avatar className="user-avatar">{initials}</Avatar>
                <span className="user-menu-name">{user?.first_name}</span>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content className="app-content">
          <Breadcrumb items={[{ title: 'StockFlow' }, { title: pageTitle }]} />
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
