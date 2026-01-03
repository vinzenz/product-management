"""Plan Commands - CLI command handlers for the planning system."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.table import Table

from pm.core.planner.orchestrator import PlannerOrchestrator

console = Console()


class PlanCommands:
    """Handles /plan CLI commands."""

    def __init__(self, project_path: Path, model: str = "claude"):
        """Initialize plan commands.

        Args:
            project_path: Path to the project root.
            model: Model to use for planning.
        """
        self.project_path = project_path
        self.model = model
        self._orchestrator: Optional[PlannerOrchestrator] = None

    @property
    def orchestrator(self) -> PlannerOrchestrator:
        """Get or create the orchestrator."""
        if self._orchestrator is None:
            self._orchestrator = PlannerOrchestrator(self.project_path, self.model)
        return self._orchestrator

    def handle_command(self, args: list[str]) -> None:
        """Handle a /plan command.

        Args:
            args: Command arguments.
        """
        if not args:
            self.cmd_status()
            return

        subcmd = args[0].lower()
        subargs = args[1:]

        commands = {
            "start": self.cmd_start,
            "status": self.cmd_status,
            "continue": self.cmd_continue,
            "approve": self.cmd_approve,
            "reject": self.cmd_reject,
            "layers": self.cmd_layers,
            "groups": self.cmd_groups,
            "tasks": self.cmd_tasks,
            "next": self.cmd_next,
        }

        if subcmd in commands:
            commands[subcmd](subargs)
        else:
            console.print(f"[red]Unknown plan command:[/red] {subcmd}")
            self._print_help()

    def cmd_start(self, args: list[str]) -> None:
        """Start a new planning session."""
        greenfield = True
        target_repo = None

        for i, arg in enumerate(args):
            if arg == "--brownfield":
                greenfield = False
            elif arg == "--target" and i + 1 < len(args):
                target_repo = Path(args[i + 1])

        try:
            session = self.orchestrator.start_planning(greenfield, target_repo)
            console.print()
            console.print(f"[green]Planning session started:[/green] {session.id}")
            console.print(f"Project type: {'greenfield' if greenfield else 'brownfield'}")
            if target_repo:
                console.print(f"Target repo: {target_repo}")
            console.print()
            console.print("[dim]Use /plan continue to start the architect phase[/dim]")
            console.print()
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def cmd_status(self, args: list[str] = None) -> None:
        """Show planning status."""
        status = self.orchestrator.get_status()

        console.print()
        if not status.get("has_session"):
            console.print("[dim]No planning session[/dim]")
            console.print("[dim]Use /plan start to begin[/dim]")
            console.print()
            return

        console.print(f"[bold]Planning Session:[/bold] {status['session_id']}")
        console.print(f"[bold]Project Type:[/bold] {status['project_type']}")
        console.print(f"[bold]Current Phase:[/bold] {status['current_phase']}")

        if status.get("current_layer"):
            console.print(f"[bold]Current Layer:[/bold] {status['current_layer']}")
        if status.get("current_group"):
            console.print(f"[bold]Current Group:[/bold] {status['current_group']}")

        if status.get("completed_layers"):
            console.print(f"[bold]Completed Layers:[/bold] {', '.join(status['completed_layers'])}")

        console.print()

        # Checkpoint summary
        cp = status.get("checkpoints", {})
        console.print(f"[bold]Checkpoints:[/bold] {cp.get('approved', 0)} approved, {cp.get('pending', 0)} pending")

        if cp.get("pending", 0) > 0:
            console.print("[yellow]There is a pending checkpoint. Use /plan approve or /plan reject[/yellow]")
        elif status.get("can_continue"):
            console.print("[green]Ready to continue. Use /plan continue[/green]")

        console.print()

    def cmd_continue(self, args: list[str] = None) -> None:
        """Continue planning from current state."""
        try:
            # Get next action info
            next_action = self.orchestrator.get_next_action()
            action = next_action.get("action")

            if action == "start":
                console.print("[yellow]No session. Use /plan start first[/yellow]")
                return

            if action == "checkpoint":
                console.print("[yellow]Pending checkpoint:[/yellow]")
                console.print(f"  Phase: {next_action['phase']}")
                console.print("[dim]Use /plan approve or /plan reject[/dim]")
                return

            if action == "completed":
                console.print("[green]Planning is complete![/green]")
                console.print("[dim]All tasks have been created.[/dim]")
                return

            # Show what we're about to do
            console.print()
            console.print(f"[bold]Running:[/bold] {next_action.get('message', action)}")
            console.print()

            # Run the phase with streaming output
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=15) as live:
                for chunk in self.orchestrator.continue_planning():
                    full_response += chunk
                    live.update(Markdown(full_response))

            console.print()
            console.print("[green]Phase complete[/green]")

            # Show next action
            next_action = self.orchestrator.get_next_action()
            if next_action.get("action") == "checkpoint":
                console.print()
                console.print("[bold]Checkpoint created.[/bold] Review the output above.")
                console.print("[dim]Use /plan approve to continue, or /plan reject <feedback> to revise[/dim]")

        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

    def cmd_approve(self, args: list[str] = None) -> None:
        """Approve the current checkpoint."""
        feedback = " ".join(args) if args else ""

        result = self.orchestrator.approve_checkpoint(feedback)

        if result:
            console.print()
            console.print(f"[green]Approved checkpoint:[/green] {result['id']}")
            if feedback:
                console.print(f"[dim]Feedback: {feedback}[/dim]")
            console.print()

            # Show next action
            next_action = self.orchestrator.get_next_action()
            console.print(f"[dim]Next: {next_action.get('message', 'Unknown')}[/dim]")
            console.print("[dim]Use /plan continue to proceed[/dim]")
            console.print()
        else:
            console.print("[yellow]No pending checkpoint to approve[/yellow]")

    def cmd_reject(self, args: list[str] = None) -> None:
        """Reject the current checkpoint."""
        if not args:
            console.print("[red]Usage:[/red] /plan reject <feedback>")
            console.print("[dim]Provide feedback explaining why the output should be revised[/dim]")
            return

        feedback = " ".join(args)
        result = self.orchestrator.reject_checkpoint(feedback)

        if result:
            console.print()
            console.print(f"[yellow]Rejected checkpoint:[/yellow] {result['id']}")
            console.print(f"[dim]Feedback: {feedback}[/dim]")
            console.print()
            console.print("[dim]The phase will need to be re-run with /plan continue[/dim]")
            console.print()
        else:
            console.print("[yellow]No pending checkpoint to reject[/yellow]")

    def cmd_layers(self, args: list[str] = None) -> None:
        """List architecture layers."""
        layers = self.orchestrator.list_layers()

        if not layers:
            console.print("[dim]No layers defined yet. Run architect phase first.[/dim]")
            return

        console.print()
        table = Table(title="Architecture Layers")
        table.add_column("ID", style="bold")
        table.add_column("Name")
        table.add_column("Order")
        table.add_column("Status")

        for layer in layers:
            status = "[green]Complete[/green]" if layer["completed"] else "[dim]Pending[/dim]"
            table.add_row(
                layer["id"],
                layer["name"],
                str(layer["order"]),
                status,
            )

        console.print(table)
        console.print()

    def cmd_groups(self, args: list[str] = None) -> None:
        """List groups for a layer."""
        if not args:
            console.print("[red]Usage:[/red] /plan groups <layer-id>")
            return

        layer_id = args[0]
        groups = self.orchestrator.list_groups(layer_id)

        if not groups:
            console.print(f"[dim]No groups defined for layer {layer_id}[/dim]")
            return

        console.print()
        table = Table(title=f"Groups in {layer_id}")
        table.add_column("ID", style="bold")
        table.add_column("Name")
        table.add_column("Order")
        table.add_column("Est. Tasks")
        table.add_column("Status")

        for group in groups:
            status = "[green]Complete[/green]" if group["completed"] else "[dim]Pending[/dim]"
            table.add_row(
                group["id"],
                group["name"],
                str(group["order"]),
                str(group["estimated_tasks"]),
                status,
            )

        console.print(table)
        console.print()

    def cmd_tasks(self, args: list[str] = None) -> None:
        """List tasks for a group."""
        if not args:
            console.print("[red]Usage:[/red] /plan tasks <group-id>")
            console.print("[dim]To see all tasks, use /artifact task list[/dim]")
            return

        group_id = args[0]
        # Tasks are managed by ArtifactManager
        console.print(f"[dim]Tasks for group {group_id}:[/dim]")
        console.print("[dim]Use /artifact task list to see all tasks[/dim]")

    def cmd_next(self, args: list[str] = None) -> None:
        """Show the next action to take."""
        next_action = self.orchestrator.get_next_action()

        console.print()
        console.print(f"[bold]Next Action:[/bold] {next_action.get('action', 'unknown')}")
        console.print(next_action.get("message", ""))

        if next_action.get("layer_id"):
            console.print(f"[dim]Layer: {next_action['layer_id']}[/dim]")
        if next_action.get("group_id"):
            console.print(f"[dim]Group: {next_action['group_id']}[/dim]")
        if next_action.get("checkpoint_id"):
            console.print(f"[dim]Checkpoint: {next_action['checkpoint_id']}[/dim]")

        console.print()

    def _print_help(self) -> None:
        """Print help for plan commands."""
        console.print()
        console.print("[bold]/plan[/bold] commands:")
        console.print()
        console.print("  [bold]start[/bold]                    Start new planning session (greenfield)")
        console.print("  [bold]start --brownfield[/bold]       Start with existing codebase analysis")
        console.print("  [bold]start --target /path[/bold]     Specify target repo for brownfield")
        console.print()
        console.print("  [bold]status[/bold]                   Show current planning status")
        console.print("  [bold]continue[/bold]                 Continue from current checkpoint")
        console.print("  [bold]approve[/bold] [feedback]       Approve current checkpoint")
        console.print("  [bold]reject[/bold] <feedback>        Reject and request revision")
        console.print()
        console.print("  [bold]layers[/bold]                   List defined layers")
        console.print("  [bold]groups[/bold] <layer-id>        List groups in a layer")
        console.print("  [bold]tasks[/bold] <group-id>         List tasks in a group")
        console.print("  [bold]next[/bold]                     Show next action to take")
        console.print()
