from pydantic import BaseModel, Field


class IngredientInfo(BaseModel):
    id: str
    name: str
    grams: float


class NutritionDish(BaseModel):
    dish_id: str = Field(..., description="Unique ID from Nutrition5k dataset")
    total_calories: float
    total_mass: float
    total_fat: float
    total_carb: float
    total_protein: float
    ingredients: list[IngredientInfo]
    complexity: str = Field(..., description="'simple' or 'complex'")
    image_path: str | None = None

    @property
    def summary(self) -> str:
        """Returns a natural language summary for the Oracle response."""
        ing_list = ", ".join([f"{i.grams:.1f}g {i.name}" for i in self.ingredients])
        return (
            f"This dish contains: {ing_list}. "
            f"Total Macros: {self.total_calories:.0f} kcal, "
            f"P: {self.total_protein:.1f}g, F: {self.total_fat:.1f}g, C: {self.total_carb:.1f}g."
        )


class OracleConfig(BaseModel):
    limit: int = 50
    complexity: str = "simple"
    seed: int = 42
    api_url: str = "http://localhost:8000"
    email: str
    password: str
    max_turns: int = 3
