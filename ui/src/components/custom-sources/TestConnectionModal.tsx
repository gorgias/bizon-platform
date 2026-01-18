import { useState } from 'react'
import { CheckCircle, XCircle, Play } from 'lucide-react'
import { Modal, Button, LoadingSpinner } from '../ui'
import { useTestCustomSourceConnection } from '../../hooks'
import type { CustomSource } from '../../api'

interface TestConnectionModalProps {
  isOpen: boolean
  onClose: () => void
  source: CustomSource | null
}

export function TestConnectionModal({ isOpen, onClose, source }: TestConnectionModalProps) {
  const [selectedStream, setSelectedStream] = useState<string>('')
  const testConnection = useTestCustomSourceConnection()

  const handleTest = () => {
    if (source && selectedStream) {
      testConnection.mutate({
        name: source.name,
        request: { stream: selectedStream },
      })
    }
  }

  const handleClose = () => {
    setSelectedStream('')
    testConnection.reset()
    onClose()
  }

  // Set default stream when source changes
  if (source && !selectedStream && source.streams.length > 0) {
    setSelectedStream(source.streams[0])
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={`Test Connection: ${source?.name || ''}`} size="md">
      <div className="p-6 space-y-4">
        {source && (
          <>
            <div>
              <label className="block text-sm font-medium text-bizon-text mb-2">
                Select Stream
              </label>
              <select
                value={selectedStream}
                onChange={(e) => setSelectedStream(e.target.value)}
                className="w-full px-3 py-2 bg-bizon-bg border border-bizon-border rounded-lg text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary/50"
              >
                {source.streams.map((stream) => (
                  <option key={stream} value={stream}>
                    {stream}
                  </option>
                ))}
              </select>
            </div>

            <Button
              onClick={handleTest}
              disabled={testConnection.isPending || !selectedStream}
              className="w-full"
            >
              {testConnection.isPending ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Test Connection
                </>
              )}
            </Button>

            {testConnection.data && (
              <div
                className={`p-4 rounded-lg flex items-start gap-3 ${
                  testConnection.data.success
                    ? 'bg-bizon-success/10 border border-bizon-success/30'
                    : 'bg-bizon-danger/10 border border-bizon-danger/30'
                }`}
              >
                {testConnection.data.success ? (
                  <CheckCircle className="h-5 w-5 text-bizon-success flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 text-bizon-danger flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <p
                    className={`font-medium ${
                      testConnection.data.success ? 'text-bizon-success' : 'text-bizon-danger'
                    }`}
                  >
                    {testConnection.data.success ? 'Connection Successful' : 'Connection Failed'}
                  </p>
                  <p className="text-sm text-bizon-textSecondary mt-1">
                    {testConnection.data.message}
                  </p>
                </div>
              </div>
            )}

            {testConnection.error && (
              <div className="p-4 rounded-lg bg-bizon-danger/10 border border-bizon-danger/30">
                <div className="flex items-start gap-3">
                  <XCircle className="h-5 w-5 text-bizon-danger flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-bizon-danger">Error</p>
                    <p className="text-sm text-bizon-textSecondary mt-1">
                      {testConnection.error instanceof Error
                        ? testConnection.error.message
                        : 'An error occurred'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}
