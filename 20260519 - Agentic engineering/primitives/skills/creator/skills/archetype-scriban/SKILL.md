---
name: archetype-scriban
description: Scriban template syntax for Dev CLI archetypes. Use when writing .scriban template files or Scriban expressions inside archetype.json (output paths, conditions, computed parameters, action values).
---

# Scriban in Archetypes

## Where Scriban Is Used

Scriban expressions (`{{ ... }}`) appear in two places:

**Inside `.scriban` template files** — the full template body.

**Inline in `archetype.json` fields:**

| Field                          | Example                                          |
| ------------------------------ | ------------------------------------------------ |
| `files[].output`               | `"{{ FeatureName }}Handler.cs"`                  |
| `files[].targetProject`        | `"{{ ProjectName }}.Tests"`                      |
| `files[].targetPath`           | `"Features/{{ Namespace }}/{{ FeatureName }}"`   |
| `files[].condition`            | `"{{ IncludeTests }}"`                           |
| `parameters[].computed`        | `"{{ ProjectName }}.Features.{{ FeatureName }}"` |
| `parameters[].promptCondition` | `"{{ Trigger == 'timer' }}"`                     |
| `actions[].condition`          | `"{{ HasServiceBus }}"`                          |
| `actions[].file`               | `"infra/{{ FeatureName \| kebab_case }}.bicep"`  |
| `actions[].parameters.*`       | `"'{{ QueueName }}'"`                            |
| `postActions[].message`        | `"{{ FeatureName }} created successfully!"`      |

---

## Variables

```scriban
{{ FeatureName }}
{{ ProjectName }}
{{ Namespace }}
```

All parameter names are PascalCase. Access is direct — no `params.` prefix.

---

## Conditionals

```scriban
{{ if IncludeTests }}
// test-specific content
{{ end }}

{{ if Namespace }}
using {{ Namespace }};
{{ else }}
// no namespace
{{ end }}

{{ if Trigger == 'http' }}
[HttpGet]
{{ else if Trigger == 'timer' }}
[TimerTrigger]
{{ end }}
```

### Truthy Rules (critical)

| Value             | Evaluates as |
| ----------------- | ------------ |
| `true`            | true         |
| `false`           | false        |
| Non-empty string  | **true**     |
| Empty string `""` | false        |
| `null`            | false        |
| Any number ≠ 0    | true         |

> **Gotcha**: `{{ if SomeString }}` is `true` even if SomeString is `"false"`. Use `{{ if SomeString == 'false' }}` to compare string values. For boolean parameters, always use the `boolean` type — never `string`.

---

## Loops

```scriban
{{ for item in Items }}
- {{ item.Name }}: {{ item.Value }}
{{ end }}

{{~ for item in Items ~}}
{{ item }}
{{~ end ~}}
```

Use `~` to strip surrounding whitespace/newlines.

---

## Built-in String Filters

```scriban
{{ value | string.downcase }}       → "myfeature"
{{ value | string.upcase }}         → "MYFEATURE"
{{ value | string.capitalize }}     → "Myfeature"
{{ value | string.replace '/' '.' }}→ "a.b.c"
{{ value | string.contains 'abc' }} → true/false
{{ value | string.starts_with 'My' }}
{{ value | string.strip }}          → trimmed
{{ value | string.strip_left }}
{{ value | string.strip_right }}
{{ "prefix-" | string.append value }}
```

Array filters:

```scriban
{{ items | array.first }}
{{ items | array.last }}
{{ items | array.size }}
{{ items | array.join ', ' }}
```

---

## Custom Filters

These are the most important — use them instead of manual casing:

```scriban
{{ value | pascal_case }}    → "GetOrder"
{{ value | camel_case }}     → "getOrder"
{{ value | kebab_case }}     → "get-order"
{{ value | snake_case }}     → "get_order"
{{ value | pluralize }}      → "Orders"
{{ value | singularize }}    → "Order"
{{ code  | indent 4 }}       → adds 4 spaces to every line
{{ type  | nullable }}       → "string?"
```

> **Gotcha**: In JSON `computed` expressions, use `string.downcase`/`string.upcase`. The custom filters (`pascal_case` etc.) work in both template files and JSON inline expressions.

---

## Common Patterns

### Namespace from path

```scriban
{{ Namespace | string.replace '/' '.' }}
```

### Conditional namespace segment

```scriban
{{ ProjectName }}.Features{{ if Namespace }}.{{ Namespace | string.replace '/' '.' }}{{ end }}.{{ FeatureName }}
```

### Conditional path segment

```scriban
Features{{ if Namespace }}/{{ Namespace }}{{ end }}/{{ FeatureName }}
```

### Lowercase kebab for file/resource names

```scriban
{{ FeatureName | kebab_case }}
```

### Computed parameter using multiple transforms

```json
"TopicNameKebab": {
  "type": "string",
  "source": "computed",
  "computed": "{{ TopicName | kebab_case | string.downcase }}"
}
```

---

## Template File Patterns

Typical C# template structure:

```scriban
namespace {{ RootNamespace }};

public sealed class {{ FeatureName }}Handler
{
    {{ if IncludeDependency }}
    private readonly IDependency _dependency;

    public {{ FeatureName }}Handler(IDependency dependency)
    {
        _dependency = dependency;
    }
    {{ end }}
}
```

Use `{{~` and `~}}` to avoid blank lines from conditional blocks:

```scriban
{{~ if IncludeLogging ~}}
using Microsoft.Extensions.Logging;
{{~ end ~}}

namespace {{ RootNamespace }};
```

---

## Gotchas

| Mistake                                                     | Fix                                                                               |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| String param used as boolean condition                      | Declare as `type: boolean`                                                        |
| `{{ if Namespace == "" }}` to check empty                   | Use `{{ if !Namespace }}` or `{{ if Namespace == null \|\| Namespace == '' }}`    |
| Quotes in JSON `computed` — `"computed": "{{ 'literal' }}"` | Use single quotes inside Scriban inside JSON double-quoted string                 |
| Custom transform not applied in `condition`                 | `condition` evaluates after transforms — reference the transformed value directly |
| `{{ false }}` rendered as string "false" in output          | Use conditionals, don't interpolate booleans directly into text                   |
