# ConoHa VPS Deployment Guide

## Prerequisites
- ConoHa VPS running Ubuntu 20.04/22.04
- SSH access to your VPS
- IP: `160.251.171.205`

## Step-by-Step Deployment

### 1. Connect to your ConoHa VPS
```bash
ssh root@160.251.171.205
# or
ssh your-username@160.251.171.205
```

### 2. Upload backend files
From your local machine:
```bash
scp -r backend/ your-username@160.251.171.205:~/pokepara-backend/
```

Or use Git:
```bash
cd ~
git clone <your-repo-url>
cd pokepara-autofollow/backend
```

### 3. Run the deployment script
```bash
cd ~/pokepara-backend
chmod +x deploy_conoha.sh
./deploy_conoha.sh
```

### 4. Verify the service is running
```bash
sudo systemctl status pokepara-backend
```

### 5. Test the API
```bash
curl http://160.251.171.205:8000
# Should return: {"message":"Auto Follow Backend API"}
```

## Manual Installation (Alternative)

If the script doesn't work, follow these manual steps:

### 1. Install dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### 2. Create virtual environment
```bash
cd ~/pokepara-backend
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Python packages
```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

### 4. Run the application
```bash
# Test run
python main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Run as background service with systemd
Create `/etc/systemd/system/pokepara-backend.service`:
```ini
[Unit]
Description=Pokepara Auto-Follow Backend
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/pokepara-backend
Environment="PATH=/home/your-username/pokepara-backend/venv/bin"
ExecStart=/home/your-username/pokepara-backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pokepara-backend
sudo systemctl start pokepara-backend
```

## Useful Commands

### Service Management
```bash
# Check status
sudo systemctl status pokepara-backend

# View logs
sudo journalctl -u pokepara-backend -f

# Restart service
sudo systemctl restart pokepara-backend

# Stop service
sudo systemctl stop pokepara-backend

# Start service
sudo systemctl start pokepara-backend
```

### Firewall
```bash
# Allow port 8000
sudo ufw allow 8000/tcp
sudo ufw enable
```

### Update Code
```bash
# Stop service
sudo systemctl stop pokepara-backend

# Pull latest code
cd ~/pokepara-backend
git pull

# Or upload new files via scp
# scp main.py your-username@160.251.171.205:~/pokepara-backend/

# Restart service
sudo systemctl start pokepara-backend
```

## Troubleshooting

### Check if port 8000 is listening
```bash
sudo netstat -tulpn | grep 8000
# or
sudo ss -tulpn | grep 8000
```

### Test from VPS itself
```bash
curl http://localhost:8000
```

### Check Playwright installation
```bash
source venv/bin/activate
playwright install --with-deps chromium
```

### View detailed logs
```bash
sudo journalctl -u pokepara-backend -n 100 --no-pager
```

### If Chromium fails to launch
Install missing dependencies:
```bash
sudo apt install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2
```

## Security Notes

1. **Firewall**: Only open port 8000 if needed. Consider using a reverse proxy (nginx) with SSL.
2. **CORS**: Update `allow_origins` in `main.py` to only allow your frontend domain.
3. **Credentials**: Move hardcoded credentials to environment variables.

## Production Recommendations

1. Use nginx as reverse proxy with SSL certificate
2. Set up automatic backups
3. Monitor service health
4. Use environment variables for sensitive data
5. Set up log rotation

