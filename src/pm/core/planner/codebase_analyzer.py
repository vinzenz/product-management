"""Codebase Analyzer - Analyzes existing codebases for brownfield planning."""

import json
import re
from pathlib import Path
from typing import Optional

from pm.models.planner import CodebaseAnalysis, Dependency, ExistingPattern
from pm.storage.files import read_yaml_file, write_yaml_file, ensure_directory


class CodebaseAnalyzer:
    """Analyzes existing codebases to extract patterns and constraints.

    Used for brownfield projects to understand the existing tech stack,
    patterns, and constraints before planning new features.
    """

    def __init__(self, target_repo: Path):
        """Initialize the analyzer.

        Args:
            target_repo: Path to the repository to analyze.
        """
        self.target_repo = target_repo

    def analyze(self) -> CodebaseAnalysis:
        """Run full codebase analysis.

        Returns:
            Complete analysis results.
        """
        analysis = CodebaseAnalysis()

        # Detect package manager and dependencies
        self._analyze_package_manager(analysis)

        # Detect language and framework
        self._detect_language_and_framework(analysis)

        # Analyze directory structure
        self._analyze_directory_structure(analysis)

        # Detect patterns
        self._detect_patterns(analysis)

        # Generate constraints
        self._generate_constraints(analysis)

        return analysis

    def _analyze_package_manager(self, analysis: CodebaseAnalysis) -> None:
        """Detect package manager and extract dependencies."""
        # Check for Node.js / npm
        package_json = self.target_repo / "package.json"
        if package_json.exists():
            analysis.package_manager = "npm"
            self._extract_npm_dependencies(package_json, analysis)
            return

        # Check for Python / pip
        pyproject = self.target_repo / "pyproject.toml"
        if pyproject.exists():
            analysis.package_manager = "pip"
            self._extract_python_dependencies(pyproject, analysis)
            return

        requirements = self.target_repo / "requirements.txt"
        if requirements.exists():
            analysis.package_manager = "pip"
            self._extract_requirements_txt(requirements, analysis)
            return

        # Check for Go
        go_mod = self.target_repo / "go.mod"
        if go_mod.exists():
            analysis.package_manager = "go"
            self._extract_go_dependencies(go_mod, analysis)
            return

        # Check for Rust
        cargo_toml = self.target_repo / "Cargo.toml"
        if cargo_toml.exists():
            analysis.package_manager = "cargo"
            return

    def _extract_npm_dependencies(
        self,
        package_json: Path,
        analysis: CodebaseAnalysis,
    ) -> None:
        """Extract dependencies from package.json."""
        try:
            with open(package_json) as f:
                data = json.load(f)

            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})

            for name, version in deps.items():
                analysis.existing_dependencies.append(
                    Dependency(name=name, version=version.lstrip("^~"), purpose="dependency")
                )

            for name, version in dev_deps.items():
                analysis.existing_dependencies.append(
                    Dependency(name=name, version=version.lstrip("^~"), purpose="dev dependency")
                )

        except (json.JSONDecodeError, IOError):
            pass

    def _extract_python_dependencies(
        self,
        pyproject: Path,
        analysis: CodebaseAnalysis,
    ) -> None:
        """Extract dependencies from pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            return

        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)

            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                # Parse "package>=1.0" format
                match = re.match(r"([a-zA-Z0-9_-]+)(?:[>=<]+)?(.+)?", dep)
                if match:
                    name = match.group(1)
                    version = match.group(2) or "latest"
                    analysis.existing_dependencies.append(
                        Dependency(name=name, version=version, purpose="dependency")
                    )

        except (IOError, KeyError):
            pass

    def _extract_requirements_txt(
        self,
        requirements: Path,
        analysis: CodebaseAnalysis,
    ) -> None:
        """Extract dependencies from requirements.txt."""
        try:
            content = requirements.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse "package==1.0" format
                match = re.match(r"([a-zA-Z0-9_-]+)(?:[>=<]+)?(.+)?", line)
                if match:
                    name = match.group(1)
                    version = match.group(2) or "latest"
                    analysis.existing_dependencies.append(
                        Dependency(name=name, version=version, purpose="dependency")
                    )

        except IOError:
            pass

    def _extract_go_dependencies(
        self,
        go_mod: Path,
        analysis: CodebaseAnalysis,
    ) -> None:
        """Extract dependencies from go.mod."""
        try:
            content = go_mod.read_text()
            # Match require block
            require_match = re.search(r"require\s*\((.*?)\)", content, re.DOTALL)
            if require_match:
                for line in require_match.group(1).splitlines():
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        analysis.existing_dependencies.append(
                            Dependency(name=parts[0], version=parts[1], purpose="dependency")
                        )

        except IOError:
            pass

    def _detect_language_and_framework(self, analysis: CodebaseAnalysis) -> None:
        """Detect primary language and framework."""
        # Based on package manager
        if analysis.package_manager == "npm":
            analysis.detected_language = "typescript" if self._has_typescript() else "javascript"
            analysis.detected_framework = self._detect_js_framework(analysis)

        elif analysis.package_manager == "pip":
            analysis.detected_language = "python"
            analysis.detected_framework = self._detect_python_framework(analysis)

        elif analysis.package_manager == "go":
            analysis.detected_language = "go"
            analysis.detected_framework = self._detect_go_framework(analysis)

        elif analysis.package_manager == "cargo":
            analysis.detected_language = "rust"

    def _has_typescript(self) -> bool:
        """Check if project uses TypeScript."""
        tsconfig = self.target_repo / "tsconfig.json"
        return tsconfig.exists()

    def _detect_js_framework(self, analysis: CodebaseAnalysis) -> str:
        """Detect JavaScript/TypeScript framework."""
        dep_names = {d.name for d in analysis.existing_dependencies}

        if "next" in dep_names:
            return "next"
        if "react" in dep_names:
            return "react"
        if "vue" in dep_names:
            return "vue"
        if "svelte" in dep_names:
            return "svelte"
        if "hono" in dep_names:
            return "hono"
        if "express" in dep_names:
            return "express"
        if "fastify" in dep_names:
            return "fastify"
        if "@nestjs/core" in dep_names:
            return "nestjs"

        return "unknown"

    def _detect_python_framework(self, analysis: CodebaseAnalysis) -> str:
        """Detect Python framework."""
        dep_names = {d.name.lower() for d in analysis.existing_dependencies}

        if "django" in dep_names:
            return "django"
        if "flask" in dep_names:
            return "flask"
        if "fastapi" in dep_names:
            return "fastapi"
        if "starlette" in dep_names:
            return "starlette"

        return "unknown"

    def _detect_go_framework(self, analysis: CodebaseAnalysis) -> str:
        """Detect Go framework."""
        dep_names = {d.name for d in analysis.existing_dependencies}

        if "github.com/gin-gonic/gin" in dep_names:
            return "gin"
        if "github.com/labstack/echo" in dep_names:
            return "echo"
        if "github.com/gofiber/fiber" in dep_names:
            return "fiber"

        return "standard-library"

    def _analyze_directory_structure(self, analysis: CodebaseAnalysis) -> None:
        """Analyze directory structure."""
        structure = {}

        # Look for common directory patterns
        common_dirs = [
            "src",
            "lib",
            "app",
            "api",
            "components",
            "pages",
            "routes",
            "models",
            "services",
            "utils",
            "helpers",
            "tests",
            "test",
            "__tests__",
            "spec",
            "config",
            "scripts",
            "public",
            "static",
            "assets",
        ]

        for dir_name in common_dirs:
            dir_path = self.target_repo / dir_name
            if dir_path.exists() and dir_path.is_dir():
                structure[dir_name] = self._get_dir_summary(dir_path)

        analysis.directory_structure = structure

    def _get_dir_summary(self, path: Path, depth: int = 1) -> dict:
        """Get summary of directory contents."""
        summary = {"type": "directory", "children": []}

        if depth > 2:  # Limit depth
            return summary

        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.name == "node_modules":
                    continue

                if item.is_file():
                    summary["children"].append(item.name)
                elif item.is_dir():
                    summary["children"].append({
                        item.name: self._get_dir_summary(item, depth + 1)
                    })

        except PermissionError:
            pass

        return summary

    def _detect_patterns(self, analysis: CodebaseAnalysis) -> None:
        """Detect coding patterns in the codebase."""
        patterns = []

        # Check for common patterns based on directory structure
        dirs = set(analysis.directory_structure.keys())

        if "components" in dirs:
            patterns.append(
                ExistingPattern(
                    name="Component-based UI",
                    description="UI is organized into reusable components",
                    files=["components/"],
                )
            )

        if "services" in dirs:
            patterns.append(
                ExistingPattern(
                    name="Service Layer",
                    description="Business logic is organized into services",
                    files=["services/"],
                )
            )

        if "models" in dirs:
            patterns.append(
                ExistingPattern(
                    name="Model Layer",
                    description="Data models are defined separately",
                    files=["models/"],
                )
            )

        if "routes" in dirs or "api" in dirs:
            patterns.append(
                ExistingPattern(
                    name="Route-based API",
                    description="API is organized by routes",
                    files=["routes/", "api/"],
                )
            )

        # Check for specific file patterns
        src_dir = self.target_repo / "src"
        if src_dir.exists():
            # Look for barrel files
            index_files = list(src_dir.rglob("index.ts")) + list(src_dir.rglob("index.js"))
            if len(index_files) > 3:
                patterns.append(
                    ExistingPattern(
                        name="Barrel Exports",
                        description="Modules use index files for clean exports",
                        files=[str(f.relative_to(self.target_repo)) for f in index_files[:5]],
                    )
                )

            # Look for test colocated with source
            test_files = list(src_dir.rglob("*.test.ts")) + list(src_dir.rglob("*.spec.ts"))
            if test_files:
                patterns.append(
                    ExistingPattern(
                        name="Colocated Tests",
                        description="Tests are placed alongside source files",
                        files=[str(f.relative_to(self.target_repo)) for f in test_files[:5]],
                    )
                )

        analysis.patterns = patterns

    def _generate_constraints(self, analysis: CodebaseAnalysis) -> None:
        """Generate constraints based on existing codebase."""
        constraints = []

        if analysis.detected_language:
            constraints.append(f"Must use {analysis.detected_language}")

        if analysis.detected_framework and analysis.detected_framework != "unknown":
            constraints.append(f"Must be compatible with {analysis.detected_framework} framework")

        if analysis.package_manager:
            constraints.append(f"Must use {analysis.package_manager} for dependency management")

        # Check for strict TypeScript
        if analysis.detected_language == "typescript":
            tsconfig = self.target_repo / "tsconfig.json"
            if tsconfig.exists():
                try:
                    with open(tsconfig) as f:
                        data = json.load(f)
                    compiler_opts = data.get("compilerOptions", {})
                    if compiler_opts.get("strict"):
                        constraints.append("Must follow strict TypeScript mode")
                except (json.JSONDecodeError, IOError):
                    pass

        # Check for existing test framework
        for dep in analysis.existing_dependencies:
            if dep.name in ("vitest", "jest", "mocha", "pytest", "go-test"):
                constraints.append(f"Tests must use {dep.name}")
                break

        # Check for linting/formatting
        eslint_config = self.target_repo / ".eslintrc.json"
        prettier_config = self.target_repo / ".prettierrc"
        if eslint_config.exists() or prettier_config.exists():
            constraints.append("Must pass existing linting rules")

        analysis.constraints = constraints

    def save_analysis(self, project_path: Path) -> Path:
        """Run analysis and save results.

        Args:
            project_path: Path to save analysis to.

        Returns:
            Path to saved analysis file.
        """
        analysis = self.analyze()

        planning_dir = project_path / "planning"
        ensure_directory(planning_dir)

        analysis_path = planning_dir / "codebase-analysis.yaml"
        write_yaml_file(analysis_path, analysis.to_dict())

        return analysis_path
