---
tags:
  - universidad
  - big-data
  - proyecto
  - python
  - scraping
  - mongodb
status: en progreso
fecha_inicio: 2026-04
curso: Big Data para la toma de decisiones
universidad: UCN
---

# Proyecto Big Data — E-Commerce & Precios

## Contexto general

Proyecto grupal del curso **Big Data para la toma de decisiones** (UCN, 2026-1). El grupo se llama **E-Commerce & Precios** y somos 6 integrantes, cada uno scrapeando una categoría distinta de MercadoLibre Chile y subiendo los datos a una base de datos compartida en MongoDB Atlas.

| Integrante | Categoría | Colección Atlas |
|---|---|---|
| Valentina Aróstica (**yo**) | Smartphones y Celulares | `smartphones_mercadolibre` |
| Alondra Segovia | Televisores | `televisores_mercadolibre` |
| Luis Molina | Laptops | `laptops_mercadolibre` |
| Kimberly Neira | Tablets | `tablets_mercadolibre` |
| Ariel Peña | Auriculares | `auriculares_mercadolibre` |
| Mayra Gutierrez | Hornos | `hornos_mercadolibre` |

**Repo GitHub:** `avancesproyectobigdata2026-1e-commerce-precios`  
**Base de datos:** MongoDB Atlas — `BigData_ECommerce`  
**Cluster:** `cluster0.gxkvvjs.mongodb.net`  
**Usuario Atlas:** `valentinaarostica_db_user`

---

## Stack tecnológico usado

| Herramienta | Para qué se usó |
|---|---|
| **Python 3.13** | Lenguaje principal |
| **Selenium** | Automatizar el navegador para scraping dinámico |
| **undetected-chromedriver** | Evitar bloqueos anti-bot de MercadoLibre |
| **BeautifulSoup4** | Parsear el HTML descargado por Selenium |
| **pandas** | Manipulación y análisis del DataFrame de productos |
| **pymongo** | Conectar Python con MongoDB Atlas |
| **matplotlib + seaborn** | Gráficos de distribución de precios y descuentos |
| **MongoDB Atlas** | Base de datos NoSQL en la nube, compartida entre los 6 |
| **Jupyter Notebook** | Entorno de desarrollo y presentación |
| **VS Code** | Editor principal |
| **Docker** | Entorno alternativo con Jupyter + Spark + MongoDB local |

---

## Por qué se usa Selenium y no requests

MercadoLibre es un sitio **React/Next.js** — el HTML que entrega el servidor está vacío, los productos se renderizan con JavaScript en el navegador. Si usas `requests.get(url)` no ves ningún producto. Selenium lanza un Chrome real que ejecuta el JavaScript y entrega el HTML ya renderizado, que BeautifulSoup puede parsear.

`undetected-chromedriver` es un wrapper sobre Selenium que modifica el fingerprint del Chrome para que MercadoLibre no detecte que es un bot y bloquee la sesión.

---

## Arquitectura del scraper

El scraper es una clase `ScraperMercadoLibre` en Python con los siguientes componentes:

### Configuración (celda 1 — la única que cambia entre compañeros)

```python
RESPONSABLE = 'Valentina'
CATEGORIA   = 'smartphones'
BASE_URL    = 'https://listado.mercadolibre.cl/celulares-telefonos/celulares-smartphones/'
NUM_PAGINAS = 20
```

Cada compañero solo cambia esta celda. El resto del código es idéntico.

### Paginación

MercadoLibre usa offsets de 48 productos por página:

```
Página 1 → <BASE_URL>
Página 2 → <BASE_URL>_Desde_49
Página 3 → <BASE_URL>_Desde_97
Página n → <BASE_URL>_Desde_{(n-1)*48 + 1}
```

### Selectores CSS verificados

| Campo | Selector |
|---|---|
| Contenedor de ítem | `li.ui-search-layout__item` |
| Título | `.poly-component__title` |
| Precio actual | `.andes-money-amount__fraction` (excluyendo `.andes-money-amount--previous`) |
| Precio original (tachado) | `.andes-money-amount--previous` |
| Descuento | `.andes-money-amount__discount` |
| Imagen | `img.poly-component__picture` → atributo `src` |
| ID del producto | atributo `data-item-id` en el `<li>`, fallback regex `MLC-?\d+` en href |

### Filtros de calidad

**1. Precio mínimo por categoría** — descarta productos con precio absurdo (probablemente accesorios baratos o errores de scraping):

| Categoría | Precio mínimo |
|---|---|
| Smartphones | $30.000 CLP |
| Televisores | $80.000 CLP |
| Laptops | $150.000 CLP |
| Tablets | $50.000 CLP |
| Auriculares | $8.000 CLP |
| Hornos | $25.000 CLP |

**2. Filtro de accesorios** — si el título contiene alguna de estas palabras, el producto se descarta:

```
lapiz, lápiz, funda, case, carcasa, protector, vidrio, templado, cristal,
auricular, audifono, auriculares, cable, cargador, adaptador, soporte,
holder, grip, bateria, powerbank, kit, tripode, selfie, anillo, lampara,
disparador, espejo, correa, strap, stylus, teclado, mouse, parlante,
altavoz, repuesto, touch
```

**3. Extracción de marca** — solo reconoce marcas de una lista conocida (`_MARCAS`). Si el título no contiene ninguna marca conocida, guarda `null` en el campo marca (el producto igual se guarda, solo queda sin marca reconocida).

### Schema de documento en MongoDB

```json
{
  "producto_id": "MLC-1677507405",
  "titulo": "Teléfono Oppo Reno13 F 5G 12+256GB Morado Smartphone",
  "marca": "Oppo",
  "precio_actual": 309990,
  "precio_original": 449990,
  "descuento_porcentaje": 31,
  "tiene_descuento": true,
  "url": "https://...",
  "imagen_url": "https://...",
  "pagina": 1,
  "fecha_scraping": "2026-04-26T17:42:33.479210",
  "grupo": "E-Commerce",
  "responsable": "Valentina",
  "categoria": "smartphones"
}
```

### Subida a Atlas

La celda de subida:
1. Hace `col.drop()` → borra toda la colección anterior
2. Crea índice único por `(titulo, pagina, responsable)`
3. Sube en lotes de 500 usando `bulk_write` con `UpdateOne` upsert
4. Limpia `NaN` e `Inf` de pandas antes de insertar (MongoDB no acepta esos valores)

---

## Bugs encontrados y cómo se resolvieron

### Bug 1 — precio_actual igual a precio_original

**Síntoma:** Ambos campos tenían el mismo valor.  
**Causa:** El selector `.andes-money-amount__fraction` matcheaba tanto el precio actual como la fracción dentro del precio tachado `<s class="andes-money-amount--previous">`.  
**Fix:** Se agregó el parámetro `excluir_clase='andes-money-amount--previous'` al método `_parsear_precio`. Itera los elementos y salta los que tienen un padre con esa clase.

```python
def _parsear_precio(self, contenedor, excluir_clase=None):
    for elem in contenedor.select('.andes-money-amount__fraction'):
        if excluir_clase and elem.find_parent(class_=excluir_clase):
            continue  # ← salta el precio tachado
        ...
```

### Bug 2 — producto_id siempre None

**Síntoma:** Todos los productos tenían `producto_id = None`.  
**Causa:** La regex `MLC-\d+` se aplicaba sobre URLs de click tracking (`click1.mercadolibre.cl/mclics/...`) que no contienen el ID del producto.  
**Fix:** Primero buscar el atributo `data-item-id` en el `<li>`, y solo si falla, aplicar la regex sobre el href.

```python
producto_id = item.get('data-item-id')
if not producto_id and url:
    m = re.search(r'(MLC-?\d+)', url)
    producto_id = m.group(1) if m else None
```

### Bug 3 — marcas falsas ("Smartphones", "Mini", "Nuevo", ".")

**Síntoma:** La columna marca mostraba palabras como "Smartphones", "Mini", "Nuevo", ".".  
**Causa:** El método `_extraer_marca` hacía `titulo.split()[0]` como fallback cuando no encontraba marca conocida, retornando la primera palabra del título.  
**Fix:** Retornar `None` en vez del fallback. El producto se guarda sin marca, y en el análisis se usa `df.dropna(subset=['marca'])` antes del groupby.

### Bug 4 — NameError: 'os' is not defined

**Síntoma:** Error al ejecutar la celda de configuración.  
**Causa:** `os.environ.get(...)` se usaba antes del `import os` en la misma celda.  
**Fix:** Mover todos los imports al inicio de la celda, variables de config después.

### Bug 5 — 'power' filtraba teléfonos reales

**Síntoma:** "Snapdragon Power Edition" (smartphone real) era descartado como accesorio.  
**Causa:** 'power' estaba en el set `_ACCESORIOS` y hacía match como substring.  
**Fix:** Remover 'power' del set. Se mantiene 'powerbank' que es suficientemente específico.

### Bug 6 — Cómo limpiar accesorios que ya están en Atlas o en CSV

Si se subieron datos viejos (antes de que el filtro estuviera activo), hay dos opciones:

**Opción A — Re-correr el scraper:** La celda de subida tiene `col.drop()` que borra todo y re-sube limpio.

**Opción B — Borrar solo accesorios de Atlas con PyMongo:**
```python
patron = 'funda|case|carcasa|cargador|cable|auricular|...'
col.delete_many({'titulo': {'$regex': patron, '$options': 'i'}})
```

**Opción C — Limpiar CSVs locales con pandas:**
```python
df_csv = df_csv[~df_csv['titulo'].str.contains(patron, case=False, na=False)]
df_csv.to_csv(csv_path, index=False)
```

---

## Resultados obtenidos (Hito 1 — abril 2026)

### Conteo en Atlas (último scraping conocido)

| Categoría | Documentos | Requisito mínimo | Estado |
|---|---|---|---|
| Smartphones (Valentina) | 820 | 500 | ✅ |
| Televisores (Alondra) | 540 | 500 | ✅ |
| Tablets (Kimberly) | 572 | 500 | ✅ |
| Auriculares (Ariel) | 567 | 500 | ✅ |
| Hornos (Mayra) | 510 | 500 | ✅ |
| Laptops (Luis) | pendiente | 500 | ⏳ |

### Análisis de smartphones (mi categoría)

- **Productos válidos:** 900
- **Con descuento:** 560 (62.2%)
- **Precio promedio:** $172.478 CLP
- **Precio mediano:** $63.252 CLP
- **Rango:** $32.509 — $586.297 CLP
- **Descuento promedio:** 36.7%
- **Marcas reconocidas en top:** Ulefone (140), Oppo (80), Xiaomi (40)
- **Sin marca reconocida:** 640 productos (el campo queda `null`, no se eliminan)

---

## Hito 1 — Qué se entregó

**Requisitos del hito:**
- ≥ 500 productos por integrante subidos a MongoDB Atlas ✅
- ≥ 5 commits en branch personal *(verificar)*
- Notebook funcional con análisis de datos ✅
- Documentación en README ✅

**Evidencias requeridas:**
- Screenshot de `docker stats` con los contenedores activos
- Screenshot del conteo de documentos en MongoDB (`db.collection.countDocuments()`)

**Estructura de entrega:**
- Notebook en `Proyecto_MercadoLibre/notebooks/`
- CSVs generados en `notebooks/outputs/`
- README actualizado en `Proyecto_MercadoLibre/README.md`

---

## Estructura de archivos del proyecto

```
Proyecto_MercadoLibre/
├── notebooks/
│   ├── Scraper_MercadoLibre_ECommerce.ipynb    ← mi notebook (smartphones)
│   ├── Scraper_Televisores_MercadoLibre.ipynb
│   ├── Scraper_Laptops_MercadoLibre.ipynb
│   ├── Scraper_Tablets_MercadoLibre.ipynb
│   ├── Scraper_Auriculares_MercadoLibre.ipynb
│   ├── Scraper_Hornos_MercadoLibre.ipynb
│   └── outputs/
│       ├── smartphones_ml_YYYYMMDD_HHMMSS.csv
│       ├── grafico_precios_descuentos.png
│       └── bitacora_smartphones.json
├── docs/
│   └── BigData_ECommerce_Personal.md           ← esta nota
└── README.md
```

---

## Cómo volver a correr el scraper

1. Abrir `Scraper_MercadoLibre_ECommerce.ipynb` en VS Code o Jupyter
2. Verificar que `NUM_PAGINAS = 20` en la celda de configuración
3. Ejecutar todas las celdas en orden
4. La celda de Atlas borra la colección anterior y sube los datos nuevos automáticamente

Si Chrome da error de versión:
```python
return uc.Chrome(options=options, version_main=147)  # ajustar el número
```

---

## Cosas pendientes / próximos hitos

- [ ] Luis sube su scraper de laptops
- [ ] Verificar ≥ 5 commits en branch personal
- [ ] Preparar evidencias (Docker stats + conteo MongoDB)
- [ ] Hito 2 (pendiente definición de requisitos)
