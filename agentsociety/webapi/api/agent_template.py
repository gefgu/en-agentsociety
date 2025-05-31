import uuid
from typing import Dict, List, cast, Any, Type

from fastapi import APIRouter, Body, HTTPException, Request, status
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ApiResponseWrapper
from ..models.agent_template import (
    AgentTemplateDB,
    ApiAgentTemplate,
    ChoiceDistribution,
    UniformIntDistribution,
    NormalDistribution,
    ChoiceDistributionConfig,
    UniformIntDistributionConfig,
    NormalDistributionConfig,
    AgentParams,
    DistributionType,
)

try:
    from agentsociety_community.agents import citizens, supervisors
    from agentsociety_community.workflows import functions as workflow_functions
    from agentsociety_community.blocks import citizens as citizen_blocks
except ImportError:
    import warnings

    warnings.warn(
        "agentsociety_community is not installed. Please install it with `pip install agentsociety-community`"
    )

    citizens = None
    supervisors = None
    workflow_functions = None
    citizen_blocks = None

__all__ = ["router"]

router = APIRouter(tags=["agent_templates"])


@router.get("/agent-templates")
async def list_agent_templates(
    request: Request,
) -> ApiResponseWrapper[List[ApiAgentTemplate]]:
    """List all agent templates"""
    try:
        tenant_id = await request.app.state.get_tenant_id(request)

        async with request.app.state.get_db() as db:
            db = cast(AsyncSession, db)
            stmt = (
                select(AgentTemplateDB)
                .where(AgentTemplateDB.tenant_id.in_([tenant_id, ""]))
                .order_by(AgentTemplateDB.created_at.desc())
            )

            result = await db.execute(stmt)
            templates = result.scalars().all()

            api_templates = []
            for template in templates:
                # Convert distribution configuration from database to corresponding distribution objects
                memory_distributions_dict = {}
                for key, value in template.profile.items():
                    if isinstance(value, dict):
                        dist_type = value.get("type")
                        if dist_type == "choice":
                            if "params" in value:
                                memory_distributions_dict[key] = ChoiceDistribution(
                                    type=DistributionType.CHOICE,
                                    params={
                                        "choices": value["params"]["choices"],
                                        "weights": value["params"]["weights"],
                                    },
                                )
                            else:
                                memory_distributions_dict[key] = (
                                    ChoiceDistributionConfig(
                                        type=DistributionType.CHOICE,
                                        choices=value["choices"],
                                        weights=value["weights"],
                                    )
                                )
                        elif dist_type == "uniform_int":
                            if "params" in value:
                                memory_distributions_dict[key] = UniformIntDistribution(
                                    type=DistributionType.UNIFORM_INT,
                                    params={
                                        "min_value": value["params"]["min_value"],
                                        "max_value": value["params"]["max_value"],
                                    },
                                )
                            else:
                                memory_distributions_dict[key] = (
                                    UniformIntDistributionConfig(
                                        type=DistributionType.UNIFORM_INT,
                                        min_value=value["min_value"],
                                        max_value=value["max_value"],
                                    )
                                )
                        elif dist_type == "normal":
                            if "params" in value:
                                memory_distributions_dict[key] = NormalDistribution(
                                    type=DistributionType.NORMAL,
                                    params={
                                        "mean": value["params"]["mean"],
                                        "std": value["params"]["std"],
                                    },
                                )
                            else:
                                memory_distributions_dict[key] = (
                                    NormalDistributionConfig(
                                        type=DistributionType.NORMAL,
                                        mean=value["mean"],
                                        std=value["std"],
                                    )
                                )

                api_template = ApiAgentTemplate(
                    tenant_id=template.tenant_id,
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    agent_type=template.agent_type,
                    agent_class=template.agent_class,
                    memory_distributions=memory_distributions_dict,
                    agent_params=AgentParams(**template.agent_params),
                    blocks=template.blocks,
                    created_at=template.created_at,
                    updated_at=template.updated_at,
                )
                api_templates.append(api_template)

            return ApiResponseWrapper(data=api_templates)

    except Exception as e:
        print(f"Error in list_agent_templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )


@router.get("/agent-templates/{template_id}")
async def get_agent_template(
    request: Request,
    template_id: str,
) -> ApiResponseWrapper[ApiAgentTemplate]:
    """Get agent template by ID"""
    try:
        tenant_id = await request.app.state.get_tenant_id(request)

        async with request.app.state.get_db() as db:
            db = cast(AsyncSession, db)
            stmt = select(AgentTemplateDB).where(
                AgentTemplateDB.tenant_id.in_([tenant_id, ""]),
                AgentTemplateDB.id == template_id,
            )

            result = await db.execute(stmt)
            template = result.scalar_one_or_none()

            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
                )

            # Convert distribution configuration from database to corresponding distribution objects
            memory_distributions_dict = {}
            for key, value in template.profile.items():
                if isinstance(value, dict):
                    dist_type = value.get("type")
                    if dist_type == "choice":
                        if "params" in value:
                            memory_distributions_dict[key] = ChoiceDistribution(
                                type=DistributionType.CHOICE,
                                params={
                                    "choices": value["params"]["choices"],
                                    "weights": value["params"]["weights"],
                                },
                            )
                        else:
                            memory_distributions_dict[key] = ChoiceDistributionConfig(
                                type=DistributionType.CHOICE,
                                choices=value["choices"],
                                weights=value["weights"],
                            )
                    elif dist_type == "uniform_int":
                        if "params" in value:
                            memory_distributions_dict[key] = UniformIntDistribution(
                                type=DistributionType.UNIFORM_INT,
                                params={
                                    "min_value": value["params"]["min_value"],
                                    "max_value": value["params"]["max_value"],
                                },
                            )
                        else:
                            memory_distributions_dict[key] = (
                                UniformIntDistributionConfig(
                                    type=DistributionType.UNIFORM_INT,
                                    min_value=value["min_value"],
                                    max_value=value["max_value"],
                                )
                            )
                    elif dist_type == "normal":
                        if "params" in value:
                            memory_distributions_dict[key] = NormalDistribution(
                                type=DistributionType.NORMAL,
                                params={
                                    "mean": value["params"]["mean"],
                                    "std": value["params"]["std"],
                                },
                            )
                        else:
                            memory_distributions_dict[key] = NormalDistributionConfig(
                                type=DistributionType.NORMAL, mean=value["mean"], std=value["std"]
                            )

            api_template = ApiAgentTemplate(
                tenant_id=template.tenant_id,
                id=template.id,
                name=template.name,
                description=template.description,
                agent_type=template.agent_type,
                agent_class=template.agent_class,
                memory_distributions=memory_distributions_dict,
                agent_params=AgentParams(**template.agent_params),
                blocks=template.blocks,
                created_at=template.created_at,
                updated_at=template.updated_at,
            )

            return ApiResponseWrapper(data=api_template)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_agent_template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        )


@router.post("/agent-templates")
async def create_agent_template(
    request: Request,
    template: ApiAgentTemplate = Body(...),
) -> ApiResponseWrapper[ApiAgentTemplate]:
    """Create a new agent template"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    try:
        tenant_id = await request.app.state.get_tenant_id(request)
        template_id = str(uuid.uuid4())

        # Convert memory_distributions to serializable dictionary format
        profile_dict = {}
        for key, value in template.memory_distributions.items():
            if isinstance(
                value,
                (
                    ChoiceDistributionConfig,
                    UniformIntDistributionConfig,
                    NormalDistributionConfig,
                ),
            ):
                # 如果是Config类型，直接转换为字典
                profile_dict[key] = value.model_dump()
            elif isinstance(
                value, (ChoiceDistribution, UniformIntDistribution, NormalDistribution)
            ):
                # 如果是Distribution类型，保持params结构
                profile_dict[key] = value.model_dump()
            else:
                # 如果已经是字典格式，直接使用
                profile_dict[key] = value

        # Create default base configuration
        base_config = {
            "home": {"aoi_position": {"aoi_id": 0}},
            "work": {"aoi_position": {"aoi_id": 0}},
        }

        # Create default states configuration
        states_config = {"needs": "str", "plan": "dict"}

        async with request.app.state.get_db() as db:
            db = cast(AsyncSession, db)

            new_template = AgentTemplateDB(
                tenant_id=tenant_id,
                id=template_id,
                name=template.name,
                description=template.description,
                agent_type=template.agent_type,
                agent_class=template.agent_class,
                profile=profile_dict,
                base=base_config,
                states=states_config,
                agent_params=template.agent_params.dict(),
                blocks=template.blocks,
            )

            db.add(new_template)
            await db.commit()
            await db.refresh(new_template)

            # Construct response data
            response_template = ApiAgentTemplate(
                tenant_id=new_template.tenant_id,
                id=new_template.id,
                name=new_template.name,
                description=new_template.description,
                agent_type=new_template.agent_type,
                agent_class=new_template.agent_class,
                memory_distributions=new_template.profile,
                base=new_template.base,
                states=new_template.states,
                agent_params=AgentParams(**new_template.agent_params),
                blocks=new_template.blocks,
                created_at=new_template.created_at,
                updated_at=new_template.updated_at,
            )

            return ApiResponseWrapper(data=response_template)

    except Exception as e:
        print(f"Error details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.put("/agent-templates/{template_id}")
async def update_agent_template(
    request: Request,
    template_id: str,
    template: ApiAgentTemplate = Body(...),
) -> ApiResponseWrapper[ApiAgentTemplate]:
    """Update an existing agent template"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = (
            update(AgentTemplateDB)
            .where(
                AgentTemplateDB.tenant_id == tenant_id,
                AgentTemplateDB.id == template_id,
            )
            .values(
                name=template.name,
                description=template.description,
                agent_type=template.agent_type,
                agent_class=template.agent_class,
                profile=template.memory_distributions,
                agent_params=template.agent_params.model_dump(),
                blocks=template.blocks,
            )
        )

        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )

        await db.commit()
        return ApiResponseWrapper(data=template)


@router.delete("/agent-templates/{template_id}")
async def delete_agent_template(
    request: Request,
    template_id: str,
) -> ApiResponseWrapper[Dict[str, str]]:
    """Delete an agent template"""
    if request.app.state.read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Server is in read-only mode"
        )

    tenant_id = await request.app.state.get_tenant_id(request)

    async with request.app.state.get_db() as db:
        db = cast(AsyncSession, db)
        stmt = delete(AgentTemplateDB).where(
            AgentTemplateDB.tenant_id == tenant_id, AgentTemplateDB.id == template_id
        )

        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )

        await db.commit()
        return ApiResponseWrapper(data={"message": "Template deleted successfully"})


@router.get("/agent-blocks")
async def get_agent_blocks(
    request: Request,
) -> ApiResponseWrapper[List[str]]:
    """Get available block types"""
    try:
        blocks = []
        
        # 获取citizen blocks
        if citizen_blocks is not None:
            # for block_name, block_class in citizen_blocks.get_type_to_cls_dict().items():
            #     block_info = {
            #         "block_name": block_class.name,
            #         "description": block_class.description,
            #     }
            #     blocks.append(block_info)
            blocks = list(citizen_blocks.get_type_to_cls_dict().keys())

        return ApiResponseWrapper(data=blocks)
    except Exception as e:
        print(f"Error in get_agent_blocks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent blocks: {str(e)}",
        )


def simplify_type(type_annotation):
    """Convert type annotation to a simplified string format"""
    type_str = str(type_annotation)

    # Handle class format
    if type_str.startswith("<class '") and type_str.endswith("'>"):
        return type_str[8:-2]

    # Handle typing.Optional
    if type_str.startswith("typing.Optional["):
        inner_type = type_str[len("typing.Optional[") : -1]
        return f"{simplify_type(inner_type)}?"

    # Handle typing.List
    if type_str.startswith("typing.List["):
        inner_type = type_str[len("typing.List[") : -1]
        return f"List<{simplify_type(inner_type)}>"

    # Handle typing.Dict
    if type_str.startswith("typing.Dict["):
        # Extract key and value types
        inner_types = type_str[len("typing.Dict[") : -1].split(", ")
        if len(inner_types) == 2:
            key_type = simplify_type(inner_types[0])
            value_type = simplify_type(inner_types[1])
            return f"Dict<{key_type}, {value_type}>"

    # Handle Union type
    if type_str.startswith("typing.Union["):
        inner_types = type_str[len("typing.Union[") : -1].split(", ")
        return " | ".join(simplify_type(t) for t in inner_types)

    return type_str.replace("typing.", "")


def get_field_info(field):
    """Helper function to safely get field information"""
    try:
        default_value = None
        if hasattr(field, "default") and field.default is not None:
            # Handle Pydantic Undefined type
            if str(field.default.__class__).endswith("PydanticUndefinedType'>"):
                default_value = None
            else:
                default_value = field.default

        return {
            "type": simplify_type(field.annotation),
            "description": field.description if hasattr(field, "description") else None,
            "default": default_value,
        }
    except Exception as e:
        print(f"Error processing field: {str(e)}")
        return {"type": "unknown", "description": None, "default": None}


@router.get("/agent-param")
async def get_agent_param(
    request: Request,
    agent_type: str,
    agent_class: str,
) -> ApiResponseWrapper[Dict[str, Any]]:
    """Get agent's parameters including ParamsType, BlockOutputType, Context and StatusAttributes based on agent type and class"""
    try:
        # Get the appropriate agent class based on agent_type and agent_class
        if agent_type == "citizen":
            if citizens is None:
                type_dict = {}
            else:
                type_dict = citizens.get_type_to_cls_dict()
        elif agent_type == "supervisor":
            if supervisors is None:
                type_dict = {}
            else:
                type_dict = supervisors.get_type_to_cls_dict()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_type. Must be 'citizen' or 'supervisor', got: {agent_type}",
            )

        if agent_class not in type_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_class '{agent_class}' for agent_type '{agent_type}'. Available classes: {list(type_dict.keys())}",
            )

        # Get the agent class
        agent_cls_factory = type_dict[agent_class]
        agent_cls = agent_cls_factory()

        # Get agent parameters information
        param_data = {
            "params_type": {},
            "block_output_type": {},
            "context": {},
            "status_attributes": [],
        }

        # Process ParamsType
        if hasattr(agent_cls.ParamsType, "model_fields"):
            param_data["params_type"] = {
                field_name: get_field_info(field)
                for field_name, field in agent_cls.ParamsType.model_fields.items()
            }

        # Process BlockOutputType
        if hasattr(agent_cls.BlockOutputType, "model_fields"):
            param_data["block_output_type"] = {
                field_name: get_field_info(field)
                for field_name, field in agent_cls.BlockOutputType.model_fields.items()
            }

        # Process Context
        if hasattr(agent_cls.Context, "model_fields"):
            param_data["context"] = {
                field_name: get_field_info(field)
                for field_name, field in agent_cls.Context.model_fields.items()
            }

        # Process StatusAttributes
        param_data["status_attributes"] = [
            {
                "name": attr.name,
                "type": simplify_type(attr.type),
                "default": (
                    None
                    if str(attr.default.__class__).endswith("PydanticUndefinedType'>")
                    else attr.default
                ),
                "description": attr.description,
                # "whether_embedding": attr.whether_embedding if hasattr(attr, "whether_embedding") else False
            }
            for attr in agent_cls.StatusAttributes
        ]

        return ApiResponseWrapper(data=param_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_agent_param: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent parameters: {str(e)}",
        )


@router.get("/block-param/{block_type}")
async def get_block_param(
    request: Request,
    block_type: str,
) -> ApiResponseWrapper[Dict[str, Any]]:
    """Get Block's parameters including ParamsType and Context for specified block type"""
    try:
        # 在citizen blocks中查找
        if citizen_blocks is not None:
            block_map = citizen_blocks.get_type_to_cls_dict()
            if block_type in block_map:
                block_class_factory = block_map[block_type]
                block_class = block_class_factory()

        if block_class is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid block type: {block_type}",
            )

        # Get Block parameters information
        param_data = {
            "params_type": {},
            "context": {},
        }

        # Process ParamsType
        if hasattr(block_class, "ParamsType") and hasattr(
            block_class.ParamsType, "model_fields"
        ):
            param_data["params_type"] = {
                field_name: get_field_info(field)
                for field_name, field in block_class.ParamsType.model_fields.items()
                if field_name != "block_memory"  # 排除 block_memory 字段
            }

        # Process Context
        if hasattr(block_class, "ContextType") and hasattr(
            block_class.ContextType, "model_fields"
        ):
            param_data["context"] = {
                field_name: get_field_info(field)
                for field_name, field in block_class.ContextType.model_fields.items()
            }

        return ApiResponseWrapper(data=param_data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_block_param: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get block parameters: {str(e)}",
        )


@router.get("/agent-classes")
async def get_agent_classes(
    request: Request,
    agent_type: str,
) -> ApiResponseWrapper[List[Dict[str, str]]]:
    """Get available agent classes base on agent type"""
    try:
        if agent_type == "citizen":
            if citizens is None:
                type_dict = {}
            else:
                type_dict = citizens.get_type_to_cls_dict()
        elif agent_type == "supervisor":
            if supervisors is None:
                type_dict = {}
            else:
                type_dict = supervisors.get_type_to_cls_dict()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent_type. Must be 'citizen' or 'supervisor', got: {agent_type}",
            )

        # Convert to list of dicts with value and label for frontend Select component
        agent_type_result = [
            {"value": type_name, "label": type_name} for type_name in type_dict.keys()
        ]
        return ApiResponseWrapper(data=agent_type_result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_agent_classes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent_classes '{agent_type}': {str(e)}",
        )


@router.get("/community/workflow/functions")
async def get_workflow_functions(
    request: Request,
) -> ApiResponseWrapper[List[str]]:
    """Get available workflow function names"""
    try:
        if workflow_functions is None:
            function_map = {}
        else:
            function_map = workflow_functions.get_type_to_cls_dict()
        function_names = list(function_map.keys())
        return ApiResponseWrapper(data=function_names)
    except Exception as e:
        print(f"Error in get_workflow_functions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow functions: {str(e)}",
        )
