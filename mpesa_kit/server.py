from typing import Any, Dict, Optional

from fastapi import FastAPI, Request

from .storage import EventStore

app = FastAPI(title="M-Pesa Automation Kit", version="0.2.0")
store = EventStore()


def _nested(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _event_key(kind: str, body: Dict[str, Any]) -> Optional[str]:
    if kind == "stk":
        return _nested(body, "Body", "stkCallback", "CheckoutRequestID")
    if kind.startswith("b2c") or kind.startswith("balance") or kind.startswith("status"):
        return _nested(body, "Result", "ConversationID") or _nested(body, "Result", "OriginatorConversationID")
    if kind.startswith("c2b"):
        return body.get("TransID")
    return None


async def _capture(kind: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    store.add(kind, body, _event_key(kind, body))
    return body


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/mpesa/stk/callback")
async def stk_callback(request: Request) -> Dict[str, Any]:
    await _capture("stk", request)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@app.post("/mpesa/b2c/result")
async def b2c_result(request: Request) -> Dict[str, str]:
    await _capture("b2c_result", request)
    return {"status": "accepted"}


@app.post("/mpesa/b2c/timeout")
async def b2c_timeout(request: Request) -> Dict[str, str]:
    await _capture("b2c_timeout", request)
    return {"status": "accepted"}


@app.post("/mpesa/balance/result")
async def balance_result(request: Request) -> Dict[str, str]:
    await _capture("balance_result", request)
    return {"status": "accepted"}


@app.post("/mpesa/balance/timeout")
async def balance_timeout(request: Request) -> Dict[str, str]:
    await _capture("balance_timeout", request)
    return {"status": "accepted"}


@app.post("/mpesa/status/result")
async def status_result(request: Request) -> Dict[str, str]:
    await _capture("status_result", request)
    return {"status": "accepted"}


@app.post("/mpesa/status/timeout")
async def status_timeout(request: Request) -> Dict[str, str]:
    await _capture("status_timeout", request)
    return {"status": "accepted"}


@app.post("/mpesa/c2b/validation")
async def c2b_validation(request: Request) -> Dict[str, Any]:
    await _capture("c2b_validation", request)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@app.post("/mpesa/c2b/confirmation")
async def c2b_confirmation(request: Request) -> Dict[str, Any]:
    await _capture("c2b_confirmation", request)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
