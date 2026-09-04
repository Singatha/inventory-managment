import { useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { App, Form, Input, Modal } from 'antd'
import { createWarehouse, updateWarehouse } from '../../api/warehouses'
import { getApiErrorMessage } from '../../api/client'
import type { Warehouse, WarehouseInput } from '../../types/warehouse'

interface WarehouseFormModalProps {
  open: boolean
  warehouse: Warehouse | null
  onClose: () => void
}

const emptyWarehouse: WarehouseInput = { name: '', code: '', location: '' }

export function WarehouseFormModal({ open, warehouse, onClose }: WarehouseFormModalProps) {
  const [form] = Form.useForm<WarehouseInput>()
  const queryClient = useQueryClient()
  const { message } = App.useApp()
  const mutation = useMutation({
    mutationFn: (values: WarehouseInput) => warehouse
      ? updateWarehouse(warehouse.id, values)
      : createWarehouse(values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['warehouses'] })
      message.success(warehouse ? 'Warehouse updated' : 'Warehouse created')
      onClose()
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  useEffect(() => {
    if (!open) return
    form.setFieldsValue(warehouse ? {
      name: warehouse.name,
      code: warehouse.code,
      location: warehouse.location,
    } : emptyWarehouse)
  }, [form, open, warehouse])

  return (
    <Modal
      title={warehouse ? 'Edit warehouse' : 'Add warehouse'}
      open={open}
      onCancel={onClose}
      okText={warehouse ? 'Save changes' : 'Create warehouse'}
      confirmLoading={mutation.isPending}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Form<WarehouseInput>
        form={form}
        layout="vertical"
        onFinish={(values) => mutation.mutate(values)}
        requiredMark={false}
      >
        <Form.Item label="Warehouse name" name="name" rules={[{ required: true }, { max: 200 }]}>
          <Input placeholder="e.g. Johannesburg Distribution Centre" />
        </Form.Item>
        <Form.Item label="Warehouse code" name="code" rules={[{ required: true }, { max: 32 }]}>
          <Input placeholder="e.g. JHB-01" />
        </Form.Item>
        <Form.Item label="Location" name="location" rules={[{ required: true }, { max: 500 }]}>
          <Input.TextArea rows={3} placeholder="Street address or operating location" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
