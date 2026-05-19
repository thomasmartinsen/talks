---
name: openspec-bootstrap
description: Bootstrap and initialize OpenSpec for an existing brownfield project, supporting any AI coding tool (GitHub Copilot, Claude Code, OpenAI Codex, Cursor, Windsurf, and more). Analyzes the codebase deeply, populates openspec/config.yaml, seeds initial specifications, creates tool-appropriate agent definitions and instructions (placing files in .github/ for Copilot, CLAUDE.md and .claude/rules/ for Claude Code, AGENTS.md for Codex, .cursor/rules/ for Cursor, .windsurfrules for Windsurf). Use this skill whenever someone wants to set up OpenSpec in an existing project, onboard a codebase for AI-assisted development, generate project-specific AI agents or instructions for any AI tool, prepare a repository for spec-driven development, or bootstrap AI tooling for a brownfield codebase. Even if they just say "bootstrap this project", "set up OpenSpec", "generate agents", "prepare for Claude Code", "set up Cursor rules", or "prepare for AI-assisted dev", use this skill.
---

# OpenSpec Bootstrap

A meta-skill that explores an existing brownfield codebase and generates the complete OpenSpec + AI tooling infrastructure. This is a "Day 0" skill — run it once when adopting OpenSpec in a project, and it produces everything needed to start spec-driven development with whichever AI coding tools the team uses.

**Supported AI tools:** GitHub Copilot, Claude Code, OpenAI Codex, Cursor, Windsurf (and any tool supported by `openspec init --tools`).

**What it generates:**

| Output | Location | Purpose |
|--------|----------|---------|
| Project config | `openspec/config.yaml` | Tech stack context, conventions, per-artifact rules |
| Seed specs | `openspec/specs/**` | Initial behavioral specifications for existing system |
| Agent definitions | Tool-specific (see below) | Specialized AI agents tailored to the project |
| Instructions / Rules | Tool-specific (see below) | Domain context, coding standards, security rules |
| Additional skills | `.github/skills/` | Project-specific Copilot skills (if warranted) |

**Tool-specific output locations:**

| Content | GitHub Copilot | Claude Code | OpenAI Codex | Cursor | Windsurf |
|---------|---------------|-------------|-------------|--------|----------|
| Agents | `.github/agents/<role>.md` | `CLAUDE.md` sections | `AGENTS.md` sections | `.cursor/rules/agent-<role>.mdc` | `.windsurfrules` sections |
| Instructions | `.github/instructions/*.instructions.md` | `.claude/rules/<topic>.md` | `AGENTS.md` sections | `.cursor/rules/<topic>.mdc` | `.windsurfrules` sections |
| Root context | — | `CLAUDE.md` | `AGENTS.md` | — | `.windsurfrules` |

## Prerequisites

- Node.js ≥ 20.19.0
- OpenSpec CLI: `npm install -g @fission-ai/openspec@latest`
- Target project should be an existing git repository with code
- **Optional — Knowledge Graph + AST analysis:** Python ≥ 3.10 + `graphifyy` package. Installed automatically into a `.openspec-bootstrap-venv/` virtual environment in the project root if the user selects Knowledge Graph mode. No global pip install needed. Uses a dedicated venv name to avoid conflicts with any existing `.venv/`.

## Working Directory

All intermediate analysis artifacts are written to `.openspec-bootstrap-tmp/` in the project root. This keeps the graph outputs, project profile, and verification reports out of context until explicitly needed. Add `.openspec-bootstrap-tmp/` to `.gitignore`.

## Model Recommendation

This skill performs deep codebase analysis requiring strong reasoning. Use:
- **Claude Opus 4.6** or **GPT 5.4** for analysis phases
- Standard models work but may produce shallower analysis

---

## Execution Flow

Run phases sequentially. Each builds on the previous.

### Phase 0: Analysis Mode Selection

Before starting analysis, ask the user which analysis mode to use:

> **How would you like to analyze the codebase?**
>
> 1. **Standard** — File-level heuristic analysis (no extra dependencies, faster)
> 2. **Knowledge Graph + AST** — Deeper analysis using graphify: tree-sitter AST parsing, cross-file call graphs, Leiden community detection, and design rationale extraction (requires `pip install graphifyy`)
> 3. **Knowledge Graph (deep mode)** — Same as above with `--mode deep` for aggressive cross-module relationship extraction (recommended for large/complex codebases, costs more tokens)

If the user picks option 2 or 3, run the following prerequisite checks **before proceeding**:

1. **Check for Python ≥ 3.10.** Run `python3 --version` (or `python --version` on Windows). If Python is not installed or the version is below 3.10:
   - Tell the user: *"Knowledge Graph mode requires Python 3.10 or later, which is not installed on this system. Please install Python (https://www.python.org/downloads/) and re-run this skill."*
   - **Stop the skill entirely.** Do not fall back to Standard mode — the user explicitly chose Knowledge Graph mode and should fix the prerequisite first.

2. **Set up a virtual environment.** Create a dedicated `.openspec-bootstrap-venv/` in the project root. This uses a skill-specific name to avoid conflicts with any existing `.venv/` the project may already have:
   ```bash
   python3 -m venv .openspec-bootstrap-venv
   .openspec-bootstrap-venv/bin/pip install graphifyy
   ```
   Add `.openspec-bootstrap-venv/` to `.gitignore` if not already present.

3. **Use the venv-installed graphify for all subsequent commands.** Set the path once:
   ```bash
   GRAPHIFY=".openspec-bootstrap-venv/bin/graphify"
   ```
   All `graphify` commands in later phases use `$GRAPHIFY` instead of a bare `graphify` call. This avoids polluting the system Python or any existing virtual environment.

Store the choice — it gates all graphify-dependent steps in subsequent phases.

### Phase 0.5: Knowledge Graph Build (if selected)

Skip this phase if the user chose **Standard** mode.

1. Create the working directory: `mkdir -p .openspec-bootstrap-tmp/graphify-out`
2. Run `$GRAPHIFY . --no-viz --output .openspec-bootstrap-tmp/graphify-out` on the project root (add `--mode deep` if option 3 was selected). This writes all graph artifacts directly into the tmp folder:
   - `.openspec-bootstrap-tmp/graphify-out/GRAPH_REPORT.md` — god nodes, communities, surprising connections, suggested questions
   - `.openspec-bootstrap-tmp/graphify-out/graph.json` — full graph (NetworkX format, queryable)
   - `.openspec-bootstrap-tmp/graphify-out/cache/` — SHA256 cache for incremental re-runs
3. Optionally run `$GRAPHIFY . --wiki --output .openspec-bootstrap-tmp/graphify-out` to generate a community-indexed wiki — articles per community can accelerate Phase 3 spec seeding.

All graphify output stays inside `.openspec-bootstrap-tmp/` — nothing is written to the project root.

The AST pass is deterministic and free (tree-sitter, no LLM). It extracts classes, functions, imports, call graphs, docstrings, and rationale comments (`# WHY:`, `# HACK:`, `# NOTE:`, `# IMPORTANT:`). The doc/image extraction pass uses your LLM provider.

### Phase 1: Deep Codebase Discovery

Read `references/analysis-guide.md` for the full analysis checklist.

Spawn **parallel** explore agents (using `task` tool with `agent_type: "explore"`) across up to six dimensions:

1. **Structure & Stack** — Languages, frameworks, package managers, build tools, runtimes
2. **Architecture** — Service boundaries, API layers, data flow, frontend/backend split, patterns
3. **Domain** — Business domains, bounded contexts, core entities, key workflows, vocabulary
4. **Quality & Standards** — Linter configs, test frameworks, CI/CD, naming conventions, error patterns
5. **Security & Infrastructure** — Auth patterns, secret management, cloud provider, IaC, databases
6. **Graph Structure** *(only if `.openspec-bootstrap-tmp/graphify-out/GRAPH_REPORT.md` exists)* — God nodes, Leiden communities, cross-module connections, call graph hot paths, rationale nodes

Additionally, detect which **AI coding tools** the project uses. Check for:
- `.github/agents/`, `.github/instructions/`, `.github/copilot-instructions.md` → **GitHub Copilot**
- `CLAUDE.md`, `.claude/`, `.claude/rules/` → **Claude Code**
- `AGENTS.md` (at root) + `.codex/` → **OpenAI Codex** (see disambiguation below)
- `.cursor/`, `.cursor/rules/`, `.cursorrules` → **Cursor**
- `.windsurfrules`, `.windsurf/` → **Windsurf**

**`AGENTS.md` disambiguation:** `AGENTS.md` is NOT exclusive to OpenAI Codex — many agent frameworks and AI tools create or reference `AGENTS.md` files. When `AGENTS.md` is found at the project root:
1. If `.codex/` directory also exists → confidently classify as **OpenAI Codex**.
2. If `.codex/` is absent, inspect the content of `AGENTS.md` for Codex-specific patterns (e.g., `AGENTS.override.md` references, hierarchical subdirectory `AGENTS.md` files, Codex CLI conventions).
3. If still uncertain, **ask the user**: _"I found an `AGENTS.md` file at the project root. Is this project using OpenAI Codex, or is it from another agent framework? Which AI coding tools should I generate output for?"_

Do NOT silently assume `AGENTS.md` means Codex.

If no tool markers are found, ask the user which AI tools they use. Read `references/tool-conventions.md` for the full detection and mapping guide.

If the **Graph Structure** agent ran, the Architecture and Domain agents should cross-reference their findings against the graph report. Communities that don't align with discovered architecture boundaries signal hidden coupling or misnamed modules. God nodes that the Domain agent missed indicate core concepts buried in implementation rather than exposed in naming.

Synthesize findings into a **Project Profile** including a `tools:` section listing detected AI tools. Save to `.openspec-bootstrap-tmp/project-profile.md`.

### Phase 2: OpenSpec Initialization & Config

1. Check if `openspec/` directory exists
2. Run `openspec init` with the appropriate `--tools` flag based on detected tools (e.g., `--tools github-copilot,claude,codex,cursor`)
3. Populate `openspec/config.yaml` with the Project Profile

Read `references/config-examples.md` for the config template and examples.

The config MUST include:
- **`context:`** — Comprehensive tech stack, architecture, domain overview, conventions
- **`rules:`** — Per-artifact rules for `proposal`, `specs`, `design`, and `tasks`

### Phase 3: Initial Spec Seeding

Create `openspec/specs/<domain>/spec.md` for each discovered domain.

**Domain discovery strategy** (in priority order):
1. If `.openspec-bootstrap-tmp/graphify-out/GRAPH_REPORT.md` exists, use **Leiden communities** as the primary domain partitioning signal. Each community maps to a domain. Name domains after the community's god node or dominant concept.
2. If graphify produced a `--wiki` output (`.openspec-bootstrap-tmp/graphify-out/wiki/`), read community articles as a starting point for each domain's spec content — they already contain extracted concepts, relationships, and rationale.
3. **Bridge nodes** (nodes appearing in multiple communities) indicate cross-cutting concerns. Create a shared spec (e.g., `openspec/specs/shared/` or `openspec/specs/cross-cutting/`) for these.
4. Fall back to directory structure and domain analysis from Phase 1 when no graph is available.

For each spec:
1. If graph data was used, add a `<!-- graphify-metadata -->` HTML comment block at the **top** of the file (before any headings) containing the graph-derived context. This separates volatile graph details from the stable spec content:
   ```markdown
   <!-- graphify-metadata
   community: 0 (electrical-graph)
   god_nodes: GridQueryService, ElectricalNode, AssetParameters
   bridge_nodes: GridQueryService (also in community 3)
   related_tables: electrical_nodes, electrical_edges, electrical_edge_vertices, asset_parameters
   -->
   ```
   Community IDs are non-deterministic (Leiden clustering may assign different numbers on re-runs). The metadata block preserves traceability to the graph without polluting the spec prose. Use the community's **descriptive label** (e.g., "electrical-graph") alongside the numeric ID so the spec remains meaningful even if IDs shift.

2. Write a `## Purpose` section. Do **not** reference community IDs or god node names in the Purpose prose — describe the domain in plain business/technical language. Instead of *"The god node GridQueryService in community 0 orchestrates queries"*, write *"Orchestrates queries against the derived electrical graph model"*.
3. Document 3–5 key **existing** requirements using `### Requirement:` headings. When graph data is available, prioritize **god nodes** within the community — these are the highest-connectivity concepts and represent the most critical requirements. Reference entities by their domain name, not their graph role.
4. Add `#### Scenario:` blocks with Given/When/Then format
5. Use RFC 2119 keywords (SHALL, MUST, SHOULD, MAY)
6. If `rationale_for` edges exist in the graph for entities in this domain, include the rationale as `> **Design rationale:** ...` blocks under the relevant requirement.

**Rules:**
- Only spec verified, existing behavior — never invent requirements
- Focus on observable behavior, not implementation details
- Keep lightweight — these are seed specs, not exhaustive documentation
- When uncertain, use SHOULD instead of MUST
- **Never embed raw community IDs or graph terminology (god node, bridge node, Leiden community) in spec prose.** These belong only in the metadata comment block at the top of the file.

### Phase 4: Agent Generation

Generate agent definitions for **each detected AI tool**. Read `references/agent-catalog.md` for role templates and `references/tool-conventions.md` for tool-specific file formats.

**For GitHub Copilot:** Create `.github/agents/<role>.md` with YAML frontmatter (`description` field). One file per role. Users invoke via `@<role>` in Copilot Chat.

**For Claude Code:** Add role-specific sections to `CLAUDE.md` and/or create `.claude/rules/agent-<role>.md` with `paths` frontmatter for scoped guidance. Claude doesn't have named agents — role context is expressed as rules that activate when working on relevant files.

**For OpenAI Codex:** Add role-specific guidance as sections in root `AGENTS.md`. For large projects, place service-specific agent guidance in subdirectory `AGENTS.md` files (e.g., `services/payments/AGENTS.md`). Codex doesn't have named agents.

**For Cursor:** Create `.cursor/rules/agent-<role>.mdc` files with `globs` frontmatter. Rules activate when Cursor works on matching files.

**For Windsurf:** Add role-specific sections to `.windsurfrules`. All guidance is global (no scoping mechanism).

Determine role relevance based on the Project Profile. When graph data is available, use **community composition and god node types** as stronger signals than file-level heuristics alone:

| Agent | Create when... | Graph signal (if available) |
|-------|---------------|---------------------------|
| `frontend-developer` | UI layer exists (React, Vue, Angular, Svelte, etc.) | Community dominated by UI component/rendering nodes |
| `backend-developer` | Server-side code exists (APIs, services, workers) | Community with API handler, service, and middleware nodes |
| `fullstack-developer` | Small project where FE/BE split is unnecessary | ≤2 communities spanning both UI and API nodes |
| `tester` | Always — every project needs testing guidance | — |
| `architect` | Complex architecture (microservices, event-driven, DDD) | >5 communities or god nodes spanning multiple communities |
| `project-manager` | Always — manages specs, tasks, coordination | — |
| `database-expert` | Database schemas, migrations, or complex queries | Community with high-degree ORM/model/migration nodes |
| `cloud-architect` | Cloud infrastructure (AWS, Azure, GCP, Kubernetes) | Community with IaC, deployment, cloud-service nodes |
| `security-engineer` | Sensitive data, auth, compliance, or regulated industry | Auth/crypto nodes appearing as god nodes |
| `devops-engineer` | CI/CD pipelines, IaC, containerization | Pipeline/Docker/deploy nodes forming own community |
| `api-designer` | Exposes or consumes APIs (REST, GraphQL, gRPC) | API route/schema nodes with high fan-out |
| `performance-engineer` | Performance-critical paths or SLA requirements | Call graph hot paths with deep dependency chains |

Each agent MUST (regardless of tool):
- Reference `openspec/specs/` as the source of truth for behavior
- Work within the `/opsx:propose → /opsx:apply → /opsx:archive` workflow
- Include project-specific context (tech stack, patterns, conventions)
- Define clear boundaries (what the agent does and does NOT do)

The **same role knowledge** is expressed in each tool's format. Write the Copilot agent file first (most structured), then adapt for other tools.

### Phase 5: Instruction / Rule Generation

Generate instructions or rules for **each detected AI tool**. Read `references/instruction-templates.md` for content templates and `references/tool-conventions.md` for tool-specific formats.

The same five core topics must be covered regardless of tool:

| Topic | Copilot `applyTo` | Claude `paths` | Cursor `globs` |
|-------|-------------------|----------------|-----------------|
| Domain context | `**/*` | (no paths = global) | `alwaysApply: true` |
| Coding standards | `src/**/*` | `["src/**/*"]` | `"src/**/*"` |
| Security | `**/*` | (no paths = global) | `alwaysApply: true` |
| Testing | `**/*.test.*` | `["**/*.test.*"]` | `"**/*.test.*"` |
| Architecture | Source dirs | Source dir paths | Source dir globs |

**For GitHub Copilot:** Create `.github/instructions/<topic>.instructions.md` with `applyTo` frontmatter.

**For Claude Code:**
1. Create `CLAUDE.md` at project root with project overview, tech stack, dev commands, and key conventions (under 200 lines). Use `@` imports for detailed topics.
2. Create `.claude/rules/<topic>.md` with `paths` frontmatter for scoped rules.

**For OpenAI Codex:**
1. Create `AGENTS.md` at project root with all instruction content organized by section.
2. For monorepos, create subdirectory `AGENTS.md` files for service-specific guidance.

**For Cursor:** Create `.cursor/rules/<topic>.mdc` files with `globs` and `description` frontmatter.

**For Windsurf:** Create `.windsurfrules` at project root containing all instruction content as markdown sections.

Add domain-specific instructions as warranted by the project analysis.

### Phase 6: Additional Skill Generation (Optional)

Only create project-specific skills if the analysis reveals clear, repeatable patterns:
- Database migration workflows
- API endpoint creation patterns
- Component scaffolding templates
- Deployment checklists

Do not generate skills speculatively.

### Phase 7: Graph-Based Verification (Optional)

Run this phase only if `.openspec-bootstrap-tmp/graphify-out/graph.json` exists. Read `references/verification-guide.md` for the full checklist and query patterns.

Use the knowledge graph to verify that generated outputs actually cover the codebase:

1. **Spec coverage** — Query the graph for all god nodes and community labels. Check each is represented in at least one spec file under `openspec/specs/`. Write uncovered nodes to `.openspec-bootstrap-tmp/coverage-gaps.md`.
2. **Agent coverage** — Check that generated agent roles cover all major communities. A community with >10 nodes and no matching agent role is a gap.
3. **Instruction accuracy** — Compare AST-extracted patterns (naming conventions from function/class names, import patterns, error handling from rationale comments) against generated coding-standards instructions. Flag contradictions.
4. **Cross-cutting verification** — Use `$GRAPHIFY path` between god nodes in different communities to verify that surprising connections are documented in specs or architecture instructions.

Produce a **verification report** at `.openspec-bootstrap-tmp/verification-report.md` with:
- Coverage score: `(covered god nodes / total god nodes) × 100%`
- Gap list with recommendations ("Community X has no matching spec — consider adding `openspec/specs/x/spec.md`")
- Contradiction list (if any)

If coverage is below 80%, iterate on Phases 3–5 to fill gaps before presenting the output summary.

---

## Output Summary

After completing all phases, present a summary grouped by tool:

```
OpenSpec Bootstrap Complete!

Config:       openspec/config.yaml     ✓ populated with project context
Specs:        openspec/specs/          ✓ N domains seeded

GitHub Copilot:
  Agents:       .github/agents/          ✓ N agent definitions
  Instructions: .github/instructions/    ✓ N instruction files

Claude Code:
  Root context: CLAUDE.md                ✓ project overview
  Rules:        .claude/rules/           ✓ N scoped rule files

OpenAI Codex:
  Root context: AGENTS.md                ✓ project guidance

Cursor:
  Rules:        .cursor/rules/           ✓ N rule files

Windsurf:
  Rules:        .windsurfrules           ✓ project guidance

Next steps:
1. Review generated files and adjust to your preferences
2. Run: openspec validate --specs
3. Start using OpenSpec: /opsx:propose <your-first-change>
```

If Phase 7 (verification) ran, also show:

```
Verification:  .openspec-bootstrap-tmp/verification-report.md
  Coverage:     N% of god nodes covered by specs
  Gaps:         N uncovered communities (see report)
```

Only show sections for the tools that were detected/generated.

### Cleanup

Before cleanup, **always** copy key analysis artifacts into `openspec/` so they survive deletion and remain useful as project documentation:

```bash
cp .openspec-bootstrap-tmp/project-profile.md openspec/project-profile.md
# If verification ran:
cp .openspec-bootstrap-tmp/verification-report.md openspec/verification-report.md 2>/dev/null || true
```

These files provide valuable context for both developers and AI models working on the project later.

Then ask the user:

> **Would you like to keep the `.openspec-bootstrap-tmp/` directory?**
>
> The project profile and verification report have been copied to `openspec/`. The tmp directory still contains raw graph data, query outputs, and coverage gap details — useful for debugging or re-running, but not needed for day-to-day work.
>
> 1. **Keep it** — Add `.openspec-bootstrap-tmp/` and `.openspec-bootstrap-venv/` to `.gitignore`
> 2. **Delete it** — Remove the tmp directory and the dedicated venv

If the user chooses to delete:
```bash
rm -rf .openspec-bootstrap-tmp/
rm -rf .openspec-bootstrap-venv/
```

If the user chooses to keep, ensure `.openspec-bootstrap-tmp/` and `.openspec-bootstrap-venv/` are in `.gitignore`.

## Key Principles

- **Derive, don't invent.** Every generated artifact must be grounded in what's actually in the codebase.
- **Match the project's voice.** Use the domain vocabulary, naming patterns, and conventions already present.
- **Be thorough but not exhaustive.** Seed enough to establish patterns — the team will iterate from here.
- **Keep it actionable.** Vague guidance is worse than no guidance. Be specific.
- **Make iteration easy.** Everything generated should be straightforward to edit and extend.
