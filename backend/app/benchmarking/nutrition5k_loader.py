import csv
import random
from pathlib import Path

from app.benchmarking.schemas import IngredientInfo, NutritionDish
from app.benchmarking.stratification import StratificationEngine

# Default path relative to this file
# .../backend/app/benchmarking/nutrition5k_loader.py -> .../root/data/nutrition5k
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "nutrition5k"


class Nutrition5kLoader:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self._stratification_engine = StratificationEngine()

    def load_dishes(
        self, seed: int = 42, complexity: str | None = None, limit: int | None = None
    ) -> list[NutritionDish]:
        """
        Loads dishes from metadata CSVs, stratifies by complexity, and returns a deterministic sample.
        """
        dishes = []
        files = ["metadata/dish_metadata_cafe1.csv", "metadata/dish_metadata_cafe2.csv"]

        for filename in files:
            file_path = self.data_dir / filename
            if not file_path.exists():
                print(f"Warning: Metadata file not found: {file_path}")
                continue

            with open(file_path) as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    try:
                        dish = self._parse_row(row)
                        if dish:
                            dishes.append(dish)
                    except ValueError:
                        continue

        # Deterministic Sort
        dishes.sort(key=lambda x: x.dish_id)

        # Shuffle with seed
        rng = random.Random(seed)  # noqa: S311
        rng.shuffle(dishes)

        # Filter
        if complexity:
            dishes = [d for d in dishes if d.complexity.lower() == complexity.lower()]

        # Limit and Validate Image URLs
        if limit:
            import urllib.request

            print(f"Finding {limit} dishes with valid images in Google Cloud Storage...")
            valid_dishes = []
            for d in dishes:
                url = f"https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/imagery/realsense_overhead/{d.dish_id}/rgb.png"
                assert url.startswith("https://")
                req = urllib.request.Request(url, method="HEAD")  # noqa: S310
                try:
                    urllib.request.urlopen(req)  # noqa: S310
                    valid_dishes.append(d)
                except Exception:  # noqa: S110
                    pass
                if len(valid_dishes) == limit:
                    break
            dishes = valid_dishes

        return dishes

    def _parse_row(self, row: list[str]) -> NutritionDish | None:
        # Format: dish_id, cals, mass, fat, carb, prot, [id, name, grams, cals, fat, carb, prot]...
        if len(row) < 6:
            return None

        dish_id = row[0]
        try:
            total_calories = float(row[1])
            total_mass = float(row[2])
            total_fat = float(row[3])
            total_carb = float(row[4])
            total_protein = float(row[5])
        except ValueError:
            return None

        ingredients = []
        idx = 6
        # Each ingredient has 7 fields
        while idx + 6 < len(row):
            try:
                i_id = row[idx]
                i_name = row[idx + 1]
                i_grams = float(row[idx + 2])
                # We skip per-ingredient macros for now as they aren't in IngredientInfo schema
                # idx+3=cals, idx+4=fat, idx+5=carb, idx+6=prot

                ingredients.append(IngredientInfo(id=i_id, name=i_name, grams=i_grams))
                idx += 7
            except (ValueError, IndexError):
                break

        # Image Path Check
        # Image path: imagery/realsense_overhead/<dish_id>/rgb.png
        image_p = self.data_dir / "imagery" / "realsense_overhead" / dish_id / "rgb.png"
        image_path_str = str(image_p) if image_p.exists() else None

        # Create dish with placeholder complexity (will be classified below)
        dish = NutritionDish(
            dish_id=dish_id,
            total_calories=total_calories,
            total_mass=total_mass,
            total_fat=total_fat,
            total_carb=total_carb,
            total_protein=total_protein,
            ingredients=ingredients,
            complexity="pending",  # Will be classified
            image_path=image_path_str,
        )

        # Use multi-factor stratification engine
        dish.complexity = self._stratification_engine.classify(dish)

        return dish
