import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Play, Eye, EyeOff } from 'lucide-react'
import { Modal, Button, LoadingSpinner } from '../ui'
import { useTestCustomSourceConnection, useCustomSourceConfigSchema } from '../../hooks'
import type { CustomSource, ConfigFieldSchema } from '../../api'

interface TestConnectionModalProps {
  isOpen: boolean
  onClose: () => void
  source: CustomSource | null
}

function ConfigField({
  field,
  value,
  onChange,
}: {
  field: ConfigFieldSchema
  value: unknown
  onChange: (value: unknown) => void
}) {
  const [showSecret, setShowSecret] = useState(false)

  const inputClassName =
    'w-full px-3 py-2 bg-bizon-bg border border-bizon-border rounded-lg text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary/50'

  const convertValue = (rawValue: string): unknown => {
    if (field.type === 'integer') {
      const parsed = parseInt(rawValue, 10)
      return isNaN(parsed) ? '' : parsed
    }
    if (field.type === 'number') {
      const parsed = parseFloat(rawValue)
      return isNaN(parsed) ? '' : parsed
    }
    if (field.type === 'boolean') {
      return rawValue === 'true'
    }
    return rawValue
  }

  if (field.type === 'boolean') {
    return (
      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => onChange(e.target.checked)}
            className="w-4 h-4 rounded border-bizon-border bg-bizon-bg text-bizon-primary focus:ring-bizon-primary/50"
          />
          <span className="text-sm font-medium text-bizon-text">
            {field.name}
            {field.required && <span className="text-bizon-danger ml-1">*</span>}
          </span>
        </label>
        {field.description && (
          <p className="text-xs text-bizon-textSecondary mt-1 ml-6">{field.description}</p>
        )}
      </div>
    )
  }

  return (
    <div>
      <label className="block text-sm font-medium text-bizon-text mb-1">
        {field.name}
        {field.required && <span className="text-bizon-danger ml-1">*</span>}
      </label>
      {field.description && (
        <p className="text-xs text-bizon-textSecondary mb-2">{field.description}</p>
      )}
      <div className="relative">
        <input
          type={field.is_secret && !showSecret ? 'password' : field.type === 'integer' || field.type === 'number' ? 'number' : 'text'}
          value={value !== undefined && value !== null ? String(value) : ''}
          onChange={(e) => onChange(convertValue(e.target.value))}
          placeholder={field.default !== null ? `Default: ${field.default}` : undefined}
          className={`${inputClassName} ${field.is_secret ? 'pr-10' : ''}`}
        />
        {field.is_secret && (
          <button
            type="button"
            onClick={() => setShowSecret(!showSecret)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-bizon-textSecondary hover:text-bizon-text"
          >
            {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  )
}

export function TestConnectionModal({ isOpen, onClose, source }: TestConnectionModalProps) {
  const [selectedStream, setSelectedStream] = useState<string>('')
  const [configValues, setConfigValues] = useState<Record<string, unknown>>({})
  const testConnection = useTestCustomSourceConnection()

  const { data: configSchema, isLoading: isLoadingSchema } = useCustomSourceConfigSchema(
    source?.name || '',
    isOpen && !!source
  )

  // Reset state when source changes
  useEffect(() => {
    if (source) {
      setSelectedStream(source.streams[0] || '')
      setConfigValues({})
      testConnection.reset()
    }
  }, [source?.name])

  const handleConfigChange = (fieldName: string, value: unknown) => {
    setConfigValues((prev) => ({
      ...prev,
      [fieldName]: value,
    }))
  }

  const customFields = configSchema?.fields || []

  // Check if all required fields are filled
  const requiredFieldsMissing = customFields
    .filter((f) => f.required)
    .some((f) => {
      const value = configValues[f.name]
      return value === undefined || value === null || value === ''
    })

  const canTest = selectedStream && !requiredFieldsMissing

  const handleTest = () => {
    if (source && selectedStream) {
      // Build config object, only including non-empty values
      const config: Record<string, unknown> = {}
      for (const field of customFields) {
        const value = configValues[field.name]
        if (value !== undefined && value !== null && value !== '') {
          config[field.name] = value
        }
      }

      testConnection.mutate({
        name: source.name,
        request: {
          stream: selectedStream,
          config: Object.keys(config).length > 0 ? config : undefined,
        },
      })
    }
  }

  const handleClose = () => {
    setSelectedStream('')
    setConfigValues({})
    testConnection.reset()
    onClose()
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

            {isLoadingSchema && (
              <div className="flex items-center justify-center py-4">
                <LoadingSpinner size="sm" className="mr-2" />
                <span className="text-sm text-bizon-textSecondary">Loading configuration...</span>
              </div>
            )}

            {customFields.length > 0 && (
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-bizon-textSecondary uppercase tracking-wide">
                  Configuration
                </h4>
                {customFields.map((field) => (
                  <ConfigField
                    key={field.name}
                    field={field}
                    value={configValues[field.name]}
                    onChange={(value) => handleConfigChange(field.name, value)}
                  />
                ))}
              </div>
            )}

            <Button
              onClick={handleTest}
              disabled={testConnection.isPending || !canTest || isLoadingSchema}
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
