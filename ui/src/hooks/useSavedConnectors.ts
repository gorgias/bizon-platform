import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { savedApi } from '../api'
import type { CreateSavedConnectorRequest, UpdateSavedConnectorRequest } from '../api'

const QUERY_KEYS = {
  sources: ['saved', 'sources'] as const,
  source: (id: string) => ['saved', 'sources', id] as const,
  destinations: ['saved', 'destinations'] as const,
  destination: (id: string) => ['saved', 'destinations', id] as const,
}

// Sources
export function useSavedSources(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.sources, params],
    queryFn: () => savedApi.listSources(params),
  })
}

export function useSavedSource(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.source(id),
    queryFn: () => savedApi.getSource(id),
    enabled: !!id,
  })
}

export function useCreateSavedSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSavedConnectorRequest) => savedApi.createSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
    },
  })
}

export function useUpdateSavedSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSavedConnectorRequest }) =>
      savedApi.updateSource(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(id) })
    },
  })
}

export function useDeleteSavedSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedApi.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
    },
  })
}

// Destinations
export function useSavedDestinations(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...QUERY_KEYS.destinations, params],
    queryFn: () => savedApi.listDestinations(params),
  })
}

export function useSavedDestination(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.destination(id),
    queryFn: () => savedApi.getDestination(id),
    enabled: !!id,
  })
}

export function useCreateSavedDestination() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSavedConnectorRequest) => savedApi.createDestination(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
    },
  })
}

export function useUpdateSavedDestination() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSavedConnectorRequest }) =>
      savedApi.updateDestination(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destination(id) })
    },
  })
}

export function useDeleteSavedDestination() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => savedApi.deleteDestination(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
    },
  })
}
