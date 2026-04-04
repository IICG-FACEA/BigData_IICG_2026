# Imagen base: trae Jupyter + Python + PySpark ya configurado
FROM jupyter/pyspark-notebook:latest

# Cambia al usuario administrador (root) para poder instalar programas
USER root

<<<<<<< HEAD
# 1. Actualiza repositorios e instala herramientas básicas, instala Google Chrome y librerías necesarias
=======
>>>>>>> 028e3b7a5ae5d666ed330ac8f30c6303f183c54f
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
<<<<<<< HEAD
    ca-certificates && \
    mkdir -p /etc/apt/keyrings && \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y \
    google-chrome-stable \
    libnss3 \
    libgbm1 \
    libasound2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# 2. Instala librerías de Python necesarias
RUN pip install selenium pymongo webdriver-manager

# Vuelve al usuario normal de Jupyter (buena práctica de seguridad)
USER jovyan
=======
    ca-certificates \
    xvfb \
    fluxbox \
    x11vnc \
    supervisor \
    python3-websockify \
    novnc \
    libnss3 \
    libgbm1 \
    libasound2 \
    && mkdir -p /etc/apt/keyrings && \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install selenium pymongo webdriver-manager pandas

ENV DISPLAY=:99
ENV SCREEN_WIDTH=1366
ENV SCREEN_HEIGHT=768
ENV SCREEN_DEPTH=24

COPY start-vnc.sh /usr/local/bin/start-vnc.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chmod +x /usr/local/bin/start-vnc.sh

EXPOSE 8888 5900 6080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

USER root
>>>>>>> 028e3b7a5ae5d666ed330ac8f30c6303f183c54f
