# Task Format Specification

## Document Info

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Status | Approved |
| Created | 2026-01-02 |
| Source | ADR-021, TASK_FORMAT_V3.md |

---

## 1. Overview

This document defines the **contract-driven task format** optimized for autonomous execution by LLM agents. The format is designed for constrained models (8K context) and eliminates ambiguity through explicit contracts, test specifications, and deterministic verification.

### Design Goals

1. **Deterministic success** - No LLM judgment in verification
2. **Constrained context** - Tasks fit in ~8K tokens
3. **Zero implicit knowledge** - Everything needed is in the task
4. **Micro-task architecture** - Small, focused, composable units

---

## 2. Target Agent Constraints

The task format assumes execution by cost-effective models with limited capabilities:

| Constraint | Limit | Implication |
|------------|-------|-------------|
| Effective context | ~8K tokens | Task + context + output must fit |
| Reasoning depth | ~3 steps | No complex multi-step logic in one task |
| File understanding | 1-2 files | Never require reading 3+ files |
| Implicit inference | Poor | Everything must be explicit |
| Pattern completion | Strong | Provide complete patterns to copy |

### What These Models Cannot Do

- Infer intent from vague instructions
- Remember previous tasks
- Read and synthesize multiple files
- Make judgment calls about edge cases
- "Follow existing patterns" without seeing them

### What These Models Excel At

- Pattern matching and completion
- Following explicit, step-by-step instructions
- Copying and modifying provided code
- Implementing to satisfy type signatures

---

## 3. Task Format Structure

Every task follows this structure:

```yaml
---
id: TASK-XXX
title: Short descriptive title
layer: N
track: backend | frontend | shared
depends_on: [TASK-YYY, TASK-ZZZ]
estimated_complexity: trivial | simple | medium | complex
---

# TASK-XXX: Title

## Contract
## Dependencies (Interfaces Only)
## Test Specification
## Output Files
## Verification (Deterministic)
## Done When
```

---

## 4. Section Specifications

### 4.1 Contract

Defines **WHAT** must be created using TypeScript type signatures. Not implementation details—just the public API.

```typescript
// backend/src/services/content.service.ts

export const contentService: {
  findById(id: string): Promise<Result<ContentItem, 'NOT_FOUND'>>;
  create(data: CreateContentData): Promise<Result<ContentItem, 'VALIDATION_ERROR'>>;
};
```

**Rules:**
- Use TypeScript signatures, not prose descriptions
- Export names must match exactly
- Include file path as comment
- No implementation details

### 4.2 Dependencies (Interfaces Only)

Defines what the task can rely on—**interfaces only**, not full implementations.

```typescript
// From TASK-031: contentRepository
type ContentRepository = {
  findById(id: string): Promise<ContentItem | null>;
  create(data: CreateContentData): Promise<ContentItem>;
};

// From TASK-002: env.ts
interface Env {
  DATABASE_URL: string;
  NODE_ENV: 'development' | 'production' | 'test';
}
```

**Rules:**
- Reference source task ID
- Only include interfaces actually needed
- 5 lines of interface, not 200 lines of implementation
- Agent doesn't need to read dependency files

### 4.3 Test Specification

Complete, runnable test code. **Tests ARE the spec**—the agent implements to make tests pass.

```typescript
// backend/src/services/content.service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { contentService } from './content.service.js';

// Mock dependencies
vi.mock('../repositories/content.repository.js', () => ({
  contentRepository: {
    findById: vi.fn(),
  },
}));

describe('contentService.findById', () => {
  it('returns content when found', async () => {
    const mockContent = { id: '1', title: 'Test' };
    contentRepository.findById.mockResolvedValue(mockContent);

    const result = await contentService.findById('1');

    expect(result.ok).toBe(true);
    expect(result.data.id).toBe('1');
  });

  it('returns NOT_FOUND when missing', async () => {
    contentRepository.findById.mockResolvedValue(null);

    const result = await contentService.findById('nonexistent');

    expect(result.ok).toBe(false);
    expect(result.error).toBe('NOT_FOUND');
  });
});
```

**Rules:**
- Complete, runnable test code
- Include all mocks and setup
- Cover success and error cases
- Tests define expected behavior unambiguously

### 4.4 Output Files

Explicit list of files to create/modify with line estimates.

```
WRITE: backend/src/services/content.service.ts (~40 lines)
WRITE: backend/src/services/content.service.test.ts (~50 lines)
MODIFY: backend/src/services/index.ts (add export)
```

**Rules:**
- Use WRITE for new files, MODIFY for existing
- Include line estimates to scope work
- Estimates help prevent overengineering

### 4.5 Verification (Deterministic)

Exact bash commands to verify success. **No LLM judgment**—purely mechanical checks.

```bash
# All must pass
cd backend
npx tsc --noEmit src/services/content.service.ts
npx vitest run src/services/content.service.test.ts
```

**Rules:**
- Commands must be copy-pasteable
- Output is pass/fail, not subjective
- Include directory context (cd commands)
- Order matters—run in sequence

### 4.6 Done When

Checkable acceptance criteria as checkboxes.

```markdown
- [ ] `contentService` exported with `findById` method
- [ ] All 2 tests pass
- [ ] No TypeScript errors
- [ ] No unused imports
```

**Rules:**
- Each criterion is objectively checkable
- No subjective assessments ("code is clean")
- Matches contract and test expectations

---

## 5. Task Sizing

### Size Limits (Strict)

| Complexity | Token Budget | Output Lines | When to Use |
|------------|--------------|--------------|-------------|
| Trivial | 500 | ~15 | Add import, fix typo, add field |
| Simple | 1000 | ~30 | Add method following pattern |
| Medium | 1500 | ~50 | Create file from template |
| Complex | 2000 | ~65 | Create file with 2-3 methods |
| **Too Big** | >2000 | >65 | **MUST SPLIT** |

### File Size Limits

| Type | Maximum Lines | Rationale |
|------|---------------|-----------|
| Source file | 150 | Fits in context with task |
| Test file | 200 | May include fixtures |
| Schema file | 100 | One entity per file |

### When to Split

If a task requires:
- More than 2 files to read
- More than 65 lines of output
- More than 3 logical steps
- Multiple independent functions

**Split it into micro-tasks.**

---

## 6. Anti-Patterns

These patterns cause agent failure:

| Anti-Pattern | Why It Fails | Fix |
|--------------|--------------|-----|
| "Implement the service layer" | Too vague | Define exact methods |
| "Follow existing pattern in X" | Requires reading other file | Include pattern inline |
| "Use your judgment" | No judgment available | List exact cases |
| "Handle edge cases" | Must list each case | Enumerate all cases |
| "Similar to how we did Y" | No memory of Y | Repeat the pattern |
| Multi-file changes | Context overflow | Split into micro-tasks |
| `/* ... */` placeholders | Incomplete pattern | Provide full code |
| Prose requirements | Ambiguous | Use type signatures |

---

## 7. Good Task Examples

### Example: Simple Method Addition

```markdown
---
id: TASK-042
title: Add findByState method to ContentRepository
layer: 2
track: backend
depends_on: [TASK-031]
estimated_complexity: simple
---

# TASK-042: Add findByState to ContentRepository

## Contract

```typescript
// backend/src/repositories/content.repository.ts
// ADD to existing contentRepository object:

findByState(state: ContentState): Promise<ContentItem[]>;
```

## Dependencies (Interfaces Only)

```typescript
// From TASK-031: existing repository structure
export const contentRepository: {
  findById(id: string): Promise<ContentItem | null>;
  // ... existing methods
};

// From TASK-030: ContentState type
type ContentState = 'opportunity' | 'draft' | 'review' | 'published' | 'archived';
```

## Test Specification

```typescript
// ADD to backend/src/repositories/content.repository.test.ts

describe('contentRepository.findByState', () => {
  it('returns items matching state', async () => {
    // Setup: insert test data
    await db.insert(contentItems).values([
      { id: '1', state: 'draft', title: 'Draft 1' },
      { id: '2', state: 'published', title: 'Published 1' },
      { id: '3', state: 'draft', title: 'Draft 2' },
    ]);

    const result = await contentRepository.findByState('draft');

    expect(result).toHaveLength(2);
    expect(result.every(item => item.state === 'draft')).toBe(true);
  });

  it('returns empty array when no matches', async () => {
    const result = await contentRepository.findByState('archived');
    expect(result).toEqual([]);
  });
});
```

## Output Files

```
MODIFY: backend/src/repositories/content.repository.ts (~10 lines added)
MODIFY: backend/src/repositories/content.repository.test.ts (~20 lines added)
```

## Verification (Deterministic)

```bash
cd backend
npx tsc --noEmit
npx vitest run src/repositories/content.repository.test.ts
```

## Done When

- [ ] `findByState` method added to `contentRepository`
- [ ] Returns `Promise<ContentItem[]>`
- [ ] Filters by state column
- [ ] Orders by `created_at DESC`
- [ ] Both new tests pass
```

---

## 8. Task Dependencies

### Dependency Rules

1. **Flat dependencies preferred**: A → B allowed
2. **Chain dependencies require splitting**: A → B → C should be A → B, then B → C
3. **Interface-only coupling**: Depend on contracts, not implementations
4. **Explicit declaration**: All dependencies in frontmatter

### Dependency Graph

Tasks form a DAG (Directed Acyclic Graph). The execution system:
1. Parses `depends_on` for each task
2. Builds execution order
3. Parallelizes independent tasks
4. Sequences dependent tasks

```
TASK-006 ──┬──▶ TASK-007 ──▶ TASK-008a ──▶ TASK-008b
           │
TASK-009a ─┴──▶ TASK-009b ──▶ TASK-010
```

---

## 9. Verification Pipeline

### Deterministic Checks (No LLM)

1. **Type check**: `npx tsc --noEmit`
2. **Unit tests**: `npx vitest run <test-file>`
3. **Lint**: `npx eslint <source-file>`
4. **Contract validation**: TypeScript compile-time check

### Contract Validation Script

```typescript
// scripts/validate-contract.ts
import { contentService } from '../src/services/content.service.js';

// Type assertion - fails at compile time if exports don't match
const _typeCheck: {
  findById(id: string): Promise<Result<ContentItem, 'NOT_FOUND'>>;
} = contentService;

console.log('Contract validation passed');
```

Run: `npx tsx scripts/validate-contract.ts`

---

## 10. Orchestration Model

```
┌─────────────────────────────────────────────────┐
│  Orchestrator (Sonnet/Opus)                     │
│  - Reads PRD, specs, existing code              │
│  - Decomposes into micro-tasks                  │
│  - Sequences dependencies                       │
│  - Retries failures with enriched context       │
└─────────────┬───────────────────────────────────┘
              │ Task queue
              ▼
┌─────────────────────────────────────────────────┐
│  Worker Pool (GLM-4.x / Haiku / Claude Code)    │
│  - Receives single task                         │
│  - Executes pattern completion                  │
│  - Returns success/failure                      │
│  - No memory between tasks                      │
└─────────────┬───────────────────────────────────┘
              │ Verification
              ▼
┌─────────────────────────────────────────────────┐
│  Verification Pipeline                          │
│  - Type checking (tsc)                          │
│  - Unit tests (vitest)                          │
│  - Lint (eslint)                                │
│  - Contract validation                          │
└─────────────────────────────────────────────────┘
```

---

## 11. Summary

The contract-driven task format achieves autonomous execution by:

| Principle | Implementation |
|-----------|----------------|
| Eliminate ambiguity | Contracts are type signatures |
| Deterministic verification | Tests + TypeScript = truth |
| Reduce context needs | Interfaces instead of full files |
| Support micro-tasks | Small, focused, composable |
| Remove LLM judgment | Mechanical pass/fail checks |

This format enables:
- **Any** capable agent to implement **any** task
- **Massive parallelization** (100+ concurrent agents)
- **Isolated failures** (single task, easy retry)
- **Cheap execution** ($0.001-0.01 per task)
- **Human review at PR level**, not task level
