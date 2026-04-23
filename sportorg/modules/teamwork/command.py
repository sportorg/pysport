import socket
from typing import Optional

import orjson

from .crypto import TeamworkCipher
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

    def is_service_keepalive(self) -> bool:
        return self.data is None and self.header.op_type == Operations.Read.value

    def get_packet(self, cipher: Optional[TeamworkCipher] = None) -> bytes:
        pack_data = orjson.dumps(self.data)
        if cipher is not None:
            encrypted_data = cipher.encrypt(pack_data)
            return (
                self.header.pack_header(
                    len(encrypted_data), version=Header.VERSION_AES256_GCM
                )
                + encrypted_data
            )
        return (
            self.header.pack_header(len(pack_data), version=Header.VERSION_PLAIN)
            + pack_data
        )
