## 1. Icons

- [x] 1.1 Create `img/icon/live-on.svg` (active/coloured icon for enabled state; `img/icon/live.svg` may be used for the disabled state)

## 2. Toggle Action

- [x] 2.1 Add `LiveToggleAction` to `sportorg/gui/menu/actions.py` — reads `race().get_setting("live_enabled", False)`, inverts it, writes back via `race().set_setting()`, then calls `self.app.refresh()`

## 3. Toolbar Button

- [x] 3.1 In `sportorg/gui/toolbar.py`, add a 5-element tuple for the Live button: `(icon_path, title, action_name, property_name, context_menu_flag)` — or use a sentinel to signal `QToolButton` creation
- [x] 3.2 In `sportorg/gui/main_window.py` `_setup_toolbar()`, detect the Live entry and create a `QToolButton` using `addWidget()` instead of `addAction()`:
  - Set `Qt.CustomContextMenu` policy
  - Connect `clicked` to `LiveToggleAction`
  - Connect `customContextMenuRequested` to `_show_live_context_menu()`
  - Store the button in `self.toolbar_property["live"]`

## 4. Context Menu

- [x] 4.1 Add `_show_live_context_menu(pos: QPoint)` method to `MainWindow`:
  - Build a `QMenu` dynamically each call
  - Item 1: "Disable Live" / "Enable Live" based on `race().get_setting("live_enabled", False)` — connects to `LiveToggleAction`
  - Item 2: "Send Selected" with `QAction.setShortcut(QKeySequence("Ctrl+K"))` — connects to `OnlineSendAction`
  - Item 3: "Settings" — connects to `LiveSettingsAction` (existing action that opens `LiveDialog`)
  - Execute the menu at `self.toolbar_property["live"].mapToGlobal(pos)`

## 5. State Polling

- [x] 5.1 Add `live_status = False` class attribute and `live_icon = {True: "live-on.svg", False: "live.svg"}` dict to `MainWindow` (alongside existing `teamwork_status` / `teamwork_icon`)
- [x] 5.2 In `MainWindow.interval()`, add a block that compares `LiveClient.is_enabled()` to `self.live_status`; if changed, update `self.toolbar_property["live"].setIcon(...)` and store new status

## 6. Translations

- [x] 6.1 Wrap new UI strings in `translate()`: "Disable Live", "Enable Live", "Send Selected", "Settings", "Live" (button tooltip)
- [x] 6.2 Run `uv run poe generate-mo` to compile updated `.po` files

## 7. Verification

- [x] 7.1 Run the application and confirm the Live button appears in the toolbar
- [x] 7.2 Verify left-click toggles `live_enabled` and the icon updates within one polling cycle
- [x] 7.3 Verify right-click shows context menu with correct label, Ctrl+K shortcut visible on "Send Selected", and Settings opens `LiveDialog`

- [x] 7.4 Run `uv run poe test` and confirm no regressions
