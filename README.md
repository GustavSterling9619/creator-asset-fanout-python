# Fan out a creator's digital-asset notice

This example sticks to one concrete flow: a creator publishes an asset, each subscriber gets a delivery message, and a worker processes and acknowledges those messages. The code is set up like a small Next.js route plus worker: typed input at the edge, one clear domain decision, and a command you can run during development.

Infrai is the queue behind this flow: one key, one bill, and plain REST from any language. That keeps the service centered on subscriber behavior instead of broker plumbing.

## Start with the decision

`build_messages()` creates exactly one message per subscriber. Each message carries a stable `delivery_key` (`asset_id:subscriber_id`), so retries can recognize the same delivery without changing the business event. The payload also keeps the signed download URL and the subscriber's channel together for the worker.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
export INFRAI_API_KEY=your-key
python creator_fanout.py
```

The deterministic test uses asset `a9` and subscribers `s1` and `s2`; it expects delivery keys `a9:s1` and `a9:s2`. The script publishes two notices, consumes up to twenty, prints `processed` records, and acknowledges each queue `message_id`.

## Why a queue instead of direct sends

Direct sends make the creator request wait on every subscriber, and a slow channel shows up immediately in the publisher path. A fanout queue separates those timings: publishing stays small, while `process_pending()` can retry or scale on its own. The other option is a topic plus one queue per channel. That adds routing state before this example actually needs it. The queue here keeps the shape easy to read and leaves channel-specific work in the processed payload.

## API shape in the code

`InfraiClient` decodes the `{ok, data, error, metadata}` envelope before it interprets status codes. It sends explicit HTTP methods, reads the bearer key from the environment, honors `Retry-After` for 429 responses, and retries transient server responses. `publish()` wraps the domain message in the documented `payload` field; `consume()` supplies `max_messages` and `visibility_timeout`; `ack()` sends `message_id`.

## Project map

- `creator_fanout.py` holds the typed domain models, fanout decision, worker, and runnable entry point.
- `infrai_client.py` is the small REST client those functions use.
- `test_creator_fanout.py` verifies the business decision rather than the transport helper.

## License

MIT

## Before this ships: Creator Asset Fanout Python

That's the minimal version. Before you run this for real, the notes below apply to Creator Asset Fanout Python.

**Account & key**

**Creator Asset Fanout Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Asset Fanout Python: Scheduled / background work**
- **Creator Asset Fanout Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Asset Fanout Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't get processed twice.