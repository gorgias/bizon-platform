"""Saved connectors CRUD endpoints - No Auth Version."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bizon_platform_lite.api.schemas import (
    SavedConnectorCreate,
    SavedConnectorResponse,
    SavedConnectorUpdate,
)
from bizon_platform_lite.db.models import SavedConnector
from bizon_platform_lite.db.session import get_session

router = APIRouter(prefix="/saved", tags=["saved-connectors"])


# ============================================================================
# Saved Sources
# ============================================================================


@router.post("/sources", response_model=SavedConnectorResponse, status_code=201)
async def create_saved_source(data: SavedConnectorCreate) -> SavedConnector:
    """Create a saved source configuration."""
    async with get_session() as session:
        connector = SavedConnector(
            name=data.name,
            type="source",
            connector_name=data.connector_name,
            config=data.config,
            description=data.description,
        )
        session.add(connector)
        try:
            await session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"A saved source with name '{data.name}' already exists",
            )
        await session.refresh(connector)
        return connector


@router.get("/sources", response_model=list[SavedConnectorResponse])
async def list_saved_sources(limit: int = 100, offset: int = 0) -> list[SavedConnector]:
    """List all saved source configurations."""
    async with get_session() as session:
        query = (
            select(SavedConnector)
            .where(SavedConnector.type == "source")
            .limit(limit)
            .offset(offset)
            .order_by(SavedConnector.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())


@router.get("/sources/{connector_id}", response_model=SavedConnectorResponse)
async def get_saved_source(connector_id: uuid.UUID) -> SavedConnector:
    """Get a saved source configuration by ID."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "source":
            raise HTTPException(status_code=404, detail="Saved source not found")
        return connector


@router.put("/sources/{connector_id}", response_model=SavedConnectorResponse)
async def update_saved_source(
    connector_id: uuid.UUID, data: SavedConnectorUpdate
) -> SavedConnector:
    """Update a saved source configuration."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "source":
            raise HTTPException(status_code=404, detail="Saved source not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(connector, key, value)

        try:
            await session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"A saved source with name '{data.name}' already exists",
            )
        await session.refresh(connector)
        return connector


@router.delete("/sources/{connector_id}", status_code=204)
async def delete_saved_source(connector_id: uuid.UUID) -> None:
    """Delete a saved source configuration."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "source":
            raise HTTPException(status_code=404, detail="Saved source not found")
        await session.delete(connector)


# ============================================================================
# Saved Destinations
# ============================================================================


@router.post("/destinations", response_model=SavedConnectorResponse, status_code=201)
async def create_saved_destination(data: SavedConnectorCreate) -> SavedConnector:
    """Create a saved destination configuration."""
    async with get_session() as session:
        connector = SavedConnector(
            name=data.name,
            type="destination",
            connector_name=data.connector_name,
            config=data.config,
            description=data.description,
        )
        session.add(connector)
        try:
            await session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"A saved destination with name '{data.name}' already exists",
            )
        await session.refresh(connector)
        return connector


@router.get("/destinations", response_model=list[SavedConnectorResponse])
async def list_saved_destinations(
    limit: int = 100, offset: int = 0
) -> list[SavedConnector]:
    """List all saved destination configurations."""
    async with get_session() as session:
        query = (
            select(SavedConnector)
            .where(SavedConnector.type == "destination")
            .limit(limit)
            .offset(offset)
            .order_by(SavedConnector.created_at.desc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())


@router.get("/destinations/{connector_id}", response_model=SavedConnectorResponse)
async def get_saved_destination(connector_id: uuid.UUID) -> SavedConnector:
    """Get a saved destination configuration by ID."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "destination":
            raise HTTPException(status_code=404, detail="Saved destination not found")
        return connector


@router.put("/destinations/{connector_id}", response_model=SavedConnectorResponse)
async def update_saved_destination(
    connector_id: uuid.UUID, data: SavedConnectorUpdate
) -> SavedConnector:
    """Update a saved destination configuration."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "destination":
            raise HTTPException(status_code=404, detail="Saved destination not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(connector, key, value)

        try:
            await session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=409,
                detail=f"A saved destination with name '{data.name}' already exists",
            )
        await session.refresh(connector)
        return connector


@router.delete("/destinations/{connector_id}", status_code=204)
async def delete_saved_destination(connector_id: uuid.UUID) -> None:
    """Delete a saved destination configuration."""
    async with get_session() as session:
        connector = await session.get(SavedConnector, connector_id)
        if not connector or connector.type != "destination":
            raise HTTPException(status_code=404, detail="Saved destination not found")
        await session.delete(connector)
