import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from sportorg import settings
from sportorg.models.memory import Person, race
from sportorg.modules.plugins.manager import (
    PluginConfig,
    PluginClient,
    PluginEntityUpdate,
    PluginProcess,
    _method_for_entity,
)


class FakePluginCallbacks:
    def __init__(self) -> None:
        self.initialized = False
        self.plugin_id = ""
        self.plugin_settings: Dict[str, Any] = {}
        self.notifications = []
        self.menu_updates = 0

    def get_plugin_settings(self, plugin_id: str) -> Dict[str, Any]:
        return self.plugin_settings.get(plugin_id, {})

    def plugin_initialized(
        self,
        config_index: int,
        plugin_id: str,
        plugin_name: str,
        plugin_version: str,
        returned_settings: Optional[Dict[str, Any]],
    ) -> None:
        self.initialized = True
        self.plugin_id = plugin_id
        if returned_settings is not None:
            self.plugin_settings[plugin_id] = returned_settings

    def plugin_settings_updated(
        self, plugin_id: str, plugin_settings: Dict[str, Any]
    ) -> None:
        self.plugin_settings[plugin_id] = plugin_settings

    def plugin_notification(self, level: str, message: str) -> None:
        self.notifications.append({"level": level, "message": message})

    def plugin_entity_update(
        self, process: Any, request_id: Any, method: str, params: Dict[str, Any]
    ) -> None:
        pass

    def plugin_menu_updated(self) -> None:
        self.menu_updates += 1


def wait_until(condition, timeout: float = 5.0, step: float = 0.05) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return
        time.sleep(step)
    raise TimeoutError("Condition was not met in time")


def test_plugin_process_initializes_and_handles_updates() -> None:
    callbacks = FakePluginCallbacks()
    script_path = Path("plugin-example/plugin_example/__main__.py").resolve()
    process = PluginProcess(
        PluginConfig(
            index=0,
            executable_path=sys.executable,
            arguments=str(script_path),
            enabled=True,
        ),
        callbacks,
    )

    try:
        process.start()
        wait_until(lambda: callbacks.initialized)
        wait_until(lambda: bool(process.get_menu_entries()))

        assert callbacks.plugin_id == "sportorg.example.python"
        assert process.get_menu_entries()[0]["id"] == "show_summary"

        process.send_entity_update(
            "updated",
            str(race().id),
            {
                "object": "Person",
                "id": "person-1",
            },
        )
        response = process.send_request(
            "plugin.menu.execute",
            {
                "id": "show_summary",
                "language": "en_US",
                "context": {"race_id": str(race().id), "selection": {}},
            },
        )

        assert "person=1" in response["result"]["message"]
    finally:
        process.stop()


def test_result_entities_use_result_update_method() -> None:
    assert (
        _method_for_entity({"object": "ResultSportident"}) == "sportorg.result.update"
    )
    assert _method_for_entity({"object": "ResultManual"}) == "sportorg.result.update"


def test_plugin_client_applies_incoming_person_update() -> None:
    client = PluginClient()
    person = Person()
    person_data = person.to_dict()
    person_data["name"] = "Plugin"
    person_data["surname"] = "Updated"

    try:
        result = client.apply_entity_update(
            PluginEntityUpdate(
                process=None,
                request_id="plugin-1",
                method="sportorg.person.update",
                params={"operation": "created", "entity": person_data},
            )
        )

        assert result["updated"] is True
        created_person = race().get_obj("Person", person_data["id"])
        assert created_person is not None
        assert created_person.full_name == "Updated Plugin"

        client.apply_entity_update(
            PluginEntityUpdate(
                process=None,
                request_id="plugin-2",
                method="sportorg.person.update",
                params={
                    "operation": "deleted",
                    "entity": {"object": "Person", "id": person_data["id"]},
                },
            )
        )

        assert race().get_obj("Person", person_data["id"]) is None
    finally:
        race().delete_persons_by_id([person.id])
        race().person_index.pop(str(person.id), None)


def test_plugin_settings_are_normalized() -> None:
    original_plugins = settings.SETTINGS.plugins
    original_plugin_settings = settings.SETTINGS.plugin_settings
    try:
        settings.SETTINGS.plugins = [
            {
                "path": "/tmp/plugin",
                "arguments": "--debug",
                "enabled": True,
                "plugin_id": "plugin.id",
            },
            "invalid",
        ]
        settings.SETTINGS.plugin_settings = {
            "plugin.id": {"token": "secret"},
            "broken": "not a dict",
        }

        assert settings.get_plugin_configs() == [
            {
                "executable_path": "/tmp/plugin",
                "arguments": "--debug",
                "enabled": True,
                "plugin_id": "plugin.id",
            }
        ]
        assert settings.get_plugin_saved_settings("plugin.id") == {"token": "secret"}
        assert settings.get_plugin_saved_settings("broken") == {}
    finally:
        settings.SETTINGS.plugins = original_plugins
        settings.SETTINGS.plugin_settings = original_plugin_settings
