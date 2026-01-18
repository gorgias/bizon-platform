"""Pydantic schemas for API requests and responses."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Pipeline schemas
# =============================================================================


class PipelineCreate(BaseModel):
    """Schema for creating a pipeline."""

    name: str
    config: dict[str, Any]
    schedule: Optional[str] = None
    enabled: bool = True
    tags: Optional[list[str]] = None


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""

    name: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    tags: Optional[list[str]] = None


class PipelineResponse(BaseModel):
    """Schema for pipeline response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    config: dict[str, Any]
    schedule: Optional[str]
    enabled: bool
    tags: Optional[list[str]]
    created_at: datetime
    updated_at: Optional[datetime]


class PipelineRunCreate(BaseModel):
    """Schema for triggering a pipeline run."""

    triggered_by: str = "manual"


class PipelineRunResponse(BaseModel):
    """Schema for pipeline run response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    status: str
    triggered_by: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error: Optional[str]
    logs: Optional[str]
    log_file_path: Optional[str]
    output_file: Optional[str]
    output_file_size: Optional[int]
    created_at: datetime


class RunLogsResponse(BaseModel):
    """Schema for run logs response."""

    logs: Optional[str]


# =============================================================================
# Health and Stats schemas
# =============================================================================


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    database: str


class StatsResponse(BaseModel):
    """Schema for platform stats response."""

    total_pipelines: int
    enabled_pipelines: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    pending_runs: int


# =============================================================================
# Connector check schemas
# =============================================================================


class SourceCheckRequest(BaseModel):
    """Request for checking source connectivity."""

    source_name: str
    stream_name: str
    authentication: Optional[dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class DestinationCheckRequest(BaseModel):
    """Request for checking destination connectivity."""

    destination_name: str
    config: dict[str, Any]


class CheckResponse(BaseModel):
    """Response from connectivity check."""

    success: bool
    message: Optional[str] = None


# =============================================================================
# Saved Connector schemas
# =============================================================================


class SavedConnectorCreate(BaseModel):
    """Schema for creating a saved connector."""

    name: str = Field(..., min_length=1, max_length=255)
    connector_name: str = Field(..., min_length=1, max_length=100)
    config: dict[str, Any]
    description: Optional[str] = None


class SavedConnectorUpdate(BaseModel):
    """Schema for updating a saved connector."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[dict[str, Any]] = None
    description: Optional[str] = None


class SavedConnectorResponse(BaseModel):
    """Schema for saved connector response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    connector_name: str
    config: dict[str, Any]
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


# =============================================================================
# Custom Source schemas
# =============================================================================


class CustomSourceCreate(BaseModel):
    """Schema for creating a custom source."""

    name: str = Field(..., min_length=1, max_length=255)
    source_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Snake_case connector name",
    )
    code: str = Field(..., min_length=1, description="Python source code")
    description: Optional[str] = Field(None, max_length=1000)


class CustomSourceUpdate(BaseModel):
    """Schema for updating a custom source."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=1000)


class CustomSourceResponse(BaseModel):
    """Schema for custom source response (list view - no code)."""

    id: uuid.UUID
    name: str
    source_name: str
    streams: list[str]
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class CustomSourceDetailResponse(BaseModel):
    """Schema for custom source detail response (includes code)."""

    id: uuid.UUID
    name: str
    source_name: str
    streams: list[str]
    description: Optional[str]
    code: str
    created_at: datetime
    updated_at: Optional[datetime]


class CustomSourceValidationError(BaseModel):
    """A single validation error."""

    line: int
    column: int
    message: str
    severity: str = "error"


class ConfigFieldSchema(BaseModel):
    """A field in a config class."""

    name: str
    type_hint: str
    default: Optional[str] = None
    required: bool = True


class ExtractedSchemaResponse(BaseModel):
    """Extracted config and auth schema from source code."""

    config_class_name: Optional[str] = None
    config_fields: list[ConfigFieldSchema] = Field(default_factory=list)
    auth_class_name: Optional[str] = None
    auth_type: Optional[str] = None


class CustomSourceValidateRequest(BaseModel):
    """Request for validating custom source code."""

    code: str = Field(..., min_length=1)


class CustomSourceValidateResponse(BaseModel):
    """Response from custom source validation."""

    valid: bool
    errors: list[CustomSourceValidationError] = Field(default_factory=list)
    warnings: list[CustomSourceValidationError] = Field(default_factory=list)
    extracted_source_name: Optional[str] = None
    extracted_streams: list[str] = Field(default_factory=list)
    extracted_schema: Optional[ExtractedSchemaResponse] = None


class CustomSourcePreviewRequest(BaseModel):
    """Request for previewing a custom source."""

    source_id: Optional[uuid.UUID] = Field(None, description="ID of saved source (if previewing saved)")
    code: Optional[str] = Field(None, description="Source code (if previewing unsaved)")
    stream: str = Field(..., description="Stream name to preview")
    authentication: Optional[dict[str, Any]] = Field(None, description="Authentication config for the source")
    max_records: int = Field(default=10, ge=1, le=100, description="Max records to fetch")


class CustomSourcePreviewRecord(BaseModel):
    """A single record from preview."""

    id: str
    data: dict[str, Any]


class CustomSourcePreviewResponse(BaseModel):
    """Response from custom source preview."""

    success: bool
    records: list[CustomSourcePreviewRecord] = Field(default_factory=list)
    total_count: Optional[int] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
