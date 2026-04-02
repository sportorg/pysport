## Teamwork

### Overview

Teamwork is a TCP-based client/server synchronization protocol used to exchange race data between SportOrg instances.

- Transport: `TCP`
- Default port: `50010`
- Roles:
  - `server`: accepts multiple clients and relays updates
  - `client`: connects to one server and sends/receives updates

Each message is sent as a binary frame: `Header + payload`.

### Packet Format

`Header` is packed with Python struct format `=2s2H36sLQ` (`54` bytes total):

- `pack_tag` (`2s`): constant `b"SO"`
- `op_type` (`H`): operation code
- `obj_type` (`H`): object type code
- `uuid` (`36s`): object identifier (usually UUID string)
- `version` (`L`): payload format version
  - `0`: plain JSON payload
  - `1`: AES-256-GCM encrypted payload
- `size` (`Q`): payload size in bytes (after encryption if enabled)

Payload:

- Encoded as JSON bytes (`orjson`)
- Most domain messages are JSON objects
- Keepalive uses JSON `null`

### Encryption

Encryption is optional but must match on both sides.

- Algorithm: `AES-256-GCM`
- Encrypted payload format: `nonce(12 bytes) + ciphertext_and_tag`
- If one side expects encrypted packets and receives plain packets (or vice versa), connection is dropped.

Key input supports:

- `hex:<hex-bytes>`
- `base64:<base64-bytes>`
- raw string (UTF-8 bytes)

If decoded key length is not 32 bytes, it is normalized via `SHA-256`.

### Operations and Messages

Operation codes:

- `0 Create`
- `1 Read` (service keepalive)
- `2 Update`
- `3 Delete`
- `4 SyncRace` (reserved/not actively used in current flow)
- `5 GetLock` (reserved)
- `6 ReleaseLoc` (reserved)
- `7 SendRaceId`
- `8 RaceIdMismatch`

Key message payloads:

- `Create` / `Update` / `Delete`: domain object payload with key fields:
  - `object`: object name (`Race`, `Person`, `Result`, etc.)
  - `id`: object UUID
  - other object fields
- `Read` keepalive:
  - payload is `null`
- `SendRaceId`:
  - `object: "Race"`
  - `id`: current client race UUID
- `RaceIdMismatch` (server -> client):
  - `object: "Race"`
  - `id`: server race UUID that client should switch to (after user confirmation in UI)

### Protocol Flow

1. Client connects to server.
1. Client periodically sends keepalive (`Read` with `null`) when no outgoing data exists.
1. Client sends `SendRaceId` after startup.
1. If race ID checking is enabled on server:
   - matching race ID -> client is allowed to sync
   - mismatch -> server sends `RaceIdMismatch`; other client data packets are ignored until a valid `SendRaceId` is received
1. For normal data packets, server:
   - pushes command to local processing queue
   - relays it to all other connected clients except original sender

### Object Type Codes

Main object type mapping in header:

- `0 Race`
- `1 Course`
- `2 Group`
- `3 Organization`
- `4 Person`
- `5 Result`
- `6 ResultManual`
- `7 ResultSportident`
- `8 ResultSFR`
- `9 ResultSportiduino`
- `10 ResultRfidImpinj`
- `11 ResultSrpid`
- `255 Unknown`
