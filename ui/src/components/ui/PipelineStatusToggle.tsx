import { cn } from '../../lib/utils'

interface PipelineStatusToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  disabled?: boolean
  className?: string
}

export function PipelineStatusToggle({
  enabled,
  onChange,
  disabled,
  className,
}: PipelineStatusToggleProps) {
  return (
    <button
      type="button"
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 cursor-pointer',
        'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-bizon-bg',
        enabled
          ? 'bg-bizon-success/15 text-bizon-success hover:bg-bizon-success/25 focus:ring-bizon-success/50'
          : 'bg-bizon-muted/15 text-bizon-muted hover:bg-bizon-muted/25 focus:ring-bizon-muted/50',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {/* Status dot */}
      <span
        className={cn(
          'w-2 h-2 rounded-full',
          enabled ? 'bg-bizon-success' : 'bg-bizon-muted'
        )}
      />
      {enabled ? 'Active' : 'Paused'}
    </button>
  )
}
