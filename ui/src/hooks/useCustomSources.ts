import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { customSourcesApi } from '../api'
import { ApiError } from '../api/client'
import { useToast } from '../contexts/ToastContext'
import type { TestConnectionRequest } from '../api'

const QUERY_KEYS = {
  list: ['connectors', 'custom-sources'] as const,
  code: (name: string) => ['custom-sources', name, 'code'] as const,
  configSchema: (name: string) => ['custom-sources', name, 'config-schema'] as const,
  gitSyncStatus: ['custom-sources', 'git-sync-status'] as const,
}

export function useCustomSourceCode(name: string, enabled = true) {
  return useQuery({
    queryKey: QUERY_KEYS.code(name),
    queryFn: () => customSourcesApi.getCode(name),
    enabled: enabled && !!name,
  })
}

export function useCustomSourceConfigSchema(name: string, enabled = true) {
  return useQuery({
    queryKey: QUERY_KEYS.configSchema(name),
    queryFn: () => customSourcesApi.getConfigSchema(name),
    enabled: enabled && !!name,
  })
}

export function useTestCustomSourceConnection() {
  return useMutation({
    mutationFn: ({ name, request }: { name: string; request: TestConnectionRequest }) =>
      customSourcesApi.testConnection(name, request),
  })
}

export function useUploadCustomSource() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (file: File) => customSourcesApi.upload(file),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
      addToast({ type: 'success', message: `Custom source '${result.name}' uploaded successfully` })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to upload source' })
    },
  })
}

export function useDeleteCustomSource() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: (name: string) => customSourcesApi.delete(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
      addToast({ type: 'success', message: 'Custom source deleted' })
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Failed to delete source' })
    },
  })
}

export function useGitSyncStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.gitSyncStatus,
    queryFn: () => customSourcesApi.getGitSyncStatus(),
  })
}

export function useSyncFromGit() {
  const queryClient = useQueryClient()
  const { addToast } = useToast()

  return useMutation({
    mutationFn: () => customSourcesApi.syncFromGit(),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
      if (result.success) {
        addToast({
          type: 'success',
          message: result.files_updated > 0
            ? `Synced ${result.files_updated} file${result.files_updated > 1 ? 's' : ''} from git`
            : 'Already up to date',
        })
      } else {
        addToast({ type: 'error', message: result.message || 'Git sync failed' })
      }
    },
    onError: (error: ApiError) => {
      addToast({ type: 'error', message: error.detail || error.message || 'Git sync failed' })
    },
  })
}
