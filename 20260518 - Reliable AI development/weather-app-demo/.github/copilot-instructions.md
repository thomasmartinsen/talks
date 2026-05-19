# Copilot instructions

These instructions define how GitHub Copilot and other AI coding assistants should behave when generating code for this solution. Keep changes aligned with the current repository, not a generic template or a different product.

---

## Solution context

This repository is a small **Aspire-based weather demo** used to demonstrate agent-driven development workflows.

The application currently consists of:
- A React frontend that displays a 5-day weather forecast.
- An ASP.NET Core backend that exposes a minimal API endpoint at `/api/weatherforecast`.
- A .NET Aspire AppHost that orchestrates the frontend, backend, and Redis.
- Redis used for output caching of the weather endpoint.

Do not treat this repository as a large clean-architecture product unless the code in the repo is first changed to support that.

---

## Current project layout

All active projects are under `src/`:

- `src/frontend/` - React 19 + TypeScript + Vite frontend.
- `src/Weather.Server/` - ASP.NET Core 10 minimal API backend.
- `src/Weather.AppHost/` - .NET Aspire AppHost orchestration project.
- `src/add-weather-demo.slnx` - solution file.

Important:
- The backend is currently a **minimal API**, not a FastEndpoints application.
- There are no `Application`, `Domain`, `Infrastructure`, `API`, `ServiceDefaults`, or `WebApp` projects in this repo.
- Shared Aspire defaults currently live in `src/Weather.Server/Extensions.cs`.

---

## Tech stack

### Frontend
- React 19
- TypeScript 5
- Vite 7
- ESLint 9
- Plain CSS via `src/frontend/src/App.css` and `src/frontend/src/index.css`

### Backend
- .NET 10
- ASP.NET Core minimal APIs
- OpenAPI in development
- Redis output caching via Aspire integration
- OpenTelemetry instrumentation

### Orchestration
- .NET Aspire 13.1
- Redis resource orchestration
- Vite app orchestration from AppHost

---

## Architectural rules

### General
- Prefer small, focused changes that match the current demo structure.
- Fix the problem at the actual implementation point instead of introducing new abstraction layers by default.
- Do not add large architectural patterns unless the user explicitly asks for them.
- Keep frontend and backend communication over HTTP using the existing `/api/...` route pattern.

### Frontend and backend integration
- The frontend should call the backend using relative URLs such as `/api/weatherforecast`.
- Prefer keeping the frontend same-origin with the backend unless the repo is explicitly restructured.
- If the API contract changes, update both the backend response shape and the frontend TypeScript interface together.

### Aspire orchestration
- Preserve the AppHost as the place that wires together Redis, the server project, and the Vite frontend.
- Keep service names and references consistent when modifying AppHost resource wiring.
- Do not remove health checks, service defaults, or Redis wiring unless the change requires it.

---

## Code style

### General
- Prefer readability over cleverness.
- Use explicit, descriptive names.
- Keep methods and components focused.
- Avoid unnecessary indirection in a demo-sized codebase.
- Follow the existing formatting style in each file.

### Backend (.NET)
- Nullable reference types must remain enabled.
- Use async I/O when adding new I/O-bound work.
- Prefer ASP.NET Core built-in features before introducing new dependencies.
- Keep API logic thin and clear.
- For this repo, simple endpoint logic can stay in `Program.cs` until there is a clear need to extract it.
- Reuse the existing service defaults and telemetry patterns in `Extensions.cs` when adding backend capabilities.
- Preserve the existing development-only behavior for OpenAPI and health endpoints unless there is a clear reason to change it.

### Frontend (TypeScript/React)
- Components use PascalCase.
- Functions, variables, and hooks use camelCase.
- Keep state local unless there is a demonstrated need to share it.
- Prefer straightforward React patterns that fit the current app.
- Do not introduce routing, global state libraries, UI frameworks, or data libraries unless the user asks for them.
- Keep accessibility attributes intact for interactive controls.

### CSS and UI
- Preserve the current visual style unless the task is explicitly a redesign.
- Prefer extending the existing CSS files over introducing a new styling system.
- Keep responsive behavior and accessible labels intact when updating UI elements.

---

## Dependencies

- Prefer existing platform and framework capabilities first.
- Ask before adding major new packages or frameworks.
- Do not add Tailwind, shadcn/ui, React Router, TanStack Query, Zod, FastEndpoints, AutoMapper, MediatR, or database packages unless explicitly requested.

---

## API conventions

- Keep API routes under `/api`.
- Return shapes that are simple and stable for the frontend to consume.
- When changing the weather forecast contract, update the corresponding frontend interface and rendering logic.
- Preserve output caching behavior when modifying the weather endpoint unless the task requires different caching semantics.

---

## Observability and runtime behavior

- Keep OpenTelemetry instrumentation wired through the existing service defaults.
- Preserve health endpoints and default Aspire service behavior where possible.
- Avoid changes that break AppHost startup orchestration or published frontend asset serving.

---

## Testing and validation

- For frontend changes, validate with the frontend build or lint command when relevant.
- For backend changes, validate with a focused .NET build or run check when relevant.
- When changing cross-project integration, prefer validating the affected slice rather than only reviewing diffs.

Useful commands:
- `npm run build` in `src/frontend`
- `npm run lint` in `src/frontend`
- `dotnet build src/add-weather-demo.slnx`

---

## Security and configuration

- Never commit secrets.
- Respect existing user-secrets and environment-based configuration patterns.
- Do not hardcode connection strings, keys, or external service credentials.

---

## When in doubt

- Follow the code that exists in this repo rather than scaffolding patterns from unrelated templates.
- Ask before introducing new architecture, new infrastructure, or major dependencies.
- Keep the repo working as an Aspire weather demo unless the user requests a broader change.
