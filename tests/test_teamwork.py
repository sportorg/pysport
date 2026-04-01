import logging
import socket
import time
from queue import Queue
from threading import Event

import pytest
import orjson

from sportorg.modules.teamwork.client import ClientThread
from sportorg.modules.teamwork.crypto import (
    TeamworkCipher,
    TeamworkCryptoError,
    generate_teamwork_key,
    load_teamwork_key_from_file,
    normalize_teamwork_key,
)
from sportorg.modules.teamwork.packet_header import Header
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


def start_server_and_client(
    keepalive_interval: float = 5.0,
    server_cipher=None,
    client_cipher=None,
):
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
        cipher=server_cipher,
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
        cipher=client_cipher,
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


def test_teamwork_with_encryption():
    server_cipher = _create_cipher_or_skip("teamwork-shared-key")
    client_cipher = _create_cipher_or_skip("teamwork-shared-key")
    threads = start_server_and_client(
        keepalive_interval=1.0,
        server_cipher=server_cipher,
        client_cipher=client_cipher,
    )
    server = threads["server"]
    server_in_queue = threads["server_in_queue"]
    server_out_queue = threads["server_out_queue"]
    client_in_queue = threads["client_in_queue"]
    client_out_queue = threads["client_out_queue"]

    person_data = {
        "object": "Person",
        "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
        "name": "Danil",
    }

    try:
        wait_until(lambda: len(server.get_clients()) == 1)

        server_in_queue.put(Command(person_data, "Create"))
        result = client_out_queue.get(timeout=10)
        assert result.data == person_data

        client_in_queue.put(Command(person_data, "Create"))
        result = server_out_queue.get(timeout=5)
        assert result.data == person_data
    finally:
        stop_server_and_client(threads)


def test_teamwork_disconnect_on_encryption_mismatch():
    server_cipher = _create_cipher_or_skip("teamwork-shared-key")
    threads = start_server_and_client(
        keepalive_interval=1.0,
        server_cipher=server_cipher,
        client_cipher=None,
    )
    server = threads["server"]
    client_in_queue = threads["client_in_queue"]

    try:
        wait_until(lambda: len(server.get_clients()) == 1)
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
        wait_until(lambda: len(server.get_clients()) == 0, timeout=4)
    finally:
        stop_server_and_client(threads)


def test_teamwork_encrypted_packet_contains_nonce():
    cipher = _create_cipher_or_skip("teamwork-shared-key")
    command = Command(
        {
            "object": "Person",
            "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
            "name": "Danil",
        },
        "Create",
    )
    packet = command.get_packet(cipher)

    header = Header()
    header.unpack_header(packet[: Header.header_size])
    assert header.version == Header.VERSION_AES256_GCM

    encrypted_payload = packet[Header.header_size :]
    decrypted_payload = cipher.decrypt(encrypted_payload)
    assert orjson.loads(decrypted_payload) == command.data


def test_load_teamwork_key_from_file(tmp_path):
    key_file = tmp_path / "teamwork.key"
    key_file.write_text("  teamwork-shared-key  \n", encoding="utf-8")
    assert load_teamwork_key_from_file(str(key_file)) == "teamwork-shared-key"


def test_generate_teamwork_key():
    key = generate_teamwork_key()
    assert key.startswith("hex:")
    assert len(key) == 68
    assert len(normalize_teamwork_key(key)) == 32


def _create_cipher_or_skip(key):
    try:
        return TeamworkCipher(key)
    except TeamworkCryptoError as e:
        pytest.skip(str(e))
