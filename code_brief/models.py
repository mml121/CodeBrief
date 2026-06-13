from dataclasses import dataclass, field
from typing import List


def normalise_severity(value: str) -> str:
    severity = (value or "LOW").upper()
    if severity in {"MEDIUM", "MID"}:
        return "MED"
    if severity in {"HIGH", "MED", "LOW"}:
        return severity
    return "LOW"


@dataclass
class Risk:
    severity: str
    confidence: int
    description: str

@dataclass
class PRSummary:
    pr_number: int
    repo: str
    title: str
    summary: str
    risks: List[Risk] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)
