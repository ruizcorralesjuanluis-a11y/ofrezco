from pydantic import BaseModel
from typing import Optional, List


class CategoryOut(BaseModel):
    id: int
    slug: str
    name: str
    parent_id: Optional[int] = None
    active: bool

    class Config:
        from_attributes = True  # Pydantic v2


class CategoryTree(CategoryOut):
    children: List["CategoryTree"] = []
