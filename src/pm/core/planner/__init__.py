"""Planner module - Multi-phase planning system for PM artifacts.

This module provides orchestration for transforming PM artifacts (PRD, features,
requirements) into executable tasks through a multi-phase planning process:

1. Technical Architect Phase: Analyzes requirements, selects tech stack, defines layers
2. Layer Planner Phase: Breaks each layer into functional groups
3. Group Planner Phase: Creates executable T-*.md task files

Each phase runs with a fresh conversation context, passing only file artifacts
between phases to prevent context overflow.
"""

from pm.core.planner.orchestrator import PlannerOrchestrator
from pm.core.planner.phases import (
    GroupPlannerPhase,
    LayerPlannerPhase,
    PhaseRunner,
    TechnicalArchitectPhase,
)
from pm.core.planner.context import ContextBuilder
from pm.core.planner.checkpoints import CheckpointManager
from pm.core.planner.codebase_analyzer import CodebaseAnalyzer
from pm.core.planner.docs_fetcher import DocsFetcher

__all__ = [
    "PlannerOrchestrator",
    "PhaseRunner",
    "TechnicalArchitectPhase",
    "LayerPlannerPhase",
    "GroupPlannerPhase",
    "ContextBuilder",
    "CheckpointManager",
    "CodebaseAnalyzer",
    "DocsFetcher",
]
