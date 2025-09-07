from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeShort


class SlotMealResponse(BaseModel):
    meal_item_id: int | None = None
    slot: int
    meal_type: str
    recipe: RecipeShort | None
    model_config = ConfigDict(from_attributes=True)

class _DayMealsGroup(BaseModel):
    day: int = Field(..., ge=0, le=6, description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    meals: list[SlotMealResponse]
    model_config = ConfigDict(from_attributes=True)

class MealPlanResponse(BaseModel):
    id: int | None
    days: list[_DayMealsGroup]
    model_config = ConfigDict(from_attributes=True)

class GeneratedMealResponse(BaseModel):
    meal_plan: MealPlanResponse
    status: str

class MealItemCreate(BaseModel):
    meal_plan_id: int
    recipe_id: int
    day_index: int = Field(..., ge=0, le=6, description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    slot: int = Field(..., ge=0)
    meal_type: str




    