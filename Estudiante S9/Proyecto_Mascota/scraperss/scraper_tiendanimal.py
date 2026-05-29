# ============================================================
# Proyecto Big Data: Inteligencia de Mercado en Productos para Mascotas
# Entregable 1: Captura y almacenamiento de datos crudos
# Archivo: scraperss/scraper_tiendanimal.py
# ============================================================

# ============================================================
# ETAPA 1: PREPARACIÓN DEL ENTORNO
# ============================================================

# Paso 1.1: Importar librerías necesarias

# Imports Estandar Python 
import os
import re
import time
# Librerias Externas
import requests
import pandas as pd
# Imports Específicos
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from IPython.display import display
# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# Webdriver
from webdriver_manager.chrome import ChromeDriverManager
# PySpark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, regexp_extract, when, lit, round


# Paso 1.2: Cargar variables de entorno desde el archivo .env

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
RESPONSABLE_SCRAPER = "Yahima"


# ============================================================
# ETAPA 2: DESARROLLO DEL SCRAPER
# ============================================================

# Paso 2.1: Configurar la fuente web

URL_BASE = "https://www.tiendanimal.es"

URL_CATEGORIA = "https://www.tiendanimal.es/perros/pienso-para-perros/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# Paso 2.2: Configurar conexión con MongoDB Atlas

def conectar_mongodb():
    """
    Conecta el proyecto con MongoDB Atlas y retorna la colección
    donde se almacenarán los datos crudos.
    """

    cliente = MongoClient(MONGO_URI)
    base_datos = cliente[MONGO_DB]
    coleccion = base_datos[MONGO_COLLECTION]

    print("Conexión exitosa con MongoDB Atlas")
    print(f"Base de datos utilizada: {MONGO_DB}")
    print(f"Colección utilizada: {MONGO_COLLECTION}")

    return coleccion


# Paso 2.3: Obtener el HTML del sitio web

def obtener_html(url):
    """
    Descarga el contenido HTML de la página web indicada.
    """

    respuesta = requests.get(url, headers=HEADERS, timeout=20)

    if respuesta.status_code == 200:
        print("HTML obtenido correctamente")
        return respuesta.text
    else:
        print(f"No se pudo obtener el HTML. Código de estado: {respuesta.status_code}")
        return None


# Paso 2.4: Detectar posibles bloqueos

def detectar_bloqueo(html):
    """
    Revisa si el sitio devuelve señales de bloqueo, captcha
    o restricciones de acceso.
    """

    html = html.lower()

    palabras_bloqueo = [
        "captcha",
        "robot",
        "access denied",
        "forbidden",
        "unusual traffic"
    ]

    bloqueo_detectado = any(palabra in html for palabra in palabras_bloqueo)

    if bloqueo_detectado:
        print("Posible bloqueo detectado. Puede requerir intervención humana.")
        return True
    else:
        print("No se detectan señales evidentes de bloqueo en el HTML.")
        return False


# Resolver bloqueos en el navegador
def resolver_bloqueo_manual(url):
    """
    Abre un navegador para que el usuario pueda resolver
    manualmente captcha o validaciones del sitio.
    """

    print("\n=== MODO INTERVENCIÓN MANUAL ACTIVADO ===")

    print("Abra el navegador visual Docker/noVNC en:")
    print("http://localhost:6080/vnc.html\n")

    print("Dentro del navegador:")
    print("- Resuelva captcha si aparece")
    print("- Espere a que cargue la página")
    print("- No cierre la ventana del navegador\n")

    print("El sistema esperará 30 segundos para la validación manual.\n")

    opciones = Options()

    # Muy importante para Docker/noVNC
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opciones
    )

    # Abrir la página
    driver.get(url)

    # Esperar intervención manual
    time.sleep(3)

    # Obtener HTML final luego del captcha
    html = driver.page_source

    # Cerrar navegador
    driver.quit()

    return html

# Paso 2.5: Extraer información de productos

def extraer_productos(html, url, pagina):
    """
    Extrae información de productos desde el HTML.

    Campos considerados:
    - nombre_producto
    - precio
    - rating
    - numero_reviews
    - categoria
    - marca
    - disponibilidad
    - descripcion
    - url_producto
    - fecha_extraccion
    - responsable_scraper
    """

    soup = BeautifulSoup(html, "html.parser")

    # Tarjetas principales de productos
    tarjetas = soup.find_all("div", class_="isk-product-card")

    print("Tarjetas de producto encontradas:", len(tarjetas))

    productos = []

    fecha_actual = time.strftime("%Y-%m-%d %H:%M:%S")

    for i, tarjeta in enumerate(tarjetas, start=1):

        texto_completo = tarjeta.get_text(" ", strip=True)

        # ==================================================
        # Nombre del producto
        # ==================================================

        nombre_tag = tarjeta.find(class_="isk-product-card__headline")

        nombre = (
            nombre_tag.get_text(" ", strip=True)
            if nombre_tag else None
        )

        # ==================================================
        # Rating y opiniones
        # ==================================================

        reviews_tag = tarjeta.find(class_="isk-product-card__reviews")

        reviews_text = (
            reviews_tag.get_text(" ", strip=True)
            if reviews_tag else ""
        )

        rating = None
        opiniones = None

        match_reviews = re.search(
            r"(\d+[.,]?\d*)\s*estrellas\s*con\s*(\d+)\s*opiniones",
            reviews_text,
            re.IGNORECASE
        )

        if match_reviews:
            rating = float(
                match_reviews.group(1).replace(",", ".")
            )

            opiniones = int(
                match_reviews.group(2)
            )

        # ==================================================
        # Precio y formato
        # ==================================================

        precios_tag = tarjeta.find(
            class_="isk-product-card__prices"
        )

        precios_text = (
            precios_tag.get_text(" ", strip=True)
            if precios_tag else ""
        )

        precio_raw = None
        formato_raw = None

        match_precio = re.search(
            r"Precio\s+de\s+([0-9]+[.,][0-9]{2}€(?:\s*a\s*[0-9]+[.,][0-9]{2}€)?)",
            precios_text,
            re.IGNORECASE
        )

        if match_precio:
            precio_raw = match_precio.group(1)

        match_formato = re.search(
            r"([0-9]+[.,][0-9]{2}€\s*el\s*kg|Desde\s+[0-9]+[.,][0-9]{2}€\s*/\s*kg|[0-9]+\s+opciones\s+de\s+peso)",
            precios_text,
            re.IGNORECASE
        )

        if match_formato:
            formato_raw = match_formato.group(1)

        # ==================================================
        # SKU interno académico
        # ==================================================

        sku_id = f"TD_P{pagina:04d}_{i:05d}"

        # ==================================================
        # Documento JSON Raw
        # ==================================================

        producto = {

            # Identificación
            "sku_id": sku_id,

            # Información producto
            "nombre_producto": nombre,
            "marca": nombre.split()[0] if nombre else "Sin_marca",

            # Precio
            "precio_raw": precio_raw,
            "formato_raw": formato_raw,

            # Rating
            "rating": rating,
            "opiniones": opiniones,

            # Metadata académica
            "categoria": "Pienso para perros",
            "tienda": "Tiendanimal",
            "url_fuente": url,

            # Metadata scraping
            "responsable_scraper": RESPONSABLE_SCRAPER,
            "fecha_extraccion": fecha_actual,

            # Texto original completo
            "texto_crudo": texto_completo
        }

        productos.append(producto)

    return productos


# ============================================================
# ETAPA 3: ALMACENAMIENTO DE DATOS RAW
# ============================================================

# Paso 3.1: Guardar documentos JSON en MongoDB Atlas

def guardar_en_mongodb(coleccion, productos):
    """
    Guarda los documentos JSON en MongoDB Atlas.
    """

    if len(productos) > 0:
        resultado = coleccion.insert_many(productos)
        print(f"Productos guardados correctamente: {len(resultado.inserted_ids)}")
    else:
        print("No hay productos para guardar.")


# Paso 3.2: Mostrar muestra de datos extraídos

def mostrar_muestra(productos, cantidad=5):
    """
    Muestra productos en formato tabla Jupyter.
    """

    if len(productos) == 0:
        print("No existen productos para mostrar.")
        return
    print("\nMuestra de productos extraídos:")   
    for producto in productos[:cantidad]:
        print(producto)

    print(f"\nMostrando {cantidad} productos extraídos:\n")

    df = pd.DataFrame(productos[:cantidad])

    display(df)

# ============================================================
# ETAPA 4: EJECUCIÓN DEL PIPELINE
# ============================================================

# Paso 4.1: Ejecutar el flujo completo

def main():
    """
    Ejecuta la etapa Scraper / Raw Data del pipeline:

    Sitio Web
        ↓
    Scraping Web (.py)
        ↓
    MongoDB Atlas Raw Data
    """

    print("Inicio del pipeline Scraper / Raw Data")

    coleccion = conectar_mongodb()

    todos_los_productos = []

    pagina_inicio = 61
    pagina_fin = 80
    
    pagina = pagina_inicio

    while pagina <= pagina_fin:

        print(f"\nProcesando página {pagina}")

        url_pagina = f"{URL_CATEGORIA}?page={pagina}"

        print("URL:", url_pagina)

        html = obtener_html(url_pagina)

        if html is None:
            print("No se pudo obtener HTML.")
            break

        bloqueo = detectar_bloqueo(html)

        if bloqueo:
            html = resolver_bloqueo_manual(url_pagina)

        productos = extraer_productos(html, url_pagina, pagina)

        # Si no hay productos termina el loop
        if len(productos) == 0:
            print("No se encontraron más productos.")
            break

        todos_los_productos.extend(productos)

        print(f"Productos acumulados: {len(todos_los_productos)}")

        pagina += 1

    # Mostrar muestra
    mostrar_muestra(todos_los_productos)

    # Guardar en MongoDB
    guardar_en_mongodb(coleccion, todos_los_productos)

    print("\nPipeline finalizado correctamente")


# Paso 4.2: Punto de entrada del programa

if __name__ == "__main__":
    main()

# ============================================================
# ETAPA 5: LIMPIEZA, NORMALIZACIÓN Y EDA CON SPARK
#   MongoDB Atlas
#       ↓
#    Spark
#       ↓
#   Limpieza de datos
#       ↓
#   Normalización de precio y peso
#       ↓
#   Cálculo de precio por kilo
#       ↓
#      EDA
# ============================================================

# Paso 5.1: Crear sesión de Spark conectada a MongoDB Atlas

def iniciar_spark():
    """
    Crea una sesión de Spark para leer datos desde MongoDB Atlas.
    """

    uri_lectura = f"{MONGO_URI.split('?')[0]}/{MONGO_DB}.{MONGO_COLLECTION}?retryWrites=true&w=majority"

    spark = SparkSession.builder \
        .appName("Semana10_EDA_Mascotas") \
        .config("spark.mongodb.read.connection.uri", uri_lectura) \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1") \
        .getOrCreate()

    print("Sesión Spark creada correctamente.")
    print("Leyendo desde:", MONGO_DB, ".", MONGO_COLLECTION)

    return spark



# Paso 5.2: Cargar datos RAW desde MongoDB Atlas


def cargar_datos_raw_spark(spark):
    """
    Carga los documentos RAW de MongoDB Atlas como DataFrame Spark.
    """

    df_raw = spark.read.format("mongodb").load()

    print("Datos RAW cargados correctamente desde MongoDB Atlas.")
    print("Cantidad de registros RAW:", df_raw.count())

    df_raw.printSchema()
    df_raw.show(5, truncate=False)

    return df_raw


# Paso 5.3: Eliminar duplicados e incompletos

def eliminar_duplicados_e_incompletos(df_raw):
    """
    Elimina productos duplicados y registros sin campos mínimos.
    """

    df_clean = df_raw.dropDuplicates(["sku_id", "tienda"])

    df_clean = df_clean.filter(col("nombre_producto").isNotNull())
    df_clean = df_clean.filter(col("precio_raw").isNotNull())
    df_clean = df_clean.filter(col("precio_raw") != "")

    print("Limpieza inicial completada.")
    print("Registros después de eliminar duplicados e incompletos:", df_clean.count())

    return df_clean


# Paso 5.4: Normalizar precio

def normalizar_precio(df_clean):
    """
    Limpia el campo precio_raw y lo convierte a número decimal.
    """

    df_clean = df_clean.withColumn(
        "precio_limpio",
        regexp_replace(col("precio_raw"), "[^0-9,\\.]", "")
    )

    df_clean = df_clean.withColumn(
        "precio_limpio",
        regexp_replace(col("precio_limpio"), ",", ".")
    )

    df_clean = df_clean.withColumn(
        "precio_num",
        col("precio_limpio").cast("double")
    )

    df_clean = df_clean.withColumn(
        "moneda",
        lit("EUR")
    )

    print("Normalización de precio completada.")

    df_clean.select("nombre_producto", "precio_raw", "precio_num", "moneda").show(10, truncate=False)

    return df_clean


# Paso 5.5: Extraer peso desde formato_raw o texto_crudo

def extraer_peso(df_clean):
    """
    Extrae peso desde formato_raw o texto_crudo.
    Convierte gramos a kilogramos cuando corresponde.
    """

    df_clean = df_clean.withColumn(
        "texto_peso",
        when(col("formato_raw").isNotNull(), col("formato_raw"))
        .otherwise(col("texto_crudo"))
    )

    df_clean = df_clean.withColumn(
        "peso_extraido",
        regexp_extract(col("texto_peso"), r"(\d+[.,]?\d*)\s*(kg|g|gr)", 1)
    )

    df_clean = df_clean.withColumn(
        "unidad_peso",
        regexp_extract(col("texto_peso"), r"(\d+[.,]?\d*)\s*(kg|g|gr)", 2)
    )

    df_clean = df_clean.withColumn(
        "peso_extraido",
        regexp_replace(col("peso_extraido"), ",", ".").cast("double")
    )

    df_clean = df_clean.withColumn(
        "peso_kg",
        when(col("unidad_peso").isin("g", "gr"), col("peso_extraido") / 1000)
        .when(col("unidad_peso") == "kg", col("peso_extraido"))
        .otherwise(None)
    )

    print("Extracción y normalización de peso completada.")

    df_clean.select("nombre_producto", "formato_raw", "peso_kg", "unidad_peso").show(10, truncate=False)

    return df_clean


# Paso 5.6: Calcular precio por kilo

def calcular_precio_por_kilo(df_clean):
    """
    Calcula el precio por kilo a partir del precio numérico y el peso normalizado.
    """

    df_clean = df_clean.withColumn(
        "precio_kg",
        when(
            (col("peso_kg").isNotNull()) & (col("peso_kg") > 0),
            round(col("precio_num") / col("peso_kg"), 2)
        ).otherwise(None)
    )

    print("Cálculo de precio por kilo completado.")

    df_clean.select("nombre_producto", "precio_num", "peso_kg", "precio_kg").show(10, truncate=False)

    return df_clean


# Paso 5.7: Normalizar rating y opiniones

def normalizar_rating_opiniones(df_clean):
    """
    Asegura que rating y opiniones estén en formato numérico.
    """

    df_clean = df_clean.withColumn(
        "rating_num",
        col("rating").cast("double")
    )

    df_clean = df_clean.withColumn(
        "opiniones_num",
        col("opiniones").cast("int")
    )

    print("Normalización de rating y opiniones completada.")

    df_clean.select("nombre_producto", "rating", "rating_num", "opiniones", "opiniones_num").show(10, truncate=False)

    return df_clean



# Paso 5.8: Análisis de valores faltantes

def analizar_valores_faltantes(df_clean):
    """
    Muestra cantidad de valores nulos por columna.
    """

    print("Análisis de valores faltantes:")

    df_clean.select([
        count(
            when(
                col(c).isNull(),
                c
            )
        ).alias(c)
        for c in df_clean.columns
    ]).show(truncate=False)


# Paso 5.9: EDA básico con Spark

def ejecutar_eda_basico(df_clean):
    """
    Ejecuta análisis exploratorio básico sobre productos de mascotas.
    """

    print("Resumen estadístico de variables numéricas:")
    df_clean.select(
        "precio_num",
        "peso_kg",
        "precio_kg",
        "rating_num",
        "opiniones_num"
    ).describe().show()

    print("Cantidad de productos por tienda:")
    df_clean.groupBy("tienda").count().show()

    print("Cantidad de productos por marca:")
    df_clean.groupBy("marca").count().orderBy(col("count").desc()).show(20)

    print("Precio promedio por marca:")
    df_clean.groupBy("marca") \
        .avg("precio_kg") \
        .orderBy(col("avg(precio_kg)").desc()) \
        .show(20)

    print("Productos más caros por kilo:")
    df_clean.select(
        "nombre_producto",
        "marca",
        "precio_num",
        "peso_kg",
        "precio_kg",
        "rating_num",
        "opiniones_num"
    ).orderBy(col("precio_kg").desc()).show(20, truncate=False)



# Paso 5.10: Ejecutar pipeline de limpieza y EDA

def ejecutar_etapa_5():
    """
    Ejecuta toda la etapa 5:
    MongoDB Atlas → Spark → Limpieza → Normalización → EDA.
    """

    print("Iniciando ETAPA 5: Limpieza, normalización y EDA con Spark")

    spark = iniciar_spark()

    df_raw = cargar_datos_raw_spark(spark)

    df_clean = eliminar_duplicados_e_incompletos(df_raw)

    df_clean = normalizar_precio(df_clean)

    df_clean = extraer_peso(df_clean)

    df_clean = calcular_precio_por_kilo(df_clean)

    df_clean = normalizar_rating_opiniones(df_clean)

    analizar_valores_faltantes(df_clean)

    ejecutar_eda_basico(df_clean)

    print("ETAPA 5 finalizada correctamente.")

    return df_clean