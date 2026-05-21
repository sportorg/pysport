import hashlib
import json
import logging
import os
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Lock, Thread
from typing import Any, Dict, List, Optional, Protocol, Tuple

from sportorg import config, settings
from sportorg.models.memory import race

PROTOCOL_VERSION = 1
PLUGIN_MENU_ACTION_PREFIX = "PluginMenuAction:"

RESULT_OBJECTS = {
    "Result",
    "ResultManual",
    "ResultSportident",
    "ResultSFR",
    "ResultSportiduino",
    "ResultRfidImpinj",
    "ResultSrpid",
    "ResultHuichang",
}

ENTITY_COLLECTIONS = [
    "organizations",
    "courses",
    "groups",
    "results",
    "persons",
]

ENTITY_METHODS = {
    "Race": "sportorg.race.update",
    "Result": "sportorg.result.update",
    "Person": "sportorg.person.update",
    "Group": "sportorg.group.update",
    "Organization": "sportorg.organization.update",
    "Course": "sportorg.course.update",
}

ENTITY_UPDATE_METHODS = {
    "sportorg.race.update": "Race",
    "sportorg.result.update": "Result",
    "sportorg.person.update": "Person",
    "sportorg.group.update": "Group",
    "sportorg.organization.update": "Organization",
    "sportorg.course.update": "Course",
    "sportorg.entity.update": "",
}

ENTITY_CAPABILITIES = {
    "Race": "race_updates",
    "Person": "person_updates",
    "Group": "group_updates",
    "Organization": "organization_updates",
    "Course": "course_updates",
    "Result": "result_updates",
}


class PluginProtocolError(Exception):
    pass


@dataclass
class PluginConfig:
    index: int
    executable_path: str
    arguments: str = ""
    enabled: bool = False
    plugin_id: str = ""


@dataclass
class PluginEntityUpdate:
    process: Any
    request_id: Any
    method: str
    params: Dict[str, Any]


class PluginCallbacks(Protocol):
    def get_plugin_settings(self, plugin_id: str) -> Dict[str, Any]: ...

    def plugin_initialized(
        self,
        config_index: int,
        plugin_id: str,
        plugin_name: str,
        plugin_version: str,
        returned_settings: Optional[Dict[str, Any]],
    ) -> None: ...

    def plugin_settings_updated(
        self, plugin_id: str, plugin_settings: Dict[str, Any]
    ) -> None: ...

    def plugin_notification(self, level: str, message: str) -> None: ...

    def plugin_entity_update(
        self, process: Any, request_id: Any, method: str, params: Dict[str, Any]
    ) -> None: ...

    def plugin_menu_updated(self) -> None: ...


def make_plugin_menu_action(plugin_id: str, item_id: str) -> str:
    return "{}{}:{}".format(PLUGIN_MENU_ACTION_PREFIX, plugin_id, item_id)


def parse_plugin_menu_action(action_key: str) -> Tuple[str, str]:
    if not action_key.startswith(PLUGIN_MENU_ACTION_PREFIX):
        return "", ""

    action_id = action_key[len(PLUGIN_MENU_ACTION_PREFIX) :]
    plugin_id, separator, item_id = action_id.partition(":")
    if not separator:
        return "", ""
    return plugin_id, item_id


def _json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)


def _local_timezone_name() -> str:
    tzinfo = datetime.now().astimezone().tzinfo
    if tzinfo is None:
        return ""
    return str(tzinfo)


def _entity_type(object_name: str) -> str:
    if object_name in RESULT_OBJECTS:
        return "Result"
    return object_name


def _method_for_entity(entity: Dict[str, Any]) -> str:
    object_name = str(entity.get("object", ""))
    entity_type = _entity_type(object_name)
    return ENTITY_METHODS.get(entity_type, "sportorg.entity.update")


def _capability_for_entity(entity: Dict[str, Any]) -> str:
    object_name = str(entity.get("object", ""))
    entity_type = _entity_type(object_name)
    return ENTITY_CAPABILITIES.get(entity_type, "")


def _validate_entity_update_method(method: str, entity: Dict[str, Any]) -> bool:
    expected_type = ENTITY_UPDATE_METHODS.get(method)
    if expected_type is None:
        return False
    if not expected_type:
        return True

    object_name = str(entity.get("object", ""))
    return _entity_type(object_name) == expected_type


def _entity_uuid(entity: Dict[str, Any]) -> uuid.UUID:
    entity_id = str(entity.get("id", ""))
    if not entity_id:
        raise PluginProtocolError("entity.id is required")
    try:
        return uuid.UUID(entity_id)
    except ValueError as exc:
        raise PluginProtocolError("entity.id must be a UUID") from exc


def _build_entity_map(
    race_snapshot: Dict[str, Any],
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    entity_map = {}
    race_id = str(race_snapshot.get("id", ""))
    if race_id:
        entity_map[("Race", race_id)] = race_snapshot

    for collection in ENTITY_COLLECTIONS:
        entities = race_snapshot.get(collection, [])
        if not isinstance(entities, list):
            continue

        for entity in entities:
            if not isinstance(entity, dict):
                continue
            object_name = str(entity.get("object", ""))
            entity_id = str(entity.get("id", ""))
            if object_name and entity_id:
                entity_map[(object_name, entity_id)] = entity

    return entity_map


def _diff_entity_maps(
    old_entities: Dict[Tuple[str, str], Dict[str, Any]],
    new_entities: Dict[Tuple[str, str], Dict[str, Any]],
) -> List[Tuple[str, Dict[str, Any]]]:
    changes = []
    old_keys = set(old_entities)
    new_keys = set(new_entities)

    for key in sorted(new_keys - old_keys):
        changes.append(("created", new_entities[key]))

    for key in sorted(old_keys & new_keys):
        if _stable_json(old_entities[key]) != _stable_json(new_entities[key]):
            changes.append(("updated", new_entities[key]))

    for key in sorted(old_keys - new_keys):
        old_entity = old_entities[key]
        changes.append(
            (
                "deleted",
                {
                    "object": old_entity.get("object", key[0]),
                    "id": old_entity.get("id", key[1]),
                },
            )
        )

    return changes


def _build_selection_context(app: Any) -> Dict[str, Any]:
    context = {
        "race_id": str(race().id),
        "selection": {
            "object": "",
            "ids": [],
        },
    }

    try:
        current_tab = app.current_tab
        rows = app.get_selected_rows()
    except Exception:
        return context

    tab_map = {
        0: ("Person", race().persons),
        1: ("Result", race().results),
        2: ("Group", race().groups),
        3: ("Course", race().courses),
        4: ("Organization", race().organizations),
    }
    if current_tab not in tab_map:
        return context

    object_name, collection = tab_map[current_tab]
    selected_ids = []
    for row in rows:
        if 0 <= row < len(collection):
            selected_ids.append(str(collection[row].id))

    context["selection"] = {
        "object": object_name,
        "ids": selected_ids,
    }
    return context


class PluginProcess:
    def __init__(self, plugin_config: PluginConfig, callbacks: PluginCallbacks):
        self.config = plugin_config
        self._callbacks = callbacks
        self._process: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[Thread] = None
        self._stderr_thread: Optional[Thread] = None
        self._bootstrap_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._write_lock = Lock()
        self._request_lock = Lock()
        self._pending_lock = Lock()
        self._state_lock = Lock()
        self._pending: Dict[Any, Queue] = {}
        self._next_request_id = 1
        self._revision = 0
        self.plugin_id = plugin_config.plugin_id
        self.plugin_name = ""
        self.plugin_version = ""
        self.capabilities: Dict[str, Any] = {}
        self._menu_items: List[Dict[str, Any]] = []
        self._status = "stopped"

    def start(self) -> None:
        if not self.config.enabled:
            return

        executable_path = self.config.executable_path.strip()
        if not executable_path:
            self._set_status("empty executable path")
            return

        if self.is_alive():
            return

        command = self._build_command()
        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            self._set_status("start failed: {}".format(exc))
            logging.error("Cannot start plugin %s: %s", executable_path, exc)
            return

        self._stop_event.clear()
        self._set_status("starting")
        self._reader_thread = Thread(
            target=self._read_loop,
            name="PluginReader-{}".format(self.config.index),
            daemon=True,
        )
        self._reader_thread.start()

        self._stderr_thread = Thread(
            target=self._stderr_loop,
            name="PluginStderr-{}".format(self.config.index),
            daemon=True,
        )
        self._stderr_thread.start()

        self._bootstrap_thread = Thread(
            target=self._bootstrap,
            name="PluginBootstrap-{}".format(self.config.index),
            daemon=True,
        )
        self._bootstrap_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        process = self._process
        if process is None:
            return

        if self.is_alive():
            try:
                self.send_notification(
                    "plugin.shutdown", {"reason": "application_exit"}
                )
            except Exception as exc:
                logging.debug("Cannot send plugin shutdown: %s", exc)

            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()

        self._set_status("stopped")

    def is_alive(self) -> bool:
        process = self._process
        return process is not None and process.poll() is None

    def display_name(self) -> str:
        if self.plugin_name:
            return self.plugin_name
        if self.plugin_id:
            return self.plugin_id
        return os.path.basename(self.config.executable_path)

    def status(self) -> str:
        with self._state_lock:
            return self._status

    def get_menu_entries(self) -> List[Dict[str, Any]]:
        with self._state_lock:
            return [item.copy() for item in self._menu_items]

    def refresh_menu_async(self, context: Optional[Dict[str, Any]] = None) -> None:
        if not self._supports_capability("menu"):
            return

        Thread(
            target=self.refresh_menu,
            args=(context,),
            name="PluginMenu-{}".format(self.config.index),
            daemon=True,
        ).start()

    def refresh_menu(self, context: Optional[Dict[str, Any]] = None) -> None:
        if not self.is_alive() or not self._supports_capability("menu"):
            return

        params = {
            "language": settings.SETTINGS.locale,
            "context": context or {"race_id": str(race().id), "selection": {}},
        }
        try:
            response = self.send_request("plugin.menu.get", params, timeout=10)
        except Exception as exc:
            logging.error("Cannot refresh plugin menu %s: %s", self.display_name(), exc)
            return

        result = response.get("result", {})
        items = result.get("items", []) if isinstance(result, dict) else []
        menu_items = self._normalize_menu_items(items)
        with self._state_lock:
            self._menu_items = menu_items
        self._callbacks.plugin_menu_updated()

    def execute_menu_item_async(
        self, item_id: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        Thread(
            target=self._execute_menu_item,
            args=(item_id, context),
            name="PluginExecute-{}".format(self.config.index),
            daemon=True,
        ).start()

    def send_entity_update(
        self, operation: str, race_id: str, entity: Dict[str, Any]
    ) -> None:
        if not self.is_alive() or not self.plugin_id:
            return

        capability = _capability_for_entity(entity)
        if capability and not self._supports_capability(capability):
            return

        self._revision += 1
        params = {
            "operation": operation,
            "race_id": race_id,
            "revision": self._revision,
            "entity": entity,
        }
        try:
            self.send_notification(_method_for_entity(entity), params)
        except Exception as exc:
            logging.error("Cannot send plugin update: %s", exc)

    def send_request(
        self, method: str, params: Dict[str, Any], timeout: float = 10
    ) -> Dict[str, Any]:
        with self._request_lock:
            request_id = self._next_request_id
            self._next_request_id += 1
        response_queue = Queue(maxsize=1)

        with self._pending_lock:
            self._pending[request_id] = response_queue

        try:
            self._send_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params,
                }
            )
        except Exception:
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise

        try:
            response = response_queue.get(timeout=timeout)
        except Empty as exc:
            with self._pending_lock:
                self._pending.pop(request_id, None)
            raise PluginProtocolError(
                "Plugin request timed out: {}".format(method)
            ) from exc

        if isinstance(response, dict) and "error" in response:
            error = response.get("error", {})
            message = error.get("message", "Plugin error")
            raise PluginProtocolError(str(message))

        if not isinstance(response, dict):
            raise PluginProtocolError("Invalid plugin response")
        return response

    def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        self._send_message(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }
        )

    def respond_result(self, request_id: Any, result: Dict[str, Any]) -> None:
        if request_id is not None:
            self._send_result(request_id, result)

    def respond_error(self, request_id: Any, code: int, message: str) -> None:
        if request_id is not None:
            self._send_error(request_id, code, message)

    def _build_command(self) -> List[str]:
        arguments = shlex.split(self.config.arguments, posix=os.name != "nt")
        return [self.config.executable_path] + arguments

    def _bootstrap(self) -> None:
        try:
            response = self.send_request(
                "plugin.initialize", self._build_initialize_params(), timeout=10
            )
            self._handle_initialize_response(response)
            self._set_status("running")
            self.refresh_menu()
        except Exception as exc:
            self._set_status("initialize failed: {}".format(exc))
            logging.error("Cannot initialize plugin %s: %s", self.display_name(), exc)

    def _build_initialize_params(self) -> Dict[str, Any]:
        plugin_settings = {}
        if self.config.plugin_id:
            plugin_settings = self._callbacks.get_plugin_settings(self.config.plugin_id)

        return {
            "protocol_version": PROTOCOL_VERSION,
            "host": {
                "name": config.NAME,
                "version": config.VERSION,
            },
            "settings": {
                "language": settings.SETTINGS.locale,
                "timezone": _local_timezone_name(),
                "plugin": plugin_settings,
                "host": race().settings.copy(),
            },
            "race": race().to_dict(),
        }

    def _handle_initialize_response(self, response: Dict[str, Any]) -> None:
        result = response.get("result", {})
        if not isinstance(result, dict):
            raise PluginProtocolError("plugin.initialize returned invalid result")

        plugin_info = result.get("plugin", {})
        if not isinstance(plugin_info, dict):
            plugin_info = {}

        plugin_id = str(plugin_info.get("id", "") or self.config.plugin_id)
        if not plugin_id:
            plugin_id = self._fallback_plugin_id()

        returned_settings = result.get("settings")
        if returned_settings is not None and not isinstance(returned_settings, dict):
            returned_settings = None

        capabilities = result.get("capabilities", {})
        if not isinstance(capabilities, dict):
            capabilities = {}

        with self._state_lock:
            self.plugin_id = plugin_id
            self.plugin_name = str(plugin_info.get("name", plugin_id))
            self.plugin_version = str(plugin_info.get("version", ""))
            self.capabilities = capabilities

        self._callbacks.plugin_initialized(
            self.config.index,
            self.plugin_id,
            self.plugin_name,
            self.plugin_version,
            returned_settings,
        )

    def _fallback_plugin_id(self) -> str:
        source = "{} {}".format(self.config.executable_path, self.config.arguments)
        digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
        return "executable.{}".format(digest)

    def _execute_menu_item(
        self, item_id: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        params = {
            "id": item_id,
            "language": settings.SETTINGS.locale,
            "context": context or {"race_id": str(race().id), "selection": {}},
        }
        try:
            response = self.send_request("plugin.menu.execute", params, timeout=30)
        except Exception as exc:
            message = "Plugin action failed: {}".format(exc)
            logging.error(message)
            self._callbacks.plugin_notification("error", message)
            return

        result = response.get("result", {})
        if not isinstance(result, dict):
            return

        returned_settings = result.get("settings")
        if isinstance(returned_settings, dict) and self.plugin_id:
            self._callbacks.plugin_settings_updated(self.plugin_id, returned_settings)

        message = result.get("message")
        if message:
            self._callbacks.plugin_notification("info", str(message))

        self.refresh_menu(context)

    def _normalize_menu_items(self, items: Any) -> List[Dict[str, Any]]:
        if not isinstance(items, list):
            return []

        menu_items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("visible", True) is False:
                continue

            item_id = str(item.get("id", "")).strip()
            label = str(item.get("label", "")).strip()
            if not item_id or not label:
                continue

            menu_items.append(
                {
                    "id": item_id,
                    "label": label,
                    "tooltip": str(item.get("tooltip", "")),
                    "enabled": bool(item.get("enabled", True)),
                    "group": str(item.get("group", "Plugins") or "Plugins"),
                    "order": int(item.get("order", 0) or 0),
                }
            )

        return sorted(
            menu_items, key=lambda item: (item["group"], item["order"], item["label"])
        )

    def _read_loop(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return

        for line in process.stdout:
            if self._stop_event.is_set():
                break
            line = line.strip()
            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                logging.error("Invalid plugin JSON: %s", exc)
                continue

            if not isinstance(message, dict):
                logging.error("Invalid plugin message type: %s", type(message))
                continue

            self._handle_message(message)

        if not self._stop_event.is_set():
            self._set_status("stopped")

    def _stderr_loop(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return

        for line in process.stderr:
            line = line.rstrip()
            if line:
                logging.info("Plugin %s: %s", self.display_name(), line)

    def _handle_message(self, message: Dict[str, Any]) -> None:
        if "id" in message and ("result" in message or "error" in message):
            with self._pending_lock:
                response_queue = self._pending.pop(message.get("id"), None)
            if response_queue is not None:
                response_queue.put(message)
            return

        method = message.get("method")
        if not method:
            logging.error("Plugin message without method: %s", message)
            return

        if "id" in message:
            self._handle_plugin_request(message)
        else:
            self._handle_plugin_notification(message)

    def _handle_plugin_request(self, message: Dict[str, Any]) -> None:
        method = str(message.get("method", ""))
        request_id = message.get("id")
        params = message.get("params", {})
        if not isinstance(params, dict):
            self._send_error(request_id, -32602, "Invalid params")
            return

        if method in ENTITY_UPDATE_METHODS:
            entity = params.get("entity", {})
            if not isinstance(entity, dict):
                self._send_error(request_id, -32602, "entity must be an object")
                return
            if not _validate_entity_update_method(method, entity):
                self._send_error(
                    request_id, -32602, "entity.object does not match method"
                )
                return

            self._callbacks.plugin_entity_update(self, request_id, method, params)
            return

        if method == "sportorg.settings.update":
            plugin_settings = params.get("settings", {})
            if not self.plugin_id:
                self._send_error(request_id, -32000, "Plugin is not initialized")
                return
            if not isinstance(plugin_settings, dict):
                self._send_error(request_id, -32602, "settings must be an object")
                return

            self._callbacks.plugin_settings_updated(self.plugin_id, plugin_settings)
            self._send_result(request_id, {"saved": True})
            return

        if method == "sportorg.notification.show":
            level = str(params.get("level", "info"))
            message_text = str(params.get("message", ""))
            if level not in {"info", "warning", "error"}:
                level = "info"
            if message_text:
                self._callbacks.plugin_notification(level, message_text)
            self._send_result(request_id, {"shown": True})
            return

        self._send_error(request_id, -32601, "Method not found")

    def _handle_plugin_notification(self, message: Dict[str, Any]) -> None:
        method = str(message.get("method", ""))
        params = message.get("params", {})
        if method in ENTITY_UPDATE_METHODS and isinstance(params, dict):
            entity = params.get("entity", {})
            if isinstance(entity, dict) and _validate_entity_update_method(
                method, entity
            ):
                self._callbacks.plugin_entity_update(self, None, method, params)
                return

        logging.debug("Plugin notification ignored: %s", message)

    def _send_result(self, request_id: Any, result: Dict[str, Any]) -> None:
        self._send_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }
        )

    def _send_error(self, request_id: Any, code: int, message: str) -> None:
        self._send_message(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                },
            }
        )

    def _send_message(self, message: Dict[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None or not self.is_alive():
            raise PluginProtocolError("Plugin process is not running")

        line = _json_dumps(message) + "\n"
        with self._write_lock:
            process.stdin.write(line)
            process.stdin.flush()

    def _supports_capability(self, capability: str) -> bool:
        with self._state_lock:
            if not self.capabilities:
                return True
            return bool(self.capabilities.get(capability, False))

    def _set_status(self, status: str) -> None:
        with self._state_lock:
            self._status = status


class PluginClient(PluginCallbacks):
    def __init__(self) -> None:
        self._plugins: List[PluginProcess] = []
        self._lock = Lock()
        self._notifications = Queue()
        self._entity_updates = Queue()
        self._menu_revision = 0
        self._entity_snapshot: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def start(self) -> None:
        self.stop()
        self._entity_snapshot = _build_entity_map(race().to_dict())

        plugin_configs = [
            PluginConfig(
                index=index,
                executable_path=str(item.get("executable_path", "")),
                arguments=str(item.get("arguments", "")),
                enabled=bool(item.get("enabled", False)),
                plugin_id=str(item.get("plugin_id", "")),
            )
            for index, item in enumerate(settings.get_plugin_configs())
        ]

        plugins = []
        for plugin_config in plugin_configs:
            if not plugin_config.enabled:
                continue
            process = PluginProcess(plugin_config, self)
            process.start()
            plugins.append(process)

        with self._lock:
            self._plugins = plugins

    def reload(self) -> None:
        self.start()

    def stop(self) -> None:
        with self._lock:
            plugins = self._plugins
            self._plugins = []

        for process in plugins:
            process.stop()

    def get_plugin_settings(self, plugin_id: str) -> Dict[str, Any]:
        return settings.get_plugin_saved_settings(plugin_id)

    def plugin_initialized(
        self,
        config_index: int,
        plugin_id: str,
        plugin_name: str,
        plugin_version: str,
        returned_settings: Optional[Dict[str, Any]],
    ) -> None:
        settings.set_plugin_config_plugin_id(config_index, plugin_id)
        if returned_settings is not None:
            settings.set_plugin_saved_settings(plugin_id, returned_settings)
        settings.save_settings_to_file()
        logging.info("Plugin initialized: %s %s", plugin_name, plugin_version)
        self.plugin_menu_updated()

    def plugin_settings_updated(
        self, plugin_id: str, plugin_settings: Dict[str, Any]
    ) -> None:
        settings.set_plugin_saved_settings(plugin_id, plugin_settings)
        settings.save_settings_to_file()

    def plugin_notification(self, level: str, message: str) -> None:
        self._notifications.put({"level": level, "message": message})

    def plugin_entity_update(
        self, process: Any, request_id: Any, method: str, params: Dict[str, Any]
    ) -> None:
        self._entity_updates.put(
            PluginEntityUpdate(
                process=process,
                request_id=request_id,
                method=method,
                params=params,
            )
        )

    def plugin_menu_updated(self) -> None:
        with self._lock:
            self._menu_revision += 1

    def menu_revision(self) -> int:
        with self._lock:
            return self._menu_revision

    def pull_notifications(self) -> List[Dict[str, str]]:
        notifications = []
        while True:
            try:
                notifications.append(self._notifications.get_nowait())
                self._notifications.task_done()
            except Empty:
                return notifications

    def pull_entity_updates(self) -> List[PluginEntityUpdate]:
        updates = []
        while True:
            try:
                updates.append(self._entity_updates.get_nowait())
                self._entity_updates.task_done()
            except Empty:
                return updates

    def apply_entity_update(self, update: PluginEntityUpdate) -> Dict[str, Any]:
        params = update.params
        operation = str(params.get("operation", "updated"))
        entity = params.get("entity", {})
        if not isinstance(entity, dict):
            raise PluginProtocolError("entity must be an object")
        if not _validate_entity_update_method(update.method, entity):
            raise PluginProtocolError("entity.object does not match method")

        if operation == "deleted":
            self._delete_entity(entity)
        elif operation in {"created", "updated", "snapshot"}:
            race().update_data(entity)
        else:
            raise PluginProtocolError(
                "Unsupported entity operation: {}".format(operation)
            )

        race().rebuild_indexes(True, True)
        self._entity_snapshot = _build_entity_map(race().to_dict())
        return {
            "updated": True,
            "operation": operation,
            "object": str(entity.get("object", "")),
            "id": str(entity.get("id", "")),
        }

    def _delete_entity(self, entity: Dict[str, Any]) -> None:
        object_name = str(entity.get("object", ""))
        entity_type = _entity_type(object_name)
        entity_id = _entity_uuid(entity)
        race_obj = race()

        if entity_type == "Person":
            race_obj.delete_persons_by_id([entity_id])
        elif entity_type == "Result":
            race_obj.delete_results_by_id([entity_id])
        elif entity_type == "Group":
            race_obj.delete_groups_by_id([entity_id])
        elif entity_type == "Course":
            race_obj.delete_courses_by_id([entity_id])
        elif entity_type == "Organization":
            race_obj.delete_organizations_by_id([entity_id])
        elif entity_type == "Race":
            raise PluginProtocolError("Race deletion is not supported")
        else:
            raise PluginProtocolError(
                "Unsupported entity object: {}".format(object_name)
            )
        self._remove_entity_from_index(race_obj, entity_type, entity_id)

    @staticmethod
    def _remove_entity_from_index(
        race_obj: Any, entity_type: str, entity_id: uuid.UUID
    ) -> None:
        indexes = {
            "Person": race_obj.person_index,
            "Result": race_obj.result_index,
            "Group": race_obj.group_index,
            "Course": race_obj.course_index,
            "Organization": race_obj.organization_index,
        }
        index = indexes.get(entity_type)
        if index is None:
            return
        index.pop(entity_id, None)
        index.pop(str(entity_id), None)

    def refresh_menus(self, app: Any = None) -> None:
        context = _build_selection_context(app) if app is not None else None
        for process in self._get_plugins():
            process.refresh_menu_async(context)

    def get_menu_tree(self) -> List[Dict[str, Any]]:
        plugin_menus = []
        for process in self._get_plugins():
            entries = process.get_menu_entries()
            if not entries:
                continue

            grouped_entries: Dict[str, List[Dict[str, Any]]] = {}
            for entry in entries:
                grouped_entries.setdefault(entry["group"], []).append(entry)

            actions = []
            if len(grouped_entries) == 1 and "Plugins" in grouped_entries:
                actions = self._build_menu_actions(process, grouped_entries["Plugins"])
            else:
                for group_name in sorted(grouped_entries):
                    actions.append(
                        {
                            "title": group_name,
                            "actions": self._build_menu_actions(
                                process, grouped_entries[group_name]
                            ),
                        }
                    )

            if actions:
                plugin_menus.append(
                    {
                        "title": process.display_name(),
                        "actions": actions,
                    }
                )

        return plugin_menus

    def execute_menu_action(self, action_key: str, app: Any) -> None:
        plugin_id, item_id = parse_plugin_menu_action(action_key)
        if not plugin_id or not item_id:
            return

        context = _build_selection_context(app)
        for process in self._get_plugins():
            if process.plugin_id == plugin_id:
                process.execute_menu_item_async(item_id, context)
                return

    def sync_current_race(self) -> None:
        self.sync_race_snapshot(race().to_dict())

    def sync_race_snapshot(self, race_snapshot: Dict[str, Any]) -> None:
        new_snapshot = _build_entity_map(race_snapshot)
        if not self._entity_snapshot:
            self._entity_snapshot = new_snapshot
            return

        changes = _diff_entity_maps(self._entity_snapshot, new_snapshot)
        self._entity_snapshot = new_snapshot
        if not changes:
            return

        race_id = str(race_snapshot.get("id", ""))
        for process in self._get_plugins():
            for operation, entity in changes:
                process.send_entity_update(operation, race_id, entity)

    def _get_plugins(self) -> List[PluginProcess]:
        with self._lock:
            return list(self._plugins)

    @staticmethod
    def _build_menu_actions(
        process: PluginProcess, entries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        actions = []
        for entry in entries:
            actions.append(
                {
                    "title": entry["label"],
                    "status_tip": entry["tooltip"],
                    "enabled": entry["enabled"],
                    "action": make_plugin_menu_action(process.plugin_id, entry["id"]),
                }
            )
        return actions


plugin_client = PluginClient()
