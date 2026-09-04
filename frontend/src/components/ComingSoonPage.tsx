import { ClockCircleOutlined } from '@ant-design/icons'
import { Card, Empty, Tag, Typography } from 'antd'

interface ComingSoonPageProps {
  title: string
  milestone: number
}

export function ComingSoonPage({ title, milestone }: ComingSoonPageProps) {
  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>{title}</Typography.Title>
          <Typography.Text type="secondary">This feature is part of the staged delivery plan.</Typography.Text>
        </div>
        <Tag icon={<ClockCircleOutlined />} color="blue">Milestone {milestone}</Tag>
      </div>
      <Card>
        <Empty description={`${title} will be implemented in Milestone ${milestone}.`} />
      </Card>
    </section>
  )
}

