import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { App, Form, Input, InputNumber, Modal, Select } from 'antd'
import { transferStock } from '../../api/inventory'
import { getApiErrorMessage } from '../../api/client'
import type { Product } from '../../types/product'
import type { Warehouse } from '../../types/warehouse'
import type { StockTransferInput } from '../../types/inventory'

interface TransferStockModalProps {
  open: boolean
  products: Product[]
  warehouses: Warehouse[]
  optionsLoading: boolean
  onClose: () => void
}

export function TransferStockModal({
  open,
  products,
  warehouses,
  optionsLoading,
  onClose,
}: TransferStockModalProps) {
  const [form] = Form.useForm<StockTransferInput>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const sourceWarehouseId = Form.useWatch('source_warehouse_id', form)
  const mutation = useMutation({
    mutationFn: (values: StockTransferInput) => transferStock(values),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['inventory'] }),
        queryClient.invalidateQueries({ queryKey: ['stock-movements'] }),
      ])
      message.success('Stock transferred')
      onClose()
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  useEffect(() => {
    if (!open) return
    form.resetFields()
    form.setFieldsValue({ quantity: 1 })
  }, [form, open])

  const warehouseOptions = warehouses.map((warehouse) => ({
    value: warehouse.id,
    label: `${warehouse.code} — ${warehouse.name}`,
  }))

  return (
    <Modal
      title="Transfer stock"
      open={open}
      onCancel={onClose}
      okText="Transfer stock"
      confirmLoading={mutation.isPending}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form<StockTransferInput>
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        requiredMark={false}
      >
        <Form.Item label="Product" name="product_id" rules={[{ required: true }]}>
          <Select
            showSearch
            optionFilterProp="label"
            loading={optionsLoading}
            placeholder="Select a product"
            options={products.map((product) => ({
              value: product.id,
              label: `${product.sku} — ${product.name}`,
            }))}
          />
        </Form.Item>
        <div className="form-grid">
          <Form.Item label="Source warehouse" name="source_warehouse_id" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              loading={optionsLoading}
              placeholder="Move stock from"
              options={warehouseOptions}
              onChange={() => form.setFieldValue('destination_warehouse_id', undefined)}
            />
          </Form.Item>
          <Form.Item label="Destination warehouse" name="destination_warehouse_id" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              loading={optionsLoading}
              disabled={!sourceWarehouseId}
              placeholder="Move stock to"
              options={warehouseOptions.filter((option) => option.value !== sourceWarehouseId)}
            />
          </Form.Item>
        </div>
        <Form.Item label="Quantity" name="quantity" rules={[{ required: true }]}>
          <InputNumber min={1} precision={0} className="full-width" />
        </Form.Item>
        <Form.Item label="Transfer notes" name="notes" rules={[{ max: 2000 }]}>
          <Input.TextArea rows={3} placeholder="Optional reason or handling instructions" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
