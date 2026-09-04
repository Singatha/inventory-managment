import { useQuery } from '@tanstack/react-query'
import { Card, Descriptions, Drawer, Empty, List, Space, Tag, Typography } from 'antd'
import { getProductInventory, getStockMovements } from '../../api/inventory'
import type { Product } from '../../types/product'

interface ProductDetailsDrawerProps {
  product: Product | null
  onClose: () => void
}

const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })

export function ProductDetailsDrawer({ product, onClose }: ProductDetailsDrawerProps) {
  const inventoryQuery = useQuery({
    queryKey: ['inventory', 'product', product?.id],
    queryFn: () => getProductInventory(product?.id ?? 0),
    enabled: Boolean(product),
  })
  const movementsQuery = useQuery({
    queryKey: ['stock-movements', 'product', product?.id],
    queryFn: () => getStockMovements({
      page: 1,
      page_size: 5,
      product_id: product?.id,
      sort_order: 'desc',
    }),
    enabled: Boolean(product),
  })

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
          <Card size="small" title="Inventory by warehouse" loading={inventoryQuery.isLoading}>
            {inventoryQuery.data?.items.length ? (
              <List
                dataSource={inventoryQuery.data.items}
                renderItem={(item) => (
                  <List.Item extra={<Tag color={item.is_low_stock ? 'warning' : 'success'}>{item.available_quantity} available</Tag>}>
                    <List.Item.Meta title={`${item.warehouse.code} — ${item.warehouse.name}`} description={`${item.quantity_on_hand} on hand · ${item.quantity_reserved} reserved`} />
                  </List.Item>
                )}
              />
            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No stock has been recorded for this product." />}
          </Card>
          <Card size="small" title="Recent stock movements" loading={movementsQuery.isLoading}>
            {movementsQuery.data?.items.length ? (
              <List
                dataSource={movementsQuery.data.items}
                renderItem={(movement) => (
                  <List.Item extra={<Typography.Text type={movement.quantity < 0 ? 'danger' : 'success'} strong>{movement.quantity > 0 ? '+' : ''}{movement.quantity}</Typography.Text>}>
                    <List.Item.Meta title={movement.type.replaceAll('_', ' ')} description={`${movement.warehouse.code} · ${new Date(movement.created_at).toLocaleString()}`} />
                  </List.Item>
                )}
              />
            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No stock movements have been recorded." />}
          </Card>
        </Space>
      )}
    </Drawer>
  )
}
