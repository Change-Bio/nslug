# Slug Pump Control

Web-based control system for a peristaltic pump with live WebRTC video streaming. Runs on a Raspberry Pi with a React + TypeScript frontend and Flask backend.

## Structure

```
slug_pump_control/
├── pump.py               # Standalone CLI for pump control
├── deploy.sh             # Build frontend & deploy to Pi
├── backend/
│   ├── app.py            # Flask API server (runs on Pi)
│   └── requirements.txt
├── frontend/             # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── VideoFeed.tsx    # WebRTC camera feed
│   │   │   └── PumpControls.tsx # Pump control UI
│   │   ├── services/
│   │   │   ├── api.ts           # Pump API client
│   │   │   └── whep.ts          # WebRTC WHEP client
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── infra/
    └── cloudflare-tunnel.yml.template
```

## Hardware

- Raspberry Pi with GPIO access
- Stepper motor on GPIO 17 (STEP) and GPIO 27 (DIR), 1/32 microstepping (6400 steps/rev)
- Camera module (streamed via MediaMTX)

## CLI Usage

```bash
python3 pump.py <turns> <forward|backward>
```

## Web Server Setup

### Backend (on Pi)

```bash
cd backend
pip3 install -r requirements.txt
python3 app.py
```

Runs on `http://0.0.0.0:5000`. Supports mock mode when GPIO is unavailable.

### Frontend (development)

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000` with API proxy to the backend.

## Deploy

```bash
PI_HOST=user@your-pi-ip ./deploy.sh
```

Builds the frontend, copies everything to the Pi, and restarts the backend.

## Environment Variables

### Deploy (`deploy.sh`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PI_HOST` | Yes | - | SSH target, e.g. `user@192.168.1.100` |
| `PI_DEPLOY_DIR` | No | `~/slug_pump_control` | Install path on Pi |

### Backend (`app.py`)

| Variable | Default | Description |
|----------|---------|-------------|
| `PUMP_STEP_PIN` | `17` | GPIO pin for stepper STEP signal |
| `PUMP_DIR_PIN` | `27` | GPIO pin for stepper DIR signal |
| `PUMP_STEPS_PER_REV` | `6400` | Steps per revolution (microstepping) |
| `PUMP_SERVER_PORT` | `5000` | Flask server port |

## API

- `GET /api/health` - Health check
- `GET /api/pump/status` - Pump status (running, mode, turns_remaining)
- `POST /api/pump/move` - Start pump: `{"turns": 1.5, "mode": "forward"}`
- `POST /api/pump/stop` - Emergency stop

## Cloudflare Tunnel

See `infra/cloudflare-tunnel.yml.template` for exposing the app publicly with WebRTC video streaming through Cloudflare Tunnel.
