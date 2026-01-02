"""Project Manager - handles project lifecycle and state."""

from pathlib import Path
from typing import Optional

from pm.models.project import Project, ProjectStatus
from pm.storage.files import read_yaml_file, write_yaml_file, slugify, ensure_directory


class ProjectManager:
    """Manages product management projects."""

    def __init__(self, base_path: Path):
        """Initialize with base path for projects directory."""
        self.base_path = base_path
        self.projects_dir = base_path / "projects"
        self._current_project: Optional[Project] = None
        ensure_directory(self.projects_dir)

    @property
    def current_project(self) -> Optional[Project]:
        """Get the currently active project."""
        return self._current_project

    def create_project(self, name: str, project_id: Optional[str] = None) -> Project:
        """Create a new project with standard directory structure."""
        if project_id is None:
            project_id = slugify(name)

        project_dir = self.projects_dir / project_id
        if project_dir.exists():
            raise ValueError(f"Project '{project_id}' already exists")

        # Create project
        project = Project(id=project_id, name=name)

        # Create directory structure
        self._create_project_structure(project_dir)

        # Write project metadata
        write_yaml_file(project_dir / ".project.yaml", project.to_dict())

        self._current_project = project
        return project

    def _create_project_structure(self, project_dir: Path) -> None:
        """Create the standard project directory structure."""
        dirs = [
            "prd/sections",
            "features",
            "requirements/functional",
            "requirements/non-functional",
            "design/personas",
            "design/journeys",
            "design/wireframes",
            "design/interactions",
            "design/design-system",
            "architecture/adrs",
            "architecture/components",
            "api",
            "data-models",
            "tasks",
            "execution/logs",
            "execution/reviews",
            "memory",
        ]
        for dir_path in dirs:
            ensure_directory(project_dir / dir_path)

        # Create initial overview file
        overview = project_dir / "overview.md"
        overview.write_text("# Project Overview\n\n[Add your project pitch here]\n")

    def list_projects(self) -> list[Project]:
        """List all available projects."""
        projects = []
        if not self.projects_dir.exists():
            return projects

        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                meta_file = project_dir / ".project.yaml"
                if meta_file.exists():
                    data = read_yaml_file(meta_file)
                    projects.append(Project.from_dict(data))

        return sorted(projects, key=lambda p: p.updated, reverse=True)

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        project_dir = self.projects_dir / project_id
        meta_file = project_dir / ".project.yaml"

        if not meta_file.exists():
            return None

        data = read_yaml_file(meta_file)
        return Project.from_dict(data)

    def switch_project(self, project_id: str) -> Project:
        """Switch to a different project."""
        project = self.get_project(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' not found")

        self._current_project = project
        return project

    def update_project(self, project: Project) -> None:
        """Update project metadata."""
        from datetime import datetime

        project.updated = datetime.now()
        project_dir = self.projects_dir / project.id
        write_yaml_file(project_dir / ".project.yaml", project.to_dict())

        if self._current_project and self._current_project.id == project.id:
            self._current_project = project

    def set_status(self, status: ProjectStatus) -> None:
        """Update the current project's status."""
        if not self._current_project:
            raise ValueError("No project selected")

        self._current_project.status = status
        self.update_project(self._current_project)

    def get_project_path(self, project_id: Optional[str] = None) -> Path:
        """Get the path to a project directory."""
        if project_id is None:
            if self._current_project is None:
                raise ValueError("No project selected")
            project_id = self._current_project.id

        return self.projects_dir / project_id
