#!/bin/bash
# Run once on a fresh Hetzner Ubuntu server to set up the football app.
# Usage: bash scripts/server_setup.sh

set -e

echo "=== Installing Docker ==="
sudo apt update && sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker "$USER"

echo "=== Setting up app directory ==="
mkdir -p /app/football/football_data/logs
cd /app/football

echo "=== Setting up environment variables ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo ">>> Edit .env and fill in your Neon DB credentials and API key:"
    echo "    nano .env"
    echo ""
fi

echo "=== Adding cron jobs ==="
IMAGE="ghcr.io/$(git remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||' | tr '[:upper:]' '[:lower:]'):latest"

(crontab -l 2>/dev/null; cat <<EOF

# Football predictor — Docker-based cron
# Pull today's results every night at 23:30
30 23 * * * docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m ingestion.main today >> /app/football/football_data/logs/cron.log 2>&1

# Refresh standings every Monday at 02:00
0 2 * * 1 docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m ingestion.main standings >> /app/football/football_data/logs/cron.log 2>&1

# Predict next 7 days every Monday at 03:00
0 3 * * 1 docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m modelling.main predict >> /app/football/football_data/logs/cron.log 2>&1

# Score settled predictions every night at 23:45
45 23 * * * docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m modelling.main accuracy >> /app/football/football_data/logs/cron.log 2>&1
EOF
) | crontab -

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /app/football/.env with your credentials"
echo "  2. Log out and back in (to pick up docker group membership)"
echo "  3. Pull the latest image manually the first time:"
echo "     docker pull $IMAGE"
echo "  4. Do a one-off backfill:"
echo "     docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m ingestion.main backfill"
echo "  5. Train the model:"
echo "     docker run --rm --env-file /app/football/.env -v /app/football/football_data:/app/football_data $IMAGE python -m modelling.main train"
