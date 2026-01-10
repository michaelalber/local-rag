"""Data models for Aegis MCP responses."""

from dataclasses import dataclass


@dataclass
class ComplianceSearchResult:
    """Result from compliance search."""

    control_id: str
    title: str
    description: str
    framework: str
    relevance_score: float


@dataclass
class ControlDetail:
    """Detailed control information."""

    control_id: str
    title: str
    description: str
    framework: str
    requirements: list[str]
    guidance: str | None = None
