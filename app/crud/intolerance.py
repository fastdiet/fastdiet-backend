from sqlalchemy.orm import Session
from app.models import Intolerance

def get_intolerances_by_ids(db: Session, intolerance_ids: list[int] ) ->  list[Intolerance]:
    return db.query(Intolerance).filter(Intolerance.id.in_(intolerance_ids)).all()

def get_intolerance_by_id(db: Session, intolerance_id: int) -> Intolerance | None:
    return db.query(Intolerance).filter(Intolerance.id == intolerance_id).first()
