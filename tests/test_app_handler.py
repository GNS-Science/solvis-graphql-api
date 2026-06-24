"""Lambda entry (`app.handler`) — warmup-event guard + HTTP passthrough to Mangum."""

from solvis_graphql_api.app import handler


def test_handler_swallows_warmup_ping():
    # serverless-plugin-warmup sends a non-HTTP event Mangum can't infer; we short-circuit it
    resp = handler({"source": "serverless-plugin-warmup"}, None)
    assert resp == {"statusCode": 200, "body": "warmed"}


def test_handler_delegates_non_warmup_to_mangum(monkeypatch):
    # any non-warmup event is passed straight to Mangum (the real HTTP path is proven by the
    # live deploy smoke); here we just assert the guard delegates rather than short-circuits
    seen = {}

    def fake_mangum(event, context):
        seen["event"] = event
        return {"statusCode": 200}

    monkeypatch.setattr("solvis_graphql_api.app._mangum", fake_mangum)
    resp = handler({"httpMethod": "POST", "path": "/graphql"}, None)
    assert seen.get("event") == {"httpMethod": "POST", "path": "/graphql"}
    assert resp == {"statusCode": 200}
