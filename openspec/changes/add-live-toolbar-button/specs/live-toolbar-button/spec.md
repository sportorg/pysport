## ADDED Requirements

### Requirement: Live toolbar button is present
The toolbar SHALL contain a Live button displayed as a `QToolButton` with an icon reflecting the current Live mode state.

#### Scenario: Button visible when toolbar is enabled
- **WHEN** the application launches with `window_show_toolbar` setting enabled
- **THEN** a Live button is visible in the toolbar

#### Scenario: Button absent when toolbar is hidden
- **WHEN** the application launches with `window_show_toolbar` setting disabled
- **THEN** no Live button is rendered

### Requirement: Live button icon reflects current state
The Live button icon SHALL visually distinguish between enabled and disabled Live mode states. The icon SHALL update within one polling cycle whenever the state changes.

#### Scenario: Icon shows enabled state
- **WHEN** `LiveClient.is_enabled()` returns `True`
- **THEN** the Live button displays the "live-on" icon

#### Scenario: Icon shows disabled state
- **WHEN** `LiveClient.is_enabled()` returns `False`
- **THEN** the Live button displays the "live-off" icon

#### Scenario: Icon updates when state changes externally
- **WHEN** the user changes Live settings via the Settings dialog
- **THEN** the Live button icon updates to reflect the new state within one polling interval

### Requirement: Left-click toggles Live mode
A left-click on the Live button SHALL toggle the `live_enabled` race setting between `True` and `False`.

#### Scenario: Left-click enables Live when disabled
- **WHEN** `live_enabled` is `False` and the user left-clicks the Live button
- **THEN** `live_enabled` is set to `True`

#### Scenario: Left-click disables Live when enabled
- **WHEN** `live_enabled` is `True` and the user left-clicks the Live button
- **THEN** `live_enabled` is set to `False`

### Requirement: Right-click shows context menu
A right-click on the Live button SHALL show a context menu with three items: Enable/Disable, Send Selected, and Settings.

#### Scenario: Context menu appears on right-click
- **WHEN** the user right-clicks the Live button
- **THEN** a context menu appears with items: Enable/Disable Live, Send Selected, Settings

#### Scenario: Enable/Disable label reflects current state
- **WHEN** `live_enabled` is `True` and the context menu is shown
- **THEN** the first menu item reads "Disable Live"

#### Scenario: Enable/Disable label when disabled
- **WHEN** `live_enabled` is `False` and the context menu is shown
- **THEN** the first menu item reads "Enable Live"

### Requirement: Context menu Send Selected shows keyboard shortcut
The "Send Selected" item in the context menu SHALL display its keyboard shortcut (Ctrl+K) next to the label.

#### Scenario: Shortcut displayed in context menu
- **WHEN** the context menu is open
- **THEN** the "Send Selected" item shows "Ctrl+K" as its shortcut

#### Scenario: Send Selected executes OnlineSendAction
- **WHEN** the user clicks "Send Selected" in the context menu
- **THEN** `OnlineSendAction` executes with the currently selected rows

### Requirement: Context menu Settings opens Live dialog
The "Settings" item in the context menu SHALL open the Live Settings dialog.

#### Scenario: Settings item opens dialog
- **WHEN** the user clicks "Settings" in the context menu
- **THEN** the Live Settings dialog opens
