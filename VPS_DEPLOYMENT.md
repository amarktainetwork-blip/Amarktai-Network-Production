# 🚀 Amarktai Network - VPS Deployment Guide (Webdock Ubuntu 24.04)

## Target Environment

- **VPS:** Webdock (Ubuntu 24.04)
- **Backend:** `/var/amarktai/backend`
- **Frontend:** `/var/amarktai/frontend`
- **Python:** 3.11+
- **Database:** MongoDB (localhost)
- **Web Server:** Nginx (reverse proxy)
- **Process Manager:** systemd

---

## Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  nodejs \
  npm \
  mongodb \
  nginx \
  git \
  certbot \
  python3-certbot-nginx

# Verify installations
python3.11 --version
node --version
mongod --version
nginx -v
```

---

## Step 1: Clone Repository

```bash
# Create directory
sudo mkdir -p /var/amarktai
sudo chown -R $USER:$USER /var/amarktai

# Clone (replace with your repo URL)
cd /var
git clone <your-repo-url> amarktai
cd amarktai
```

---

## Step 2: Backend Setup

### 2.1 Python Virtual Environment

```bash
cd /var/amarktai/backend

# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Environment Configuration

```bash
# Copy example env
cp .env.example .env

# Edit with your values
nano .env
```

**Critical values to set:**
```env
JWT_SECRET=<generate-strong-secret-32+chars>
ADMIN_PASSWORD=<your-secure-password>
OPENAI_API_KEY=sk-proj-...
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<gmail-app-password>
```

**Generate strong JWT secret:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2.3 Test Backend

```bash
# Activate venv
source .venv/bin/activate

# Test run
uvicorn server:app --host 127.0.0.1 --port 8000

# Should see: "Application startup complete"
# Press Ctrl+C to stop
```

---

## Step 3: MongoDB Setup

```bash
# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify
sudo systemctl status mongod

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

**Database will be auto-created on first backend run.**

---

## Step 4: Frontend Setup

```bash
cd /var/amarktai/frontend

# Install dependencies
npm install

# Copy environment
cp .env.example .env

# Edit
nano .env
```

**Set your domain:**
```env
REACT_APP_BACKEND_URL=https://your-domain.com
```

### Build for Production

```bash
npm run build

# Output will be in ./build/
ls -la build/
```

---

## Step 5: systemd Service

### 5.1 Create Service File

```bash
sudo nano /etc/systemd/system/amarktai-api.service
```

**Service configuration:**
```ini
[Unit]
Description=Amarktai Network Trading API
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/amarktai/backend
EnvironmentFile=/var/amarktai/backend/.env

ExecStart=/var/amarktai/backend/.venv/bin/uvicorn server:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 2 \
  --log-level info

# Restart policy
Restart=always
RestartSec=10

# Limits
LimitNOFILE=65536

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=amarktai-api

[Install]
WantedBy=multi-user.target
```

### 5.2 Set Permissions

```bash
# Set ownership
sudo chown -R www-data:www-data /var/amarktai

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable amarktai-api

# Start service
sudo systemctl start amarktai-api

# Check status
sudo systemctl status amarktai-api

# View logs
sudo journalctl -u amarktai-api -f
```

---

## Step 6: Nginx Configuration

### 6.1 Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/amarktai
```

**Configuration:**
```nginx
# Amarktai Network - Nginx Configuration

upstream amarktai_backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS (will be configured by certbot)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (certbot will add these)
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
    
    # Frontend (React build)
    location / {
        root /var/amarktai/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api {
        proxy_pass http://amarktai_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket
    location /api/ws {
        proxy_pass http://amarktai_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Long timeout for WebSocket
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # SSE (Server-Sent Events)
    location ~* /api/.*/stream$ {
        proxy_pass http://amarktai_backend;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;
        
        # Long timeout
        proxy_read_timeout 3600s;
        
        # Required headers
        add_header Cache-Control "no-cache";
        add_header X-Accel-Buffering "no";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 6.2 Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/amarktai /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Step 7: SSL Certificate (Let's Encrypt)

```bash
# Install cert and auto-configure Nginx
sudo certbot --nginx -d your-domain.com

# Certbot will:
# 1. Issue SSL certificate
# 2. Modify Nginx config to use it
# 3. Setup auto-renewal

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Step 8: Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Step 9: Create Admin User

```bash
cd /var/amarktai/backend
source .venv/bin/activate

python3 << 'EOF'
import asyncio
from database import users_collection
from auth import get_password_hash
from uuid import uuid4
from datetime import datetime, timezone

async def create_admin():
    admin = {
        "id": str(uuid4()),
        "email": "admin@amarktai.com",
        "password": get_password_hash("YourStrongPassword123!"),
        "first_name": "Admin",
        "role": "admin",
        "currency": "ZAR",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await users_collection.insert_one(admin)
    print(f"✅ Admin created: {admin['email']}")

asyncio.run(create_admin())
EOF
```

---

## Step 10: Verify Deployment

### Backend Health Check

```bash
# Via curl
curl https://your-domain.com/api/health

# Check systemd
sudo systemctl status amarktai-api

# View logs
sudo journalctl -u amarktai-api -n 100
```

### Frontend Check

```bash
# Visit in browser
https://your-domain.com

# Should see:
# - Login page loads
# - No console errors
# - Can register/login
```

### Database Check

```bash
mongosh

use amarktai_trading

# Check collections created
show collections

# Check users
db.users.find().pretty()

exit
```

---

## Maintenance Commands

### Restart Backend

```bash
sudo systemctl restart amarktai-api
```

### Update Code

```bash
cd /var/amarktai
git pull origin main

# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart amarktai-api

# Frontend
cd ../frontend
npm install
npm run build
```

### View Logs

```bash
# Real-time backend logs
sudo journalctl -u amarktai-api -f

# Last 100 lines
sudo journalctl -u amarktai-api -n 100

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Database Backup

```bash
# Backup
mongodump --db=amarktai_trading --out=/var/backups/mongo/$(date +%Y%m%d)

# Restore
mongorestore --db=amarktai_trading /var/backups/mongo/20240101/amarktai_trading
```

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
sudo journalctl -u amarktai-api -n 50

# Common issues:
# - MongoDB not running: sudo systemctl start mongod
# - Port 8000 in use: sudo lsof -i :8000
# - Missing dependencies: pip install -r requirements.txt
# - Wrong .env values: check JWT_SECRET, MONGO_URL
```

### Frontend blank page

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Rebuild frontend
cd /var/amarktai/frontend
npm run build

# Check build directory exists
ls -la build/
```

### WebSocket not connecting

```bash
# Check Nginx config includes WebSocket proxy
sudo nginx -t
sudo systemctl reload nginx

# Check browser console for WS errors
# Should connect to: wss://your-domain.com/api/ws
```

---

## Production Checklist

- [ ] VPS provisioned (Ubuntu 24.04)
- [ ] Domain pointing to VPS IP
- [ ] Repository cloned to /var/amarktai
- [ ] Backend .env configured
- [ ] Frontend .env configured
- [ ] Python dependencies installed
- [ ] Frontend built
- [ ] MongoDB running
- [ ] systemd service enabled
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Admin user created
- [ ] Health checks passing
- [ ] Logs clean (no errors)
- [ ] WebSocket connecting
- [ ] Real-time updates working

---

## Support

**Logs Location:**
- Backend: `sudo journalctl -u amarktai-api`
- Nginx: `/var/log/nginx/`
- MongoDB: `/var/log/mongodb/mongod.log`

**Configuration Files:**
- Backend: `/var/amarktai/backend/.env`
- Frontend: `/var/amarktai/frontend/.env`
- systemd: `/etc/systemd/system/amarktai-api.service`
- Nginx: `/etc/nginx/sites-available/amarktai`

---

**System is now live and production-ready! 🚀**
