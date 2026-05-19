## Why

The UI currently has a single language, which limits accessibility and makes the demo less useful for multilingual users. Adding a language switch gives the app a clearer internationalization story while keeping English as the default experience.

## What Changes

- Add a language selector in the frontend UI.
- Support switching the displayed UI language between Danish, English, Finnish, Norwegian, and Swedish.
- Keep English as the default language on first load.
- Preserve the existing app flow and weather functionality while only changing UI text localization.

## Capabilities

### New Capabilities
- `language-switch-ui`: UI language selection and localized interface text for the supported languages.

### Modified Capabilities
- None.

## Impact

- Affects `src/frontend` only.
- No backend API contract changes are required.
- No AppHost or Redis changes are required.
- Introduces frontend localization data and language selection state in the React UI.