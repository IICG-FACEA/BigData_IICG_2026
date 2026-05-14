from pyspark.sql import SparkSession
from scrapers import scraper_soto, scraper_perez

# 1. Recolectamos listas de Python de todos los estudiantes
data_RodOrt = scraper_soto.ejecutar_extraccion()
data_perez = scraper_perez.ejecutar_extraccion()

# 2. Iniciamos Spark
spark = SparkSession.builder \
    .appName("IntegradoraBigData") \
    .config("spark.mongodb.output.uri", "mongodb+srv://tu_usuario:tu_pass@cluster...") \
    .getOrCreate()

# 3. Spark convierte las listas en un solo DataFrame unificado
 df_soto = spark.createDataFrame(data_soto)
 df_perez = spark.createDataFrame(data_perez)

 df_final = df_soto.union(df_perez)

# 4. ACCION DE SPARK: Limpieza y Transformacion
 # Por ejemplo: Quitar s mbolos de moneda y convertir a numero enmilisegundos
  from pyspark.sql.functions import col, regexp_replace

 df_limpio = df_final.withColumn("valor_numerico",
 regexp_replace(col("valor"), "[^0-9]", "").cast("float"))

# 5. Spark guarda todo de UN SOLO GOLPE en MongoDB
 df_limpio.write.format("mongodb").mode("append").save()