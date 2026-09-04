import { DeleteOutlined, EditOutlined, EyeOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App,
  Button,
  Card,
  Input,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import type { TableColumnsType, TablePaginationConfig } from 'antd'
import type { FilterValue, SorterResult } from 'antd/es/table/interface'
import { useState } from 'react'
import { deactivateProduct, getProductCategories, getProducts } from '../../api/products'
import { getApiErrorMessage } from '../../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Product, ProductQuery, ProductSortField } from '../../types/product'
import { ProductDetailsDrawer } from './ProductDetailsDrawer'
import { ProductFormModal } from './ProductFormModal'

const currency = new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR' })

export function ProductsPage() {
  const { user } = useAuth()
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const [query, setQuery] = useState<ProductQuery>({
    page: 1,
    page_size: 20,
    is_active: true,
    sort_by: 'name',
    sort_order: 'asc',
  })
  const [formProduct, setFormProduct] = useState<Product | null | undefined>(undefined)
  const [detailProduct, setDetailProduct] = useState<Product | null>(null)
  const canManage = user?.role === 'ADMIN' || user?.role === 'WAREHOUSE_MANAGER'
  const productsQuery = useQuery({
    queryKey: ['products', query],
    queryFn: () => getProducts(query),
  })
  const categoriesQuery = useQuery({
    queryKey: ['product-categories'],
    queryFn: getProductCategories,
  })
  const deleteMutation = useMutation({
    mutationFn: deactivateProduct,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['products'] })
      message.success('Product deactivated')
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  const columns: TableColumnsType<Product> = [
    { title: 'SKU', dataIndex: 'sku', sorter: true, width: 150, render: (sku: string) => <Typography.Text code>{sku}</Typography.Text> },
    {
      title: 'Product',
      dataIndex: 'name',
      sorter: true,
      render: (name: string, product) => <Button type="link" className="table-link" onClick={() => setDetailProduct(product)}>{name}</Button>,
    },
    { title: 'Category', dataIndex: 'category', sorter: true, width: 170 },
    { title: 'Price', dataIndex: 'price', sorter: true, width: 140, align: 'right', render: (price: number) => currency.format(price) },
    { title: 'Reorder at', dataIndex: 'reorder_level', sorter: true, width: 120, align: 'right' },
    { title: 'Status', dataIndex: 'is_active', width: 110, render: (active: boolean) => <Tag color={active ? 'success' : 'default'}>{active ? 'Active' : 'Inactive'}</Tag> },
    {
      title: '',
      key: 'actions',
      width: canManage ? 130 : 55,
      align: 'right',
      render: (_, product) => (
        <Space size={2}>
          <Tooltip title="View"><Button type="text" aria-label={`View ${product.name}`} icon={<EyeOutlined />} onClick={() => setDetailProduct(product)} /></Tooltip>
          {canManage && <Tooltip title="Edit"><Button type="text" aria-label={`Edit ${product.name}`} icon={<EditOutlined />} onClick={() => setFormProduct(product)} /></Tooltip>}
          {canManage && product.is_active && (
            <Popconfirm title="Deactivate this product?" description="It will remain available in audit history." onConfirm={() => deleteMutation.mutate(product.id)}>
              <Tooltip title="Deactivate"><Button type="text" danger aria-label={`Deactivate ${product.name}`} icon={<DeleteOutlined />} /></Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  function handleTableChange(
    pagination: TablePaginationConfig,
    _: Record<string, FilterValue | null>,
    sorter: SorterResult<Product> | SorterResult<Product>[],
  ) {
    const activeSorter = Array.isArray(sorter) ? sorter[0] : sorter
    const allowedSorts: ProductSortField[] = ['sku', 'name', 'category', 'price', 'reorder_level', 'created_at']
    const field = typeof activeSorter?.field === 'string' && allowedSorts.includes(activeSorter.field as ProductSortField)
      ? activeSorter.field as ProductSortField
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
          <Typography.Title level={2}>Products</Typography.Title>
          <Typography.Text type="secondary">Manage the catalog, pricing, and reorder thresholds.</Typography.Text>
        </div>
        {canManage && <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormProduct(null)}>Add product</Button>}
      </div>
      <Card>
        <div className="table-toolbar">
          <Input.Search
            allowClear
            placeholder="Search by SKU or product name"
            onSearch={(search) => setQuery((current) => ({ ...current, page: 1, search: search || undefined }))}
          />
          <Select
            allowClear
            placeholder="All categories"
            loading={categoriesQuery.isLoading}
            options={categoriesQuery.data?.map((category) => ({ value: category, label: category }))}
            onChange={(category) => setQuery((current) => ({ ...current, page: 1, category }))}
          />
          <Select
            value={query.is_active === undefined ? 'all' : String(query.is_active)}
            options={[{ value: 'all', label: 'All statuses' }, { value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]}
            onChange={(value) => setQuery((current) => ({ ...current, page: 1, is_active: value === 'all' ? undefined : value === 'true' }))}
          />
        </div>
        <Table<Product>
          rowKey="id"
          columns={columns}
          dataSource={productsQuery.data?.items}
          loading={productsQuery.isLoading}
          onChange={handleTableChange}
          scroll={{ x: 980 }}
          locale={{ emptyText: productsQuery.isError ? getApiErrorMessage(productsQuery.error) : 'No products match these filters' }}
          pagination={{
            current: query.page,
            pageSize: query.page_size,
            total: productsQuery.data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} products`,
          }}
        />
      </Card>
      <ProductFormModal open={formProduct !== undefined} product={formProduct ?? null} onClose={() => setFormProduct(undefined)} />
      <ProductDetailsDrawer product={detailProduct} onClose={() => setDetailProduct(null)} />
    </section>
  )
}

