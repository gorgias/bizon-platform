import { cn } from '../../lib/utils'
import { forwardRef, type ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center font-medium rounded-lg transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-bizon-bg',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          {
            'bg-bizon-primary text-white hover:bg-bizon-primary/90 focus:ring-bizon-primary':
              variant === 'primary',
            'bg-bizon-surface text-bizon-text border border-bizon-border hover:bg-bizon-border focus:ring-bizon-border':
              variant === 'secondary',
            'bg-bizon-danger text-white hover:bg-bizon-danger/90 focus:ring-bizon-danger':
              variant === 'danger',
            'text-bizon-textSecondary hover:text-bizon-text hover:bg-bizon-surface':
              variant === 'ghost',
          },
          {
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-sm': size === 'md',
            'px-6 py-3 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'
