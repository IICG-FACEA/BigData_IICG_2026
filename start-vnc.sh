#!/bin/bash
set -e

export DISPLAY=:99
export XDG_RUNTIME_DIR=/tmp/runtime-root

mkdir -p /tmp/runtime-root
chmod 700 /tmp/runtime-root
rm -f /tmp/.X99-lock

Xvfb :99 -screen 0 1366x768x24 &
sleep 2

fluxbox &
x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 &
websockify --web=/usr/share/novnc/ 6080 localhost:5900 &

exec start-notebook.sh --ip=0.0.0.0 --port=8888 --no-browser --allow-root --ServerApp.token='' --ServerApp.password=''