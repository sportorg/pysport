import base64
import binascii
import hashlib
import os
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ModuleNotFoundError:  # pragma: no cover - depends on runtime environment
    AESGCM = None


class TeamworkCryptoError(Exception):
    pass


class TeamworkCipher:
    NONCE_SIZE = 12
    KEY_SIZE = 32

    def __init__(self, raw_key: str):
        if AESGCM is None:
            raise TeamworkCryptoError(
                "Teamwork encryption requires the 'cryptography' package"
            )
        self._key = normalize_teamwork_key(raw_key)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(self.NONCE_SIZE)
        encrypted = self._aesgcm.encrypt(nonce, data, None)
        return nonce + encrypted

    def decrypt(self, data: bytes) -> bytes:
        if len(data) <= self.NONCE_SIZE:
            raise TeamworkCryptoError("Invalid encrypted teamwork packet")
        nonce = data[: self.NONCE_SIZE]
        encrypted = data[self.NONCE_SIZE :]
        try:
            return self._aesgcm.decrypt(nonce, encrypted, None)
        except Exception as e:
            raise TeamworkCryptoError("Failed to decrypt teamwork packet") from e


def normalize_teamwork_key(raw_key: str) -> bytes:
    value = raw_key.strip()
    if not value:
        raise TeamworkCryptoError("Teamwork encryption key is empty")

    decoded = _decode_key(value)
    if len(decoded) == TeamworkCipher.KEY_SIZE:
        return decoded
    return hashlib.sha256(decoded).digest()


def load_teamwork_key_from_file(path: str) -> str:
    key = Path(path).read_text(encoding="utf-8").strip()
    if not key:
        raise TeamworkCryptoError("Teamwork key file is empty")
    return key


def generate_teamwork_key() -> str:
    return "hex:{}".format(os.urandom(TeamworkCipher.KEY_SIZE).hex())


def _decode_key(value: str) -> bytes:
    if value.startswith("hex:"):
        raw = value[4:].strip()
        try:
            return bytes.fromhex(raw)
        except ValueError as e:
            raise TeamworkCryptoError("Invalid hex teamwork key") from e

    if value.startswith("base64:"):
        raw = value[7:].strip()
        try:
            return base64.b64decode(raw, validate=True)
        except (ValueError, binascii.Error) as e:
            raise TeamworkCryptoError("Invalid base64 teamwork key") from e

    if len(value) == 64:
        try:
            return bytes.fromhex(value)
        except ValueError:
            pass

    return value.encode("utf-8")
