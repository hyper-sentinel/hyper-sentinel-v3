# 🛡️ Sentinel API — Getting Started

> Go from zero to your first API call in 60 seconds.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- A `.env` file with your API keys

---

## Installation

```bash
# Clone the repo
git clone https://github.com/hyper-sentinel/hyper-sentinel-v3.git
cd hyper-sentinel-v3

# Install dependencies
uv sync

# Copy the example env
cp .env.example .env
# Edit .env with your keys
```

---

## Start the API Server

```bash
uv run python api_server.py
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

---

## Your First API Call

### In the browser

Open **http://localhost:8000/docs** — the interactive Swagger dashboard.

1. Click on `POST /api/v1/tools/{tool_name}`
2. Click **"Try it out"**
3. Set `tool_name` to `get_crypto_price`
4. Set request body to `{"coin_id": "bitcoin"}`
5. Click **Execute**
6. See Bitcoin's live price in the response

### From the terminal

```bash
curl -X POST http://localhost:8000/api/v1/tools/get_crypto_price \
  -H "Content-Type: application/json" \
  -d '{"coin_id":"bitcoin"}'
```

### From Python

```python
import requests

r = requests.post("http://localhost:8000/api/v1/tools/get_crypto_price",
                   json={"coin_id": "bitcoin"})
data = r.json()
print(f"Bitcoin: ${data['result']['current_price']:,}")
# → Bitcoin: $70,617
```

---

## What's Available

| Category | Tools | Auth |
|----------|-------|------|
| Crypto prices | 3 | Public |
| Macro data (FRED) | 3 | Public |
| News & intelligence | 4 | Public |
| Social sentiment | 5 | Public |
| Twitter search | 1 | Public |
| Hyperliquid trading | 8 | Mixed |
| Aster DEX | 14 | Mixed |
| Polymarket | 10 | Mixed |

**Total:** 49 tools · 28 public, 21 auth-required

---

## Next Steps

- 📖 [Full API Reference](./API-REFERENCE.md) — every tool with parameters and examples
- 🔐 Set up API keys for private endpoints
- 🚀 Deploy to Cloud Run with `./deploy.sh`

---

*Built with ❤️ by the Hyper-Sentinel team*
