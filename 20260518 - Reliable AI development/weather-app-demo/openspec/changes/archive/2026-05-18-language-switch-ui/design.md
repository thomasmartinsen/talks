## Context

The current frontend in `src/frontend` is a single-language React app with hardcoded English labels in `src/frontend/src/App.tsx`. The UI already has local state for weather loading, error handling, and the temperature unit toggle, so the new language switch should fit that same lightweight client-side pattern.

The request only affects the frontend experience. The weather data still comes from `/api/weatherforecast`, and the backend/AppHost setup does not need to change.

## Goals / Non-Goals

**Goals:**
- Let users switch the UI between Danish, English, Finnish, Norwegian, and Swedish.
- Keep English as the default on first load.
- Keep the implementation small and dependency-free.
- Preserve the existing weather forecast flow and temperature toggle.

**Non-Goals:**
- Translating backend weather summaries or changing the API contract.
- Adding a general-purpose i18n framework.
- Changing AppHost orchestration, Redis, or server-side behavior.
- Persisting the language choice across browser refreshes in this change.

## Decisions

- Use a client-side translation map in the frontend rather than adding an external localization package. This keeps the demo simple and avoids new dependencies for a small set of static strings.
- Store the active language in React state in the main app component. This is enough to update the visible UI immediately and keeps the change localized.
- Translate only static UI text, labels, and button chrome. Leave weather data and numeric values untouched because they come from the backend and are not part of the UI shell.
- Render the selector as an accessible control that matches the existing UI style. A compact dropdown or segmented control fits the current header layout better than adding a new navigation surface.

## Risks / Trade-offs

- Translation drift between keys and UI text → Keep all supported strings in one typed dictionary and reuse the same keys across the app.
- Partial coverage of visible text → Review the main app shell, weather card labels, footer labels, and accessibility text together before shipping.
- Language choice is not durable across refreshes → Accept this for the first version to avoid extra storage logic; revisit persistence only if it is requested.

## Migration Plan

1. Add the supported language dictionary and language state in `src/frontend/src/App.tsx`.
2. Replace hardcoded English strings with dictionary lookups.
3. Add the language selector near the existing header actions.
4. Verify the UI still loads the forecast and the temperature toggle still works.
5. Validate the frontend build and lint output.

## Open Questions

- Should the selected language persist across browser refreshes in a follow-up change?
- Should any footer or external link labels be localized beyond the main app shell?