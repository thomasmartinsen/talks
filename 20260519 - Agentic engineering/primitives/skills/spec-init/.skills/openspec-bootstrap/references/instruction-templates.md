# Instruction Templates

Reference for Phase 5: generating instructions and rules for all supported AI tools.

Each tool has its own file format and location, but the **content** is the same. Write the content once, then express it in each tool's format. See `references/tool-conventions.md` for the full format specifications.

---

## GitHub Copilot Format

Location: `.github/instructions/<topic>.instructions.md`

```markdown
---
description: Brief description of what this instruction covers
applyTo: "glob/pattern/**/*"
---

# Title

Content here...
```

### Key rules for `applyTo`:

- `**/*` — applies to all files (global)
- `src/**/*` — applies to source files
- `**/*.test.*` — applies to test files
- `**/*.{ts,tsx}` — applies to TypeScript files
- Multiple patterns: use separate instruction files, one per scope

## Claude Code Format

Location: `.claude/rules/<topic>.md`

```markdown
---
paths:
  - "src/**/*"
---

# Title

Content here...
```

- Rules without `paths` frontmatter apply globally
- Supports arrays: `["src/**/*.ts", "lib/**/*.ts"]`
- Brace expansion: `"src/**/*.{ts,tsx}"`

## OpenAI Codex Format

Location: `AGENTS.md` (sections within the root file)

```markdown
## Topic Name

Content here...
```

- No frontmatter — all content in a single file organized by sections
- For monorepos, place service-specific content in subdirectory `AGENTS.md` files

## Cursor Format

Location: `.cursor/rules/<topic>.mdc`

```markdown
---
description: Brief description
globs: "src/**/*.{ts,tsx}"
alwaysApply: false
---

# Title

Content here...
```

- `alwaysApply: true` for global rules (equivalent to `**/*`)
- `globs` for file-scoped activation

## Windsurf Format

Location: `.windsurfrules` (sections within single root file)

```markdown
## Topic Name

Content here...
```

- No frontmatter, no scoping — all content applies globally

---

## Required Instruction Topics

The following five topics must be generated for **every** detected AI tool. The templates below show the content — adapt the file format (frontmatter, location) to each tool using the format specifications above.

### 1. Domain Context

**Copilot:** `.github/instructions/domain-context.instructions.md` (`applyTo: "**/*"`)
**Claude:** `.claude/rules/domain-context.md` (no `paths` = global)
**Codex:** Section in `AGENTS.md`
**Cursor:** `.cursor/rules/domain-context.mdc` (`alwaysApply: true`)
**Windsurf:** Section in `.windsurfrules`

**Content template:**

```markdown
---
description: Project domain context, vocabulary, and business rules
applyTo: "**/*"
---

# Domain Context

## Project Overview
[FILL: 2-3 sentence description of what this project does and who it serves]

## Domain Vocabulary

Use these terms consistently throughout the codebase:

| Term | Definition | Do NOT use |
|------|-----------|------------|
| [FILL: e.g., Workspace] | [FILL: A container for projects owned by a team] | [FILL: Tenant, Organization] |
| [FILL: e.g., Member] | [FILL: A user within a workspace] | [FILL: User, Account] |
| [FILL: e.g., Sprint] | [FILL: A time-boxed iteration] | [FILL: Iteration, Cycle] |

## Business Rules

These invariants must be preserved in all code changes:

- [FILL: e.g., An order MUST have at least one line item]
- [FILL: e.g., Free-tier workspaces are limited to 3 projects]
- [FILL: e.g., Deleted items are soft-deleted (marked inactive), never hard-deleted]
- [FILL: e.g., All monetary values are stored as integers in cents, displayed with 2 decimal places]

## Specifications

Behavioral specifications live in `openspec/specs/`. Always check the relevant spec before making changes to ensure new code aligns with documented behavior. If the spec is outdated, update it via `/opsx:propose`.
```

---

### 2. Coding Standards

**Copilot:** `.github/instructions/coding-standards.instructions.md` (`applyTo: "src/**/*"`)
**Claude:** `.claude/rules/coding-standards.md` (`paths: ["src/**/*"]`)
**Codex:** Section in `AGENTS.md`
**Cursor:** `.cursor/rules/coding-standards.mdc` (`globs: "src/**/*"`)
**Windsurf:** Section in `.windsurfrules`

**Content template:**

```markdown
---
description: Language conventions, naming patterns, and code organization standards
applyTo: "[FILL: src/**/* or appropriate source glob]"
---

# Coding Standards

## Naming Conventions

| Context | Convention | Example |
|---------|-----------|---------|
| Files | [FILL: kebab-case / snake_case / PascalCase] | [FILL: user-profile.tsx] |
| Components | [FILL: PascalCase] | [FILL: UserProfile] |
| Functions | [FILL: camelCase] | [FILL: getUserById] |
| Variables | [FILL: camelCase] | [FILL: isLoading] |
| Constants | [FILL: SCREAMING_SNAKE] | [FILL: MAX_RETRY_COUNT] |
| Types/Interfaces | [FILL: PascalCase] | [FILL: UserResponse] |
| Database columns | [FILL: snake_case] | [FILL: created_at] |
| CSS classes | [FILL: kebab-case / BEM / utility] | [FILL: card-header] |
| Environment vars | [FILL: SCREAMING_SNAKE] | [FILL: DATABASE_URL] |

## File Organization

[FILL: Describe how files are organized — by feature, by layer, by domain. Include examples.]

```
[FILL: Example directory tree showing the expected organization pattern]
```

## Imports

[FILL: Import ordering rules, absolute vs relative, barrel exports policy]

## Error Handling

[FILL: How errors are handled — custom error classes, error boundaries, middleware, Result types]

## Comments & Documentation

- [FILL: When to comment — only for "why", not "what"]
- [FILL: JSDoc/docstring requirements — public APIs, complex functions]
- [FILL: TODO format — e.g., "TODO(username): description"]

## Patterns to Follow

[FILL: Key patterns specific to this project's stack, e.g.:]
- [e.g., Use Server Actions for form mutations, not API routes]
- [e.g., All database queries go through the repository layer]
- [e.g., Use the Result pattern for operations that can fail]

## Anti-Patterns to Avoid

[FILL: Patterns explicitly banned in this project, e.g.:]
- [e.g., No `any` type — use `unknown` and narrow with type guards]
- [e.g., No barrel exports — import directly from the source file]
- [e.g., No nested ternaries — use early returns or if/else]
```

---

### 3. Security

**Copilot:** `.github/instructions/security.instructions.md` (`applyTo: "**/*"`)
**Claude:** `.claude/rules/security.md` (no `paths` = global)
**Codex:** Section in `AGENTS.md`
**Cursor:** `.cursor/rules/security.mdc` (`alwaysApply: true`)
**Windsurf:** Section in `.windsurfrules`

**Content template:**

```markdown
---
description: Security rules, authentication patterns, and data protection requirements
applyTo: "**/*"
---

# Security Rules

## Authentication

[FILL: How authentication works in this project]
- [FILL: Auth provider and mechanism (JWT, sessions, OAuth)]
- [FILL: How to protect routes/endpoints]
- [FILL: Token handling rules (storage, refresh, expiry)]

## Authorization

[FILL: How authorization is enforced]
- [FILL: RBAC/ABAC model and available roles]
- [FILL: How to check permissions in code]
- [FILL: Row-level security patterns if applicable]

## Input Validation

All external input MUST be validated before processing:
- [FILL: Validation library and patterns (Zod, class-validator, etc.)]
- [FILL: Where validation happens (API boundary, service layer, both)]
- [FILL: Sanitization rules for user-generated content]

## Secrets & Credentials

- NEVER hardcode secrets, API keys, passwords, or tokens in source code
- NEVER log sensitive data (passwords, tokens, PII, payment info)
- NEVER commit `.env` files — use `.env.example` with placeholder values
- [FILL: How secrets are managed (Vault, AWS SSM, environment variables)]
- [FILL: How to add new secrets to the project]

## Data Protection

- [FILL: PII handling rules]
- [FILL: Encryption requirements (at rest, in transit)]
- [FILL: Data retention and deletion policies]
- [FILL: Compliance requirements (GDPR, HIPAA, SOC2, PCI) if any]

## Common Vulnerabilities to Prevent

- **SQL Injection**: [FILL: Always use parameterized queries / ORM, never string concatenation]
- **XSS**: [FILL: Sanitize user content, use framework's built-in escaping]
- **CSRF**: [FILL: How CSRF is prevented in this project]
- **Path Traversal**: [FILL: Validate and sanitize file paths]
- **Mass Assignment**: [FILL: Use explicit allowlists for request body fields]

## Dependency Security

- [FILL: How dependency vulnerabilities are tracked (Dependabot, Snyk, npm audit)]
- [FILL: Policy for addressing vulnerabilities (critical within 24h, high within 1 week)]
- [FILL: Review requirements for new dependencies]
```

---

### 4. Testing

**Copilot:** `.github/instructions/testing.instructions.md` (`applyTo: "**/*.test.*"`)
**Claude:** `.claude/rules/testing.md` (`paths: ["**/*.test.*", "**/*.spec.*"]`)
**Codex:** Section in `AGENTS.md`
**Cursor:** `.cursor/rules/testing.mdc` (`globs: "**/*.test.*"`)
**Windsurf:** Section in `.windsurfrules`

**Content template:**

```markdown
---
description: Testing conventions, patterns, and requirements
applyTo: "[FILL: **/*.test.*, **/*.spec.*, test/**/*]"
---

# Testing Conventions

## Test Framework

[FILL: Primary test framework and supporting libraries]

## Test Organization

[FILL: How tests are organized — colocated, separate directory, etc.]

```
[FILL: Example test file structure]
```

## Test Naming

[FILL: Test naming convention, e.g.:]
- Describe block: name of the unit under test
- It/test block: "should [expected behavior] when [condition]"
- Example: `describe('UserService')` → `it('should return user when valid ID is provided')`

## Writing Tests

### Unit Tests
- [FILL: What to unit test, isolation patterns, mocking approach]
- [FILL: Mock library and conventions]

### Integration Tests
- [FILL: What to integration test, database/service setup patterns]
- [FILL: Test database management (in-memory, test containers, fixtures)]

### E2E Tests
- [FILL: E2E framework, page object patterns, test data setup]
- [FILL: Which flows require E2E coverage]

## Test Data

- [FILL: How test data is created (factories, fixtures, builders)]
- [FILL: Naming conventions for test data]
- [FILL: Cleanup strategy]

## Coverage

- [FILL: Coverage targets (e.g., 80% overall, 90% for business logic)]
- [FILL: How to check coverage locally]
- [FILL: What to do when coverage drops]

## Mapping to OpenSpec Scenarios

OpenSpec scenarios (Given/When/Then) map directly to test cases:

```
Spec: "GIVEN a user with valid credentials WHEN they log in THEN a token is returned"

Test:
describe('login') {
  it('should return token when credentials are valid') {
    // GIVEN
    const user = createUser({ email: 'test@example.com', password: 'valid' })

    // WHEN
    const result = await authService.login(user.email, user.password)

    // THEN
    expect(result.token).toBeDefined()
  }
}
```
```

---

### 5. Architecture

**Copilot:** `.github/instructions/architecture.instructions.md` (`applyTo: "src/**/*"`)
**Claude:** `.claude/rules/architecture.md` (`paths: ["src/**/*"]`)
**Codex:** Section in `AGENTS.md`
**Cursor:** `.cursor/rules/architecture.mdc` (`globs: "src/**/*"`)
**Windsurf:** Section in `.windsurfrules`

**Content template:**

```markdown
---
description: Architecture patterns, layer boundaries, and system design rules
applyTo: "[FILL: src/**/*]"
---

# Architecture

## System Overview

[FILL: Brief description of the system architecture — monolith, microservices, serverless, etc.]

```
[FILL: ASCII diagram of the high-level architecture]
```

## Layer Boundaries

[FILL: Describe the layers and their dependency rules, e.g.:]

```
Presentation (UI / API Controllers)
    ↓ depends on
Application (Use Cases / Services)
    ↓ depends on
Domain (Entities / Business Rules)
    ↓ depends on
Infrastructure (Database / External Services)
```

**Rules:**
- [FILL: e.g., Domain layer MUST NOT import from infrastructure]
- [FILL: e.g., Presentation layer talks to application layer only, never directly to domain]
- [FILL: e.g., Infrastructure implements interfaces defined in domain]

## Service Communication

[FILL: How services/modules communicate — HTTP, messaging, events, direct calls]
- [FILL: Sync vs async patterns and when to use each]
- [FILL: Error handling across service boundaries]
- [FILL: Retry and circuit breaker patterns]

## State Management

[FILL: How state is managed across the system]
- [FILL: Client-side state strategy]
- [FILL: Server-side session/cache strategy]
- [FILL: Database as source of truth patterns]

## Error Handling

[FILL: System-wide error handling strategy]
- [FILL: Error classification (operational vs programmer errors)]
- [FILL: Error propagation across layers]
- [FILL: Logging and monitoring for errors]

## Adding New Features

When adding a new feature, follow this pattern:

1. [FILL: e.g., Start with the domain model — define entities and business rules]
2. [FILL: e.g., Add the application layer — create use cases / service methods]
3. [FILL: e.g., Implement infrastructure — database migrations, external service calls]
4. [FILL: e.g., Build the presentation layer — API endpoints or UI components]
5. [FILL: e.g., Write tests at each layer]
```

---

## Optional Domain-Specific Instructions

Create additional instruction files for domains that need specialized guidance:

### API Conventions

**File:** `.github/instructions/api-conventions.instructions.md`

```markdown
---
description: REST/GraphQL API design conventions and patterns
applyTo: "[FILL: src/api/**/*, app/api/**/*]"
---

# API Conventions

## URL Patterns
- [FILL: e.g., /api/v1/<resource> using plural nouns]
- [FILL: e.g., Nested resources: /api/v1/workspaces/:id/projects]

## HTTP Methods
- GET: Read (never mutates)
- POST: Create
- PUT/PATCH: Update (specify which one the project uses)
- DELETE: Remove

## Response Format
[FILL: Standard response envelope, pagination format, error format]

## Status Codes
[FILL: Which status codes to use for which situations]

## Versioning
[FILL: API versioning strategy]
```

### Database Conventions

**File:** `.github/instructions/database.instructions.md`

```markdown
---
description: Database schema conventions, migration patterns, and query guidelines
applyTo: "[FILL: relevant source paths for data layer]"
---

# Database Conventions

## Schema Design
- [FILL: Naming conventions for tables and columns]
- [FILL: Primary key strategy (auto-increment, UUID, CUID)]
- [FILL: Timestamp columns (created_at, updated_at)]
- [FILL: Soft delete pattern if used]

## Migrations
- [FILL: Migration tool and naming conventions]
- [FILL: Reversibility requirements]
- [FILL: Data migration patterns]

## Query Patterns
- [FILL: ORM usage rules]
- [FILL: Raw query policy]
- [FILL: N+1 prevention patterns]
```

### Styling Conventions

**File:** `.github/instructions/styling.instructions.md`

```markdown
---
description: CSS, styling, and design system conventions
applyTo: "[FILL: **/*.css, **/*.scss, **/*.tsx, **/*.vue]"
---

# Styling Conventions

[FILL: CSS framework, design tokens, component styling approach, responsive design patterns]
```

---

## Generation Guidelines

1. **Replace all `[FILL: ...]` placeholders** with project-specific content from the Project Profile
2. **Adjust `applyTo` globs** to match the actual project structure
3. **Remove irrelevant sections** — don't include GraphQL if the project uses REST
4. **Add project-specific rules** derived from linter configs and existing patterns
5. **Keep each file focused** — it's better to have 6 specific instruction files than 2 sprawling ones
6. **Be specific and actionable** — "Use Zod schemas at API boundaries" beats "Validate input"
7. **Include examples** from the actual codebase where possible
