from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T] = Field(default_factory=list)
    total: int = Field(..., description="Number of items matching the filter")
    limit: int
    offset: int
