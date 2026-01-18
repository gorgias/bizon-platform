import { Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { Modal, Button, LoadingSpinner } from '../ui'
import { useCustomSourceCode } from '../../hooks'

interface SourceCodeModalProps {
  isOpen: boolean
  onClose: () => void
  sourceName: string
}

export function SourceCodeModal({ isOpen, onClose, sourceName }: SourceCodeModalProps) {
  const { data, isLoading, error } = useCustomSourceCode(sourceName, isOpen)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (data?.code) {
      await navigator.clipboard.writeText(data.code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const lines = data?.code.split('\n') || []

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Source Code: ${sourceName}`} size="xl">
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="p-4 bg-bizon-danger/10 border border-bizon-danger/30 rounded-lg">
            <p className="text-bizon-danger">
              Failed to load source code: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-bizon-muted font-mono">{data?.file_path}</p>
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-1.5 text-bizon-success" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1.5" />
                    Copy
                  </>
                )}
              </Button>
            </div>

            <div className="relative bg-bizon-bg border border-bizon-border rounded-lg overflow-hidden">
              <div className="overflow-auto max-h-[60vh]">
                <table className="w-full">
                  <tbody>
                    {lines.map((line, index) => (
                      <tr key={index} className="hover:bg-bizon-surface/50">
                        <td className="px-4 py-0.5 text-right text-bizon-muted text-sm font-mono select-none border-r border-bizon-border bg-bizon-surface/30 sticky left-0">
                          {index + 1}
                        </td>
                        <td className="px-4 py-0.5 text-bizon-text text-sm font-mono whitespace-pre">
                          {line || ' '}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </Modal>
  )
}
