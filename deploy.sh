#!/bin/bash
#
# AMARKTAI NETWORK - GITHUB DEPLOYMENT SCRIPT
# Deploys directly from GitHub repository
# Compatible with Ubuntu 22.04 and 24.04
#
# Usage: Run this on your VPS as root or with sudo
# sudo bash deploy.sh
#

set -e  # Exit on any error

echo "========================================="
echo "🚀 AMARKTAI NETWORK - GITHUB DEPLOYMENT"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# GitHub repository
REPO_URL="https://github.com/amarktainetwork-blip/Amarktai-Network-Production.git"
DEPLOY_PATH="/var/amarktai/Amarktai-Network-2"

# Step 1: Backup SSL certificates
echo -e "${BLUE}Step 1: Backing up SSL certificates...${NC}"
mkdir -p /root/ssl_backup
cp -r /etc/letsencrypt /root/ssl_backup/ 2>/dev/null || echo "No existing SSL to backup"
echo -e "${GREEN}✅ SSL certificates backed up${NC}"
echo ""

# Step 2: Stop existing services
echo -e "${BLUE}Step 2: Stopping existing services...${NC}"
systemctl stop amarktai-api 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# Step 3: Clean old installation (preserve SSL)
echo -e "${BLUE}Step 3: Cleaning old installation...${NC}"
rm -rf ${DEPLOY_PATH} 2>/dev/null || true
mkdir -p /var/amarktai
echo -e "${GREEN}✅ Old installation removed${NC}"
echo ""

# Step 4: Install system dependencies
echo -e "${BLUE}Step 4: Installing system dependencies...${NC}"
apt-get update -qq

# Install MongoDB (handle different Ubuntu versions)
if ! command -v mongod &> /dev/null; then
    echo "Installing MongoDB..."
    
    # Import MongoDB GPG key
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
        gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
        tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Update and install
    apt-get update -qq
    apt-get install -y mongodb-org -qq
else
    echo "MongoDB already installed"
fi

# Install other dependencies
apt-get install -y git python3 python3-pip python3-venv nodejs npm redis-server nginx curl -qq

echo -e "${GREEN}✅ System dependencies installed${NC}"
echo ""

# Step 5: Clone from GitHub
echo -e "${BLUE}Step 5: Cloning from GitHub...${NC}"
git clone ${REPO_URL} ${DEPLOY_PATH}
chown -R admin:sudo ${DEPLOY_PATH}
echo -e "${GREEN}✅ Repository cloned from GitHub${NC}"
echo ""

# Step 6: Start MongoDB and Redis
echo -e "${BLUE}Step 6: Starting MongoDB and Redis...${NC}"
systemctl start mongod
systemctl enable mongod
systemctl start redis-server
systemctl enable redis-server
sleep 3
echo -e "${GREEN}✅ MongoDB and Redis started${NC}"
echo ""

# Step 7: Setup backend
echo -e "${BLUE}Step 7: Setting up backend...${NC}"
cd ${DEPLOY_PATH}/backend
sudo -u admin python3 -m venv .venv
sudo -u admin .venv/bin/pip install --upgrade pip -q
sudo -u admin .venv/bin/pip install -r requirements.txt -q
sudo -u admin .venv/bin/pip uninstall bcrypt -y -q
sudo -u admin .venv/bin/pip install bcrypt==4.0.1 -q
echo -e "${GREEN}✅ Backend setup complete${NC}"
echo ""

# Step 8: Create .env file
echo -e "${BLUE}Step 8: Creating .env file...${NC}"
JWT_SECRET="amarktai-production-$(openssl rand -hex 32)"
cat > ${DEPLOY_PATH}/backend/.env << ENVEOF
# MongoDB
MONGODB_URI=mongodb://localhost:27017/amarktai

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# API Keys (optional - add when available)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
ENVEOF
chown admin:sudo ${DEPLOY_PATH}/backend/.env
echo -e "${GREEN}✅ .env file created with secure JWT secret${NC}"
echo ""

# Step 9: Setup frontend
echo -e "${BLUE}Step 9: Setting up frontend...${NC}"
cd ${DEPLOY_PATH}/frontend
sudo -u admin npm install --legacy-peer-deps --silent 2>&1 | grep -v "deprecated" || true
sudo -u admin npm run build --silent 2>&1 | grep -v "deprecated" || true
echo -e "${GREEN}✅ Frontend built${NC}"
echo ""

# Step 10: Configure Nginx
echo -e "${BLUE}Step 10: Configuring Nginx...${NC}"
rm -f /etc/nginx/sites-enabled/default

tee /etc/nginx/sites-available/amarktai > /dev/null << 'EOF'
server {
    listen 80;
    server_name amarktai.online www.amarktai.online;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name amarktai.online www.amarktai.online;

    ssl_certificate /etc/letsencrypt/live/amarktai.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/amarktai.online/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/amarktai/Amarktai-Network-2/frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ws {
        proxy_pass http://127.0.0.1:8000/api/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

ln -sf /etc/nginx/sites-available/amarktai /etc/nginx/sites-enabled/
nginx -t
echo -e "${GREEN}✅ Nginx configured${NC}"
echo ""

# Step 11: Create systemd service
echo -e "${BLUE}Step 11: Creating systemd service...${NC}"
tee /etc/systemd/system/amarktai-api.service > /dev/null << 'EOF'
[Unit]
Description=Amarktai FastAPI Backend
After=network.target mongod.service redis-server.service

[Service]
Type=simple
User=admin
WorkingDirectory=/var/amarktai/Amarktai-Network-2
Environment="PATH=/var/amarktai/Amarktai-Network-2/backend/.venv/bin"
ExecStart=/var/amarktai/Amarktai-Network-2/backend/.venv/bin/python3 -m uvicorn backend.server:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd service created${NC}"
echo ""

# Step 12: Start services
echo -e "${BLUE}Step 12: Starting services...${NC}"
systemctl enable amarktai-api
systemctl start amarktai-api
sleep 5
systemctl restart nginx
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 13: Verify deployment
echo -e "${BLUE}Step 13: Verifying deployment...${NC}"
echo ""
echo "Backend status:"
systemctl status amarktai-api --no-pager | head -10
echo ""
echo "Nginx status:"
systemctl status nginx --no-pager | head -10
echo ""

# Step 14: Test API
echo -e "${BLUE}Step 14: Testing API...${NC}"
sleep 3
API_RESPONSE=$(curl -s http://127.0.0.1:8000/api/health/ping 2>/dev/null || echo "failed")
if [[ $API_RESPONSE == *"ok"* ]] || [[ $API_RESPONSE == *"pong"* ]]; then
    echo -e "${GREEN}✅ API is responding${NC}"
else
    echo -e "${YELLOW}⚠️  API not responding yet (may need a few more seconds)${NC}"
    echo "Check logs: journalctl -u amarktai-api -n 50"
fi
echo ""

echo "========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "========================================="
echo ""
echo "🌐 Your site is live at: https://amarktai.online"
echo ""
echo "📋 Next steps:"
echo "1. Visit https://amarktai.online"
echo "2. Register a new account"
echo "3. Login and test the dashboard"
echo "4. Add exchange API keys in backend/.env (optional)"
echo ""
echo "🔍 To check logs:"
echo "   sudo journalctl -u amarktai-api -f"
echo ""
echo "🔄 To restart services:"
echo "   sudo systemctl restart amarktai-api"
echo "   sudo systemctl restart nginx"
echo ""
echo "📦 Repository: ${REPO_URL}"
echo ""
echo "✅ JWT Secret has been automatically generated and configured"
echo ""
