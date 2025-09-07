import copy
import logging
from google.cloud import translate_v2 as translate
from app.core.config import get_settings

UNIT_TRANSLATOR = {
    "g": "g",
    "gram": "gramo",
    "grams": "gramos",
    "kg": "kg",
    "kilogram": "kilogramo",
    "kilograms": "kilogramos",
    "oz": "oz",
    "ounce": "onza",
    "ounces": "onzas",
    "lb": "lb",
    "pound": "libra",
    "pounds": "libras",
    "inches": "pulgadas",
    "inch": "pulgada",
    "pinch": "pizca",
    "ml": "ml",
    "milliliter": "mililitro",
    "milliliters": "mililitros",
    "l": "l",
    "liter": "litro",
    "liters": "litros",
    "cup": "taza",
    "cups": "tazas",
    "teaspoon": "cucharadita",
    "tsp": "cucharadita",
    "teaspoons": "cucharaditas",
    "tsps": "cucharaditas",
    "tablespoon": "cucharada",
    "tbs": "cucharada",
    "tbsp": "cucharada",
    "tablespoons": "cucharadas",
    "tbsps": "cucharadas",
    "fluid ounce": "onza líquida",
    "fluid ounces": "onzas líquidas",
    "pint": "pinta",
    "pints": "pintas",
    "half pint": "media pinta",
    "drop": "gota",
    "drops": "gotas",
    "dash": "pizca",
    "dashes": "pizcas",

    "package": "paquete",
    "large handful": "manojo grande",
    "packages": "paquetes",
    "box": "caja",
    "boxes": "cajas",
    "container": "envase",
    "containers": "envases",
    "can": "lata",
    "cans": "latas",
    "bar": "barra",
    "bars": "barras",
    "portion": "porción",
    "portions": "porciones",
    "serving": "porción",
    "servings": "porciones",
    "piece": "pieza",
    "pieces": "piezas",
    "slice": "rebanada",
    "slices": "rebanadas",
    "large slices": "lonchas grandes",
    "handful": "puñado",
    "bunch": "manojo",
    "sprig": "ramita",
    "leave": "hoja",
    "leaves": "hojas",
    "clove": "diente",
    "cloves": "dientes",
    "link": "salchicha",
    "links": "salchichas",
    "shell": "tortilla",
    "crust": "base",
    "shot": "chupito",
    "cookie": "galleta",
    "cookies": "galletas",
    "sprigs": "ramitas",
    "small": "pequeño",
    "medium": "mediano",
    "large": "grande",
    "miniature": "miniatura",
    "taco": "taco",
    "roast": "asado",
    "breast": "pechuga",
    "head": "cabeza",
    "heads": "cabezas",
    "halves": "mitades",
    "stalk": "tallo",
    "stalks": "tallos",
    "strips": "tiras",
    "strip": "tira",
    "leaf": "hojas"
    
}

REVERSED_UNIT_EXCEPTIONS = {v: k for k, v in UNIT_TRANSLATOR.items()}


logger = logging.getLogger(__name__)
credentials = get_settings().google_translation_credentials
translate_client = translate.Client.from_service_account_json(json_credentials_path=credentials)

def translate_text(text_or_list: str | list[str], target_language='es'):
    
    if not text_or_list or (isinstance(text_or_list, list) and not any(text_or_list)):
        return text_or_list
    
    try:
        result = translate_client.translate(
            text_or_list,
            target_language=target_language,
            source_language='en'
        )
    except Exception as e:
        print(f"Error in the translation: {e}")
        return text_or_list
    
    if isinstance(text_or_list, list):
        return [item['translatedText'] for item in result]
    else:
        return result['translatedText']
    
def translate_analyzed_instructions(instructions_en: list | None) -> list | None:
    if not instructions_en:
        return None

    steps_to_translate = []
    for group in instructions_en:
        for step in group.get('steps', []):
            if step_text := step.get('step'):
                steps_to_translate.append(step_text)

    if not steps_to_translate:
        return instructions_en

    try:
        translated_steps = translate_text(steps_to_translate, target_language='es')
    except Exception as e:
        logger.error(f"Error translating the instructions. We wil use the originals. Error: {e}")
        return instructions_en
        
    instructions_es = copy.deepcopy(instructions_en)
    
    translation_index = 0
    for group in instructions_es:
        for step in group.get('steps', []):
            if step.get('step'):
                step['step'] = translated_steps[translation_index]
                translation_index += 1
    
    return instructions_es
    

def translate_units(units_en: list[str]) -> list[str]:
    if not units_en:
        return []

    final_translations = {}
    units_to_translate_api = []

    for unit in units_en:
        unit_to_check = unit.strip().lower() 
        if unit_to_check in UNIT_TRANSLATOR:
            final_translations[unit] = UNIT_TRANSLATOR[unit_to_check]
        else:
            units_to_translate_api.append(unit)

    if units_to_translate_api:
        api_translations = translate_text(units_to_translate_api)
        translated_map = dict(zip(units_to_translate_api, api_translations))
        final_translations.update(translated_map)

    return [final_translations[unit] for unit in units_en]

def translate_unit_for_display(unit: str | None, lang: str) -> str | None:
    """Translates a unit to Spanish for display purposes"""
    if not unit or lang != "es":
        return unit
    return UNIT_TRANSLATOR.get(unit.strip().lower(), unit)

def translate_unit_to_english(unit: str | None) -> str | None:
    if not unit:
        return unit
    return REVERSED_UNIT_EXCEPTIONS.get(unit.strip().lower(), unit)


def translate_measures_for_shopping_list(measures: dict | None, lang: str) -> dict | None:
    if not measures or lang != "es":
        return measures
    
    translated = {}
    for system, measure in measures.items():
        translated[system] = {
            "amount": measure["amount"],
            "unit": UNIT_TRANSLATOR.get(measure.get("unit", "").lower(), measure.get("unit")),
        }
    return translated

def translate_measures_for_recipe(measures: dict | None, lang: str) -> dict | None:
    if not measures or lang != "es":
        return measures
    
    translated = {}
    for system, measure in measures.items():
        translated[system] = {
            "amount": measure["amount"],
            "unitShort": UNIT_TRANSLATOR.get(measure.get("unitShort", "").lower(), measure.get("unitShort")),
            "unitLong": UNIT_TRANSLATOR.get(measure.get("unitLong", "").lower(), measure.get("unitLong")),
        }
    return translated