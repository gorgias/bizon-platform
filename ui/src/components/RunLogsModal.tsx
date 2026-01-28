import { useEffect, useRef, useState } from 'react'
import { format } from 'date-fns'
import { X, Download, Square, ArrowDown } from 'lucide-react'
import { Button, StatusChip, LoadingSpinner } from './ui'
import { useRun, useRunLogs, useCancelRun } from '../hooks'
import type { PipelineRun } from '../api'

interface RunLogsModalProps {
  run: PipelineRun
  onClose: () => void
}

export function RunLogsModal({ run: initialRun, onClose }: RunLogsModalProps) {
  const logsEndRef = useRef<HTMLDivElement>(null)
  const logsContainerRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)

  // Poll for run status updates
  const { data: run } = useRun(initialRun.id)
  const currentRun = run || initialRun

  // Poll for logs while run is active
  const { data: logsData, isLoading: logsLoading } = useRunLogs(
    initialRun.id,
    currentRun.status === 'pending' || currentRun.status === 'running'
  )

  const cancelRun = useCancelRun()

  const logs = logsData?.logs || currentRun.logs || ''

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  // Detect manual scroll
  const handleScroll = () => {
    if (!logsContainerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50
    setAutoScroll(isAtBottom)
  }

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    setAutoScroll(true)
  }

  const handleDownload = () => {
    const blob = new Blob([logs], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `run-${initialRun.id.slice(0, 8)}-logs.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleCancel = () => {
    if (confirm('Are you sure you want to cancel this run?')) {
      cancelRun.mutate(initialRun.id)
    }
  }

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  const formatLogLine = (line: string) => {
    // Highlight ERROR lines
    if (line.includes('| ERROR |') || line.includes('ERROR:')) {
      return <span className="text-red-400">{line}</span>
    }
    // Highlight WARNING lines
    if (line.includes('| WARNING |') || line.includes('WARNING:')) {
      return <span className="text-yellow-400">{line}</span>
    }
    // Highlight SUCCESS/INFO lines
    if (line.includes('| SUCCESS |') || line.includes('SUCCESS:')) {
      return <span className="text-green-400">{line}</span>
    }
    return line
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative bg-bizon-surface border border-bizon-border rounded-xl shadow-2xl flex flex-col w-[95vw] h-[90vh] max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-bizon-border">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-bizon-text">Run Logs</h2>
            <StatusChip status={currentRun.status} />
            {(currentRun.status === 'pending' || currentRun.status === 'running') && (
              <LoadingSpinner size="sm" />
            )}
          </div>
          <div className="flex items-center gap-2">
            {(currentRun.status === 'pending' || currentRun.status === 'running') && (
              <Button
                variant="danger"
                size="sm"
                onClick={handleCancel}
                disabled={cancelRun.isPending}
              >
                <Square className="h-3 w-3 mr-1" />
                Cancel
              </Button>
            )}
            {logs && (
              <Button variant="secondary" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-bizon-muted hover:text-bizon-text rounded-lg hover:bg-bizon-bg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Run info bar */}
        <div className="px-6 py-3 border-b border-bizon-border bg-bizon-bg/50 text-sm text-bizon-muted flex items-center gap-6">
          <span>
            <span className="text-bizon-textSecondary">ID:</span>{' '}
            <span className="font-mono">{initialRun.id.slice(0, 8)}</span>
          </span>
          <span>
            <span className="text-bizon-textSecondary">Triggered:</span>{' '}
            {initialRun.triggered_by || 'manual'}
          </span>
          {currentRun.started_at && (
            <span>
              <span className="text-bizon-textSecondary">Started:</span>{' '}
              {format(new Date(currentRun.started_at), 'MMM d, HH:mm:ss')}
            </span>
          )}
          {currentRun.finished_at && currentRun.started_at && (
            <span>
              <span className="text-bizon-textSecondary">Duration:</span>{' '}
              {Math.round(
                (new Date(currentRun.finished_at).getTime() -
                  new Date(currentRun.started_at).getTime()) /
                  1000
              )}
              s
            </span>
          )}
        </div>

        {/* Error banner */}
        {currentRun.error && (
          <div className="px-6 py-3 bg-red-500/10 border-b border-red-500/20">
            <p className="text-red-400 text-sm font-medium">Error: {currentRun.error}</p>
          </div>
        )}

        {/* Logs content */}
        <div
          ref={logsContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-auto bg-bizon-bg font-mono text-sm"
        >
          {logsLoading && !logs ? (
            <div className="flex items-center justify-center h-full">
              <LoadingSpinner />
            </div>
          ) : logs ? (
            <pre className="p-4 whitespace-pre-wrap break-words text-bizon-textSecondary leading-relaxed">
              {logs.split('\n').map((line, i) => (
                <div key={i} className="hover:bg-bizon-surface/50">
                  {formatLogLine(line)}
                </div>
              ))}
              <div ref={logsEndRef} />
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-bizon-muted">
              {currentRun.status === 'pending'
                ? 'Waiting for run to start...'
                : 'No logs available'}
            </div>
          )}
        </div>

        {/* Scroll to bottom button */}
        {!autoScroll && logs && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-20 right-8 p-2 bg-bizon-primary text-white rounded-full shadow-lg hover:bg-bizon-primary/90 transition-colors"
          >
            <ArrowDown className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  )
}
