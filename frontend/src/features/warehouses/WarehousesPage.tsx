import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { App, Button, Card, Input, Popconfirm, Space, Table, Tooltip, Typography } from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import type { FilterValue, SorterResult } from 'antd/es/table/interface'
import { useState } from 'react'
import { deleteWarehouse, getWarehouses } from '../../api/warehouses'
import { getApiErrorMessage } from '../../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Warehouse, WarehouseQuery, WarehouseSortField } from '../../types/warehouse'
import { WarehouseFormModal } from './WarehouseFormModal'

export function WarehousesPage() {
  const { user } = useAuth()
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState<WarehouseQuery>({
    page: 1,
    page_size: 20,
    sort_by: 'name',
    sort_order: 'asc',
  })
  const [formWarehouse, setFormWarehouse] = useState<Warehouse | null | undefined>(undefined)
  const canManage = user?.role === 'ADMIN' || user?.role === 'WAREHOUSE_MANAGER'
  const warehousesQuery = useQuery({
    queryKey: ['warehouses', query],
    queryFn: () => getWarehouses(query),
  })
  const deleteMutation = useMutation({
    mutationFn: deleteWarehouse,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      message.success('Warehouse deleted')
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  const columns: TableColumnsType<Warehouse> = [
    { title: 'Code', dataIndex: 'code', sorter: true, width: 150, render: (code: string) => <Typography.Text code>{code}</Typography.Text> },
    { title: 'Warehouse', dataIndex: 'name', sorter: true, render: (name: string) => <Typography.Text strong>{name}</Typography.Text> },
    { title: 'Location', dataIndex: 'location', sorter: true },
    {
      title: '',
      key: 'actions',
      width: canManage ? 95 : 0,
      align: 'right',
      render: (_, warehouse) => canManage ? (
        <Space size={2}>
          <Tooltip title="Edit"><Button type="text" aria-label={`Edit ${warehouse.name}`} icon={<EditOutlined />} onClick={() => setFormWarehouse(warehouse)} /></Tooltip>
          <Popconfirm title="Delete this warehouse?" description="Warehouses with inventory history cannot be deleted." onConfirm={() => deleteMutation.mutate(warehouse.id)}>
            <Tooltip title="Delete"><Button type="text" danger aria-label={`Delete ${warehouse.name}`} icon={<DeleteOutlined />} /></Tooltip>
          </Popconfirm>
        </Space>
      ) : null,
    },
  ]

  function handleTableChange(
    pagination: TablePaginationConfig,
    _: Record<string, FilterValue | null>,
    sorter: SorterResult<Warehouse> | SorterResult<Warehouse>[],
  ) {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter
    const allowedSorts: WarehouseSortField[] = ['code', 'name', 'location', 'created_at']
    const field = typeof activeSorter?.field === 'string' && allowedSorts.includes(activeSorter.field as WarehouseSortField)
      ? activeSorter.field as WarehouseSortField
      : query.sort_by
    setQuery((current) => ({
      ...current,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 20,
      sort_by: field,
      sort_order: activeSorter?.order === 'descend' ? 'desc' : 'asc',
    }))
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Warehouses</Typography.Title>
          <Typography.Text type="secondary">Manage the locations that receive and hold inventory.</Typography.Text>
        </div>
        {canManage && <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormWarehouse(null)}>Add warehouse</Button>}
      </div>
      <Card>
        <div className="single-search-toolbar">
          <Input.Search
            allowClear
            placeholder="Search by code, name, or location"
            onSearch={(search) => setQuery((current) => ({ ...current, page: 1, search: search || undefined }))}
          />
        </div>
        <Table<Warehouse>
          rowKey="id"
          columns={columns}
          dataSource={warehousesQuery.data?.items}
          loading={warehousesQuery.isLoading}
          onChange={handleTableChange}
          scroll={{ x: 760 }}
          locale={{ emptyText: warehousesQuery.isError ? getApiErrorMessage(warehousesQuery.error) : 'No warehouses match this search' }}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total: warehousesQuery.data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} warehouses`,
          }}
        />
      </Card>
      <WarehouseFormModal
        open={formWarehouse !== undefined}
        warehouse={formWarehouse ?? null}
        onClose={() => setFormWarehouse(undefined)}
      />
    </section>
  )
}
