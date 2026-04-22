import subprocess, sys

# Instalar dependencias si faltan
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymongo', 'dnspython', '--quiet'])

from pymongo import MongoClient, UpdateOne
import pandas as pd
import glob, os, math


# ── Conexión ──────────────────────────────────────────────────────────────
ATLAS_URI = "mongodb+srv://valentinaarostica_db_user:ecommerce@cluster0.gxkvvjs.mongodb.net/BigData_ECommerce?appName=Cluster0"
DB_NAME   = "BigData_ECommerce"

print("Conectando a MongoDB Atlas...")
client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
client.admin.command('ping')
db = client[DB_NAME]
print(f"Conectado — base de datos: {DB_NAME}\n")

# ── Funciones auxiliares ───────────────────────────────────────────────────
def subir_con_upsert(coleccion, documentos, clave_upsert):
    if not documentos:
        print("  Sin documentos.")
        return 0, 0
    ops = [
        UpdateOne({k: doc[k] for k in clave_upsert if k in doc}, {"$set": doc}, upsert=True)
        for doc in documentos
    ]
    ins = act = 0
    for i in range(0, len(ops), 500):
        r = coleccion.bulk_write(ops[i:i+500], ordered=False)
        ins += r.upserted_count
        act += r.modified_count
    return ins, act

def limpiar_fila(fila):
    out = {}
    for k, v in fila.items():
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            out[k] = None
        elif hasattr(v, 'item'):
            out[k] = v.item()
        else:
            out[k] = v
    return out

# ── Smartphones MercadoLibre ───────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV   = os.path.join(SCRIPT_DIR, '..', 'outputs', 'smartphones_ml_*.csv')
archivos   = sorted(glob.glob(RUTA_CSV))
print(f"CSV encontrados: {len(archivos)}")

frames = []
for archivo in archivos:
    if os.path.getsize(archivo) == 0:
        print(f"  Vacío, saltado: {os.path.basename(archivo)}")
        continue
    try:
        df_tmp = pd.read_csv(archivo, index_col=0)
    except Exception:
        print(f"  Sin datos, saltado: {os.path.basename(archivo)}")
        continue
    if df_tmp.empty:
        print(f"  Sin filas, saltado: {os.path.basename(archivo)}")
        continue
    frames.append(df_tmp)

df_sm = pd.concat(frames, ignore_index=True)
# Misma lógica que el scraper: un producto único = titulo + pagina + responsable
df_sm['responsable'] = df_sm['responsable'].fillna('Valentina')
df_sm.drop_duplicates(subset=['titulo', 'pagina', 'responsable'], inplace=True)
print(f"Filas únicas de smartphones: {len(df_sm):,}")

col_sm = db['smartphones_mercadolibre']

# Limpiar colección anterior para evitar conflictos de índice
print("  Limpiando colección anterior en Atlas...")
col_sm.drop()

col_sm = db['smartphones_mercadolibre']
col_sm.create_index([('titulo', 1), ('pagina', 1), ('responsable', 1)], unique=True, background=True)

docs = [limpiar_fila(f) for f in df_sm.to_dict('records')]
ins, act = subir_con_upsert(col_sm, docs, ['titulo', 'pagina', 'responsable'])
print(f"  Insertados: {ins:,}  |  Actualizados: {act:,}  |  Total en Atlas: {col_sm.count_documents({}):,}\n")

# ── Resumen ────────────────────────────────────────────────────────────────
print("=" * 50)
print(f"BASE DE DATOS: {DB_NAME}")
print("=" * 50)
for nombre in db.list_collection_names():
    n = db[nombre].count_documents({})
    print(f"  {nombre:<35} {n:>8,} docs")
print("=" * 50)
print("Todos los datos estan en Atlas.")
client.close()
