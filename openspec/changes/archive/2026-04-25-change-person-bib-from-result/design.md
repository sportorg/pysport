## Context

`ResultEditDialog` (`sportorg/gui/dialogs/result_edit.py`) shows an inline label `label_person_info` that displays participant info when a bib is typed. When no participant is found it shows "not found". Currently there is no action the user can take from this state — the only options are to retype a valid bib or cancel.

A common workflow is: result comes in, operator wants to correct a participant's bib number directly from the result card (e.g., bib was misread during registration). Today this requires opening the participant dialog separately.

## Goals / Non-Goals

**Goals:**
- Add a "Change bib" button that appears only when: (1) a participant is already linked to the result AND (2) the entered bib number is not found in the race.
- Button press sets `result.person.bib` to the entered value, then refreshes the label to show updated participant info.
- Tab order: bib spin box → change-bib button → next field (days or start).

**Non-Goals:**
- Handling the case where no participant is currently linked (button stays hidden).
- Validating bib uniqueness across all participants — the caller is responsible; duplicate bibs are already a user error elsewhere in the app.
- Any change to the `apply_changes_impl` logic for the "not found" path.

## Decisions

**Decision 1 — Button visibility vs. enabled state**

Options:
- (A) Always show the button, disable it when conditions not met.
- (B) Show/hide the button dynamically.

Choice: **(B) show/hide**. The button is only meaningful in one narrow state; a perpetually-disabled button adds visual noise and is confusing when a participant *is* found.

Implementation: `show_person_info()` already fires on every bib change. Extend it to call `button_change_bib.setVisible(...)` based on conditions.

**Decision 2 — Where to store the button in the layout**

The label `label_person_info` is in its own form row. The button will be placed on the *same row* as the label by replacing the label-only row with a small `QWidget` container that holds both `label_person_info` and `button_change_bib` side-by-side (horizontal layout). This keeps the form compact and the button visually attached to "not found".

**Decision 3 — Tab order**

Qt's default tab order follows widget creation order. To guarantee the button comes right after `item_bib`, explicitly call `QWidget.setTabOrder(self.item_bib, self.button_change_bib)` in `init_ui()` after all widgets are created.

**Decision 4 — Applying the bib change immediately vs. on OK**

Options:
- (A) Button immediately mutates `result.person.bib` in the model.
- (B) Button only updates dialog state; mutation happens on OK.

Choice: **(B) dialog-local state**. Mutating the model before OK is inconsistent with how every other field in the dialog works. Store the "pending bib override" in the dialog and apply it in `apply_changes_impl`.

A simple approach: on button click, store `self._pending_bib_for_person = new_bib` and call `show_person_info()` to refresh the label to show the participant info (as if found). On `apply_changes_impl`, if `_pending_bib_for_person` is set, update `result.person.bib` before the rest of the bib-assignment logic.

## Risks / Trade-offs

- [Duplicate bib] If the new bib is already assigned to another participant, after the change two participants share a bib. → No mitigation in this change; bib uniqueness is the operator's responsibility (same as in the participant edit dialog).
- [Invisible button in tab loop] If `button_change_bib` is hidden, Qt skips it in tab traversal automatically — no extra handling needed.

## Open Questions

- None.
