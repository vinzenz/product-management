# Technical Specification: Product Management System

## Document Info

| Field | Value |
|-------|-------|
| Version | 0.1.0-draft |
| Status | Draft |
| Created | 2026-01-02 |
| Source | INTERVIEW_LOG.md |

---

## 1. Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python |
| CLI Framework | TBD (e.g., Click, Typer) |
| Storage | Flat files (Markdown + YAML frontmatter + JSON) |
| Version Control | Git (leveraged directly) |
| LLM Integration | Claude Code CLI, opencode CLI |
| Web UI (post-MVP) | TBD |

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                        │
│  ┌─────────────┐                    ┌─────────────────┐     │
│  │  CLI (REPL) │                    │  Web UI (future)│     │
│  └──────┬──────┘                    └────────┬────────┘     │
└─────────┼────────────────────────────────────┼──────────────┘
          │                                    │
          ▼                                    ▼
┌─────────────────────────────────────────────────────────────┐
│                       Core Engine                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Conversation │  │   Artifact   │  │   Knowledge      │  │
│  │   Manager    │  │   Manager    │  │   Manager        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Agent     │  │   Workflow   │  │     Project      │  │
│  │  Orchestrator│  │   Engine     │  │     Manager      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Execution System                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Task Runner  │  │  CLI Driver  │  │   Log Collector  │  │
│  │              │  │ (Claude Code)│  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Verifier    │  │   Reviewer   │  │  Post-Mortem     │  │
│  │              │  │  (indep LLM) │  │   Analyzer       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Storage Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Projects   │  │   Tooling    │  │   Knowledge      │  │
│  │   (files)    │  │   (configs)  │  │   (templates)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| Conversation Manager | Handle REPL sessions, context, model switching |
| Artifact Manager | CRUD for all artifact types, validation, linking |
| Knowledge Manager | Templates, prompts, decision records, extraction |
| Agent Orchestrator | Load/compose agents from persona+specialization+workflow |
| Workflow Engine | Execute workflow stages, suggest perspectives |
| Project Manager | Project lifecycle, status tracking, phase transitions |
| Task Runner | DAG execution, parallelization, scheduling |
| CLI Driver | Interface with Claude Code / opencode |
| Log Collector | Structured JSON logging of all execution events |
| Verifier | Run tests, static analysis, self-review |
| Reviewer | Independent LLM review of changes |
| Post-Mortem Analyzer | Analyze failures, extract learnings |

---

## 3. Directory Structure

### 3.1 Repository Root

```
product-management/
├── docs/                    # System documentation
│   ├── PRD.md
│   └── TECHNICAL_SPEC.md
├── projects/                # Individual projects
│   └── {project-slug}/
├── tooling/                 # System configuration
│   ├── agents/              # Agent definitions
│   ├── personas/            # Persona configs
│   ├── specializations/     # Domain knowledge configs
│   ├── workflows/           # Workflow definitions
│   └── prompts/             # Proven prompts
├── knowledge/               # Extracted knowledge
│   ├── templates/           # Document templates
│   ├── patterns/            # Code/design patterns
│   └── decisions/           # Decision records
└── INTERVIEW_LOG.md         # Source interview
```

### 3.2 Project Structure

```
projects/{project-slug}/
├── .project.yaml            # Project metadata
├── overview.md              # Project overview/pitch
├── prd/
│   ├── summary.md           # PRD summary
│   └── sections/            # PRD sections
├── features/
│   ├── F-001-{slug}.md
│   ├── F-002-{slug}.md
│   └── ...
├── requirements/
│   ├── functional/
│   │   ├── FR-001-{slug}.md
│   │   └── ...
│   └── non-functional/
│       ├── NFR-001-{slug}.md
│       └── ...
├── design/
│   ├── personas/
│   ├── journeys/
│   ├── wireframes/
│   ├── interactions/
│   └── design-system/
├── architecture/
│   ├── overview.md
│   ├── adrs/                # Architecture Decision Records
│   │   ├── ADR-001-{slug}.md
│   │   └── ...
│   └── components/
├── api/
│   └── {format-appropriate-files}
├── data-models/
├── tasks/
│   ├── T-001-{slug}.md
│   ├── T-002-{slug}.md
│   └── ...
├── execution/
│   ├── logs/                # Execution logs (JSON)
│   └── reviews/             # Independent review records
└── memory/                  # Project-specific memory
    └── decisions.json
```

---

## 4. Data Models

### 4.1 Project Metadata (.project.yaml)

```yaml
id: "project-slug"
name: "Project Display Name"
status: "ideation|requirements|design|architecture|planning|executing|review|archived"
created: "2026-01-02T10:00:00Z"
updated: "2026-01-02T15:30:00Z"
git_branch: "main"
target_repo: "/path/to/implementation/repo"  # optional, for brownfield
```

### 4.2 Feature File (features/F-001-*.md)

```yaml
---
id: F-001
title: "Feature Title"
status: draft|approved|implemented|verified
priority: must|should|could|wont
created: "2026-01-02T10:00:00Z"
updated: "2026-01-02T10:00:00Z"
requirements: [FR-001, FR-002]
---

# Feature Title

## Description

[Feature description]

## User Stories

[User stories]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
```

### 4.3 Requirement File (requirements/functional/FR-001-*.md)

```yaml
---
id: FR-001
title: "Requirement Title"
status: draft|approved|implemented|verified
priority: must|should|could|wont
feature: F-001
created: "2026-01-02T10:00:00Z"
updated: "2026-01-02T10:00:00Z"
tasks: [T-001, T-002]
---

# Requirement Title

## Description

[Requirement description]

## Rationale

[Why this requirement exists]

## Acceptance Criteria

- [ ] Criterion 1
```

### 4.4 Task File (tasks/T-001-*.md)

Tasks use the **Contract-Driven Task Format** optimized for autonomous LLM execution.

> **Full specification**: See [TASK_FORMAT_SPEC.md](./TASK_FORMAT_SPEC.md)

```yaml
---
id: T-001
title: "Task Title"
status: pending|in_progress|completed|failed|blocked
layer: 1
track: backend|frontend|shared
depends_on: [T-000]
estimated_complexity: trivial|simple|medium|complex
---

# T-001: Task Title

## Contract
[TypeScript signatures defining exports]

## Dependencies (Interfaces Only)
[Interface contracts from dependent tasks]

## Test Specification
[Complete, runnable test code]

## Output Files
[Files to create/modify with line estimates]

## Verification (Deterministic)
[Exact bash commands - no LLM judgment]

## Done When
[Checkable acceptance criteria]
```

**Key principles:**
- Contracts are type signatures, not prose
- Tests ARE the spec
- Interfaces instead of full file reads
- Micro-tasks: <50 lines output, <2K tokens
- Deterministic verification (TypeScript + tests)

### 4.5 Agent Definition (tooling/agents/*.yaml)

```yaml
id: "architect-agent"
name: "Software Architect"
description: "Technical architecture and system design perspective"
model: "claude-sonnet"  # default model
persona: "analytical"
specialization: "software-architecture"
workflow: "architecture-review"  # optional
```

### 4.6 Persona Definition (tooling/personas/*.yaml)

```yaml
id: "analytical"
name: "Analytical Thinker"
description: "Systematic, detail-oriented approach"
system_prompt_additions: |
  You approach problems systematically, breaking them down into components.
  You ask clarifying questions before making assumptions.
  You consider edge cases and potential issues proactively.
```

### 4.7 Specialization Definition (tooling/specializations/*.yaml)

```yaml
id: "software-architecture"
name: "Software Architecture"
description: "System design, patterns, technical decisions"
knowledge_areas:
  - "Design patterns"
  - "System scalability"
  - "API design"
  - "Data modeling"
system_prompt_additions: |
  You have deep expertise in software architecture including:
  - Distributed systems design
  - API design best practices
  - Database selection and modeling
  - Performance optimization strategies
```

### 4.8 Execution Log Entry (execution/logs/*.jsonl)

```json
{
  "timestamp": "2026-01-02T10:30:00Z",
  "event_type": "task_start|task_end|file_change|command_run|error",
  "task_id": "T-001",
  "details": {
    "files_changed": ["src/Button.tsx"],
    "command": "npm test",
    "exit_code": 0,
    "duration_ms": 1500
  }
}
```

---

## 5. LLM Integration

### 5.1 Provider Abstraction

```python
class LLMProvider(Protocol):
    def complete(self, messages: list[Message], **kwargs) -> Response: ...
    def summarize(self, content: str) -> str: ...

class ClaudeCodeDriver(LLMProvider):
    """Drives Claude Code CLI for execution tasks"""

class ConversationProvider(LLMProvider):
    """Direct API for conversation (Claude, OpenAI, MiniMax, GLM)"""
```

### 5.2 Model Selection

- Smart defaults based on task type
- User can override per-task or globally
- Agent definitions specify default model

### 5.3 Context Handoff

When switching models:
1. Generate summary of current state
2. Pass summary + current artifacts to new model
3. Silent handoff (user doesn't see summary)

---

## 6. Execution System

### 6.1 Task Execution Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Load Task    │────▶│ Place in     │────▶│ Start CLI    │
│ from File    │     │ Target Repo  │     │ (Claude Code)│
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
         ┌───────────────────────────────────────┘
         ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Monitor      │────▶│ Collect      │────▶│ Task         │
│ Execution    │     │ Logs         │     │ Complete?    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                     ┌───────────────────────────┼───────────────────┐
                     ▼                           ▼                   ▼
              ┌──────────────┐           ┌──────────────┐    ┌──────────────┐
              │ Run Tests    │           │ Independent  │    │ Retry with   │
              │ & Verify     │           │ LLM Review   │    │ Context      │
              └──────────────┘           └──────────────┘    └──────────────┘
                     │                           │
                     └───────────┬───────────────┘
                                 ▼
                          ┌──────────────┐
                          │ Mark Task    │
                          │ Complete     │
                          └──────────────┘
```

### 6.2 Monitoring Signals

| Signal | Source | Purpose |
|--------|--------|---------|
| stdout/stderr | CLI process | Progress, errors |
| File changes | Filesystem watch | What was modified |
| Git commits | Git hooks | Completed units |
| Exit code | CLI process | Success/failure |

### 6.3 Failure Handling

1. **Retry with context**: Add failure logs to task context, retry
2. **Decompose**: Break task into smaller subtasks
3. **Peer review**: Another LLM analyzes failure
4. **Human escalation**: Pause and request input

### 6.4 Isolation Options

| Mode | Description |
|------|-------------|
| Direct | Run on host (default) |
| Docker | Isolated container per task |
| Sandbox | Lightweight isolation |

User configures per-project or globally.

---

## 7. Knowledge System

### 7.1 Knowledge Extraction Flow

```
Project Complete
       │
       ▼
┌──────────────┐
│ Analyze      │
│ Project      │
└──────┬───────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Extract      │ │ Extract      │ │ Extract      │
│ Prompts      │ │ Templates    │ │ Decisions    │
└──────────────┘ └──────────────┘ └──────────────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
                      ▼
               ┌──────────────┐
               │ Archive      │
               │ Project      │
               └──────────────┘
```

### 7.2 Prompt Engineering

| Mode | Description |
|------|-------------|
| Lab | Dedicated testing environment |
| Inline | Refine during normal use |
| Background | Automatic A/B testing and improvement |

---

## 8. CLI Interface

### 8.1 REPL Commands (Draft)

```
# Project management
/project new <name>          # Create new project
/project list                # List all projects
/project switch <name>       # Switch active project
/project status              # Show current project status

# Perspectives
/perspective <name>          # Switch to named perspective
/perspectives                # List available perspectives
/parallel                    # Get responses from multiple perspectives

# Artifacts
/artifact <type> new         # Create new artifact
/artifact <type> list        # List artifacts of type
/artifact edit <id>          # Edit artifact

# Execution
/execute                     # Start task execution
/execute status              # Check execution status
/execute pause               # Pause execution
/execute resume              # Resume execution

# Knowledge
/prompts list                # List available prompts
/prompts lab                 # Enter prompt lab

# General
/help                        # Show help
/context                     # Show current context
/clear                       # Clear conversation
```

---

## 9. Configuration

### 9.1 Global Config (~/.product-management/config.yaml)

```yaml
default_model: "claude-sonnet"
providers:
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
  openai:
    api_key: "${OPENAI_API_KEY}"
execution:
  isolation: "direct"  # direct|docker|sandbox
  log_level: "medium"  # low|medium|high
```

---

## 10. Implementation Phases

### Phase 1: Core Foundation
- Project structure and file management
- Basic CLI REPL
- Artifact CRUD (PRD, features, requirements)
- Single-model conversation

### Phase 2: Agent System
- Persona + Specialization loading
- Perspective switching
- Multi-model support
- Context summarization

### Phase 3: Execution Engine
- Claude Code integration
- Task execution flow
- Logging and monitoring
- Basic verification

### Phase 4: Knowledge System
- Prompt management
- Template extraction
- Decision recording

### Phase 5: Advanced Features
- Independent review
- Post-mortem analysis
- Background prompt optimization
- Web UI

---

## 11. Open Questions

See `docs/OPEN_QUESTIONS.md` for detailed design decisions still needed.
