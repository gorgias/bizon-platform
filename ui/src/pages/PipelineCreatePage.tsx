import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Button, Card, CardHeader, CardTitle, CardContent, TagInput } from '../components/ui'
import {
  useCreatePipeline,
  useSourceConnectors,
  useDestinationConnectors,
  useCustomSources,
  useTags,
} from '../hooks'
import type { CreatePipelineRequest } from '../api'

type SourceType = 'builtin' | 'custom'

export function PipelineCreatePage() {
  const navigate = useNavigate()
  const createPipeline = useCreatePipeline()
  const { data: sources } = useSourceConnectors()
  const { data: destinations } = useDestinationConnectors()
  const { data: customSources } = useCustomSources()
  const { data: existingTags } = useTags()

  const [formData, setFormData] = useState({
    name: '',
    sourceType: 'builtin' as SourceType,
    // Built-in source fields
    sourceName: '',
    sourceStream: '',
    // Custom source fields
    customSourceName: '',
    customSourceStream: '',
    customSourceFilePath: '',
    // Common fields
    destinationName: '',
    schedule: '',
    enabled: true,
    tags: [] as string[],
  })

  const selectedSource = sources?.find((s) => s.name === formData.sourceName)
  const selectedCustomSource = customSources?.find((s) => s.name === formData.customSourceName)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const isCustom = formData.sourceType === 'custom'

    const request: CreatePipelineRequest = {
      name: formData.name,
      config: {
        name: formData.name,
        source: isCustom
          ? {
              source_file_path: formData.customSourceFilePath,
              name: formData.customSourceName,
              stream: formData.customSourceStream,
            }
          : {
              name: formData.sourceName,
              stream: formData.sourceStream,
              authentication: {
                type: 'api_key',
                params: { token: 'placeholder' },
              },
            },
        destination: {
          name: formData.destinationName,
          config: {},
        },
      },
      schedule: formData.schedule || undefined,
      enabled: formData.enabled,
      tags: formData.tags.length > 0 ? formData.tags : undefined,
    }

    try {
      await createPipeline.mutateAsync(request)
      navigate('/pipelines')
    } catch (error) {
      console.error('Failed to create pipeline:', error)
    }
  }

  const inputClassName =
    'w-full px-3 py-2 bg-bizon-bg border border-bizon-border rounded-lg text-bizon-text focus:outline-none focus:ring-2 focus:ring-bizon-primary'

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-4">
        <Link to="/pipelines">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-bold text-bizon-text">Create Pipeline</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-bizon-text mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className={inputClassName}
                placeholder="my-pipeline"
                required
              />
            </div>

            {/* Source Type Selection */}
            <div>
              <label className="block text-sm font-medium text-bizon-text mb-2">Source Type</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="sourceType"
                    value="builtin"
                    checked={formData.sourceType === 'builtin'}
                    onChange={() =>
                      setFormData({
                        ...formData,
                        sourceType: 'builtin',
                        customSourceName: '',
                        customSourceStream: '',
                        customSourceFilePath: '',
                      })
                    }
                    className="h-4 w-4 text-bizon-primary border-bizon-border bg-bizon-bg focus:ring-bizon-primary"
                  />
                  <span className="text-sm text-bizon-text">Built-in Source</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="sourceType"
                    value="custom"
                    checked={formData.sourceType === 'custom'}
                    onChange={() =>
                      setFormData({
                        ...formData,
                        sourceType: 'custom',
                        sourceName: '',
                        sourceStream: '',
                      })
                    }
                    className="h-4 w-4 text-bizon-primary border-bizon-border bg-bizon-bg focus:ring-bizon-primary"
                  />
                  <span className="text-sm text-bizon-text">Custom Source</span>
                </label>
              </div>
            </div>

            {/* Built-in Source Fields */}
            {formData.sourceType === 'builtin' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-bizon-text mb-1">Source</label>
                  <select
                    value={formData.sourceName}
                    onChange={(e) =>
                      setFormData({ ...formData, sourceName: e.target.value, sourceStream: '' })
                    }
                    className={inputClassName}
                    required
                  >
                    <option value="">Select a source</option>
                    {sources?.map((source) => (
                      <option key={source.name} value={source.name}>
                        {source.name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedSource && (
                  <div>
                    <label className="block text-sm font-medium text-bizon-text mb-1">Stream</label>
                    <select
                      value={formData.sourceStream}
                      onChange={(e) => setFormData({ ...formData, sourceStream: e.target.value })}
                      className={inputClassName}
                      required
                    >
                      <option value="">Select a stream</option>
                      {selectedSource.streams.map((stream) => (
                        <option key={stream.name} value={stream.name}>
                          {stream.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

            {/* Custom Source Fields */}
            {formData.sourceType === 'custom' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-bizon-text mb-1">
                    Custom Source
                  </label>
                  {customSources && customSources.length > 0 ? (
                    <select
                      value={formData.customSourceName}
                      onChange={(e) => {
                        const selected = customSources.find((s) => s.name === e.target.value)
                        setFormData({
                          ...formData,
                          customSourceName: e.target.value,
                          customSourceFilePath: selected?.file_path || '',
                          customSourceStream: '',
                        })
                      }}
                      className={inputClassName}
                      required
                    >
                      <option value="">Select a custom source</option>
                      {customSources.map((source) => (
                        <option key={source.name} value={source.name}>
                          {source.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <p className="text-sm text-bizon-muted">
                      No custom sources found. Add sources to{' '}
                      <code className="bg-bizon-surface px-1 rounded">custom-sources/</code>{' '}
                      directory.
                    </p>
                  )}
                </div>

                {selectedCustomSource && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-bizon-text mb-1">
                        File Path
                      </label>
                      <input
                        type="text"
                        value={formData.customSourceFilePath}
                        onChange={(e) =>
                          setFormData({ ...formData, customSourceFilePath: e.target.value })
                        }
                        className={`${inputClassName} font-mono text-sm`}
                        placeholder="/custom-sources/my_source/source.py"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-bizon-text mb-1">
                        Stream
                      </label>
                      <select
                        value={formData.customSourceStream}
                        onChange={(e) =>
                          setFormData({ ...formData, customSourceStream: e.target.value })
                        }
                        className={inputClassName}
                        required
                      >
                        <option value="">Select a stream</option>
                        {selectedCustomSource.streams.map((stream) => (
                          <option key={stream} value={stream}>
                            {stream}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-bizon-text mb-1">Destination</label>
              <select
                value={formData.destinationName}
                onChange={(e) => setFormData({ ...formData, destinationName: e.target.value })}
                className={inputClassName}
                required
              >
                <option value="">Select a destination</option>
                {destinations?.map((dest) => (
                  <option key={dest.name} value={dest.name}>
                    {dest.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-bizon-text mb-1">
                Schedule (cron expression)
              </label>
              <input
                type="text"
                value={formData.schedule}
                onChange={(e) => setFormData({ ...formData, schedule: e.target.value })}
                className={`${inputClassName} font-mono`}
                placeholder="0 9 * * * (optional)"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enabled"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                className="h-4 w-4 rounded border-bizon-border bg-bizon-bg text-bizon-primary focus:ring-bizon-primary"
              />
              <label htmlFor="enabled" className="text-sm text-bizon-text">
                Enable pipeline
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-bizon-text mb-1">Tags</label>
              <TagInput
                tags={formData.tags}
                onChange={(tags) => setFormData({ ...formData, tags })}
                suggestions={existingTags || []}
                placeholder="Add tags..."
              />
              <p className="text-xs text-bizon-muted mt-1">
                Press Enter to add a tag. Use tags to group and filter pipelines.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Link to="/pipelines">
                <Button type="button" variant="secondary">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={createPipeline.isPending}>
                {createPipeline.isPending ? 'Creating...' : 'Create Pipeline'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
