#!/bin/bash
# PadelMind Pi — one-command setup
# Run on the Pi after SSH: bash install.sh
set -e

echo "=== PadelMind Recorder Setup ==="

# System packages
sudo apt-get update -q
sudo apt-get install -y ffmpeg python3-pip python3-venv v4l-utils

# App directory
APP_DIR=/home/pi/padelmind-recorder
mkdir -p "$APP_DIR"
cp recorder.py "$APP_DIR/"
cp requirements.txt "$APP_DIR/"

# Check config.env exists
if [ ! -f "$APP_DIR/config.env" ]; then
  cp config.env.example "$APP_DIR/config.env"
  echo ""
  echo "⚠️  config.env created from example. Fill in credentials before starting:"
  echo "    nano $APP_DIR/config.env"
  echo ""
fi

# Python virtualenv
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet -r requirements.txt

# systemd service
sudo cp padelmind-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable padelmind-recorder

echo ""
echo "=== Camera devices on this Pi ==="
v4l2-ctl --list-devices 2>/dev/null || echo "(no cameras detected yet)"

echo ""
echo "=== Done ==="
echo "After filling in config.env, start the service:"
echo "  sudo systemctl start padelmind-recorder"
echo "  sudo systemctl status padelmind-recorder"
echo ""
echo "Tail live logs:"
echo "  tail -f /var/log/padelmind-recorder.log"
echo ""
echo "Test endpoints (from Mac on same network):"
echo "  curl http://<pi-ip>:5000/ping"
echo "  curl http://<pi-ip>:5000/status"
