import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { App, Button, Form, InputNumber, Modal, Select, Space } from 'antd'
import { createOrder } from '../../api/orders'
import { getApiErrorMessage } from '../../api/client'
import type { Product } from '../../types/product'
import type { Warehouse } from '../../types/warehouse'
import type { OrderInput } from '../../types/order'

interface OrderCreateModalProps {
  open: boolean
  products: Product[]
  warehouses: Warehouse[]
  optionsLoading: boolean
  onClose: () => void
  onCreated: (orderId: number) => void
}

export function OrderCreateModal({
  open,
  products,
  warehouses,
  optionsLoading,
  onClose,
  onCreated,
}: OrderCreateModalProps) {
  const [form] = Form.useForm<OrderInput>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const mutation = useMutation({
    mutationFn: createOrder,
    onSuccess: async (order) => {
      await queryClient.invalidateQueries({ queryKey: ['orders'] })
      message.success(`Order ${order.order_number} created`)
      onClose()
      onCreated(order.id)
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  useEffect(() => {
    if (!open) return
    form.resetFields()
    form.setFieldsValue({ items: [{ quantity: 1 }] as OrderInput['items'] })
  }, [form, open])

  return (
    <Modal
      title="Create order"
      width={780}
      open={open}
      onCancel={onClose}
      okText="Create order"
      confirmLoading={mutation.isPending}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form<OrderInput>
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        requiredMark={false}
      >
        <Form.List name="items" rules={[{ validator: async (_, items) => {
          if (!items?.length) throw new Error('Add at least one order line.')
        } }]}
        >
          {(fields, { add, remove }, { errors }) => (
            <Space direction="vertical" className="full-width" size="middle">
              {fields.map((field, index) => (
                <div className="order-line" key={field.key}>
                  <Form.Item
                    label={index === 0 ? 'Product' : undefined}
                    name={[field.name, 'product_id']}
                    rules={[{ required: true, message: 'Select a product' }]}
                  >
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
                  <Form.Item
                    label={index === 0 ? 'Fulfil from' : undefined}
                    name={[field.name, 'warehouse_id']}
                    rules={[{ required: true, message: 'Select a warehouse' }]}
                  >
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
                    label={index === 0 ? 'Quantity' : undefined}
                    name={[field.name, 'quantity']}
                    rules={[{ required: true, message: 'Enter a quantity' }]}
                  >
                    <InputNumber min={1} precision={0} className="full-width" />
                  </Form.Item>
                  <Button
                    type="text"
                    danger
                    aria-label={`Remove order line ${index + 1}`}
                    icon={<DeleteOutlined />}
                    disabled={fields.length === 1}
                    onClick={() => remove(field.name)}
                  />
                </div>
              ))}
              <Form.ErrorList errors={errors} />
              <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ quantity: 1 })}>
                Add order line
              </Button>
            </Space>
          )}
        </Form.List>
      </Form>
    </Modal>
  )
}
