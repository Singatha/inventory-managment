import { Descriptions, Drawer, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import type { StockMovementDetail, StockMovementType } from '../../types/inventory'

interface MovementDetailsDrawerProps {
  movement: StockMovementDetail | null
  onClose: () => void
}

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

export function MovementDetailsDrawer({ movement, onClose }: MovementDetailsDrawerProps) {
  return (
    <Drawer
      title="Stock movement details"
      width={540}
      open={Boolean(movement)}
      onClose={onClose}
      destroyOnHidden
    >
      {movement && (
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="Movement">
            <Tag>{movementLabels[movement.type]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Date">
            {dayjs(movement.created_at).format('D MMM YYYY, HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="Product">
            <Typography.Text strong>{movement.product.name}</Typography.Text>
            <br />
            <Typography.Text type="secondary" code>{movement.product.sku}</Typography.Text>
          </Descriptions.Item>
          <Descriptions.Item label="Warehouse">
            {movement.warehouse.code} — {movement.warehouse.name}
          </Descriptions.Item>
          <Descriptions.Item label="Quantity">
            <Typography.Text type={movement.quantity < 0 ? 'danger' : 'success'} strong>
              {movement.quantity > 0 ? '+' : ''}{movement.quantity}
            </Typography.Text>
          </Descriptions.Item>
          <Descriptions.Item label="Performed by">
            {movement.creator.first_name} {movement.creator.last_name}
          </Descriptions.Item>
          <Descriptions.Item label="Reference">
            {movement.reference_type && movement.reference_id
              ? `${movement.reference_type} #${movement.reference_id}`
              : '—'}
          </Descriptions.Item>
          <Descriptions.Item label="Notes">{movement.notes || '—'}</Descriptions.Item>
        </Descriptions>
      )}
    </Drawer>
  )
}
