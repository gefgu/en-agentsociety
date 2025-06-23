from datetime import datetime, timedelta
import os
import uuid
from typing import List, cast

from pydantic import BaseModel
from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    Request,
    status,
    File,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...configs import EnvConfig
from ..models import ApiResponseWrapper
from ..models.config import (
    AgentConfig,
    ApiAgentConfig,
    ApiLLMConfig,
    ApiMapConfig,
    ApiWorkflowConfig,
    LLMConfig,
    MapConfig,
    MapTempDownloadLink,
    RealMapConfig,
    WorkflowConfig,
)
from .timezone import ensure_timezone_aware

__all__ = ["router"]

router = APIRouter(tags=["configs"])


# LLM Config API
@router.get("/llm-configs")
async def list_llm_configs(
    request: Request,
) -> ApiResponseWrapper[List[ApiLLMConfig]]:
    """List all LLM configurations"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            select(LLMConfig)
            .where(LLMConfig.tenant_id.in_([tenant_id, ""]))
            .order_by(LLMConfig.created_at.desc())
        )
        results = await db.execute(stmt)
        db_configs = list(results.scalars().all())
        api_configs = [
            ApiLLMConfig(
                tenant_id=config.tenant_id,
                id=config.id,
                name=config.name,
                description=config.description,
                config=config.config,
                created_at=ensure_timezone_aware(config.created_at),
                updated_at=ensure_timezone_aware(config.updated_at),
            )
            for config in db_configs
        ]
        # if config.tenant_id is "", hide the api_key
        for api_config in api_configs:
            if api_config.tenant_id == "":
                for c in api_config.config:
                    c["api_key"] = "********"
        return ApiResponseWrapper(data=api_configs)


@router.get("/llm-configs/{config_id}")
async def get_llm_config_by_id(
    request: Request,
    config_id: uuid.UUID,
) -> ApiResponseWrapper[ApiLLMConfig]:
    """Get LLM configuration by ID"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(LLMConfig).where(
            LLMConfig.tenant_id.in_([tenant_id, ""]),
            LLMConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM configuration not found",
            )
        config = row
        api_config = ApiLLMConfig(
            tenant_id=config.tenant_id,
            id=config.id,
            name=config.name,
            description=config.description,
            config=config.config,
            created_at=ensure_timezone_aware(config.created_at),
            updated_at=ensure_timezone_aware(config.updated_at),
        )
        # if config.tenant_id is "", hide the api_key
        if api_config.tenant_id == "":
            for c in api_config.config:
                c["api_key"] = "********"
        return ApiResponseWrapper(data=api_config)


@router.post("/llm-configs")
async def create_llm_config(
    request: Request,
    config_data: ApiLLMConfig = Body(...),
):
    """Create a new LLM configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = insert(LLMConfig).values(
            tenant_id=tenant_id,
            name=config_data.name,
            description=config_data.description,
            config=config_data.config,
        )
        await db.execute(stmt)
        await db.commit()


@router.put("/llm-configs/{config_id}")
async def update_llm_config(
    request: Request,
    config_id: uuid.UUID,
    config_data: ApiLLMConfig = Body(...),
):
    """Update LLM configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            update(LLMConfig)
            .where(LLMConfig.tenant_id == tenant_id, LLMConfig.id == config_id)
            .values(
                name=config_data.name,
                description=config_data.description,
                config=config_data.config,
            )
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM configuration not found",
            )
        await db.commit()


@router.delete("/llm-configs/{config_id}")
async def delete_llm_config(
    request: Request,
    config_id: uuid.UUID,
):
    """Delete LLM configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = delete(LLMConfig).where(
            LLMConfig.tenant_id == tenant_id, LLMConfig.id == config_id
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM configuration not found",
            )
        await db.commit()


# Map Config API
@router.get("/map-configs")
async def list_map_configs(
    request: Request,
) -> ApiResponseWrapper[List[ApiMapConfig]]:
    """List all map configurations"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            select(MapConfig)
            .where(MapConfig.tenant_id.in_([tenant_id, ""]))
            .order_by(MapConfig.created_at.desc())
        )
        results = await db.execute(stmt)
        db_configs = list(results.scalars().all())
        
        # 处理时区
        for config in db_configs:
            config.created_at = ensure_timezone_aware(config.created_at)
            config.updated_at = ensure_timezone_aware(config.updated_at)
        
        configs = cast(List[ApiMapConfig], db_configs)
        return ApiResponseWrapper(data=configs)


@router.get("/map-configs/{config_id}")
async def get_map_config_by_id(
    request: Request,
    config_id: uuid.UUID,
) -> ApiResponseWrapper[ApiMapConfig]:
    """Get map configuration by ID"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(MapConfig).where(
            MapConfig.tenant_id.in_([tenant_id, ""]),
            MapConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )
        config = row
        # 处理时区
        config.created_at = ensure_timezone_aware(config.created_at)
        config.updated_at = ensure_timezone_aware(config.updated_at)
        return ApiResponseWrapper(data=config)


@router.post("/map-configs/-/upload")
async def upload_map_file(
    request: Request,
    file: UploadFile = File(...),
):
    """Upload a map file to S3"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)
    env: EnvConfig = request.app.state.env
    # Validate file extension
    if not file.filename or not file.filename.endswith(".pb"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only .pb files are allowed"
        )
    # Generate a unique map ID
    map_id = str(uuid.uuid4())
    # Construct S3 path
    path = (
        f"maps/{tenant_id}/{map_id}.pb"
        if tenant_id
        else f"maps/{map_id}.pb"
    )

    # Upload to S3
    fs_client = env.fs_client
    content = await file.read()
    fs_client.upload(content, path)

    return ApiResponseWrapper(data={"file_path": path})


@router.post("/map-configs", status_code=status.HTTP_201_CREATED)
async def create_map_config(
    request: Request,
    config_data: ApiMapConfig = Body(...),
):
    """Create a new map configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.tenant_id = tenant_id
    config_data.validate_config()

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = insert(MapConfig).values(
            tenant_id=tenant_id,
            name=config_data.name,
            description=config_data.description,
            config=config_data.config,
        )
        await db.execute(stmt)
        await db.commit()


@router.put("/map-configs/{config_id}")
async def update_map_config(
    request: Request,
    config_id: uuid.UUID,
    config_data: ApiMapConfig = Body(...),
):
    """Update map configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.tenant_id = tenant_id
    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            update(MapConfig)
            .where(MapConfig.tenant_id == tenant_id, MapConfig.id == config_id)
            .values(
                name=config_data.name,
                description=config_data.description,
                config=config_data.config,
            )
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )
        await db.commit()


@router.delete("/map-configs/{config_id}")
async def delete_map_config(
    request: Request,
    config_id: uuid.UUID,
):
    """Delete map configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = delete(MapConfig).where(
            MapConfig.tenant_id == tenant_id, MapConfig.id == config_id
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )
        await db.commit()


@router.post("/map-configs/{config_id}/export")
async def export_map_config(
    request: Request,
    config_id: uuid.UUID,
):
    """Export map configuration and file"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(MapConfig).where(
            MapConfig.tenant_id.in_([tenant_id, ""]),
            MapConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )
    config = RealMapConfig.model_validate(row.config)

    env: EnvConfig = request.app.state.env
    # Get map file path from config
    map_path = config.file_path

    fs_client = env.fs_client
    # download map file from s3
    file_content = fs_client.download(map_path)

    # Create response with file
    return StreamingResponse(
        content=iter([file_content]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(map_path)}"
        },
    )


class CreateTempDownloadLinkRequest(BaseModel):
    expire_seconds: int = 600


class CreateTempDownloadLinkResponse(BaseModel):
    token: str


@router.post("/map-configs/{config_id}/temp-link")
async def create_temp_download_link(
    request: Request,
    config_id: uuid.UUID,
    body: CreateTempDownloadLinkRequest = Body(...),
):
    """Create a temporary download link for map"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(MapConfig).where(
            MapConfig.tenant_id.in_([tenant_id, ""]),
            MapConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )

        link = MapTempDownloadLink(
            map_config_id=config_id,
            expire_at=datetime.now() + timedelta(seconds=body.expire_seconds),
            token=str(uuid.uuid4().hex),
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)

        return ApiResponseWrapper(data=CreateTempDownloadLinkResponse(token=link.token))


@router.get("/map-configs/{config_id}/temp-link")
async def download_map_by_token(
    request: Request,
    config_id: uuid.UUID,
    token: str = Query(...),
):
    """Download map by token"""
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(MapTempDownloadLink).where(
            MapTempDownloadLink.map_config_id == config_id,
            MapTempDownloadLink.token == token,
        )
        result = await db.execute(stmt)
        link = result.scalar_one_or_none()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Download link not found",
            )
        if link.expire_at < datetime.now(link.expire_at.tzinfo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Download link expired. {link.expire_at} < {datetime.now()}",
            )

        stmt = select(MapConfig).where(MapConfig.id == config_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Map configuration not found",
            )

    config = RealMapConfig.model_validate(row.config)
    map_path = config.file_path
    env: EnvConfig = request.app.state.env
    fs_client = env.fs_client
    file_content = fs_client.download(map_path)

    return StreamingResponse(
        content=iter([file_content]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(map_path)}"
        },
    )


# Agent Config API
@router.get("/agent-configs")
async def list_agent_configs(
    request: Request,
) -> ApiResponseWrapper[List[ApiAgentConfig]]:
    """List all agent configurations"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            select(AgentConfig)
            .where(AgentConfig.tenant_id.in_([tenant_id, ""]))
            .order_by(AgentConfig.created_at.desc())
        )
        results = await db.execute(stmt)
        db_configs = list(results.scalars().all())
        
        # 处理时区
        for config in db_configs:
            config.created_at = ensure_timezone_aware(config.created_at)
            config.updated_at = ensure_timezone_aware(config.updated_at)
        
        configs = cast(List[ApiAgentConfig], db_configs)
        return ApiResponseWrapper(data=configs)


@router.get("/agent-configs/{config_id}")
async def get_agent_config_by_id(
    request: Request,
    config_id: uuid.UUID,
) -> ApiResponseWrapper[ApiAgentConfig]:
    """Get agent configuration by ID"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(AgentConfig).where(
            AgentConfig.tenant_id.in_([tenant_id, ""]),
            AgentConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent configuration not found",
            )
        config = row
        # 处理时区
        config.created_at = ensure_timezone_aware(config.created_at)
        config.updated_at = ensure_timezone_aware(config.updated_at)
        return ApiResponseWrapper(data=config)


@router.post("/agent-configs")
async def create_agent_config(
    request: Request,
    config_data: ApiAgentConfig = Body(...),
):
    """Create a new agent configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = insert(AgentConfig).values(
            tenant_id=tenant_id,
            name=config_data.name,
            description=config_data.description,
            config=config_data.config,
        )
        await db.execute(stmt)
        await db.commit()


@router.put("/agent-configs/{config_id}")
async def update_agent_config(
    request: Request,
    config_id: uuid.UUID,
    config_data: ApiAgentConfig = Body(...),
):
    """Update agent configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            update(AgentConfig)
            .where(AgentConfig.tenant_id == tenant_id, AgentConfig.id == config_id)
            .values(
                name=config_data.name,
                description=config_data.description,
                config=config_data.config,
            )
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent configuration not found",
            )
        await db.commit()


@router.delete("/agent-configs/{config_id}")
async def delete_agent_config(
    request: Request,
    config_id: uuid.UUID,
):
    """Delete agent configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = delete(AgentConfig).where(
            AgentConfig.tenant_id == tenant_id, AgentConfig.id == config_id
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent configuration not found",
            )
        await db.commit()


# Workflow Config API
@router.get("/workflow-configs")
async def list_workflow_configs(
    request: Request,
) -> ApiResponseWrapper[List[ApiWorkflowConfig]]:
    """List all workflow configurations"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            select(WorkflowConfig)
            .where(WorkflowConfig.tenant_id.in_([tenant_id, ""]))
            .order_by(WorkflowConfig.created_at.desc())
        )
        results = await db.execute(stmt)
        db_configs = list(results.scalars().all())
        
        # 处理时区
        for config in db_configs:
            config.created_at = ensure_timezone_aware(config.created_at)
            config.updated_at = ensure_timezone_aware(config.updated_at)
        
        configs = cast(List[ApiWorkflowConfig], db_configs)
        return ApiResponseWrapper(data=configs)


@router.get("/workflow-configs/{config_id}")
async def get_workflow_config_by_id(
    request: Request,
    config_id: uuid.UUID,
) -> ApiResponseWrapper[ApiWorkflowConfig]:
    """Get workflow configuration by ID"""
    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = select(WorkflowConfig).where(
            WorkflowConfig.tenant_id.in_([tenant_id, ""]),
            WorkflowConfig.id == config_id,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow configuration not found",
            )
        config = row
        # 处理时区
        config.created_at = ensure_timezone_aware(config.created_at)
        config.updated_at = ensure_timezone_aware(config.updated_at)
        return ApiResponseWrapper(data=config)


@router.post("/workflow-configs")
async def create_workflow_config(
    request: Request,
    config_data: ApiWorkflowConfig = Body(...),
):
    """Create a new workflow configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = insert(WorkflowConfig).values(
            tenant_id=tenant_id,
            name=config_data.name,
            description=config_data.description,
            config=config_data.config,
        )
        await db.execute(stmt)
        await db.commit()


@router.put("/workflow-configs/{config_id}")
async def update_workflow_config(
    request: Request,
    config_id: uuid.UUID,
    config_data: ApiWorkflowConfig = Body(...),
):
    """Update workflow configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    config_data.validate_config()
    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            update(WorkflowConfig)
            .where(
                WorkflowConfig.tenant_id == tenant_id, WorkflowConfig.id == config_id
            )
            .values(
                name=config_data.name,
                description=config_data.description,
                config=config_data.config,
            )
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow configuration not found",
            )
        await db.commit()


@router.delete("/workflow-configs/{config_id}")
async def delete_workflow_config(
    request: Request,
    config_id: uuid.UUID,
):
    """Delete workflow configuration"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = delete(WorkflowConfig).where(
            WorkflowConfig.tenant_id == tenant_id,
            WorkflowConfig.id == config_id,
        )
        res = await db.execute(stmt)
        if res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow configuration not found",
            )
        await db.commit()
