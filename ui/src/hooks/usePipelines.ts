import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pipelinesApi } from '../api'
import type { CreatePipelineRequest, UpdatePipelineRequest, TriggerRunRequest } from '../api'

const QUERY_KEYS = {
  pipelines: ['pipelines'] as const,
  pipeline: (id: string) => ['pipelines', id] as const,
  runs: (pipelineId: string) => ['pipelines', pipelineId, 'runs'] as const,
  run: (runId: string) => ['runs', runId] as const,
  sources: ['connectors', 'sources'] as const,
  destinations: ['connectors', 'destinations'] as const,
  customSources: ['connectors', 'custom-sources'] as const,
  tags: ['pipelines', 'tags'] as const,
}

export function usePipelines(params?: { limit?: number; offset?: number; enabled?: boolean; tags?: string[] }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.pipelines, params],
    queryFn: () => pipelinesApi.list(params),
  })
}

export function useTags() {
  return useQuery({
    queryKey: QUERY_KEYS.tags,
    queryFn: () => pipelinesApi.listTags(),
  })
}

export function usePipeline(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.pipeline(id),
    queryFn: () => pipelinesApi.get(id),
    enabled: !!id,
  })
}

export function useCreatePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePipelineRequest) => pipelinesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipelines })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.tags })
    },
  })
}

export function useUpdatePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdatePipelineRequest }) =>
      pipelinesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipelines })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipeline(id) })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.tags })
    },
  })
}

export function useDeletePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => pipelinesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipelines })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.tags })
    },
  })
}

export function useDuplicatePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => pipelinesApi.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipelines })
    },
  })
}

export function useSyncOtherStreams() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => pipelinesApi.syncStreams(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.pipelines })
    },
  })
}

export function useTriggerRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: TriggerRunRequest }) =>
      pipelinesApi.triggerRun(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.runs(id) })
    },
  })
}

export function usePipelineRuns(pipelineId: string, params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.runs(pipelineId), params],
    queryFn: () => pipelinesApi.listRuns(pipelineId, params),
    enabled: !!pipelineId,
    refetchInterval: 5000, // Poll every 5 seconds
  })
}

export function useRun(runId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.run(runId),
    queryFn: () => pipelinesApi.getRun(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const run = query.state.data
      if (run && (run.status === 'pending' || run.status === 'running')) {
        return 2000 // Poll every 2 seconds while running
      }
      return false
    },
  })
}

export function useSourceConnectors() {
  return useQuery({
    queryKey: QUERY_KEYS.sources,
    queryFn: () => pipelinesApi.listSources(),
  })
}

export function useDestinationConnectors() {
  return useQuery({
    queryKey: QUERY_KEYS.destinations,
    queryFn: () => pipelinesApi.listDestinations(),
  })
}

export function useCustomSources() {
  return useQuery({
    queryKey: QUERY_KEYS.customSources,
    queryFn: () => pipelinesApi.listCustomSources(),
  })
}

export function useRunLogs(runId: string, isActive: boolean) {
  return useQuery({
    queryKey: [...QUERY_KEYS.run(runId), 'logs'],
    queryFn: () => pipelinesApi.getRunLogs(runId),
    enabled: !!runId,
    refetchInterval: isActive ? 1000 : false, // Poll every 1 second while active
  })
}

export function useCancelRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (runId: string) => pipelinesApi.cancelRun(runId),
    onSuccess: (_, runId) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.run(runId) })
    },
  })
}
