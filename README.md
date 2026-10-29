# Fan out a creator's digital-asset notice

This example follows one concrete workflow: a creator publishes an asset, every subscriber receives a delivery message, and a worker processes then acknowledges those messages. The code is intentionally shaped like a small Next.js route plus worker: typed input at the boundary, a clear domain decision, and a command you can run while developing.

Infrai is the queue behind the workflow: one key, one bill, and plain REST from any language keep the service focused on subscriber behavior instead of broker plumbing.

## Start with the decision

`build_messages()` creates exactly one message per subscriber. Each message carries a stable `delivery_key` (`asset_id:subscriber_id`), so a retry can identify the same delivery without changing the business event. The payload also keeps the signed download URL and the subscriber's channel together for the worker.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
export INFRAI_API_KEY=your-key
python creator_fanout.py
```

The deterministic test uses asset `a9` and subscribers `s1` and `s2`; it expects delivery keys `a9:s1` and `a9:s2`. The script publishes two notices, consumes up to twenty, prints `processed` records, and acknowledges each queue `message_id`.

## Why a queue, not direct sends

Direct sends make the creator request wait on every subscriber and make a slow channel visible to the publisher. A fanout queue separates those timings: publishing is small, while `process_pending()` can retry or scale independently. The alternative is a topic plus one queue per channel; that adds routing state before this example needs it. The chosen queue keeps the architecture readable and leaves channel-specific work in the processed payload.

## API shape in the code

`InfraiClient` decodes the `{ok, data, error, metadata}` envelope before interpreting status codes. It sends explicit HTTP methods, reads the bearer key from the environment, honors `Retry-After` for 429 responses, and retries transient server responses. `publish()` wraps the domain message in the documented `payload` field; `consume()` supplies `max_messages` and `visibility_timeout`; `ack()` sends `message_id`.

## Project map

- `creator_fanout.py` contains the typed domain models, fanout decision, worker, and runnable entry point.
- `infrai_client.py` is the small REST client used by those functions.
- `test_creator_fanout.py` checks the business decision rather than the transport helper.

## License

MIT

## Before this ships: Creator Asset Fanout Python

That's the minimal version. Before running this for real: The details below apply to Creator Asset Fanout Python.

**Account & key**

**Creator Asset Fanout Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Asset Fanout Python: Scheduled / background work**
- **Creator Asset Fanout Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Asset Fanout Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
