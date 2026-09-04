import { DatabaseOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { getApiErrorMessage } from '../../api/client'
import type { LoginCredentials } from '../../types/auth'
import { useAuth } from './AuthContext'

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (auth.isAuthenticated) return <Navigate to="/" replace />

  async function handleSubmit(values: LoginCredentials) {
    setError(null)
    setSubmitting(true)
    try {
      await auth.login(values)
      const destination = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/'
      navigate(destination, { replace: true })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-intro">
        <div className="login-brand"><span className="brand-mark"><DatabaseOutlined /></span> StockFlow</div>
        <div>
          <Typography.Title>Know what’s in stock.<br />Move it with confidence.</Typography.Title>
          <Typography.Paragraph>
            One operational workspace for products, warehouses, orders, and procurement.
          </Typography.Paragraph>
        </div>
        <Typography.Text>Inventory operations, without the guesswork.</Typography.Text>
      </section>
      <section className="login-panel">
        <Card className="login-card">
          <Typography.Title level={2}>Welcome back</Typography.Title>
          <Typography.Paragraph type="secondary">Sign in to your operations workspace.</Typography.Paragraph>
          {error && <Alert type="error" showIcon message={error} closable onClose={() => setError(null)} />}
          <Form<LoginCredentials> layout="vertical" size="large" onFinish={handleSubmit} requiredMark={false}>
            <Form.Item label="Email address" name="email" rules={[{ required: true }, { type: 'email' }]}>
              <Input prefix={<MailOutlined />} autoComplete="email" placeholder="you@company.com" />
            </Form.Item>
            <Form.Item label="Password" name="password" rules={[{ required: true }]}>
              <Input.Password prefix={<LockOutlined />} autoComplete="current-password" placeholder="Enter your password" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={submitting} block>Sign in</Button>
          </Form>
          <Typography.Text className="login-help" type="secondary">
            Access is managed by your StockFlow administrator.
          </Typography.Text>
        </Card>
      </section>
    </main>
  )
}

