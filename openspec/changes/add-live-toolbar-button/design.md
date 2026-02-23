## Context

The toolbar currently uses `QAction` objects created in `_setup_toolbar()` (main_window.py:359). Each action supports a single `triggered` signal (left-click). State-aware buttons (sportident, teamwork) store their `QAction` in `self.toolbar_property[name]` and update their icon from `interval()` (main_window.py:175).

Live mode state is tracked in `race().get_setting("live_enabled", False)` and validated by `LiveClient.is_enabled()`, which additionally requires at least one URL configured. Sending is handled by `OnlineSendAction` (Ctrl+K) in `actions.py:844`. The Live Settings dialog exists at `gui/dialogs/live_dialog.py`.

## Goals / Non-Goals

**Goals:**
- Add a Live toolbar button that visually reflects enabled/disabled state
- Left-click toggles `live_enabled` race setting
- Right-click shows a context menu with: Enable/Disable, Send Selected (Ctrl+K), Settings
- Context menu items display their keyboard shortcuts natively (via `QAction.setShortcut()`)
- Icon updates in real time via the existing `interval()` polling loop

**Non-Goals:**
- No changes to Live module logic or Orgeo API
- No changes to the Live Settings dialog internals
- No changes to menu shortcuts or how `OnlineSendAction` works
- No separate toolbar button for Teamwork (out of scope)

## Decisions

### 1. QToolButton instead of QAction for the Live toolbar entry

`QAction` only fires `triggered` on left-click; it does not distinguish left from right. `QToolButton` supports `clicked` (left-click) and `customContextMenuRequested` (right-click via `Qt.CustomContextMenu` policy). This is the same approach PySide6 requires for split click behavior.

`_setup_toolbar()` must be extended to handle a new tuple variant with 5 elements `(icon, title, action, property_name, context_menu_builder)` that inserts a `QToolButton` via `self.toolbar.addWidget()` instead of `self.toolbar.addAction()`.

Alternative: `QToolButton.setMenu()` with `QToolButton.MenuButtonPopup` mode renders a visible arrow and shows the menu on left-click of the arrow, not on right-click. Rejected — the spec requires right-click for the menu.

### 2. Icon-based state indicator (two SVG files)

Follow the same pattern as sportident (`sportident.png` / `sportident-on.png`) and teamwork (`network-off.svg` / `network.svg`): two icon files selected by a `live_icon` dict in `MainWindow`, updated in `interval()`.

Icons: `live.svg` already exists in `img/icon/` and may be used as the disabled state. Only `live-on.svg` needs to be created for the enabled state. Both are referenced via `config.icon_dir()`.

Alternative: single SVG with color overlay at runtime. Rejected — adds complexity without benefit; the existing pattern is simpler.

### 3. LiveToggleAction as a named Action

Add `LiveToggleAction` to `actions.py` using the existing `ActionFactory` metaclass. It reads `live_enabled`, inverts the value, writes it back via `race().set_setting()`, then triggers a UI refresh so the icon updates within the next `interval()` tick.

The same action is reused for both the left-click handler of the toolbar button and the Enable/Disable item in the context menu, keeping logic in one place.

### 4. Context menu built at show-time (dynamic)

The context menu for the right-click is constructed in a helper method each time it is shown, so the Enable/Disable label reflects the current state ("Disable Live" when enabled, "Enable Live" when disabled). `QAction.setShortcut()` is called on the Send Selected action to display `Ctrl+K` natively in the menu.

### 5. State polling in interval()

Follows the identical pattern already used for sportident and teamwork: compare `LiveClient.is_enabled()` to a cached `live_status` field; update the button icon if the state changed.

## Risks / Trade-offs

- **`QToolButton` vs toolbar layout**: `addWidget()` inserts the button directly into the toolbar QToolBar; it won't have a separator automatically. Acceptable — consistent with how PySide6 toolbars work.
- **`live_enabled` toggle without URLs**: `LiveClient.is_enabled()` returns `False` when no URLs are configured even if `live_enabled=True`. The icon will remain "off" in that case — correct UX (user must configure URLs first).
- **Icon update latency**: Icon refreshes on the next `interval()` tick (~500 ms). This is acceptable and consistent with sportident/teamwork behavior.
- **`interval()` access to QToolButton**: `toolbar_property["live"]` stores the `QToolButton`; calling `.setIcon()` on it works the same as on `QAction`.
