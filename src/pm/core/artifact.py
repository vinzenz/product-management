"""Artifact Manager - CRUD operations for features and requirements."""

from pathlib import Path
from typing import Optional

from pm.models.artifact import Feature, Requirement, ArtifactStatus, Priority
from pm.storage.files import (
    read_frontmatter_file,
    write_frontmatter_file,
    generate_id,
    slugify,
    ensure_directory,
)


class ArtifactManager:
    """Manages artifact CRUD operations."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.features_dir = project_path / "features"
        self.fr_dir = project_path / "requirements" / "functional"
        self.nfr_dir = project_path / "requirements" / "non-functional"

        ensure_directory(self.features_dir)
        ensure_directory(self.fr_dir)
        ensure_directory(self.nfr_dir)

    # Feature operations

    def create_feature(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.SHOULD,
    ) -> Feature:
        """Create a new feature."""
        existing_ids = [f.id for f in self.list_features()]
        feature_id = generate_id("F", existing_ids)

        feature = Feature(
            id=feature_id,
            title=title,
            description=description,
            priority=priority,
        )

        self._save_feature(feature)
        return feature

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        """Get a feature by ID."""
        for path in self.features_dir.glob(f"{feature_id}-*.md"):
            frontmatter, content = read_frontmatter_file(path)
            return Feature.from_frontmatter(frontmatter, content)
        return None

    def list_features(self) -> list[Feature]:
        """List all features."""
        features = []
        for path in sorted(self.features_dir.glob("F-*.md")):
            frontmatter, content = read_frontmatter_file(path)
            features.append(Feature.from_frontmatter(frontmatter, content))
        return features

    def update_feature(self, feature: Feature) -> None:
        """Update an existing feature."""
        from datetime import datetime

        feature.updated = datetime.now()
        self._save_feature(feature)

    def delete_feature(self, feature_id: str) -> bool:
        """Delete a feature by ID."""
        for path in self.features_dir.glob(f"{feature_id}-*.md"):
            path.unlink()
            return True
        return False

    def _save_feature(self, feature: Feature) -> None:
        """Save a feature to disk."""
        slug = slugify(feature.title)
        filename = f"{feature.id}-{slug}.md"
        path = self.features_dir / filename
        write_frontmatter_file(path, feature.to_frontmatter(), feature.to_markdown())

    # Requirement operations

    def create_requirement(
        self,
        title: str,
        description: str = "",
        is_functional: bool = True,
        feature_id: Optional[str] = None,
        priority: Priority = Priority.SHOULD,
    ) -> Requirement:
        """Create a new requirement."""
        prefix = "FR" if is_functional else "NFR"
        target_dir = self.fr_dir if is_functional else self.nfr_dir

        existing_ids = [r.id for r in self.list_requirements(is_functional)]
        req_id = generate_id(prefix, existing_ids)

        requirement = Requirement(
            id=req_id,
            title=title,
            description=description,
            feature=feature_id,
            priority=priority,
            is_functional=is_functional,
        )

        self._save_requirement(requirement)
        return requirement

    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        is_functional = req_id.startswith("FR")
        target_dir = self.fr_dir if is_functional else self.nfr_dir

        for path in target_dir.glob(f"{req_id}-*.md"):
            frontmatter, content = read_frontmatter_file(path)
            return Requirement.from_frontmatter(frontmatter, content, is_functional)
        return None

    def list_requirements(self, is_functional: Optional[bool] = None) -> list[Requirement]:
        """List requirements, optionally filtered by type."""
        requirements = []

        if is_functional is None or is_functional:
            for path in sorted(self.fr_dir.glob("FR-*.md")):
                frontmatter, content = read_frontmatter_file(path)
                requirements.append(Requirement.from_frontmatter(frontmatter, content, True))

        if is_functional is None or not is_functional:
            for path in sorted(self.nfr_dir.glob("NFR-*.md")):
                frontmatter, content = read_frontmatter_file(path)
                requirements.append(Requirement.from_frontmatter(frontmatter, content, False))

        return requirements

    def update_requirement(self, requirement: Requirement) -> None:
        """Update an existing requirement."""
        from datetime import datetime

        requirement.updated = datetime.now()
        self._save_requirement(requirement)

    def delete_requirement(self, req_id: str) -> bool:
        """Delete a requirement by ID."""
        is_functional = req_id.startswith("FR")
        target_dir = self.fr_dir if is_functional else self.nfr_dir

        for path in target_dir.glob(f"{req_id}-*.md"):
            path.unlink()
            return True
        return False

    def _save_requirement(self, requirement: Requirement) -> None:
        """Save a requirement to disk."""
        target_dir = self.fr_dir if requirement.is_functional else self.nfr_dir
        slug = slugify(requirement.title)
        filename = f"{requirement.id}-{slug}.md"
        path = target_dir / filename
        write_frontmatter_file(path, requirement.to_frontmatter(), requirement.to_markdown())

    # Linking operations

    def link_requirement_to_feature(self, req_id: str, feature_id: str) -> bool:
        """Link a requirement to a feature."""
        requirement = self.get_requirement(req_id)
        feature = self.get_feature(feature_id)

        if not requirement or not feature:
            return False

        requirement.feature = feature_id
        if req_id not in feature.requirements:
            feature.requirements.append(req_id)

        self.update_requirement(requirement)
        self.update_feature(feature)
        return True
