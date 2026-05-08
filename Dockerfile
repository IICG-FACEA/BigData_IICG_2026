# Imagen base: trae Jupyter + Python + PySpark ya configurado
FROM jupyter/pyspark-notebook:latest

# Cambia al usuario administrador (root) para poder instalar programas
USER root

# 1. Instala entorno visual, supervisor, Chrome y dependencias
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    openssl \
    xvfb \
    fluxbox \
    x11vnc \
    supervisor \
    git \
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

# 2. Instala librerías Python necesarias
RUN pip install selenium pymongo webdriver-manager pandas pyspark==3.5.0

# 3. Instala JARs de MongoDB Spark Connector (versión 10.3.0 compatible con Spark 3.5 + Scala 2.12)
RUN rm -f /usr/local/spark/jars/mongo-spark-connector* && \
    rm -f /usr/local/spark/jars/mongodb-driver* && \
    rm -f /usr/local/spark/jars/bson* && \
    wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.3.0/mongo-spark-connector_2.12-10.3.0.jar -P /usr/local/spark/jars/ && \
    wget https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-sync/4.11.1/mongodb-driver-sync-4.11.1.jar -P /usr/local/spark/jars/ && \
    wget https://repo1.maven.org/maven2/org/mongodb/mongodb-driver-core/4.11.1/mongodb-driver-core-4.11.1.jar -P /usr/local/spark/jars/ && \
<<<<<<< HEAD
    wget https://repo1.maven.org/maven2/org/mongodb/bson/4.11.1/bson-4.11.1.jar -P /usr/local/spark/jars/

# 4. Instala noVNC desde GitHub y websockify
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC \
    && git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify \
    && ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html
=======
    wget https://repo1.maven.org/maven2/org/mongodb/bson/4.11.1/bson-4.11.1.jar -P /usr/local/spark/jars/ && \
    wget https://repo1.maven.org/maven2/org/mongodb/bson-record-codec/4.11.1/bson-record-codec-4.11.1.jar -P /usr/local/spark/jars/

# 3. Librer�as de Python para todo el curso (Scraping + Atlas + Spark)
RUN pip install --no-cache-dir --upgrade pip && \
    #pip install --no-cache-dir "pymongo[srv]" dnspython certifi selenium webdriver-manager pandas
    pip install --no-cache-dir "pymongo[srv]" dnspython selenium webdriver-manager pandas certifi

>>>>>>> origin/main

    

# Configura variable de entorno para Xvfb
ENV DISPLAY=:0

# Vuelve al usuario normal de Jupyter (buena práctica de seguridad)
USER jovyan
