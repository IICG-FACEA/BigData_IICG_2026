#!/bin/bash
Xvfb :0 -screen 0 1366x768x24 &
sleep 2
fluxbox &
sleep 2
x11vnc -display :0 -nopw -forever -shared -rfbport 5900 &
sleep 2
cd /opt/noVNC && ./utils/novnc_proxy --vnc localhost:5900 --listen 6080 --web . &
start-notebook.sh --NotebookApp.token='' --NotebookApp.password=''

