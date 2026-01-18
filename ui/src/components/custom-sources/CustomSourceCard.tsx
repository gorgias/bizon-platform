import { useState } from 'react'
import { Code, Play, Trash2 } from 'lucide-react'
import { Button } from '../ui'
import { SourceCodeModal } from './SourceCodeModal'
import type { CustomSource } from '../../api'

interface CustomSourceCardProps {
  source: CustomSource
  onTest: () => void
  onDelete: () => void
  isDeleting?: boolean
}

export function CustomSourceCard({
  source,
  onTest,
  onDelete,
  isDeleting,
}: CustomSourceCardProps) {
  const [showCodeModal, setShowCodeModal] = useState(false)

  return (
    <>
      <div className="p-4 bg-bizon-surface border border-bizon-border rounded-lg hover:border-bizon-primary/30 transition-colors">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-bizon-text truncate">{source.name}</h3>
            <p className="text-sm text-bizon-muted mt-1">
              {source.streams.length} stream{source.streams.length !== 1 ? 's' : ''}
            </p>
            <div className="flex flex-wrap gap-1 mt-2">
              {source.streams.slice(0, 4).map((stream) => (
                <span
                  key={stream}
                  className="px-2 py-0.5 text-xs bg-bizon-bg text-bizon-textSecondary rounded"
                >
                  {stream}
                </span>
              ))}
              {source.streams.length > 4 && (
                <span className="px-2 py-0.5 text-xs bg-bizon-bg text-bizon-muted rounded">
                  +{source.streams.length - 4} more
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-bizon-border">
          <Button variant="ghost" size="sm" onClick={() => setShowCodeModal(true)}>
            <Code className="h-4 w-4 mr-1.5" />
            View Code
          </Button>
          <Button variant="ghost" size="sm" onClick={onTest}>
            <Play className="h-4 w-4 mr-1.5" />
            Test
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            disabled={isDeleting}
            className="ml-auto text-bizon-danger hover:text-bizon-danger"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <SourceCodeModal
        isOpen={showCodeModal}
        onClose={() => setShowCodeModal(false)}
        sourceName={source.name}
      />
    </>
  )
}
