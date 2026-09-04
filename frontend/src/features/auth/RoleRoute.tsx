import type { PropsWithChildren } from 'react'
import { Result } from 'antd'
import type { UserRole } from '../../types/auth'
import { useAuth } from './AuthContext'

interface RoleRouteProps extends PropsWithChildren {
  roles: UserRole[]
}

export function RoleRoute({ roles, children }: RoleRouteProps) {
  const { user } = useAuth()
  if (!user || !roles.includes(user.role)) {
    return <Result status="403" title="Access denied" subTitle="You do not have permission to view this page." />
  }
  return children
}

