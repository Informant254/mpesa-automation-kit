# M-Pesa Automation Kit

A practical Python toolkit for Safaricom Daraja integrations: STK Push, STK status query, B2C payouts, account balance requests, transaction status, C2B URL registration, webhook capture, SQLite event history, CLI and Docker.

> Built for Daraja sandbox first. Switch to production only after your Safaricom app and shortcode are approved for the API products you use.

## What works in v0.2

- OAuth token generation with automatic refresh
- Sandbox / production switch
- Kenyan phone normalization (`0712...`, `712...`, `254712...`)
- STK Push and STK query
- B2C using `/mpesa/b2c/v3/paymentrequest`
- Account balance request
- Transaction status request
- C2B validation / confirmation URL registration
- FastAPI callback receiver
- SQLite persistence for callback events
- Automatic hosted callback URL generation
- `kenyapay` CLI
- Docker / Docker Compose
- Render Blueprint deployment
- Unit tests and GitHub Actions CI

## Install

```bash
git clone https://github.com/Informant254/mpesa-automation-kit.git
cd mpesa-automation-kit
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Fill `.env` with credentials from your Daraja app. Never commit `.env`.

## Configuration check

```bash
kenyapay doctor
```

This only reports whether variables are present. It never prints their values.

## Fastest sandbox deployment: Render

The repository includes `render.yaml`.

Create a Render Blueprint from this GitHub repository and provide these four sandbox values when prompted:

```text
CONSUMER_KEY
CONSUMER_SECRET
SHORTCODE
PASSKEY
```

`MPESA_ENVIRONMENT` defaults to `sandbox` in the Blueprint. Render exposes `RENDER_EXTERNAL_HOSTNAME`, which the SDK automatically converts into the correct HTTPS callback URLs.

After deployment, verify:

```text
GET https://<your-render-host>/health
```

Expected response:

```json
{"status":"ok"}
```

For the initial sandbox STK test you do not need `INITIATOR_NAME` or `SECURITY_CREDENTIAL`. Add those later for B2C, account balance, and transaction-status operations.

> The free Render filesystem is not a durable production database. SQLite is fine for sandbox callback testing, but production reconciliation should use persistent storage before real money flows through the service.

## Callback URL discovery

When `PUBLIC_BASE_URL=https://payments.example.com`, the SDK automatically derives:

```text
https://payments.example.com/mpesa/stk/callback
https://payments.example.com/mpesa/b2c/result
https://payments.example.com/mpesa/b2c/timeout
https://payments.example.com/mpesa/balance/result
https://payments.example.com/mpesa/balance/timeout
https://payments.example.com/mpesa/status/result
https://payments.example.com/mpesa/status/timeout
https://payments.example.com/mpesa/c2b/validation
https://payments.example.com/mpesa/c2b/confirmation
```

You can still override any individual route with its matching environment variable.

## CLI examples

```bash
kenyapay token
kenyapay stk --phone 0712345678 --amount 100 --ref ORDER123
kenyapay stk-query --checkout-id ws_CO_...
kenyapay b2c --phone 0712345678 --amount 500 --remarks "Refund"
kenyapay balance
kenyapay status --transaction-id RKTQDM7W6S
kenyapay register-c2b --response-type Completed
kenyapay events --limit 20
```

## Webhook server

```bash
kenyapay serve --host 0.0.0.0 --port 8000
```

Health check:

```text
GET /health
```

Callback routes:

```text
POST /mpesa/stk/callback
POST /mpesa/b2c/result
POST /mpesa/b2c/timeout
POST /mpesa/balance/result
POST /mpesa/balance/timeout
POST /mpesa/status/result
POST /mpesa/status/timeout
POST /mpesa/c2b/validation
POST /mpesa/c2b/confirmation
```

Callbacks are stored in SQLite (`MPESA_DB_PATH`, default `mpesa_events.db`) and can be inspected with `kenyapay events`.

## Docker

```bash
cp .env.example .env
# fill in .env first
docker compose up --build
```

The API listens on port `8000` and callback events are persisted in a Docker volume.

## Python usage

```python
from mpesa_kit import MpesaClient

mpesa = MpesaClient()
response = mpesa.stk_push(phone_number="0712345678", amount=100, account_reference="ORDER123")
print(response)
```

## Security notes

- Keep `CONSUMER_SECRET`, `PASSKEY`, and `SECURITY_CREDENTIAL` out of Git.
- `SECURITY_CREDENTIAL` is the encrypted initiator credential expected by Daraja, not a password you should publish.
- Use HTTPS callback URLs in production.
- Validate and authenticate traffic at your reverse proxy / application boundary before attaching business side-effects to callbacks.
- Treat Daraja acknowledgement responses as asynchronous acceptance, not proof that money moved. Reconcile using callbacks and transaction status.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

No license has been added yet. Add one before encouraging external reuse or contributions.
