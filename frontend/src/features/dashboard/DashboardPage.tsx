import {
  ArrowRightOutlined,
  CheckCircleFilled,
  DatabaseOutlined,
  InboxOutlined,
  ShoppingCartOutlined,
  ShopOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Row, Space, Statistic, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getProducts } from '../../api/products'
import { getInventory } from '../../api/inventory'
import { getWarehouses } from '../../api/warehouses'
import { getOrders } from '../../api/orders'
import { useHealth } from '../../hooks/useHealth'

const milestones = [
  { title: 'Foundation', description: 'API, database, Docker, and application shell', status: 'Complete' },
  { title: 'Identity & access', description: 'Authentication, users, and role-based access', status: 'Complete' },
  { title: 'Product catalog', description: 'Product management and searchable catalog', status: 'Complete' },
  { title: 'Inventory operations', description: 'Warehouses, receipts, and stock adjustments', status: 'Complete' },
  { title: 'Stock movement flow', description: 'Transfers and movement audit history', status: 'Complete' },
  { title: 'Order lifecycle', description: 'Reservations, cancellation, and shipment', status: 'Complete' },
  { title: 'Procurement', description: 'Suppliers and purchase order receiving', status: 'Next' },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const health = useHealth()
  const apiOnline = health.data?.status === 'ok'
  const productSummary = useQuery({
    queryKey: ['products', 'dashboard-summary'],
    queryFn: () => getProducts({ page: 1, page_size: 1 }),
  })
  const warehouseSummary = useQuery({
    queryKey: ['warehouses', 'dashboard-summary'],
    queryFn: () => getWarehouses({ page: 1, page_size: 1 }),
  })
  const inventorySummary = useQuery({
    queryKey: ['inventory', 'dashboard-summary'],
    queryFn: () => getInventory({ page: 1, page_size: 1 }),
  })
  const orderSummary = useQuery({
    queryKey: ['orders', 'dashboard-summary'],
    queryFn: () => getOrders({ page: 1, page_size: 1, order_status: 'PENDING' }),
  })

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Good morning</Typography.Title>
          <Typography.Text type="secondary">Here’s the current state of your operations workspace.</Typography.Text>
        </div>
        <Tag color={apiOnline ? 'success' : health.isError ? 'error' : 'processing'}>
          {apiOnline ? 'API operational' : health.isError ? 'API unavailable' : 'Checking API'}
        </Tag>
      </div>

      <Alert
        className="foundation-alert"
        type="info"
        showIcon
        message="Milestone 6 order lifecycle is ready"
        description="Orders now reserve inventory, release it on cancellation, and consume it atomically at shipment. Supplier procurement is next."
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <Card loading={productSummary.isLoading}><Statistic title="Products" value={productSummary.data?.total ?? 0} prefix={<InboxOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card loading={warehouseSummary.isLoading}><Statistic title="Warehouses" value={warehouseSummary.data?.total ?? 0} prefix={<ShopOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card loading={inventorySummary.isLoading}><Statistic title="Inventory units" value={inventorySummary.data?.total_available_quantity ?? 0} prefix={<DatabaseOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card loading={orderSummary.isLoading}><Statistic title="Pending orders" value={orderSummary.data?.total ?? 0} prefix={<ShoppingCartOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} lg={15}>
          <Card title="Delivery roadmap" className="roadmap-card">
            <Space direction="vertical" size={0} className="roadmap-list">
              {milestones.map((milestone, index) => (
                <div className="roadmap-item" key={milestone.title}>
                  <span className={`roadmap-index ${index < 6 ? 'is-complete' : ''}`}>
                    {index < 6 ? <CheckCircleFilled /> : index + 1}
                  </span>
                  <div className="roadmap-copy">
                    <Typography.Text strong>{milestone.title}</Typography.Text>
                    <Typography.Text type="secondary">{milestone.description}</Typography.Text>
                  </div>
                  <Tag color={index < 6 ? 'success' : index === 6 ? 'blue' : 'default'}>
                    {milestone.status}
                  </Tag>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={9}>
          <Card title="System status" className="status-card">
            <div className="status-line">
              <span><span className={`status-dot ${apiOnline ? 'online' : ''}`} />REST API</span>
              <Typography.Text type={apiOnline ? 'success' : 'secondary'}>
                {apiOnline ? `v${health.data?.version}` : 'Connecting'}
              </Typography.Text>
            </div>
            <div className="status-line">
              <span><span className="status-dot online" />Web application</span>
              <Typography.Text type="success">Online</Typography.Text>
            </div>
            <div className="status-line">
              <span><span className="status-dot online" />PostgreSQL</span>
              <Typography.Text type="success">Configured</Typography.Text>
            </div>
            <Button type="link" onClick={() => navigate('/suppliers')}>
              Continue to procurement <ArrowRightOutlined />
            </Button>
          </Card>
        </Col>
      </Row>
    </section>
  )
}
