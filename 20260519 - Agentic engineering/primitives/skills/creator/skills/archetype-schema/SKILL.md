---
name: archetype-schema
description: Define the archetype.json structure for Dev CLI archetypes. Use when creating or editing an archetype definition — covers top-level properties, parameters, files, and post-actions.
---

# Archetype Schema

Place `archetype.json` in `.dev/archetypes/<archetype-name>/`. Template files (`.scriban`) live in the same folder.

## Top-Level Properties

| Property                  | Type     | Req | Description                                                            |
| ------------------------- | -------- | --- | ---------------------------------------------------------------------- |
| `$schema`                 | string   | —   | `../archetype.schema.json`                                             |
| `name`                    | string   | ✓   | Unique identifier, kebab-case                                          |
| `displayName`             | string   | ✓   | Human-readable name                                                    |
| `description`             | string   | ✓   | What the archetype creates                                             |
| `version`                 | string   | ✓   | Semver: `1.0.0`                                                        |
| `extends`                 | string   | —   | Parent archetype name (inherits everything)                            |
| `internal`                | boolean  | —   | Hide from `list`/`new` commands (default: `false`)                     |
| `targetProjects`          | string[] | —   | Valid project names; wildcards supported: `Functions.*`                |
| `requiresProject`         | boolean  | —   | Prompt for project in interactive mode                                 |
| `requiresNamespace`       | boolean  | —   | Prompt for namespace in interactive mode                               |
| `supportsSchemaInference` | boolean  | —   | Enable `--schema` flag for type inference                              |
| `requiresSchemaInference` | boolean  | —   | Require `--schema`; implies `supportsSchemaInference`                  |
| `triggers`                | string[] | —   | `http`, `servicebus`, `timer`, `blob`, `queue`, `eventgrid`, `durable` |
| `defaultTrigger`          | string   | —   | Default trigger when not specified                                     |
| `parameters`              | object   | —   | Parameter definitions (see below)                                      |
| `files`                   | array    | —   | Template → file mappings (see below)                                   |
| `actions`                 | array    | —   | File modification actions (see archetype-actions skill)                |
| `postActions`             | array    | —   | Messages / commands after generation                                   |

---

## Parameters

Each key is the parameter name (PascalCase). Parameters are referenced in Scriban as `{{ ParameterName }}`.

### Parameter Properties

| Property          | Type    | Description                                                                  |
| ----------------- | ------- | ---------------------------------------------------------------------------- |
| `type`            | string  | `string`, `boolean`, `number`, `array`, `object` — **required**              |
| `description`     | string  | Help text in CLI — **required**                                              |
| `required`        | boolean | Must be provided (default: `false`)                                          |
| `default`         | any     | Default value                                                                |
| `source`          | string  | How value is obtained (default: `argument`)                                  |
| `computed`        | string  | Scriban expression — required when `source: computed`                        |
| `transform`       | string  | Applied after value is resolved (see transforms table)                       |
| `allowedValues`   | array   | Restrict to specific values                                                  |
| `prefix`          | string  | Prepended to value after transform                                           |
| `suffix`          | string  | Appended to value after transform                                            |
| `promptCondition` | string  | Scriban expression; only prompt user if evaluates to `true`                  |
| `inferredFrom`    | string  | Controls how the value is inferred when `source: inferred`; see values below |
| `itemSchema`      | object  | Schema for array items when `type` is `array`                                |

#### `inferredFrom` Values

| Value                 | Description                                                          |
| --------------------- | -------------------------------------------------------------------- |
| `schemaFileName`      | The filename (without extension) of the `--schema` file              |
| `schemaProperties`    | Top-level property names from the schema, provided as a string array |
| `schemaNestedObjects` | Names of nested object properties within the schema                  |
| `projectName`         | The project name derived from the schema context                     |
| `moduleName`          | The module name derived from the schema context                      |

### Sources

| Source        | Description                                          |
| ------------- | ---------------------------------------------------- |
| `argument`    | CLI argument `--ParameterName value` (default)       |
| `computed`    | Evaluated from a Scriban `computed` expression       |
| `inferred`    | Inferred from schema file (requires `--schema` flag) |
| `environment` | Read from environment variable                       |
| `prompt`      | Always prompted interactively                        |

### Transforms

Applied to string values after resolution:

| Transform     | Example input | Output      |
| ------------- | ------------- | ----------- |
| `PascalCase`  | `get order`   | `GetOrder`  |
| `camelCase`   | `GetOrder`    | `getOrder`  |
| `kebab-case`  | `GetOrder`    | `get-order` |
| `snake_case`  | `GetOrder`    | `get_order` |
| `UPPER_CASE`  | `GetOrder`    | `GETORDER`  |
| `Pluralize`   | `Order`       | `Orders`    |
| `Singularize` | `Orders`      | `Order`     |

### Built-in Parameters (always available)

| Parameter        | Description                            |
| ---------------- | -------------------------------------- |
| `ProjectName`    | Target project name                    |
| `Namespace`      | Subdirectory path                      |
| `RepositoryRoot` | Absolute path to repository root       |
| `Generator`      | Archetype name that generated the file |
| `GeneratedAt`    | Timestamp: `2026-01-15 14:00:00`       |

Use `{{ date.now | date.to_string '%Y-%m-%d' }}` for custom date formats.

### Parameter Examples

```json
"parameters": {
  "FeatureName": {
    "type": "string",
    "description": "Feature name in PascalCase",
    "required": true,
    "transform": "PascalCase"
  },
  "FullNamespace": {
    "type": "string",
    "description": "Computed namespace",
    "source": "computed",
    "computed": "{{ ProjectName }}.Features.{{ FeatureName }}"
  },
  "Trigger": {
    "type": "string",
    "default": "http",
    "allowedValues": ["http", "timer", "servicebus"]
  },
  "TimerSchedule": {
    "type": "string",
    "default": "0 * * * * *",
    "promptCondition": "{{ Trigger == 'timer' }}"
  }
}
```

---

## Files

Each entry renders a `.scriban` template into an output file. All string values support Scriban.

| Property        | Req | Description                                                |
| --------------- | --- | ---------------------------------------------------------- |
| `template`      | ✓   | Path to `.scriban` file, relative to archetype folder      |
| `output`        | ✓   | Output filename — supports Scriban: `{{ FeatureName }}.cs` |
| `targetProject` | —   | Destination project name — supports Scriban                |
| `targetPath`    | —   | Path within project — supports Scriban                     |
| `condition`     | —   | Scriban expression; file only generated if `true`          |
| `overwrite`     | —   | Overwrite existing files (default: `false`)                |

```json
"files": [
  {
    "template": "Handler.cs.scriban",
    "output": "{{ FeatureName }}Handler.cs",
    "targetProject": "{{ ProjectName }}",
    "targetPath": "Features/{{ FeatureName }}"
  },
  {
    "template": "HandlerTests.cs.scriban",
    "output": "{{ FeatureName }}HandlerTests.cs",
    "targetProject": "{{ ProjectName }}.Tests",
    "targetPath": "Features/{{ FeatureName }}",
    "condition": "{{ IncludeTests }}"
  }
]
```

---

## Post-Actions

Run after all files and actions are complete.

| Type          | Required fields | Description               |
| ------------- | --------------- | ------------------------- |
| `success`     | `message`       | Green success banner      |
| `info`        | `message`       | Info message              |
| `warning`     | `message`       | Yellow warning message    |
| `run-command` | `command`       | Execute a shell command   |
| `open-file`   | `file`          | Open a file in the editor |

All support an optional `condition` (Scriban expression).

```json
"postActions": [
  { "type": "success", "message": "{{ FeatureName }} created in {{ ProjectName }}!" },
  { "type": "warning", "message": "Remember to register the service.", "condition": "{{ NeedsRegistration }}" },
  { "type": "run-command", "command": "dotnet build" }
]
```

---

## Complete Minimal Example

```json
{
  "$schema": "../archetype.schema.json",
  "name": "cqrs-query",
  "displayName": "CQRS Query",
  "description": "Creates a CQRS query with handler and tests",
  "version": "1.0.0",
  "targetProjects": ["Web.Api", "Functions.*"],
  "parameters": {
    "QueryName": {
      "type": "string",
      "description": "Query name in PascalCase",
      "required": true,
      "transform": "PascalCase"
    },
    "IncludeTests": {
      "type": "boolean",
      "description": "Generate test files",
      "default": true
    },
    "RootNamespace": {
      "type": "string",
      "source": "computed",
      "computed": "{{ ProjectName }}.Features{{ if Namespace }}.{{ Namespace | string.replace '/' '.' }}{{ end }}.{{ QueryName }}"
    }
  },
  "files": [
    {
      "template": "Handler.cs.scriban",
      "output": "{{ QueryName }}Handler.cs",
      "targetProject": "{{ ProjectName }}",
      "targetPath": "Features/{{ QueryName }}"
    },
    {
      "template": "HandlerTests.cs.scriban",
      "output": "{{ QueryName }}HandlerTests.cs",
      "targetProject": "{{ ProjectName }}.Tests",
      "targetPath": "Features/{{ QueryName }}",
      "condition": "{{ IncludeTests }}"
    }
  ],
  "postActions": [
    { "type": "success", "message": "Query {{ QueryName }} created!" }
  ]
}
```

---

## Validation Checklist

- [ ] `name` is kebab-case
- [ ] `version` is semver (`X.Y.Z`)
- [ ] Every parameter has `type` and `description`
- [ ] `source: computed` parameters have a `computed` expression
- [ ] Template files referenced in `files` exist with `.scriban` extension
- [ ] `condition` and `computed` expressions use correct Scriban syntax (`{{ }}`)
- [ ] Action `file` paths are correct (see archetype-actions skill)
