#! /usr/bin/env python

"""GolemBase Python SDK"""

import asyncio
import logging
import logging.config

from xdg import BaseDirectory

from golem_base_sdk import Annotation, GolemBaseClient, GolemBaseCreate, GolemBaseExtend

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
    },
    "kaolin": {
        "rpc": "https://rpc.kaolin.holesky.golem-base.io",
        "ws": "wss://ws.rpc.kaolin.holesky.golem-base.io",
    },
}


async def connect():
    """
    connect
    """
    with open(
        BaseDirectory.xdg_config_home + "/golembase/private.key",
        "rb",
    ) as f:
        key_bytes = f.readline()

    client = await GolemBaseClient.create(
        rpc_url=INSTANCE_URLS["kaolin"]["rpc"],
        ws_url=INSTANCE_URLS["kaolin"]["ws"],
        private_key=key_bytes,
    )

    await client.watch_logs(
        lambda create: logger.info("Got create event: %s", create),
        lambda update: logger.info("Got update event: %s", update),
        lambda deleted_key: logger.info("Got delete event: %s", deleted_key),
        lambda extension: logger.info("Got extension event: %s", extension),
    )

    if await client.is_connected():
        block = await client.http_client().eth.get_block("latest")
        logger.info("Retrieved block %s", block.number)

        logger.info("entity count: %s", await client.get_entity_count())

        receipt = await client.create_entities(
            [GolemBaseCreate("hello", 60, [Annotation("foo", "bar")], [])]
        )
        entity_key = receipt[0].entity_key
        logger.info("receipt: %s", receipt)
        logger.info("entity count: %s", await client.get_entity_count())

        logger.info(entity_key)
        logger.info("storage value: %s", await client.get_storage_value(entity_key))
        metadata = await client.get_entity_metadata(entity_key)
        logger.info("entity metadata: %s", metadata)
        logger.info(
            "entities to expire at block: %s",
            await client.get_entities_to_expire_at_block(metadata.expires_at_block),
        )

        receipt = await client.extend_entities([GolemBaseExtend(entity_key, 60)])
        logger.info("receipt: %s", receipt)
    else:
        logger.warning("Could not connect to the API...")

    await client.disconnect()


async def run():
    """
    run
    """
    print("Connecting...")
    await connect()


async def main():
    """
    main
    """
    logger.info("Starting main loop")
    asyncio.run(main())


if __name__ == "__main__":
    main()
