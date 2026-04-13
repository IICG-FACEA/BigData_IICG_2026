# Imagen base con Jupyter + PySpark
FROM jupyter/pyspark-notebook:latest

USER root

# Instala entorno visual, supervisor y Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
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
    sed \
    unzip \
    fonts-liberation \
    libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome (forma estable)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Instala librerías Python para scraping y MongoDB
RUN pip install selenium pymongo webdriver-manager pandas

# Variables del entorno gráfico
ENV DISPLAY=:99
ENV SCREEN_WIDTH=1366
ENV SCREEN_HEIGHT=768
ENV SCREEN_DEPTH=24

# Copia archivos de inicio
COPY start-vnc.sh /usr/local/bin/start-vnc.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Convierte saltos de línea Windows a Linux y da permisos
RUN sed -i 's/\r$//' /usr/local/bin/start-vnc.sh && chmod +x /usr/local/bin/start-vnc.sh

# Puertos del contenedor
EXPOSE 8888 5900 6080 4040

# Inicia supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]