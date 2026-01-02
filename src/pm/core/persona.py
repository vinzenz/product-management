"""Persona management - loading and switching perspectives."""

from pathlib import Path
from typing import Optional

from pm.models.persona import DEFAULT_PERSONAS, Persona
from pm.storage.files import read_yaml_file, write_yaml_file


class PersonaManager:
    """Manages personas for a project."""

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize persona manager.

        Args:
            project_path: Path to project directory. If None, only default personas available.
        """
        self._project_path = project_path
        self._custom_personas: dict[str, Persona] = {}
        self._current_persona: Optional[Persona] = None

        if project_path:
            self._load_custom_personas()

    def _get_personas_dir(self) -> Optional[Path]:
        """Get the personas directory for the current project."""
        if not self._project_path:
            return None
        return self._project_path / "design" / "personas"

    def _load_custom_personas(self) -> None:
        """Load custom personas from project directory."""
        personas_dir = self._get_personas_dir()
        if not personas_dir or not personas_dir.exists():
            return

        for file in personas_dir.glob("*.yaml"):
            try:
                data = read_yaml_file(file)
                persona = Persona.from_dict(data)
                self._custom_personas[persona.id] = persona
            except Exception:
                # Skip invalid persona files
                pass

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a persona by ID.

        Checks custom personas first, then defaults.
        """
        # Check custom personas first (allows overriding defaults)
        if persona_id in self._custom_personas:
            return self._custom_personas[persona_id]
        # Fall back to defaults
        return DEFAULT_PERSONAS.get(persona_id)

    def list_personas(self) -> list[Persona]:
        """List all available personas (custom + defaults)."""
        # Start with defaults
        personas = dict(DEFAULT_PERSONAS)
        # Override with custom personas
        personas.update(self._custom_personas)
        return list(personas.values())

    def get_current_persona(self) -> Optional[Persona]:
        """Get the currently active persona."""
        return self._current_persona

    def set_persona(self, persona_id: str) -> Optional[Persona]:
        """Set the current persona by ID.

        Returns:
            The persona if found, None otherwise.
        """
        persona = self.get_persona(persona_id)
        if persona:
            self._current_persona = persona
        return persona

    def clear_persona(self) -> None:
        """Clear the current persona (return to default assistant)."""
        self._current_persona = None

    def save_persona(self, persona: Persona) -> Path:
        """Save a custom persona to the project.

        Args:
            persona: The persona to save.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If no project path is set.
        """
        if not self._project_path:
            raise ValueError("Cannot save persona without a project")

        personas_dir = self._get_personas_dir()
        personas_dir.mkdir(parents=True, exist_ok=True)

        file_path = personas_dir / f"{persona.id}.yaml"
        write_yaml_file(file_path, persona.to_dict())

        # Update cache
        self._custom_personas[persona.id] = persona

        return file_path

    def delete_persona(self, persona_id: str) -> bool:
        """Delete a custom persona.

        Args:
            persona_id: ID of the persona to delete.

        Returns:
            True if deleted, False if not found or is a default persona.
        """
        if persona_id not in self._custom_personas:
            return False

        personas_dir = self._get_personas_dir()
        if personas_dir:
            file_path = personas_dir / f"{persona_id}.yaml"
            if file_path.exists():
                file_path.unlink()

        del self._custom_personas[persona_id]

        # Clear current if it was the deleted one
        if self._current_persona and self._current_persona.id == persona_id:
            self._current_persona = None

        return True

    def create_project_personas(self) -> None:
        """Create default persona files in the project directory."""
        if not self._project_path:
            return

        personas_dir = self._get_personas_dir()
        personas_dir.mkdir(parents=True, exist_ok=True)

        # Only create if directory is empty
        existing = list(personas_dir.glob("*.yaml"))
        if existing:
            return

        # Save all default personas as starter templates
        for persona in DEFAULT_PERSONAS.values():
            file_path = personas_dir / f"{persona.id}.yaml"
            write_yaml_file(file_path, persona.to_dict())
