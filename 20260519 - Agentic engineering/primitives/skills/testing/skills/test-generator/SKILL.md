---
name: test-generator
description: "Generates comprehensive, compilable unit tests for any programming language using a Research → Plan → Implement pipeline. Use when asked to generate tests, write unit tests, add or improve test coverage, or create test files — even casual requests like 'add tests for this' or 'improve coverage'. Supports C#, TypeScript, JavaScript, Python, Go, Rust, Java, and more."
---

# Polyglot Test Generation Skill

Generate comprehensive, workable unit tests for any programming language using a structured **Research → Plan → Implement** pipeline.


## How It Works

The pipeline has three sequential phases. Complete each phase before moving to the next.

1. **Research** — Analyze the codebase to understand structure, language, testing framework, and what needs testing
2. **Plan** — Create a phased implementation plan grouping files by priority and complexity
3. **Implement** — Write tests phase by phase, verifying each phase compiles and passes before proceeding

All pipeline state is stored in `.testagent/` at the project root (`research.md`, `plan.md`, `status.md`).

## Step-by-Step Instructions

### Step 1: Clarify the Request

Understand what the user is asking and for what scope:

- What scope? (entire project, specific files, specific classes/modules)
- Any priority areas or framework preferences?
- Any specific coverage goals?

If the user does not express strong requirements for test style, coverage goals, or conventions, follow the guidelines in [references/unit-test-generation.prompt.md](references/unit-test-generation.prompt.md) for best practices on discovering conventions, parameterization strategies, coverage goals (aim for 80%), and language-specific patterns.

### Step 2: Research Phase

Delegate to the `polyglot-test-researcher` agent (via the `task` tool with `agent_type: "polyglot-test-researcher"`) to analyze the codebase. Use `mode: "background"` so you can do preparation work while research runs. Use a prompt like:

```
Analyze the codebase to understand its structure and testing setup.

Project root: <project-root>
Scope: <scope — e.g., "entire project" or "src/services/UserService.ts">

Save your findings to: <project-root>/.testagent/research.md

Cover: language and testing framework, project structure, source files in scope,
existing tests, build and test commands, and relevant conventions.
```

While research is running, add `.testagent/` to the project's `.gitignore` if it isn't already there — this directory holds temporary orchestration state, not deliverable artifacts.

The researcher produces a research document covering:
- **Language & framework** (C#, TypeScript, Python, Go, Rust, Java, etc.)
- **Testing framework** (MSTest, xUnit, Jest, pytest, go test, etc.)
- **Project structure** (source files, existing tests, dependencies)
- **Build & test commands** (how to compile and run tests)

#### If research fails

If the researcher can't detect the language or framework (e.g., unconventional project layout), ask the user to clarify the language, testing framework, and build commands, then write `.testagent/research.md` manually and proceed to planning.

### Step 3: Planning Phase

After research completes, delegate to the `polyglot-test-planner` agent (`agent_type: "polyglot-test-planner"`, `mode: "sync"`). Use a prompt like:

```
Create a phased test implementation plan.

Research document: <project-root>/.testagent/research.md
Scope: <scope>

Save the plan to: <project-root>/.testagent/plan.md

Group files into 2–5 phases ordered by priority and complexity,
with specific test cases identified for each file.
```

The planner produces `.testagent/plan.md` with files grouped into 2–5 phases by priority and complexity.

#### If planning produces an unreasonable plan

Review the plan before proceeding to implementation. If the phases are too large (>10 files each), the grouping is illogical, or key files are missing, either adjust the plan yourself or re-run the planner with more specific guidance.

### Step 4: Implementation Phase

For each phase in the plan, delegate to the `polyglot-test-implementer` agent (`agent_type: "polyglot-test-implementer"`) sequentially. Use `mode: "background"` so you can provide status updates to the user while each phase runs. Use a prompt like:

```
Implement tests for Phase <N> of the test plan.

Plan:     <project-root>/.testagent/plan.md
Research: <project-root>/.testagent/research.md
Project root: <project-root>

Run the full build/test/fix cycle until all tests in this phase pass.
Update progress in: <project-root>/.testagent/status.md
```

Wait for each phase to complete before starting the next — this ensures earlier test files are stable before adding more.

The implementer handles the full cycle per phase:

1. Reads source files to understand the API
2. Writes test files following project patterns
3. For **compiled languages** (TypeScript, C#, Go, Rust, Java): verifies compilation via `polyglot-test-builder`; calls `polyglot-test-fixer` if it fails
4. Runs tests to verify they pass (via `polyglot-test-tester`)
5. Formats code if a linter is available (via `polyglot-test-linter`)

#### Handling failures

If an implementer phase fails after multiple fix attempts:
1. Read the error output to understand what went wrong
2. Check whether the issue is in the test code or the source code
3. If the test assumptions are wrong (e.g., mocking an interface that doesn't exist), update the plan and retry
4. If a specific file is persistently failing, skip it, continue with remaining phases, and report the failure to the user at the end

### Step 5: Report Results

After all phases are complete:

- Summarize tests created (files, test count, pass rate)
- Report any failures or unresolved issues
- Suggest next steps if needed

## Agent Reference

### Direct delegates (called by this skill)

| `agent_type`                | Purpose                                                             |
| --------------------------- | ------------------------------------------------------------------- |
| `polyglot-test-researcher`  | Analyzes codebase structure, language, framework, and build commands |
| `polyglot-test-planner`     | Groups files into prioritized phases with specific test cases       |
| `polyglot-test-implementer` | Writes test files for one phase and coordinates build/test/fix      |

### Internal agents (called by the implementer — do not call directly)

The implementer delegates to these agents as needed during its cycle. The builder is only invoked for compiled languages (TypeScript, C#, Go, Rust, Java); the fixer only if build or tests fail; the linter only if a lint command exists.

| `agent_type`              | Purpose                                                              |
| ------------------------- | -------------------------------------------------------------------- |
| `polyglot-test-builder`   | Runs the project build and reports compilation errors (compiled langs only) |
| `polyglot-test-tester`    | Executes the test suite and reports pass/fail results                |
| `polyglot-test-fixer`     | Reads build/test errors and patches source or test files             |
| `polyglot-test-linter`    | Runs project lint/format tools on generated files                    |

## Examples

### Full Project Testing

```
Generate unit tests for my Calculator project at src/Calculator
```

### Specific File Testing

```
Generate unit tests for src/services/UserService.ts
```

### Targeted Coverage

```
Add tests for the authentication module with focus on edge cases
```

## Requirements

- Project must have a build/test system configured (or be configurable — the researcher will attempt to discover commands)
- Testing framework should be installed (or installable)

## Troubleshooting

### Tests don't compile

The implementer automatically delegates to `polyglot-test-fixer` to resolve compilation errors. If errors persist after multiple attempts, check `.testagent/status.md` for details and consider adjusting the plan.

### Tests fail

Review the test output and adjust test expectations. Some tests may require mocking dependencies. Re-run the failing phase with updated guidance.

### Wrong testing framework detected

Specify your preferred framework in the initial request: "Generate Jest tests for..."

### Agent not available

If a required agent is unavailable, fall back to performing that step directly. For example, if `polyglot-test-builder` is unavailable, run the build command manually and inspect the output.
