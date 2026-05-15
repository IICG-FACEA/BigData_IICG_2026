from pyspark.sql import SparkSession
from scrapers import scraper_nicolegarcia, scraper_soto, scraper_perez

# 1. Ejecutar scrapers
data_nicole = scraper_nicolegarcia.ejecutar_extraccion()
data_soto = scraper_soto.ejecutar_extraccion()
data_perez = scraper_perez.ejecutar_extraccion()

# 2. Iniciar Spark
spark = SparkSession.builder \
    .appName("IntegradoraBigData") \
    .config("spark.mongodb.output.uri", "mongodb+srv://usuario:password@cluster...") \
    .getOrCreate()

# 3. Convertir listas en DataFrames
df_nicole = spark.createDataFrame(data_nicole)
df_soto = spark.createDataFrame(data_soto)
df_perez = spark.createDataFrame(data_perez)

# 4. Unir todo
df_final = df_nicole.union(df_soto).union(df_perez)

# 5. Limpieza y transformación
from pyspark.sql.functions import col, regexp_replace
df_limpio = df_final.withColumn("valor_numerico",
    regexp_replace(col("valor"), "[^0-9]", "").cast("float"))

# 6. Guardar en MongoDB
df_limpio.write.format("mongodb").mode("append").save()
