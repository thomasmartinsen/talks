---
name: archetype-creator
description: Design and build an archetype for the Dev CLI
---

**Steps**

1. **Clarify what to build**

   If a clear name and purpose haven't been provided, use the **AskUserQuestion tool** to ask:

   > "What should this archetype scaffold? Describe the feature, integration pattern, or file structure you want to generate."

   From the description, derive a kebab-case archetype name (e.g., "service bus consumer" → `servicebus-consumer`).

   **Do NOT proceed without knowing what the archetype should produce.**

2. **Load skill files**

   Always read the following skill:
   - `archetype-schema/SKILL.md` — `archetype.json` structure, parameters, files, post-actions

   Read additionally the following skills as needed:
   - `archetype-scriban/SKILL.md` — when writing `.scriban` templates
   - `archetype-actions/SKILL.md` — when wiring up Bicep, YAML, JSON, C#, or command actions

3. **Check for existing archetypes**

   List `.dev/archetypes/` to understand what already exists. If there's an archetype close to what's needed:
   - Read it as inspiration for structure and conventions

4. **Design the archetype**

   Before writing files, think through:
   - What files does this archetype generate?
   - What parameters does the user need to supply?
   - Are any actions needed (e.g., appending to an existing file)?
   - What post-action messages should appear after generation?

   If the design has non-obvious choices, briefly describe them so the user can confirm before you write files.

5. **Create the archetype**

   Write files to `.dev/archetypes/<name>/`:
   - **`archetype.json`** following the schema from the skill file:
     - Include `$schema: "../archetype.schema.json"`
     - Use PascalCase parameter names
     - Map each template with `template` → `output` (output paths may use `{{ ParameterName }}`)

   - **`.scriban` templates** for each generated file:
     - Keep templates production-ready and idiomatic
     - Use `{{ string.downcase ParameterName }}`, `{{ string.pascalcase ParameterName }}` etc. for casing
     - Emit clean, working code — not placeholder stubs

6. **Validate**

   Run:

   ```bash
   dev-cli archetype validate <name>
   ```

   If validation fails, fix the reported issues and re-validate before finishing.

7. **Show a summary**

   After successful validation, output:
   - The archetype name and location
   - Parameters the user will be prompted for when running `dev-cli archetype new <name>`
   - Files that will be generated
   - Any actions that will run

---

**Guardrails**

- Archetype names must be **kebab-case** and unique within `.dev/archetypes/`
- Template files must use the **`.scriban`** extension
- Always include `$schema` pointing to `../../archetype.schema.json`
- Output paths in `files` may interpolate parameters with `{{ ParameterName }}`
- Never write direct code to a project — only archetype definitions and templates
- If modifying an existing archetype, read the current state first and preserve intent
