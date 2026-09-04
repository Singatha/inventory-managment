import { EditOutlined, ReloadOutlined, TeamOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  App,
  Button,
  Card,
  Drawer,
  Form,
  Grid,
  Input,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { TableColumnsType } from 'antd'
import { useState } from 'react'
import { getApiErrorMessage } from '../../api/client'
import { getUsers, updateUser, type UserUpdate } from '../../api/users'
import type { User, UserRole } from '../../types/auth'

const roleLabels: Record<UserRole, string> = {
  ADMIN: 'Administrator',
  WAREHOUSE_MANAGER: 'Warehouse manager',
  EMPLOYEE: 'Employee',
}

export function UsersPage() {
  const { message } = App.useApp()
  const queryClient = useQueryClient()
  const screens = Grid.useBreakpoint()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [form] = Form.useForm<UserUpdate>()
  const usersQuery = useQuery({
    queryKey: ['users', page, pageSize],
    queryFn: () => getUsers(page, pageSize),
  })
  const updateMutation = useMutation({
    mutationFn: ({ id, changes }: { id: number; changes: UserUpdate }) => updateUser(id, changes),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['users'] })
      message.success('User updated')
      setSelectedUser(null)
    },
    onError: (error) => message.error(getApiErrorMessage(error)),
  })

  function openEditor(user: User) {
    setSelectedUser(user)
    form.setFieldsValue({
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      is_active: user.is_active,
    })
  }

  const columns: TableColumnsType<User> = [
    {
      title: 'User',
      key: 'user',
      render: (_, user) => (
        <div className="user-cell">
          <span className="user-initials">{user.first_name[0]}{user.last_name[0]}</span>
          <span><Typography.Text strong>{user.first_name} {user.last_name}</Typography.Text><Typography.Text type="secondary">{user.email}</Typography.Text></span>
        </div>
      ),
    },
    { title: 'Role', dataIndex: 'role', render: (role: UserRole) => roleLabels[role] },
    {
      title: 'Status',
      dataIndex: 'is_active',
      render: (active: boolean) => <Tag color={active ? 'success' : 'default'}>{active ? 'Active' : 'Inactive'}</Tag>,
    },
    {
      title: '',
      key: 'actions',
      align: 'right',
      render: (_, user) => <Button type="text" aria-label={`Edit ${user.first_name}`} icon={<EditOutlined />} onClick={() => openEditor(user)} />,
    },
  ]

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>Users</Typography.Title>
          <Typography.Text type="secondary">Manage access, roles, and account status.</Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => usersQuery.refetch()}>Refresh</Button>
      </div>
      <Card>
        <Table<User>
          rowKey="id"
          columns={columns}
          dataSource={usersQuery.data?.items}
          loading={usersQuery.isLoading}
          locale={{ emptyText: usersQuery.isError ? getApiErrorMessage(usersQuery.error) : 'No users found' }}
          scroll={{ x: 680 }}
          pagination={{
            current: page,
            pageSize,
            total: usersQuery.data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} users`,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPageSize !== pageSize ? 1 : nextPage)
              setPageSize(nextPageSize)
            },
          }}
        />
      </Card>
      <Drawer
        title={<Space><TeamOutlined /> Edit user</Space>}
        width={screens.sm ? 440 : '100%'}
        open={Boolean(selectedUser)}
        onClose={() => setSelectedUser(null)}
        destroyOnHidden
        extra={<Button type="primary" loading={updateMutation.isPending} onClick={() => form.submit()}>Save changes</Button>}
      >
        <Form<UserUpdate>
          form={form}
          layout="vertical"
          onFinish={(changes) => selectedUser && updateMutation.mutate({ id: selectedUser.id, changes })}
        >
          <Form.Item label="First name" name="first_name" rules={[{ required: true }, { max: 100 }]}>
            <Input size="large" />
          </Form.Item>
          <Form.Item label="Last name" name="last_name" rules={[{ required: true }, { max: 100 }]}>
            <Input size="large" />
          </Form.Item>
          <Form.Item label="Role" name="role" rules={[{ required: true }]}>
            <Select
              size="large"
              options={Object.entries(roleLabels).map(([value, label]) => ({ value, label }))}
            />
          </Form.Item>
          <Form.Item label="Active account" name="is_active" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Drawer>
    </section>
  )
}
