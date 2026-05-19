---
applyTo: 'src/server/**/*.{cs}'
description: 'Rules for .NET Aspire backend services'
---

# Backend guidelines

## Context loading
- `/docs/architecture.md`
- Backend ADRs
- `/instructions/security.instructions.md`

## Deterministic requirements
- .NET 10 with Aspire
- REST APIs for web frontend
- MCP server for chat frontend
- No frontend concerns in backend
- Authentication via Entra ID bearer tokens

## Structured output
- API contracts defined
- Unit tests implemented
- Integration HTTP tests present
- Observability configured
