"""Main CLI entry point."""

import click
from pathlib import Path
from rich.console import Console

from pm.cli.repl import REPL
from pm.core.project import ProjectManager

console = Console()


def get_base_path() -> Path:
    """Get the base path for the product management system."""
    # Default to current directory, but could be configured
    return Path.cwd()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Product Management System - CLI-first LLM-powered product development."""
    ctx.ensure_object(dict)

    base_path = get_base_path()
    ctx.obj["base_path"] = base_path
    ctx.obj["project_manager"] = ProjectManager(base_path)

    if ctx.invoked_subcommand is None:
        # No subcommand - start REPL
        repl = REPL(ctx.obj["project_manager"])
        repl.run()


@main.command()
@click.argument("name")
@click.pass_context
def new(ctx: click.Context, name: str) -> None:
    """Create a new project."""
    pm = ctx.obj["project_manager"]
    try:
        project = pm.create_project(name)
        console.print(f"[green]Created project:[/green] {project.name} ({project.id})")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command("list")
@click.pass_context
def list_projects(ctx: click.Context) -> None:
    """List all projects."""
    pm = ctx.obj["project_manager"]
    projects = pm.list_projects()

    if not projects:
        console.print("[dim]No projects found[/dim]")
        return

    for project in projects:
        status_color = "yellow" if project.status.value in ("ideation", "requirements") else "green"
        console.print(
            f"  [{status_color}]{project.status.value:12}[/{status_color}] "
            f"[bold]{project.id}[/bold] - {project.name}"
        )


@main.command()
@click.argument("project_id")
@click.pass_context
def switch(ctx: click.Context, project_id: str) -> None:
    """Switch to a project and start REPL."""
    pm = ctx.obj["project_manager"]
    try:
        project = pm.switch_project(project_id)
        console.print(f"[green]Switched to:[/green] {project.name}")

        repl = REPL(pm)
        repl.run()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current project status."""
    pm = ctx.obj["project_manager"]
    project = pm.current_project

    if not project:
        console.print("[dim]No project selected[/dim]")
        return

    console.print(f"[bold]Project:[/bold] {project.name}")
    console.print(f"[bold]ID:[/bold] {project.id}")
    console.print(f"[bold]Status:[/bold] {project.status.value}")
    console.print(f"[bold]Created:[/bold] {project.created.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"[bold]Updated:[/bold] {project.updated.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
