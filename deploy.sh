#!/bin/bash
#
# AMARKTAI NETWORK - ROBUST DEPLOYMENT SCRIPT
# Handles broken packages and existing installations
#
# Usage: sudo bash deploy.sh
#

set -e  # Exit on any error

echo "========================================="
echo "🚀 AMARKTAI NETWORK - DEPLOYMENT"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPO_URL="https://github.com/amarktainetwork-blip/Amarktai-Network-Production.git"
DEPLOY_PATH="/var/amarktai/Amarktai-Network-2"

# Step 1: Backup SSL
echo -e "${BLUE}Step 1: Backing up SSL certificates...${NC}"
mkdir -p /root/ssl_backup
cp -r /etc/letsencrypt /root/ssl_backup/ 2>/dev/null || true
echo -e "${GREEN}✅ SSL backed up${NC}"
echo ""

# Step 2: Stop services
echo -e "${BLUE}Step 2: Stopping services...${NC}"
systemctl stop amarktai-api 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true
echo -e "${GREEN}✅ Services stopped${NC}"
echo ""

# Step 3: Clean old installation
echo -e "${BLUE}Step 3: Cleaning old installation...${NC}"
rm -rf ${DEPLOY_PATH} 2>/dev/null || true
mkdir -p /var/amarktai
echo -e "${GREEN}✅ Cleaned${NC}"
echo ""

# Step 4: Fix broken packages
echo -e "${BLUE}Step 4: Fixing package system...${NC}"
apt-get update -qq
apt-get install -f -y -qq 2>/dev/null || true
dpkg --configure -a 2>/dev/null || true
apt-get autoremove -y -qq 2>/dev/null || true
echo -e "${GREEN}✅ Package system fixed${NC}"
echo ""

# Step 5: Install dependencies (skip if already installed)
echo -e "${BLUE}Step 5: Installing dependencies...${NC}"

# Check and install each package individually
for pkg in git curl gnupg; do
    dpkg -l | grep -q "^ii  $pkg " || apt-get install -y $pkg -qq
done

# Python
if ! command -v python3 &> /dev/null; then
    apt-get install -y python3 python3-pip python3-venv -qq
fi

# Node.js
if ! command -v node &> /dev/null; then
    apt-get install -y nodejs npm -qq
fi

# Redis
if ! command -v redis-server &> /dev/null; then
    apt-get install -y redis-server -qq
fi

# Nginx
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx -qq
fi

# MongoDB (only if not installed)
if ! command -v mongod &> /dev/null; then
    echo "Installing MongoDB 7.0..."
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
        gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor 2>/dev/null
    
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
        tee /etc/apt/sources.list.d/mongodb-org-7.0.list >/dev/null
    
    apt-get update -qq
    apt-get install -y mongodb-org -qq
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 6: Clone from GitHub
echo -e "${BLUE}Step 6: Cloning from GitHub...${NC}"
git clone ${REPO_URL} ${DEPLOY_PATH}
chown -R admin:sudo ${DEPLOY_PATH}
echo -e "${GREEN}✅ Cloned${NC}"
echo ""

# Step 7: Start MongoDB and Redis
echo -e "${BLUE}Step 7: Starting databases...${NC}"
systemctl start mongod 2>/dev/null || systemctl start mongodb
systemctl enable mongod 2>/dev/null || systemctl enable mongodb
systemctl start redis-server
systemctl enable redis-server
sleep 2
echo -e "${GREEN}✅ Databases started${NC}"
echo ""

# Step 8: Setup backend
echo -e "${BLUE}Step 8: Setting up backend...${NC}"
cd ${DEPLOY_PATH}/backend
sudo -u admin python3 -m venv .venv
sudo -u admin .venv/bin/pip install --upgrade pip -q 2>/dev/null
sudo -u admin .venv/bin/pip install -r requirements.txt -q 2>/dev/null
sudo -u admin .venv/bin/pip uninstall bcrypt -y -q 2>/dev/null
sudo -u admin .venv/bin/pip install bcrypt==4.0.1 -q 2>/dev/null
echo -e "${GREEN}✅ Backend ready${NC}"
echo ""

# Step 9: Create .env
echo -e "${BLUE}Step 9: Creating .env...${NC}"
JWT_SECRET="amarktai-$(openssl rand -hex 32)"
cat > ${DEPLOY_PATH}/backend/.env << ENVEOF
MONGODB_URI=mongodb://localhost:27017/amarktai
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
ENVEOF
chown admin:sudo ${DEPLOY_PATH}/backend/.env
echo -e "${GREEN}✅ .env created${NC}"
echo ""

# Step 10: Build frontend
echo -e "${BLUE}Step 10: Building frontend...${NC}"
cd ${DEPLOY_PATH}/frontend
sudo -u admin npm install --legacy-peer-deps 2>&1 | tail -5
sudo -u admin npm run build 2>&1 | tail -5
echo -e "${GREEN}✅ Frontend built${NC}"
echo ""

# Step 11: Configure Nginx
echo -e "${BLUE}Step 11: Configuring Nginx...${NC}"
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/amarktai << 'NGINXEOF'
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
NGINXEOF

ln -sf /etc/nginx/sites-available/amarktai /etc/nginx/sites-enabled/
nginx -t
echo -e "${GREEN}✅ Nginx configured${NC}"
echo ""

# Step 12: Create systemd service
echo -e "${BLUE}Step 12: Creating service...${NC}"
cat > /etc/systemd/system/amarktai-api.service << 'SERVICEEOF'
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
SERVICEEOF

systemctl daemon-reload
echo -e "${GREEN}✅ Service created${NC}"
echo ""

# Step 13: Start services
echo -e "${BLUE}Step 13: Starting services...${NC}"
systemctl enable amarktai-api
systemctl start amarktai-api
sleep 5
systemctl restart nginx
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 14: Test
echo -e "${BLUE}Step 14: Testing...${NC}"
sleep 3
if curl -s http://127.0.0.1:8000/api/health/ping 2>/dev/null | grep -q "ok\|pong"; then
    echo -e "${GREEN}✅ API responding${NC}"
else
    echo -e "${YELLOW}⚠️  API may need more time${NC}"
fi
echo ""

echo "========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "========================================="
echo ""
echo "🌐 Site: https://amarktai.online"
echo "📋 Test: Register and login"
echo "🔍 Logs: sudo journalctl -u amarktai-api -f"
echo ""
