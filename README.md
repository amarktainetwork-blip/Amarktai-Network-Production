# Amarktai Network - Production Trading Platform

**AI-Powered Trading** | **Multi-Exchange Support** | **Autonomous Systems**

Live at: [amarktai.online](https://amarktai.online)

---

## 🚀 Quick Deploy to VPS

```bash
# Clone repository
git clone https://github.com/amarktainetwork-blip/Amarktai-Network-Production.git /var/amarktai/Amarktai-Network-2
cd /var/amarktai/Amarktai-Network-2

# Run automated deployment
chmod +x deploy.sh
sudo ./deploy.sh
```

---

## 📋 What's Included

### ✅ Complete Codebase
- **Backend**: FastAPI + MongoDB + Redis
- **Frontend**: React + TailwindCSS
- **Trading Engine**: 292-line enhanced production engine
- **AI Engines**: GPT-4o, Claude, Gemini, DeepSeek
- **Dashboard**: 3,406-line professional UI
- **Assets**: 7.4MB images, videos, audio

### ✅ All Fixes Applied
- Database connection (load_dotenv)
- Profile endpoint (no logout issue)
- Bcrypt 4.0.1 compatibility
- Complete .env configuration

---

## 🏗️ Architecture

**Backend:**
- Python 3.12+, FastAPI, Uvicorn
- MongoDB for data, Redis for cache
- JWT authentication with bcrypt
- WebSocket for real-time updates

**Frontend:**
- React 18, craco build system
- TailwindCSS styling
- Real-time dashboard updates

**Deployment:**
- Nginx reverse proxy
- Systemd service management
- Let's Encrypt SSL

---

## 📦 Installation

### Prerequisites

```bash
# Ubuntu 22.04+ / Debian 11+
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
  nodejs npm mongodb redis-server nginx curl
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Fix bcrypt (critical!)
pip uninstall bcrypt -y
pip install bcrypt==4.0.1

# Configure environment
cp .env.example .env
nano .env
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Build for production
npm run build
```

---

## ⚙️ Configuration

### Backend .env

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/amarktai

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# API Keys (optional)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
```

---

## 🚀 Running

### Development

```bash
# Backend
cd backend
source .venv/bin/activate
python3 -m uvicorn backend.server:app --reload

# Frontend
cd frontend
npm start
```

### Production

```bash
# Use systemd service
sudo systemctl start amarktai-api
sudo systemctl enable amarktai-api

# Check status
sudo systemctl status amarktai-api
```

---

## 🌐 Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name amarktai.online;

    ssl_certificate /etc/letsencrypt/live/amarktai.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/amarktai.online/privkey.pem;

    root /var/amarktai/Amarktai-Network-2/frontend/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ws {
        proxy_pass http://127.0.0.1:8000/api/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📁 Project Structure

```
Amarktai-Network-2/
├── backend/
│   ├── routes/
│   │   ├── auth.py              # Login, register, profile
│   │   ├── trading.py           # Trading operations
│   │   └── ai_chat.py           # AI functionality
│   ├── engines/
│   │   ├── trading_engine_production.py  # 292 lines
│   │   ├── gpt4o_engine.py
│   │   └── ...
│   ├── emergentintegrations/    # Advanced integrations
│   ├── database.py              # MongoDB (with load_dotenv fix)
│   ├── auth.py                  # JWT utilities
│   └── server.py                # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard.js     # 3,406 lines
│   │   └── components/
│   └── public/
│       └── assets/              # 7.4MB media files
└── README.md
```

---

## 🔒 Security

- JWT authentication
- bcrypt 4.0.1 password hashing
- Environment variable secrets
- CORS protection
- SSL/TLS encryption

---

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/api/health/ping

# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'

# Profile (use token from login)
curl http://localhost:8000/api/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🐛 Troubleshooting

### Login Logs Out Immediately

**Fix**: Verify profile endpoint exists and database connection works

```bash
cd backend
source .venv/bin/activate
python3 -c "from backend.database import db; print('DB:', db)"
```

### Bcrypt Errors

```bash
pip uninstall bcrypt -y
pip install bcrypt==4.0.1
```

### Frontend Won't Build

```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run build
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `GET /api/auth/profile` - Get profile
- `GET /api/auth/me` - Current user

### Trading
- `GET /api/trading/portfolio` - Portfolio
- `POST /api/trading/execute` - Execute trade
- `GET /api/trading/history` - History
- `WS /api/ws` - Real-time updates

---

## 🎯 Features

- ✅ Multi-exchange trading (Luno, Binance, KuCoin, Kraken, VALR)
- ✅ AI autopilot with 4 AI engines
- ✅ Real-time portfolio tracking
- ✅ Advanced risk management
- ✅ Paper trading mode
- ✅ WebSocket updates
- ✅ Professional dashboard

---

## 📝 Version

**v2.1 Production**
- Fixed database connection
- Fixed profile endpoint
- Fixed bcrypt compatibility
- Enhanced trading engine
- Complete assets package

---

## 📄 License

Proprietary - Amarktai Network

---

## 📞 Support

- Website: https://amarktai.online
- GitHub Issues: Report bugs here

---

**Built for production. Deploy with confidence. 🚀**
