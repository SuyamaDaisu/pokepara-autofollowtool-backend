#!/bin/bash
# ConoHa VPS Deployment Script for Pokepara Auto-Follow Backend

echo "=== Pokepara Auto-Follow Backend Deployment ==="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install system dependencies for Playwright
echo "Installing Playwright system dependencies..."
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1

# Create app directory
echo "Setting up application directory..."
cd /home/$(whoami)
mkdir -p pokepara-backend
cd pokepara-backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright Chromium..."
playwright install chromium
playwright install-deps chromium

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pokepara-backend.service > /dev/null <<EOF
[Unit]
Description=Pokepara Auto-Follow Backend
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/home/$(whoami)/pokepara-backend
Environment="PATH=/home/$(whoami)/pokepara-backend/venv/bin"
ExecStart=/home/$(whoami)/pokepara-backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable pokepara-backend
sudo systemctl start pokepara-backend

# Configure firewall
echo "Configuring firewall..."
sudo ufw allow 8000/tcp
sudo ufw --force enable

echo "=== Deployment Complete ==="
echo "Service status:"
sudo systemctl status pokepara-backend --no-pager
echo ""
echo "To view logs: sudo journalctl -u pokepara-backend -f"
echo "To restart: sudo systemctl restart pokepara-backend"
echo "To stop: sudo systemctl stop pokepara-backend"

