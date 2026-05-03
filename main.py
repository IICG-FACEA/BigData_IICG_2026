"""
main.py — Orquestador principal del proyecto Big Data E-Commerce & Precios
Grupo 1 | UCN | Ingeniería en Información y Control de Gestión | 2026

Flujo:
  1. Lee los CSVs generados por cada integrante en sus ramas
  2. Une los 6 DataFrames con Spark (unionByName)
  3. Aplica transformaciones: Filter, Map/Transform
  4. Sube el resultado consolidado a MongoDB Atlas
"""

import os
import glob
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit
from pyspark.sql.types import IntegerType, BooleanType

# ============================================================
# CONFIGURACIÓN
# ============================================================
ATLAS_URI = os.environ.get(
    "ATLAS_URI",
    "mongodb+srv://valentinaarostica_db_user:ecommerce"
    "@cluster0.gxkvvjs.mongodb.net/BigData_ECommerce?appName=Cluster0"
)
DATABASE   = "BigData_ECommerce"
COLECCION  = "productos_consolidados"

# Carpeta donde cada integrante guarda su CSV tras correr el scraper
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "Proyecto_MercadoLibre", "notebooks", "outputs")

# Categorías esperadas → patrón del nombre de archivo
CATEGORIAS = [
    "smartphones",
    "televisores",
    "laptops",
    "tablets",
    "auriculares",
    "hornos",
]

# ============================================================
# INICIAR SPARK
# ============================================================
spark = SparkSession.builder \
    .appName("BigData_ECommerce_Integrador") \
    .config("spark.mongodb.write.connection.uri", ATLAS_URI) \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("SparkSession iniciada.\n")

# ============================================================
# LECTURA DE CSVs (uno por categoría, el más reciente)
# ============================================================
print(f"Buscando CSVs en: {OUTPUTS_DIR}")
print("-" * 65)

dfs = []
for categoria in CATEGORIAS:
    patron  = os.path.join(OUTPUTS_DIR, f"{categoria}_ml_*.csv")
    archivos = sorted(glob.glob(patron))          # orden alfabético = cronológico

    if not archivos:
        print(f"  FALTA  {categoria:<18} → no se encontró CSV (rama no mergeada aún)")
        continue

    csv_reciente = archivos[-1]                   # el más reciente
    df = spark.read.option("header", True).csv(csv_reciente)
    n  = df.count()
    print(f"  OK     {categoria:<18} → {os.path.basename(csv_reciente)}  ({n} filas)")
    dfs.append(df)

if not dfs:
    print("\nNo se encontró ningún CSV. Asegúrate de haber hecho el merge de todas las ramas.")
    spark.stop()
    raise SystemExit(1)

# ============================================================
# UNION / MERGE (Sección 8.3)
# ============================================================
df_total = dfs[0]
for df in dfs[1:]:
    df_total = df_total.unionByName(df, allowMissingColumns=True)

total_bruto = df_total.count()
print(f"\nUnión completada: {total_bruto:,} filas en total\n")

# ============================================================
# FILTER (Sección 8.3)
# Eliminar registros sin precio o con datos inválidos
# ============================================================
df_filtrado = df_total.filter(
    col("precio_actual").isNotNull() &
    col("titulo").isNotNull()        &
    (col("precio_actual").cast(IntegerType()) > 0)
)
descartados = total_bruto - df_filtrado.count()
print(f"Filter: {descartados} registros descartados (precio nulo o cero)")
print(f"Registros válidos: {df_filtrado.count():,}\n")

# ============================================================
# MAP / TRANSFORM (Sección 8.3)
# Corregir tipos (CSV los lee como string) y añadir segmento
# ============================================================
df_final = df_filtrado \
    .withColumn("precio_actual",         col("precio_actual").cast(IntegerType())) \
    .withColumn("precio_original",       col("precio_original").cast(IntegerType())) \
    .withColumn("descuento_porcentaje",  col("descuento_porcentaje").cast(IntegerType())) \
    .withColumn("pagina",                col("pagina").cast(IntegerType())) \
    .withColumn(
        "tiene_descuento",
        when(col("tiene_descuento") == "True", lit(True)).otherwise(lit(False))
    ) \
    .withColumn(
        "segmento_precio",
        when(col("precio_actual") < 50_000,   "Economico")
        .when(col("precio_actual") < 200_000, "Gama Media")
        .when(col("precio_actual") < 600_000, "Gama Alta")
        .otherwise("Premium")
    )

# ============================================================
# SUBIR A MONGODB ATLAS
# ============================================================
print("Subiendo datos a MongoDB Atlas...")
df_final.write \
    .format("mongodb") \
    .mode("append") \
    .option("database",   DATABASE) \
    .option("collection", COLECCION) \
    .save()

print(f"Datos guardados en Atlas: {DATABASE}.{COLECCION}")
print(f"Total documentos subidos: {df_final.count():,}\n")

# ============================================================
# REPORTE FINAL
# ============================================================
from pyspark.sql.functions import count, avg, round as spark_round

print("=" * 65)
print("  REPORTE CONSOLIDADO — E-COMMERCE & PRECIOS ML CHILE 2026")
print("=" * 65)

print("\n[1] DOCUMENTOS POR INTEGRANTE:")
df_final.groupBy("responsable", "categoria") \
    .agg(count("*").alias("total_docs")) \
    .orderBy("total_docs", ascending=False) \
    .show(truncate=False)

print("[2] PRECIO PROMEDIO POR CATEGORÍA (CLP):")
df_final.groupBy("categoria") \
    .agg(
        count("*").alias("productos"),
        spark_round(avg("precio_actual"), 0).alias("precio_promedio"),
    ) \
    .orderBy("precio_promedio", ascending=False) \
    .show(truncate=False)

print("=" * 65)
print(f"  TOTAL SUBIDO A ATLAS: {df_final.count():,} documentos")
print("=" * 65)

spark.stop()
print("\nProceso completado exitosamente.")
