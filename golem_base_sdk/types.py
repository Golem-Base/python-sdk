"""Golem Base SDK Types."""

from collections.abc import Callable, Coroutine, Sequence
from dataclasses import dataclass
from typing import (
    Any,
    NewType,
    override,
)

from eth_typing import ChecksumAddress, HexStr
from web3 import AsyncWeb3
from web3.types import Wei


@dataclass(frozen=True)
class GenericBytes:
    """Class to represent bytes that can be converted to more meaningful types."""

    generic_bytes: bytes

    def as_hex_string(self) -> HexStr:
        """Convert this instance to a hexadecimal string."""
        return HexStr("0x" + self.generic_bytes.hex())

    def as_address(self) -> ChecksumAddress:
        """Convert this instance to a `eth_typing.ChecksumAddress`."""
        return AsyncWeb3.to_checksum_address(self.as_hex_string())

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.as_hex_string()})"

    @staticmethod
    def from_hex_string(hexstr: str) -> "GenericBytes":
        """Create a `GenericBytes` instance from a hexadecimal string."""
        assert hexstr.startswith("0x")
        assert len(hexstr) % 2 == 0

        return GenericBytes(bytes.fromhex(hexstr[2:]))


EntityKey = NewType("EntityKey", GenericBytes)
Address = NewType("Address", GenericBytes)


@dataclass(frozen=True)
class Annotation[V]:
    """Helper class for constructing annotations. Represents an annotation key-value pair to attach to an entity.

    This is a generic class that can be used to create annotations for entities,
    such as `Annotation[str]` or `Annotation[int]`.

    Type Parameters:
        V: The value type (commonly `str` or `int`).

    Use:
        Include as `string_annotations` (Annotation[str]) or `numeric_annotations` (Annotation[int]) when creating or updating entities.
    """
    

    key: str
    value: V

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.key} -> {self.value})"


@dataclass(frozen=True)
class GolemBaseCreate:
    """Helper class for creating entities.

    An instance of this class specifies the data to fill an entity with. You can
    pass an array of these instances into the `create_entities` method to create
    one or more entities.

    Members:
        data (bytes): The raw data or payload to be saved.
        ttl (int): The number of blocks to live.
        string_annotations (Sequence[Annotation[str]]): Key-value pairs where the value is a string.
        numeric_annotations (Sequence[Annotation[int]]): Key-value pairs where the value is a number.

    Note:
        `ttl` will be deprecated and replaced with `btl` (for "blocks to live").
    """

    data: bytes
    ttl: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class GolemBaseUpdate:
    """Helper class for updating existing entities.

    An instance of this class specifies the data to replace an existing entity with.
    You can pass an array of these instances into the `update_entities` method to
    update one or more entities.

    Members:
        entity_key (EntityKey): The key of the existing entity to update.
        data (bytes): The raw data or payload to be saved.
        ttl (int): The number of blocks to live.
        string_annotations (Sequence[Annotation[str]]): Key-value pairs where the value is a string.
        numeric_annotations (Sequence[Annotation[int]]): Key-value pairs where the value is a number.

    Note:
        `ttl` will be deprecated and replaced with `btl` (for "blocks to live").
    """

    entity_key: EntityKey
    data: bytes
    ttl: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class GolemBaseDelete:
    """Helper class for deleting entities.

    An instance of this class specifies the key of an entity to delete. You can
    pass an array of these instances into the `delete_entities` method to delete
    one or more entities.

    Members:
        entity_key (EntityKey): The key of the existing entity to update.
    """

    entity_key: EntityKey


@dataclass(frozen=True)
class GolemBaseExtend:
    """Helper class for extending the time to live for existing entities.

    An instance of this class specifies the key of an entity to extend and the
    number of blocks to extend it by. You can pass an array of these instances
    into the `extend_entities` method.

    Members:
        entity_key (EntityKey): The key of the existing entity to update.
        number_of_blocks (int): The number of blocks by which to extend the entity's time to live.
    """

    entity_key: EntityKey
    number_of_blocks: int


@dataclass(frozen=True)
class GolemBaseTransaction:
    """Represents a single transaction to pass to an op-geth node.

    This class can include any combination of creates, deletes, updates, and
    extensions, each as an array of size zero or more.

    Members:
        creates (Sequence[GolemBaseCreate] | None = None, optional): A list of entity creation structures. 
        updates (Sequence[GolemBaseUpdate] | None = None, optional): A list of entity update structures.
        deletes (Sequence[GolemBaseDelete] | None = None, optional): A list of entity delete structures.
        extensions (Sequence[GolemBaseExtend] | None = None, optional): A list of entity block extension structures.
        gas (int | None, optional): The maximum amount of gas to spend. Defaults to None.
        maxFeePerGas (Wei | None, optional): The amount of Wei to spend per gas unit. Defaults to None.
        maxPriorityFeePerGas (Wei | None, optional): The tip amount. Defaults to None.

    """

    def __init__(
        self,
        *,
        creates: Sequence[GolemBaseCreate] | None = None,
        updates: Sequence[GolemBaseUpdate] | None = None,
        deletes: Sequence[GolemBaseDelete] | None = None,
        extensions: Sequence[GolemBaseExtend] | None = None,
        gas: int | None = None,
        maxFeePerGas: Wei | None = None,
        maxPriorityFeePerGas: Wei | None = None,
    ):
        """Initialise the GolemBaseTransaction instance."""
        object.__setattr__(self, "creates", creates or [])
        object.__setattr__(self, "updates", updates or [])
        object.__setattr__(self, "deletes", deletes or [])
        object.__setattr__(self, "extensions", extensions or [])
        object.__setattr__(self, "gas", gas)
        object.__setattr__(self, "maxFeePerGas", maxFeePerGas)
        object.__setattr__(self, "maxPriorityFeePerGas", maxPriorityFeePerGas)

    creates: Sequence[GolemBaseCreate]
    updates: Sequence[GolemBaseUpdate]
    deletes: Sequence[GolemBaseDelete]
    extensions: Sequence[GolemBaseExtend]
    gas: int | None
    maxFeePerGas: Wei | None
    maxPriorityFeePerGas: Wei | None


@dataclass(frozen=True)
class CreateEntityReturnType:
    """Represents the return type of `create_entities`.

    It consists of the key of the created entity and the expiration block number.
    The `create_entities` method returns an array of `CreateEntityReturnType` instances,
    one for each entity created.

    Members:
        entity_key (EntityKey): The key assigned to the created entity.
        expiration_block (int): The block number when the entity will expire.
    """

    expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class UpdateEntityReturnType:
    """Represents the return type of `update_entity`.

    It consists of the key of the updated entity and the expiration block.

    Members:
        entity_key (EntityKey): The key assigned to the created entity.
        expiration_block (int): The block number when the entity will expire.
    """

    expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class ExtendEntityReturnType:
    """Represents the return type of `extend_entity`.

    It consists of the key of the extended entity, the old expiration block, and
    the new expiration block.

    Members:
        entity_key (EntityKey): The key assigned to the created entity.
        old_expiration_block (int): The expiration block before the update.
        new_expiration_block (int): The new expiration block after the update.
    """

    old_expiration_block: int
    new_expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class GolemBaseTransactionReceipt:
    """The return type of a Golem Base transaction.
    
    Members:
        creates (Sequence[CreateEntityReturnType]): A list of entity creation return receipts.
        updates (Sequence[UpdateEntityReturnType]): A list of entity update return receipts.
        extensions (Sequence[ExtendEntityReturnType]): A list of entity extensinon return receipts.
        deletes (Sequence[EntityKey]):  A list of entity delete return receipts.    
    """

    creates: Sequence[CreateEntityReturnType]
    updates: Sequence[UpdateEntityReturnType]
    extensions: Sequence[ExtendEntityReturnType]
    deletes: Sequence[EntityKey]


@dataclass(frozen=True)
class EntityMetadata:
    ## class EntityMetadata
    """Represents the metadata for an entity.

    An instance of this class is returned by the `get_entity_metadata` function.

    Members:
        entity_key (EntityKey): The key (hash) of the entity.
        owner (Address): The owner of the entity.
        expires_at_block (int): The block at which this entity will expire.
        string_annotations (Sequence[Annotation[str]]): A list of string annotations in key/value format.
        numeric_annotations (Sequence[Annotation[int]]): A list of numeric annotations in key/value format.

    """
    entity_key: EntityKey
    owner: Address
    expires_at_block: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class QueryEntitiesResult:
    """A class representing the return value of a Golem Base query."""

    entity_key: EntityKey
    storage_value: bytes


@dataclass(frozen=True)
class WatchLogsHandle:
    """
    Class returned by `GolemBaseClient.watch_logs`.

    Allows you to unsubscribe from the associated subscription.
    """

    _unsubscribe: Callable[[], Coroutine[Any, Any, None]]

    async def unsubscribe(self) -> None:
        """Unsubscribe from this subscription."""
        await self._unsubscribe()
