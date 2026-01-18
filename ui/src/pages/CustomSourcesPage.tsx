import { useState, useMemo } from 'react'
import { Plus, Search, RefreshCw } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { Button, PageLoader, EmptyState } from '../components/ui'
import {
  CustomSourceCard,
  SourceCodeModal,
  TestConnectionModal,
  UploadSourceModal,
} from '../components/custom-sources'
import { useCustomSources, useDeleteCustomSource } from '../hooks'
import type { CustomSource } from '../api'

export function CustomSourcesPage() {
  const queryClient = useQueryClient()
  const { data: sources, isLoading, isFetching } = useCustomSources()
  const deleteSource = useDeleteCustomSource()

  const [searchQuery, setSearchQuery] = useState('')
  const [codeModalSource, setCodeModalSource] = useState<string | null>(null)
  const [testModalSource, setTestModalSource] = useState<CustomSource | null>(null)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)

  const filteredSources = useMemo(() => {
    if (!sources) return []
    if (!searchQuery.trim()) return sources

    const query = searchQuery.toLowerCase()
    return sources.filter(
      (source) =>
        source.name.toLowerCase().includes(query) ||
        source.streams.some((stream) => stream.toLowerCase().includes(query))
    )
  }, [sources, searchQuery])

  const handleDelete = (source: CustomSource) => {
    if (confirm(`Delete custom source "${source.name}"? This cannot be undone.`)) {
      deleteSource.mutate(source.name)
    }
  }

  if (isLoading) {
    return <PageLoader />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-bizon-text">Custom Sources</h1>
          <p className="text-bizon-textSecondary mt-1">
            Manage your custom data source connectors
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['connectors', 'custom-sources'] })}
            disabled={isFetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
            Scan
          </Button>
          <Button onClick={() => setUploadModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Upload
          </Button>
        </div>
      </div>

      {/* Search */}
      {sources && sources.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-bizon-muted" />
          <input
            type="text"
            placeholder="Search sources or streams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-bizon-surface border border-bizon-border rounded-lg text-bizon-text placeholder-bizon-muted focus:outline-none focus:ring-2 focus:ring-bizon-primary/50"
          />
        </div>
      )}

      {/* Grid */}
      {filteredSources.length === 0 ? (
        sources && sources.length > 0 ? (
          <EmptyState
            title="No matching sources"
            description={`No custom sources match "${searchQuery}"`}
          />
        ) : (
          <EmptyState
            title="No custom sources"
            description="Upload a custom source to get started"
            action={
              <Button onClick={() => setUploadModalOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Upload Source
              </Button>
            }
          />
        )
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((source) => (
            <CustomSourceCard
              key={source.name}
              source={source}
              onViewCode={() => setCodeModalSource(source.name)}
              onTest={() => setTestModalSource(source)}
              onDelete={() => handleDelete(source)}
              isDeleting={deleteSource.isPending && deleteSource.variables === source.name}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <SourceCodeModal
        isOpen={!!codeModalSource}
        onClose={() => setCodeModalSource(null)}
        sourceName={codeModalSource || ''}
      />

      <TestConnectionModal
        isOpen={!!testModalSource}
        onClose={() => setTestModalSource(null)}
        source={testModalSource}
      />

      <UploadSourceModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />
    </div>
  )
}
