import { apiClient } from './client'
import type {
  Pipeline,
  PipelineRun,
  CreatePipelineRequest,
  UpdatePipelineRequest,
  TriggerRunRequest,
  SourceConnector,
  DestinationConnector,
  CustomSource,
} from './types'

export const pipelinesApi = {
  // Pipelines
  list: (params?: { limit?: number; offset?: number; enabled?: boolean; tags?: string[] }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.offset) searchParams.set('offset', String(params.offset))
    if (params?.enabled !== undefined) searchParams.set('enabled', String(params.enabled))
    if (params?.tags?.length) searchParams.set('tags', params.tags.join(','))
    const query = searchParams.toString()
    return apiClient.get<Pipeline[]>(`/pipelines${query ? `?${query}` : ''}`)
  },

  listTags: () => apiClient.get<string[]>('/pipelines/tags'),

  get: (id: string) => apiClient.get<Pipeline>(`/pipelines/${id}`),

  create: (data: CreatePipelineRequest) =>
    apiClient.post<Pipeline>('/pipelines', data),

  update: (id: string, data: UpdatePipelineRequest) =>
    apiClient.put<Pipeline>(`/pipelines/${id}`, data),

  delete: (id: string) => apiClient.delete(`/pipelines/${id}`),

  duplicate: (id: string) => apiClient.post<Pipeline>(`/pipelines/${id}/duplicate`),

  syncStreams: (id: string) => apiClient.post<Pipeline[]>(`/pipelines/${id}/sync-streams`),

  // Runs
  triggerRun: (id: string, data?: TriggerRunRequest) =>
    apiClient.post<PipelineRun>(`/pipelines/${id}/run`, data || { triggered_by: 'manual' }),

  listRuns: (pipelineId: string, params?: { limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.offset) searchParams.set('offset', String(params.offset))
    const query = searchParams.toString()
    return apiClient.get<PipelineRun[]>(`/pipelines/${pipelineId}/runs${query ? `?${query}` : ''}`)
  },

  getRun: (runId: string) => apiClient.get<PipelineRun>(`/pipelines/runs/${runId}`),

  getRunLogs: (runId: string) => apiClient.get<{ logs: string }>(`/pipelines/runs/${runId}/logs`),

  cancelRun: (runId: string) => apiClient.post(`/pipelines/runs/${runId}/cancel`),

  // Connectors
  listSources: () => apiClient.get<SourceConnector[]>('/connectors/sources'),

  listDestinations: () => apiClient.get<DestinationConnector[]>('/connectors/destinations'),

  listCustomSources: () => apiClient.get<CustomSource[]>('/connectors/custom-sources'),
}
