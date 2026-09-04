import { AuditOutlined, InboxOutlined, PlusOutlined, WarningOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Button, Card, Col, Input, Row, Select, Space, Statistic, Table, Tag, Typography } from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import type { FilterValue, SorterResult } from 'antd/es/table/interface'
import { useState } from 'react'
import { getInventory } from '../../api/inventory'
import { getProducts } from '../../api/products'
import { getWarehouses } from '../../api/warehouses'
import { getApiErrorMessage } from '../../api/client'
import type { InventoryItem, InventoryQuery, InventorySortField } from '../../types/inventory'
import { useAuth } from '../auth/AuthContext'
import { InventoryOperationModal, type InventoryOperation } from './InventoryOperationModal'

export function InventoryPage() {
  const { user } = useAuth()
  const [query, setQuery] = useState<InventoryQuery>({
    page: 1,
    page_size: 20,
    sort_by: 'product',
    sort_order: 'asc',
  })
  const [operation, setOperation] = useState<InventoryOperation | null>(null)
  const [selectedInventory, setSelectedInventory] = useState<InventoryItem | null>(null)
  const canManage = user?.role === 'ADMIN' || user?.role === 'WAREHOUSE_MANAGER'
  const inventoryQuery = useQuery({
    queryKey: ['inventory', query],
    queryFn: () => getInventory(query),
  })
  const productsQuery = useQuery({
    queryKey: ['products', 'inventory-options'],
    queryFn: () => getProducts({ page: 1, page_size: 100, is_active: true }),
  })
  const warehousesQuery = useQuery({
    queryKey: ['warehouses', 'inventory-options'],
    queryFn: () => getWarehouses({ page: 1, page_size: 100 }),
  })

  function openOperation(mode: InventoryOperation, inventory: InventoryItem | null = null) {
    setSelectedInventory(inventory)
    setOperation(mode)
  }

  const columns: TableColumnsType<InventoryItem> = [
    {
      title: 'Product',
      key: 'product',
      sorter: true,
      render: (_, inventory) => (
        <div className="inventory-identity">
          <Typography.Text strong>{inventory.product.name}</Typography.Text>
          <Typography.Text type="secondary" code>{inventory.product.sku}</Typography.Text>
        </div>
      ),
    },
    {
      title: 'Warehouse',
      key: 'warehouse',
      sorter: true,
      render: (_, inventory) => (
        <div className="inventory-identity">
          <Typography.Text>{inventory.warehouse.name}</Typography.Text>
          <Typography.Text type="secondary">{inventory.warehouse.code}</Typography.Text>
        </div>
      ),
    },
    { title: 'On hand', dataIndex: 'quantity_on_hand', sorter: true, align: 'right', width: 115 },
    { title: 'Reserved', dataIndex: 'quantity_reserved', sorter: true, align: 'right', width: 115 },
    { title: 'Available', dataIndex: 'available_quantity', sorter: true, align: 'right', width: 115, render: (value: number) => <Typography.Text strong>{value}</Typography.Text> },
    { title: 'Reorder at', key: 'reorder_level', align: 'right', width: 110, render: (_, inventory) => inventory.product.reorder_level },
    { title: 'Status', key: 'status', width: 115, render: (_, inventory) => <Tag color={inventory.is_low_stock ? 'warning' : 'success'}>{inventory.is_low_stock ? 'Low stock' : 'Healthy'}</Tag> },
    {
      title: '',
      key: 'actions',
      align: 'right',
      width: canManage ? 100 : 0,
      render: (_, inventory) => canManage ? <Button type="link" onClick={() => openOperation('adjust', inventory)}>Adjust</Button> : null,
    },
  ]

  function handleTableChange(
    pagination: TablePaginationConfig,
    _: Record<string, FilterValue | null>,
    sorter: SorterResult<InventoryItem> | SorterResult<InventoryItem>[],
  ) {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter
    const allowedSorts: InventorySortField[] = ['product', 'warehouse', 'quantity_on_hand', 'quantity_reserved', 'available_quantity']
    const field = typeof activeSorter?.columnKey === 'string' && allowedSorts.includes(activeSorter.columnKey as InventorySortField)
      ? activeSorter.columnKey as InventorySortField
      : typeof activeSorter?.field === 'string' && allowedSorts.includes(activeSorter.field as InventorySortField)
        ? activeSorter.field as InventorySortField
        : query.sort_by
    setQuery((current) => ({
      ...current,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 20,
      sort_by: field,
      sort_order: activeSorter?.order === 'descend' ? 'desc' : 'asc',
    }))
  }

  const summary = inventoryQuery.data
  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Inventory</Typography.Title>
          <Typography.Text type="secondary">Track available stock and record every physical quantity change.</Typography.Text>
        </div>
        {canManage && (
          <Space>
            <Button icon={<AuditOutlined />} onClick={() => openOperation('adjust')}>Adjust stock</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openOperation('receive')}>Receive stock</Button>
          </Space>
        )}
      </div>
      <Row gutter={[16, 16]} className="inventory-summary">
        <Col xs={12} lg={6}><Card><Statistic title="On hand" value={summary?.total_quantity_on_hand ?? 0} prefix={<InboxOutlined />} /></Card></Col>
        <Col xs={12} lg={6}><Card><Statistic title="Reserved" value={summary?.total_quantity_reserved ?? 0} /></Card></Col>
        <Col xs={12} lg={6}><Card><Statistic title="Available" value={summary?.total_available_quantity ?? 0} /></Card></Col>
        <Col xs={12} lg={6}><Card><Statistic title="Low stock" value={summary?.low_stock_count ?? 0} prefix={<WarningOutlined />} /></Card></Col>
      </Row>
      <Card>
        <div className="inventory-toolbar">
          <Input.Search
            allowClear
            placeholder="Search products or warehouses"
            onSearch={(search) => setQuery((current) => ({ ...current, page: 1, search: search || undefined }))}
          />
          <Select
            allowClear
            showSearch
            optionFilterProp="label"
            placeholder="All warehouses"
            loading={warehousesQuery.isLoading}
            options={warehousesQuery.data?.items.map((warehouse) => ({ value: warehouse.id, label: `${warehouse.code} — ${warehouse.name}` }))}
            onChange={(warehouseId) => setQuery((current) => ({ ...current, page: 1, warehouse_id: warehouseId }))}
          />
          <Select
            value={query.low_stock === undefined ? 'all' : String(query.low_stock)}
            options={[{ value: 'all', label: 'All stock levels' }, { value: 'true', label: 'Low stock' }, { value: 'false', label: 'Healthy stock' }]}
            onChange={(value) => setQuery((current) => ({ ...current, page: 1, low_stock: value === 'all' ? undefined : value === 'true' }))}
          />
        </div>
        <Table<InventoryItem>
          rowKey="id"
          columns={columns}
          dataSource={summary?.items}
          loading={inventoryQuery.isLoading}
          onChange={handleTableChange}
          scroll={{ x: 1050 }}
          locale={{ emptyText: inventoryQuery.isError ? getApiErrorMessage(inventoryQuery.error) : 'No inventory matches these filters' }}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total: summary?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} inventory records`,
          }}
        />
      </Card>
      <InventoryOperationModal
        mode={operation}
        inventory={selectedInventory}
        products={productsQuery.data?.items ?? []}
        warehouses={warehousesQuery.data?.items ?? []}
        optionsLoading={productsQuery.isLoading || warehousesQuery.isLoading}
        onClose={() => {
          setOperation(null)
          setSelectedInventory(null)
        }}
      />
    </section>
  )
}
