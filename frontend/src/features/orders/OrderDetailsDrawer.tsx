import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Descriptions, Drawer, Popconfirm, Space, Table, Tag, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import { getOrder, transitionOrder } from '../../api/orders'
import { getApiErrorMessage } from '../../api/client'
import type { OrderAction, OrderItem, OrderStatus } from '../../types/order'
import { useAuth } from '../auth/AuthContext'

interface OrderDetailsDrawerProps {
  orderId: number | null
  onClose: () => void
}

const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })
const statusColors: Record<OrderStatus, string> = {
  PENDING: 'gold',
  CONFIRMED: 'blue',
  PROCESSING: 'cyan',
  SHIPPED: 'purple',
  COMPLETED: 'green',
  CANCELLED: 'default',
}
const nextActions: Partial<Record<OrderStatus, OrderAction>> = {
  PENDING: 'confirm',
  CONFIRMED: 'process',
  PROCESSING: 'ship',
  SHIPPED: 'complete',
}

export function OrderDetailsDrawer({ orderId, onClose }: OrderDetailsDrawerProps) {
  const { user } = useAuth()
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const orderQuery = useQuery({
    queryKey: ['orders', 'detail', orderId],
    queryFn: () => getOrder(orderId ?? 0),
    enabled: orderId !== null,
  })
  const mutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: OrderAction }) => transitionOrder(id, action),
    onSuccess: async (order) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['orders'] }),
        queryClient.invalidateQueries({ queryKey: ['inventory'] }),
        queryClient.invalidateQueries({ queryKey: ['stock-movements'] }),
      ])
      message.success(`Order ${order.order_number} is now ${order.status.toLowerCase()}`)
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })
  const order = orderQuery.data
  const canManage = user?.role === 'ADMIN' || user?.role === 'WAREHOUSE_MANAGER'
  const nextAction = order ? nextActions[order.status] : undefined
  const canEmployeeCancel = Boolean(
    order && user?.role === 'EMPLOYEE' && order.created_by === user.id && order.status === 'PENDING',
  )
  const canManagerCancel = Boolean(
    order && canManage && ['PENDING', 'CONFIRMED', 'PROCESSING'].includes(order.status),
  )
  const canCancel = canEmployeeCancel || canManagerCancel
  const columns: TableColumnsType<OrderItem> = [
    { title: 'Product', render: (_, item) => <div className="inventory-identity"><Typography.Text strong>{item.product.name}</Typography.Text><Typography.Text type="secondary" code>{item.product.sku}</Typography.Text></div> },
    { title: 'Warehouse', render: (_, item) => `${item.warehouse.code} — ${item.warehouse.name}` },
    { title: 'Qty', dataIndex: 'quantity', align: 'right', width: 65 },
    { title: 'Price', dataIndex: 'unit_price', align: 'right', width: 110, render: (value: number) => currency.format(value) },
    { title: 'Line total', align: 'right', width: 120, render: (_, item) => currency.format(item.quantity * item.unit_price) },
  ]

  function run(action: OrderAction) {
    if (order) mutation.mutate({ id: order.id, action })
  }

  return (
    <Drawer
      title="Order details"
      width={760}
      open={orderId !== null}
      onClose={onClose}
      loading={orderQuery.isLoading}
      destroyOnHidden
      extra={order && (
        <Space>
          {canCancel && (
            <Popconfirm title="Cancel this order?" description="Any reserved stock will be released." onConfirm={() => run('cancel')}>
              <Button danger loading={mutation.isPending}>Cancel order</Button>
            </Popconfirm>
          )}
          {canManage && nextAction && (
            <Button type="primary" loading={mutation.isPending} onClick={() => run(nextAction)}>
              {nextAction === 'confirm' ? 'Confirm & reserve' : `${nextAction[0].toUpperCase()}${nextAction.slice(1)} order`}
            </Button>
          )}
        </Space>
      )}
    >
      {order && (
        <Space direction="vertical" size="large" className="full-width">
          <div className="order-title">
            <div>
              <Typography.Title level={3}>{order.order_number}</Typography.Title>
              <Typography.Text type="secondary">Created {new Date(order.created_at).toLocaleString()}</Typography.Text>
            </div>
            <Tag color={statusColors[order.status]}>{order.status}</Tag>
          </div>
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="Created by">{order.creator.first_name} {order.creator.last_name}</Descriptions.Item>
            <Descriptions.Item label="Order total">{currency.format(order.total)}</Descriptions.Item>
            <Descriptions.Item label="Last updated" span={2}>{new Date(order.updated_at).toLocaleString()}</Descriptions.Item>
          </Descriptions>
          <Table<OrderItem>
            rowKey="id"
            size="small"
            columns={columns}
            dataSource={order.items}
            pagination={false}
            scroll={{ x: 650 }}
          />
        </Space>
      )}
    </Drawer>
  )
}
