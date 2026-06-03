from dataclasses import dataclass, field
from typing import List

@dataclass
class Risk:
    severity: str
    description: str

@dataclass
class PRSummary:
    pr_number: int
    repo: str
    title: str
    summary: str
    risks: List[Risk] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)