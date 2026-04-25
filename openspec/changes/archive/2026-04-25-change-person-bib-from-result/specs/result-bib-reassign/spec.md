## ADDED Requirements

### Requirement: Change-bib button visibility
The dialog SHALL display a "Change bib" button adjacent to the person-info label, and the button SHALL be visible if and only if all of the following conditions hold simultaneously: (a) the current result has a linked participant (`result.person` is not None), and (b) the bib number entered in the bib field does not match any participant in the race.

#### Scenario: Button appears when participant linked and bib not found
- **WHEN** a result with a linked participant is open in the edit dialog
- **AND** the user enters a bib number that belongs to no participant
- **THEN** the "Change bib" button SHALL become visible next to the "not found" label

#### Scenario: Button hidden when bib matches a participant
- **WHEN** the user enters a bib number that belongs to an existing participant
- **THEN** the "Change bib" button SHALL NOT be visible

#### Scenario: Button hidden when no participant linked
- **WHEN** the current result has no linked participant
- **AND** the user enters a bib number that belongs to no participant
- **THEN** the "Change bib" button SHALL NOT be visible

#### Scenario: Button hidden when bib field is zero
- **WHEN** the bib field value is 0
- **THEN** the "Change bib" button SHALL NOT be visible

### Requirement: Change-bib button tab order
The "Change bib" button SHALL be the immediate next focusable widget after the bib number spin box in the dialog's tab order.

#### Scenario: Tab from bib field reaches button when visible
- **WHEN** the "Change bib" button is visible
- **AND** the user presses Tab while focus is on the bib number spin box
- **THEN** focus SHALL move to the "Change bib" button

#### Scenario: Tab from bib field skips hidden button
- **WHEN** the "Change bib" button is not visible
- **AND** the user presses Tab while focus is on the bib number spin box
- **THEN** focus SHALL move to the next visible field after the button

### Requirement: Change-bib button action
When the "Change bib" button is activated, the dialog SHALL record the intent to reassign the linked participant's bib to the entered value. This intent SHALL be applied to the model when the user confirms the dialog with OK.

#### Scenario: Button click stores pending bib and refreshes label
- **WHEN** the user clicks the "Change bib" button (or activates it via keyboard)
- **THEN** the dialog SHALL store the entered bib as a pending reassignment for the linked participant
- **AND** the person-info label SHALL update to display the linked participant's info (as though the participant was found with that bib)
- **AND** the "Change bib" button SHALL become hidden

#### Scenario: Pending reassignment applied on OK
- **WHEN** the user has activated the "Change bib" button in the current dialog session
- **AND** the user confirms the dialog with OK
- **THEN** the linked participant's bib SHALL be updated to the pending value in the race model
- **AND** the result SHALL remain linked to the same participant

#### Scenario: Pending reassignment discarded on Cancel
- **WHEN** the user has activated the "Change bib" button in the current dialog session
- **AND** the user cancels the dialog
- **THEN** the linked participant's bib SHALL remain unchanged
