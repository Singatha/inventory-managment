import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { App, Form, Input, InputNumber, Modal, Select } from 'antd'
import { adjustStock, receiveStock } from '../../api/inventory'
import { getApiErrorMessage } from '../../api/client'
import type { Product } from '../../types/product'
import type { Warehouse } from '../../types/warehouse'
import type { InventoryItem } from '../../types/inventory'

export type InventoryOperation = 'receive' | 'adjust'

interface OperationFormValues {
  product_id: number
  warehouse_id: number
  quantity: number
  notes?: string
  reason?: string
}

interface InventoryOperationModalProps {
  mode: InventoryOperation | null
  inventory: InventoryItem | null
  products: Product[]
  warehouses: Warehouse[]
  optionsLoading: boolean
  onClose: () => void
}

export function InventoryOperationModal({
  mode,
  inventory,
  products,
  warehouses,
  optionsLoading,
  onClose,
}: InventoryOperationModalProps) {
  const [form] = Form.useForm<OperationFormValues>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const mutation = useMutation({
    mutationFn: (values: OperationFormValues) => mode === 'receive'
      ? receiveStock({
          product_id: values.product_id,
          warehouse_id: values.warehouse_id,
          quantity: values.quantity,
          notes: values.notes || null,
        })
      : adjustStock({
          product_id: values.product_id,
          warehouse_id: values.warehouse_id,
          quantity: values.quantity,
          reason: values.reason || '',
        }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['inventory'] })
      message.success(mode === 'receive' ? 'Stock received' : 'Stock adjusted')
      onClose()
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  useEffect(() => {
    if (!mode) return
    form.resetFields()
    form.setFieldsValue({
      product_id: inventory?.product_id,
      warehouse_id: inventory?.warehouse_id,
      quantity: mode === 'receive' ? 1 : undefined,
    })
  }, [form, inventory, mode])

  return (
    <Modal
      title={mode === 'receive' ? 'Receive stock' : 'Adjust stock'}
      open={Boolean(mode)}
      onCancel={onClose}
      okText={mode === 'receive' ? 'Receive stock' : 'Apply adjustment'}
      confirmLoading={mutation.isPending}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form<OperationFormValues>
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
        <Form.Item label="Warehouse" name="warehouse_id" rules={[{ required: true }]}>
          <Select
            showSearch
            optionFilterProp="label"
            loading={optionsLoading}
            placeholder="Select a warehouse"
            options={warehouses.map((warehouse) => ({
              value: warehouse.id,
              label: `${warehouse.code} — ${warehouse.name}`,
            }))}
          />
        </Form.Item>
        <Form.Item
          label={mode === 'receive' ? 'Quantity received' : 'Quantity change'}
          name="quantity"
          extra={mode === 'adjust' ? 'Use a positive number to add stock or a negative number to remove it.' : undefined}
          rules={[
            { required: true },
            {
              validator: (_, value) => mode === 'adjust' && value === 0
                ? Promise.reject(new Error('Adjustment quantity cannot be zero.'))
                : Promise.resolve(),
            },
          ]}
        >
          <InputNumber
            min={mode === 'receive' ? 1 : undefined}
            precision={0}
            className="full-width"
            placeholder={mode === 'receive' ? 'Units received' : 'e.g. -3 or 5'}
          />
        </Form.Item>
        {mode === 'receive' ? (
          <Form.Item label="Receipt notes" name="notes" rules={[{ max: 2000 }]}>
            <Input.TextArea rows={3} placeholder="Optional delivery or receiving notes" />
          </Form.Item>
        ) : (
          <Form.Item label="Reason" name="reason" rules={[{ required: true }, { max: 2000 }]}>
            <Input.TextArea rows={3} placeholder="Explain why this adjustment is required" />
          </Form.Item>
        )}
      </Form>
    </Modal>
  )
}
