import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface TagChipProps {
  tag: string
  onRemove?: () => void
  onClick?: () => void
  selected?: boolean
  size?: 'sm' | 'md'
}

const colors = [
  'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'bg-purple-500/20 text-purple-400 border-purple-500/30',
  'bg-green-500/20 text-green-400 border-green-500/30',
  'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'bg-pink-500/20 text-pink-400 border-pink-500/30',
  'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'bg-red-500/20 text-red-400 border-red-500/30',
]

function getColorForTag(tag: string): string {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

export function TagChip({ tag, onRemove, onClick, selected, size = 'sm' }: TagChipProps) {
  const colorClass = getColorForTag(tag)

  return (
    <span
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1 border rounded-full font-medium',
        colorClass,
        onClick && 'cursor-pointer hover:opacity-80',
        selected && 'ring-2 ring-white/50',
        {
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
        }
      )}
    >
      {tag}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className="hover:opacity-70 -mr-0.5"
        >
          <X className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
        </button>
      )}
    </span>
  )
}
