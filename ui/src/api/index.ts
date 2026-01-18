export * from './types'
export * from './client'
export * from './pipelines'
export * from './saved'
export * from './customSources'

import { apiClient } from './client'
import type { PlatformStats } from './types'

export const statsApi = {
  get: () => apiClient.get<PlatformStats>('/stats'),
}

export const healthApi = {
  check: () => apiClient.get<{ status: string }>('/health'),
}
