## Why

Live (Online) mode management is only accessible through the Service → Online menu, with no visual indication of the current state. Users need quick toolbar access to toggle Live mode and send results without navigating menus.

## What Changes

- Add a Live toolbar button with two visual states (enabled / disabled icon variants)
- Left-click toggles Live mode (enable/disable)
- Right-click shows a context menu with:
  - Enable / Disable (reflects current state)
  - Send Selected (with keyboard shortcut Ctrl+K)
  - Settings (opens Live Settings dialog)
- The toolbar icon reflects the current Live state in real time
- Context menu displays keyboard shortcuts where assigned

## Capabilities

### New Capabilities
- `live-toolbar-button`: Toolbar button for controlling Live mode — left-click toggle, right-click context menu, icon-based state indicator

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- `sportorg/gui/toolbar.py` — add Live button entry (with property name `live` for state tracking)
- `sportorg/gui/main_window.py` — use a custom `QToolButton` instead of a plain `QAction` (required to separate left/right click and attach a context menu); update icon on Live state change
- `sportorg/modules/live/live.py` — use existing `LiveClient.is_enabled()` to read current state; existing `OnlineSendAction` (Ctrl+K) is reused
- `sportorg/gui/menu/actions.py` — add `LiveToggleAction` to flip `live_enabled` in race settings
- New SVG icon `live-on.svg` in `img/icon/`; existing `img/icon/live.svg` may be used for the disabled state
- Translation strings for new menu items via `sportorg/language.py`
