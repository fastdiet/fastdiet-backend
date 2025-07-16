from pydantic import BaseModel, ConfigDict, Field

class RecipeShort(BaseModel):
    id: int | None
    spoonacular_id: int | None
    title: str | None
    image_url: str | None
    ready_min: int | None = None
    calories: float | None = None
    servings: int | None = None

    model_config = ConfigDict(from_attributes=True)

class _SlotMeal(BaseModel):
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



    