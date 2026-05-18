# Sportorg Plugin Protocol (SPP)

## Overview

SportOrg plugins are external processes started by SportOrg and controlled over
standard input/output with JSON-RPC 2.0 messages.

- Transport: `stdio`
- Encoding: UTF-8
- Message format: JSON-RPC 2.0
- Framing: one JSON message per line (`\n`)
- Plugin logs: `stderr` only
- Protocol version: `1`

The host writes JSON-RPC requests and notifications to the plugin process
`stdin`. The plugin writes JSON-RPC responses, requests, and notifications to
`stdout`. A plugin must not write human-readable logs to `stdout`, because every
line on `stdout` is parsed as a protocol message.

## Message Rules

Every request or notification is a single JSON object with the standard
JSON-RPC fields:

```json
{"jsonrpc":"2.0","id":1,"method":"plugin.initialize","params":{}}
```

Requests include `id` and require a response. Notifications omit `id` and must
not be answered.

Errors use standard JSON-RPC error objects:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {"field": "settings.language"}
  }
}
```

Recommended error codes:

- `-32700 Parse error`
- `-32600 Invalid request`
- `-32601 Method not found`
- `-32602 Invalid params`
- `-32603 Internal error`
- `-32000 Plugin error`
- `-32001 Operation is not supported`
- `-32002 Operation was rejected by the user or plugin policy`

## Lifecycle

### `plugin.initialize`

Sent by SportOrg immediately after the plugin process starts.

The request includes host information, current language, current race state, and
the plugin settings previously saved by SportOrg.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "plugin.initialize",
  "params": {
    "protocol_version": 1,
    "host": {
      "name": "SportOrg",
      "version": "1.6.0"
    },
    "settings": {
      "language": "en_US",
      "timezone": "Europe/Moscow",
      "plugin": {
        "api_token": "",
        "endpoint_url": "https://example.org/api"
      },
      "host": {
        "time_accuracy": 0,
        "result_processing_mode": "time"
      }
    },
    "race": {
      "object": "Race",
      "id": "37a31618-47d0-4120-a11c-2d113df839a0",
      "data": {},
      "settings": {},
      "organizations": [],
      "courses": [],
      "groups": [],
      "results": [],
      "persons": []
    }
  }
}
```

Fields:

- `protocol_version`: SportOrg plugin protocol version.
- `host`: SportOrg application metadata.
- `settings.language`: current UI language as a locale string.
- `settings.timezone`: local timezone name if known.
- `settings.plugin`: plugin-specific settings loaded from SportOrg storage.
- `settings.host`: selected SportOrg race/application settings useful to the
  plugin.
- `race`: current full race snapshot in the same shape as `Race.to_dict()`.

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "plugin": {
      "id": "example.live_export",
      "name": "Example Live Export",
      "version": "1.0.0"
    },
    "capabilities": {
      "menu": true,
      "race_updates": true,
      "result_updates": true,
      "person_updates": true,
      "group_updates": true,
      "organization_updates": true,
      "course_updates": true,
      "settings": true
    },
    "settings": {
      "api_token": "",
      "endpoint_url": "https://example.org/api",
      "auto_publish": false
    }
  }
}
```

The plugin may return `settings`. SportOrg stores them as plugin-specific
settings together with SportOrg settings and sends the stored value back in the
next `plugin.initialize` call. Returned settings replace the previous
plugin-specific settings for this plugin.

### `plugin.shutdown`

Sent before SportOrg stops the plugin process.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "plugin.shutdown",
  "params": {
    "reason": "application_exit"
  }
}
```

After this notification, the plugin should finish outstanding work and exit with
code `0`.

## Entity Updates

SportOrg sends entity update notifications whenever the corresponding in-memory
entity is created, updated, or deleted. Payloads use the same field names as the
existing SportOrg JSON serialization.

Common update envelope:

```json
{
  "operation": "updated",
  "entity": {},
  "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
  "revision": 42
}
```

Fields:

- `operation`: `created`, `updated`, `deleted`, or `snapshot`.
- `entity`: serialized entity. For `deleted`, the payload must include at least
  `object` and `id`.
- `race_id`: current race identifier.
- `revision`: monotonically increasing host-side change number for this plugin
  session.

### `sportorg.race.update`

Sent when race metadata, race settings, or full race content changes.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.race.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 43,
    "entity": {
      "object": "Race",
      "id": "37a31618-47d0-4120-a11c-2d113df839a0",
      "data": {
        "title": "City Cup",
        "description": "",
        "short_title": "City Cup",
        "location": "City",
        "chief_referee": "",
        "secretary": "",
        "url": "",
        "race_type": 0,
        "start_datetime": "2026-05-18 10:00:00",
        "end_datetime": "2026-05-18 15:00:00",
        "relay_leg_count": 3
      },
      "settings": {},
      "organizations": [],
      "courses": [],
      "groups": [],
      "results": [],
      "persons": []
    }
  }
}
```

### `sportorg.result.update`

Sent when a result changes.

The `entity.object` value may be `Result`, `ResultManual`, `ResultSportident`,
`ResultSFR`, `ResultSportiduino`, `ResultRfidImpinj`, `ResultSrpid`, or
`ResultHuichang`.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.result.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 44,
    "entity": {
      "object": "ResultSportident",
      "id": "7d85e44a-630c-4e06-83c8-8d0c86049911",
      "bib": 101,
      "person_id": "bb280db8-dce1-4245-9e65-b4e8b234e7db",
      "days": 0,
      "start_time": 36000000,
      "finish_time": 39000000,
      "status": 1,
      "status_comment": "",
      "splits": []
    }
  }
}
```

### `sportorg.person.update`

Sent when a person changes.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.person.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 45,
    "entity": {
      "object": "Person",
      "id": "bb280db8-dce1-4245-9e65-b4e8b234e7db",
      "name": "John",
      "surname": "Smith",
      "middle_name": "",
      "card_number": 123456,
      "bib": 101,
      "birth_date": "1990-01-01",
      "group_id": "6245b064-cc9f-4fa7-a80f-ec34a730973e",
      "organization_id": "a90ac671-ea03-4187-b380-4d2305ec6b8b"
    }
  }
}
```

### `sportorg.group.update`

Sent when a group changes.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.group.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 46,
    "entity": {
      "object": "Group",
      "id": "6245b064-cc9f-4fa7-a80f-ec34a730973e",
      "name": "M21",
      "long_name": "Men 21",
      "course_id": "07426a6c-1e3a-4531-a22c-9ad0c4fe6ca7",
      "is_any_course": false,
      "price": 0,
      "min_year": 0,
      "max_year": 0,
      "min_age": 0,
      "max_age": 0
    }
  }
}
```

### `sportorg.organization.update`

Sent when an organization changes.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.organization.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 47,
    "entity": {
      "object": "Organization",
      "id": "a90ac671-ea03-4187-b380-4d2305ec6b8b",
      "name": "Sport Club",
      "country": "RUS",
      "region": "",
      "contact": "",
      "code": ""
    }
  }
}
```

### `sportorg.course.update`

Sent when a course changes.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.course.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 48,
    "entity": {
      "object": "Course",
      "id": "07426a6c-1e3a-4531-a22c-9ad0c4fe6ca7",
      "name": "Course 1",
      "length": 5200,
      "climb": 120,
      "controls": [
        {"object": "CourseControl", "code": "31", "length": 0}
      ]
    }
  }
}
```

### `sportorg.entity.update`

Generic fallback for future entity types.

SportOrg may use this notification for entities that do not yet have a
dedicated method. Plugins should ignore unknown `entity.object` values unless
they explicitly support them.

Notification:

```json
{
  "jsonrpc": "2.0",
  "method": "sportorg.entity.update",
  "params": {
    "operation": "updated",
    "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
    "revision": 49,
    "entity": {
      "object": "SomeFutureEntity",
      "id": "6f9408c6-f77a-4d0e-bde9-cf5930dc3196"
    }
  }
}
```

## Menu Items

### `plugin.menu.get`

SportOrg calls this method when it needs to build or refresh plugin menu items.
The current language is included so the plugin can return localized labels.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "plugin.menu.get",
  "params": {
    "language": "en_US",
    "context": {
      "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
      "selection": {
        "object": "Person",
        "ids": ["bb280db8-dce1-4245-9e65-b4e8b234e7db"]
      }
    }
  }
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "items": [
      {
        "id": "publish_results",
        "label": "Publish results",
        "tooltip": "Send current results to the configured endpoint",
        "enabled": true,
        "visible": true,
        "group": "Plugins",
        "order": 100
      },
      {
        "id": "settings",
        "label": "Settings",
        "enabled": true,
        "visible": true,
        "group": "Plugins",
        "order": 900
      }
    ]
  }
}
```

Menu item fields:

- `id`: stable plugin-local action identifier.
- `label`: visible menu text.
- `tooltip`: optional help text.
- `enabled`: whether the action can be triggered now.
- `visible`: whether SportOrg should show the item.
- `group`: menu group name. Default is `Plugins`.
- `order`: numeric sort key inside the group.

### `plugin.menu.execute`

Sent when the user selects a plugin menu item.

Request:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "plugin.menu.execute",
  "params": {
    "id": "publish_results",
    "language": "en_US",
    "context": {
      "race_id": "37a31618-47d0-4120-a11c-2d113df839a0",
      "selection": {
        "object": "Person",
        "ids": ["bb280db8-dce1-4245-9e65-b4e8b234e7db"]
      }
    }
  }
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "status": "ok",
    "message": "Results were published"
  }
}
```

If a menu action changes plugin settings, the plugin returns the new settings:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "status": "ok",
    "settings": {
      "api_token": "secret",
      "endpoint_url": "https://example.org/api",
      "auto_publish": true
    }
  }
}
```

SportOrg persists returned settings and passes them back in
`plugin.initialize.settings.plugin` on the next plugin start.

## Plugin-Initiated Requests

Plugins may send requests to SportOrg over `stdout`. SportOrg responds on
`stdin` with the same `id`.

### `sportorg.settings.update`

Requests persistence of plugin-specific settings without waiting for a menu
action response.

Request from plugin:

```json
{
  "jsonrpc": "2.0",
  "id": "plugin-1",
  "method": "sportorg.settings.update",
  "params": {
    "settings": {
      "api_token": "secret",
      "endpoint_url": "https://example.org/api",
      "auto_publish": true
    }
  }
}
```

Response from SportOrg:

```json
{
  "jsonrpc": "2.0",
  "id": "plugin-1",
  "result": {
    "saved": true
  }
}
```

Settings are scoped to the plugin identity declared during
`plugin.initialize`. SportOrg must not merge plugin settings into race settings
unless the user explicitly performs a host-side configuration action.

### `sportorg.notification.show`

Requests a user-visible notification.

Request from plugin:

```json
{
  "jsonrpc": "2.0",
  "id": "plugin-2",
  "method": "sportorg.notification.show",
  "params": {
    "level": "info",
    "message": "Results were published"
  }
}
```

Supported `level` values are `info`, `warning`, and `error`.

## Settings Persistence

SportOrg keeps plugin settings in the host configuration store under the plugin
identity returned from `plugin.initialize.result.plugin.id`.

Persistence rules:

1. On startup, SportOrg loads saved plugin settings.
1. SportOrg sends them in `plugin.initialize.params.settings.plugin`.
1. The plugin may return updated settings from `plugin.initialize`,
   `plugin.menu.execute`, or `sportorg.settings.update`.
1. SportOrg stores the complete returned settings object for that plugin.
1. On the next initialization, SportOrg sends the stored settings back to the
   same plugin.

Plugin settings must be JSON objects. Secret values are allowed, but plugins
should keep secret fields stable and avoid echoing them into messages, logs, or
menu labels.

## Compatibility

Plugins should:

- Ignore unknown fields.
- Ignore unknown notification methods.
- Treat missing optional fields as `null` or a documented default.
- Preserve their own settings schema across versions when possible.
- Declare supported features through `plugin.initialize.result.capabilities`.

SportOrg should:

- Start with `plugin.initialize`.
- Send only notifications for capabilities enabled by the plugin.
- Keep plugin-specific settings isolated by plugin id.
- Continue running when one plugin returns an error, unless the error happens
  during required initialization.
