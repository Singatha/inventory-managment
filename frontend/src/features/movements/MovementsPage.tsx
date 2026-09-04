import { useQuery } from '@tanstack/react-query'
import { Button, Card, DatePicker, Input, Select, Table, Tag, Typography } from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import type { FilterValue, SorterResult } from 'antd/es/table/interface'
import dayjs from 'dayjs'
import { useState } from 'react'
import { getStockMovements } from '../../api/inventory'
import { getWarehouses } from '../../api/warehouses'
import { getApiErrorMessage } from '../../api/client'
import type {
  StockMovementDetail,
  StockMovementQuery,
  StockMovementType,
} from '../../types/inventory'
import { MovementDetailsDrawer } from './MovementDetailsDrawer'

const movementLabels: Record<StockMovementType, string> = {
  RECEIVE: 'Receipt',
  ADJUSTMENT: 'Adjustment',
  RESERVE: 'Reservation',
  RELEASE: 'Release',
  SHIPMENT: 'Shipment',
  TRANSFER_IN: 'Transfer in',
  TRANSFER_OUT: 'Transfer out',
  RETURN: 'Return',
}

const movementColors: Record<StockMovementType, string> = {
  RECEIVE: 'green',
  ADJUSTMENT: 'gold',
  RESERVE: 'blue',
  RELEASE: 'cyan',
  SHIPMENT: 'purple',
  TRANSFER_IN: 'geekblue',
  TRANSFER_OUT: 'volcano',
  RETURN: 'lime',
}

const movementTypes = Object.entries(movementLabels).map(([value, label]) => ({
  value: value as StockMovementType,
  label,
}))

export function MovementsPage() {
  const [query, setQuery] = useState<StockMovementQuery>({
    page: 1,
    page_size: 20,
    sort_order: 'desc',
  })
  const [selectedMovement, setSelectedMovement] = useState<StockMovementDetail | null>(null)
  const movementsQuery = useQuery({
    queryKey: ['stock-movements', query],
    queryFn: () => getStockMovements(query),
  })
  const warehousesQuery = useQuery({
    queryKey: ['warehouses', 'movement-options'],
    queryFn: () => getWarehouses({ page: 1, page_size: 100 }),
  })

  const columns: TableColumnsType<StockMovementDetail> = [
    {
      title: 'Date',
      dataIndex: 'created_at',
      sorter: true,
      width: 165,
      render: (value: string) => dayjs(value).format('D MMM YYYY, HH:mm'),
    },
    {
      title: 'Movement',
      dataIndex: 'type',
      width: 135,
      render: (type: StockMovementType) => <Tag color={movementColors[type]}>{movementLabels[type]}</Tag>,
    },
    {
      title: 'Product',
      key: 'product',
      render: (_, movement) => (
        <div className="inventory-identity">
          <Button type="link" className="table-link" onClick={() => setSelectedMovement(movement)}>{movement.product.name}</Button>
          <Typography.Text type="secondary" code>{movement.product.sku}</Typography.Text>
        </div>
      ),
    },
    {
      title: 'Warehouse',
      key: 'warehouse',
      render: (_, movement) => (
        <div className="inventory-identity">
          <Typography.Text>{movement.warehouse.name}</Typography.Text>
          <Typography.Text type="secondary">{movement.warehouse.code}</Typography.Text>
        </div>
      ),
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      align: 'right',
      width: 105,
      render: (quantity: number) => (
        <Typography.Text type={quantity < 0 ? 'danger' : 'success'} strong>
          {quantity > 0 ? '+' : ''}{quantity}
        </Typography.Text>
      ),
    },
    {
      title: 'Performed by',
      key: 'creator',
      width: 155,
      render: (_, movement) => `${movement.creator.first_name} ${movement.creator.last_name}`,
    },
    {
      title: 'Reference',
      key: 'reference',
      width: 130,
      render: (_, movement) => movement.reference_type && movement.reference_id
        ? `${movement.reference_type} #${movement.reference_id}`
        : '—',
    },
  ]

  function handleTableChange(
    pagination: TablePaginationConfig,
    _: Record<string, FilterValue | null>,
    sorter: SorterResult<StockMovementDetail> | SorterResult<StockMovementDetail>[],
  ) {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter
    setQuery((current) => ({
      ...current,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 20,
      sort_order: activeSorter?.order === 'ascend' ? 'asc' : 'desc',
    }))
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Stock movements</Typography.Title>
          <Typography.Text type="secondary">Trace every receipt, adjustment, and transfer across warehouses.</Typography.Text>
        </div>
      </div>
      <Card>
        <div className="movement-toolbar">
          <Input.Search
            allowClear
            placeholder="Search products or warehouses"
            onSearch={(search) => setQuery((current) => ({ ...current, page: 1, search: search || undefined }))}
          />
          <Select
            allowClear
            placeholder="All movement types"
            options={movementTypes}
            onChange={(movementType) => setQuery((current) => ({ ...current, page: 1, movement_type: movementType }))}
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
          <DatePicker.RangePicker
            onChange={(_, dateStrings) => setQuery((current) => ({
              ...current,
              page: 1,
              created_from: dateStrings[0] ? dayjs(dateStrings[0]).startOf('day').toISOString() : undefined,
              created_to: dateStrings[1] ? dayjs(dateStrings[1]).endOf('day').toISOString() : undefined,
            }))}
          />
        </div>
        <Table<StockMovementDetail>
          rowKey="id"
          columns={columns}
          dataSource={movementsQuery.data?.items}
          loading={movementsQuery.isLoading}
          onChange={handleTableChange}
          scroll={{ x: 1120 }}
          locale={{ emptyText: movementsQuery.isError ? getApiErrorMessage(movementsQuery.error) : 'No stock movements match these filters' }}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total: movementsQuery.data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} movements`,
          }}
        />
      </Card>
      <MovementDetailsDrawer movement={selectedMovement} onClose={() => setSelectedMovement(null)} />
    </section>
  )
}
