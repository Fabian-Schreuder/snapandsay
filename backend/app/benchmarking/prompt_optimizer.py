import logging
import uuid
from datetime import datetime

from app.benchmarking.experiment_log import ExperimentLog, ExperimentResult
from app.benchmarking.metrics import LatencyTracker, MetricsCalculator
from app.benchmarking.nutrition5k_loader import Nutrition5kLoader
from app.benchmarking.oracle_runner import OracleRunner
from app.benchmarking.prompts import PromptRegistry
from app.config import settings

logger = logging.getLogger(__name__)


class PromptOptimizer:
    def __init__(
        self,
        prompt_registry: PromptRegistry,
        experiment_log: ExperimentLog,
        api_url: str,
        email: str,
        password: str,
    ):
        self.registry = prompt_registry
        self.log = experiment_log
        self.runner = OracleRunner(api_url=api_url, email=email, password=password)
        self.loader = Nutrition5kLoader()

    async def run_experiment(
        self, prompt_id: str, limit: int = 5, complexity: str = "simple", seed: int = 42
    ) -> ExperimentResult:
        """Run a benchmark experiment with a specific prompt version."""
        prompt = self.registry.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt version {prompt_id} not found")

        logger.info(f"Starting experiment with prompt {prompt_id} ({prompt.name})")
        dishes = self.loader.load_dishes(seed=seed, complexity=complexity, limit=limit)

        results = []
        latency_tracker = LatencyTracker()
        metrics_calculator = MetricsCalculator()

        experiment_id = str(uuid.uuid4())[:8]
        dish_maes = []

        for i, dish in enumerate(dishes):
            logger.info(f"Experiment {experiment_id} | Dish {i+1}/{len(dishes)}: {dish.dish_id}")

            # Pass the override to the runner
            result = await self.runner.run_dish(dish, system_prompt_override=prompt.template)

            if result["success"]:
                latency_tracker.record(dish.dish_id, result["latency_seconds"], dish.complexity)
                results.append(result)

                # Calculate per-dish MAE
                predicted = result.get("final_data")
                dish_mae = metrics_calculator.calculate_dish_mae(predicted, dish)
                dish_maes.append(dish_mae)
            else:
                logger.error(f"Dish {dish.dish_id} failed: {result.get('error')}")

        # Calculate aggregate metrics
        aggregate = metrics_calculator.aggregate_mae(dish_maes)
        mae_metrics = {
            "calories": aggregate.mean_calories,
            "protein": aggregate.mean_protein,
            "fat": aggregate.mean_fat,
            "carbs": aggregate.mean_carbs,
        }
        latency_stats = latency_tracker.aggregate().to_dict()

        experiment_result = ExperimentResult(
            experiment_id=experiment_id,
            prompt_version=prompt_id,
            timestamp=datetime.now().isoformat(),
            metrics=mae_metrics,
            latency_stats=latency_stats,
            per_dish_results=results,
            config={"limit": limit, "complexity": complexity, "seed": seed},
        )
        return experiment_result

    async def suggest_improvements(self, result: ExperimentResult) -> str:
        """Analyze errors and suggest prompt improvements using LLM."""
        logger.info(f"Analyzing errors for experiment {result.experiment_id}...")

        # Identify top errors
        errors = [r for r in result.per_dish_results if r.get("mae", {}).get("calories", 0) > 50]
        error_summary = []
        for e in errors:
            calories_gt = e["ground_truth"]["calories"]
            calories_pred = e["predicted"]["calories"]
            mae = e["mae"]["calories"]
            error_summary.append(
                f"- Dish {e['dish_id']}: GT={calories_gt} kcal, Pred={calories_pred} kcal (MAE={mae:.1f})"
            )

        prompt_text = self.registry.get(result.prompt_version).template

        analysis_prompt = f"""
        You are an AI prompt engineer. Analyze the following benchmark results and suggest improvements.
        
        CURRENT PROMPT:
        \"\"\"{prompt_text}\"\"\"
        
        PERFORMANCE SUMMARY:
        - Calories MAE: {result.metrics['calories']:.2f} kcal
        - Protein MAE: {result.metrics['protein']:.2f} g
        
        TOP ERRORS:
        {"\n".join(error_summary[:10])}
        
        SUGGESTION:
        Provide a revised version of the prompt that addresses these errors. 
        Focus on the estimation methodology or specific food types that were missed.
        Return ONLY the revised prompt template.
        """

        try:
            from app.services.llm_service import _get_client

            client = _get_client()
            resp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME, messages=[{"role": "user", "content": analysis_prompt}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to suggest improvements: {e}")
            return "Could not generate suggestions."

    async def close(self):
        await self.runner.client.aclose()
