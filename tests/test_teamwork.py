import logging
import socket
import time
from queue import Queue
from threading import Event

from sportorg.modules.teamwork.client import ClientThread
from sportorg.modules.teamwork.server import Command, ServerThread


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until(condition, timeout: float = 5.0, step: float = 0.05) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return
        time.sleep(step)
    raise TimeoutError("Condition was not met in time")


def start_server_and_client(keepalive_interval: float = 5.0):
    port = get_free_port()

    server_in_queue = Queue()
    server_out_queue = Queue()
    server_stop_event = Event()
    server = ServerThread(
        ("127.0.0.1", port),
        server_in_queue,
        server_out_queue,
        server_stop_event,
        logging.root,
    )
    server.start()
    server.wait()

    client_in_queue = Queue()
    client_out_queue = Queue()
    client_stop_event = Event()
    client = ClientThread(
        ("127.0.0.1", port),
        client_in_queue,
        client_out_queue,
        client_stop_event,
        logging.root,
        keepalive_interval=keepalive_interval,
    )
    client.start()
    client.wait()

    return {
        "server": server,
        "server_in_queue": server_in_queue,
        "server_out_queue": server_out_queue,
        "server_stop_event": server_stop_event,
        "client": client,
        "client_in_queue": client_in_queue,
        "client_out_queue": client_out_queue,
        "client_stop_event": client_stop_event,
    }


def stop_server_and_client(threads) -> None:
    threads["client_stop_event"].set()
    threads["server_stop_event"].set()
    threads["client"].join(timeout=5)
    threads["server"].join(timeout=5)


def test_teamwork():
    threads = start_server_and_client()
    server = threads["server"]
    server_in_queue = threads["server_in_queue"]
    server_out_queue = threads["server_out_queue"]
    client_in_queue = threads["client_in_queue"]
    client_out_queue = threads["client_out_queue"]

    try:
        wait_until(lambda: len(server.get_clients()) == 1)

        server_in_queue.put(
            Command(
                {
                    "object": "Person",
                    "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
                    "name": "Danil",
                },
                "Create",
            )
        )
        result = client_out_queue.get(timeout=10)
        assert result.data == {
            "object": "Person",
            "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
            "name": "Danil",
        }

        client_in_queue.put(
            Command(
                {
                    "object": "Person",
                    "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
                    "name": "Danil",
                },
                "Create",
            )
        )
        result = server_out_queue.get(timeout=5)
        assert result.data == {
            "object": "Person",
            "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
            "name": "Danil",
        }

        wait_until(lambda: server.get_clients()[0]["packets"] >= 1)
    finally:
        stop_server_and_client(threads)


def test_teamwork_keepalive_and_server_disconnect():
    threads = start_server_and_client(keepalive_interval=1.0)
    server = threads["server"]
    server_out_queue = threads["server_out_queue"]

    try:
        wait_until(lambda: len(server.get_clients()) == 1)
        wait_until(lambda: server.get_clients()[0]["keepalive_packets"] >= 1, timeout=4)
        assert server_out_queue.empty()

        client_id = int(server.get_clients()[0]["id"])
        server.disconnect_client(client_id)
        wait_until(lambda: len(server.get_clients()) == 0, timeout=4)
    finally:
        stop_server_and_client(threads)
