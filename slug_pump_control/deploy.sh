#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PI_HOST="${PI_HOST:?Set PI_HOST (e.g. nslug@192.168.1.100)}"
PI_DEPLOY_DIR="${PI_DEPLOY_DIR:-~/slug_pump_control}"

echo "Building frontend..."
cd frontend
npm run build

echo "Copying files to Pi ($PI_HOST)..."
ssh "$PI_HOST" "mkdir -p $PI_DEPLOY_DIR/{backend,frontend/dist}"
scp -r dist/* "$PI_HOST:$PI_DEPLOY_DIR/frontend/dist/"
scp "$SCRIPT_DIR/backend/app.py" "$PI_HOST:$PI_DEPLOY_DIR/backend/"
scp "$SCRIPT_DIR/backend/requirements.txt" "$PI_HOST:$PI_DEPLOY_DIR/backend/"
scp "$SCRIPT_DIR/pump.py" "$PI_HOST:$PI_DEPLOY_DIR/"

echo "Restarting backend on Pi..."
ssh "$PI_HOST" "sudo pkill -f 'python3.*app.py' || true && cd $PI_DEPLOY_DIR/backend && sudo python3 app.py > /tmp/pump-backend.log 2>&1 &"

echo "Deploy complete!"
