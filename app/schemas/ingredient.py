from pydantic import BaseModel, ConfigDict



class IngredientShort(BaseModel):
    id: int
    name: str
    image_filename: str | None = None
    aisle: str | None = None
    model_config = ConfigDict(from_attributes=True)