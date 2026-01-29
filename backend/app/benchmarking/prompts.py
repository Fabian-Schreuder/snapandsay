from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class PromptVersion:
    id: str
    name: str
    description: str
    template: str
    parent_id: str | None = None


class PromptRegistry:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def get(self, version_id: str) -> PromptVersion | None:
        """Get a prompt version by ID."""
        for file in self.prompts_dir.glob("*.yaml"):
            with open(file) as f:
                data = yaml.safe_load(f)
                if data.get("id") == version_id:
                    return PromptVersion(**data)
        return None

    def list_all(self) -> list[PromptVersion]:
        """List all available prompt versions."""
        prompts = []
        for file in self.prompts_dir.glob("*.yaml"):
            with open(file) as f:
                data = yaml.safe_load(f)
                prompts.append(PromptVersion(**data))
        return sorted(prompts, key=lambda p: p.id)

    def save(self, prompt: PromptVersion) -> None:
        """Save a new prompt version."""
        filename = f"{prompt.id}_{prompt.name.replace(' ', '_').lower()}.yaml"
        file_path = self.prompts_dir / filename
        data = {
            "id": prompt.id,
            "name": prompt.name,
            "description": prompt.description,
            "template": prompt.template,
        }
        if prompt.parent_id:
            data["parent_id"] = prompt.parent_id

        with open(file_path, "w") as f:
            yaml.dump(data, f, sort_keys=False)
