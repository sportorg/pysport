## 1. Dialog UI

- [x] 1.1 In `init_ui()`, replace the single `label_person_info` form row with a container `QWidget` holding `label_person_info` and a new `QPushButton` ("Change bib") in a horizontal layout
- [x] 1.2 Set `button_change_bib` initially hidden (`setVisible(False)`)
- [x] 1.3 Call `QWidget.setTabOrder(self.item_bib, self.button_change_bib)` after all widgets are created to fix tab order

## 2. Button visibility logic

- [x] 2.1 In `show_person_info()`, after the "not found" branch, show `button_change_bib` only when `result.person` is not None and `bib != 0`
- [x] 2.2 In all other branches of `show_person_info()` (bib==0, person found), hide `button_change_bib`

## 3. Pending bib state

- [x] 3.1 Add `self._pending_bib_for_person: int = 0` to `__init__`
- [x] 3.2 Connect `button_change_bib.clicked` to a slot that sets `self._pending_bib_for_person = self.item_bib.value()`, hides the button, and calls `show_person_info()` to refresh the label

## 4. Apply logic

- [x] 4.1 In `apply_changes_impl()`, before the existing bib-assignment block, if `self._pending_bib_for_person` is set apply `result.person.bib = self._pending_bib_for_person` and update `cur_bib` accordingly so the rest of the method treats the bib as unchanged
