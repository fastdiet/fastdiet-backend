from typing import Literal
from pydantic import BaseModel, ConfigDict, computed_field

class GoalUpdate(BaseModel):
    goal: Literal['lose_weight', 'maintain_weight', 'gain_weight']

class GoalUpdateResponse(BaseModel):
    goal: Literal['lose_weight', 'maintain_weight', 'gain_weight']
    calories_goal: float | None

class ActivityUpddate(BaseModel):
    activity_level: Literal['sedentary', 'light', 'moderate', 'high', 'very_high']

class ActivityUpdateResponse(BaseModel):
    activity_level: Literal['sedentary', 'light', 'moderate', 'high', 'very_high']
    calories_goal: float | None

class DietTypeUpdate(BaseModel):
    id: int

class _DietResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class DietTypeUpdateResponse(BaseModel):
    diet: _DietResponse | None 

class CuisineRegionUpdate(BaseModel):
    cuisine_ids: list[int]

class _CuisineResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class CuisinesUpdateResponse(BaseModel):
    cuisines: list[_CuisineResponse]


class IntoleranceUpdate(BaseModel):
    intolerance_ids: list[int]

class _IntoleranceResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class IntolerancesUpdateResponse(BaseModel):
    intolerances: list[_IntoleranceResponse]



class UserPreferencesResponse(BaseModel):
    id: int
    user_id: int
    diet_type_id: int | None = None
    activity_level: Literal['sedentary', 'light', 'moderate', 'high', 'very_high'] | None = None
    goal: Literal['lose_weight', 'maintain_weight', 'gain_weight'] | None = None
    max_ready_min: int| None = None
    servings: int | None = None
    calories_goal: float | None = None
    sustainable: bool | None = None
    diet: _DietResponse | None = None
    cuisines: list[_CuisineResponse] = []
    intolerances: list[_IntoleranceResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

