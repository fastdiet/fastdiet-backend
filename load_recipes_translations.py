import csv
import asyncio
import time
from app.db.db_connection import get_db, init_db
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.services.spoonacular import SpoonacularService
from app.utils.translator import translate_analyzed_instructions, translate_text, translate_units
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError




async def load_spoon_recipes_translations():
    init_db()
    db = next(get_db())

    recipes_to_translate = db.query(Recipe).filter(Recipe.title_es == None, Recipe.spoonacular_id != None).all()
    
    if not recipes_to_translate:
        print("All recipes are already translated. No action needed.")
        return

    print(f"Found {len(recipes_to_translate)} recipes to translate. Starting process...")

    for i, recipe in enumerate(recipes_to_translate):
        print(f"[{i+1}/{len(recipes_to_translate)}] Translating recipe ID: {recipe.id} - '{recipe.title[:50]}...'")
        
        try:
            if recipe.title:
                recipe.title_es = translate_text(recipe.title)

            if recipe.summary:
                recipe.summary_es = translate_text(recipe.summary)
            
            if recipe.analyzed_instructions:
                recipe.analyzed_instructions_es = translate_analyzed_instructions(recipe.analyzed_instructions)
        
        except Exception as e:
            print(f"  !! An unexpected error occurred while processing recipe {recipe.id}: {e}")
            print(f"  !! Skipping this recipe. It can be re-run later.")
            continue # Move to the next recipe

    print("\nAll translations processed. Committing changes to the database...")
    try:
        db.commit()
        print("✅ Migration complete! Database has been updated.")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to commit changes to the database. Error: {e}")
        print("Please check the error and consider restoring from your backup.")
        db.rollback()


if __name__ == "__main__":
    asyncio.run(load_spoon_recipes_translations())