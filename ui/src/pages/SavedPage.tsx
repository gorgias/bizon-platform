import { Trash2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, Button, PageLoader, EmptyState } from '../components/ui'
import {
  useSavedSources,
  useSavedDestinations,
  useDeleteSavedSource,
  useDeleteSavedDestination,
} from '../hooks'

export function SavedPage() {
  const { data: sources, isLoading: sourcesLoading } = useSavedSources()
  const { data: destinations, isLoading: destinationsLoading } = useSavedDestinations()
  const deleteSource = useDeleteSavedSource()
  const deleteDestination = useDeleteSavedDestination()

  if (sourcesLoading || destinationsLoading) {
    return <PageLoader />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-bizon-text">Saved Connectors</h1>
        <p className="text-bizon-textSecondary mt-1">
          Reusable connector configurations
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Saved Sources */}
        <Card>
          <CardHeader>
            <CardTitle>Sources ({sources?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            {sources?.length === 0 ? (
              <EmptyState
                title="No saved sources"
                description="Save a source configuration to reuse it in pipelines"
              />
            ) : (
              <div className="space-y-3">
                {sources?.map((source) => (
                  <div
                    key={source.id}
                    className="p-3 bg-bizon-bg rounded-lg border border-bizon-border"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-bizon-text">{source.name}</p>
                        <p className="text-sm text-bizon-muted mt-1">
                          {source.connector_name}
                        </p>
                        {source.description && (
                          <p className="text-sm text-bizon-textSecondary mt-1">
                            {source.description}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (confirm('Delete this saved source?')) {
                            deleteSource.mutate(source.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-bizon-danger" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Saved Destinations */}
        <Card>
          <CardHeader>
            <CardTitle>Destinations ({destinations?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            {destinations?.length === 0 ? (
              <EmptyState
                title="No saved destinations"
                description="Save a destination configuration to reuse it in pipelines"
              />
            ) : (
              <div className="space-y-3">
                {destinations?.map((dest) => (
                  <div
                    key={dest.id}
                    className="p-3 bg-bizon-bg rounded-lg border border-bizon-border"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-bizon-text">{dest.name}</p>
                        <p className="text-sm text-bizon-muted mt-1">
                          {dest.connector_name}
                        </p>
                        {dest.description && (
                          <p className="text-sm text-bizon-textSecondary mt-1">
                            {dest.description}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (confirm('Delete this saved destination?')) {
                            deleteDestination.mutate(dest.id)
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-bizon-danger" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
