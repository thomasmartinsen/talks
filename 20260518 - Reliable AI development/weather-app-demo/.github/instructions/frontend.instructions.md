---
applyTo: 'src/frontend/**/*.{ts,tsx}'
description: 'Rules for React/TypeScript frontend development'
---

# Frontend guidelines

## Context loading
- `/docs/architecture.md`
- `/instructions/security.instructions.md`
- Frontend ADRs

## Deterministic requirements
- React + TypeScript only
- No business logic in UI components
- API access only via typed clients
- Authentication enforced via Entra ID
- No direct AI calls from frontend

## Structured output
- Typed components
- API client definitions
- UI test coverage
- Security review completed
