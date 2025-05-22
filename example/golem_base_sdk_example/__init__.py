#! /usr/bin/env python

"""GolemBase Python SDK"""

import argparse
import asyncio
import logging
import logging.config

from xdg import BaseDirectory

from golem_base_sdk import (
    Annotation,
    GolemBaseClient,
    GolemBaseCreate,
    GolemBaseDelete,
    GolemBaseExtend,
    GolemBaseUpdate,
)

__version__ = "0.0.1"

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            # "": {"level": "DEBUG", "handlers": ["console"]},
            "": {"level": "INFO", "handlers": ["console"]},
        },
        # Avoid pre-existing loggers from imports being disabled
        "disable_existing_loggers": False,
    }
)
logger = logging.getLogger(__name__)

INSTANCE_URLS = {
    "demo": {
        "rpc": "https://api.golembase.demo.golem-base.io",
    },
    "local": {
        "rpc": "http://localhost:8545",
        "ws": "ws://localhost:8545",
    },
    "kaolin": {
        "rpc": "https://rpc.kaolin.holesky.golem-base.io",
        "ws": "wss://ws.rpc.kaolin.holesky.golem-base.io",
    },
}


async def run_example(instance: str) -> None:
    """
    connect
    """

    with open(
        BaseDirectory.xdg_config_home + "/golembase/private.key",
        "rb",
    ) as private_key_file:
        key_bytes = private_key_file.readline()

    client = await GolemBaseClient.create(
        rpc_url=INSTANCE_URLS[instance]["rpc"],
        ws_url=INSTANCE_URLS[instance]["ws"],
        private_key=key_bytes,
    )

    await client.watch_logs(
        lambda create: logger.info(
            """\n
Got create event: %s
        """,
            create,
        ),
        lambda update: logger.info(
            """\n
Got update event: %s
        """,
            update,
        ),
        lambda deleted_key: logger.info(
            """\n
Got delete event: %s
        """,
            deleted_key,
        ),
        lambda extension: logger.info(
            """\n
Got extend event: %s
        """,
            extension,
        ),
    )

    if await client.is_connected():
        block = await client.http_client().eth.get_block("latest")

        logger.info("""\n
        *****************************
        * Checking basic methods... *
        *****************************
        """)

        logger.info("Retrieved block %s", block.number)

        logger.info("entity count: %s", await client.get_entity_count())

        logger.info("""\n
        *************************
        * Creating an entity... *
        *************************
        """)

        create_receipt = await client.create_entities(
            [GolemBaseCreate(b"hello", 60, [Annotation("app", "demo")], [])]
        )
        entity_key = create_receipt[0].entity_key
        logger.info("receipt: %s", create_receipt)
        logger.info("entity count: %s", await client.get_entity_count())

        logger.info("created entity with key %s", entity_key)
        logger.info("storage value: %s", await client.get_storage_value(entity_key))
        metadata = await client.get_entity_metadata(entity_key)
        logger.info("entity metadata: %s", metadata)

        logger.info("""\n
        ***********************************
        * Extend the BTL of the entity... *
        ***********************************
        """)

        logger.info(
            "entities to expire at block: %s",
            await client.get_entities_to_expire_at_block(metadata.expires_at_block),
        )

        extend_receipt = await client.extend_entities([GolemBaseExtend(entity_key, 60)])
        logger.info("receipt: %s", extend_receipt)

        logger.info(
            "entities to expire at block: %s",
            await client.get_entities_to_expire_at_block(metadata.expires_at_block),
        )
        logger.info("entity metadata: %s", await client.get_entity_metadata(entity_key))

        logger.info("""\n
        ************************
        * Update the entity... *
        ************************
        """)

        update_receipt = await client.update_entities(
            [GolemBaseUpdate(entity_key, b"hello", 60, [Annotation("app", "demo")], [])]
        )
        logger.info("receipt: %s", update_receipt)
        entity_key = update_receipt[0].entity_key

        logger.info("entity metadata: %s", await client.get_entity_metadata(entity_key))

        logger.info("""\n
        *************************
        * Query for entities... *
        *************************
        """)

        query_result = await client.query_entities('app = "demo"')
        logger.info("Query result: %s", query_result)

        logger.info("""\n
        ************************
        * Delete the entity... *
        ************************
        """)

        logger.info("entity metadata: %s", await client.get_entity_metadata(entity_key))
        receipt = await client.delete_entities([GolemBaseDelete(entity_key)])
        logger.info("receipt: %s", receipt)

        logger.info(
            "My entities: %s",
            await client.get_entities_of_owner(client.get_account_address()),
        )

        logger.info(
            "All entities: %s",
            await client.get_all_entity_keys(),
        )
    else:
        logger.warning("Could not connect to the API...")

    await client.disconnect()


def main() -> None:
    """
    main
    """
    parser = argparse.ArgumentParser(description="GolemBase Python SDK Example")
    parser.add_argument(
        "--instance",
        choices=INSTANCE_URLS.keys(),
        default="kaolin",
        help="Which instance to connect to (default: kaolin)",
    )
    args = parser.parse_args()
    logger.info("Starting main loop")
    asyncio.run(run_example(args.instance))


if __name__ == "__main__":
    main()
