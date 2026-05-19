## 1. Theme State And Header Control

- [x] 1.1 Add frontend theme state with light mode as the default on initial render.
- [x] 1.2 Add an accessible light/dark theme toggle in the top-right header area.
- [x] 1.3 Wire the toggle so theme changes update the page without reloading.

## 2. Theme Styling

- [x] 2.1 Refactor theme tokens so light and dark palettes are controlled by the app instead of `prefers-color-scheme`.
- [x] 2.2 Update header, card, toggle, and supporting UI styles to render correctly in both themes.
- [x] 2.3 Verify responsive layout keeps the new header control usable on smaller screens.

## 3. Validation

- [x] 3.1 Run the frontend build to confirm the toggle changes compile cleanly.
- [x] 3.2 Run the frontend lint command and fix any issues introduced by the change.
- [x] 3.3 Manually verify light mode is the default and dark mode can be toggled from the top-right header area.