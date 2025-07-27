from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recipe import RecipeShort


class _SlotMeal(BaseModel):
    meal_item_id: int
    slot: int = Field(..., ge=0, le=2, description="0=Breakfast, 1=Lunch, 2=Dinner")
    recipe: RecipeShort
    model_config = ConfigDict(from_attributes=True)

class _DayMealsGroup(BaseModel):
    day: int = Field(..., ge=0, le=6, description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    meals: list[_SlotMeal]
    model_config = ConfigDict(from_attributes=True)

class MealPlanResponse(BaseModel):
    id: int | None
    days: list[_DayMealsGroup]
    model_config = ConfigDict(from_attributes=True)

class MealItemCreate(BaseModel):
    meal_plan_id: int
    recipe_id: int
    day_index: int = Field(..., ge=0, le=6, description="0=Monday, 1=Tuesday, ..., 6=Sunday")
    slot: int = Field(..., ge=0, le=2, description="0=Breakfast, 1=Lunch, 2=Dinner")

class MealItemResponse(BaseModel):
    meal_item_id: int
    recipe: RecipeShort
    slot: int



    