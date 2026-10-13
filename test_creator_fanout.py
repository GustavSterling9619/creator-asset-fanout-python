from creator_fanout import AssetNotice, Subscriber, build_messages


def test_each_subscriber_gets_a_deduplicated_delivery_key():
    notice = AssetNotice("c1", "a9", "New pack", "https://cdn.example/a9")
    messages = build_messages(notice, [Subscriber("s1", "email"), Subscriber("s2", "webhook")])
    assert [m["delivery_key"] for m in messages] == ["a9:s1", "a9:s2"]
    assert all(m["event"] == "asset.available" for m in messages)
