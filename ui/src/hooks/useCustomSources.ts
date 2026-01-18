import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { customSourcesApi } from '../api'
import type { TestConnectionRequest } from '../api'

const QUERY_KEYS = {
  list: ['connectors', 'custom-sources'] as const,
  code: (name: string) => ['custom-sources', name, 'code'] as const,
  gitSyncStatus: ['custom-sources', 'git-sync-status'] as const,
}

export function useCustomSourceCode(name: string, enabled = true) {
  return useQuery({
    queryKey: QUERY_KEYS.code(name),
    queryFn: () => customSourcesApi.getCode(name),
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

  return useMutation({
    mutationFn: (file: File) => customSourcesApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
    },
  })
}

export function useDeleteCustomSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (name: string) => customSourcesApi.delete(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
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

  return useMutation({
    mutationFn: () => customSourcesApi.syncFromGit(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list })
    },
  })
}
