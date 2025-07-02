from pydantic import BaseModel, ConfigDict


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