## Why

When editing a result, if the user types a bib number that belongs to no registered participant, the dialog silently does nothing (or leaves the result in an inconsistent state). The only feedback is a "not found" label — but there is no action available. A common legitimate use case is reassigning the current participant's own bib to a new number directly from the result card.

## What Changes

- Add a **"Change bib"** button next to the "not found" label in the result edit dialog.
- The button is visible only when: a participant is already linked to the current result AND the entered bib does not match any existing participant.
- Clicking the button updates the linked participant's bib to the newly entered value.
- The button is placed in tab order immediately after the bib number spin box, so it can be reached and activated with Tab + Space/Enter without using the mouse.

## Capabilities

### New Capabilities

- `result-bib-reassign`: In-dialog action to reassign the current participant's bib to a new number entered in the bib field, when no participant with that number exists.

### Modified Capabilities

<!-- none -->

## Impact

- `sportorg/gui/dialogs/result_edit.py` — `ResultEditDialog.init_ui()`, `show_person_info()`
- `sportorg/models/memory.py` — `Person.bib` field (written, not changed structurally)
- No new dependencies; no API or serialization changes.
