import { EyeOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Button, Card, Input, Select, Table, Tag, Tooltip, Typography } from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import type { FilterValue, SorterResult } from 'antd/es/table/interface'
import { useState } from 'react'
import { getOrders } from '../../api/orders'
import { getProducts } from '../../api/products'
import { getWarehouses } from '../../api/warehouses'
import { getApiErrorMessage } from '../../api/client'
import type { Order, OrderQuery, OrderSortField, OrderStatus } from '../../types/order'
import { OrderCreateModal } from './OrderCreateModal'
import { OrderDetailsDrawer } from './OrderDetailsDrawer'

const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })
const statuses: OrderStatus[] = ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'COMPLETED', 'CANCELLED']
const statusColors: Record<OrderStatus, string> = {
  PENDING: 'gold', CONFIRMED: 'blue', PROCESSING: 'cyan', SHIPPED: 'purple', COMPLETED: 'green', CANCELLED: 'default',
}

export function OrdersPage() {
  const [query, setQuery] = useState<OrderQuery>({ page: 1, page_size: 20, sort_by: 'created_at', sort_order: 'desc' })
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null)
  const ordersQuery = useQuery({ queryKey: ['orders', query], queryFn: () => getOrders(query) })
  const productsQuery = useQuery({
    queryKey: ['products', 'order-options'],
    queryFn: () => getProducts({ page: 1, page_size: 100, is_active: true }),
  })
  const warehousesQuery = useQuery({
    queryKey: ['warehouses', 'order-options'],
    queryFn: () => getWarehouses({ page: 1, page_size: 100 }),
  })
  const columns: TableColumnsType<Order> = [
    { title: 'Order', dataIndex: 'order_number', sorter: true, render: (value: string, order) => <Button type="link" className="table-link" onClick={() => setSelectedOrderId(order.id)}>{value}</Button> },
    { title: 'Status', dataIndex: 'status', sorter: true, width: 130, render: (value: OrderStatus) => <Tag color={statusColors[value]}>{value}</Tag> },
    { title: 'Items', key: 'items', align: 'right', width: 85, render: (_, order) => order.items.reduce((total, item) => total + item.quantity, 0) },
    { title: 'Total', dataIndex: 'total', align: 'right', width: 140, render: (value: number) => currency.format(value) },
    { title: 'Created by', key: 'creator', width: 170, render: (_, order) => `${order.creator.first_name} ${order.creator.last_name}` },
    { title: 'Created', dataIndex: 'created_at', sorter: true, width: 180, render: (value: string) => new Date(value).toLocaleString() },
    { title: '', width: 50, align: 'right', render: (_, order) => <Tooltip title="View order"><Button type="text" aria-label={`View ${order.order_number}`} icon={<EyeOutlined />} onClick={() => setSelectedOrderId(order.id)} /></Tooltip> },
  ]

  function handleTableChange(
    pagination: TablePaginationConfig,
    _: Record<string, FilterValue | null>,
    sorter: SorterResult<Order> | SorterResult<Order>[],
  ) {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter
    const allowed: OrderSortField[] = ['order_number', 'status', 'created_at', 'updated_at']
    const field = typeof activeSorter?.field === 'string' && allowed.includes(activeSorter.field as OrderSortField)
      ? activeSorter.field as OrderSortField
      : query.sort_by
    setQuery((current) => ({
      ...current,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 20,
      sort_by: field,
      sort_order: activeSorter?.order === 'ascend' ? 'asc' : 'desc',
    }))
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Orders</Typography.Title>
          <Typography.Text type="secondary">Reserve stock and guide orders safely through fulfilment.</Typography.Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>Create order</Button>
      </div>
      <Card>
        <div className="orders-toolbar">
          <Input.Search allowClear placeholder="Search order number or creator" onSearch={(search) => setQuery((current) => ({ ...current, page: 1, search: search || undefined }))} />
          <Select allowClear placeholder="All statuses" options={statuses.map((value) => ({ value, label: value }))} onChange={(order_status) => setQuery((current) => ({ ...current, page: 1, order_status }))} />
        </div>
        <Table<Order>
          rowKey="id"
          columns={columns}
          dataSource={ordersQuery.data?.items}
          loading={ordersQuery.isLoading}
          onChange={handleTableChange}
          scroll={{ x: 1000 }}
          locale={{ emptyText: ordersQuery.isError ? getApiErrorMessage(ordersQuery.error) : 'No orders match these filters' }}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total: ordersQuery.data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} orders`,
          }}
        />
      </Card>
      <OrderCreateModal
        open={createOpen}
        products={productsQuery.data?.items ?? []}
        warehouses={warehousesQuery.data?.items ?? []}
        optionsLoading={productsQuery.isLoading || warehousesQuery.isLoading}
        onClose={() => setCreateOpen(false)}
        onCreated={setSelectedOrderId}
      />
      <OrderDetailsDrawer orderId={selectedOrderId} onClose={() => setSelectedOrderId(null)} />
    </section>
  )
}
