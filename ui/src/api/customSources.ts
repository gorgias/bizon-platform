import { apiClient } from './client'
import type {
  CustomSourceCode,
  GitSyncResponse,
  GitSyncStatusResponse,
  TestConnectionRequest,
  TestConnectionResponse,
  UploadSourceResponse,
} from './types'

const API_BASE = '/api'

export const customSourcesApi = {
  getCode: (name: string) =>
    apiClient.get<CustomSourceCode>(`/custom-sources/${name}/code`),

  testConnection: (name: string, request: TestConnectionRequest) =>
    apiClient.post<TestConnectionResponse>(`/custom-sources/${name}/test`, request),

  upload: async (file: File): Promise<UploadSourceResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/custom-sources/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      let detail: string | undefined
      try {
        const data = await response.json()
        detail = data.detail
      } catch {
        // ignore
      }
      throw new Error(detail || response.statusText)
    }

    return response.json()
  },

  delete: (name: string) =>
    apiClient.delete(`/custom-sources/${name}`),

  // Git sync
  getGitSyncStatus: () =>
    apiClient.get<GitSyncStatusResponse>('/custom-sources/git-sync/status'),

  syncFromGit: () =>
    apiClient.post<GitSyncResponse>('/custom-sources/git-sync', {}),
}
