"""
skill_registry.py — Central registry for all skills.

Skills self-register here at import time.
The AgentExecutor and AgentPlanner use this registry to:
  - List available skills (shown to LLM during planning)
  - Look up a skill by name (during execution)
  - Search skills by tag or keyword (during planning)
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.skills.base_skill import BaseSkill


class SkillRegistry:
    """
    Singleton skill registry.

    Usage:
        registry = SkillRegistry.instance()
        registry.register(MySkill())
        skill = registry.get("my_skill")
    """

    _instance: "SkillRegistry | None" = None

    def __new__(cls) -> "SkillRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills: dict[str, "BaseSkill"] = {}
        return cls._instance

    # ── registration ─────────────────────────────────────────────────────

    def register(self, skill: "BaseSkill") -> None:
        """Register a skill instance."""
        name = skill.descriptor.name
        self._skills[name] = skill

    def unregister(self, name: str) -> None:
        self._skills.pop(name, None)

    # ── lookup ───────────────────────────────────────────────────────────

    def get(self, name: str) -> "BaseSkill | None":
        """Retrieve a skill by exact name."""
        return self._skills.get(name)

    def get_or_raise(self, name: str) -> "BaseSkill":
        skill = self.get(name)
        if skill is None:
            available = ", ".join(self._skills.keys()) or "none"
            raise KeyError(
                f"Skill '{name}' not found. Available skills: {available}"
            )
        return skill

    # ── discovery ────────────────────────────────────────────────────────

    def list_all(self) -> list["BaseSkill"]:
        """Return all registered skills."""
        return list(self._skills.values())

    def list_names(self) -> list[str]:
        return list(self._skills.keys())

    def search(self, query: str) -> list["BaseSkill"]:
        """
        Find skills that match a keyword in name, description, or tags.
        Used by the AgentPlanner to pick the right tool for a step.
        """
        query_lower = query.lower()
        matches = []
        for skill in self._skills.values():
            d = skill.descriptor
            if (
                query_lower in d.name.lower()
                or query_lower in d.description.lower()
                or any(query_lower in tag.lower() for tag in d.tags)
            ):
                matches.append(skill)
        return matches

    def describe_all(self) -> str:
        """
        Return a formatted description of all skills for injection into LLM prompts.
        """
        if not self._skills:
            return "No skills available."

        lines = ["Available skills:"]
        for skill in self._skills.values():
            d = skill.descriptor
            params = ", ".join(
                f"{k}: {v.get('type', 'any')}"
                for k, v in d.parameters.items()
            )
            lines.append(
                f"  - {d.name}({params}): {d.description}"
            )
        return "\n".join(lines)

    # ── dynamic loading ──────────────────────────────────────────────────

    def load_from_package(self, package_name: str = "app.skills") -> int:
        """
        Auto-discover and import all modules in the given package.
        Skills with `AUTO_REGISTER = True` will register themselves on import.
        Returns the number of modules loaded.
        """
        try:
            package = importlib.import_module(package_name)
            count = 0
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                if module_name.startswith("_"):
                    continue
                importlib.import_module(f"{package_name}.{module_name}")
                count += 1
            return count
        except Exception as e:
            print(f"[SkillRegistry] Warning: could not auto-load {package_name}: {e}")
            return 0

    def __len__(self):
        return len(self._skills)

    def __repr__(self):
        return f"<SkillRegistry: {self.list_names()}>"
