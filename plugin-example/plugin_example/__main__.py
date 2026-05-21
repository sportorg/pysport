import json
import sys
from typing import Any, Dict

PLUGIN_INFO = {
    "id": "sportorg.example.python",
    "name": "Python Example Plugin",
    "version": "0.1.0",
}


class ExamplePlugin:
    def __init__(self) -> None:
        self.settings: Dict[str, Any] = {
            "auto_publish": False,
            "executions": 0,
        }
        self.race: Dict[str, Any] = {}
        self.update_counts = {
            "race": 0,
            "result": 0,
            "person": 0,
            "group": 0,
            "organization": 0,
            "course": 0,
            "entity": 0,
        }

    def handle_request(self, message: Dict[str, Any]) -> None:
        method = str(message.get("method", ""))
        request_id = message.get("id")
        params = message.get("params", {})
        if not isinstance(params, dict):
            self.write_error(request_id, -32602, "Invalid params")
            return

        if method == "plugin.initialize":
            plugin_settings = (
                params.get("settings", {}).get("plugin", {})
                if isinstance(params.get("settings", {}), dict)
                else {}
            )
            if isinstance(plugin_settings, dict):
                self.settings.update(plugin_settings)
            race = params.get("race", {})
            if isinstance(race, dict):
                self.race = race
            self.write_result(
                request_id,
                {
                    "plugin": PLUGIN_INFO,
                    "capabilities": {
                        "menu": True,
                        "race_updates": True,
                        "result_updates": True,
                        "person_updates": True,
                        "group_updates": True,
                        "organization_updates": True,
                        "course_updates": True,
                        "settings": True,
                    },
                    "settings": self.settings,
                },
            )
            return

        if method == "plugin.menu.get":
            self.write_result(
                request_id,
                {
                    "items": [
                        {
                            "id": "show_summary",
                            "label": "Show plugin summary",
                            "tooltip": "Show how many updates the example plugin received",
                            "enabled": True,
                            "visible": True,
                            "group": "Example",
                            "order": 100,
                        },
                        {
                            "id": "toggle_auto_publish",
                            "label": self._toggle_label(),
                            "enabled": True,
                            "visible": True,
                            "group": "Example",
                            "order": 200,
                        },
                        {
                            "id": "update_race_description",
                            "label": "Update race description",
                            "enabled": bool(self.race),
                            "visible": True,
                            "group": "Example",
                            "order": 300,
                        },
                    ]
                },
            )
            return

        if method == "plugin.menu.execute":
            action_id = str(params.get("id", ""))
            if action_id == "show_summary":
                self.settings["executions"] = (
                    int(self.settings.get("executions", 0)) + 1
                )
                self.write_result(
                    request_id,
                    {
                        "status": "ok",
                        "message": self._summary_message(),
                        "settings": self.settings,
                    },
                )
                return

            if action_id == "toggle_auto_publish":
                self.settings["auto_publish"] = not bool(
                    self.settings.get("auto_publish", False)
                )
                self.write_result(
                    request_id,
                    {
                        "status": "ok",
                        "message": self._toggle_label(),
                        "settings": self.settings,
                    },
                )
                return

            if action_id == "update_race_description":
                self.send_race_description_update()
                self.write_result(
                    request_id,
                    {
                        "status": "ok",
                        "message": "Race update sent from example plugin",
                    },
                )
                return

            self.write_error(request_id, -32601, "Unknown menu action")
            return

        self.write_error(request_id, -32601, "Method not found")

    def handle_notification(self, message: Dict[str, Any]) -> None:
        method = str(message.get("method", ""))
        if method == "plugin.shutdown":
            raise SystemExit(0)

        prefix = "sportorg."
        suffix = ".update"
        if method.startswith(prefix) and method.endswith(suffix):
            entity_name = method[len(prefix) : -len(suffix)]
            if entity_name in self.update_counts:
                self.update_counts[entity_name] += 1

    def write_result(self, request_id: Any, result: Dict[str, Any]) -> None:
        self.write_message({"jsonrpc": "2.0", "id": request_id, "result": result})

    def write_error(self, request_id: Any, code: int, message: str) -> None:
        self.write_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                },
            }
        )

    def write_message(self, message: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def send_race_description_update(self) -> None:
        if not self.race:
            return

        race_entity = dict(self.race)
        race_data = dict(race_entity.get("data", {}))
        race_data["description"] = "Updated by Python Example Plugin"
        race_entity["data"] = race_data
        self.write_message(
            {
                "jsonrpc": "2.0",
                "method": "sportorg.race.update",
                "params": {
                    "operation": "updated",
                    "race_id": race_entity.get("id", ""),
                    "entity": race_entity,
                },
            }
        )

    def _summary_message(self) -> str:
        parts = [
            "{}={}".format(key, value)
            for key, value in sorted(self.update_counts.items())
            if value
        ]
        if not parts:
            return "Example plugin is connected; no updates received yet"
        return "Example plugin updates: {}".format(", ".join(parts))

    def _toggle_label(self) -> str:
        if bool(self.settings.get("auto_publish", False)):
            return "Disable auto publish"
        return "Enable auto publish"


def main() -> None:
    plugin = ExamplePlugin()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stderr.write("Invalid JSON: {}\n".format(exc))
            sys.stderr.flush()
            continue

        if not isinstance(message, dict):
            continue

        if "id" in message and "method" in message:
            plugin.handle_request(message)
        elif "method" in message:
            plugin.handle_notification(message)


if __name__ == "__main__":
    main()
