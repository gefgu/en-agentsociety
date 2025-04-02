from fastapi import APIRouter, Request

__all__ = ["router"]

router = APIRouter(tags=["mlflow"])


@router.get("/mlflow/url")
async def get_mlflow_base_url(request: Request):
    mlflow_url = request.app.state.mlflow_url
    return {"data": mlflow_url}
