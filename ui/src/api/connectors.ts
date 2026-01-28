import { apiClient } from './client'

export interface SourceCheckRequest {
  source_name: string
  stream_name: string
  authentication?: Record<string, unknown>
}

export interface DestinationCheckRequest {
  destination_name: string
  config: Record<string, unknown>
}

export interface CheckResponse {
  success: boolean
  message: string | null
}

export const connectorsApi = {
  checkSource: (request: SourceCheckRequest) =>
    apiClient.post<CheckResponse>('/connectors/sources/check', request),

  checkDestination: (request: DestinationCheckRequest) =>
    apiClient.post<CheckResponse>('/connectors/destinations/check', request),
}
