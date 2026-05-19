## Why

The frontend currently derives its theme from CSS `prefers-color-scheme`, which means users can land in a dark presentation without choosing it. This change adds an explicit theme control so the app always starts in light mode and lets users switch to dark mode when they want it.

## What Changes

- Add a theme mode toggle to the top-right area of the frontend header actions.
- Make light mode the default visual theme on initial load.
- Introduce an explicit dark theme that restyles the existing weather experience without changing forecast functionality.
- Remove reliance on OS color-scheme preference as the primary source of theme selection.

## Capabilities

### New Capabilities
- `theme-mode-toggle`: Allows users to switch between light and dark themes from a top-right toggle while keeping light mode as the default state.

### Modified Capabilities

None.

## Impact

Affected code is limited to the React frontend, primarily the main app component and its CSS theme tokens. No backend APIs, Aspire orchestration, or external dependencies are expected to change.