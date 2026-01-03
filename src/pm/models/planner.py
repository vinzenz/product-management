"""Planner data models for multi-phase planning system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class PlanningPhase(str, Enum):
    """Current phase in the planning process."""

    NOT_STARTED = "not_started"
    ARCHITECT = "architect"
    LAYER_PLANNING = "layer_planning"
    GROUP_PLANNING = "group_planning"
    COMPLETED = "completed"


class CheckpointStatus(str, Enum):
    """Status of a checkpoint."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProjectType(str, Enum):
    """Type of project being planned."""

    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"


# --- Tech Stack Models ---


@dataclass
class Dependency:
    """A project dependency."""

    name: str
    version: str
    purpose: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version, "purpose": self.purpose}

    @classmethod
    def from_dict(cls, data: dict) -> "Dependency":
        return cls(
            name=data["name"],
            version=data["version"],
            purpose=data.get("purpose", ""),
        )


@dataclass
class FrameworkConfig:
    """Configuration for a framework."""

    name: str
    version: str
    docs_url: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "version": self.version, "docs_url": self.docs_url}

    @classmethod
    def from_dict(cls, data: dict) -> "FrameworkConfig":
        return cls(
            name=data["name"],
            version=data["version"],
            docs_url=data.get("docs_url", ""),
        )


@dataclass
class RuntimeConfig:
    """Runtime configuration."""

    language: str
    version: str
    runtime: str = ""
    runtime_version: str = ""

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "version": self.version,
            "runtime": self.runtime,
            "runtime_version": self.runtime_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RuntimeConfig":
        return cls(
            language=data["language"],
            version=data["version"],
            runtime=data.get("runtime", ""),
            runtime_version=data.get("runtime_version", ""),
        )


@dataclass
class DatabaseConfig:
    """Database configuration."""

    type: str
    version: str
    orm: str = ""
    orm_version: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "version": self.version,
            "orm": self.orm,
            "orm_version": self.orm_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DatabaseConfig":
        return cls(
            type=data["type"],
            version=data["version"],
            orm=data.get("orm", ""),
            orm_version=data.get("orm_version", ""),
        )


@dataclass
class TestingConfig:
    """Testing framework configuration."""

    unit: str = ""
    e2e: str = ""
    integration: str = ""

    def to_dict(self) -> dict:
        return {"unit": self.unit, "e2e": self.e2e, "integration": self.integration}

    @classmethod
    def from_dict(cls, data: dict) -> "TestingConfig":
        return cls(
            unit=data.get("unit", ""),
            e2e=data.get("e2e", ""),
            integration=data.get("integration", ""),
        )


@dataclass
class TechStack:
    """Complete tech stack definition."""

    version: str = "1.0"
    created: datetime = field(default_factory=datetime.now)
    project_type: str = "web_application"
    runtime: Optional[RuntimeConfig] = None
    frameworks: dict[str, FrameworkConfig] = field(default_factory=dict)
    database: Optional[DatabaseConfig] = None
    testing: Optional[TestingConfig] = None
    dependencies: list[Dependency] = field(default_factory=list)
    security_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created": self.created.isoformat(),
            "project_type": self.project_type,
            "runtime": self.runtime.to_dict() if self.runtime else None,
            "frameworks": {k: v.to_dict() for k, v in self.frameworks.items()},
            "database": self.database.to_dict() if self.database else None,
            "testing": self.testing.to_dict() if self.testing else None,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "security_notes": self.security_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TechStack":
        return cls(
            version=data.get("version", "1.0"),
            created=datetime.fromisoformat(data["created"]) if "created" in data else datetime.now(),
            project_type=data.get("project_type", "web_application"),
            runtime=RuntimeConfig.from_dict(data["runtime"]) if data.get("runtime") else None,
            frameworks={k: FrameworkConfig.from_dict(v) for k, v in data.get("frameworks", {}).items()},
            database=DatabaseConfig.from_dict(data["database"]) if data.get("database") else None,
            testing=TestingConfig.from_dict(data["testing"]) if data.get("testing") else None,
            dependencies=[Dependency.from_dict(d) for d in data.get("dependencies", [])],
            security_notes=data.get("security_notes", []),
        )


# --- Layer Models ---


@dataclass
class Layer:
    """A layer in the architecture."""

    id: str
    name: str
    order: int
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "description": self.description,
            "responsibilities": self.responsibilities,
            "outputs": self.outputs,
            "depends_on": self.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Layer":
        return cls(
            id=data["id"],
            name=data["name"],
            order=data["order"],
            description=data.get("description", ""),
            responsibilities=data.get("responsibilities", []),
            outputs=data.get("outputs", []),
            depends_on=data.get("depends_on", []),
        )


@dataclass
class LayerDefinition:
    """Complete layers definition from architect phase."""

    version: str = "1.0"
    created: datetime = field(default_factory=datetime.now)
    architect_summary: str = ""
    layers: list[Layer] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created": self.created.isoformat(),
            "architect_summary": self.architect_summary,
            "layers": [layer.to_dict() for layer in self.layers],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LayerDefinition":
        return cls(
            version=data.get("version", "1.0"),
            created=datetime.fromisoformat(data["created"]) if "created" in data else datetime.now(),
            architect_summary=data.get("architect_summary", ""),
            layers=[Layer.from_dict(layer) for layer in data.get("layers", [])],
        )

    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get a layer by ID."""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None


# --- Group Models ---


@dataclass
class ContractExport:
    """An exported contract from a group."""

    name: str
    type: str
    file: str

    def to_dict(self) -> dict:
        return {"name": self.name, "type": self.type, "file": self.file}

    @classmethod
    def from_dict(cls, data: dict) -> "ContractExport":
        return cls(name=data["name"], type=data["type"], file=data["file"])


@dataclass
class InterfaceMethod:
    """A method signature in an interface."""

    signature: str

    def to_dict(self) -> str:
        return self.signature

    @classmethod
    def from_dict(cls, data: str) -> "InterfaceMethod":
        return cls(signature=data)


@dataclass
class ContractInterface:
    """An interface definition in a contract."""

    name: str
    methods: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"name": self.name, "methods": self.methods}

    @classmethod
    def from_dict(cls, data: dict) -> "ContractInterface":
        return cls(name=data["name"], methods=data.get("methods", []))


@dataclass
class GroupContract:
    """Contract definitions for a group."""

    exports: list[ContractExport] = field(default_factory=list)
    interfaces: list[ContractInterface] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "exports": [e.to_dict() for e in self.exports],
            "interfaces": [i.to_dict() for i in self.interfaces],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupContract":
        return cls(
            exports=[ContractExport.from_dict(e) for e in data.get("exports", [])],
            interfaces=[ContractInterface.from_dict(i) for i in data.get("interfaces", [])],
        )


@dataclass
class Group:
    """A group within a layer."""

    id: str
    name: str
    order: int
    description: str = ""
    contracts: Optional[GroupContract] = None
    depends_on_groups: list[str] = field(default_factory=list)
    estimated_tasks: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "order": self.order,
            "description": self.description,
            "contracts": self.contracts.to_dict() if self.contracts else None,
            "depends_on_groups": self.depends_on_groups,
            "estimated_tasks": self.estimated_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        return cls(
            id=data["id"],
            name=data["name"],
            order=data["order"],
            description=data.get("description", ""),
            contracts=GroupContract.from_dict(data["contracts"]) if data.get("contracts") else None,
            depends_on_groups=data.get("depends_on_groups", []),
            estimated_tasks=data.get("estimated_tasks", 0),
        )


@dataclass
class GroupDefinition:
    """Groups definition for a layer."""

    version: str = "1.0"
    layer_id: str = ""
    layer_name: str = ""
    groups: list[Group] = field(default_factory=list)
    execution_order: list[list[str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "groups": [g.to_dict() for g in self.groups],
            "execution_order": self.execution_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupDefinition":
        return cls(
            version=data.get("version", "1.0"),
            layer_id=data.get("layer_id", ""),
            layer_name=data.get("layer_name", ""),
            groups=[Group.from_dict(g) for g in data.get("groups", [])],
            execution_order=data.get("execution_order", []),
        )

    def get_group(self, group_id: str) -> Optional[Group]:
        """Get a group by ID."""
        for group in self.groups:
            if group.id == group_id:
                return group
        return None


# --- Checkpoint Models ---


@dataclass
class Checkpoint:
    """A checkpoint requiring user approval."""

    id: str
    phase: PlanningPhase
    description: str
    status: CheckpointStatus = CheckpointStatus.PENDING
    created: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    feedback: str = ""
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "phase": self.phase.value,
            "description": self.description,
            "status": self.status.value,
            "created": self.created.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "feedback": self.feedback,
            "artifacts": self.artifacts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        return cls(
            id=data["id"],
            phase=PlanningPhase(data["phase"]),
            description=data["description"],
            status=CheckpointStatus(data.get("status", "pending")),
            created=datetime.fromisoformat(data["created"]),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            feedback=data.get("feedback", ""),
            artifacts=data.get("artifacts", []),
        )


# --- Session Models ---


@dataclass
class PlanningSession:
    """A planning session state."""

    id: str
    project_type: ProjectType = ProjectType.GREENFIELD
    current_phase: PlanningPhase = PlanningPhase.NOT_STARTED
    target_repo: Optional[Path] = None
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)

    # Phase progress
    current_layer_id: Optional[str] = None
    current_group_id: Optional[str] = None
    completed_layers: list[str] = field(default_factory=list)
    completed_groups: list[str] = field(default_factory=list)

    # Checkpoints
    checkpoints: list[Checkpoint] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_type": self.project_type.value,
            "current_phase": self.current_phase.value,
            "target_repo": str(self.target_repo) if self.target_repo else None,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
            "current_layer_id": self.current_layer_id,
            "current_group_id": self.current_group_id,
            "completed_layers": self.completed_layers,
            "completed_groups": self.completed_groups,
            "checkpoints": [c.to_dict() for c in self.checkpoints],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanningSession":
        return cls(
            id=data["id"],
            project_type=ProjectType(data.get("project_type", "greenfield")),
            current_phase=PlanningPhase(data.get("current_phase", "not_started")),
            target_repo=Path(data["target_repo"]) if data.get("target_repo") else None,
            created=datetime.fromisoformat(data["created"]),
            updated=datetime.fromisoformat(data["updated"]),
            current_layer_id=data.get("current_layer_id"),
            current_group_id=data.get("current_group_id"),
            completed_layers=data.get("completed_layers", []),
            completed_groups=data.get("completed_groups", []),
            checkpoints=[Checkpoint.from_dict(c) for c in data.get("checkpoints", [])],
        )

    def get_pending_checkpoint(self) -> Optional[Checkpoint]:
        """Get the current pending checkpoint, if any."""
        for checkpoint in self.checkpoints:
            if checkpoint.status == CheckpointStatus.PENDING:
                return checkpoint
        return None

    def add_checkpoint(
        self, phase: PlanningPhase, description: str, artifacts: list[str] | None = None
    ) -> Checkpoint:
        """Add a new checkpoint."""
        checkpoint_id = f"cp-{len(self.checkpoints) + 1:03d}"
        checkpoint = Checkpoint(
            id=checkpoint_id,
            phase=phase,
            description=description,
            artifacts=artifacts or [],
        )
        self.checkpoints.append(checkpoint)
        self.updated = datetime.now()
        return checkpoint


# --- Codebase Analysis Models (for brownfield) ---


@dataclass
class ExistingPattern:
    """A pattern found in the existing codebase."""

    name: str
    description: str
    files: list[str] = field(default_factory=list)
    example: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "files": self.files,
            "example": self.example,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExistingPattern":
        return cls(
            name=data["name"],
            description=data["description"],
            files=data.get("files", []),
            example=data.get("example", ""),
        )


@dataclass
class CodebaseAnalysis:
    """Analysis results for an existing codebase."""

    analyzed_at: datetime = field(default_factory=datetime.now)
    detected_language: str = ""
    detected_framework: str = ""
    package_manager: str = ""
    existing_dependencies: list[Dependency] = field(default_factory=list)
    patterns: list[ExistingPattern] = field(default_factory=list)
    directory_structure: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "detected_language": self.detected_language,
            "detected_framework": self.detected_framework,
            "package_manager": self.package_manager,
            "existing_dependencies": [d.to_dict() for d in self.existing_dependencies],
            "patterns": [p.to_dict() for p in self.patterns],
            "directory_structure": self.directory_structure,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CodebaseAnalysis":
        return cls(
            analyzed_at=datetime.fromisoformat(data["analyzed_at"]) if "analyzed_at" in data else datetime.now(),
            detected_language=data.get("detected_language", ""),
            detected_framework=data.get("detected_framework", ""),
            package_manager=data.get("package_manager", ""),
            existing_dependencies=[Dependency.from_dict(d) for d in data.get("existing_dependencies", [])],
            patterns=[ExistingPattern.from_dict(p) for p in data.get("patterns", [])],
            directory_structure=data.get("directory_structure", {}),
            constraints=data.get("constraints", []),
        )
