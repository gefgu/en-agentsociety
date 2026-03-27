from typing import Annotated, Any, Dict
from fastapi import APIRouter, HTTPException, status, Query, Depends
from ..clickhouse import get_clickhouse_client
from ..models import ApiResponseWrapper

__all__ = ["router"]

router = APIRouter(tags=["schedule"])

# Mapping from raw block names to display categories
BLOCK_MAPPING = {
    "MonthEconomyPlanBlock": "EconomyBlock",
    "NeedsBlock": "NeedsBlock",
    "PlanBlock": "PlanBlock",
    "BlockDispatcher": "Dispatcher",
    "SleepBlock": "OtherBlock",
    "SocietyAgent": "CognitionBlock",
    "OtherNoneBlock": "OtherBlock",
    "CognitionBlock": "CognitionBlock",
    "SocialNoneBlock": "SocialBlock",
    "WorkBlock": "EconomyBlock",
    "MoveBlock": "MobilityBlock",
    "PlaceSelectionBlock": "MobilityBlock",
}


@router.get("/experiments/{exp_id}/schedule-metadata")
async def get_schedule_metadata(
    exp_id: str,
    client: Annotated[Any, Depends(get_clickhouse_client)],
) -> ApiResponseWrapper[Dict[str, Any]]:
    """
    Get metadata for the schedule view: available agent IDs and total days.
    """
    try:
        # 1. Get unique agent IDs using parameterized query
        agent_query = """
        SELECT DISTINCT agent_id
        FROM prompt_responses
        WHERE exp_id = %(exp_id)s
        ORDER BY agent_id
        """
        # Pass variables as a dictionary to the client - FIXED: params -> parameters
        agent_df = client.query_df(agent_query, parameters={"exp_id": exp_id})
        agent_ids = agent_df["agent_id"].tolist()

        # 2. Get max simulation step using parameterized query
        days_query = """
        SELECT MAX(simulation_step) as max_step
        FROM prompt_responses
        WHERE exp_id = %(exp_id)s
        """
        # FIXED: params -> parameters
        days_df = client.query_df(days_query, parameters={"exp_id": exp_id})
        
        # Safe extraction of max_step
        max_step = 0
        if not days_df.empty and days_df["max_step"].iloc[0] is not None:
            max_step = days_df["max_step"].iloc[0]
            
        total_days = (max_step // 144) + 1

        data = {"agent_ids": agent_ids, "total_days": int(total_days)}

        return ApiResponseWrapper(data=data)

    except Exception as e:
        # Log the actual error for debugging, but be careful what you show the user
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching schedule metadata: {str(e)}",
        ) from e


@router.get("/experiments/{exp_id}/agent/{agent_id}/schedule")
async def get_agent_schedule(
    exp_id: str,
    agent_id: int,
    client: Annotated[Any, Depends(get_clickhouse_client)],
    day: int = Query(1, ge=1, description="Day number (1-indexed)"),
) -> ApiResponseWrapper[Dict[str, Any]]:
    """
    Get the daily schedule for a specific agent and day.
    Returns block executions with prompts and responses for each simulation step.
    """
    try:
        # Calculate step range for the requested day
        start_step = (day - 1) * 144
        end_step = start_step + 143

        # 1. Define parameters in a dictionary
        query_params = {
            "exp_id": exp_id,
            "agent_id": agent_id,
            "start_step": start_step,
            "end_step": end_step
        }

        # 2. Use placeholders (%(name)s) instead of f-strings
        blocks_query = """
        SELECT simulation_step, block_name, timestamp
        FROM prompt_responses 
        WHERE exp_id = %(exp_id)s 
          AND agent_id = %(agent_id)s 
          AND simulation_step >= %(start_step)s
          AND simulation_step <= %(end_step)s
        ORDER BY simulation_step, timestamp
        """

        # 3. Pass the parameters dictionary to the client method
        blocks_df = client.query_df(blocks_query, parameters=query_params)

        if blocks_df.empty:
            return ApiResponseWrapper(data={"schedule": []})

        blocks_per_step = blocks_df.groupby("simulation_step")["block_name"].apply(list)

        # Apply the same fix to the second query
        prompts_query = """
        SELECT 
            simulation_step, 
            block_name,
            prompt,
            response
        FROM prompt_responses 
        WHERE exp_id = %(exp_id)s 
          AND agent_id = %(agent_id)s 
          AND simulation_step >= %(start_step)s
          AND simulation_step <= %(end_step)s
        ORDER BY simulation_step, timestamp
        """

        # Pass params here as well
        prompts_df = client.query_df(prompts_query, parameters=query_params)

        # --- The rest of the processing logic remains unchanged ---
        schedule = []

        for step in range(144):  # Always return 144 steps for consistency
            global_step = start_step + step

            if global_step in blocks_per_step.index:
                raw_blocks = blocks_per_step[global_step]
                mapped_blocks = [BLOCK_MAPPING.get(b, "OtherBlock") for b in raw_blocks]
            else:
                mapped_blocks = []

            step_prompts = prompts_df[prompts_df["simulation_step"] == global_step]
            block_executions = []

            for _, row in step_prompts.iterrows():
                raw_block_name = row["block_name"]
                mapped_block_name = BLOCK_MAPPING.get(raw_block_name, "OtherBlock")

                block_executions.append(
                    {
                        "block_name": mapped_block_name,
                        "prompt": row.get("prompt", ""),
                        "response": row.get("response", ""),
                    }
                )

            if not block_executions and mapped_blocks:
                unique_blocks = []
                seen = set()
                for block in mapped_blocks:
                    if block not in seen:
                        unique_blocks.append(block)
                        seen.add(block)

                block_executions = [
                    {
                        "block_name": block,
                        "prompt": f"Execution of {block} at step {step}",
                        "response": f"Completed {block} successfully",
                    }
                    for block in unique_blocks
                ]

            schedule.append(
                {
                    "simulation_step": step, 
                    "block_executions": block_executions,
                }
            )

        data = {
            "schedule": schedule,
            "agent_id": agent_id,
            "day": day,
            "exp_id": exp_id,
        }

        return ApiResponseWrapper(data=data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching agent schedule: {str(e)}",
        ) from e