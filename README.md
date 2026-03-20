# KrishiSarth 🌱

> Smart Water Management System for Precision Irrigation and Fertigation

KrishiSarth (कृषिसार्थ — "meaningful farming") is an IoT + AI platform that gives Indian farmers real-time visibility and intelligent control over irrigation and fertigation across their fields.

---

## What it does

- Collects live soil moisture, temperature, EC, and water quality data from ESP32 sensor nodes via LoRa mesh networking
- Runs LSTM + Random Forest models to decide when, how much, and what to irrigate — factoring in weather forecasts, crop stage, and soil profiles
- Lets farmers view and control every zone from a mobile-friendly web dashboard
- Delivers clear decisions in plain language: "Skip irrigation today — 80% rain forecast, saving 20L"

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML · JavaScript · Tailwind CSS · PWA |
| Backend | FastAPI · Python 3.11 |
| Primary DB | PostgreSQL 15 (farms, zones, schedules, logs) |
| Time-series DB | InfluxDB 2.x (sensor readings) |
| Cache / Queue | Redis 7 |
| Message broker | Mosquitto MQTT |
| Task runner | Celery |
| ML models | Keras LSTM · scikit-learn Random Forest |
| Firmware | Arduino C++ on ESP32 (PlatformIO) |
| Hosting | Render (MVP) → AWS (production) |
| File storage | AWS S3 (ML models, CSV exports) |

---

## Repository layout

```
krishisarth/
├── backend/          FastAPI service, Celery workers, MQTT subscriber, ML engine
├── frontend/         Single-page web app + PWA manifest
├── firmware/         ESP32 sensor node + Pi gateway code (PlatformIO)
├── docker-compose.yml  Local dev: Postgres + InfluxDB + Redis + MQTT
├── Makefile          Shortcuts: make dev, make test, make migrate, make deploy
├── .env.example      All required environment variables documented
├── README.md         This file
├── PROJECT_SPEC.md   Full technical specification
└── TODO.md           Backlog and milestone tracker
```

---

## Quick start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- PlatformIO CLI (for firmware only)

### 1. Clone and configure

```bash
git clone https://github.com/yourorg/krishisarth.git
cd krishisarth
cp .env.example .env
# Fill in: JWT_SECRET, DB credentials, InfluxDB token, OpenWeather API key
```

### 2. Start infrastructure

```bash
docker-compose up -d
# Starts: PostgreSQL · InfluxDB · Redis · Mosquitto MQTT
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head           # run migrations
uvicorn main:app --reload      # API at http://localhost:8000
celery -A app.workers.celery_app worker --loglevel=info   # task worker
python -m app.mqtt.client      # MQTT subscriber
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

### 5. Firmware (optional — field hardware)

```bash
cd firmware
pio run --target upload        # flash to connected ESP32
```

---

## API

Base URL: `https://api.krishisarth.in/v1`

All protected endpoints require: `Authorization: Bearer <jwt_token>`

Key endpoint groups:

| Group | Endpoints |
|-------|-----------|
| Auth | POST /auth/register, /login, /refresh |
| Farms | GET/POST /farms, GET /farms/:id |
| Zones | GET/POST /farms/:id/zones, PATCH /zones/:id |
| Dashboard | GET /farms/:id/dashboard |
| Control | POST /zones/:id/irrigate, /stop, /fertigation |
| AI | GET /zones/:id/ai-decisions, POST run |
| Analytics | GET /farms/:id/analytics, /export |
| Alerts | GET /farms/:id/alerts, PATCH /alerts/:id/read |

Full API specification: see `PROJECT_SPEC.md → Section 6`

---

## Environment variables

See `.env.example` for the complete list. Key variables:

```env
DATABASE_URL=postgresql://user:pass@localhost/krishisarth
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-256-bit-secret
JWT_REFRESH_SECRET=your-other-256-bit-secret
OPENWEATHER_API_KEY=your-key
MQTT_BROKER_HOST=localhost
AWS_S3_BUCKET=krishisarth-ml-models
```

---

## Running tests

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Contributing

1. Create a feature branch: `git checkout -b feat/zone-heatmap`
2. Run tests before pushing
3. Open a pull request against `main`
4. CI must pass (lint + tests) before merge

---

## License

MIT — see LICENSE file.

---

*KrishiSarth — Smart farming for every acre*
