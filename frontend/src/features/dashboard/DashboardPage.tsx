import {
  AlertOutlined,
  ArrowRightOutlined,
  CheckCircleFilled,
  DatabaseOutlined,
  InboxOutlined,
  ShopOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Row, Space, Statistic, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useHealth } from '../../hooks/useHealth'

const milestones = [
  { title: 'Foundation', description: 'API, database, Docker, and application shell', status: 'Complete' },
  { title: 'Identity & access', description: 'Authentication, users, and role-based access', status: 'Next' },
  { title: 'Product catalog', description: 'Product management and searchable catalog', status: 'Planned' },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const health = useHealth()
  const apiOnline = health.data?.status === 'ok'

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
        message="Milestone 1 foundation is ready"
        description="The domain modules are intentionally staged. Authentication and user access are next."
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <Card><Statistic title="Products" value={0} prefix={<InboxOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card><Statistic title="Warehouses" value={0} prefix={<ShopOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card><Statistic title="Inventory units" value={0} prefix={<DatabaseOutlined />} /></Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card><Statistic title="Low-stock alerts" value={0} prefix={<AlertOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="dashboard-row">
        <Col xs={24} lg={15}>
          <Card title="Delivery roadmap" className="roadmap-card">
            <Space direction="vertical" size={0} className="roadmap-list">
              {milestones.map((milestone, index) => (
                <div className="roadmap-item" key={milestone.title}>
                  <span className={`roadmap-index ${index === 0 ? 'is-complete' : ''}`}>
                    {index === 0 ? <CheckCircleFilled /> : index + 1}
                  </span>
                  <div className="roadmap-copy">
                    <Typography.Text strong>{milestone.title}</Typography.Text>
                    <Typography.Text type="secondary">{milestone.description}</Typography.Text>
                  </div>
                  <Tag color={index === 0 ? 'success' : index === 1 ? 'blue' : 'default'}>
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
            <Button type="link" onClick={() => navigate('/users')}>
              Continue to Milestone 2 <ArrowRightOutlined />
            </Button>
          </Card>
        </Col>
      </Row>
    </section>
  )
}
