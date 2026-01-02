"""Project data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    IDEATION = "ideation"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEW = "review"
    ARCHIVED = "archived"


@dataclass
class Project:
    """A product management project."""

    id: str
    name: str
    status: ProjectStatus = ProjectStatus.IDEATION
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    git_branch: str = "main"
    target_repo: Optional[Path] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "git_branch": self.git_branch,
            "target_repo": str(self.target_repo) if self.target_repo else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Create from dictionary (YAML deserialization)."""
        return cls(
            id=data["id"],
            name=data["name"],
            status=ProjectStatus(data.get("status", "ideation")),
            created=datetime.fromisoformat(data["created"]),
            updated=datetime.fromisoformat(data["updated"]),
            git_branch=data.get("git_branch", "main"),
            target_repo=Path(data["target_repo"]) if data.get("target_repo") else None,
        )
