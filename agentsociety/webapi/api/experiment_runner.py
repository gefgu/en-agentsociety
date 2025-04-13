import asyncio
import base64
import json
import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ...cli.docker_runner import run_experiment_in_container
from ..models import ApiResponseWrapper

__all__ = ["router"]

router = APIRouter(tags=["experiment_runner"])
logger = logging.getLogger(__name__)


class ExperimentResponse(BaseModel):
    """Experiment response model"""

    id: str
    name: str
    status: str


@router.post("/run-experiments", status_code=status.HTTP_200_OK)
async def run_experiment(
    request: Request, config: Dict[str, Any]
) -> ApiResponseWrapper[ExperimentResponse]:
    """Start a new experiment"""
    try:
        if request.app.state.read_only:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Server is in read-only mode",
            )
        tenant_id = await request.app.state.get_tenant_id(request)
        if hasattr(request.app.state.env, "model_dump"):  # Pydantic v2
            config["env"] = request.app.state.env.model_dump()
        elif hasattr(request.app.state.env, "dict"):  # Pydantic v1
            config["env"] = request.app.state.env.dict()
        else:
            config["env"] = request.app.state.env.__dict__

        logger.debug(f"Received experiment config: {json.dumps(config, indent=2)}")

        # Generate unique experiment ID
        experiment_id = str(uuid.uuid4())

        # Convert config to base64
        config_base64 = base64.b64encode(json.dumps(config).encode()).decode()

        # Start experiment container
        try:
            # Create an async task and get its result
            task = asyncio.create_task(
                run_experiment_in_container(
                    config_base64=config_base64,
                )
            )

            # Set up a callback function to handle task completion
            def container_started(future):
                try:
                    container_id = future.result()
                    logger.info(f"Container started with ID: {container_id}")
                except Exception as e:
                    logger.error(f"Error starting container: {e}")

            # Add callback
            task.add_done_callback(container_started)

            logger.info("Successfully created experiment container task")
        except Exception as e:
            logger.error(f"Error in run_experiment_in_container: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start experiment: {str(e)}",
            )

        return ApiResponseWrapper(
            data=ExperimentResponse(
                id=experiment_id,
                name=config.get("exp", {}).get("name", "Default Experiment"),
                status="running",
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error in run_experiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start experiment: {str(e)}",
        )
