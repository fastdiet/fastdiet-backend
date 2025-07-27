from typing import Literal
from pydantic import BaseModel, ConfigDict

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

class DietResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class DietTypeUpdateResponse(BaseModel):
    diet_type: DietResponse | None 

class CuisineRegionUpdate(BaseModel):
    cuisine_ids: list[int]

class CuisineResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class CuisinesUpdateResponse(BaseModel):
    cuisines: list[CuisineResponse]


class IntoleranceUpdate(BaseModel):
    intolerance_ids: list[int]

class IntoleranceResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class IntolerancesUpdateResponse(BaseModel):
    intolerances: list[IntoleranceResponse]



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
    diet_type: DietResponse | None = None
    cuisines: list[CuisineResponse] = []
    intolerances: list[IntoleranceResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

