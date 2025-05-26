"""Constants used in the Golem Base SDK."""

from collections.abc import Sequence
from typing import Any, Final

from .types import (
    Address,
    GenericBytes,
)

STORAGE_ADDRESS: Final[Address] = Address(
    GenericBytes.from_hex_string("0x0000000000000000000000000000000060138453")
)

GOLEM_BASE_ABI: Final[Sequence[dict[str, Any]]] = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "entityKey", "type": "uint256"},
            {"indexed": False, "name": "expirationBlock", "type": "uint256"},
        ],
        "name": "GolemBaseStorageEntityCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "entityKey", "type": "uint256"},
            {"indexed": False, "name": "expirationBlock", "type": "uint256"},
        ],
        "name": "GolemBaseStorageEntityUpdated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [{"indexed": True, "name": "entityKey", "type": "uint256"}],
        "name": "GolemBaseStorageEntityDeleted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "entityKey", "type": "uint256"},
            {"indexed": False, "name": "oldExpirationBlock", "type": "uint256"},
            {"indexed": False, "name": "newExpirationBlock", "type": "uint256"},
        ],
        "name": "GolemBaseStorageEntityBTLExtended",
        "type": "event",
    },
    # Old ABI event that has a typo in the name and a missing non-indexed argument.
    # This can be removed once we retire the kaolin network (the only one using
    # this event hash).
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "entityKey", "type": "uint256"},
            {"indexed": False, "name": "expirationBlock", "type": "uint256"},
        ],
        "name": "GolemBaseStorageEntityBTLExptended",
        "type": "event",
    },
    # Old ABI before rename of TTL -> BTL
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "entityKey", "type": "uint256"},
            {"indexed": False, "name": "expirationBlock", "type": "uint256"},
        ],
        "name": "GolemBaseStorageEntityTTLExptended",
        "type": "event",
    },
]
