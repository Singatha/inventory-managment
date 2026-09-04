import { Card, Descriptions, Drawer, Empty, Space, Tag, Typography } from 'antd'
import type { Product } from '../../types/product'

interface ProductDetailsDrawerProps {
  product: Product | null
  onClose: () => void
}

const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })

export function ProductDetailsDrawer({ product, onClose }: ProductDetailsDrawerProps) {
  return (
    <Drawer
      title="Product details"
      width={560}
      open={Boolean(product)}
      onClose={onClose}
      destroyOnHidden
    >
      {product && (
        <Space direction="vertical" size="large" className="full-width">
          <div>
            <Space><Typography.Title level={3}>{product.name}</Typography.Title><Tag color={product.is_active ? 'success' : 'default'}>{product.is_active ? 'Active' : 'Inactive'}</Tag></Space>
            <Typography.Text type="secondary">{product.sku}</Typography.Text>
          </div>
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Category">{product.category}</Descriptions.Item>
            <Descriptions.Item label="Unit price">{currency.format(product.price)}</Descriptions.Item>
            <Descriptions.Item label="Reorder level">{product.reorder_level}</Descriptions.Item>
            <Descriptions.Item label="Description">{product.description || '—'}</Descriptions.Item>
          </Descriptions>
          <Card size="small" title="Inventory by warehouse">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Inventory levels arrive in Milestone 4." />
          </Card>
          <Card size="small" title="Recent stock movements">
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Movement history arrives in Milestone 5." />
          </Card>
        </Space>
      )}
    </Drawer>
  )
}

