# 🕵️ Discord Anonymous Confession Bot

A feature-rich, containerized Discord Anonymous Confession Bot built with Python (`discord.py` v2.x), Redis caching layer, and SQLite persistent storage.

**Support server:** [discord.gg/CbM8AAUcua](https://discord.gg/CbM8AAUcua)

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

Open `.env` and set your Discord Bot Token and owner ID:
```env
DISCORD_TOKEN=your_actual_discord_bot_token
BOT_USER_ID=1508460938255138981
STAFF_GUILD_ID=1534941712177168384
BOT_OWNER_ID=your_discord_user_id
SUPPORT_SERVER_URL=https://discord.gg/CbM8AAUcua
```

---

### Step 2: Start the Bot & Redis with Docker Compose
```bash
docker compose up -d --build
```

View logs:
```bash
docker compose logs -f confess
```

Stop services:
```bash
docker compose down
```

---

## 🤖 Discord Slash Commands

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/confess` | Submit an anonymous confession | Everyone |
| `/help` | Show help and support link | Everyone |
| `/setup` | Configure confession & review channels | Administrator |
| `/panel` | Customization panel (avatar, word filter) | Administrator |
| `/lookup` | Look up confession/reply author by ID | Bot owner only |

---

## 📋 Logging Channels (staff guild)

| Channel | ID | Purpose |
| :--- | :--- | :--- |
| Errors | `1536045899049078965` | Error embeds + traceback files |
| Join / Leave | `1536045678508118056` | Bot added / removed from servers |
| Guild activity | `1536045911862411326` | Setup, posts, approvals |
| Reports | `1536045946956415168` | User-reported confessions |

Staff guild ID: `1534941712177168384`  
Bot user ID: `1508460938255138981`

---

## 🛠️ Discord Developer Portal Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Create an application and open the **Bot** tab.
3. Copy the **Bot Token** into `.env` as `DISCORD_TOKEN`.
4. Under **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Manage Messages`, `Embed Links`, `Read Message History`, `Use Slash Commands`, `View Audit Log`
5. Invite the bot to your server using the generated URL.

Need help? Join the [support server](https://discord.gg/CbM8AAUcua).
