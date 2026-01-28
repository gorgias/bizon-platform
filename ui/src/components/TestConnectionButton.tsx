import { useState } from 'react'
import { Plug, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { Button } from './ui'
import { connectorsApi } from '../api'
import { useToast } from '../contexts/ToastContext'

interface TestConnectionButtonProps {
  type: 'source' | 'destination'
  connectorName: string
  config: Record<string, unknown>
  stream?: string // Required for sources
  className?: string
}

export function TestConnectionButton({
  type,
  connectorName,
  config,
  stream,
  className,
}: TestConnectionButtonProps) {
  const [status, setStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const { addToast } = useToast()

  const handleTest = async () => {
    setStatus('testing')

    try {
      let result

      if (type === 'source') {
        if (!stream) {
          addToast({ type: 'error', message: 'Stream is required for source connection test' })
          setStatus('error')
          return
        }

        result = await connectorsApi.checkSource({
          source_name: connectorName,
          stream_name: stream,
          authentication: config.authentication as Record<string, unknown> | undefined,
        })
      } else {
        result = await connectorsApi.checkDestination({
          destination_name: connectorName,
          config,
        })
      }

      if (result.success) {
        setStatus('success')
        addToast({ type: 'success', message: 'Connection successful' })
        // Reset to idle after 3 seconds
        setTimeout(() => setStatus('idle'), 3000)
      } else {
        setStatus('error')
        addToast({ type: 'error', message: result.message || 'Connection failed' })
        setTimeout(() => setStatus('idle'), 3000)
      }
    } catch (error) {
      setStatus('error')
      const message = error instanceof Error ? error.message : 'Connection test failed'
      addToast({ type: 'error', message })
      setTimeout(() => setStatus('idle'), 3000)
    }
  }

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={handleTest}
      disabled={status === 'testing'}
      className={className}
    >
      {status === 'testing' && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
      {status === 'success' && <CheckCircle className="h-4 w-4 mr-1 text-green-500" />}
      {status === 'error' && <XCircle className="h-4 w-4 mr-1 text-red-500" />}
      {status === 'idle' && <Plug className="h-4 w-4 mr-1" />}
      {status === 'testing' ? 'Testing...' : 'Test'}
    </Button>
  )
}
