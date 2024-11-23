import logging
import time
from queue import Queue
from threading import Event

from sportorg.modules.teamwork.client import ClientThread
from sportorg.modules.teamwork.server import Command, ServerThread


def test_teamwork():
    in_queue = Queue()
    out_queue = Queue()
    event = Event()
    server = ServerThread(("0.0.0.0", 50010), in_queue, out_queue, event, logging.root)
    server.start()
    server.wait()
    client_in_queue = Queue()
    client_out_queue = Queue()
    client = ClientThread(
        ("localhost", 50010), client_in_queue, client_out_queue, event, logging.root
    )
    client.start()
    client.wait()
    time.sleep(5)

    in_queue.put(
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
    result = out_queue.get(timeout=5)
    assert result.data == {
        "object": "Person",
        "id": "c24eef6c-a33b-4581-a6d1-78294711aef1",
        "name": "Danil",
    }

    event.set()
    server.join()
    client.join()
