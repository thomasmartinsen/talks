---
name: archetype-actions
description: All action types for Dev CLI archetypes. Use when wiring up infrastructure changes, file modifications, project references, or AI-powered actions in an archetype's actions array.
---

# Archetype Actions

Actions modify **existing** files after template generation. All actions share these base fields:

## Available Action Types

- `create-file` — create a new file from a template
- `modify-bicep` — add parameters, variables, resources, modules, imports to `.bicep` files
- `modify-bicepparam` — add/update params and object arrays in `.bicepparam` files
- `modify-yaml` — set properties, add array elements, merge or remove nodes in `.yml`/`.yaml` files
- `modify-json` — set properties, add array elements, merge or remove nodes in `.json` files
- `modify-text` — pattern-based insertions and replacements for any file type
- `modify-csproj` — add package references, set properties, add items in `.csproj` files
- `add-project-reference` — add a project-to-project reference
- `run-command` — execute a shell command after generation
- `copilot` — invoke GitHub Copilot with a natural language prompt

---

## Base Fields

| Field         | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| `type`        | Action type — required                                       |
| `description` | Human-readable label — optional                              |
| `file`        | Target file path — required for most types; supports Scriban |
| `condition`   | Scriban expression; action skipped if not `true` — optional  |
| `parameters`  | Action-specific config — see each type below                 |

---

## `create-file`

Create a new file from a template.

```json
{
  "type": "create-file",
  "file": "src/Apps/Web.Api/config/{{ FeatureName }}.json",
  "parameters": {
    "template": "config.json.scriban",
    "overwrite": false
  }
}
```

| Parameter      | Req   | Description                                       |
| -------------- | ----- | ------------------------------------------------- |
| `template`     | Yes\* | Template file path (relative to archetype folder) |
| `templatePath` | Yes\* | Alternative to `template`                         |
| `overwrite`    | —     | Overwrite if exists (default: `false`)            |

\*Either `template` or `templatePath` required.

---

## `modify-bicep`

Modify `.bicep` files. **File field required.**

### `add-parameter`

```json
{ "operation": "add-parameter", "name": "myParam", "type": "string" }
```

### `add-variable`

```json
{ "operation": "add-variable", "name": "myVar", "value": "'my-value'" }
```

### `add-resource`

```json
{
  "operation": "add-resource",
  "name": "myQueue",
  "resourceType": "Microsoft.ServiceBus/namespaces/queues@2024-01-01",
  "parent": "sbNamespace",
  "properties": {
    "name": "'{{ QueueName | kebab_case }}'",
    "properties": {
      "maxSizeInMegabytes": "1024",
      "enablePartitioning": "false"
    }
  }
}
```

### `add-module`

```json
{
  "operation": "add-module",
  "name": "{{ FeatureName }}Api",
  "path": "../../../templates/apim-api.bicep",
  "deploymentName": "{{ FeatureName | kebab_case }}-api",
  "properties": {
    "apimName": "=apim.name",
    "apiName": "'{{ FeatureName }}'"
  }
}
```

### `add-import`

```json
{ "operation": "add-import", "path": "./types/custom.bicep" }
```

### `add-property-to-type`

```json
{
  "operation": "add-property-to-type",
  "targetType": "ConfigType",
  "name": "myProp",
  "type": "string"
}
```

### `add-property-to-variable`

```json
{
  "operation": "add-property-to-variable",
  "targetVariable": "config",
  "name": "myProp",
  "value": "'value'"
}
```

### `add-element-to-array`

```json
{
  "operation": "add-element-to-array",
  "targetVariable": "myArray",
  "value": "'new-element'"
}
```

### Property Value Prefixes (critical!)

| Pattern            | Bicep result   | Example input                                        |
| ------------------ | -------------- | ---------------------------------------------------- |
| `=expression`      | Raw expression | `"=shared.naming.sb.name"` → `shared.naming.sb.name` |
| `"true"`/`"false"` | Boolean        | `"true"` → `true`                                    |
| Numeric string     | Integer        | `"1024"` → `1024`                                    |
| Everything else    | Quoted string  | `"my-queue"` → `'my-queue'`                          |

> Use `=` prefix for variable references, function calls, and any raw Bicep expression that must **not** be quoted.

---

## `modify-bicepparam`

Modify `.bicepparam` files. **File field required.**

### `add-object-to-array`

```json
{
  "type": "modify-bicepparam",
  "file": "infra/infra.dev.bicepparam",
  "parameters": {
    "operation": "add-object-to-array",
    "paramName": "shared.config.sb.queues",
    "identifyingProperty": "name",
    "skipIfExists": true,
    "properties": {
      "name": "'{{ QueueName | kebab_case }}'",
      "enabled": "true"
    }
  }
}
```

### `add-property`

```json
{
  "operation": "add-property",
  "paramName": "shared.config",
  "propertyPath": "feature.enabled",
  "value": "true"
}
```

### `add-parameter-assignment`

```json
{
  "operation": "add-parameter-assignment",
  "name": "newParam",
  "value": "'paramValue'"
}
```

| Parameter             | Description                                             |
| --------------------- | ------------------------------------------------------- |
| `paramName`           | Dot-path to the target param: `shared.config.sb.queues` |
| `identifyingProperty` | Property used to check for duplicates                   |
| `skipIfExists`        | Skip if already present (default: `true`)               |

---

## `modify-yaml`

Modify `.yml`/`.yaml` files. **File field required.**
Use dot-notation with numeric indices for paths: `stages.0.jobs.1.steps`

### `add-to-array`

```json
{
  "operation": "add-to-array",
  "path": "stages.0.jobs",
  "position": "end",
  "value": { "job": "NewJob", "displayName": "New Job" }
}
```

### `set-property`

```json
{
  "operation": "set-property",
  "path": "settings.feature.enabled",
  "value": true
}
```

### `merge-object`

```json
{
  "operation": "merge-object",
  "path": "settings",
  "value": { "newKey": "newValue" }
}
```

### `remove-node`

```json
{ "operation": "remove-node", "path": "settings.deprecated" }
```

---

## `modify-json`

Modify `.json` files. **File field required.**
Supports Scriban in `path`: `"Features.{{ FeatureName }}"`

### `set-property`

```json
{
  "operation": "set-property",
  "path": "Features.{{ FeatureName }}",
  "value": { "Enabled": true, "Timeout": 30 }
}
```

### `add-to-array`

```json
{
  "operation": "add-to-array",
  "path": "scripts",
  "position": "end",
  "value": "new-script"
}
```

### `merge-object`

```json
{
  "operation": "merge-object",
  "path": "ConnectionStrings",
  "value": { "{{ FeatureName }}": "..." }
}
```

### `remove-node`

```json
{ "operation": "remove-node", "path": "settings.deprecated" }
```

---

## `modify-text`

Pattern-based text modifications for any file type. **File field required.**

### `insert-after-pattern`

```json
{
  "operation": "insert-after-pattern",
  "pattern": "services.AddScoped<",
  "matchLast": true,
  "matchUntil": ");",
  "value": "\n        services.AddScoped<I{{ FeatureName }}Service, {{ FeatureName }}Service>();",
  "skipIfContains": "I{{ FeatureName }}Service",
  "continueOnError": true
}
```

### `insert-before-pattern`

```json
{
  "operation": "insert-before-pattern",
  "pattern": "namespace ",
  "value": "using {{ RootNamespace }};\n",
  "skipIfContains": "using {{ RootNamespace }}"
}
```

### `replace-pattern`

```json
{
  "operation": "replace-pattern",
  "pattern": "OldValue",
  "value": "NewValue",
  "isRegex": false
}
```

### `add-using`

```json
{ "operation": "add-using", "namespace": "System.Text.Json" }
```

| Parameter         | Default | Description                                    |
| ----------------- | ------- | ---------------------------------------------- |
| `pattern`         | —       | Text or regex pattern to match                 |
| `value`           | —       | Content to insert or replace; supports Scriban |
| `valuePath`       | —       | Template file path (alternative to `value`)    |
| `matchLast`       | false   | Match last occurrence instead of first         |
| `matchUntil`      | —       | Extend match to end of this pattern            |
| `isRegex`         | false   | Treat `pattern` as a regex                     |
| `skipIfContains`  | —       | Skip if file already contains this text        |
| `indentation`     | —       | Number of spaces to indent inserted content    |
| `continueOnError` | false   | Don't fail the archetype if match not found    |

---

## `modify-csproj`

Modify `.csproj` files. **File field required.**

### `add-package-reference`

```json
{ "operation": "add-package-reference", "name": "FluentValidation" }
```

### `set-property`

```json
{ "operation": "set-property", "name": "TargetFramework", "value": "net9.0" }
```

### `add-item`

```json
{
  "operation": "add-item",
  "itemType": "Content",
  "value": "files/**/*",
  "metadata": { "CopyToOutputDirectory": "PreserveNewest" }
}
```

---

## `add-project-reference`

Add a project-to-project reference. No `file` field — `project` is in `parameters`.

```json
{
  "type": "add-project-reference",
  "description": "Add reference to DataContracts",
  "parameters": {
    "project": "Web.Api",
    "reference": "Services.DataContracts"
  }
}
```

---

## `run-command`

Execute a shell command after generation.

```json
{
  "type": "run-command",
  "parameters": {
    "command": "dotnet format {{ ProjectPath }}",
    "workingDirectory": "{{ RepositoryRoot }}",
    "failOnError": false
  }
}
```

---

## `copilot`

Invoke GitHub Copilot with a natural language prompt (requires Copilot SDK).

```json
{
  "type": "copilot",
  "description": "Generate mapper",
  "parameters": {
    "prompt": "Create a Mapperly mapper for {{ FeatureName }}Request to {{ FeatureName }}Entity.",
    "workingDirectory": "src/Apps/{{ ProjectName }}",
    "systemMessage": "You are a C# expert.",
    "agent": "dev-cli.archetype-dev",
    "timeout": 120,
    "availableTools": ["read_file", "create_file", "file_search"]
  }
}
```

| Parameter          | Req | Description                               |
| ------------------ | --- | ----------------------------------------- |
| `prompt`           | ✓   | Natural language prompt; supports Scriban |
| `workingDirectory` | —   | Working directory (default: repo root)    |
| `model`            | —   | Specific model (e.g., `gpt-4`)            |
| `systemMessage`    | —   | System message prepended to conversation  |
| `agent`            | —   | Pre-configured agent name                 |
| `timeout`          | —   | Seconds before timeout (default: 120)     |
| `availableTools`   | —   | Tools made available to the agent         |
