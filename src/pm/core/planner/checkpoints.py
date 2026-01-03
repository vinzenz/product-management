"""Checkpoint Manager - Manages planning checkpoints and user approvals."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pm.models.planner import (
    Checkpoint,
    CheckpointStatus,
    PlanningPhase,
    PlanningSession,
)
from pm.storage.files import read_yaml_file, write_yaml_file, ensure_directory


class CheckpointManager:
    """Manages checkpoints in the planning process.

    Checkpoints are pause points where the user reviews and approves
    the output of a planning phase before proceeding to the next.
    """

    def __init__(self, project_path: Path):
        """Initialize the checkpoint manager.

        Args:
            project_path: Path to the project root.
        """
        self.project_path = project_path
        self.planning_dir = project_path / "planning"
        self.session_file = self.planning_dir / "session.yaml"
        ensure_directory(self.planning_dir)

    def load_session(self) -> Optional[PlanningSession]:
        """Load the current planning session.

        Returns:
            The current session, or None if no session exists.
        """
        if not self.session_file.exists():
            return None

        data = read_yaml_file(self.session_file)
        if not data:
            return None

        return PlanningSession.from_dict(data)

    def save_session(self, session: PlanningSession) -> None:
        """Save the planning session.

        Args:
            session: The session to save.
        """
        session.updated = datetime.now()
        write_yaml_file(self.session_file, session.to_dict())

    def create_checkpoint(
        self,
        session: PlanningSession,
        phase: PlanningPhase,
        description: str,
        artifacts: list[str] | None = None,
    ) -> Checkpoint:
        """Create a new checkpoint.

        Args:
            session: The current planning session.
            phase: The phase this checkpoint is for.
            description: Description of what was accomplished.
            artifacts: List of artifact paths created.

        Returns:
            The created checkpoint.
        """
        checkpoint = session.add_checkpoint(phase, description, artifacts)
        self.save_session(session)
        return checkpoint

    def approve_checkpoint(
        self,
        session: PlanningSession,
        checkpoint_id: str,
        feedback: str = "",
    ) -> Optional[Checkpoint]:
        """Approve a checkpoint.

        Args:
            session: The current planning session.
            checkpoint_id: ID of the checkpoint to approve.
            feedback: Optional feedback from the user.

        Returns:
            The approved checkpoint, or None if not found.
        """
        for checkpoint in session.checkpoints:
            if checkpoint.id == checkpoint_id:
                checkpoint.status = CheckpointStatus.APPROVED
                checkpoint.approved_at = datetime.now()
                checkpoint.feedback = feedback
                self.save_session(session)
                return checkpoint
        return None

    def reject_checkpoint(
        self,
        session: PlanningSession,
        checkpoint_id: str,
        feedback: str,
    ) -> Optional[Checkpoint]:
        """Reject a checkpoint.

        Args:
            session: The current planning session.
            checkpoint_id: ID of the checkpoint to reject.
            feedback: Feedback explaining the rejection.

        Returns:
            The rejected checkpoint, or None if not found.
        """
        for checkpoint in session.checkpoints:
            if checkpoint.id == checkpoint_id:
                checkpoint.status = CheckpointStatus.REJECTED
                checkpoint.feedback = feedback
                self.save_session(session)
                return checkpoint
        return None

    def get_pending_checkpoint(
        self,
        session: PlanningSession,
    ) -> Optional[Checkpoint]:
        """Get the current pending checkpoint.

        Args:
            session: The current planning session.

        Returns:
            The pending checkpoint, or None if none pending.
        """
        return session.get_pending_checkpoint()

    def can_proceed(self, session: PlanningSession) -> bool:
        """Check if the session can proceed to the next phase.

        Args:
            session: The current planning session.

        Returns:
            True if there's no pending checkpoint.
        """
        return session.get_pending_checkpoint() is None

    def get_checkpoint_summary(self, session: PlanningSession) -> dict:
        """Get a summary of checkpoints.

        Args:
            session: The current planning session.

        Returns:
            Summary dict with counts and status.
        """
        total = len(session.checkpoints)
        approved = sum(1 for c in session.checkpoints if c.status == CheckpointStatus.APPROVED)
        rejected = sum(1 for c in session.checkpoints if c.status == CheckpointStatus.REJECTED)
        pending = sum(1 for c in session.checkpoints if c.status == CheckpointStatus.PENDING)

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "current_phase": session.current_phase.value,
            "can_proceed": pending == 0,
        }

    def format_checkpoint_for_display(self, checkpoint: Checkpoint) -> str:
        """Format a checkpoint for display.

        Args:
            checkpoint: The checkpoint to format.

        Returns:
            Formatted string for display.
        """
        lines = [
            f"Checkpoint: {checkpoint.id}",
            f"Phase: {checkpoint.phase.value}",
            f"Status: {checkpoint.status.value}",
            f"Created: {checkpoint.created.strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"Description: {checkpoint.description}",
        ]

        if checkpoint.artifacts:
            lines.append("")
            lines.append("Artifacts:")
            for artifact in checkpoint.artifacts:
                lines.append(f"  - {artifact}")

        if checkpoint.feedback:
            lines.append("")
            lines.append(f"Feedback: {checkpoint.feedback}")

        if checkpoint.approved_at:
            lines.append(f"Approved: {checkpoint.approved_at.strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(lines)

    def list_checkpoints(self, session: PlanningSession) -> list[dict]:
        """List all checkpoints as dicts.

        Args:
            session: The current planning session.

        Returns:
            List of checkpoint dicts.
        """
        return [
            {
                "id": c.id,
                "phase": c.phase.value,
                "status": c.status.value,
                "description": c.description,
                "created": c.created.isoformat(),
                "approved_at": c.approved_at.isoformat() if c.approved_at else None,
            }
            for c in session.checkpoints
        ]
