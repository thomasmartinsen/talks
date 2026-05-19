# creator

A pack for creating and iterating on GitHub Copilot CLI skills and Dev CLI archetypes.

---

## Contents

### Skills

#### `skill-creator`

A Copilot CLI skill that guides you through the full lifecycle of building a skill — from capturing intent to iterating on quality using automated evals.

**What it helps you do:**

- Write a new skill from scratch (interview → draft → test → iterate)
- Improve an existing skill based on eval results
- Run evaluation suites and benchmark skill performance with variance analysis
- Optimize a skill's description so it triggers reliably

---

#### `archetype-creator`

A Copilot CLI skill that guides you through designing and building a new Dev CLI archetype — from clarifying intent to writing templates, wiring actions, and validating the result.

**What it helps you do:**

- Clarify what the archetype should scaffold and derive a kebab-case name
- Design the parameter surface, file mappings, and post-actions before writing anything
- Write `archetype.json` and `.scriban` templates that are production-ready
- Run `dev-cli archetype validate` and fix any reported issues
- Summarise the archetype (parameters, generated files, actions) once complete

The skill automatically loads `archetype-schema`, `archetype-scriban`, and `archetype-actions` as reference material when needed.

---

#### `archetype-schema`

A reference skill covering the complete `archetype.json` structure. Used internally by `archetype-creator` and useful on its own when editing an existing archetype definition.

**Covers:**

- Top-level properties (`name`, `version`, `targetProjects`, `triggers`, …)
- Parameter definitions — types, sources, transforms, computed expressions, `promptCondition`
- File mappings — `template`, `output`, `targetProject`, `targetPath`, `condition`
- Post-actions — `success`, `info`, `warning`, `run-command`, `open-file`
- Built-in parameters (`ProjectName`, `Namespace`, `RepositoryRoot`, …)

---

#### `archetype-scriban`

A reference skill covering Scriban template syntax as used in Dev CLI archetypes — both inside `.scriban` template files and inline in `archetype.json` fields.

**Covers:**

- Variables, conditionals, loops, and whitespace control (`{{~` / `~}}`)
- Built-in string and array filters
- Custom filters: `pascal_case`, `camel_case`, `kebab_case`, `snake_case`, `pluralize`, `indent`, `nullable`
- Common patterns (namespace from path, conditional segments, computed transforms)
- Common gotchas (string-vs-boolean conditions, blank lines from conditionals)

---

#### `archetype-actions`

A reference skill covering all action types available in an archetype's `actions` array — used to modify existing files after template generation.

**Action types:**

| Action | Description |
| --- | --- |
| `create-file` | Create a new file from a template |
| `modify-bicep` | Add parameters, variables, resources, modules, or imports to `.bicep` files |
| `modify-bicepparam` | Add or update params and object arrays in `.bicepparam` files |
| `modify-yaml` | Set properties, add array elements, merge or remove nodes in YAML files |
| `modify-json` | Set properties, add array elements, merge or remove nodes in JSON files |
| `modify-text` | Pattern-based insertions and replacements for any file type |
| `modify-csproj` | Add package references, set properties, or add items in `.csproj` files |
| `add-project-reference` | Add a project-to-project reference |
| `run-command` | Execute a shell command after generation |
| `copilot` | Invoke GitHub Copilot with a natural language prompt |

---

## Agents

The skill ships with three specialist agents used during the eval and improvement loop:

| Agent        | Role                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------ |
| `analyzer`   | Examines skill runs and extracts structured observations about what worked and what didn't |
| `comparator` | Compares two skill versions head-to-head to determine which performs better                |
| `grader`     | Scores individual skill outputs against a set of defined expectations                      |

---

## Workflow

The iterative improvement loop looks like this:

```
Capture intent
     │
     ▼
Write SKILL.md draft
     │
     ▼
Create eval cases (prompts + expectations)
     │
     ▼
Run evals  ──────────────────────────────┐
     │                                   │
     ▼                                   │
Grade outputs (grader)                   │
     │                                   │
     ▼                                   │
Compare versions (comparator)            │
     │                                   │
     ▼                                   │
Analyze results (analyzer)               │
     │                                   │
     ▼                                   │
Rewrite skill based on findings  ────────┘
     │
     ▼
Run description optimizer
```

Each iteration produces a pass rate you can track over time. Once you're satisfied, run the **description optimizer** to make sure the skill triggers on the right user phrases.

---

### Archetype authoring workflow

```
Clarify what to scaffold
         │
         ▼
Design parameters, files & actions
         │
         ▼
Write archetype.json + .scriban templates
         │
         ▼
Run dev-cli archetype validate
         │
    ┌────┴────┐
  Fails     Passes
    │         │
    ▼         ▼
  Fix      Show summary
 issues   (params / files / actions)
    │
    └──────────┘
```

`archetype-creator` drives the loop. `archetype-schema`, `archetype-scriban`, and `archetype-actions` are loaded automatically as reference material when needed.
