## Context

The current frontend theme is driven by CSS variables with dark values defined in `:root` and light values applied through `@media (prefers-color-scheme: light)`. That approach makes the initial theme depend on the user's OS preference instead of the app's own behavior. The requested change is small and frontend-only, but it still benefits from a short design because it changes the app's presentation model and header layout.

## Goals / Non-Goals

**Goals:**
- Make light mode the default theme every time the app loads.
- Add a theme toggle in the top-right area of the UI.
- Reuse the existing CSS variable approach so the forecast experience keeps the same structure and interactions.
- Keep the change local to the frontend without modifying backend contracts.

**Non-Goals:**
- Persist the selected theme across browser sessions.
- Follow `prefers-color-scheme` after the app has loaded.
- Redesign the weather cards, forecast data model, or refresh behavior.

## Decisions

### Decision: Use explicit theme state in the React app
The app will track theme mode with local component state instead of relying on media-query selection. This keeps the default deterministic and allows the toggle to update the UI immediately.

Alternative considered: keeping `prefers-color-scheme` and adding only a visual switch. Rejected because the app would still default to OS-selected dark mode for some users, which conflicts with the requested behavior.

### Decision: Apply theme through a container attribute or class that switches CSS variables
The existing styling already depends on CSS custom properties, so the smallest safe change is to define light and dark token sets explicitly and switch them by theme on the app container. This preserves the current component structure and avoids touching each weather card style individually.

Alternative considered: duplicating component styles for each theme. Rejected because it increases CSS surface area and makes future style changes harder to maintain.

### Decision: Place the control in the header action area at the top-right
The app already uses an action cluster near the weather section header for the temperature unit toggle and refresh button, but the request is specifically for a top-right theme toggle. The header layout should be updated so the theme control sits in the global header's top-right area without affecting forecast interactions.

Alternative considered: placing the theme toggle next to the temperature toggle. Rejected because theme selection applies to the full page, not just the forecast card, and the requested location is the top-right corner.

## Risks / Trade-offs

- Header layout shift on small screens -> Keep the toggle compact and preserve responsive wrapping behavior.
- Theme token gaps could leave some controls with mismatched contrast -> Audit the existing variables and move any remaining hard-coded colors behind theme-aware tokens.
- No persistence may surprise users who expect the app to remember their choice -> Document that session persistence is out of scope for this change and keep the default behavior explicit.