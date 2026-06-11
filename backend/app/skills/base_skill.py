"""
base_skill.py — Foundation for the Skills Framework.

A Skill is a self-describing, versioned, executable capability.
Each skill carries its own descriptor so the system can discover,
search, and dynamically load capabilities at runtime.
"""

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillDescriptor:
    """
    Metadata that fully describes a skill.

    The descriptor is what the Agent Planner and Executor use to
    decide which skill to invoke for a given sub-task.
    """
    name: str                          # unique identifier, e.g. "web_search"
    description: str                   # what the skill does (shown to LLM)
    parameters: dict                   # JSON-Schema style parameter definition
    return_type: str = "str"           # expected return type description
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)  # e.g. ["search", "web"]
    author: str = "system"
    is_safe: bool = True               # False = requires extra guardrail checks


class BaseSkill(abc.ABC):
    """
    Abstract base class for all skills.

    Every skill must:
      1. Define a `descriptor` class attribute
      2. Implement `execute(**kwargs) -> Any`
    """

    descriptor: SkillDescriptor  # must be defined by subclass

    @abc.abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Run the skill with the given keyword arguments.

        Arguments should match the keys defined in descriptor.parameters.
        Returns a string result (or raises on unrecoverable failure).
        """
        ...

    def safe_execute(self, **kwargs) -> str:
        """
        Execute with error handling — always returns a string, never raises.
        Agents use this to get graceful error messages.
        """
        try:
            result = self.execute(**kwargs)
            return str(result)
        except Exception as e:
            return f"[{self.descriptor.name} error]: {type(e).__name__}: {e}"

    def __repr__(self):
        return f"<Skill: {self.descriptor.name} v{self.descriptor.version}>"
