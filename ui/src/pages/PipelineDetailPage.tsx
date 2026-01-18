import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Play, Settings, Clock, FileText } from 'lucide-react'
import { format } from 'date-fns'
import { Button, Card, CardHeader, CardTitle, CardContent, PageLoader, TagChip, PipelineStatusToggle, StatusChip } from '../components/ui'
import { RunLogsModal } from '../components/RunLogsModal'
import { usePipeline, usePipelineRuns, useTriggerRun, useUpdatePipeline } from '../hooks'
import type { PipelineRun } from '../api'

export function PipelineDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: pipeline, isLoading: pipelineLoading } = usePipeline(id!)
  const { data: runs, isLoading: runsLoading } = usePipelineRuns(id!)
  const triggerRun = useTriggerRun()
  const updatePipeline = useUpdatePipeline()
  const [selectedRun, setSelectedRun] = useState<PipelineRun | null>(null)

  if (pipelineLoading || !pipeline) {
    return <PageLoader />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/pipelines">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-bizon-text">{pipeline.name}</h1>
            <PipelineStatusToggle
              enabled={pipeline.enabled}
              onChange={(enabled) => updatePipeline.mutate({ id: id!, data: { enabled } })}
              disabled={updatePipeline.isPending}
            />
          </div>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-bizon-textSecondary">
              <span className="font-mono">{pipeline.config.source.name}</span>
              <span className="mx-2">→</span>
              <span className="font-mono">{pipeline.config.destination.name}</span>
            </span>
            {pipeline.tags && pipeline.tags.length > 0 && (
              <div className="flex items-center gap-1">
                {pipeline.tags.map((tag) => (
                  <TagChip key={tag} tag={tag} size="sm" />
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/pipelines/${id}/edit`}>
            <Button variant="secondary">
              <Settings className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </Link>
          <Button
            onClick={() => triggerRun.mutate({ id: id! })}
            disabled={triggerRun.isPending}
          >
            <Play className="h-4 w-4 mr-2" />
            Run Now
          </Button>
        </div>
      </div>

      {/* Pipeline Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-bizon-muted">Schedule</p>
              <p className="text-bizon-text font-mono">
                {pipeline.schedule || 'Manual only'}
              </p>
            </div>
            <div>
              <p className="text-sm text-bizon-muted">Source</p>
              <p className="text-bizon-text font-mono">
                {pipeline.config.source.name} / {pipeline.config.source.stream}
              </p>
            </div>
            <div>
              <p className="text-sm text-bizon-muted">Destination</p>
              <p className="text-bizon-text font-mono">
                {pipeline.config.destination.name}
              </p>
            </div>
            {pipeline.config.transforms && pipeline.config.transforms.length > 0 && (
              <div>
                <p className="text-sm text-bizon-muted">Transforms</p>
                <p className="text-bizon-text">
                  {pipeline.config.transforms.length} transform(s)
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Timestamps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-bizon-muted">Created</p>
              <p className="text-bizon-text">
                {format(new Date(pipeline.created_at), 'PPpp')}
              </p>
            </div>
            {pipeline.updated_at && (
              <div>
                <p className="text-sm text-bizon-muted">Last Updated</p>
                <p className="text-bizon-text">
                  {format(new Date(pipeline.updated_at), 'PPpp')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Run History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Run History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {runsLoading ? (
            <p className="text-bizon-muted">Loading runs...</p>
          ) : runs?.length === 0 ? (
            <p className="text-bizon-muted">No runs yet</p>
          ) : (
            <div className="space-y-2">
              {runs?.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className="w-full flex items-center justify-between py-3 px-3 -mx-3 border-b border-bizon-border last:border-0 hover:bg-bizon-bg/50 rounded-lg transition-colors text-left"
                >
                  <div className="flex items-center gap-4">
                    <StatusChip status={run.status} />
                    <span className="text-sm text-bizon-muted">
                      {run.triggered_by || 'manual'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-bizon-muted">
                      {run.started_at
                        ? format(new Date(run.started_at), 'MMM d, yyyy HH:mm')
                        : format(new Date(run.created_at), 'MMM d, yyyy HH:mm')}
                      {run.finished_at && run.started_at && (
                        <span className="ml-2">
                          (
                          {Math.round(
                            (new Date(run.finished_at).getTime() -
                              new Date(run.started_at).getTime()) /
                              1000
                          )}
                          s)
                        </span>
                      )}
                    </span>
                    <FileText className="h-4 w-4 text-bizon-muted" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Logs Modal */}
      {selectedRun && (
        <RunLogsModal run={selectedRun} onClose={() => setSelectedRun(null)} />
      )}
    </div>
  )
}
