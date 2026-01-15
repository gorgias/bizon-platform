import { Card, CardHeader, CardTitle, CardContent, PageLoader } from '../components/ui'
import { useSourceConnectors, useDestinationConnectors } from '../hooks'

export function ConnectorsPage() {
  const { data: sources, isLoading: sourcesLoading } = useSourceConnectors()
  const { data: destinations, isLoading: destinationsLoading } = useDestinationConnectors()

  if (sourcesLoading || destinationsLoading) {
    return <PageLoader />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-bizon-text">Connectors</h1>
        <p className="text-bizon-textSecondary mt-1">
          Available source and destination connectors
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sources */}
        <Card>
          <CardHeader>
            <CardTitle>Sources ({sources?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sources?.map((source) => (
                <div
                  key={source.name}
                  className="p-3 bg-bizon-bg rounded-lg border border-bizon-border"
                >
                  <p className="font-medium text-bizon-text">{source.name}</p>
                  <p className="text-sm text-bizon-muted mt-1">
                    {source.streams.length} stream(s): {source.streams.slice(0, 3).map(s => s.name).join(', ')}
                    {source.streams.length > 3 && '...'}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Destinations */}
        <Card>
          <CardHeader>
            <CardTitle>Destinations ({destinations?.length ?? 0})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {destinations?.map((dest) => (
                <div
                  key={dest.name}
                  className="p-3 bg-bizon-bg rounded-lg border border-bizon-border"
                >
                  <p className="font-medium text-bizon-text">{dest.name}</p>
                  {dest.description && (
                    <p className="text-sm text-bizon-muted mt-1">{dest.description}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
