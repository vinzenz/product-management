"""Artifact data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ArtifactStatus(str, Enum):
    """Status for trackable artifacts."""

    DRAFT = "draft"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"


class Priority(str, Enum):
    """MoSCoW priority levels."""

    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


@dataclass
class Feature:
    """A product feature."""

    id: str
    title: str
    description: str = ""
    status: ArtifactStatus = ArtifactStatus.DRAFT
    priority: Priority = Priority.SHOULD
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    requirements: list[str] = field(default_factory=list)
    user_stories: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_frontmatter(self) -> dict:
        """Convert to YAML frontmatter dict."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "requirements": self.requirements,
        }

    def to_markdown(self) -> str:
        """Generate markdown body."""
        lines = [
            f"# {self.title}",
            "",
            "## Description",
            "",
            self.description or "[Feature description]",
            "",
            "## User Stories",
            "",
            self.user_stories or "[User stories]",
            "",
            "## Acceptance Criteria",
            "",
        ]
        if self.acceptance_criteria:
            for criterion in self.acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
        else:
            lines.append("- [ ] [Criterion 1]")
        return "\n".join(lines)

    @classmethod
    def from_frontmatter(cls, frontmatter: dict, content: str) -> "Feature":
        """Create from parsed frontmatter and markdown content."""
        return cls(
            id=frontmatter["id"],
            title=frontmatter["title"],
            description=_extract_section(content, "Description"),
            status=ArtifactStatus(frontmatter.get("status", "draft")),
            priority=Priority(frontmatter.get("priority", "should")),
            created=datetime.fromisoformat(frontmatter["created"]),
            updated=datetime.fromisoformat(frontmatter["updated"]),
            requirements=frontmatter.get("requirements", []),
            user_stories=_extract_section(content, "User Stories"),
            acceptance_criteria=_extract_checklist(content, "Acceptance Criteria"),
        )


@dataclass
class Requirement:
    """A functional or non-functional requirement."""

    id: str
    title: str
    description: str = ""
    rationale: str = ""
    status: ArtifactStatus = ArtifactStatus.DRAFT
    priority: Priority = Priority.SHOULD
    feature: Optional[str] = None
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    tasks: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    is_functional: bool = True

    def to_frontmatter(self) -> dict:
        """Convert to YAML frontmatter dict."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "feature": self.feature,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "tasks": self.tasks,
        }

    def to_markdown(self) -> str:
        """Generate markdown body."""
        lines = [
            f"# {self.title}",
            "",
            "## Description",
            "",
            self.description or "[Requirement description]",
            "",
            "## Rationale",
            "",
            self.rationale or "[Why this requirement exists]",
            "",
            "## Acceptance Criteria",
            "",
        ]
        if self.acceptance_criteria:
            for criterion in self.acceptance_criteria:
                lines.append(f"- [ ] {criterion}")
        else:
            lines.append("- [ ] [Criterion 1]")
        return "\n".join(lines)

    @classmethod
    def from_frontmatter(cls, frontmatter: dict, content: str, is_functional: bool = True) -> "Requirement":
        """Create from parsed frontmatter and markdown content."""
        return cls(
            id=frontmatter["id"],
            title=frontmatter["title"],
            description=_extract_section(content, "Description"),
            rationale=_extract_section(content, "Rationale"),
            status=ArtifactStatus(frontmatter.get("status", "draft")),
            priority=Priority(frontmatter.get("priority", "should")),
            feature=frontmatter.get("feature"),
            created=datetime.fromisoformat(frontmatter["created"]),
            updated=datetime.fromisoformat(frontmatter["updated"]),
            tasks=frontmatter.get("tasks", []),
            acceptance_criteria=_extract_checklist(content, "Acceptance Criteria"),
            is_functional=is_functional,
        )


def _extract_section(content: str, section_name: str) -> str:
    """Extract content under a ## heading."""
    lines = content.split("\n")
    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == f"## {section_name}"
        elif in_section:
            section_lines.append(line)

    return "\n".join(section_lines).strip()


def _extract_checklist(content: str, section_name: str) -> list[str]:
    """Extract checklist items from a section."""
    section = _extract_section(content, section_name)
    items = []
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("- [ ] ") or line.startswith("- [x] "):
            items.append(line[6:])
    return items
