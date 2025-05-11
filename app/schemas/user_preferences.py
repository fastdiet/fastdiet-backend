from pydantic import BaseModel, ConfigDict

class DietTypeUpdate(BaseModel):
    id: int

class CuisineRegionUpdate(BaseModel):
    cuisine_ids: list[int]

class IntoleranceUpdate(BaseModel):
    intolerance_ids: list[int]

class UserPreferencesResponse(BaseModel):
    id: int
    user_id: int
    diet_type_id: int | None
    vegetarian: bool | None
    vegan: bool | None
    gluten_free: bool | None
    dairy_free: bool | None
    very_healthy: bool | None
    cheap: bool | None
    max_ready_min: int| None
    servings: int | None
    calories_goal: float | None
    sustainable: bool | None
    low_fodmap: bool | None
    
    model_config = ConfigDict(from_attributes=True)