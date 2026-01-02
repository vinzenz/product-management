"""Interactive REPL for the Product Management System."""

from typing import Callable, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from pm.core.artifact import ArtifactManager
from pm.core.conversation import AVAILABLE_MODELS, PROVIDERS, ConversationManager, list_models_by_provider
from pm.core.persona import PersonaManager
from pm.core.project import ProjectManager

console = Console()


class REPL:
    """Interactive Read-Eval-Print Loop."""

    def __init__(self, project_manager: ProjectManager):
        self.pm = project_manager
        self.running = False
        self._artifact_manager: Optional[ArtifactManager] = None
        self._conversation: Optional[ConversationManager] = None
        self._persona_manager: Optional[PersonaManager] = None
        self.commands: dict[str, Callable[[list[str]], None]] = {
            "/help": self._cmd_help,
            "/quit": self._cmd_quit,
            "/exit": self._cmd_quit,
            "/project": self._cmd_project,
            "/status": self._cmd_status,
            "/artifact": self._cmd_artifact,
            "/context": self._cmd_context,
            "/clear": self._cmd_clear,
            "/perspective": self._cmd_perspective,
            "/persona": self._cmd_perspective,  # Alias
            "/model": self._cmd_model,
            "/summarize": self._cmd_summarize,
        }

    def run(self) -> None:
        """Start the REPL loop."""
        self.running = True
        self._print_welcome()

        while self.running:
            try:
                prompt = self._get_prompt()
                user_input = Prompt.ask(prompt)

                if not user_input.strip():
                    continue

                self._process_input(user_input)

            except KeyboardInterrupt:
                console.print("\n[dim]Use /quit to exit[/dim]")
            except EOFError:
                self._cmd_quit([])

    def _get_prompt(self) -> str:
        """Generate the prompt string."""
        parts = []

        if self.pm.current_project:
            project = self.pm.current_project
            parts.append(f"[bold blue]{project.id}[/bold blue]")
            parts.append(f"[{project.status.value}]")
        else:
            parts.append("[dim]no project[/dim]")

        # Show current perspective if set
        if self._conversation and self._conversation.get_persona():
            persona = self._conversation.get_persona()
            parts.append(f"[magenta]@{persona.id}[/magenta]")

        return " ".join(parts)

    def _print_welcome(self) -> None:
        """Print welcome message."""
        console.print()
        console.print("[bold]Product Management System[/bold]")
        console.print("[dim]Type /help for commands, or just start talking[/dim]")
        console.print()

        if not self.pm.current_project:
            projects = self.pm.list_projects()
            if projects:
                console.print("[dim]Available projects:[/dim]")
                for p in projects[:5]:
                    console.print(f"  - {p.id}: {p.name}")
                console.print()
                console.print("[dim]Use /project switch <id> to select one[/dim]")
            else:
                console.print("[dim]No projects yet. Use /project new <name> to create one[/dim]")
            console.print()

    def _process_input(self, user_input: str) -> None:
        """Process user input."""
        user_input = user_input.strip()

        if user_input.startswith("/"):
            self._handle_command(user_input)
        else:
            self._handle_conversation(user_input)

    def _handle_command(self, input_str: str) -> None:
        """Handle a slash command."""
        parts = input_str.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in self.commands:
            self.commands[cmd](args)
        else:
            console.print(f"[red]Unknown command:[/red] {cmd}")
            console.print("[dim]Type /help for available commands[/dim]")

    def _get_conversation(self) -> ConversationManager:
        """Get or create the conversation manager."""
        if self._conversation is None:
            self._conversation = ConversationManager()

        # Update project context if we have a project
        if self.pm.current_project:
            project = self.pm.current_project
            self._conversation.set_project_context(
                project.id, project.name, project.status.value
            )

        return self._conversation

    def _get_persona_manager(self) -> PersonaManager:
        """Get or create the persona manager."""
        project_path = self.pm.get_project_path() if self.pm.current_project else None

        if self._persona_manager is None or (
            project_path and self._persona_manager._project_path != project_path
        ):
            self._persona_manager = PersonaManager(project_path)

        return self._persona_manager

    def _handle_conversation(self, message: str) -> None:
        """Handle conversational input with LLM using streaming."""
        if not self.pm.current_project:
            console.print("[yellow]No project selected.[/yellow] Use /project new <name> or /project switch <id>")
            console.print("[dim]You can still chat, but responses won't have project context.[/dim]")
            console.print()

        try:
            conversation = self._get_conversation()
            console.print()

            # Stream response with live markdown rendering
            full_response = ""
            with Live(Markdown(""), console=console, refresh_per_second=15) as live:
                for chunk in conversation.chat_stream(message):
                    full_response += chunk
                    live.update(Markdown(full_response))

            console.print()

        except ValueError as e:
            # Missing API key
            console.print(f"[red]Configuration error:[/red] {e}")
        except RuntimeError as e:
            # API error
            console.print(f"[red]Error:[/red] {e}")

    # Command handlers

    def _cmd_help(self, args: list[str]) -> None:
        """Show help information."""
        console.print()
        console.print("[bold]Available Commands:[/bold]")
        console.print()
        console.print("  [bold]/project[/bold]")
        console.print("    new <name>     Create a new project")
        console.print("    list           List all projects")
        console.print("    switch <id>    Switch to a project")
        console.print("    status         Show current project status")
        console.print()
        console.print("  [bold]/artifact[/bold]")
        console.print("    feature new    Create a new feature")
        console.print("    feature list   List features")
        console.print("    req new        Create a new requirement")
        console.print("    req list       List requirements")
        console.print()
        console.print("  [bold]/perspective[/bold] (or /persona)")
        console.print("    list           List available perspectives")
        console.print("    switch <id>    Switch to a perspective (pm, engineer, designer, etc.)")
        console.print("    clear          Return to default assistant")
        console.print("    show           Show current perspective details")
        console.print()
        console.print("  [bold]/model[/bold]")
        console.print("    list           List available models")
        console.print("    switch <id>    Switch model (sonnet, haiku, opus)")
        console.print()
        console.print("  [bold]/status[/bold]          Show current context")
        console.print("  [bold]/context[/bold]         Show conversation context")
        console.print("  [bold]/summarize[/bold]       Compress conversation history")
        console.print("  [bold]/clear[/bold]           Clear conversation")
        console.print("  [bold]/quit[/bold]            Exit the REPL")
        console.print()

    def _cmd_quit(self, args: list[str]) -> None:
        """Exit the REPL."""
        console.print("[dim]Goodbye![/dim]")
        self.running = False

    def _cmd_project(self, args: list[str]) -> None:
        """Handle project commands."""
        if not args:
            self._cmd_project_status([])
            return

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "new":
            self._cmd_project_new(subargs)
        elif subcmd == "list":
            self._cmd_project_list(subargs)
        elif subcmd == "switch":
            self._cmd_project_switch(subargs)
        elif subcmd == "status":
            self._cmd_project_status(subargs)
        else:
            console.print(f"[red]Unknown project command:[/red] {subcmd}")

    def _cmd_project_new(self, args: list[str]) -> None:
        """Create a new project."""
        if not args:
            console.print("[red]Usage:[/red] /project new <name>")
            return

        name = " ".join(args)
        try:
            project = self.pm.create_project(name)
            console.print(f"[green]Created project:[/green] {project.name} ({project.id})")

            # Initialize personas for the project
            persona_manager = PersonaManager(self.pm.get_project_path())
            persona_manager.create_project_personas()
            console.print("[dim]Created default persona files in design/personas/[/dim]")

        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")

    def _cmd_project_list(self, args: list[str]) -> None:
        """List all projects."""
        projects = self.pm.list_projects()

        if not projects:
            console.print("[dim]No projects found[/dim]")
            return

        console.print()
        for project in projects:
            marker = ">" if self.pm.current_project and project.id == self.pm.current_project.id else " "
            status_color = "yellow" if project.status.value in ("ideation", "requirements") else "green"
            console.print(
                f" {marker} [{status_color}]{project.status.value:12}[/{status_color}] "
                f"[bold]{project.id}[/bold] - {project.name}"
            )
        console.print()

    def _cmd_project_switch(self, args: list[str]) -> None:
        """Switch to a project."""
        if not args:
            console.print("[red]Usage:[/red] /project switch <id>")
            return

        project_id = args[0]
        try:
            project = self.pm.switch_project(project_id)
            console.print(f"[green]Switched to:[/green] {project.name}")

            # Reset persona manager for new project
            self._persona_manager = None

        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")

    def _cmd_project_status(self, args: list[str]) -> None:
        """Show current project status."""
        project = self.pm.current_project

        if not project:
            console.print("[dim]No project selected[/dim]")
            return

        console.print()
        console.print(f"[bold]Project:[/bold] {project.name}")
        console.print(f"[bold]ID:[/bold] {project.id}")
        console.print(f"[bold]Status:[/bold] {project.status.value}")
        console.print(f"[bold]Branch:[/bold] {project.git_branch}")
        console.print(f"[bold]Created:[/bold] {project.created.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[bold]Updated:[/bold] {project.updated.strftime('%Y-%m-%d %H:%M')}")
        console.print()

    def _cmd_status(self, args: list[str]) -> None:
        """Show current status."""
        self._cmd_project_status(args)

        # Also show conversation status
        if self._conversation:
            console.print(f"[bold]Conversation:[/bold] {self._conversation.get_context_summary()}")
            console.print()

    def _cmd_artifact(self, args: list[str]) -> None:
        """Handle artifact commands."""
        if not args:
            console.print("[red]Usage:[/red] /artifact <type> <action>")
            console.print("[dim]Types: feature, req[/dim]")
            return

        if not self.pm.current_project:
            console.print("[red]No project selected.[/red] Use /project switch <id>")
            return

        artifact_type = args[0].lower()
        action = args[1].lower() if len(args) > 1 else "list"
        subargs = args[2:]

        if artifact_type in ("feature", "features"):
            self._handle_feature_command(action, subargs)
        elif artifact_type in ("req", "requirement", "requirements"):
            self._handle_requirement_command(action, subargs)
        else:
            console.print(f"[red]Unknown artifact type:[/red] {artifact_type}")

    def _get_artifact_manager(self) -> ArtifactManager:
        """Get or create the artifact manager for the current project."""
        if self._artifact_manager is None or (
            self.pm.current_project
            and self._artifact_manager.project_path != self.pm.get_project_path()
        ):
            self._artifact_manager = ArtifactManager(self.pm.get_project_path())
        return self._artifact_manager

    def _handle_feature_command(self, action: str, args: list[str]) -> None:
        """Handle feature artifact commands."""
        am = self._get_artifact_manager()

        if action == "new":
            if not args:
                title = Prompt.ask("[bold]Feature title[/bold]")
            else:
                title = " ".join(args)

            description = Prompt.ask("[dim]Description (optional)[/dim]", default="")
            feature = am.create_feature(title, description)
            console.print(f"[green]Created feature:[/green] {feature.id} - {feature.title}")

        elif action == "list":
            features = am.list_features()
            if not features:
                console.print("[dim]No features yet. Use /artifact feature new[/dim]")
                return

            table = Table(title="Features")
            table.add_column("ID", style="bold")
            table.add_column("Title")
            table.add_column("Status")
            table.add_column("Priority")

            for f in features:
                status_color = "green" if f.status.value == "approved" else "yellow"
                table.add_row(
                    f.id,
                    f.title,
                    f"[{status_color}]{f.status.value}[/{status_color}]",
                    f.priority.value,
                )
            console.print(table)

        elif action == "show":
            if not args:
                console.print("[red]Usage:[/red] /artifact feature show <id>")
                return
            feature = am.get_feature(args[0])
            if not feature:
                console.print(f"[red]Feature not found:[/red] {args[0]}")
                return
            console.print()
            console.print(f"[bold]{feature.id}: {feature.title}[/bold]")
            console.print(f"Status: {feature.status.value} | Priority: {feature.priority.value}")
            if feature.description:
                console.print(f"\n{feature.description}")
            if feature.requirements:
                console.print(f"\nLinked requirements: {', '.join(feature.requirements)}")
            console.print()

        else:
            console.print(f"[red]Unknown action:[/red] {action}")
            console.print("[dim]Actions: new, list, show[/dim]")

    def _handle_requirement_command(self, action: str, args: list[str]) -> None:
        """Handle requirement artifact commands."""
        am = self._get_artifact_manager()

        if action == "new":
            if not args:
                title = Prompt.ask("[bold]Requirement title[/bold]")
            else:
                title = " ".join(args)

            description = Prompt.ask("[dim]Description (optional)[/dim]", default="")
            req_type = Prompt.ask(
                "[dim]Type[/dim]",
                choices=["functional", "non-functional"],
                default="functional",
            )
            is_functional = req_type == "functional"

            requirement = am.create_requirement(title, description, is_functional)
            console.print(f"[green]Created requirement:[/green] {requirement.id} - {requirement.title}")

        elif action == "list":
            requirements = am.list_requirements()
            if not requirements:
                console.print("[dim]No requirements yet. Use /artifact req new[/dim]")
                return

            table = Table(title="Requirements")
            table.add_column("ID", style="bold")
            table.add_column("Title")
            table.add_column("Type")
            table.add_column("Status")
            table.add_column("Feature")

            for r in requirements:
                req_type = "FR" if r.is_functional else "NFR"
                status_color = "green" if r.status.value == "approved" else "yellow"
                table.add_row(
                    r.id,
                    r.title,
                    req_type,
                    f"[{status_color}]{r.status.value}[/{status_color}]",
                    r.feature or "-",
                )
            console.print(table)

        elif action == "show":
            if not args:
                console.print("[red]Usage:[/red] /artifact req show <id>")
                return
            requirement = am.get_requirement(args[0])
            if not requirement:
                console.print(f"[red]Requirement not found:[/red] {args[0]}")
                return
            console.print()
            console.print(f"[bold]{requirement.id}: {requirement.title}[/bold]")
            req_type = "Functional" if requirement.is_functional else "Non-Functional"
            console.print(f"Type: {req_type} | Status: {requirement.status.value} | Priority: {requirement.priority.value}")
            if requirement.description:
                console.print(f"\n{requirement.description}")
            if requirement.feature:
                console.print(f"\nLinked to feature: {requirement.feature}")
            console.print()

        else:
            console.print(f"[red]Unknown action:[/red] {action}")
            console.print("[dim]Actions: new, list, show[/dim]")

    def _cmd_context(self, args: list[str]) -> None:
        """Show conversation context."""
        if self._conversation is None:
            console.print("[dim]No conversation started yet[/dim]")
            return

        summary = self._conversation.get_context_summary()
        console.print(f"[bold]Conversation:[/bold] {summary}")

        if self.pm.current_project:
            console.print(f"[bold]Project:[/bold] {self.pm.current_project.name}")

    def _cmd_clear(self, args: list[str]) -> None:
        """Clear conversation context."""
        if self._conversation:
            self._conversation.clear_context()
        console.print("[green]Conversation cleared[/green]")

    def _cmd_perspective(self, args: list[str]) -> None:
        """Handle perspective/persona commands."""
        if not args:
            # Show current perspective
            self._cmd_perspective_show([])
            return

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "list":
            self._cmd_perspective_list(subargs)
        elif subcmd == "switch":
            self._cmd_perspective_switch(subargs)
        elif subcmd == "clear":
            self._cmd_perspective_clear(subargs)
        elif subcmd == "show":
            self._cmd_perspective_show(subargs)
        else:
            # Assume it's a persona ID shortcut: /perspective pm
            self._cmd_perspective_switch([subcmd])

    def _cmd_perspective_list(self, args: list[str]) -> None:
        """List available perspectives."""
        pm = self._get_persona_manager()
        personas = pm.list_personas()

        console.print()
        table = Table(title="Available Perspectives")
        table.add_column("ID", style="bold")
        table.add_column("Name")
        table.add_column("Specialization")
        table.add_column("Focus Areas")

        current = pm.get_current_persona()

        for p in personas:
            marker = "*" if current and p.id == current.id else ""
            focus = ", ".join(p.focus_areas[:3]) if p.focus_areas else "-"
            table.add_row(
                f"{p.id}{marker}",
                p.name,
                p.specialization.value.replace("_", " "),
                focus,
            )

        console.print(table)
        console.print()
        console.print("[dim]Use /perspective switch <id> or just /perspective <id>[/dim]")
        console.print()

    def _cmd_perspective_switch(self, args: list[str]) -> None:
        """Switch to a perspective."""
        if not args:
            console.print("[red]Usage:[/red] /perspective switch <id>")
            console.print("[dim]Example: /perspective pm, /perspective engineer[/dim]")
            return

        persona_id = args[0].lower()
        pm = self._get_persona_manager()
        persona = pm.set_persona(persona_id)

        if not persona:
            console.print(f"[red]Perspective not found:[/red] {persona_id}")
            console.print("[dim]Use /perspective list to see available options[/dim]")
            return

        # Update conversation manager
        conversation = self._get_conversation()
        conversation.set_persona(persona)

        console.print(f"[green]Switched to:[/green] {persona.name}")
        console.print(f"[dim]{persona.perspective}[/dim]")

    def _cmd_perspective_clear(self, args: list[str]) -> None:
        """Clear current perspective."""
        pm = self._get_persona_manager()
        pm.clear_persona()

        if self._conversation:
            self._conversation.set_persona(None)

        console.print("[green]Returned to default assistant perspective[/green]")

    def _cmd_perspective_show(self, args: list[str]) -> None:
        """Show current perspective details."""
        pm = self._get_persona_manager()
        persona = pm.get_current_persona()

        if not persona:
            console.print("[dim]No perspective set (using default assistant)[/dim]")
            console.print("[dim]Use /perspective list to see options[/dim]")
            return

        console.print()
        console.print(f"[bold]Current Perspective:[/bold] {persona.name}")
        console.print(f"[bold]ID:[/bold] {persona.id}")
        console.print(f"[bold]Specialization:[/bold] {persona.specialization.value.replace('_', ' ')}")

        if persona.description:
            console.print(f"\n{persona.description}")

        if persona.perspective:
            console.print(f"\n[bold]Perspective:[/bold] {persona.perspective}")

        if persona.expertise:
            console.print(f"\n[bold]Expertise:[/bold] {', '.join(persona.expertise)}")

        if persona.focus_areas:
            console.print(f"[bold]Focus Areas:[/bold] {', '.join(persona.focus_areas)}")

        if persona.questions_to_ask:
            console.print("\n[bold]Typical Questions:[/bold]")
            for q in persona.questions_to_ask[:5]:
                console.print(f"  - {q}")

        console.print()

    def _cmd_model(self, args: list[str]) -> None:
        """Handle model commands."""
        if not args:
            self._cmd_model_list([])
            return

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "list":
            self._cmd_model_list(subargs)
        elif subcmd == "switch":
            self._cmd_model_switch(subargs)
        else:
            # Assume it's a model ID shortcut: /model sonnet
            self._cmd_model_switch([subcmd])

    def _cmd_model_list(self, args: list[str]) -> None:
        """List available models grouped by provider."""
        console.print()

        current_key = self._conversation.model_key if self._conversation else "sonnet"
        models_by_provider = list_models_by_provider()

        for provider_key, models in models_by_provider.items():
            provider_config = PROVIDERS.get(provider_key, {})
            provider_name = provider_config.get("name", provider_key)
            api_key_env = provider_config.get("api_key_env", "")

            table = Table(title=f"{provider_name} Models", caption=f"[dim]Requires: {api_key_env}[/dim]")
            table.add_column("ID", style="bold")
            table.add_column("Name")
            table.add_column("Description")

            for model in models:
                key = model["key"]
                marker = "*" if key == current_key else ""
                table.add_row(
                    f"{key}{marker}",
                    model["name"],
                    model["description"],
                )

            console.print(table)
            console.print()

        console.print("[dim]Use /model switch <id> or just /model <id>[/dim]")
        console.print()

    def _cmd_model_switch(self, args: list[str]) -> None:
        """Switch to a model."""
        if not args:
            console.print("[red]Usage:[/red] /model switch <id>")
            console.print("[dim]Example: /model sonnet, /model glm-4, /model abab6.5[/dim]")
            return

        model_id = args[0].lower()

        if model_id not in AVAILABLE_MODELS:
            console.print(f"[red]Unknown model:[/red] {model_id}")
            console.print("[dim]Use /model list to see available options[/dim]")
            return

        conversation = self._get_conversation()
        model_name = conversation.set_model(model_id)

        model_config = AVAILABLE_MODELS[model_id]
        provider = model_config.get("provider", "anthropic")
        provider_name = PROVIDERS.get(provider, {}).get("name", provider)

        if provider != "anthropic":
            console.print(f"[green]Switched to:[/green] {model_name} ({provider_name})")
        else:
            console.print(f"[green]Switched to:[/green] {model_name}")

        console.print(f"[dim]{model_config['description']}[/dim]")

    def _cmd_summarize(self, args: list[str]) -> None:
        """Manually summarize conversation context."""
        if not self._conversation:
            console.print("[dim]No conversation to summarize[/dim]")
            return

        console.print("[dim]Summarizing conversation...[/dim]")

        try:
            with console.status("[bold blue]Summarizing...", spinner="dots"):
                summary = self._conversation.summarize_context()

            console.print("[green]Context summarized[/green]")
            console.print()
            console.print("[bold]Summary:[/bold]")
            console.print(summary)
            console.print()
            console.print(f"[dim]{self._conversation.get_context_summary()}[/dim]")

        except ValueError as e:
            console.print(f"[red]Configuration error:[/red] {e}")
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
