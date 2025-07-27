from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.dish_type import DishTypeBase
from app.schemas.ingredient import IngredientShort
from app.schemas.nutrient import NutrientDetail
from app.schemas.user_preferences import CuisineResponse, DietResponse



class RecipeShort(BaseModel):
    id: int | None
    spoonacular_id: int | None
    title: str | None
    image_url: str | None
    ready_min: int | None = None
    calories: float | None = None
    servings: int | None = None
    dish_types_objects: list[DishTypeBase] = Field(default=[], alias="dish_types", exclude=True)

    model_config = ConfigDict(from_attributes=True)

    @computed_field(return_type=list[str])
    def dish_types(self) -> list[str]:
        return [dt.name.lower() for dt in self.dish_types_objects]
    
class _RecipeIngredientDetail(BaseModel):
    original_ingredient_name: str | None = None
    amount: float
    unit: str | None = None
    measures_json: dict | None = None 
    ingredient: IngredientShort
    model_config = ConfigDict(from_attributes=True)

class _RecipeIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    amount: float
    unit: str | None = None



class RecipeDetailResponse(BaseModel):
    id: int
    spoonacular_id: int | None= None
    title: str
    image_url: str | None = None
    ready_min: int | None = None
    servings: int | None = None
    summary: str | None = None
    vegetarian: bool | None = None
    vegan: bool | None = None
    gluten_free: bool | None = None
    dairy_free: bool | None = None
    very_healthy: bool | None = None
    cheap: bool | None = None
    very_popular: bool | None = None
    sustainable: bool | None = None
    low_fodmap: bool | None = None
    preparation_min: int | None = None
    cooking_min: int | None = None
    calories: float | None = None
    analyzed_instructions: list[dict] | None = None
    cuisines_objects: list[CuisineResponse] = Field(default=[], alias="cuisines", exclude=True)
    dish_types_objects: list[DishTypeBase] = Field(default=[], alias="dish_types", exclude=True)
    diet_types_objects: list[DietResponse] = Field(default=[], alias="diet_types", exclude=True)
    recipes_ingredients: list[_RecipeIngredientDetail] = Field(default=[], exclude=True)
    recipes_nutrients: list[Any] = Field(default=[], exclude=True)
    model_config = ConfigDict(from_attributes=True)

    @computed_field(return_type=list[str])
    def dish_types(self) -> list[str]:
        return [dt.name for dt in self.dish_types_objects]
    
    @computed_field(return_type=list[str])
    def diet_types(self) -> list[str]:
        return [dt.name for dt in self.diet_types_objects]
    
    @computed_field(return_type=list[str])
    def cuisines(self) -> list[str]:
        return [c.name for c in self.cuisines_objects]
    
    @computed_field(return_type=list[_RecipeIngredientDetail])
    def ingredients(self) -> list[_RecipeIngredientDetail]:
        return self.recipes_ingredients
    
    @computed_field(return_type=list[NutrientDetail])
    def nutrients(self) -> list[NutrientDetail]:
        response = []
        for assoc in self.recipes_nutrients:
            if hasattr(assoc, 'nutrient') and assoc.nutrient:
                response.append(NutrientDetail(
                    name=assoc.nutrient.name,
                    is_primary=assoc.nutrient.is_primary,
                    amount=assoc.amount,
                    unit=assoc.unit
                ))
        return response


class _InstructionStep(BaseModel):
    number: int
    step: str
    ingredients: list[dict] = []
    equipment: list[dict] = []


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    summary: str | None = None
    image_url: str | None = None
    ready_min: int | None = Field(None, ge=0)
    servings: int = Field(..., ge=1)
    dish_types: list[str] | None = None
    ingredients: list[_RecipeIngredientCreate] = []
    analyzed_instructions: list[_InstructionStep] | None = None

class RecipesListResponse(BaseModel):
    recipes: list[RecipeShort]
    model_config = ConfigDict(from_attributes=True)

class RecipeId(BaseModel):
    new_recipe_id: int



