"""Documentation Fetcher - Fetches and summarizes tech documentation for planning."""

import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from pm.storage.files import ensure_directory


class DocsFetcher:
    """Fetches and caches technology documentation for planning phases.

    Downloads documentation from npm/pypi registries and summarizes
    it for efficient LLM context usage (~2K tokens per tech).
    """

    # Target token count for summaries (roughly 8K characters)
    TARGET_SUMMARY_CHARS = 8000

    def __init__(self, project_path: Path):
        """Initialize the docs fetcher.

        Args:
            project_path: Path to the project root.
        """
        self.project_path = project_path
        self.docs_dir = project_path / "docs" / "tech"
        ensure_directory(self.docs_dir)

    def fetch_npm_package_info(self, package_name: str) -> Optional[dict]:
        """Fetch package info from npm registry.

        Args:
            package_name: Name of the npm package.

        Returns:
            Package info dict, or None if not found.
        """
        import urllib.request
        import urllib.error

        # Handle scoped packages (@org/pkg -> %40org%2Fpkg)
        encoded_name = quote(package_name, safe="")
        url = f"https://registry.npmjs.org/{encoded_name}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return None

    def fetch_pypi_package_info(self, package_name: str) -> Optional[dict]:
        """Fetch package info from PyPI.

        Args:
            package_name: Name of the PyPI package.

        Returns:
            Package info dict, or None if not found.
        """
        import urllib.request
        import urllib.error

        url = f"https://pypi.org/pypi/{package_name}/json"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            return None

    def extract_npm_readme(self, package_info: dict) -> str:
        """Extract README content from npm package info.

        Args:
            package_info: Package info from npm registry.

        Returns:
            README content or empty string.
        """
        return package_info.get("readme", "")

    def extract_pypi_description(self, package_info: dict) -> str:
        """Extract description from PyPI package info.

        Args:
            package_info: Package info from PyPI.

        Returns:
            Description content or empty string.
        """
        info = package_info.get("info", {})
        return info.get("description", "")

    def summarize_documentation(self, content: str, package_name: str) -> str:
        """Summarize documentation for LLM context.

        Extracts key sections and trims to target size.

        Args:
            content: Raw documentation content.
            package_name: Name of the package.

        Returns:
            Summarized documentation.
        """
        if not content:
            return f"# {package_name}\n\nNo documentation available."

        # Extract key sections
        sections = self._extract_key_sections(content)

        # Build summary
        summary_parts = [f"# {package_name}\n"]

        # Prioritize sections by importance
        priority_order = [
            "description",
            "installation",
            "quick_start",
            "usage",
            "api",
            "configuration",
            "examples",
        ]

        remaining_chars = self.TARGET_SUMMARY_CHARS - len(summary_parts[0])

        for section_name in priority_order:
            if section_name in sections and remaining_chars > 0:
                section_content = sections[section_name]
                # Truncate if needed
                if len(section_content) > remaining_chars:
                    section_content = section_content[:remaining_chars] + "..."
                summary_parts.append(section_content)
                remaining_chars -= len(section_content)

        return "\n\n".join(summary_parts)

    def _extract_key_sections(self, content: str) -> dict[str, str]:
        """Extract key sections from markdown documentation.

        Args:
            content: Raw markdown content.

        Returns:
            Dict mapping section names to content.
        """
        sections = {}

        # Extract first paragraph as description
        first_para_match = re.search(r"^(?:#[^\n]*\n+)?([^\n#]+(?:\n[^\n#]+)*)", content)
        if first_para_match:
            sections["description"] = first_para_match.group(1).strip()[:1000]

        # Common section patterns
        section_patterns = {
            "installation": r"##?\s*(?:Install(?:ation)?|Getting\s+Started)\s*\n(.*?)(?=\n##|\Z)",
            "quick_start": r"##?\s*(?:Quick\s+Start|Quickstart)\s*\n(.*?)(?=\n##|\Z)",
            "usage": r"##?\s*(?:Usage|Basic\s+Usage)\s*\n(.*?)(?=\n##|\Z)",
            "api": r"##?\s*(?:API|API\s+Reference)\s*\n(.*?)(?=\n##|\Z)",
            "configuration": r"##?\s*(?:Config(?:uration)?|Options)\s*\n(.*?)(?=\n##|\Z)",
            "examples": r"##?\s*(?:Examples?)\s*\n(.*?)(?=\n##|\Z)",
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1).strip()
                # Limit each section
                sections[section_name] = section_content[:2000]

        return sections

    def fetch_and_cache(self, package_name: str, registry: str = "npm") -> Optional[Path]:
        """Fetch documentation and cache it locally.

        Args:
            package_name: Name of the package.
            registry: Registry to fetch from ("npm" or "pypi").

        Returns:
            Path to the cached summary, or None if fetch failed.
        """
        # Check cache first
        cache_dir = self.docs_dir / package_name.lower().replace("/", "-").replace("@", "")
        summary_path = cache_dir / "summary.md"

        if summary_path.exists():
            return summary_path

        # Fetch from registry
        if registry == "npm":
            package_info = self.fetch_npm_package_info(package_name)
            if package_info:
                content = self.extract_npm_readme(package_info)
            else:
                content = ""
        elif registry == "pypi":
            package_info = self.fetch_pypi_package_info(package_name)
            if package_info:
                content = self.extract_pypi_description(package_info)
            else:
                content = ""
        else:
            return None

        # Summarize and cache
        summary = self.summarize_documentation(content, package_name)

        ensure_directory(cache_dir)
        summary_path.write_text(summary)

        # Also save metadata
        if package_info:
            meta_path = cache_dir / "meta.json"
            meta = self._extract_metadata(package_info, registry)
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

        return summary_path

    def _extract_metadata(self, package_info: dict, registry: str) -> dict:
        """Extract package metadata.

        Args:
            package_info: Package info from registry.
            registry: Registry name.

        Returns:
            Metadata dict.
        """
        if registry == "npm":
            latest = package_info.get("dist-tags", {}).get("latest", "")
            return {
                "name": package_info.get("name", ""),
                "version": latest,
                "description": package_info.get("description", ""),
                "homepage": package_info.get("homepage", ""),
                "repository": package_info.get("repository", {}).get("url", ""),
                "license": package_info.get("license", ""),
                "registry": "npm",
            }
        elif registry == "pypi":
            info = package_info.get("info", {})
            return {
                "name": info.get("name", ""),
                "version": info.get("version", ""),
                "description": info.get("summary", ""),
                "homepage": info.get("home_page", ""),
                "repository": info.get("project_urls", {}).get("Repository", ""),
                "license": info.get("license", ""),
                "registry": "pypi",
            }
        return {}

    def fetch_tech_stack_docs(
        self,
        tech_names: list[str],
        registry: str = "npm",
    ) -> dict[str, str]:
        """Fetch documentation for a list of technologies.

        Args:
            tech_names: List of package/technology names.
            registry: Default registry to use.

        Returns:
            Dict mapping tech name to summary content.
        """
        docs = {}

        for tech_name in tech_names:
            # Try to detect registry from package name
            if tech_name.startswith("@") or "-" in tech_name:
                # Likely npm
                actual_registry = "npm"
            elif "_" in tech_name or tech_name.islower():
                # Could be pypi
                actual_registry = registry
            else:
                actual_registry = registry

            summary_path = self.fetch_and_cache(tech_name, actual_registry)
            if summary_path and summary_path.exists():
                docs[tech_name] = summary_path.read_text()

        return docs

    def get_cached_docs(self, tech_name: str) -> Optional[str]:
        """Get cached documentation for a technology.

        Args:
            tech_name: Name of the technology.

        Returns:
            Cached summary content, or None if not cached.
        """
        cache_dir = self.docs_dir / tech_name.lower().replace("/", "-").replace("@", "")
        summary_path = cache_dir / "summary.md"

        if summary_path.exists():
            return summary_path.read_text()
        return None

    def list_cached_docs(self) -> list[str]:
        """List all cached documentation.

        Returns:
            List of cached technology names.
        """
        cached = []
        if self.docs_dir.exists():
            for subdir in self.docs_dir.iterdir():
                if subdir.is_dir() and (subdir / "summary.md").exists():
                    cached.append(subdir.name)
        return sorted(cached)

    def clear_cache(self, tech_name: Optional[str] = None) -> int:
        """Clear cached documentation.

        Args:
            tech_name: Specific tech to clear, or None to clear all.

        Returns:
            Number of items cleared.
        """
        import shutil

        cleared = 0

        if tech_name:
            cache_dir = self.docs_dir / tech_name.lower().replace("/", "-").replace("@", "")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cleared = 1
        else:
            if self.docs_dir.exists():
                for subdir in self.docs_dir.iterdir():
                    if subdir.is_dir():
                        shutil.rmtree(subdir)
                        cleared += 1

        return cleared
