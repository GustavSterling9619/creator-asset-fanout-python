from dataclasses import asdict, dataclass
from typing import Any

from infrai_client import InfraiClient


@dataclass(frozen=True)
class Subscriber:
    subscriber_id: str
    channel: str


@dataclass(frozen=True)
class AssetNotice:
    creator_id: str
    asset_id: str
    title: str
    download_url: str


def build_messages(notice: AssetNotice, subscribers: list[Subscriber]) -> list[dict[str, Any]]:
    """Return one processed delivery message per subscriber."""
    return [
        {
            "event": "asset.available",
            "delivery_key": f"{notice.asset_id}:{subscriber.subscriber_id}",
            "subscriber": asdict(subscriber),
            "asset": asdict(notice),
        }
        for subscriber in subscribers
    ]


def fanout(notice: AssetNotice, subscribers: list[Subscriber], client: InfraiClient) -> int:
    """Publish the fanout and return the number accepted by the queue."""
    for message in build_messages(notice, subscribers):
        client.publish(message)
    return len(subscribers)


def process_pending(client: InfraiClient, max_messages: int = 20) -> list[dict[str, Any]]:
    """Consume, mark content processed, and acknowledge each delivery."""
    data = client.consume(max_messages=max_messages, visibility_timeout=60)
    messages = data.get("messages") or data.get("items") or []
    processed = []
    for message in messages:
        body = message.get("payload") or message
        processed.append({"delivery_key": body.get("delivery_key"), "status": "processed"})
        if message.get("message_id"):
            client.ack(message["message_id"])
    return processed


if __name__ == "__main__":
    notice = AssetNotice("creator-7", "asset-42", "Behind the scenes", "https://cdn.example/asset-42")
    subscribers = [Subscriber("fan-1", "email"), Subscriber("fan-2", "webhook")]
    client = InfraiClient()
    print({"published": fanout(notice, subscribers, client)})
    print({"processed": process_pending(client)})
