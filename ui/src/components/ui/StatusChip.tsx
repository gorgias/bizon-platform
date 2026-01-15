import { cn } from '../../lib/utils'

type Status = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'enabled' | 'disabled'

interface StatusChipProps {
  status: Status
  className?: string
}

const statusConfig: Record<Status, { label: string; className: string }> = {
  pending: {
    label: 'Pending',
    className: 'bg-bizon-warning/20 text-bizon-warning',
  },
  running: {
    label: 'Running',
    className: 'bg-bizon-primary/20 text-bizon-primary',
  },
  success: {
    label: 'Success',
    className: 'bg-bizon-success/20 text-bizon-success',
  },
  failed: {
    label: 'Failed',
    className: 'bg-bizon-danger/20 text-bizon-danger',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'bg-bizon-muted/20 text-bizon-muted',
  },
  enabled: {
    label: 'Enabled',
    className: 'bg-bizon-success/20 text-bizon-success',
  },
  disabled: {
    label: 'Disabled',
    className: 'bg-bizon-muted/20 text-bizon-muted',
  },
}

export function StatusChip({ status, className }: StatusChipProps) {
  const config = statusConfig[status]

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}
