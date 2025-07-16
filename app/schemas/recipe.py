from pydantic import BaseModel, ConfigDict, Field

from app.schemas.meal_plan import RecipeShort


class _IngredientShort(BaseModel):
    id: int
    name: str
    image_filename: str | None = None
    aisle: str | None = None
    model_config = ConfigDict(from_attributes=True)

class _RecipeIngredientDetail(BaseModel):
    original_ingredient_name: str | None = None
    amount: float
    unit: str | None = None
    measures_json: dict | None = None 
    ingredient: _IngredientShort
    model_config = ConfigDict(from_attributes=True)

class _NutrientDetail(BaseModel):
    name: str
    amount: float
    unit: str
    is_primary: bool | None = None
    model_config = ConfigDict(from_attributes=True)

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
    cuisines: list[str] = []
    dish_types: list[str] = []
    diets: list[str] = []
    ingredients: list[_RecipeIngredientDetail] = []
    nutrients: list[_NutrientDetail] = []
    model_config = ConfigDict(from_attributes=True)

class _RecipeIngredientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    amount: float
    unit: str | None = None

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
    ingredients: list[_RecipeIngredientCreate] = []
    analyzed_instructions: list[_InstructionStep] | None = None

class RecipesListResponse(BaseModel):
    recipes: list[RecipeShort]
    model_config = ConfigDict(from_attributes=True)

