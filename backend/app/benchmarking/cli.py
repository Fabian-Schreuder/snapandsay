import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from app.benchmarking.nutrition5k_loader import Nutrition5kLoader
from app.benchmarking.oracle_runner import OracleRunner

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main_async(args):
    # 1. Load Data
    logger.info("Initializing Loader...")
    loader = Nutrition5kLoader()

    logger.info(f"Loading dishes (Limit: {args.limit}, Complexity: {args.complexity}, Seed: {args.seed})")
    dishes = loader.load_dishes(seed=args.seed, complexity=args.complexity, limit=args.limit)

    if not dishes:
        logger.error("No dishes loaded. Ensure you have run 'scripts/download_nutrition5k.py' successfully.")
        sys.exit(1)

    logger.info(f"Loaded {len(dishes)} dishes for benchmarking.")

    # 2. Init Runner
    runner = OracleRunner(
        api_url=args.api_url, email=args.email, password=args.password, max_turns=args.max_turns
    )

    # 3. Login
    try:
        logger.info(f"Logging in as {args.email} to {args.api_url}...")
        await runner.login()
    except Exception as e:
        logger.error(f"Login failed: {e}")
        await runner.close()
        sys.exit(1)

    # 4. Run Loop
    results = []

    try:
        for i, dish in enumerate(dishes):
            logger.info(f"--- Processing {i+1}/{len(dishes)}: {dish.dish_id} ---")
            result = await runner.run_dish(dish)
            results.append(result)

            if result["success"]:
                logger.info(f"SUCCESS: {dish.dish_id} (Turns: {result['turns']})")
                if result.get("final_data"):
                    logger.info(f"  Title: {result['final_data'].get('title')}")
            else:
                logger.error(f"FAILURE: {dish.dish_id} - {result.get('error')}")

            # Brief pause
            await asyncio.sleep(1)

    finally:
        await runner.close()

    # 5. Report
    success_count = sum(1 for r in results if r["success"])
    total = len(results)

    print("\n=== Benchmarking Summary ===")
    print(f"Total: {total}")
    print(f"Success: {success_count}")
    print(f"Failure: {total - success_count}")
    if total > 0:
        print(f"Success Rate: {success_count/total:.1%}")

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = Path(f"benchmark_results_{ts}.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to {out_file.absolute()}")


def main():
    parser = argparse.ArgumentParser(description="Snap and Say Oracle Benchmark")
    parser.add_argument("--limit", type=int, default=10, help="Number of dishes to test")
    parser.add_argument(
        "--complexity", type=str, default="simple", choices=["simple", "complex"], help="Dish complexity"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for selection")
    parser.add_argument(
        "--api-url", type=str, default=os.getenv("API_URL", "http://localhost:8000"), help="Backend API URL"
    )

    # Optional here, checked in code
    parser.add_argument("--email", type=str, help="Test user email (or ENV: TEST_EMAIL)")
    parser.add_argument("--password", type=str, help="Test user password (or ENV: TEST_PASSWORD)")
    parser.add_argument("--max-turns", type=int, default=3, help="Max clarification turns")

    args = parser.parse_args()

    # Env fallback
    if not args.email:
        args.email = os.getenv("TEST_EMAIL")
    if not args.password:
        args.password = os.getenv("TEST_PASSWORD")

    if not args.email or not args.password:
        parser.error(
            "Email and password are required. Provide via --email/--password or "
            "TEST_EMAIL/TEST_PASSWORD env vars."
        )

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
