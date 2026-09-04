import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { App, Form, Input, InputNumber, Modal, Switch } from 'antd'
import { createProduct, updateProduct } from '../../api/products'
import { getApiErrorMessage } from '../../api/client'
import type { Product, ProductInput } from '../../types/product'

interface ProductFormModalProps {
  open: boolean
  product: Product | null
  onClose: () => void
}

const emptyProduct: ProductInput = {
  sku: '',
  name: '',
  description: null,
  category: '',
  price: 0,
  reorder_level: 0,
  is_active: true,
}

export function ProductFormModal({ open, product, onClose }: ProductFormModalProps) {
  const [form] = Form.useForm<ProductInput>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const mutation = useMutation({
    mutationFn: (values: ProductInput) => product
      ? updateProduct(product.id, values)
      : createProduct(values),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['products'] }),
        queryClient.invalidateQueries({ queryKey: ['product-categories'] }),
      ])
      message.success(product ? 'Product updated' : 'Product created')
      onClose()
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  useEffect(() => {
    if (!open) return
    form.setFieldsValue(product ? {
      sku: product.sku,
      name: product.name,
      description: product.description,
      category: product.category,
      price: product.price,
      reorder_level: product.reorder_level,
      is_active: product.is_active,
    } : emptyProduct)
  }, [form, open, product])

  return (
    <Modal
      title={product ? 'Edit product' : 'Add product'}
      open={open}
      onCancel={onClose}
      okText={product ? 'Save changes' : 'Create product'}
      confirmLoading={mutation.isPending}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form<ProductInput>
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        requiredMark={false}
      >
        <div className="form-grid">
          <Form.Item label="SKU" name="sku" rules={[{ required: true }, { max: 64 }]}>
            <Input placeholder="e.g. LAP-001" />
          </Form.Item>
          <Form.Item label="Category" name="category" rules={[{ required: true }, { max: 100 }]}>
            <Input placeholder="e.g. Laptops" />
          </Form.Item>
        </div>
        <Form.Item label="Product name" name="name" rules={[{ required: true }, { max: 200 }]}>
          <Input placeholder="e.g. Dell Latitude 7450" />
        </Form.Item>
        <Form.Item label="Description" name="description" rules={[{ max: 5000 }]}>
          <Input.TextArea rows={3} placeholder="Optional product description" />
        </Form.Item>
        <div className="form-grid">
          <Form.Item label="Unit price" name="price" rules={[{ required: true }]}>
            <InputNumber min={0} precision={2} prefix="R" className="full-width" />
          </Form.Item>
          <Form.Item label="Reorder level" name="reorder_level" rules={[{ required: true }]}>
            <InputNumber min={0} precision={0} className="full-width" />
          </Form.Item>
        </div>
        <Form.Item label="Active product" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

