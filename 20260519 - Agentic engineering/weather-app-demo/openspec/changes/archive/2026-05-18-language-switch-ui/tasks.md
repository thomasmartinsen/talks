## 1. Localization State and Text

- [x] 1.1 Define the supported language codes and a typed translation map for the app shell, weather section, footer, and accessibility text.
- [x] 1.2 Add language state to the main frontend component with English as the default selection.

## 2. UI Integration

- [x] 2.1 Add an accessible language selector in the header that lets the user switch between Danish, English, Finnish, Norwegian, and Swedish.
- [x] 2.2 Replace hardcoded English labels and button text with language-aware lookups.
- [x] 2.3 Verify the temperature toggle, weather cards, and refresh behavior still work after switching languages.

## 3. Validation

- [x] 3.1 Run `npm run lint` in `src/frontend` and fix any issues introduced by the language switch changes.
- [x] 3.2 Run `npm run build` in `src/frontend` to confirm the localized UI compiles cleanly.