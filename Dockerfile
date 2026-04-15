# Imagen base con Jupyter + PySpark
FROM jupyter/pyspark-notebook:latest

USER root

# 1. Instala entorno visual, supervisor, herramientas de red y Google Chrome
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
    && mkdir -p /etc/apt/keyrings \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala librerías Python (Scraping + Base de Datos + Pandas)
RUN pip install --upgrade pip && \
    pip install pyspark==3.4.0 selenium pymongo webdriver-manager pandas

# 3. Descarga el JAR de MongoDB Spark Connector
RUN mkdir -p /opt/spark-jars && \
    cd /opt/spark-jars && \
    wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.1.1/mongo-spark-connector_2.12-10.1.1.jar

# 4. Variables del entorno gráfico
ENV DISPLAY=:99
ENV SCREEN_WIDTH=1366
ENV SCREEN_HEIGHT=768
ENV SCREEN_DEPTH=24

# 5. Copia archivos de inicio
COPY start-vnc.sh /usr/local/bin/start-vnc.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 6. Convierte saltos de línea Windows a Linux y da permisos
RUN sed -i 's/\r$//' /usr/local/bin/start-vnc.sh && chmod +x /usr/local/bin/start-vnc.sh

# 7. Puertos del contenedor
EXPOSE 8888 5900 6080 4040

# 8. Inicia supervisord (gestiona Jupyter y el entorno visual)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]