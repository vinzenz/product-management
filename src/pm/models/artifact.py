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


class TaskStatus(str, Enum):
    """Status for tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskComplexity(str, Enum):
    """Estimated complexity for tasks."""

    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class TaskTrack(str, Enum):
    """Track/domain for tasks."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    SHARED = "shared"


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


def _extract_code_block(content: str, section_name: str) -> str:
    """Extract code block content from a section."""
    section = _extract_section(content, section_name)
    lines = section.split("\n")
    in_code = False
    code_lines = []

    for line in lines:
        if line.startswith("```"):
            if in_code:
                break
            in_code = True
            continue
        if in_code:
            code_lines.append(line)

    return "\n".join(code_lines)


@dataclass
class Task:
    """A task for autonomous execution."""

    id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    layer: int = 1
    track: TaskTrack = TaskTrack.BACKEND
    depends_on: list[str] = field(default_factory=list)
    estimated_complexity: TaskComplexity = TaskComplexity.MEDIUM
    requirement: Optional[str] = None
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)

    # Contract-driven task content
    contract: str = ""
    dependencies: str = ""
    test_specification: str = ""
    output_files: str = ""
    verification: str = ""
    done_when: list[str] = field(default_factory=list)

    def to_frontmatter(self) -> dict:
        """Convert to YAML frontmatter dict."""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "layer": self.layer,
            "track": self.track.value,
            "depends_on": self.depends_on,
            "estimated_complexity": self.estimated_complexity.value,
            "requirement": self.requirement,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
        }

    def to_markdown(self) -> str:
        """Generate markdown body following contract-driven format."""
        lines = [
            f"# {self.id}: {self.title}",
            "",
            "## Contract",
            "",
            "```typescript",
            self.contract or "// Define exports here",
            "```",
            "",
            "## Dependencies (Interfaces Only)",
            "",
            "```typescript",
            self.dependencies or "// Interface contracts from dependent tasks",
            "```",
            "",
            "## Test Specification",
            "",
            "```typescript",
            self.test_specification or "// Complete, runnable test code",
            "```",
            "",
            "## Output Files",
            "",
            "```",
            self.output_files or "WRITE: path/to/file.ts (~X lines)",
            "```",
            "",
            "## Verification (Deterministic)",
            "",
            "```bash",
            self.verification or "# Commands to verify success",
            "```",
            "",
            "## Done When",
            "",
        ]
        if self.done_when:
            for criterion in self.done_when:
                lines.append(f"- [ ] {criterion}")
        else:
            lines.append("- [ ] [Acceptance criterion]")

        return "\n".join(lines)

    @classmethod
    def from_frontmatter(cls, frontmatter: dict, content: str) -> "Task":
        """Create from parsed frontmatter and markdown content."""
        return cls(
            id=frontmatter["id"],
            title=frontmatter["title"],
            status=TaskStatus(frontmatter.get("status", "pending")),
            layer=frontmatter.get("layer", 1),
            track=TaskTrack(frontmatter.get("track", "backend")),
            depends_on=frontmatter.get("depends_on", []),
            estimated_complexity=TaskComplexity(
                frontmatter.get("estimated_complexity", "medium")
            ),
            requirement=frontmatter.get("requirement"),
            created=datetime.fromisoformat(frontmatter["created"]),
            updated=datetime.fromisoformat(frontmatter["updated"]),
            contract=_extract_code_block(content, "Contract"),
            dependencies=_extract_code_block(content, "Dependencies (Interfaces Only)"),
            test_specification=_extract_code_block(content, "Test Specification"),
            output_files=_extract_code_block(content, "Output Files"),
            verification=_extract_code_block(content, "Verification (Deterministic)"),
            done_when=_extract_checklist(content, "Done When"),
        )
