# Imagen base con Jupyter + PySpark
FROM jupyter/pyspark-notebook:latest

# Cambia al usuario administrador (root) para poder instalar programas
USER root

# Instala entorno visual, supervisor y Chrome
# Instalación de dependencias básicas
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates python3-distutils \
    xvfb fluxbox x11vnc supervisor novnc python3-websockify \
    libnss3 libgbm1 libasound2 \
    --no-install-recommends

# Instalación de Google Chrome (Método moderno de llaves)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
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