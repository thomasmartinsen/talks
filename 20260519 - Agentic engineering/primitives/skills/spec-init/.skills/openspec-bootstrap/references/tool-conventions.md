# AI Tool Conventions

Reference for multi-tool output generation. Each AI coding tool has its own conventions for where project context, agent definitions, and scoped rules live.

Use this reference during Phase 1 (tool detection) and Phases 4–5 (agent/instruction generation) to determine what files to generate and where to place them.

---

## Tool Detection

Check for these markers to determine which tools the project uses:

| Tool | Detection Signals | Confidence |
|------|------------------|------------|
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/agents/`, `.github/instructions/`, `.vscode/` | High |
| Claude Code | `CLAUDE.md`, `.claude/`, `.claude/rules/` | High |
| OpenAI Codex | `.codex/` (high), `AGENTS.md` at root (ambiguous — see below) | Varies |
| Cursor | `.cursor/`, `.cursor/rules/`, `.cursorrules` | High |
| Windsurf | `.windsurfrules`, `.windsurf/` | High |

**`AGENTS.md` is ambiguous.** Many AI tools and agent frameworks create `AGENTS.md` files (e.g., custom multi-agent setups, non-Codex workflows). When `AGENTS.md` exists at root:
1. **`.codex/` also present** → Codex confirmed.
2. **No `.codex/`** → Inspect `AGENTS.md` content for Codex conventions (hierarchical `AGENTS.md` in subdirectories, `AGENTS.override.md` references, Codex CLI patterns). If content is ambiguous, **prompt the user** to confirm which AI tool(s) the project uses.

Do NOT assume `AGENTS.md` alone means OpenAI Codex.

If **no tool markers are found**, ask the user which tools they use. If they're unsure, default to generating for all major tools — the files don't conflict.

Map detected tools to the `openspec init --tools` flag values:
- GitHub Copilot → `github-copilot`
- Claude Code → `claude`
- OpenAI Codex → `codex`
- Cursor → `cursor`
- Windsurf → `windsurf`

---

## GitHub Copilot

**Agent definitions:** `.github/agents/<role>.md`

```markdown
---
description: One-line description of the agent's role
---

# Role Name

Instructions for this agent...
```

- Separate file per agent role
- YAML frontmatter with `description` field
- Referenced via `@<role>` in Copilot Chat

**Instructions:** `.github/instructions/<topic>.instructions.md`

```markdown
---
description: Brief description
applyTo: "glob/pattern/**/*"
---

# Topic

Content...
```

- YAML frontmatter with `applyTo` glob for file-scoped activation
- Common scopes: `**/*` (global), `src/**/*`, `**/*.test.*`, `**/*.{ts,tsx}`
- One file per topic, multiple files compose

**Skills:** `.github/skills/<name>/SKILL.md`
- For reusable, complex workflows (not typically generated during bootstrap)

---

## Claude Code

**Root context:** `CLAUDE.md` (project root)

```markdown
# Project Name

## Overview
Brief project description.

## Tech Stack
- Language, framework, database...

## Architecture
Layer descriptions, key directories...

## Development Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`

## Coding Standards
Key conventions...
```

- Plain markdown, no YAML frontmatter required
- Loaded at the start of every Claude Code session
- Keep under 200 lines; use `.claude/rules/` for detailed topics
- Can import other files with `@path/to/file` syntax

**Scoped rules:** `.claude/rules/<topic>.md`

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API Development Rules

- All API endpoints must include input validation
- Use the standard error response format
```

- YAML frontmatter with `paths` field for glob-based scoping
- Rules without `paths` frontmatter apply globally
- Supports recursive subdirectories: `.claude/rules/frontend/`, `.claude/rules/backend/`
- Pattern syntax: `**/*.ts`, `src/**/*`, `*.md`, `src/components/*.tsx`
- Multiple patterns via array, brace expansion supported: `"src/**/*.{ts,tsx}"`

**AGENTS.md compatibility:** Claude Code reads `CLAUDE.md`, not `AGENTS.md`. If `AGENTS.md` exists for Codex, create a `CLAUDE.md` that imports it:

```markdown
@AGENTS.md

## Claude Code Specific
Additional Claude-specific instructions...
```

---

## OpenAI Codex

**Root context:** `AGENTS.md` (project root)

```markdown
# Project Name

## Repository Expectations
- Run `npm run lint` before opening a pull request
- Document public utilities in `docs/` when you change behavior

## Tech Stack
- Language, framework, database...

## Architecture
Key directories and their purposes...

## Coding Standards
Key conventions...
```

- Plain markdown, no YAML frontmatter
- Codex walks directory tree: root `AGENTS.md` → subdirectory `AGENTS.md` files
- Files closer to working directory override earlier guidance (later = higher priority)
- `AGENTS.override.md` in any directory takes precedence over `AGENTS.md` in that directory
- Combined size limit: 32 KiB by default

**Hierarchical scoping:** Place `AGENTS.md` files in subdirectories for service-specific guidance:

```
AGENTS.md                          # Global project rules
services/
  payments/
    AGENTS.md                      # Payment service specific rules
  search/
    AGENTS.md                      # Search service specific rules
```

**No separate agent files:** Codex doesn't have a concept of named agents like Copilot's `@role`. All guidance goes into `AGENTS.md`.

---

## Cursor

**Rules directory:** `.cursor/rules/<topic>.mdc` (preferred) or `.cursorrules` (legacy)

```markdown
---
description: Brief description of this rule
globs: "src/**/*.{ts,tsx}"
alwaysApply: false
---

# Topic

Instructions for Cursor...
```

- `.mdc` extension (markdown with context) or `.md`
- YAML frontmatter with `globs` for file scoping and `alwaysApply` flag
- Rules without globs or with `alwaysApply: true` are always active
- Supports subdirectories: `.cursor/rules/frontend/`, `.cursor/rules/backend/`

**Legacy format:** `.cursorrules` at project root
- Single file, no frontmatter, plain markdown
- Still supported but `.cursor/rules/` is preferred for new projects

**No separate agent files:** Cursor doesn't have named agents. All context goes into rules.

---

## Windsurf

**Root context:** `.windsurfrules` (project root)

```markdown
# Project Name

## Code Style and Organization
Key conventions...

## Architecture
Directory structure, patterns...

## Security Rules
Auth patterns, validation...

## Testing Requirements
Framework, coverage expectations...
```

- Single root-level file, plain markdown
- No YAML frontmatter, no glob scoping
- Applies to entire repository
- Some projects use `.windsurfrules.md` extension

**No separate agent files or scoped rules:** All guidance goes into the single root file.

---

## Cross-Tool Content Strategy

The **same underlying knowledge** (domain context, coding standards, security rules) needs to be expressed in each tool's format. The content is identical — only the file format, location, and scoping mechanism differ.

### Shared content, tool-specific formatting

For each instruction topic (e.g., "coding standards"):

| Tool | File | Scoping |
|------|------|---------|
| Copilot | `.github/instructions/coding-standards.instructions.md` | `applyTo: "src/**/*"` |
| Claude | `.claude/rules/coding-standards.md` | `paths: ["src/**/*"]` |
| Codex | Section in `AGENTS.md` | Subdirectory placement |
| Cursor | `.cursor/rules/coding-standards.mdc` | `globs: "src/**/*"` |
| Windsurf | Section in `.windsurfrules` | No scoping (global) |

### Agent content mapping

Only Copilot uses separate agent files. For other tools, agent-level guidance should be folded into:

| Tool | Where agent guidance goes |
|------|--------------------------|
| Copilot | `.github/agents/<role>.md` (one file per role) |
| Claude | `CLAUDE.md` role section or `.claude/rules/agent-<role>.md` |
| Codex | `AGENTS.md` role section |
| Cursor | `.cursor/rules/agent-<role>.mdc` |
| Windsurf | `.windsurfrules` role section |

### Priority order for multi-tool projects

When generating for multiple tools, generate in this order (most structured first):
1. GitHub Copilot (richest agent/instruction model)
2. Claude Code (scoped rules with paths)
3. Cursor (scoped rules with globs)
4. OpenAI Codex (hierarchical AGENTS.md)
5. Windsurf (single flat file)
