"""Context Builder - Builds context strings from project artifacts for planning phases."""

from pathlib import Path
from typing import Optional

from pm.core.artifact import ArtifactManager
from pm.models.artifact import Feature, Requirement
from pm.models.planner import (
    CodebaseAnalysis,
    GroupDefinition,
    LayerDefinition,
    TechStack,
)
from pm.storage.files import read_frontmatter_file, read_yaml_file


class ContextBuilder:
    """Builds context strings from artifacts for each planning phase.

    This class loads project artifacts and constructs the context strings
    that are passed to each planning phase. Each phase receives only the
    context it needs from file artifacts, not conversation history.
    """

    def __init__(self, project_path: Path):
        """Initialize the context builder.

        Args:
            project_path: Path to the project root.
        """
        self.project_path = project_path
        self.planning_dir = project_path / "planning"
        self.docs_dir = project_path / "docs"
        self.tech_docs_dir = self.docs_dir / "tech"
        self.artifact_manager = ArtifactManager(project_path)

    # --- PRD Loading ---

    def load_prd(self) -> str:
        """Load the PRD content.

        Returns:
            PRD content as string, or empty string if not found.
        """
        prd_path = self.project_path / "PRD.md"
        if not prd_path.exists():
            # Try alternate location
            prd_path = self.docs_dir / "PRD.md"

        if prd_path.exists():
            return prd_path.read_text()

        return ""

    # --- Feature/Requirement Loading ---

    def load_features(self) -> list[Feature]:
        """Load all features."""
        return self.artifact_manager.list_features()

    def load_requirements(self) -> list[Requirement]:
        """Load all requirements."""
        return self.artifact_manager.list_requirements()

    def format_features_for_context(self, features: list[Feature]) -> str:
        """Format features as context string."""
        if not features:
            return "No features defined yet."

        lines = ["## Features\n"]
        for feature in features:
            lines.append(f"### {feature.id}: {feature.title}")
            lines.append(f"Priority: {feature.priority.value} | Status: {feature.status.value}")
            if feature.description:
                lines.append(f"\n{feature.description}")
            if feature.acceptance_criteria:
                lines.append("\nAcceptance Criteria:")
                for criterion in feature.acceptance_criteria:
                    lines.append(f"  - {criterion}")
            lines.append("")

        return "\n".join(lines)

    def format_requirements_for_context(self, requirements: list[Requirement]) -> str:
        """Format requirements as context string."""
        if not requirements:
            return "No requirements defined yet."

        functional = [r for r in requirements if r.is_functional]
        non_functional = [r for r in requirements if not r.is_functional]

        lines = ["## Requirements\n"]

        if functional:
            lines.append("### Functional Requirements\n")
            for req in functional:
                lines.append(f"**{req.id}: {req.title}**")
                lines.append(f"Priority: {req.priority.value}")
                if req.description:
                    lines.append(f"{req.description}")
                if req.feature:
                    lines.append(f"Feature: {req.feature}")
                lines.append("")

        if non_functional:
            lines.append("### Non-Functional Requirements\n")
            for req in non_functional:
                lines.append(f"**{req.id}: {req.title}**")
                lines.append(f"Priority: {req.priority.value}")
                if req.description:
                    lines.append(f"{req.description}")
                lines.append("")

        return "\n".join(lines)

    # --- Planning Artifact Loading ---

    def load_tech_stack(self) -> Optional[TechStack]:
        """Load the tech stack definition."""
        tech_stack_path = self.planning_dir / "tech-stack.yaml"
        if not tech_stack_path.exists():
            return None

        data = read_yaml_file(tech_stack_path)
        return TechStack.from_dict(data)

    def load_layers(self) -> Optional[LayerDefinition]:
        """Load the layers definition."""
        layers_path = self.planning_dir / "layers.yaml"
        if not layers_path.exists():
            return None

        data = read_yaml_file(layers_path)
        return LayerDefinition.from_dict(data)

    def load_groups(self, layer_id: str) -> Optional[GroupDefinition]:
        """Load the groups definition for a layer."""
        groups_path = self.planning_dir / "groups" / layer_id / "groups.yaml"
        if not groups_path.exists():
            return None

        data = read_yaml_file(groups_path)
        return GroupDefinition.from_dict(data)

    def load_codebase_analysis(self) -> Optional[CodebaseAnalysis]:
        """Load codebase analysis for brownfield projects."""
        analysis_path = self.planning_dir / "codebase-analysis.yaml"
        if not analysis_path.exists():
            return None

        data = read_yaml_file(analysis_path)
        return CodebaseAnalysis.from_dict(data)

    # --- Tech Documentation Loading ---

    def load_tech_docs(self, tech_names: list[str]) -> dict[str, str]:
        """Load summarized tech documentation.

        Args:
            tech_names: List of technology names (e.g., ["hono", "drizzle"]).

        Returns:
            Dict mapping tech name to documentation summary.
        """
        docs = {}
        for tech_name in tech_names:
            doc_path = self.tech_docs_dir / tech_name / "summary.md"
            if doc_path.exists():
                docs[tech_name] = doc_path.read_text()
        return docs

    def format_tech_docs_for_context(self, tech_docs: dict[str, str]) -> str:
        """Format tech documentation as context string."""
        if not tech_docs:
            return ""

        lines = ["## Technology Documentation\n"]
        for tech_name, content in tech_docs.items():
            lines.append(f"### {tech_name}\n")
            lines.append(content)
            lines.append("")

        return "\n".join(lines)

    # --- Context Building Methods ---

    def build_architect_context(
        self,
        codebase_analysis: Optional[CodebaseAnalysis] = None,
    ) -> str:
        """Build context for the Technical Architect phase.

        Args:
            codebase_analysis: Optional analysis for brownfield projects.

        Returns:
            Complete context string for the architect phase.
        """
        sections = []

        # PRD
        prd = self.load_prd()
        if prd:
            sections.append("# Product Requirements Document\n")
            sections.append(prd)
            sections.append("")

        # Features
        features = self.load_features()
        sections.append(self.format_features_for_context(features))

        # Requirements
        requirements = self.load_requirements()
        sections.append(self.format_requirements_for_context(requirements))

        # Codebase analysis (brownfield)
        if codebase_analysis:
            sections.append("# Existing Codebase Analysis\n")
            sections.append(f"Language: {codebase_analysis.detected_language}")
            sections.append(f"Framework: {codebase_analysis.detected_framework}")
            sections.append(f"Package Manager: {codebase_analysis.package_manager}")

            if codebase_analysis.existing_dependencies:
                sections.append("\n## Existing Dependencies")
                for dep in codebase_analysis.existing_dependencies:
                    sections.append(f"- {dep.name}@{dep.version}: {dep.purpose}")

            if codebase_analysis.patterns:
                sections.append("\n## Existing Patterns")
                for pattern in codebase_analysis.patterns:
                    sections.append(f"- **{pattern.name}**: {pattern.description}")

            if codebase_analysis.constraints:
                sections.append("\n## Constraints")
                for constraint in codebase_analysis.constraints:
                    sections.append(f"- {constraint}")

            sections.append("")

        return "\n".join(sections)

    def build_layer_context(self, layer_id: str) -> str:
        """Build context for the Layer Planner phase.

        Args:
            layer_id: ID of the layer being planned.

        Returns:
            Complete context string for layer planning.
        """
        sections = []

        # Tech stack
        tech_stack = self.load_tech_stack()
        if tech_stack:
            sections.append("# Tech Stack\n")
            if tech_stack.runtime:
                sections.append(f"Language: {tech_stack.runtime.language} {tech_stack.runtime.version}")
            for fw_name, fw_config in tech_stack.frameworks.items():
                sections.append(f"{fw_name.title()}: {fw_config.name} {fw_config.version}")
            if tech_stack.database:
                sections.append(f"Database: {tech_stack.database.type} {tech_stack.database.version}")
                if tech_stack.database.orm:
                    sections.append(f"ORM: {tech_stack.database.orm} {tech_stack.database.orm_version}")
            sections.append("")

        # Layers definition
        layers = self.load_layers()
        if layers:
            sections.append("# Architecture Layers\n")
            sections.append(f"Summary: {layers.architect_summary}\n")

            # Current layer details
            current_layer = layers.get_layer(layer_id)
            if current_layer:
                sections.append(f"## Current Layer: {current_layer.name}\n")
                sections.append(f"Order: {current_layer.order}")
                sections.append(f"Description: {current_layer.description}")

                if current_layer.responsibilities:
                    sections.append("\nResponsibilities:")
                    for resp in current_layer.responsibilities:
                        sections.append(f"  - {resp}")

                if current_layer.outputs:
                    sections.append("\nOutput Directories:")
                    for output in current_layer.outputs:
                        sections.append(f"  - {output}")

                if current_layer.depends_on:
                    sections.append(f"\nDependencies: {', '.join(current_layer.depends_on)}")

            # Other layers (for context)
            sections.append("\n## All Layers\n")
            for layer in layers.layers:
                marker = ">>> " if layer.id == layer_id else "    "
                sections.append(f"{marker}{layer.id}: {layer.name} (order: {layer.order})")

            sections.append("")

        # Tech documentation for relevant technologies
        if tech_stack:
            tech_names = self._get_tech_names_from_stack(tech_stack)
            tech_docs = self.load_tech_docs(tech_names)
            if tech_docs:
                sections.append(self.format_tech_docs_for_context(tech_docs))

        return "\n".join(sections)

    def build_group_context(self, layer_id: str, group_id: str) -> str:
        """Build context for the Group Planner phase.

        Args:
            layer_id: ID of the layer containing the group.
            group_id: ID of the group being planned.

        Returns:
            Complete context string for group planning.
        """
        sections = []

        # Group definition
        groups = self.load_groups(layer_id)
        if groups:
            sections.append(f"# Layer: {groups.layer_name}\n")

            current_group = groups.get_group(group_id)
            if current_group:
                sections.append(f"## Current Group: {current_group.name}\n")
                sections.append(f"Description: {current_group.description}")
                sections.append(f"Estimated Tasks: {current_group.estimated_tasks}")

                if current_group.depends_on_groups:
                    sections.append(f"\nDepends on groups: {', '.join(current_group.depends_on_groups)}")

                if current_group.contracts:
                    sections.append("\n### Contracts to Define")
                    if current_group.contracts.exports:
                        sections.append("\nExports:")
                        for export in current_group.contracts.exports:
                            sections.append(f"  - {export.name}: {export.type} ({export.file})")

                    if current_group.contracts.interfaces:
                        sections.append("\nInterfaces:")
                        for interface in current_group.contracts.interfaces:
                            sections.append(f"  - {interface.name}")
                            for method in interface.methods:
                                sections.append(f"      {method}")

            # Dependent group contracts (interfaces only)
            sections.append("\n## Dependent Group Contracts\n")
            for dep_group_id in current_group.depends_on_groups if current_group else []:
                dep_group = groups.get_group(dep_group_id)
                if dep_group and dep_group.contracts:
                    sections.append(f"### From {dep_group.name}")
                    if dep_group.contracts.interfaces:
                        for interface in dep_group.contracts.interfaces:
                            sections.append(f"```typescript")
                            sections.append(f"interface {interface.name} {{")
                            for method in interface.methods:
                                sections.append(f"  {method}")
                            sections.append(f"}}")
                            sections.append(f"```")

            sections.append("")

        # Tech stack for reference
        tech_stack = self.load_tech_stack()
        if tech_stack:
            sections.append("# Tech Stack Reference\n")
            if tech_stack.runtime:
                sections.append(f"Language: {tech_stack.runtime.language} {tech_stack.runtime.version}")
            for fw_name, fw_config in tech_stack.frameworks.items():
                sections.append(f"{fw_name.title()}: {fw_config.name} {fw_config.version}")
            sections.append("")

            # Relevant tech docs
            tech_names = self._get_tech_names_from_stack(tech_stack)
            tech_docs = self.load_tech_docs(tech_names)
            if tech_docs:
                sections.append(self.format_tech_docs_for_context(tech_docs))

        return "\n".join(sections)

    def _get_tech_names_from_stack(self, tech_stack: TechStack) -> list[str]:
        """Extract technology names from tech stack for doc lookup."""
        names = []

        for fw_config in tech_stack.frameworks.values():
            names.append(fw_config.name.lower())

        if tech_stack.database and tech_stack.database.orm:
            names.append(tech_stack.database.orm.lower())

        if tech_stack.testing:
            if tech_stack.testing.unit:
                names.append(tech_stack.testing.unit.lower())
            if tech_stack.testing.e2e:
                names.append(tech_stack.testing.e2e.lower())

        for dep in tech_stack.dependencies:
            # Only include major dependencies
            names.append(dep.name.lower().replace("@", "").split("/")[-1])

        return list(set(names))  # Deduplicate

    # --- Utility Methods ---

    def get_available_artifacts_summary(self) -> dict:
        """Get a summary of available artifacts for planning.

        Returns:
            Dict with counts and status of available artifacts.
        """
        features = self.load_features()
        requirements = self.load_requirements()
        tech_stack = self.load_tech_stack()
        layers = self.load_layers()

        return {
            "prd_exists": bool(self.load_prd()),
            "feature_count": len(features),
            "requirement_count": len(requirements),
            "tech_stack_defined": tech_stack is not None,
            "layers_defined": layers is not None,
            "layer_count": len(layers.layers) if layers else 0,
        }
