## ADDED Requirements

### Requirement: Default theme is light mode
The frontend SHALL render in light mode on initial page load unless the user changes the theme through the app's theme toggle during the current session.

#### Scenario: Initial load uses light mode
- **WHEN** a user opens the frontend for the first time in a browser tab
- **THEN** the page renders with the light theme palette
- **AND** the dark theme is not applied by default

### Requirement: User can toggle between light and dark themes
The frontend SHALL provide a theme toggle that lets the user switch between light mode and dark mode without reloading the page.

#### Scenario: User enables dark mode
- **WHEN** the user activates the dark mode option in the theme toggle
- **THEN** the frontend updates to the dark theme in the current page session

#### Scenario: User returns to light mode
- **WHEN** the user activates the light mode option in the theme toggle after dark mode is active
- **THEN** the frontend updates back to the light theme in the current page session

### Requirement: Theme toggle appears in the top-right header area
The frontend SHALL place the theme toggle in the top-right area of the page header and expose its current state through accessible interactive controls.

#### Scenario: Theme control is visible in the header
- **WHEN** the page header is rendered
- **THEN** the theme toggle appears in the header's top-right area
- **AND** the current selection is exposed through accessible labels or pressed state