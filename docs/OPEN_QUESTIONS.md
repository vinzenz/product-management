# Open Questions for Handoff

## Document Info

| Field | Value |
|-------|-------|
| Created | 2026-01-02 |
| Source | INTERVIEW_LOG.md (Q72, Q77, Q79) |
| Status | Partially Resolved |

---

## 1. Task Format Specification

**Status**: ✅ **RESOLVED**

**Resolution**: Adopted the **Contract-Driven Task Format (v3)** optimized for autonomous execution by constrained LLM agents.

**Documentation**: See [TASK_FORMAT_SPEC.md](./TASK_FORMAT_SPEC.md)

**Key decisions**:
- **Contracts over patterns**: TypeScript type signatures define WHAT to export
- **Tests ARE the spec**: Complete test code provided; agent implements to make tests pass
- **Interface-only dependencies**: 5 lines of interface, not 200 lines of implementation
- **Micro-tasks**: <50 lines output, <2K tokens context
- **Deterministic verification**: TypeScript + Vitest = truth (no LLM judgment)

**Task structure**:
```
## Contract           ← TypeScript signatures
## Dependencies       ← Interface-only (from dependent tasks)
## Test Specification ← Complete, runnable tests
## Output Files       ← Paths + line estimates
## Verification       ← Exact bash commands
## Done When          ← Checkable criteria
```

---

## 2. Frontmatter Field Schemas

**Context**: Different artifact types need different metadata fields.

**Question**: What are the required and optional fields for each artifact type?

### Features (F-*)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| id | Yes | string | F-NNN format |
| title | Yes | string | Human-readable title |
| status | Yes | enum | draft, approved, implemented, verified |
| priority | Yes | enum | must, should, could, wont (MoSCoW) |
| created | Yes | datetime | ISO 8601 |
| updated | Yes | datetime | ISO 8601 |
| requirements | No | list[string] | Linked FR IDs |
| tags | No | list[string] | Categorization |

### Functional Requirements (FR-*)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| id | Yes | string | FR-NNN format |
| title | Yes | string | Human-readable title |
| status | Yes | enum | draft, approved, implemented, verified |
| priority | Yes | enum | must, should, could, wont |
| feature | Yes | string | Parent feature ID |
| created | Yes | datetime | ISO 8601 |
| updated | Yes | datetime | ISO 8601 |
| tasks | No | list[string] | Implementing task IDs |
| rationale | No | string | Why this requirement |

### Non-Functional Requirements (NFR-*)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| id | Yes | string | NFR-NNN format |
| title | Yes | string | Human-readable title |
| status | Yes | enum | draft, approved, implemented, verified |
| category | Yes | enum | performance, security, usability, reliability, etc. |
| metric | No | string | Measurable target |
| created | Yes | datetime | ISO 8601 |
| updated | Yes | datetime | ISO 8601 |

### Tasks (T-*)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| id | Yes | string | T-NNN format |
| title | Yes | string | Human-readable title |
| status | Yes | enum | pending, in_progress, completed, failed, blocked |
| requirement | No | string | Implementing requirement ID |
| dependencies | No | list[string] | Task IDs that must complete first |
| estimated_complexity | No | enum | low, medium, high |
| created | Yes | datetime | ISO 8601 |
| updated | Yes | datetime | ISO 8601 |
| execution_log | No | string | Path to execution log |

**Action Required**: Validate these schemas against real project needs during dogfooding.

---

## 3. Standard Status Values

**Context**: Fixed status values across all projects for consistency.

**Question**: What are the standard status progressions for each artifact type?

### Feature Status Flow
```
draft → approved → implemented → verified
                ↓
            deprecated (optional end state)
```

### Requirement Status Flow
```
draft → approved → implemented → verified
```

### Task Status Flow
```
pending → in_progress → completed
              ↓
           failed → in_progress (retry)
              ↓
           blocked → pending (unblocked)
```

### Project Phase Flow
```
ideation → requirements → design → architecture → planning → executing → review → archived
```

**Action Required**: Confirm these flows work in practice during initial usage.

---

## 4. Example Directory Structure

**Context**: Need a concrete example of a project structure.

**Example Project**: "Task Management CLI"

```
projects/task-cli/
├── .project.yaml
├── overview.md
├── prd/
│   ├── summary.md
│   └── sections/
│       ├── 01-problem.md
│       ├── 02-solution.md
│       ├── 03-target-user.md
│       └── 04-success-metrics.md
├── features/
│   ├── F-001-task-creation.md
│   ├── F-002-task-listing.md
│   ├── F-003-task-completion.md
│   └── F-004-task-deletion.md
├── requirements/
│   ├── functional/
│   │   ├── FR-001-create-task-with-title.md
│   │   ├── FR-002-create-task-with-due-date.md
│   │   ├── FR-003-list-all-tasks.md
│   │   ├── FR-004-list-pending-tasks.md
│   │   ├── FR-005-mark-task-complete.md
│   │   └── FR-006-delete-task.md
│   └── non-functional/
│       ├── NFR-001-response-time.md
│       └── NFR-002-data-persistence.md
├── design/
│   ├── personas/
│   │   └── busy-developer.md
│   ├── journeys/
│   │   └── daily-task-workflow.md
│   └── interactions/
│       ├── create-flow.md
│       └── list-flow.md
├── architecture/
│   ├── overview.md
│   ├── adrs/
│   │   ├── ADR-001-cli-framework.md
│   │   └── ADR-002-storage-format.md
│   └── components/
│       ├── cli-interface.md
│       ├── task-service.md
│       └── storage-layer.md
├── data-models/
│   └── task.md
├── tasks/
│   ├── T-001-setup-project.md
│   ├── T-002-implement-task-model.md
│   ├── T-003-implement-storage.md
│   ├── T-004-implement-create-command.md
│   ├── T-005-implement-list-command.md
│   ├── T-006-implement-complete-command.md
│   └── T-007-implement-delete-command.md
├── execution/
│   └── logs/
│       └── .gitkeep
└── memory/
    └── decisions.json
```

---

## 5. Additional Questions (Lower Priority)

### 5.1 Prompt Storage Format

How should proven prompts be stored in `tooling/prompts/`?

```yaml
# Option A: YAML with metadata
id: "generate-prd-section"
name: "PRD Section Generator"
version: "1.2.0"
effectiveness_score: 0.85  # from background optimization
prompt: |
  You are generating a section of a PRD...
```

### 5.2 Workflow Definition Format

How should workflows be defined in `tooling/workflows/`?

```yaml
# Draft format
id: "architecture-review"
name: "Architecture Review Workflow"
stages:
  - id: "analyze"
    perspective: "architect"
    prompt: "Analyze the proposed architecture..."
  - id: "challenge"
    perspective: "skeptic"
    prompt: "Challenge assumptions..."
  - id: "synthesize"
    perspective: "pragmatist"
    prompt: "Synthesize recommendations..."
```

### 5.3 Skills Architecture

How do skills relate to prompts, agents, and workflows?

Options:
- Skills are callable prompts with parameters
- Skills are mini-workflows
- Skills are agent capabilities (file access, code execution, etc.)
- Skills combine all of the above

---

## Resolution Process

For each open question:

1. **Prototype**: Build minimal version with best-guess format
2. **Dogfood**: Use in real project (this system itself)
3. **Evaluate**: Measure success rate, usability, friction
4. **Iterate**: Refine based on findings
5. **Document**: Update specs with chosen approach

---

## Handoff Notes

When resuming this work:

1. Read `INTERVIEW_LOG.md` for full context of all 95 decisions
2. Read `docs/PRD.md` for product requirements
3. Read `docs/TECHNICAL_SPEC.md` for implementation approach
4. Start with **Task Format Specification** (Q1) as it's critical for execution
5. Dogfood immediately by using this system to build itself
