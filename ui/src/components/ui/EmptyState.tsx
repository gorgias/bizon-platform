import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && (
        <div className="mb-4 text-bizon-muted">{icon}</div>
      )}
      <h3 className="text-lg font-medium text-bizon-text mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-bizon-textSecondary mb-4 max-w-sm">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
