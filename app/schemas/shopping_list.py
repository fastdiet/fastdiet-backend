from typing import Any
from pydantic import BaseModel


class ShoppingListItem(BaseModel):
    name: str
    measures: dict[str, Any]
    pantryItem: bool | None = False
    aisle: str | None = None
    cost: float
    ingredientId: int | None = None
    image_filename: str | None = None
    amount: float | None = None
    unit: str | None = None

class Aisle(BaseModel):
    aisle: str
    items: list[ShoppingListItem]

class ShoppingListResponse(BaseModel):
    aisles: list[Aisle]
    cost: float