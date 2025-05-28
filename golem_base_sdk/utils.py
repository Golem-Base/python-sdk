"""Utility methods."""

import logging

import rlp
from web3.types import LogReceipt

from .types import (
    Annotation,
    EntityKey,
    ExtendEntityReturnType,
    GenericBytes,
    GolemBaseTransaction,
)

logger = logging.getLogger(__name__)
"""@private"""


def rlp_encode_transaction(tx: GolemBaseTransaction) -> bytes:
    """Encode a Golem Base transaction in RLP."""

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
                lambda el: el.entity_key.generic_bytes,
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
    encoded: bytes = rlp.encode(payload)
    logger.debug("Encoded  payload: %s", encoded)
    return encoded


def parse_legacy_btl_extended_log(log_receipt: LogReceipt) -> ExtendEntityReturnType:
    """
    Parse legacy BTL extended logs.

    For legacy extend ABI types, the type signature in the ABI does
    not correspond to the actual data returned, so we need
    to parse the data ourselves.
    """
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
    data_parsed = int.from_bytes(log_receipt["data"], byteorder="big", signed=False)
    new_expiration_block = data_parsed & ((1 << 256) - 1)
    old_expiration_block = data_parsed >> 256

    return ExtendEntityReturnType(
        old_expiration_block=old_expiration_block,
        new_expiration_block=new_expiration_block,
        entity_key=EntityKey(GenericBytes(log_receipt["topics"][1])),
    )
