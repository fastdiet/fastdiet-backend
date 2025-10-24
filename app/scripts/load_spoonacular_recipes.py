import asyncio
import logging
import argparse
import random
from sqlalchemy.orm import Session
from app.db.db_connection import init_db
from app.services.spoonacular import SpoonacularService
from app.crud.recipe import get_or_create_spoonacular_recipe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecipeLoader:
    def __init__(self):
        self.spoonacular = SpoonacularService()
        self.loaded_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.api_calls = 0
        self.max_results_per_call = 100

    def save_recipe_to_db(self, db: Session, recipe_data: dict) -> bool:
        """Save a recipe to the database (or skip if already exists)."""
        try:
            recipe_id = recipe_data.get("id")
            if not recipe_id:
                self.error_count += 1
                logger.warning("Recipe without ID, skipped.")
                return False

            recipe, was_created = get_or_create_spoonacular_recipe(db, recipe_data)

            if recipe:
                if was_created:
                    self.loaded_count += 1
                    logger.info(f"✓ NEW: {recipe_data.get('title')} (ID: {recipe_id})")
                    return True
                else:
                    self.skipped_count += 1
                    logger.info(f"⊘ SKIPPED (already exists): {recipe_data.get('title')} (ID: {recipe_id})")
                    return False
            else:
                self.skipped_count += 1
                return False

        except Exception as e:
            self.error_count += 1
            db.rollback()
            logger.error(f"✗ Error saving recipe {recipe_data.get('id')}: {str(e)}")
            return False

    async def load_all_recipes(
        self,
        db: Session,
        start_offset: int = 0,
        max_recipes: int | None = None,
        sort: str = "popularity"
    ):
        offset = start_offset
        batch_number = (start_offset // self.max_results_per_call) + 1
        total_results = None
        seen_ids = set()  # Track IDs to avoid duplicates

        logger.info(f"🚀 Loading recipes from Spoonacular (sort={sort}, starting offset={offset})...")

        while True:
            try:
                logger.info(f"\n{'=' * 70}")
                logger.info(f"Batch {batch_number}: offset={offset}")
                logger.info(f"{'=' * 70}")

                # Call API with offset parameter
                result = await self.spoonacular.search_recipes(
                    query=" ",  # Space to search all recipes
                    offset=offset,
                    number=self.max_results_per_call,
                    sort=sort,
                    sort_direction="asc",
                    add_recipe_information=True,
                    add_recipe_instructions=True,
                    add_recipe_nutrition=True,
                    fill_ingredients=True,
                )
                self.api_calls += 1

                recipes = result.get("results", [])
                total_results = result.get("totalResults", total_results or 0)

                logger.info(f"Retrieved {len(recipes)} recipes from API")
                logger.info(f"Total recipes available in Spoonacular: {total_results}")

                # Stop if no more recipes
                if not recipes:
                    logger.info("No more recipes available. Finishing.")
                    break

                batch_saved = 0
                batch_skipped = 0
                for recipe_data in recipes:
                    recipe_id = recipe_data.get("id")
                    if not recipe_id:
                        continue

                    # Avoid duplicates between batches
                    if recipe_id in seen_ids:
                        logger.debug(f"Skipped duplicate recipe ID={recipe_id}")
                        batch_skipped += 1
                        continue
                    seen_ids.add(recipe_id)

                    if self.save_recipe_to_db(db, recipe_data):
                        batch_saved += 1
                    else:
                        batch_skipped += 1

                db.commit()
                logger.info(f"✅ Batch {batch_number} completed: {batch_saved} NEW recipes, {batch_skipped} already existed")

                # Progress
                progress_percentage = (self.loaded_count / total_results * 100) if total_results > 0 else 0
                logger.info(f"Progress: {self.loaded_count}/{total_results} recipes ({progress_percentage:.1f}%)")
                logger.info(f"Stats: Loaded={self.loaded_count}, Skipped={self.skipped_count}, "
                          f"Errors={self.error_count}, API Calls={self.api_calls}")

                # Stop if max recipes reached
                if max_recipes and self.loaded_count >= max_recipes:
                    logger.info(f"Maximum limit ({max_recipes}) reached. Stopping.")
                    break

                # Spoonacular typically has ~5000-5500 max results
                if offset >= total_results:
                    logger.info("Reached end of available recipes.")
                    break

                # If returned less than expected, it's the last batch
                if len(recipes) < self.max_results_per_call:
                    logger.info("Last batch detected (fewer recipes than expected). Finishing.")
                    break

                offset += self.max_results_per_call
                batch_number += 1

                # Checkpoint every 10 batches
                if batch_number % 10 == 0:
                    logger.info(f"\n🔄 Checkpoint: {batch_number} batches completed (offset={offset})")
                    self.print_summary()

                # Small pause to avoid rate limiting
                await asyncio.sleep(1.5)

            except Exception as e:
                msg = str(e).lower()
                if "rate limit" in msg or "429" in msg:
                    wait_time = random.randint(30, 90)
                    logger.warning(f"⚠️ Rate limit detected. Waiting {wait_time}s before retrying...")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(f"Error in batch {batch_number} (offset {offset}): {str(e)}", exc_info=True)
                db.rollback()
                raise

        logger.info("\n🎉 Recipe loading finished.")

    def print_summary(self):
        logger.info("\n" + "=" * 70)
        logger.info("LOADING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total loaded: {self.loaded_count}")
        logger.info(f"Duplicates skipped: {self.skipped_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info(f"API Calls: {self.api_calls}")
        logger.info("=" * 70)

    async def run(self, start_offset: int = 0, max_recipes: int = None, sort: str = "max-used-ingredients"):
        init_db()
        from app.db.db_connection import SessionLocal
        db = SessionLocal()

        try:
            # ✅ Verificar qué base de datos se está usando
            from sqlalchemy import text
            result = db.execute(text("SELECT DATABASE()")).scalar()
            logger.info("=" * 70)
            logger.info("DATABASE CONNECTION INFO")
            logger.info("=" * 70)
            logger.info(f"📊 Connected to database: {result}")
            logger.info("=" * 70)
            
            # ✅ Contar recetas actuales
            from app.models.recipe import Recipe
            initial_count = db.query(Recipe).count()
            logger.info(f"📊 Current recipes in database: {initial_count}")
            
            logger.info("=" * 70)
            logger.info("STARTING MASS RECIPE LOADING")
            logger.info("=" * 70)
            logger.info(f"Starting offset: {start_offset}")
            logger.info(f"Sort by: {sort}")
            if max_recipes:
                logger.info(f"Maximum to load: {max_recipes}")
            logger.info("=" * 70)

            await self.load_all_recipes(db, start_offset, max_recipes, sort)
            
            # ✅ Contar recetas finales
            final_count = db.query(Recipe).count()
            logger.info(f"\n📊 Final recipes in database: {final_count}")
            logger.info(f"📊 Net new recipes added: {final_count - initial_count}")
            
            self.print_summary()

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Process manually interrupted.")
            self.print_summary()
        except Exception as e:
            logger.error(f"Critical error: {str(e)}", exc_info=True)
            self.print_summary()
        finally:
            db.close()


async def main():
    parser = argparse.ArgumentParser(description="Mass recipe loading from Spoonacular.")
    parser.add_argument("--offset", type=int, default=0, help="Starting offset (to resume).")
    parser.add_argument("--max", type=int, default=None, help="Maximum number of recipes to load.")
    parser.add_argument("--sort", type=str, default="max-used-ingredients", 
                       choices=["popularity", "healthiness", "time", "random"],
                       help="Sorting criteria")
    args = parser.parse_args()

    loader = RecipeLoader()
    await loader.run(args.offset, args.max, args.sort)


if __name__ == "__main__":
    asyncio.run(main())