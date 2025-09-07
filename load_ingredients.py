import csv
import asyncio
import time
from app.db.db_connection import get_db, init_db
from app.models.ingredient import Ingredient
from app.services.spoonacular import SpoonacularService
from app.utils.translator import translate_text, translate_units
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

CSV_PATH = "data/ingredients-with-possible-units.csv"

async def insert_ingredient_from_csv_line(db: AsyncSession, row: list[str], spoon_service: SpoonacularService):
    spoonacular_id = int(row[1].strip())

    spoon_ing_data = await spoon_service.fetch_ingredients_info(spoonacular_id)
    name_en = spoon_ing_data["name"]
    name_es = translate_text(name_en)
    possible_units_es = translate_units(spoon_ing_data["possible_units"])

    ingredient = Ingredient(
        spoonacular_id=spoonacular_id,
        name_en=name_en,
        name_es=name_es,
        possible_units_en=spoon_ing_data["possible_units"],
        possible_units_es=possible_units_es,
        image_filename=spoon_ing_data["image"],
        aisle=spoon_ing_data["aisle"]
    )

    try:
        db.add(ingredient)
        db.commit()
        print(f"✅ Inserted: {name_en} ({name_es})")
    except IntegrityError:
        db.rollback()
        print(f"⚠️ It already exists: {name_en}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting {name_en}: {e}")

async def load_ingredients_from_csv():
    init_db()
    spoon_service = SpoonacularService()
    with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        rows = list(reader)


    db = next(get_db())

    for row in rows[3164:]:
        time.sleep(1)
        await insert_ingredient_from_csv_line(db, row, spoon_service)

if __name__ == "__main__":
    asyncio.run(load_ingredients_from_csv())