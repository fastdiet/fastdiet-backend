from pydantic import BaseModel, ConfigDict


class NutrientDetail(BaseModel):
    name: str
    amount: float
    unit: str
    is_primary: bool | None = None
    model_config = ConfigDict(from_attributes=True)