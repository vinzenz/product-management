# Planner Implementation Plan

## Document Info

| Field | Value |
|-------|-------|
| Created | 2026-01-02 |
| Status | Ready for Implementation |
| Priority | Next Major Feature |

---

## 1. Executive Summary

Build a multi-iteration planner system that transforms PM artifacts (PRD, features, requirements) into executable tasks. The system works in phases with **cleared context** between each iteration, allowing constrained LLM agents to produce high-quality output without context overflow.

### Core Concept

```
PRD + Features + Requirements
         ↓
┌─────────────────────────────────────┐
│  Phase 1: Technical Architect       │  ← Fresh context
│  Output: layers, tech stack, APIs   │
└─────────────────────────────────────┘
         ↓ [Clear context, pass artifacts]
┌─────────────────────────────────────┐
│  Phase 2: Layer Planner (per layer) │  ← Fresh context
│  Output: groups within layer        │
└─────────────────────────────────────┘
         ↓ [Clear context, pass artifacts]
┌─────────────────────────────────────┐
│  Phase 3: Group Planner (per group) │  ← Fresh context
│  Output: T-*.md task files          │
└─────────────────────────────────────┘
         ↓
Ready for Execution
```

---

## 2. Design Decisions

### 2.1 Context Management

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Context between iterations | **Cleared** | Prevents context overflow, ensures predictable behavior |
| Context passing method | **File-based artifacts** | YAML/markdown files as contracts between phases |
| Conversation history | **Not passed** | Only structured outputs cross phase boundaries |

### 2.2 Tech Documentation

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Version selection | **Latest stable, no CVEs** | Security + modern APIs |
| Doc storage | **Local in project** | Fast lookup, version-matched |
| Doc format | **Summarized for LLM** | ~2K tokens per tech, focused on API essentials |

### 2.3 Interaction Model

| Decision | Choice | Rationale |
|----------|--------|-----------|
| User interaction | **Interactive throughout** | Can ask questions at any phase |
| Checkpoints | **After each major phase** | User approves before proceeding |
| Autonomy | **Guided, not fully autonomous** | User maintains control |

### 2.4 Project Type Support

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Greenfield | **Supported** | Full architecture from scratch |
| Brownfield | **Supported** | Analyze existing codebase first |
| Detection | **Configurable per project** | User specifies project type |

---

## 3. Architecture

### 3.1 Module Structure

```
src/pm/core/planner/
├── __init__.py              # Exports: PlannerOrchestrator, phases
├── orchestrator.py          # Main orchestration engine
├── phases.py                # Phase definitions (Architect, Layer, Group)
├── context.py               # Context building from artifacts
├── docs_fetcher.py          # Tech documentation fetching
├── checkpoints.py           # Checkpoint/approval management
└── codebase_analyzer.py     # Brownfield codebase analysis

src/pm/models/planner.py     # Data models for planning artifacts

src/pm/cli/plan_commands.py  # CLI command handlers

tooling/prompts/planner/
├── architect-phase.md       # System prompt for architect
├── layer-planner.md         # System prompt for layer planning
└── group-planner.md         # System prompt for group planning
```

### 3.2 Key Classes

```python
# orchestrator.py
class PlannerOrchestrator:
    """Orchestrates multi-phase planning."""

    def start_planning(greenfield: bool, target_repo: Path | None) -> PlanningSession
    def run_architect_phase() -> ArchitectOutput
    def run_layer_planning(layer_id: str) -> LayerOutput
    def run_group_planning(layer_id: str, group_id: str) -> list[Task]
    def checkpoint(phase: str) -> bool  # Returns True if approved

# phases.py
class PhaseRunner:
    """Base class for planning phases."""

    def create_fresh_conversation() -> ConversationManager
    def build_context(inputs: dict) -> str
    def run(inputs: dict) -> PhaseOutput

class TechnicalArchitectPhase(PhaseRunner): ...
class LayerPlannerPhase(PhaseRunner): ...
class GroupPlannerPhase(PhaseRunner): ...

# context.py
class ContextBuilder:
    """Builds context strings from artifacts."""

    def load_prd() -> str
    def load_features() -> list[Feature]
    def load_requirements() -> list[Requirement]
    def load_layer_definition(layer_id: str) -> LayerDefinition
    def load_tech_docs(tech_stack: list[str]) -> dict[str, str]
    def build_architect_context() -> str
    def build_layer_context(layer_id: str) -> str
    def build_group_context(layer_id: str, group_id: str) -> str
```

### 3.3 Data Flow

```
Phase 1 (Architect)
├── Input: PRD, features, requirements, [codebase analysis]
├── Process: Analyze → Select tech → Define layers → Define APIs
├── Output:
│   ├── planning/tech-stack.yaml
│   ├── planning/layers.yaml
│   ├── planning/api-specs/*.yaml
│   └── docs/tech/{package}/summary.md (downloaded)
└── Checkpoint: User approves architecture

Phase 2 (Layer Planner) - runs per layer
├── Input: Layer definition, tech-stack, API specs, tech docs
├── Process: Identify groups → Define boundaries → Define contracts
├── Output:
│   └── planning/groups/{layer_id}/groups.yaml
└── Checkpoint: User approves layer breakdown

Phase 3 (Group Planner) - runs per group
├── Input: Group definition, dependent contracts, tech docs
├── Process: Break into tasks → Write contracts → Write tests
├── Output:
│   └── tasks/T-{NNN}-{slug}.md (TASK_FORMAT_SPEC compliant)
└── Checkpoint: User approves tasks
```

---

## 4. Artifact Formats

### 4.1 tech-stack.yaml

```yaml
version: "1.0"
created: "2026-01-02T10:00:00Z"
project_type: "web_application"

runtime:
  language: "typescript"
  version: "5.3.3"
  runtime: "node"
  runtime_version: "20.11.0"

frameworks:
  backend:
    name: "hono"
    version: "4.0.0"
    docs_url: "https://hono.dev/docs"
  frontend:
    name: "react"
    version: "18.2.0"

database:
  type: "postgresql"
  version: "16"
  orm: "drizzle"
  orm_version: "0.29.0"

testing:
  unit: "vitest"
  e2e: "playwright"

dependencies:
  - name: "zod"
    version: "3.22.4"
    purpose: "Schema validation"
  - name: "@tanstack/react-query"
    version: "5.17.0"
    purpose: "Server state management"

security_notes:
  - "All versions checked against npm audit"
  - "No known CVEs in selected versions"
```

### 4.2 layers.yaml

```yaml
version: "1.0"
created: "2026-01-02T10:00:00Z"
architect_summary: |
  System follows clean architecture with 4 layers.

layers:
  - id: "layer-01"
    name: "Infrastructure & Shared"
    order: 1
    description: |
      Foundation layer: config, database, shared types, utilities.
    responsibilities:
      - "Environment configuration"
      - "Database connection"
      - "Shared type definitions"
    outputs:
      - "src/lib/config/"
      - "src/lib/db/"
      - "src/lib/types/"
    depends_on: []

  - id: "layer-02"
    name: "Domain & Data Access"
    order: 2
    description: |
      Core domain logic: entities, repositories, business rules.
    outputs:
      - "src/domain/entities/"
      - "src/domain/repositories/"
      - "src/domain/services/"
    depends_on: ["layer-01"]

  - id: "layer-03"
    name: "Application & API"
    order: 3
    outputs:
      - "src/api/routes/"
      - "src/services/"
    depends_on: ["layer-01", "layer-02"]

  - id: "layer-04"
    name: "User Interface"
    order: 4
    outputs:
      - "src/ui/components/"
      - "src/ui/pages/"
    depends_on: ["layer-03"]
```

### 4.3 groups/{layer_id}/groups.yaml

```yaml
version: "1.0"
layer_id: "layer-02"
layer_name: "Domain & Data Access"

groups:
  - id: "grp-02-01"
    name: "Entity Definitions"
    order: 1
    description: "Drizzle schema definitions"
    contracts:
      exports:
        - name: "userSchema"
          type: "PgTable"
          file: "src/domain/entities/user.ts"
    depends_on_groups: []
    estimated_tasks: 4

  - id: "grp-02-02"
    name: "Repository Layer"
    order: 2
    contracts:
      exports:
        - name: "userRepository"
          type: "UserRepository"
          file: "src/domain/repositories/user.repository.ts"
      interfaces:
        - name: "UserRepository"
          methods:
            - "findById(id: string): Promise<User | null>"
            - "create(data: CreateUserData): Promise<User>"
    depends_on_groups: ["grp-02-01"]
    estimated_tasks: 6

execution_order:
  - ["grp-02-01"]
  - ["grp-02-02"]
```

---

## 5. CLI Commands

```
/plan start                      Start new planning session (greenfield)
/plan start --brownfield         Start with existing codebase analysis
/plan start --target /path       Specify target repo for brownfield

/plan status                     Show current planning status
/plan continue                   Continue from checkpoint
/plan approve [feedback]         Approve current checkpoint
/plan reject <feedback>          Reject and request revision

/plan layers                     List defined layers
/plan groups <layer-id>          List groups in a layer
/plan tasks <group-id>           List tasks in a group
```

---

## 6. Implementation Order

### Phase 1: Foundation (~300 lines)

1. **`src/pm/models/planner.py`** - Data models
   - `PlanningSession`, `TechStack`, `Layer`, `Group` dataclasses
   - Status enums
   - Serialization to/from YAML

2. **`src/pm/core/planner/__init__.py`** - Module setup

### Phase 2: Context Building (~200 lines)

3. **`src/pm/core/planner/context.py`** - ContextBuilder
   - Load all artifact types
   - Build context strings for each phase
   - Filter relevant tech docs

### Phase 3: Phase Infrastructure (~300 lines)

4. **`src/pm/core/planner/phases.py`** - PhaseRunner base + implementations
   - Fresh conversation creation
   - Interactive Q&A handling
   - Output parsing and validation

5. **`src/pm/core/planner/checkpoints.py`** - Checkpoint management
   - Create/approve/reject checkpoints
   - Persist checkpoint state

### Phase 4: Tech Documentation (~200 lines)

6. **`src/pm/core/planner/docs_fetcher.py`** - DocsFetcher
   - Fetch from npm/pypi registries
   - Download README/docs
   - Summarize for LLM context

### Phase 5: Orchestration (~250 lines)

7. **`src/pm/core/planner/orchestrator.py`** - PlannerOrchestrator
   - Coordinate all phases
   - Session management
   - Resume capability

### Phase 6: CLI Integration (~200 lines)

8. **`src/pm/cli/plan_commands.py`** - Command handlers
9. **Modify `src/pm/cli/repl.py`** - Add `/plan` command

### Phase 7: Brownfield Support (~150 lines)

10. **`src/pm/core/planner/codebase_analyzer.py`** - CodebaseAnalyzer
    - Detect tech stack from package.json/pyproject.toml
    - Extract existing patterns
    - Generate constraints for architect

### Phase 8: Prompts

11. **`tooling/prompts/planner/*.md`** - Phase-specific prompts
    - Architect phase prompt
    - Layer planner prompt
    - Group planner prompt

---

## 7. Integration Points

### Existing Code to Use

| Component | Location | Usage |
|-----------|----------|-------|
| ConversationManager | `src/pm/core/conversation.py` | Create fresh instance per phase |
| ArtifactManager | `src/pm/core/artifact.py` | Task CRUD operations |
| Agent configs | `tooling/agents/*.yaml` | Persona + specialization bundles |
| Specializations | `tooling/specialization/*.yaml` | Domain knowledge |
| Storage utils | `src/pm/storage/files.py` | YAML/frontmatter I/O |
| Task format | `docs/TASK_FORMAT_SPEC.md` | Output format for Group Planner |

### Key Pattern: Fresh Conversation

```python
def run_phase(self, phase: PhaseRunner, inputs: dict) -> PhaseOutput:
    # 1. Create fresh conversation (NO history from previous phases)
    conversation = ConversationManager(model=phase.model)

    # 2. Load persona from agent config
    persona = load_persona(phase.agent_config.persona)
    conversation.set_persona(persona)

    # 3. Build context from FILE artifacts (not conversation history)
    context = self.context_builder.build_context(inputs)

    # 4. Run phase
    response = conversation.chat(f"{context}\n\n{phase.task_prompt}")

    # 5. Parse and save output as artifacts
    output = phase.parse_output(response)
    phase.save_artifacts(output)

    return output
```

---

## 8. Testing Strategy

### Unit Tests
- Context building from mock artifacts
- Phase output parsing
- Checkpoint state management

### Integration Tests
- Full architect phase with mock LLM
- Layer → Group flow with file artifacts
- CLI command integration

### Manual Testing
- Run against this project itself (dogfooding)
- Test brownfield with existing open source repo

---

## 9. Current Project State

### Implemented
- ✅ Core PM tool (project, artifact, conversation management)
- ✅ Task artifact type with contract-driven format
- ✅ Persona and specialization configs
- ✅ Agent bundles (6 agents defined)
- ✅ Multi-model support (Anthropic, z.ai, MiniMax)

### Not Yet Implemented
- ❌ Planner orchestration system (this plan)
- ❌ Execution engine (separate future work)
- ❌ Web UI (post-MVP)

---

## 10. Open Questions (Deferred)

These can be resolved during implementation:

1. **Doc fetching rate limits** - How to handle API rate limits for npm/pypi?
2. **Large codebase analysis** - Token limits for brownfield analysis?
3. **Parallel group planning** - Can independent groups be planned in parallel?

---

## 11. Success Criteria

The planner is complete when:

1. ✅ Can run `/plan start` and get through all phases
2. ✅ Produces valid `layers.yaml` and `tech-stack.yaml`
3. ✅ Produces valid `groups.yaml` per layer
4. ✅ Produces valid `T-*.md` tasks per group
5. ✅ Tasks pass TASK_FORMAT_SPEC validation
6. ✅ Can resume from any checkpoint
7. ✅ Works for both greenfield and brownfield

---

## 12. Next Steps

To start implementation:

```bash
# 1. Create the planner module structure
mkdir -p src/pm/core/planner
touch src/pm/core/planner/__init__.py

# 2. Start with models
# Create src/pm/models/planner.py

# 3. Then context builder
# Create src/pm/core/planner/context.py

# 4. Continue with phases, orchestrator, CLI...
```

The implementation order in Section 6 is designed for incremental progress - each piece can be tested independently before moving to the next.
