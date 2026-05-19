# spec-init

A pack for bootstrapping OpenSpec and AI coding tool infrastructure in existing projects.

---

## Contents

### Skills

#### `openspec-bootstrap`

A Copilot CLI skill that analyzes an existing brownfield codebase and generates the complete OpenSpec + AI tooling setup — config, seed specs, agents, and instructions — tailored to whichever AI coding tools the team uses.

**What it helps you do:**

- Analyze a codebase across five dimensions (structure, architecture, domain, quality, security)
- Optionally build a knowledge graph via [graphify](https://github.com/safishamsi/graphify) for deeper AST-based analysis, cross-file call graphs, and Leiden community detection
- Initialize OpenSpec and populate `openspec/config.yaml` with project-specific context
- Seed initial behavioral specifications for each discovered domain
- Generate role-based agent definitions for GitHub Copilot, Claude Code, OpenAI Codex, Cursor, and Windsurf
- Create instructions and rules scoped to the right files and topics for each tool
- Verify generated outputs against the knowledge graph (spec coverage, agent coverage, instruction accuracy)

**Supported AI tools:**

| Tool | Agents | Instructions / Rules |
|------|--------|----------------------|
| GitHub Copilot | `.github/agents/<role>.md` | `.github/instructions/<topic>.instructions.md` |
| Claude Code | `CLAUDE.md` + `.claude/rules/` | `.claude/rules/<topic>.md` |
| OpenAI Codex | `AGENTS.md` sections | `AGENTS.md` sections |
| Cursor | `.cursor/rules/agent-<role>.mdc` | `.cursor/rules/<topic>.mdc` |
| Windsurf | `.windsurfrules` sections | `.windsurfrules` sections |

**Required dependencies:**

| Package | Install | Purpose |
|---------|---------|---------|
| Node.js ≥ 20.19.0 | *(system package)* | Runtime for OpenSpec CLI |
| OpenSpec CLI | `npm install -g @fission-ai/openspec@latest` | `openspec init` and spec commands |

**Optional dependencies:**

| Package | Install | Purpose |
|---------|---------|---------|
| graphify | Auto-installed into `.openspec-bootstrap-venv/` when Knowledge Graph mode is selected | Knowledge graph + AST analysis via tree-sitter, Leiden clustering, call graphs |

> **Note:** Knowledge Graph mode requires Python ≥ 3.10. If Python is not installed, the skill will inform you and stop — it will not fall back silently.

**Example prompts:**

| Prompt | What happens |
|--------|-------------|
| `Bootstrap this project with OpenSpec` | Runs the standard heuristic-based flow (no graphify needed) |
| `Bootstrap this project with OpenSpec and use the knowledge graph` | Builds a graphify knowledge graph first, then uses god nodes, communities, and call graphs for deeper analysis |
| `Set up OpenSpec with deep analysis` | Triggers `graphify . --mode deep` for more aggressive cross-module relationship extraction |
| `Set up Cursor rules for this project` | Detects Cursor and generates `.cursor/rules/` files |
| `Generate agents for Claude Code` | Generates `CLAUDE.md` and `.claude/rules/agent-*.md` files |
| `Prepare this repo for AI-assisted dev` | Full bootstrap for all detected AI tools |
