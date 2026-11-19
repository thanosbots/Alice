# Deploy Alice on Railway

Alice runs as a background worker. The root Dockerfile installs Python 3.11, FFmpeg and all Python dependencies automatically. No separate music API service is needed.

## Deploy with the template

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/WiPJvE)

Open the template and configure Alice. The six required fields are already listed: `API_ID`, `API_HASH`, `BOT_TOKEN`, `STRING_SESSION`, `MONGO_URL`, and `OWNER_ID`. Enter your own values. `LOG_GROUP_ID` defaults to `0` (optional); set your log group ID if needed. The template already attaches a volume at `/data` and sets the session directory.

MongoDB is not included: supply your existing MongoDB connection string. Keep one replica, deploy, and check for `All systems ready`. Stop any previous instance using the same bot/assistant before starting this one.

## Deploy manually from GitHub

1. Fork this repository and create a Railway service from your fork. Keep the root directory at `/`; Railway reads `railway.json` and the root Dockerfile.
2. Before starting the bot, add these service variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, `STRING_SESSION`, `MONGO_URL`, and `OWNER_ID`. Use your Telegram app credentials, bot token, assistant session string, MongoDB connection string and numeric Telegram owner ID. Optional: `LOG_GROUP_ID`. Do not upload `Config.env` or session files.
3. Attach a Railway volume to this service at **`/data`**. The image sets `SESSION_DIR=/data`; the bot session survives redeployments. Do not mount it at `/app`. MongoDB still needs its own persistent hosting; the bot volume is not a database.
4. Keep **one replica in one region**. Disable Serverless/app sleeping if your plan offers this setting. Leave Start Command at the Docker default and HTTP healthcheck blank. No public domain or exposed web port is needed.
5. Deploy and check logs for `All systems ready`. In Telegram, test `/start`, then `/play` in a group with a voice chat and the bot's required admin permissions. Stop the previous bot instance before using the same bot/assistant session here.

If you used Project Settings → Shared Variables, click **Share** for each variable and select the Alice service, then deploy the changes. Project-level variables do not reach the bot until linked to its service.

## Updates and storage

Push updates to the connected GitHub branch and deploy through Railway. `/update` explains this workflow instead of modifying the running container. VPS installations retain their existing updater.

The volume preserves the bot session only. Downloads, generated artwork and local logs are temporary and can disappear on redeploy; use Railway logs for deployment failures and owner-only `/logs` in private chat for the current bot runtime. Music queues reset on restart.

Railway credits, network access and resources depend on your account/plan. This configuration does not guarantee free 24/7 hosting. If startup cannot reach Telegram or MongoDB, check service logs, database network access and Railway account restrictions.

Official references: [Docker builds](https://docs.railway.com/builds/dockerfiles), [config as code](https://docs.railway.com/config-as-code/reference), [persistent volumes](https://docs.railway.com/volumes).
