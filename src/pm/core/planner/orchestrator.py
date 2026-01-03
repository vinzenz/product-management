"""Planner Orchestrator - Coordinates multi-phase planning process."""

from datetime import datetime
from pathlib import Path
from typing import Generator, Optional
from uuid import uuid4

from pm.core.planner.checkpoints import CheckpointManager
from pm.core.planner.context import ContextBuilder
from pm.core.planner.docs_fetcher import DocsFetcher
from pm.core.planner.phases import (
    ArchitectOutput,
    GroupOutput,
    GroupPlannerPhase,
    LayerOutput,
    LayerPlannerPhase,
    PhaseOutput,
    TechnicalArchitectPhase,
)
from pm.models.planner import (
    CheckpointStatus,
    CodebaseAnalysis,
    PlanningPhase,
    PlanningSession,
    ProjectType,
)
from pm.storage.files import ensure_directory


class PlannerOrchestrator:
    """Orchestrates the multi-phase planning process.

    Coordinates the Technical Architect, Layer Planner, and Group Planner
    phases, managing checkpoints and session state between iterations.
    """

    # Default model for planning
    DEFAULT_MODEL = "claude"

    def __init__(
        self,
        project_path: Path,
        model: str = DEFAULT_MODEL,
    ):
        """Initialize the planner orchestrator.

        Args:
            project_path: Path to the project root.
            model: Model to use for planning phases.
        """
        self.project_path = project_path
        self.model = model
        self.planning_dir = project_path / "planning"
        ensure_directory(self.planning_dir)

        self.checkpoint_manager = CheckpointManager(project_path)
        self.context_builder = ContextBuilder(project_path)
        self.docs_fetcher = DocsFetcher(project_path)

        self._session: Optional[PlanningSession] = None

    @property
    def session(self) -> Optional[PlanningSession]:
        """Get the current planning session."""
        if self._session is None:
            self._session = self.checkpoint_manager.load_session()
        return self._session

    def start_planning(
        self,
        greenfield: bool = True,
        target_repo: Optional[Path] = None,
    ) -> PlanningSession:
        """Start a new planning session.

        Args:
            greenfield: True for new project, False for existing codebase.
            target_repo: Path to target repo for brownfield projects.

        Returns:
            The new planning session.
        """
        session_id = f"plan-{uuid4().hex[:8]}"

        self._session = PlanningSession(
            id=session_id,
            project_type=ProjectType.GREENFIELD if greenfield else ProjectType.BROWNFIELD,
            current_phase=PlanningPhase.NOT_STARTED,
            target_repo=target_repo,
        )

        self.checkpoint_manager.save_session(self._session)
        return self._session

    def get_status(self) -> dict:
        """Get current planning status.

        Returns:
            Status dict with session info and checkpoint summary.
        """
        if not self.session:
            return {
                "has_session": False,
                "message": "No planning session. Use /plan start to begin.",
            }

        checkpoint_summary = self.checkpoint_manager.get_checkpoint_summary(self.session)

        return {
            "has_session": True,
            "session_id": self.session.id,
            "project_type": self.session.project_type.value,
            "current_phase": self.session.current_phase.value,
            "current_layer": self.session.current_layer_id,
            "current_group": self.session.current_group_id,
            "completed_layers": self.session.completed_layers,
            "completed_groups": self.session.completed_groups,
            "checkpoints": checkpoint_summary,
            "can_continue": checkpoint_summary["can_proceed"],
        }

    def run_architect_phase(
        self,
        codebase_analysis: Optional[CodebaseAnalysis] = None,
    ) -> Generator[str, None, ArchitectOutput]:
        """Run the Technical Architect phase.

        Args:
            codebase_analysis: Optional analysis for brownfield projects.

        Yields:
            Response chunks as they arrive.

        Returns:
            Architect phase output.
        """
        if not self.session:
            raise ValueError("No planning session. Call start_planning() first.")

        # Check if we can proceed
        if not self.checkpoint_manager.can_proceed(self.session):
            raise ValueError("Pending checkpoint. Approve or reject before continuing.")

        # Update session state
        self.session.current_phase = PlanningPhase.ARCHITECT
        self.checkpoint_manager.save_session(self.session)

        # Create and run phase
        phase = TechnicalArchitectPhase(self.project_path, self.model)
        inputs = {"codebase_analysis": codebase_analysis}

        # Run phase with streaming
        output = yield from phase.run(inputs)

        # Create checkpoint
        if output.success:
            self.checkpoint_manager.create_checkpoint(
                self.session,
                PlanningPhase.ARCHITECT,
                f"Architecture defined: {len(output.layers.layers) if output.layers else 0} layers",
                output.artifacts,
            )

            # Fetch documentation for selected technologies
            if output.tech_stack:
                tech_names = self._get_tech_names(output)
                self.docs_fetcher.fetch_tech_stack_docs(tech_names)

        return output

    def run_layer_planning(
        self,
        layer_id: str,
    ) -> Generator[str, None, LayerOutput]:
        """Run the Layer Planner phase for a specific layer.

        Args:
            layer_id: ID of the layer to plan.

        Yields:
            Response chunks as they arrive.

        Returns:
            Layer planner output.
        """
        if not self.session:
            raise ValueError("No planning session.")

        if not self.checkpoint_manager.can_proceed(self.session):
            raise ValueError("Pending checkpoint. Approve or reject before continuing.")

        # Update session state
        self.session.current_phase = PlanningPhase.LAYER_PLANNING
        self.session.current_layer_id = layer_id
        self.checkpoint_manager.save_session(self.session)

        # Create and run phase
        phase = LayerPlannerPhase(self.project_path, self.model)
        inputs = {"layer_id": layer_id}

        output = yield from phase.run(inputs)

        # Create checkpoint
        if output.success:
            self.checkpoint_manager.create_checkpoint(
                self.session,
                PlanningPhase.LAYER_PLANNING,
                f"Layer {layer_id} breakdown: {len(output.groups.groups) if output.groups else 0} groups",
                output.artifacts,
            )

        return output

    def run_group_planning(
        self,
        layer_id: str,
        group_id: str,
    ) -> Generator[str, None, GroupOutput]:
        """Run the Group Planner phase for a specific group.

        Args:
            layer_id: ID of the layer containing the group.
            group_id: ID of the group to plan.

        Yields:
            Response chunks as they arrive.

        Returns:
            Group planner output.
        """
        if not self.session:
            raise ValueError("No planning session.")

        if not self.checkpoint_manager.can_proceed(self.session):
            raise ValueError("Pending checkpoint. Approve or reject before continuing.")

        # Update session state
        self.session.current_phase = PlanningPhase.GROUP_PLANNING
        self.session.current_group_id = group_id
        self.checkpoint_manager.save_session(self.session)

        # Create and run phase
        phase = GroupPlannerPhase(self.project_path, self.model)
        inputs = {"layer_id": layer_id, "group_id": group_id}

        output = yield from phase.run(inputs)

        # Create checkpoint
        if output.success:
            self.checkpoint_manager.create_checkpoint(
                self.session,
                PlanningPhase.GROUP_PLANNING,
                f"Group {group_id} tasks: {len(output.task_ids)} tasks created",
                output.artifacts,
            )

            # Mark group as completed
            if group_id not in self.session.completed_groups:
                self.session.completed_groups.append(group_id)
                self.checkpoint_manager.save_session(self.session)

        return output

    def approve_checkpoint(self, feedback: str = "") -> Optional[dict]:
        """Approve the current pending checkpoint.

        Args:
            feedback: Optional feedback.

        Returns:
            Checkpoint info dict, or None if no pending checkpoint.
        """
        if not self.session:
            return None

        pending = self.checkpoint_manager.get_pending_checkpoint(self.session)
        if not pending:
            return None

        checkpoint = self.checkpoint_manager.approve_checkpoint(
            self.session,
            pending.id,
            feedback,
        )

        if checkpoint:
            # Check if layer is complete
            self._check_layer_completion()

            return {
                "id": checkpoint.id,
                "status": checkpoint.status.value,
                "phase": checkpoint.phase.value,
            }
        return None

    def reject_checkpoint(self, feedback: str) -> Optional[dict]:
        """Reject the current pending checkpoint.

        Args:
            feedback: Feedback explaining the rejection.

        Returns:
            Checkpoint info dict, or None if no pending checkpoint.
        """
        if not self.session:
            return None

        pending = self.checkpoint_manager.get_pending_checkpoint(self.session)
        if not pending:
            return None

        checkpoint = self.checkpoint_manager.reject_checkpoint(
            self.session,
            pending.id,
            feedback,
        )

        if checkpoint:
            return {
                "id": checkpoint.id,
                "status": checkpoint.status.value,
                "phase": checkpoint.phase.value,
                "feedback": feedback,
            }
        return None

    def get_next_action(self) -> dict:
        """Determine the next action in the planning process.

        Returns:
            Dict with action type and parameters.
        """
        if not self.session:
            return {"action": "start", "message": "Start a planning session with /plan start"}

        # Check for pending checkpoint
        pending = self.checkpoint_manager.get_pending_checkpoint(self.session)
        if pending:
            return {
                "action": "checkpoint",
                "checkpoint_id": pending.id,
                "phase": pending.phase.value,
                "message": f"Pending checkpoint for {pending.phase.value}. Use /plan approve or /plan reject",
            }

        # Determine next phase based on current state
        layers = self.context_builder.load_layers()
        if not layers:
            return {
                "action": "architect",
                "message": "Run architect phase with /plan continue",
            }

        # Check for layers needing group planning
        for layer in layers.layers:
            if layer.id not in self.session.completed_layers:
                groups = self.context_builder.load_groups(layer.id)
                if not groups:
                    return {
                        "action": "layer_planning",
                        "layer_id": layer.id,
                        "message": f"Plan groups for layer {layer.id} with /plan continue",
                    }

                # Check for groups needing task planning
                for group in groups.groups:
                    if group.id not in self.session.completed_groups:
                        return {
                            "action": "group_planning",
                            "layer_id": layer.id,
                            "group_id": group.id,
                            "message": f"Plan tasks for group {group.id} with /plan continue",
                        }

                # All groups in layer complete
                if layer.id not in self.session.completed_layers:
                    self.session.completed_layers.append(layer.id)
                    self.checkpoint_manager.save_session(self.session)

        # All done
        self.session.current_phase = PlanningPhase.COMPLETED
        self.checkpoint_manager.save_session(self.session)

        return {
            "action": "completed",
            "message": "Planning complete. All tasks have been created.",
        }

    def continue_planning(self) -> Generator[str, None, PhaseOutput]:
        """Continue to the next phase of planning.

        Yields:
            Response chunks as they arrive.

        Returns:
            Phase output.
        """
        next_action = self.get_next_action()
        action = next_action.get("action")

        if action == "start":
            raise ValueError("No session. Use start_planning() first.")

        if action == "checkpoint":
            raise ValueError(f"Pending checkpoint. Use approve_checkpoint() or reject_checkpoint().")

        if action == "completed":
            raise ValueError("Planning is complete.")

        if action == "architect":
            codebase_analysis = None
            if self.session and self.session.project_type == ProjectType.BROWNFIELD:
                codebase_analysis = self.context_builder.load_codebase_analysis()
            return (yield from self.run_architect_phase(codebase_analysis))

        if action == "layer_planning":
            layer_id = next_action.get("layer_id")
            return (yield from self.run_layer_planning(layer_id))

        if action == "group_planning":
            layer_id = next_action.get("layer_id")
            group_id = next_action.get("group_id")
            return (yield from self.run_group_planning(layer_id, group_id))

        raise ValueError(f"Unknown action: {action}")

    def list_layers(self) -> list[dict]:
        """List all defined layers.

        Returns:
            List of layer dicts.
        """
        layers = self.context_builder.load_layers()
        if not layers:
            return []

        return [
            {
                "id": layer.id,
                "name": layer.name,
                "order": layer.order,
                "completed": layer.id in (self.session.completed_layers if self.session else []),
            }
            for layer in layers.layers
        ]

    def list_groups(self, layer_id: str) -> list[dict]:
        """List groups for a layer.

        Args:
            layer_id: ID of the layer.

        Returns:
            List of group dicts.
        """
        groups = self.context_builder.load_groups(layer_id)
        if not groups:
            return []

        return [
            {
                "id": group.id,
                "name": group.name,
                "order": group.order,
                "estimated_tasks": group.estimated_tasks,
                "completed": group.id in (self.session.completed_groups if self.session else []),
            }
            for group in groups.groups
        ]

    def _get_tech_names(self, output: ArchitectOutput) -> list[str]:
        """Extract technology names from architect output."""
        names = []
        if output.tech_stack:
            for fw in output.tech_stack.frameworks.values():
                names.append(fw.name.lower())
            if output.tech_stack.database and output.tech_stack.database.orm:
                names.append(output.tech_stack.database.orm.lower())
            if output.tech_stack.testing:
                if output.tech_stack.testing.unit:
                    names.append(output.tech_stack.testing.unit.lower())
            for dep in output.tech_stack.dependencies:
                names.append(dep.name.lower())
        return names

    def _check_layer_completion(self) -> None:
        """Check if the current layer is complete."""
        if not self.session or not self.session.current_layer_id:
            return

        layer_id = self.session.current_layer_id
        groups = self.context_builder.load_groups(layer_id)

        if not groups:
            return

        # Check if all groups are complete
        all_complete = all(
            group.id in self.session.completed_groups
            for group in groups.groups
        )

        if all_complete and layer_id not in self.session.completed_layers:
            self.session.completed_layers.append(layer_id)
            self.session.current_layer_id = None
            self.checkpoint_manager.save_session(self.session)
