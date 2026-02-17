import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExperimentResult:
    experiment_id: str
    prompt_version: str
    timestamp: str
    metrics: dict[str, Any]
    latency_stats: dict[str, float]
    per_dish_results: list[dict]
    config: dict


class ExperimentLog:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.log_dir / "experiment_history.json"

    def log_experiment(self, result: ExperimentResult) -> None:
        """Log a new experiment result."""
        # Save detailed result to its own file
        detail_file = self.log_dir / f"experiment_{result.experiment_id}.json"
        with open(detail_file, "w") as f:
            json.dump(asdict(result), f, indent=2)

        # Update history summary
        history = self.get_history()
        summary = {
            "experiment_id": result.experiment_id,
            "prompt_version": result.prompt_version,
            "timestamp": result.timestamp,
            "metrics": result.metrics,
            "latency_mean": result.latency_stats.get("mean_seconds", 0),
            "sample_count": len(result.per_dish_results),
        }
        history.append(summary)
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=2)

    def get_history(self) -> list[dict]:
        """Get history of all experiments."""
        if not self.history_file.exists():
            return []
        with open(self.history_file) as f:
            return json.load(f)

    def get_best_prompt(self, metric: str = "calories") -> str | None:
        """Find the prompt version with the lowest MAE for a given metric."""
        history = self.get_history()
        if not history:
            return None

        # Sort by metric value ascending
        valid = [h for h in history if metric in h["metrics"]]
        if not valid:
            return None

        best = min(valid, key=lambda x: x["metrics"][metric])
        return best["prompt_version"]

    def export_markdown(self) -> str:
        """Export experiment history as markdown table."""
        history = self.get_history()
        if not history:
            return "No experiments recorded."

        lines = ["# Experiment History", ""]
        lines.append("| ID | Prompt | Timestamp | Calories MAE | Protein MAE | Latency | Samples |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")

        for h in history:
            m = h["metrics"]
            ts = h["timestamp"][:16]
            cal = m.get("calories")
            prot = m.get("protein")
            cal_str = f"{cal:.1f}" if isinstance(cal, int | float) else "N/A"
            prot_str = f"{prot:.1f}" if isinstance(prot, int | float) else "N/A"
            lat = h.get("latency_mean", 0)
            cnt = h["sample_count"]
            row = [
                h["experiment_id"],
                h["prompt_version"],
                ts,
                cal_str,
                prot_str,
                f"{lat:.1f}s",
                str(cnt),
            ]
            lines.append(f"| {' | '.join(row)} |")

        # Score Comparison section — render if any experiment has per-dish complexity data
        lines.extend(self._build_score_comparison_section())

        return "\n".join(lines)

    def _build_score_comparison_section(self) -> list[str]:
        """Build a score comparison table from the latest experiment's per-dish results."""
        history = self.get_history()
        if not history:
            return []

        # Use the latest experiment
        latest = history[-1]
        latest_id = latest["experiment_id"]
        detail_file = self.log_dir / f"experiment_{latest_id}.json"
        if not detail_file.exists():
            return []

        with open(detail_file) as f:
            data = json.load(f)

        per_dish = data.get("per_dish_results", [])
        rows = []
        for dish in per_dish:
            old_score = dish.get("complexity_score")
            breakdown = dish.get("complexity_breakdown")
            new_score = breakdown.get("score") if breakdown else None
            if old_score is not None or new_score is not None:
                rows.append(
                    {
                        "dish_id": dish.get("dish_id", "?"),
                        "old": f"{old_score:.3f}" if old_score is not None else "N/A",
                        "new": f"{new_score:.3f}" if new_score is not None else "N/A",
                        "factor": breakdown.get("dominant_factor", "N/A") if breakdown else "N/A",
                    }
                )

        if not rows:
            return []

        section = [
            "",
            "## Score Comparison (Old vs New)",
            "",
            f"_Experiment: {latest_id}_",
            "",
            "| Dish ID | Old Score | New Score | Dominant Factor |",
            "| --- | --- | --- | --- |",
        ]
        for r in rows:
            section.append(f"| {r['dish_id']} | {r['old']} | {r['new']} | {r['factor']} |")

        return section
