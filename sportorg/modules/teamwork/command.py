import socket
from typing import Optional

import orjson

from .packet_header import Header, ObjectTypes, Operations


class Command:
    def __init__(
        self,
        data=None,
        op=Operations.Update.name,
        sender: Optional[socket.socket] = None,
    ):
        self.data = data
        self.header = Header(data, op)
        self.next_cmd_obj_type = ObjectTypes.Unknown.value
        self._sender = sender

    def __repr__(self) -> str:
        return str(self.data)

    def is_sender(self, sender: socket.socket) -> bool:
        return self._sender is sender

    def get_packet(self) -> bytes:
        pack_data = orjson.dumps(self.data)
        return self.header.pack_header(len(pack_data)) + pack_data
