# Imagen base: trae Jupyter + Python + PySpark ya configurado
FROM jupyter/pyspark-notebook:latest

USER root

# 1. Actualiza repositorios e instala herramientas básicas
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
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

# 2. Instala librerías de Python (INCLUYE PYSPARK EXPLÍCITAMENTE)
RUN pip install --upgrade pip && \
    pip install pyspark==3.4.0 selenium pymongo webdriver-manager

# 3. Descarga el JAR de MongoDB Spark Connector
RUN mkdir -p /opt/spark-jars && \
    cd /opt/spark-jars && \
    wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.1.1/mongo-spark-connector_2.12-10.1.1.jar

USER jovyan

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=''", "--ServerApp.password=''"]