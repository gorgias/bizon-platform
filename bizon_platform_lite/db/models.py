"""Database models for bizon-platform-lite.

Simplified schema with 3 tables only:
- Pipeline: Pipeline configurations
- PipelineRun: Pipeline execution runs
- SavedConnector: Reusable connector configurations
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from bizon_platform_lite.db.types import EncryptedJSON


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Pipeline(Base):
    """Pipeline configuration model.

    The config field is encrypted at rest using AES-256.
    Set ENCRYPTION_KEY environment variable to enable encryption.
    """

    __tablename__ = "pipelines"
    __table_args__ = (UniqueConstraint("name", name="uq_pipelines_name"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    config: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    schedule: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True, default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="pipeline", cascade="all, delete"
    )


class PipelineRun(Base):
    """Pipeline execution run model."""

    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pipelines.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, running, success, failed, cancelled
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # manual, schedule
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    output_file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="runs")


class SavedConnector(Base):
    """Saved connector configuration for reuse across pipelines.

    The config field is encrypted at rest using AES-256.
    Set ENCRYPTION_KEY environment variable to enable encryption.
    """

    __tablename__ = "saved_connectors"
    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_saved_connectors_name_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "source" or "destination"
    connector_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "hubspot", "bigquery"
    config: Mapped[dict] = mapped_column(EncryptedJSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
