#! /usr/bin/env python

"""GolemBase Python SDK"""

import asyncio
import base64
import logging
import logging.config
import typing
from dataclasses import dataclass
from typing import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Iterable,
    List,
    NewType,
    Optional,
    Sequence,
    Set,
    override,
)

import rlp
from eth_typing import ChecksumAddress, HexStr
from web3 import AsyncWeb3, WebSocketProvider
from web3.contract import AsyncContract
from web3.exceptions import ProviderConnectionError
from web3.method import Method, default_root_munger
from web3.middleware import SignAndSendRawMiddlewareBuilder
from web3.types import LogReceipt, RPCEndpoint, TxReceipt
from web3.utils.subscriptions import (
    LogsSubscription,
    LogsSubscriptionContext,
)

__version__ = "0.0.2"


@dataclass(frozen=True)
class GenericBytes:
    """
    GenericBytes
    """

    generic_bytes: bytes

    def as_hex_string(self) -> str:
        """
        as_hex_string
        """
        return "0x" + self.generic_bytes.hex()

    def as_address(self) -> ChecksumAddress:
        """
        as_address
        """
        return AsyncWeb3.to_checksum_address(self.as_hex_string())

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.as_hex_string()})"

    @staticmethod
    def from_hex_string(hexstr: str) -> "GenericBytes":
        """
        from_hex_string
        """
        assert hexstr.startswith("0x")
        assert len(hexstr) % 2 == 0

        return GenericBytes(bytes.fromhex(hexstr[2:]))


EntityKey = NewType("EntityKey", GenericBytes)
Address = NewType("Address", GenericBytes)

INSTANCE_URLS = {
    "demo": {
        "rpc": "https://api.golembase.demo.golem-base.io",
    },
    "local": {
        "rpc": "http://localhost:8545",
    },
    "kaolin": {
        "rpc": "https://rpc.kaolin.holesky.golem-base.io",
        "ws": "wss://ws.rpc.kaolin.holesky.golem-base.io",
    },
}

STORAGE_ADDRESS: Address = Address(
    GenericBytes.from_hex_string("0x0000000000000000000000000000000060138453")
)

GOLEM_BASE_ABI = [
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
    # This can be removed once we retire the kaolin network (the only one using this event hash).
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


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Annotation[V]:
    """
    Annotation
    """

    key: str
    value: V

    @override
    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.key} -> {self.value})"


@dataclass(frozen=True)
class GolemBaseCreate(rlp.Serializable):
    """
    GolemBaseCreate
    """

    data: bytes
    ttl: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class GolemBaseUpdate:
    """
    GolemBaseUpdate
    """

    entity_key: EntityKey
    data: bytes
    ttl: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class GolemBaseDelete:
    """
    GolemBaseDelete
    """

    entity_key: EntityKey


@dataclass(frozen=True)
class GolemBaseExtend:
    """
    GolemBaseExtend
    """

    entity_key: EntityKey
    number_of_blocks: int


@dataclass(frozen=True)
class GolemBaseTransaction:
    """
    GolemBaseTransaction
    """

    def __init__(
        self,
        creates: Optional[Sequence[GolemBaseCreate]] = None,
        updates: Optional[Sequence[GolemBaseUpdate]] = None,
        deletes: Optional[Sequence[GolemBaseDelete]] = None,
        extensions: Optional[Sequence[GolemBaseExtend]] = None,
    ):
        object.__setattr__(self, "creates", creates or [])
        object.__setattr__(self, "updates", updates or [])
        object.__setattr__(self, "deletes", deletes or [])
        object.__setattr__(self, "extensions", extensions or [])

    creates: Sequence[GolemBaseCreate]
    updates: Sequence[GolemBaseUpdate]
    deletes: Sequence[GolemBaseDelete]
    extensions: Sequence[GolemBaseExtend]


@dataclass(frozen=True)
class CreateEntityReturnType:
    """
    CreateEntityReturnType
    """

    expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class UpdateEntityReturnType:
    """
    UpdateEntityReturnType
    """

    expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class ExtendEntityReturnType:
    """
    ExtendEntityReturnType
    """

    old_expiration_block: int
    new_expiration_block: int
    entity_key: EntityKey


@dataclass(frozen=True)
class GolemBaseTransactionReceipt:
    """
    GolemBaseTransactionReceipt
    """

    creates: Sequence[CreateEntityReturnType]
    updates: Sequence[UpdateEntityReturnType]
    extensions: Sequence[ExtendEntityReturnType]
    deletes: Sequence[EntityKey]


@dataclass(frozen=True)
class EntityMetadata:
    """
    EntityMetadata
    """

    entity_key: EntityKey
    owner: Address
    expires_at_block: int
    string_annotations: Sequence[Annotation[str]]
    numeric_annotations: Sequence[Annotation[int]]


@dataclass(frozen=True)
class QueryEntitiesResult:
    """
    QueryEntitiesResult
    """

    entity_key: EntityKey
    storage_value: bytes


class GolemBaseClient:
    """
    GolemBaseClient
    """

    _http_client: AsyncWeb3
    _ws_client: AsyncWeb3
    golem_base_contract: AsyncContract
    background_tasks: Set[asyncio.Task]

    @staticmethod
    async def create(
        rpc_url: str, ws_url: str, private_key: Sequence[bytes]
    ) -> "GolemBaseClient":
        """
        create: async constructor
        """
        ws_client = await AsyncWeb3(WebSocketProvider(ws_url))
        return GolemBaseClient(rpc_url, ws_client, private_key)

    def __init__(
        self, rpc_url: str, ws_client: AsyncWeb3, private_key: Sequence[bytes]
    ) -> None:
        self._http_client = GolemBaseClient.__create_client(rpc_url)
        self._ws_client = ws_client

        # Keep references to async tasks we created
        self.background_tasks = set()

        def is_connected(client) -> Callable[[bool], Awaitable[bool]]:
            async def inner(show_traceback: bool) -> bool:
                try:
                    logger.debug("Calling eth_blockNumber to test connectivity...")
                    await client.eth.get_block_number()
                    return True
                except (OSError, ProviderConnectionError) as e:
                    logger.debug(
                        "Problem connecting to provider", exc_info=show_traceback
                    )
                    if show_traceback:
                        raise ProviderConnectionError(
                            "Problem connecting to provider"
                        ) from e
                    return False

            return inner

        # The default is_connected method calls web3_clientVersion, but the web3
        # API is not enabled on all our nodes, so let's monkey patch this to call
        # eth_getBlockNumber instead.
        # The method on the provider is usually not called directly, instead you
        # can call the eponymous method on the client, which will delegate to the
        # provider.
        setattr(
            self.http_client().provider,
            "is_connected",
            is_connected(self.http_client()),
        )

        # Allow caching of certain methods to improve performance
        self.http_client().provider.cache_allowed_requests = True

        # Set up the ethereum account
        self.account = self.http_client().eth.account.from_key(private_key)
        # Inject a middleware that will sign transactions with the account that we created
        self.http_client().middleware_onion.inject(
            # pylint doesn't detect nested @curry annotations properly...
            # pylint: disable=no-value-for-parameter
            SignAndSendRawMiddlewareBuilder.build(self.account),
            layer=0,
        )
        # Set the account as the default, so we don't need to specify the from field
        # every time
        self.http_client().eth.default_account = self.account.address
        logger.debug("Using account: %s", self.account.address)

        # https://github.com/pylint-dev/pylint/issues/3162
        # pylint: disable=no-member
        self.golem_base_contract = self.http_client().eth.contract(
            address=STORAGE_ADDRESS.as_address(),
            abi=GOLEM_BASE_ABI,
        )
        for event in self.golem_base_contract.all_events():
            logger.debug(
                "Registered event %s with hash %s", event.signature, event.topic
            )

    @staticmethod
    def __create_client(rpc_url: str) -> AsyncWeb3:
        """
        create_client
        """
        client = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(rpc_url, request_kwargs={"timeout": 60}),
        )
        client.eth.attach_methods(
            {
                "get_storage_value": Method(
                    json_rpc_method=RPCEndpoint("golembase_getStorageValue"),
                    mungers=[default_root_munger],
                ),
                "get_entity_metadata": Method(
                    json_rpc_method=RPCEndpoint("golembase_getEntityMetaData"),
                    mungers=[default_root_munger],
                ),
                "get_entities_to_expire_at_block": Method(
                    json_rpc_method=RPCEndpoint("golembase_getEntitiesToExpireAtBlock"),
                    mungers=[default_root_munger],
                ),
                "get_entity_count": Method(
                    json_rpc_method=RPCEndpoint("golembase_getEntityCount"),
                    mungers=[default_root_munger],
                ),
                "get_all_entity_keys": Method(
                    json_rpc_method=RPCEndpoint("golembase_getAllEntityKeys"),
                    mungers=[default_root_munger],
                ),
                "get_entities_of_owner": Method(
                    json_rpc_method=RPCEndpoint("golembase_getEntitiesOfOwner"),
                    mungers=[default_root_munger],
                ),
                "query_entities": Method(
                    json_rpc_method=RPCEndpoint("golembase_queryEntities"),
                    mungers=[default_root_munger],
                ),
            }
        )
        return client

    def http_client(self):
        """
        http_client
        """
        return self._http_client

    def ws_client(self) -> AsyncWeb3:
        """
        ws_client
        """
        return self._ws_client

    async def is_connected(self) -> bool:
        """
        is_connected
        """
        return await self.http_client().is_connected()

    async def disconnect(self) -> None:
        """
        disconnect
        """
        await self.http_client().provider.disconnect()
        await self.ws_client().subscription_manager.unsubscribe_all()
        await self.ws_client().provider.disconnect()

    def get_account_address(self) -> ChecksumAddress:
        """
        get_account_address
        """
        return self.account.address

    async def get_storage_value(self, entity_key: EntityKey) -> bytes:
        """
        get_storage_value
        """
        return base64.b64decode(
            await self.http_client().eth.get_storage_value(entity_key.as_hex_string())
        )

    async def get_entity_metadata(self, entity_key: EntityKey) -> EntityMetadata:
        """
        get_entity_metadata
        """
        metadata = await self.http_client().eth.get_entity_metadata(
            entity_key.as_hex_string()
        )

        return EntityMetadata(
            entity_key=entity_key,
            owner=Address(GenericBytes.from_hex_string(metadata.owner)),
            expires_at_block=metadata.expiresAtBlock,
            string_annotations=list(
                map(
                    lambda ann: Annotation(key=ann["key"], value=ann["value"]),
                    metadata.stringAnnotations,
                )
            ),
            numeric_annotations=list(
                map(
                    lambda ann: Annotation(key=ann["key"], value=ann["value"]),
                    metadata.numericAnnotations,
                )
            ),
        )

    async def get_entities_to_expire_at_block(
        self, block_number: int
    ) -> Iterable[EntityKey]:
        """
        get_entities_to_expire_at_block
        """
        return list(
            map(
                lambda e: EntityKey(GenericBytes.from_hex_string(e)),
                await self.http_client().eth.get_entities_to_expire_at_block(
                    block_number
                ),
            )
        )

    async def get_entity_count(self) -> int:
        """
        get_entity_count
        """
        return await self.http_client().eth.get_entity_count()

    async def get_all_entity_keys(self) -> Sequence[EntityKey]:
        """
        get_entity_keys
        """
        return list(
            map(
                lambda e: EntityKey(GenericBytes.from_hex_string(e)),
                await self.http_client().eth.get_all_entity_keys(),
            )
        )

    async def get_entities_of_owner(self, owner: Address) -> Sequence[EntityKey]:
        """
        get_entities_of_owner
        """
        return list(
            map(
                lambda e: EntityKey(GenericBytes.from_hex_string(e)),
                # https://github.com/pylint-dev/pylint/issues/3162
                # pylint: disable=no-member
                await self.http_client().eth.get_entities_of_owner(owner),
            )
        )

    async def query_entities(self, query: str) -> Sequence[QueryEntitiesResult]:
        """
        query_entities
        """
        return list(
            map(
                lambda result: QueryEntitiesResult(
                    entity_key=result.key, storage_value=base64.b64decode(result.value)
                ),
                await self.http_client().eth.query_entities(query),
            )
        )

    # remaining 3 RPC methods

    async def create_entities(
        self,
        creates: Sequence[GolemBaseCreate],
    ) -> Iterable[CreateEntityReturnType]:
        """
        create_entities
        """
        return (await self.send_transaction(creates=creates)).creates

    async def update_entities(
        self,
        updates: Sequence[GolemBaseUpdate],
    ) -> Iterable[UpdateEntityReturnType]:
        """
        update_entities
        """
        return (await self.send_transaction(updates=updates)).updates

    async def delete_entities(
        self,
        deletes: Sequence[GolemBaseDelete],
    ) -> Iterable[EntityKey]:
        """
        delete_entities
        """
        return (await self.send_transaction(deletes=deletes)).deletes

    async def extend_entities(
        self,
        extensions: Sequence[GolemBaseExtend],
    ) -> Iterable[ExtendEntityReturnType]:
        """
        extend_entities
        """
        return (await self.send_transaction(extensions=extensions)).extensions

    async def send_transaction(
        self,
        creates: Optional[Sequence[GolemBaseCreate]] = None,
        updates: Optional[Sequence[GolemBaseUpdate]] = None,
        deletes: Optional[Sequence[GolemBaseDelete]] = None,
        extensions: Optional[Sequence[GolemBaseExtend]] = None,
    ) -> GolemBaseTransactionReceipt:
        """
        send_transaction
        """
        tx = GolemBaseTransaction(
            creates,
            updates,
            deletes,
            extensions,
        )
        return await self.__send_gb_transaction(tx)

    async def __process_golem_base_log_receipt(
        self,
        log_receipt: LogReceipt,
    ) -> GolemBaseTransactionReceipt:
        # Read the first entry of the topics array,
        # which is the hash of the event signature, identifying the event
        topic = AsyncWeb3.to_hex(log_receipt["topics"][0])
        # Look up the corresponding event
        # If there is no such event in the ABI, it probably needs to be added
        event = self.golem_base_contract.get_event_by_topic(topic)
        # Use the event to process the whole log
        event_data = event.process_log(log_receipt)

        creates: List[CreateEntityReturnType] = []
        updates: List[UpdateEntityReturnType] = []
        deletes: List[EntityKey] = []
        extensions: List[ExtendEntityReturnType] = []

        match event_data["event"]:
            case "GolemBaseStorageEntityCreated":
                creates.append(
                    CreateEntityReturnType(
                        expiration_block=event_data["args"]["expirationBlock"],
                        entity_key=EntityKey(
                            GenericBytes(
                                event_data["args"]["entityKey"].to_bytes(32, "big")
                            )
                        ),
                    )
                )
            case "GolemBaseStorageEntityUpdated":
                updates.append(
                    UpdateEntityReturnType(
                        expiration_block=event_data["args"]["expirationBlock"],
                        entity_key=EntityKey(
                            GenericBytes(
                                event_data["args"]["entityKey"].to_bytes(32, "big")
                            )
                        ),
                    )
                )
            case "GolemBaseStorageEntityDeleted":
                deletes.append(
                    EntityKey(
                        GenericBytes(
                            event_data["args"]["entityKey"].to_bytes(32, "big")
                        ),
                    )
                )
            case "GolemBaseStorageEntityBTLExtended":
                extensions.append(
                    ExtendEntityReturnType(
                        old_expiration_block=event_data["args"]["old_expirationBlock"],
                        new_expiration_block=event_data["args"]["new_expirationBlock"],
                        entity_key=EntityKey(
                            GenericBytes(
                                event_data["args"]["entityKey"].to_bytes(32, "big")
                            )
                        ),
                    )
                )
            # This is only here for backwards compatibility and can be removed
            # once we undeploy kaolin.
            case (
                "GolemBaseStorageEntityBTLExptended"
                | "GolemBaseStorageEntityTTLExptended"
            ):
                # For these types, the type signature in the ABI does
                # not correspond to the actual data returned, so we need
                # to parse the data ourselves.
                def parse_log(log_receipt: LogReceipt) -> ExtendEntityReturnType:
                    # pylint: disable=line-too-long
                    # Take the first 64 bytes by masking the rest
                    # (shift 1 to the left 256 positions, then negate the number)
                    # Example:
                    # 0x 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 012f
                    #    0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0143
                    # mask this with:
                    # 0x 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000
                    #    1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111 1111
                    # to obtain 0x143
                    # and then shift the original number to the right
                    # by 256 to obtain 0x12f
                    data_parsed = int.from_bytes(
                        log_receipt["data"], byteorder="big", signed=False
                    )
                    new_expiration_block = data_parsed & ((1 << 256) - 1)
                    old_expiration_block = data_parsed >> 256

                    return ExtendEntityReturnType(
                        old_expiration_block=old_expiration_block,
                        new_expiration_block=new_expiration_block,
                        entity_key=EntityKey(GenericBytes(log_receipt["topics"][1])),
                    )

                extensions.append(parse_log(log_receipt))
            case other:
                raise ValueError(f"Unknown event type: {other}")

        return GolemBaseTransactionReceipt(
            creates=creates,
            updates=updates,
            deletes=deletes,
            extensions=extensions,
        )

    async def __process_golem_base_receipt(
        self, receipt: TxReceipt
    ) -> GolemBaseTransactionReceipt:
        # There doesn't seem to be a method for this in the web3 lib.
        # The only option in the lib is to iterate over the events in the ABI
        # and call process_receipt on each of them to try and decode the logs.
        # This is inefficient though compared to reading the actual topic signature
        # and immediately selecting the right event from the ABI, which is what
        # we do here.
        async def process_receipt(
            receipt: TxReceipt,
        ) -> AsyncGenerator[GolemBaseTransactionReceipt, None]:
            for log in receipt["logs"]:
                yield await self.__process_golem_base_log_receipt(log)

        creates: List[CreateEntityReturnType] = []
        updates: List[UpdateEntityReturnType] = []
        deletes: List[EntityKey] = []
        extensions: List[ExtendEntityReturnType] = []

        async for res in process_receipt(receipt):
            creates.extend(res.creates)
            updates.extend(res.updates)
            deletes.extend(res.deletes)
            extensions.extend(res.extensions)

        return GolemBaseTransactionReceipt(
            creates=creates,
            updates=updates,
            deletes=deletes,
            extensions=extensions,
        )

    async def __send_gb_transaction(
        self, tx: GolemBaseTransaction
    ) -> GolemBaseTransactionReceipt:
        txhash = await self.http_client().eth.send_transaction(
            {
                # https://github.com/pylint-dev/pylint/issues/3162
                # pylint: disable=no-member
                "to": STORAGE_ADDRESS.as_address(),
                "value": AsyncWeb3.to_wei(0, "ether"),
                "data": self.__create_payload(tx),
            }
        )
        receipt = await self.http_client().eth.wait_for_transaction_receipt(txhash)
        return await self.__process_golem_base_receipt(receipt)

    def __create_payload(self, tx: GolemBaseTransaction) -> bytes:
        def format_annotation[T](annotation: Annotation[T]) -> tuple[str, T]:
            return (annotation.key, annotation.value)

        # Turn the transaction into a simple list of basic types that can be
        # RLP encoded
        payload = [
            # Create
            list(
                map(
                    lambda el: [
                        el.ttl,
                        el.data,
                        list(map(format_annotation, el.string_annotations)),
                        list(map(format_annotation, el.numeric_annotations)),
                    ],
                    tx.creates,
                )
            ),
            # Update
            list(
                map(
                    lambda el: [
                        el.entity_key.generic_bytes,
                        el.ttl,
                        el.data,
                        list(map(format_annotation, el.string_annotations)),
                        list(map(format_annotation, el.numeric_annotations)),
                    ],
                    tx.updates,
                )
            ),
            # Delete
            list(
                map(
                    lambda el: [
                        el.entity_key.generic_bytes,
                    ],
                    tx.deletes,
                )
            ),
            # Extend
            list(
                map(
                    lambda el: [
                        el.entity_key.generic_bytes,
                        el.number_of_blocks,
                    ],
                    tx.extensions,
                )
            ),
        ]
        logger.debug("Payload before RLP encoding: %s", payload)
        encoded = rlp.encode(payload)
        logger.debug(encoded)
        return encoded

    async def watch_logs(
        self,
        create_callback: Callable[[CreateEntityReturnType], None],
        update_callback: Callable[[UpdateEntityReturnType], None],
        delete_callback: Callable[[EntityKey], None],
        extend_callback: Callable[[ExtendEntityReturnType], None],
    ) -> None:
        """
        watch_logs
        """

        async def log_handler(
            handler_context: LogsSubscriptionContext,
        ) -> None:
            # We only use this handler for log receipts
            # TypeDicts cannot be checked at runtime
            log_receipt = typing.cast(LogReceipt, handler_context.result)
            logger.debug("New log: %s", log_receipt)
            res = await self.__process_golem_base_log_receipt(log_receipt)

            for create in res.creates:
                create_callback(create)
            for update in res.updates:
                update_callback(update)
            for key in res.deletes:
                delete_callback(key)
            for extension in res.extensions:
                extend_callback(extension)

        def create_subscription(topic: HexStr) -> LogsSubscription:
            return LogsSubscription(
                label=f"Golem Base subscription to topic {topic}",
                address=self.golem_base_contract.address,
                topics=[topic],
                handler=log_handler,
                # optional `handler_context` args to help parse a response
                handler_context={},
            )

        async def handle_subscriptions() -> None:
            await self._ws_client.subscription_manager.subscribe(
                list(
                    map(
                        lambda event: create_subscription(event.topic),
                        self.golem_base_contract.all_events(),
                    )
                ),
            )
            # handle subscriptions via configured handlers:
            await self.ws_client().subscription_manager.handle_subscriptions()

        # Create a long running task to handle subscriptions that we can run on
        # the asyncio event loop
        task = asyncio.create_task(handle_subscriptions())
        self.background_tasks.add(task)

        def task_done(task: asyncio.Task) -> None:
            logger.info("Subscription background task done, removing...")
            self.background_tasks.discard(task)

        task.add_done_callback(task_done)
