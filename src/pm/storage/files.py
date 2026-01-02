"""File management utilities for markdown + YAML frontmatter."""

from pathlib import Path
from typing import Any, TypeVar

import frontmatter
import yaml

T = TypeVar("T")


def read_frontmatter_file(path: Path) -> tuple[dict[str, Any], str]:
    """Read a markdown file with YAML frontmatter.

    Returns:
        Tuple of (frontmatter dict, markdown content)
    """
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def write_frontmatter_file(path: Path, metadata: dict[str, Any], content: str) -> None:
    """Write a markdown file with YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(content, **metadata)
    with open(path, "w") as f:
        f.write(frontmatter.dumps(post))


def read_yaml_file(path: Path) -> dict[str, Any]:
    """Read a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def write_yaml_file(path: Path, data: dict[str, Any]) -> None:
    """Write a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


def generate_id(prefix: str, existing_ids: list[str]) -> str:
    """Generate the next sequential ID with a prefix.

    Example: generate_id("F", ["F-001", "F-002"]) -> "F-003"
    """
    max_num = 0
    for id_ in existing_ids:
        if id_.startswith(f"{prefix}-"):
            try:
                num = int(id_.split("-")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                pass
    return f"{prefix}-{max_num + 1:03d}"
