import asyncio
import logging
from sqlalchemy.orm import Session
from app.db.db_connection import init_db
from app.models.recipe import Recipe
from app.services.spoonacular import SpoonacularService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_SIZE = 50


async def update_scores():
    init_db()
    from app.db.db_connection import SessionLocal
    db: Session = SessionLocal()
    spoon = SpoonacularService()

    try:
        recipes_to_update = db.query(Recipe).filter(Recipe.spoonacular_id.isnot(None)).filter(
            (Recipe.health_score.is_(None)) | (Recipe.spoonacular_score.is_(None))
        ).all()

        if not recipes_to_update:
            logger.info("✅ There are no recipes to update. Exiting.")
            return

        logger.info(f"📌 {len(recipes_to_update)} recipes need to be updated")
        for i in range(0, len(recipes_to_update), BATCH_SIZE):
            batch = recipes_to_update[i:i + BATCH_SIZE]
            ids = [r.spoonacular_id for r in batch if r.spoonacular_id]

            logger.info(f"🔄 Batch {i//BATCH_SIZE + 1}: requesting {len(ids)} recipes...")

            try:
                results = await spoon.fetch_recipes_bulk(ids)
            except Exception as e:
                logger.error(f"⚠️ Error fetching batch: {str(e)}")
                continue

            result_map = {r["id"]: r for r in results}

            for recipe in batch:
                data = result_map.get(recipe.spoonacular_id)
                if not data:
                    continue

                recipe.health_score = data.get("healthScore")
                recipe.spoonacular_score = data.get("spoonacularScore")

            db.commit()
            logger.info(f"✅ Batch {i//BATCH_SIZE + 1} updated successfully.")

            await asyncio.sleep(1.2)

        logger.info("🎉 Update successful for all recipes.")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(update_scores())