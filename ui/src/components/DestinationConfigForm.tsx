interface FieldSchema {
  name: string
  label: string
  type: 'text' | 'select' | 'number' | 'boolean'
  options?: string[]
  required?: boolean
  default?: string | number | boolean
  placeholder?: string
  description?: string
}

interface DestinationSchema {
  fields: FieldSchema[]
}

const DESTINATION_SCHEMAS: Record<string, DestinationSchema> = {
  bigquery: {
    fields: [
      {
        name: 'project_id',
        label: 'Project ID',
        type: 'text',
        required: true,
        placeholder: 'my-gcp-project',
        description: 'Google Cloud project ID',
      },
      {
        name: 'dataset',
        label: 'Dataset',
        type: 'text',
        required: true,
        placeholder: 'my_dataset',
        description: 'BigQuery dataset name',
      },
      {
        name: 'location',
        label: 'Location',
        type: 'text',
        default: 'US',
        placeholder: 'US',
        description: 'Dataset location (e.g., US, EU)',
      },
    ],
  },
  bigquery_streaming: {
    fields: [
      {
        name: 'project_id',
        label: 'Project ID',
        type: 'text',
        required: true,
        placeholder: 'my-gcp-project',
        description: 'Google Cloud project ID',
      },
      {
        name: 'dataset',
        label: 'Dataset',
        type: 'text',
        required: true,
        placeholder: 'my_dataset',
        description: 'BigQuery dataset name',
      },
    ],
  },
  bigquery_streaming_v2: {
    fields: [
      {
        name: 'project_id',
        label: 'Project ID',
        type: 'text',
        required: true,
        placeholder: 'my-gcp-project',
        description: 'Google Cloud project ID',
      },
      {
        name: 'dataset',
        label: 'Dataset',
        type: 'text',
        required: true,
        placeholder: 'my_dataset',
        description: 'BigQuery dataset name',
      },
    ],
  },
  file: {
    fields: [
      {
        name: 'format',
        label: 'Format',
        type: 'select',
        options: ['json', 'csv', 'parquet', 'jsonl'],
        default: 'json',
        description: 'Output file format',
      },
    ],
  },
  logger: {
    fields: [], // No config needed
  },
}

interface DestinationConfigFormProps {
  destinationName: string
  config: Record<string, unknown>
  onChange: (config: Record<string, unknown>) => void
}

export function DestinationConfigForm({
  destinationName,
  config,
  onChange,
}: DestinationConfigFormProps) {
  const schema = DESTINATION_SCHEMAS[destinationName]

  if (!schema || schema.fields.length === 0) {
    return (
      <p className="text-sm text-bizon-muted">
        No additional configuration required for this destination.
      </p>
    )
  }

  const inputClassName =
    'w-full px-3 py-2 bg-bizon-bg border border-bizon-border rounded-lg text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary'

  const handleFieldChange = (fieldName: string, value: unknown) => {
    onChange({ ...config, [fieldName]: value })
  }

  return (
    <div className="space-y-4">
      {schema.fields.map((field) => (
        <div key={field.name}>
          <label className="block text-sm font-medium text-bizon-text mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {field.type === 'select' && field.options ? (
            <select
              value={(config[field.name] as string) || String(field.default ?? '')}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className={inputClassName}
              required={field.required}
            >
              {field.options.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          ) : field.type === 'boolean' ? (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={(config[field.name] as boolean) ?? field.default ?? false}
                onChange={(e) => handleFieldChange(field.name, e.target.checked)}
                className="h-4 w-4 rounded border-bizon-border bg-bizon-bg text-bizon-primary focus:ring-bizon-primary"
              />
              <span className="text-sm text-bizon-textSecondary">
                {field.description || 'Enable'}
              </span>
            </label>
          ) : field.type === 'number' ? (
            <input
              type="number"
              value={(config[field.name] as number) ?? field.default ?? ''}
              onChange={(e) =>
                handleFieldChange(
                  field.name,
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              placeholder={field.placeholder}
              className={inputClassName}
              required={field.required}
            />
          ) : (
            <input
              type="text"
              value={(config[field.name] as string) || ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              placeholder={field.placeholder || String(field.default || '')}
              className={inputClassName}
              required={field.required}
            />
          )}
          {field.description && field.type !== 'boolean' && (
            <p className="text-xs text-bizon-muted mt-1">{field.description}</p>
          )}
        </div>
      ))}
    </div>
  )
}

// Helper to check if destination config is valid
export function isDestinationConfigValid(
  destinationName: string,
  config: Record<string, unknown>
): boolean {
  const schema = DESTINATION_SCHEMAS[destinationName]
  if (!schema) return true

  for (const field of schema.fields) {
    if (field.required) {
      const value = config[field.name]
      if (value === undefined || value === null || value === '') {
        return false
      }
    }
  }
  return true
}
