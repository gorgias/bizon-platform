import { apiClient } from './client'
import type {
  SavedConnector,
  CreateSavedConnectorRequest,
  UpdateSavedConnectorRequest,
} from './types'

export const savedApi = {
  // Sources
  listSources: (params?: { limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.offset) searchParams.set('offset', String(params.offset))
    const query = searchParams.toString()
    return apiClient.get<SavedConnector[]>(`/saved/sources${query ? `?${query}` : ''}`)
  },

  getSource: (id: string) => apiClient.get<SavedConnector>(`/saved/sources/${id}`),

  createSource: (data: CreateSavedConnectorRequest) =>
    apiClient.post<SavedConnector>('/saved/sources', data),

  updateSource: (id: string, data: UpdateSavedConnectorRequest) =>
    apiClient.put<SavedConnector>(`/saved/sources/${id}`, data),

  deleteSource: (id: string) => apiClient.delete(`/saved/sources/${id}`),

  // Destinations
  listDestinations: (params?: { limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.offset) searchParams.set('offset', String(params.offset))
    const query = searchParams.toString()
    return apiClient.get<SavedConnector[]>(`/saved/destinations${query ? `?${query}` : ''}`)
  },

  getDestination: (id: string) => apiClient.get<SavedConnector>(`/saved/destinations/${id}`),

  createDestination: (data: CreateSavedConnectorRequest) =>
    apiClient.post<SavedConnector>('/saved/destinations', data),

  updateDestination: (id: string, data: UpdateSavedConnectorRequest) =>
    apiClient.put<SavedConnector>(`/saved/destinations/${id}`, data),

  deleteDestination: (id: string) => apiClient.delete(`/saved/destinations/${id}`),
}
