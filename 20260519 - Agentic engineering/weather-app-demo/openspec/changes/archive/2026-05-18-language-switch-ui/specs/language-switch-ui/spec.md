## ADDED Requirements

### Requirement: UI language selection
The frontend SHALL provide a control that lets the user select Danish, English, Finnish, Norwegian, or Swedish as the active UI language.

#### Scenario: User switches the active language
- **WHEN** the user selects Finnish from the language control
- **THEN** the visible UI labels and button text change to Finnish

### Requirement: English default
The frontend SHALL display English when no prior language selection exists.

#### Scenario: First load uses English
- **WHEN** a user opens the application without a previously selected language
- **THEN** the UI renders in English

### Requirement: Accessible selector
The language selector SHALL be keyboard navigable and expose the current selection to assistive technologies.

#### Scenario: Keyboard user changes language
- **WHEN** a user navigates to the language selector using only the keyboard
- **THEN** they can change the active language without using a mouse
- **AND** assistive technologies can identify the selected language