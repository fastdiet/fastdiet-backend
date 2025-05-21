from pydantic import BaseModel, ConfigDict

class RecipeShort(BaseModel):
    id: int
    title: str
    image_url: str | None

class MealItemResponse(BaseModel):
    day: int 
    slot: int
    recipe: RecipeShort

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    meal_items: list[MealItemResponse]
    model_config = ConfigDict(from_attributes=True)