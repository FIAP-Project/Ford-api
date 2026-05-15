"""RabbitMQ topic event bus with HMAC-signed messages."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from ford_shared.security.signature import sign_payload, verify_signature

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "ford.events"
SIGNATURE_HEADER = "x-signature"


@dataclass(frozen=True)
class EventEnvelope:
    routing_key: str
    payload: dict[str, Any]
    raw_body: bytes


EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus:
    """Async RabbitMQ topic-exchange client.

    Each service instantiates one EventBus, calls `connect()` on startup,
    and `close()` on shutdown. Publishers call `publish()`; consumers call
    `subscribe()` with one or more routing-key patterns and a handler.
    """

    def __init__(self, amqp_url: str, signing_secret: str) -> None:
        self._url = amqp_url
        self._signing_secret = signing_secret
        self._connection: AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractRobustChannel | None = None
        self._exchange: aio_pika.abc.AbstractRobustExchange | None = None
        self._consumer_tasks: list[asyncio.Task[None]] = []

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("event_bus.connected", extra={"exchange": EXCHANGE_NAME})

    async def close(self) -> None:
        for task in self._consumer_tasks:
            task.cancel()
        if self._connection is not None:
            await self._connection.close()
        logger.info("event_bus.closed")

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if self._exchange is None:
            raise RuntimeError("EventBus not connected")
        body = self._serialize(payload)
        signature = sign_payload(body, self._signing_secret)
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={SIGNATURE_HEADER: signature},
            timestamp=datetime.now(UTC),
        )
        await self._exchange.publish(message, routing_key=routing_key)
        logger.info("event_bus.published", extra={"routing_key": routing_key})

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        handler: EventHandler,
        *,
        durable: bool = True,
    ) -> None:
        if self._channel is None or self._exchange is None:
            raise RuntimeError("EventBus not connected")
        queue = await self._channel.declare_queue(queue_name, durable=durable)
        for key in routing_keys:
            await queue.bind(self._exchange, routing_key=key)

        async def _consumer() -> None:
            async with queue.iterator() as it:
                async for message in it:
                    async with message.process(requeue=False):
                        await self._dispatch(message, handler)

        task = asyncio.create_task(_consumer(), name=f"consumer:{queue_name}")
        self._consumer_tasks.append(task)
        logger.info(
            "event_bus.subscribed",
            extra={"queue": queue_name, "routing_keys": routing_keys},
        )

    async def _dispatch(
        self,
        message: aio_pika.abc.AbstractIncomingMessage,
        handler: EventHandler,
    ) -> None:
        signature = message.headers.get(SIGNATURE_HEADER, "") if message.headers else ""
        if not isinstance(signature, str) or not verify_signature(
            message.body, signature, self._signing_secret
        ):
            logger.warning(
                "event_bus.signature_invalid",
                extra={"routing_key": message.routing_key},
            )
            return
        try:
            payload = json.loads(message.body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.exception("event_bus.invalid_json")
            return
        envelope = EventEnvelope(
            routing_key=message.routing_key or "",
            payload=payload,
            raw_body=message.body,
        )
        try:
            await handler(envelope)
        except Exception:
            logger.exception("event_bus.handler_error")

    @staticmethod
    def _serialize(payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
