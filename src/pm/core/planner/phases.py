"""Planning Phases - Phase runners for each stage of multi-phase planning."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Optional

from pm.core.conversation import ConversationManager
from pm.core.planner.context import ContextBuilder
from pm.models.persona import Persona, Specialization
from pm.models.planner import (
    CodebaseAnalysis,
    Group,
    GroupContract,
    GroupDefinition,
    Layer,
    LayerDefinition,
    PlanningPhase,
    TechStack,
    ContractExport,
    ContractInterface,
)
from pm.storage.files import write_yaml_file, ensure_directory


@dataclass
class PhaseOutput:
    """Base output from a planning phase."""

    success: bool
    phase: PlanningPhase
    message: str = ""
    artifacts: list[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class ArchitectOutput(PhaseOutput):
    """Output from the Technical Architect phase."""

    tech_stack: Optional[TechStack] = None
    layers: Optional[LayerDefinition] = None


@dataclass
class LayerOutput(PhaseOutput):
    """Output from the Layer Planner phase."""

    layer_id: str = ""
    groups: Optional[GroupDefinition] = None


@dataclass
class GroupOutput(PhaseOutput):
    """Output from the Group Planner phase."""

    group_id: str = ""
    task_ids: list[str] = field(default_factory=list)


class PhaseRunner(ABC):
    """Base class for planning phases.

    Each phase creates a fresh conversation context, loads relevant
    artifacts, runs the planning conversation, and saves outputs.
    """

    # Default model for planning phases
    DEFAULT_MODEL = "claude"

    def __init__(
        self,
        project_path: Path,
        model: str = DEFAULT_MODEL,
        prompt_path: Optional[Path] = None,
    ):
        """Initialize the phase runner.

        Args:
            project_path: Path to the project root.
            model: Model to use for this phase.
            prompt_path: Path to the phase-specific prompt file.
        """
        self.project_path = project_path
        self.model = model
        self.prompt_path = prompt_path
        self.context_builder = ContextBuilder(project_path)
        self.planning_dir = project_path / "planning"
        ensure_directory(self.planning_dir)

    def create_fresh_conversation(self) -> ConversationManager:
        """Create a fresh conversation for this phase.

        Returns:
            A new ConversationManager with no history.
        """
        conversation = ConversationManager(model=self.model)

        # Set up persona for this phase
        persona = self._get_phase_persona()
        if persona:
            conversation.set_persona(persona)

        return conversation

    @abstractmethod
    def _get_phase_persona(self) -> Optional[Persona]:
        """Get the persona for this phase."""
        pass

    @abstractmethod
    def _get_phase_prompt(self) -> str:
        """Get the system/task prompt for this phase."""
        pass

    @abstractmethod
    def build_context(self, inputs: dict[str, Any]) -> str:
        """Build context string from artifacts.

        Args:
            inputs: Phase-specific input parameters.

        Returns:
            Context string to include in the prompt.
        """
        pass

    @abstractmethod
    def parse_output(self, response: str) -> PhaseOutput:
        """Parse the LLM response into structured output.

        Args:
            response: Raw LLM response text.

        Returns:
            Parsed phase output.
        """
        pass

    @abstractmethod
    def save_artifacts(self, output: PhaseOutput) -> list[str]:
        """Save phase outputs as artifacts.

        Args:
            output: Parsed phase output.

        Returns:
            List of saved artifact paths.
        """
        pass

    def run(
        self,
        inputs: dict[str, Any],
        interactive: bool = True,
    ) -> Generator[str, Optional[str], PhaseOutput]:
        """Run this planning phase.

        Args:
            inputs: Phase-specific input parameters.
            interactive: Whether to allow interactive Q&A.

        Yields:
            Response chunks as they arrive.

        Returns:
            Parsed phase output after completion.
        """
        # Create fresh conversation
        conversation = self.create_fresh_conversation()

        # Build context from artifacts
        context = self.build_context(inputs)

        # Get phase prompt
        phase_prompt = self._get_phase_prompt()

        # Build the full prompt
        full_prompt = f"{context}\n\n---\n\n{phase_prompt}"

        # Run conversation with streaming
        full_response = ""
        for chunk in conversation.chat_stream(full_prompt):
            full_response += chunk
            yield chunk

        # Parse output
        output = self.parse_output(full_response)
        output.raw_response = full_response

        # Save artifacts
        if output.success:
            output.artifacts = self.save_artifacts(output)

        return output

    def _load_prompt_file(self) -> str:
        """Load prompt from file if available."""
        if self.prompt_path and self.prompt_path.exists():
            return self.prompt_path.read_text()
        return ""


class TechnicalArchitectPhase(PhaseRunner):
    """Technical Architect phase - analyzes requirements and defines architecture."""

    def __init__(self, project_path: Path, model: str = PhaseRunner.DEFAULT_MODEL):
        prompt_path = project_path.parent / "tooling" / "prompts" / "planner" / "architect-phase.md"
        super().__init__(project_path, model, prompt_path)

    def _get_phase_persona(self) -> Optional[Persona]:
        """Get architect persona."""
        return Persona(
            id="planning-architect",
            name="Technical Architect",
            specialization=Specialization.ARCHITECT,
            description="Systematic architect designing scalable systems with clean architecture.",
            expertise=[
                "System architecture",
                "Technology selection",
                "API design",
                "Layer decomposition",
                "Dependency management",
            ],
            perspective="Views the system holistically, planning for scalability and maintainability.",
            tone="Systematic, thorough, security-conscious. Documents decisions clearly.",
            focus_areas=[
                "Technology selection",
                "Architecture layers",
                "API boundaries",
                "Data modeling",
                "Security considerations",
            ],
        )

    def _get_phase_prompt(self) -> str:
        """Get the architect phase prompt."""
        file_prompt = self._load_prompt_file()
        if file_prompt:
            return file_prompt

        return """# Technical Architect Phase

Analyze the provided PRD, features, and requirements to design the system architecture.

## Your Tasks

1. **Select Tech Stack**
   - Choose appropriate technologies (language, frameworks, database, etc.)
   - Select latest stable versions without known CVEs
   - Consider the project requirements and constraints

2. **Define Architecture Layers**
   - Identify 3-5 architecture layers (e.g., Infrastructure, Domain, Application, UI)
   - Define responsibilities for each layer
   - Specify output directories
   - Define layer dependencies (which layers depend on which)

3. **Plan API Contracts**
   - Identify key API boundaries between layers
   - Define contract interfaces at boundaries

## Output Format

Provide your output in the following YAML blocks:

### Tech Stack (tech-stack.yaml)
```yaml
version: "1.0"
project_type: "web_application"  # or "cli_tool", "api_service", etc.

runtime:
  language: "<language>"
  version: "<version>"
  runtime: "<runtime>"  # e.g., "node", "python"
  runtime_version: "<version>"

frameworks:
  backend:
    name: "<framework>"
    version: "<version>"
    docs_url: "<url>"
  frontend:  # if applicable
    name: "<framework>"
    version: "<version>"

database:  # if applicable
  type: "<type>"
  version: "<version>"
  orm: "<orm>"
  orm_version: "<version>"

testing:
  unit: "<framework>"
  e2e: "<framework>"

dependencies:
  - name: "<package>"
    version: "<version>"
    purpose: "<why needed>"

security_notes:
  - "<note about version choices>"
```

### Architecture Layers (layers.yaml)
```yaml
version: "1.0"
architect_summary: |
  <Brief summary of architecture decisions>

layers:
  - id: "layer-01"
    name: "<Layer Name>"
    order: 1
    description: |
      <What this layer does>
    responsibilities:
      - "<responsibility>"
    outputs:
      - "<directory path>"
    depends_on: []

  - id: "layer-02"
    name: "<Layer Name>"
    order: 2
    description: |
      <What this layer does>
    outputs:
      - "<directory path>"
    depends_on: ["layer-01"]
```

Ask clarifying questions if the requirements are ambiguous."""

    def build_context(self, inputs: dict[str, Any]) -> str:
        """Build context for architect phase."""
        codebase_analysis = inputs.get("codebase_analysis")
        return self.context_builder.build_architect_context(codebase_analysis)

    def parse_output(self, response: str) -> ArchitectOutput:
        """Parse architect phase output."""
        import yaml

        output = ArchitectOutput(
            success=False,
            phase=PlanningPhase.ARCHITECT,
        )

        # Extract tech-stack.yaml block
        tech_stack_match = re.search(
            r"```ya?ml\s*\n(version:\s*[\"']1\.0[\"'].*?project_type:.*?)```",
            response,
            re.DOTALL,
        )
        if tech_stack_match:
            try:
                tech_data = yaml.safe_load(tech_stack_match.group(1))
                output.tech_stack = TechStack.from_dict(tech_data)
            except Exception as e:
                output.message = f"Failed to parse tech stack: {e}"
                return output

        # Extract layers.yaml block
        layers_match = re.search(
            r"```ya?ml\s*\n(version:\s*[\"']1\.0[\"'].*?architect_summary:.*?layers:.*?)```",
            response,
            re.DOTALL,
        )
        if layers_match:
            try:
                layers_data = yaml.safe_load(layers_match.group(1))
                output.layers = LayerDefinition.from_dict(layers_data)
            except Exception as e:
                output.message = f"Failed to parse layers: {e}"
                return output

        if output.tech_stack and output.layers:
            output.success = True
            output.message = f"Architecture defined: {len(output.layers.layers)} layers"
        else:
            output.message = "Could not parse architecture output. Expected tech-stack and layers YAML blocks."

        return output

    def save_artifacts(self, output: ArchitectOutput) -> list[str]:
        """Save architect phase artifacts."""
        saved = []

        if output.tech_stack:
            tech_path = self.planning_dir / "tech-stack.yaml"
            write_yaml_file(tech_path, output.tech_stack.to_dict())
            saved.append(str(tech_path))

        if output.layers:
            layers_path = self.planning_dir / "layers.yaml"
            write_yaml_file(layers_path, output.layers.to_dict())
            saved.append(str(layers_path))

        return saved


class LayerPlannerPhase(PhaseRunner):
    """Layer Planner phase - breaks a layer into functional groups."""

    def __init__(self, project_path: Path, model: str = PhaseRunner.DEFAULT_MODEL):
        prompt_path = project_path.parent / "tooling" / "prompts" / "planner" / "layer-planner.md"
        super().__init__(project_path, model, prompt_path)

    def _get_phase_persona(self) -> Optional[Persona]:
        """Get layer planner persona."""
        return Persona(
            id="planning-layer",
            name="Layer Planner",
            specialization=Specialization.ARCHITECT,
            description="Decomposes architecture layers into manageable functional groups.",
            expertise=[
                "Module decomposition",
                "Contract design",
                "Dependency analysis",
                "Interface definition",
            ],
            perspective="Breaks complex layers into cohesive, testable groups.",
            tone="Analytical, methodical, focused on boundaries and contracts.",
            focus_areas=[
                "Group boundaries",
                "Contract interfaces",
                "Execution order",
                "Task estimation",
            ],
        )

    def _get_phase_prompt(self) -> str:
        """Get the layer planner prompt."""
        file_prompt = self._load_prompt_file()
        if file_prompt:
            return file_prompt

        return """# Layer Planner Phase

Break down the specified layer into functional groups that can be implemented independently.

## Your Tasks

1. **Identify Groups**
   - Break the layer into 2-6 functional groups
   - Each group should be cohesive and focused
   - Groups should have clear boundaries

2. **Define Contracts**
   - Specify what each group exports
   - Define interface contracts between groups
   - Identify dependencies between groups

3. **Plan Execution Order**
   - Determine which groups can be done in parallel
   - Define the execution sequence

## Output Format

Provide your output in a YAML block:

```yaml
version: "1.0"
layer_id: "<layer-id>"
layer_name: "<layer name>"

groups:
  - id: "grp-<layer>-01"
    name: "<Group Name>"
    order: 1
    description: "<What this group implements>"
    contracts:
      exports:
        - name: "<exportName>"
          type: "<TypeName>"
          file: "<output file path>"
      interfaces:
        - name: "<InterfaceName>"
          methods:
            - "<method signature>"
    depends_on_groups: []
    estimated_tasks: <number>

  - id: "grp-<layer>-02"
    name: "<Group Name>"
    order: 2
    contracts:
      exports:
        - name: "<exportName>"
          type: "<TypeName>"
          file: "<output file path>"
    depends_on_groups: ["grp-<layer>-01"]
    estimated_tasks: <number>

execution_order:
  - ["grp-<layer>-01"]  # First: independent groups
  - ["grp-<layer>-02", "grp-<layer>-03"]  # Second: can be parallel
```

Ask clarifying questions if needed."""

    def build_context(self, inputs: dict[str, Any]) -> str:
        """Build context for layer planning."""
        layer_id = inputs.get("layer_id", "")
        return self.context_builder.build_layer_context(layer_id)

    def parse_output(self, response: str) -> LayerOutput:
        """Parse layer planner output."""
        import yaml

        output = LayerOutput(
            success=False,
            phase=PlanningPhase.LAYER_PLANNING,
        )

        # Extract groups.yaml block
        groups_match = re.search(
            r"```ya?ml\s*\n(version:\s*[\"']1\.0[\"'].*?layer_id:.*?groups:.*?)```",
            response,
            re.DOTALL,
        )
        if groups_match:
            try:
                groups_data = yaml.safe_load(groups_match.group(1))
                output.groups = GroupDefinition.from_dict(groups_data)
                output.layer_id = groups_data.get("layer_id", "")
                output.success = True
                output.message = f"Layer breakdown: {len(output.groups.groups)} groups"
            except Exception as e:
                output.message = f"Failed to parse groups: {e}"
        else:
            output.message = "Could not parse layer output. Expected groups YAML block."

        return output

    def save_artifacts(self, output: LayerOutput) -> list[str]:
        """Save layer planner artifacts."""
        saved = []

        if output.groups and output.layer_id:
            groups_dir = self.planning_dir / "groups" / output.layer_id
            ensure_directory(groups_dir)
            groups_path = groups_dir / "groups.yaml"
            write_yaml_file(groups_path, output.groups.to_dict())
            saved.append(str(groups_path))

        return saved


class GroupPlannerPhase(PhaseRunner):
    """Group Planner phase - creates executable task files for a group."""

    def __init__(self, project_path: Path, model: str = PhaseRunner.DEFAULT_MODEL):
        prompt_path = project_path.parent / "tooling" / "prompts" / "planner" / "group-planner.md"
        super().__init__(project_path, model, prompt_path)

    def _get_phase_persona(self) -> Optional[Persona]:
        """Get group planner persona."""
        return Persona(
            id="planning-group",
            name="Task Planner",
            specialization=Specialization.ENGINEER,
            description="Creates detailed, executable task specifications.",
            expertise=[
                "Task decomposition",
                "Contract-driven development",
                "Test specification",
                "Implementation planning",
            ],
            perspective="Breaks groups into precise, testable tasks.",
            tone="Precise, thorough, test-focused. Every task must be verifiable.",
            focus_areas=[
                "Task contracts",
                "Test specifications",
                "Verification criteria",
                "Output files",
            ],
        )

    def _get_phase_prompt(self) -> str:
        """Get the group planner prompt."""
        file_prompt = self._load_prompt_file()
        if file_prompt:
            return file_prompt

        return """# Group Planner Phase

Create detailed task files for implementing the specified group.

## Your Tasks

1. **Break Into Tasks**
   - Create 2-8 tasks for this group
   - Each task should be independently executable
   - Tasks should have clear contracts and verification

2. **Define Contracts**
   - Specify exactly what each task exports
   - Reference interface contracts from dependencies
   - Include complete type signatures

3. **Write Test Specs**
   - Write complete, runnable test code
   - Tests should verify the contract
   - Include edge cases

4. **Define Verification**
   - Deterministic commands to verify success
   - Include type checking, tests, lint checks

## Output Format

For each task, provide a markdown block:

```markdown
---
id: T-<NNN>
title: <Task Title>
status: pending
layer: <layer number>
track: <backend|frontend|shared>
depends_on: [<task IDs>]
estimated_complexity: <trivial|simple|medium|complex>
---

# T-<NNN>: <Task Title>

## Contract

```typescript
// Exact exports from this task
export interface <Name> { ... }
export function <name>(...): ... { }
```

## Dependencies (Interfaces Only)

```typescript
// Interface contracts from dependent tasks (DO NOT include implementation)
import { <Interface> } from '<path>';
```

## Test Specification

```typescript
// Complete, runnable test code
import { describe, it, expect } from 'vitest';
import { <exports> } from './<module>';

describe('<module>', () => {
  it('should <behavior>', () => {
    // Arrange
    // Act
    // Assert
  });
});
```

## Output Files

```
WRITE: <path/to/file.ts> (~<N> lines)
WRITE: <path/to/test.ts> (~<N> lines)
```

## Verification (Deterministic)

```bash
# Commands to verify task completion
npx tsc --noEmit
npx vitest run <test file>
```

## Done When

- [ ] <Criterion 1>
- [ ] <Criterion 2>
```

Generate all tasks for this group."""

    def build_context(self, inputs: dict[str, Any]) -> str:
        """Build context for group planning."""
        layer_id = inputs.get("layer_id", "")
        group_id = inputs.get("group_id", "")
        return self.context_builder.build_group_context(layer_id, group_id)

    def parse_output(self, response: str) -> GroupOutput:
        """Parse group planner output."""
        output = GroupOutput(
            success=False,
            phase=PlanningPhase.GROUP_PLANNING,
        )

        # Extract task markdown blocks
        task_pattern = r"```markdown\s*\n(---\s*\nid:\s*T-\d+.*?```)\s*```"
        task_matches = re.findall(task_pattern, response, re.DOTALL)

        if not task_matches:
            # Try alternative pattern without outer markdown fence
            task_pattern = r"(---\s*\nid:\s*T-\d+.*?## Done When\s*\n(?:- \[[ x]\].*\n?)+)"
            task_matches = re.findall(task_pattern, response, re.DOTALL)

        if task_matches:
            for match in task_matches:
                # Extract task ID from frontmatter
                id_match = re.search(r"id:\s*(T-\d+)", match)
                if id_match:
                    output.task_ids.append(id_match.group(1))

            output.success = True
            output.message = f"Created {len(output.task_ids)} tasks"
        else:
            output.message = "Could not parse tasks from output."

        return output

    def save_artifacts(self, output: GroupOutput) -> list[str]:
        """Save task files."""
        # Tasks are typically saved by the orchestrator using the ArtifactManager
        # This method would parse and save individual task files
        # For now, return empty list - orchestrator handles task creation
        return []
