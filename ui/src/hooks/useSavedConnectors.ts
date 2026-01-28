import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { savedApi } from '../api'
import { ApiError } from '../api/client'
import { useToast } from '../contexts/ToastContext'
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
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (data: CreateSavedConnectorRequest) => savedApi.createSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
      addToast({ type: 'success', message: 'Source saved successfully' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to save source' })
    },
  })
}

export function useUpdateSavedSource() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSavedConnectorRequest }) =>
      savedApi.updateSource(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.source(id) })
      addToast({ type: 'success', message: 'Source updated successfully' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to update source' })
    },
  })
}

export function useDeleteSavedSource() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (id: string) => savedApi.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sources })
      addToast({ type: 'success', message: 'Source deleted' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to delete source' })
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
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (data: CreateSavedConnectorRequest) => savedApi.createDestination(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
      addToast({ type: 'success', message: 'Destination saved successfully' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to save destination' })
    },
  })
}

export function useUpdateSavedDestination() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSavedConnectorRequest }) =>
      savedApi.updateDestination(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destination(id) })
      addToast({ type: 'success', message: 'Destination updated successfully' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to update destination' })
    },
  })
}

export function useDeleteSavedDestination() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (id: string) => savedApi.deleteDestination(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.destinations })
      addToast({ type: 'success', message: 'Destination deleted' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to delete destination' })
    },
  })
}
