# Hyper-Sentinel — First-Time Setup

This guide assumes you've never used Docker, NATS, or any of the new Sentinel stack before. Follow each step in order.

---

## Step 1 · Install `uv` (if not already installed)

You probably already have this, but just in case:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

To confirm it's installed:
```bash
uv --version
```

You should see a version number. If you do, move on.

---

## Step 2 · Install Docker Desktop

Docker is the app that lets you run services (like NATS) in containers on your Mac. Sentinel needs it to run the NATS message server.

### 2a. Download Docker Desktop

Go to: **[docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)**

Click **"Download for Mac"** — choose the Apple Silicon version (M1/M2/M3/M4).

Or install with Homebrew:
```bash
brew install --cask docker
```

### 2b. Open Docker Desktop

1. Go to **Applications** → double-click **Docker**
2. It will ask for permissions — click **OK** / **Allow**
3. Wait for it to finish starting up
4. Look at your **menu bar** (top of screen) — you should see a **whale icon** 🐋
5. When the whale stops animating, Docker is ready

### 2c. Verify Docker is working

Open a new terminal and run:
```bash
docker --version
```

You should see something like:
```
Docker version 27.5.1, build 9f9e405
```

Then run:
```bash
docker compose version
```

You should see:
```
Docker Compose version v2.32.4
```

If both commands work, Docker is good to go.

> [!TIP]
> **Optional:** Make Docker start automatically when you log in.
> Open Docker Desktop → Settings (gear icon) → General → check **"Start Docker Desktop when you sign in to your computer"**. This means you won't have to manually open it every time.

---

## Step 3 · Install the NATS CLI

The NATS CLI lets you send test messages to your agents from the terminal. The actual NATS server runs inside Docker — this is just the client tool.

```bash
brew tap nats-io/nats-tools
brew install nats-io/nats-tools/nats
```

Verify:
```bash
nats --version
```

You should see a version number.

---

## Step 4 · Clone the Project (or navigate to it)

If you already have it:
```bash
cd ~/Antigravity/Python/hyper-sentinel
```

If you're cloning fresh:
```bash
cd ~/Antigravity/Python
git clone https://github.com/hyper-sentinel/hyper-sentinel.git
cd hyper-sentinel
```

---

## Step 5 · Set Up Your Environment File

The `.env` file holds your API keys. It's gitignored so your keys never get committed.

### 5a. Create it from the template

```bash
cp .env.example .env
```

### 5b. Open it in your editor

```bash
open .env
```

Or edit it directly:
```bash
nano .env
```

### 5c. Add your API key

You'll see this in the file:
```
LLM_PROVIDER=CLAUDE
LLM_API_KEY=sk-ant-...
```

Replace `sk-ant-...` with your actual Anthropic API key.

**Where to get your API key:**

| Provider | Where to get a key |
|---|---|
| Claude (Anthropic) | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| Gemini (Google) | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Grok (xAI) | [console.x.ai](https://console.x.ai) |
| Ollama (local, free) | No key needed — set `LLM_PROVIDER=OLLAMA` |

Save and close the file.

---

## Step 6 · Start NATS

NATS is the message bus that connects agents together. It runs inside Docker.

### 6a. Make sure Docker Desktop is running

Look for the **whale icon 🐋** in your menu bar. If it's not there, open Docker Desktop from Applications and wait for it to start.

### 6b. Start the NATS server

```bash
docker compose up -d nats
```

**What this does:**
- `docker compose` = Docker's tool for running multi-container setups
- `up` = start the service
- `-d` = run in the background (detached) so it doesn't take over your terminal
- `nats` = only start the NATS service (not everything)

### 6c. Verify NATS is running

```bash
docker compose ps
```

You should see:
```
NAME                    STATUS
hyper-sentinel-nats     Up (healthy)
```

If it says "Up (healthy)" — NATS is running and ready.

> [!NOTE]
> NATS will keep running in the background until you stop it (`docker compose down`) or restart your Mac. You don't need to start it again each time you run Sentinel — just check if it's already running with `docker compose ps`.

---

## Step 7 · Run Sentinel

```bash
uv run main.py
```

That's it. Same command you use for everything else.

On first run, `uv` will download and cache the dependencies (Upsonic, NATS client, yfinance, etc.). This takes about 30 seconds the first time, then it's instant after that.

You should see the Sentinel banner, a status dashboard showing your config, and then "MarketAgent is ONLINE — awaiting messages..."

---

## Step 8 · Test It

Open a **second terminal** (keep Sentinel running in the first one) and send a test message:

```bash
cd ~/Antigravity/Python/hyper-sentinel
bash scripts/test-publish.sh
```

Go back to your first terminal — you should see the MarketAgent processing the message.

---

## You're Done 🎉

From now on, your daily workflow is:

```bash
# 1. Make sure Docker Desktop is running (whale icon in menu bar)

# 2. Start NATS (skip if already running — check with 'docker compose ps')
cd ~/Antigravity/Python/hyper-sentinel
docker compose up -d nats

# 3. Run Sentinel
uv run main.py
```

---

## Stopping Everything

```bash
# Stop Sentinel
# Just press Ctrl+C in the terminal where it's running

# Stop NATS (optional — fine to leave running)
docker compose down
```

---

## Troubleshooting

### "Cannot connect to the Docker daemon"
Docker Desktop isn't running. Open it from Applications and wait for the whale icon to appear.

### "connection refused" when starting Sentinel
NATS isn't running. Start it with `docker compose up -d nats`.

### "LLM_API_KEY" errors
Your `.env` file is missing the key. Run `open .env` and paste in your API key.

### Dependencies fail to install
Make sure you have `uv` installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Port 4222 already in use
Something else is using the NATS port. Find it with `lsof -i :4222` and kill it, or run `docker compose down` first.

### Want to completely reset
```bash
docker compose down -v
uv run main.py
```
