# mpesa-automation-kit

**Powerful Python + AI toolkit for M-Pesa & Kenyan payments automation.**

STK Push, B2C, Balance, Webhooks, Auto-reconciliation, CLI, Docker. Ready for fraud detection.
Made in Nairobi 🇰🇪

## Quick Install
```bash
git clone https://github.com/Informant254/mpesa-automation-kit.git
cd mpesa-automation-kit
pip install -e .
cp .env.example .env
```

## CLI Examples
```bash
kenyapay stk --phone 254712345678 --amount 100 --ref "ORDER123"
kenyapay b2c --phone 254712345678 --amount 500 --remarks "Salary"
kenyapay balance
```

## Run Server
```bash
docker compose up --build
```

Star ⭐ if useful!