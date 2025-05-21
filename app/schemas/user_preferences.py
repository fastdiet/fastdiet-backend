from typing import Literal
from pydantic import BaseModel, ConfigDict

class GoalUpdate(BaseModel):
    goal: Literal['lose_weight', 'maintain_weight', 'gain_weight']

class ActivityUpddate(BaseModel):
    activity_level: Literal['sedentary', 'light', 'moderate', 'high', 'very_high'] 

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
    activity_level: Literal['sedentary', 'light', 'moderate', 'high', 'very_high'] | None
    goal: Literal['lose_weight', 'maintain_weight', 'gain_weight'] | None
    max_ready_min: int| None
    servings: int | None
    calories_goal: float | None
    sustainable: bool | None
    
    model_config = ConfigDict(from_attributes=True)