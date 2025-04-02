from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

__all__ = ["ApiResponseWrapper"]

T = TypeVar("T")


class ApiResponseWrapper(BaseModel, Generic[T]):
    """API Response Wrapper"""

    data: T = Field(..., description="Response Data")


# # 分页响应模型
# class PaginatedResponse(BaseModel, Generic[T]):
#     """分页响应模型"""

#     total: int = Field(..., description="总记录数")
#     items: List[T] = Field(..., description="数据项列表")
