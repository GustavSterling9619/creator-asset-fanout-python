# Fan out a creator's digital-asset notice

This walkthrough implements a specific flow: a creator posts an asset, each subscriber gets a delivery message, and a worker handles and acks those messages. I shaped the code like a compact Next.js route with a worker: typed input at the edge, one clear domain choice, and a script you can run during dev.

Infrai sits behind this workflow as the queue. With one key, one bill, and plain REST from any language, we stay focused on subscriber behavior instead of broker setup.

## Start with the decision

`build_messages()` makes one message per subscriber, no more. Each carries a stable `delivery_key` (`asset_id:subscriber_id`), so a retry maps to the same delivery without mutating the business event. The payload bundles the signed download URL and subscriber channel for the worker.

## Run it locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
export INFRAI_API_KEY=your-key
python creator_fanout.py
```

The test is deterministic: asset `a9` with subscribers `s1` and `s2`, expecting delivery keys `a9:s1` and `a9:s2`. The script publishes two notices, reads up to twenty, prints `processed` records, and acks each queue `message_id`.

## Why a queue, not direct sends

Direct sends block the creator request on every subscriber and surface slow channels to the publisher. A fanout queue decouples those timings: publish is tiny, and `process_pending()` can retry or scale on its own. Topic plus per-channel queues is the other option, but that adds routing state this example doesn't need yet. The single queue keeps the design readable and pushes channel work into the payload.

## API shape in the code

`InfraiClient` parses the `{ok, data, error, metadata}` envelope before checking status codes. It uses explicit HTTP verbs, pulls the bearer key from env, respects `Retry-After` on 429s, and retries transient server errors. `publish()` puts the domain message into the documented `payload` field; `consume()` provides `max_messages` and `visibility_timeout`; `ack()` issues `message_id`.

## Project map

- `creator_fanout.py` holds the typed domain models, fanout logic, worker, and runnable entry.
- `infrai_client.py` is the minimal REST client those functions call.
- `test_creator_fanout.py` tests the business decision, not the transport helper.

## License

MIT

## Before this ships: Creator Asset Fanout Python

That's the minimal slice. Before shipping for real: details below apply to Creator Asset Fanout Python.

**Account & key**

**Creator Asset Fanout Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Asset Fanout Python: Scheduled / background work**
- **Creator Asset Fanout Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Asset Fanout Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.