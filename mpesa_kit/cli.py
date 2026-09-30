import argparse
import json
import os
from typing import Any, Dict

from .client import MpesaClient, MpesaError
from .storage import EventStore


def _print(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def _doctor() -> Dict[str, Any]:
    required = ["CONSUMER_KEY", "CONSUMER_SECRET", "SHORTCODE"]
    optional = ["PASSKEY", "CALLBACK_URL", "INITIATOR_NAME", "SECURITY_CREDENTIAL", "B2C_RESULT_URL", "B2C_TIMEOUT_URL", "BALANCE_RESULT_URL", "BALANCE_TIMEOUT_URL", "STATUS_RESULT_URL", "STATUS_TIMEOUT_URL", "C2B_CONFIRMATION_URL", "C2B_VALIDATION_URL"]
    return {"environment": os.getenv("MPESA_ENVIRONMENT", "sandbox"), "required": {name: bool(os.getenv(name)) for name in required}, "optional": {name: bool(os.getenv(name)) for name in optional}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kenyapay", description="M-Pesa Daraja automation CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check configuration without printing secrets")
    sub.add_parser("token", help="Generate an OAuth access token")
    stk = sub.add_parser("stk", help="Send an STK Push")
    stk.add_argument("--phone", required=True)
    stk.add_argument("--amount", required=True, type=int)
    stk.add_argument("--ref", required=True)
    stk.add_argument("--desc", default="Payment")
    stk_query = sub.add_parser("stk-query", help="Query an STK Push")
    stk_query.add_argument("--checkout-id", required=True)
    b2c = sub.add_parser("b2c", help="Send a B2C payment")
    b2c.add_argument("--phone", required=True)
    b2c.add_argument("--amount", required=True, type=int)
    b2c.add_argument("--remarks", required=True)
    b2c.add_argument("--occasion", default="Payout")
    sub.add_parser("balance", help="Request account balance")
    status = sub.add_parser("status", help="Query a transaction status")
    status.add_argument("--transaction-id", required=True)
    c2b = sub.add_parser("register-c2b", help="Register C2B callback URLs")
    c2b.add_argument("--response-type", choices=["Completed", "Cancelled"], default="Completed")
    serve = sub.add_parser("serve", help="Run webhook receiver")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    events = sub.add_parser("events", help="List persisted webhook events")
    events.add_argument("--limit", type=int, default=20)
    events.add_argument("--kind")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "doctor":
            _print(_doctor())
            return
        if args.command == "serve":
            import uvicorn
            uvicorn.run("mpesa_kit.server:app", host=args.host, port=args.port)
            return
        if args.command == "events":
            _print(EventStore().list(limit=args.limit, kind=args.kind))
            return
        client = MpesaClient()
        if args.command == "token":
            _print({"access_token": client.get_access_token()})
        elif args.command == "stk":
            _print(client.stk_push(args.phone, args.amount, args.ref, args.desc))
        elif args.command == "stk-query":
            _print(client.stk_query(args.checkout_id))
        elif args.command == "b2c":
            _print(client.b2c(args.phone, args.amount, args.remarks, args.occasion))
        elif args.command == "balance":
            _print(client.get_balance())
        elif args.command == "status":
            _print(client.transaction_status(args.transaction_id))
        elif args.command == "register-c2b":
            _print(client.register_c2b_urls(response_type=args.response_type))
    except (MpesaError, ValueError) as exc:
        raise SystemExit("error: {}".format(exc))


if __name__ == "__main__":
    main()
