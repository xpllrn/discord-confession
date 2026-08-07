# 🕵️ Discord Anonymous Confession Bot

A feature-rich, containerized Discord Anonymous Confession Bot built with Python (`discord.py` v2.x), Redis caching layer, and SQLite persistent storage.

---

## 🚀 Quick Start with Docker & Docker Compose

### Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose installed on your host system.
- A **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications).

---

### Step 1: Clone & Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and set your Discord Bot Token:
```env
DISCORD_TOKEN=your_actual_discord_bot_token
SUPPORT_SERVER_URL=https://discord.gg/your_server
```

---

### Step 2: Start the Bot & Redis with Docker Compose
Run the following command to build and launch both the Redis container and the Discord Bot container:
```bash
docker compose up -d --build
```

To view logs:
```bash
docker compose logs -f bot
```

To stop the services:
```bash
docker compose down
```

---

## 🤖 Discord Slash Commands

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/setup` | Starts the interactive 3-step setup flow to configure confession channels & review channel using Discord UI Container cards | Administrator |
| `/panel` | Opens the customization panel (Customize options, Word filters) | Administrator |

---

## 🛠️ Step-by-Step Discord Developer Portal Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give your bot a name (e.g. `ConfessionBot`).
3. Navigate to **Bot** tab on the left side menu.
4. Click **Reset Token** to copy your **Bot Token** and paste it into your `.env` file.
5. Under **OAuth2** -> **URL Generator**:
   - Select scopes: `bot`, `applications.commands`.
   - Select bot permissions: `Send Messages`, `Manage Messages`, `Embed Links`, `Read Message History`, `Use Slash Commands`.
   - Copy the generated URL and paste it into your browser to invite the bot to your Discord server!
