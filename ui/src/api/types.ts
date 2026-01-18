// Pipeline types
export interface Pipeline {
  id: string
  name: string
  config: PipelineConfig
  schedule: string | null
  enabled: boolean
  tags: string[] | null
  created_at: string
  updated_at: string | null
}

export interface PipelineConfig {
  name: string
  source: SourceConfig
  destination: DestinationConfig
  transforms?: Transform[]
}

export interface SourceConfig {
  name: string
  stream: string
  source_file_path?: string
  authentication?: {
    type: string
    params: Record<string, unknown>
  }
}

export interface DestinationConfig {
  name: string
  config: Record<string, unknown>
}

export interface Transform {
  label: string
  python: string
}

export interface PipelineRun {
  id: string
  pipeline_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  triggered_by: string | null
  started_at: string | null
  finished_at: string | null
  error: string | null
  logs: string | null
  output_file: string | null
  output_file_size: number | null
  created_at: string
}

// Saved connector types
export interface SavedConnector {
  id: string
  name: string
  type: 'source' | 'destination'
  connector_name: string
  config: Record<string, unknown>
  description: string | null
  created_at: string
  updated_at: string | null
}

// Connector discovery types
export interface StreamInfo {
  name: string
  supports_incremental: boolean
}

export interface SourceConnector {
  name: string
  streams: StreamInfo[]
  description?: string
}

export interface DestinationConnector {
  name: string
  description?: string
}

export interface CustomSource {
  name: string
  file_path: string
  streams: string[]
}

// Stats types
export interface PlatformStats {
  total_pipelines: number
  enabled_pipelines: number
  total_runs: number
  successful_runs: number
  failed_runs: number
  pending_runs: number
}

// Request/Response types
export interface CreatePipelineRequest {
  name: string
  config: PipelineConfig
  schedule?: string
  enabled?: boolean
  tags?: string[]
}

export interface UpdatePipelineRequest {
  name?: string
  config?: PipelineConfig
  schedule?: string | null
  enabled?: boolean
  tags?: string[]
}

export interface TriggerRunRequest {
  triggered_by?: string
}

export interface CreateSavedConnectorRequest {
  name: string
  connector_name: string
  config: Record<string, unknown>
  description?: string
}

export interface UpdateSavedConnectorRequest {
  name?: string
  config?: Record<string, unknown>
  description?: string
}

// Custom source types
export interface CustomSourceCode {
  name: string
  code: string
  file_path: string
}

export interface TestConnectionRequest {
  stream: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
}

export interface UploadSourceResponse {
  name: string
  file_path: string
  streams: string[]
  message: string
}

export interface DeleteSourceResponse {
  message: string
}
