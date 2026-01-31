# KAVACH-INFINITY 🛡️

## AI-Powered Critical Infrastructure Protection Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

---

## 🌟 Overview

KAVACH-INFINITY is a **production-grade, AI-powered safety monitoring platform** designed for critical infrastructure protection across multiple domains:

- 🚂 **Railways & Metro** - Train detection, level crossing protection
- ⚡ **Power & Utilities** - Grid monitoring, substation protection
- 🏭 **Industrial Safety** - Manufacturing, hazardous materials
- 🏙️ **Smart Cities** - Traffic, environmental monitoring
- 🔒 **IT/OT Security** - Network monitoring, SCADA protection

### Key Features

- **Real-time Monitoring** - Live sensor data with WebSocket streaming
- **AI-Powered Anomaly Detection** - Isolation Forest & statistical methods
- **Predictive Analytics** - Failure prediction with ML models
- **Multi-factor Risk Scoring** - Comprehensive risk assessment
- **Role-Based Access Control** - 5-tier permission system
- **Beautiful Dashboards** - Dark/Light mode, real-time charts
- **Emergency Response** - Automated safety protocols
- **Audit Trail** - Complete logging for compliance

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/kavach-infinity.git
cd kavach-infinity

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001 (admin/kavach_admin_2024)
```

### Option 2: Manual Setup

#### Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run database migrations
# (Ensure PostgreSQL is running)

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env.local

# Start development server
npm run dev
```

---

## 📁 Project Structure

```
kavach-infinity/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API Routes
│   │   │   └── v1/
│   │   │       ├── endpoints/ # All endpoints
│   │   │       ├── deps.py    # Dependencies
│   │   │       └── router.py  # Main router
│   │   ├── config/            # Configuration
│   │   ├── core/              # Core modules
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic
│   │   │   ├── ai/           # ML services
│   │   │   ├── realtime/     # WebSocket
│   │   │   └── safety/       # Safety automation
│   │   └── main.py           # Application entry
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/              # App router pages
│   │   │   ├── dashboard/    # Dashboard pages
│   │   │   └── login/        # Auth pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   └── lib/              # Utilities
│   ├── package.json
│   └── Dockerfile
│
├── docker/                     # Docker configs
│   ├── init.sql              # DB initialization
│   └── prometheus.yml        # Monitoring config
│
└── docker-compose.yml         # Full stack deployment
```

---

## 🔧 API Documentation

### Authentication

```bash
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "Admin@123"
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/stats` | GET | Dashboard statistics |
| `/api/v1/sites` | GET/POST | Site management |
| `/api/v1/sensors/{id}/data` | POST | Ingest sensor data |
| `/api/v1/alerts` | GET | List alerts |
| `/api/v1/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/api/v1/ai/detect-anomaly` | POST | Run anomaly detection |
| `/api/v1/ai/risk-score/{site_id}` | GET | Get risk score |
| `/api/v1/safety/emergency-stop/{site_id}` | POST | Trigger E-stop |

### WebSocket Connections

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/connect');

// Subscribe to rooms
ws.send(JSON.stringify({
  type: 'subscribe',
  rooms: ['alerts', 'sensors', 'safety']
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

---

## 🤖 AI/ML Capabilities

### Anomaly Detection

- **Isolation Forest** - Multivariate anomaly detection
- **Statistical Thresholds** - Min/max violations
- **Rate of Change** - Sudden value changes
- **Pattern Recognition** - Known failure modes

### Risk Scoring

Multi-factor risk calculation:
- Sensor health (20%)
- Active alerts (30%)
- Historical incidents (20%)
- Anomaly trends (15%)
- Environmental factors (10%)
- Time patterns (5%)

### Failure Prediction

- Sensor degradation analysis
- Equipment lifecycle modeling
- Maintenance scheduling

---

## 🔐 Security

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| Super Admin | Full system access |
| Admin | Site management, user management |
| Operator | Alert handling, sensor monitoring |
| Analyst | Read-only, reports, analytics |
| Viewer | Dashboard viewing only |

### Security Features

- JWT authentication with refresh tokens
- Password hashing with bcrypt
- Rate limiting
- CORS protection
- Audit logging
- Input validation

---

## 📊 Monitoring

### Prometheus Metrics

- Request latency
- Error rates
- Active connections
- Alert counts

### Grafana Dashboards

Access at `http://localhost:3001`:
- System overview
- Alert trends
- Sensor health
- AI model performance

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm run test
```

---

## 📝 Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `ENVIRONMENT` | development/production | development |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | http://localhost:8000 |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | ws://localhost:8000 |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- Next.js for the React framework
- Tailwind CSS for styling
- scikit-learn for ML algorithms

---

**Built with ❤️ for safer critical infrastructure**

---

## 📞 Support

- 📧 Email: support@kavach.io
- 📖 Documentation: https://docs.kavach.io
- 🐛 Issues: https://github.com/your-org/kavach-infinity/issues
