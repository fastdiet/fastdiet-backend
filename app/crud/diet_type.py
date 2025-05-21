from sqlalchemy.orm import Session
from app.models import DietType

# Function to get a diet type by the id
def get_diet_type_by_id(db: Session, id : int ) -> DietType | None:
    return db.query(DietType).filter(DietType.id == id).first()