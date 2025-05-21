from spoonacular import Configuration, ApiClient, DefaultApi
from spoonacular.rest import ApiException
from app.core.config import get_settings
import spoonacular

class SpoonacularService:
    def __init__(self):
        settings = get_settings()
        configuration = Configuration()
        configuration.api_key["apiKeyScheme"] = settings.spoonacular_api_key
        self.api_client = ApiClient(configuration)

    def search_recipes(self, diet: str = None, intolerances: str = None, cuisine: str = None, number: int = 5):
        try:
            api_instance = spoonacular.RecipesApi(self.api_client)
            response = api_instance.search_recipes(
                diet=diet,
                intolerances=intolerances,
                cuisine=cuisine,
                number=number
            )
            print(f"Response from Spoonacular API: {response}")
            return response.to_dict()
        except Exception as e:
            print(f"Exception when calling RecipesApi->search_recipes: {e}")
            return None
            