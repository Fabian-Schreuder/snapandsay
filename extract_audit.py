import json
import csv
from pathlib import Path
import sys
# Add backend to path so we can import from app
sys.path.append(str(Path("backend").resolve()))
from app.benchmarking.nutrition5k_loader import Nutrition5kLoader

def main():
    if len(sys.argv) > 1:
        experiment_file = Path(sys.argv[1])
    else:
        # Find the latest experiment run or use the checkpoint
        experiment_file = Path("benchmark_output/benchmark_checkpoint.json")

    if not experiment_file.exists():
        print(f"File {experiment_file} not found.")
        return

    print(f"Analyzing {experiment_file}...")
    with open(experiment_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit_data = []
    
    loader = Nutrition5kLoader()
    # load all dishes
    all_dishes = loader.load_dishes()
    dishes_map = {d.dish_id: d for d in all_dishes}

    results = data.get("results", [])
    
    for dish_result in results:
        dish_id = dish_result.get("dish_id", "unknown")
        history = dish_result.get("clarification_history", [])
        
        dish = dishes_map.get(dish_id)
        gt_ingredients = json.dumps([ig.model_dump() for ig in dish.ingredients]) if dish else "Unknown"
        
        for qna in history:
            audit_data.append({
                "dish_id": dish_id,
                "question": qna.get("question", ""),
                "parsed_intent": qna.get("intent", ""),
                "entity": qna.get("entity", ""),
                "oracle_answer": qna.get("answer", ""),
                "ground_truth_ingredients": gt_ingredients,
                "review_grade": "", # To be filled manually
                "review_notes": ""
            })

    output_file = Path("benchmark_output/oracle_audit.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    csv_file = Path("benchmark_output/oracle_audit.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        if audit_data:
            writer = csv.DictWriter(f, fieldnames=audit_data[0].keys())
            writer.writeheader()
            writer.writerows(audit_data)

    print(f"Extracted {len(audit_data)} Q&A pairs to {output_file} and {csv_file}")
    
    # Review sample
    print(f"\n--- SAMPLE OF {min(5, len(audit_data))} Q&A PAIRS ---\n")
    for row in audit_data[:5]:
        print(f"Dish: {row['dish_id']}")
        print(f"Q: {row['question']}")
        print(f"Oracle A: {row['oracle_answer']}")
        print(f"Ground Truth: {row['ground_truth_ingredients']}")
        print("-" * 40)

if __name__ == "__main__":
    main()
