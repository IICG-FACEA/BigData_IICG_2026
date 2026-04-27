# Proyecto MercadoLibre — Scraping de Precios E-Commerce

**Curso:** Big Data para la toma de decisiones — Universidad Católica del Norte  
**Grupo:** E-Commerce & Precios  
**Responsables:** 
- Valentina Aróstica
- Mayra Gutierrez
- Luis Molina
- Kimberly Neira
- Alondra Segovia
- Ariel Peña  
**Fuente de datos:** MercadoLibre Chile (https://www.mercadolibre.cl)

---

## Descripción

Scraper automatizado con Selenium que extrae precios, descuentos y atributos de productos desde MercadoLibre Chile. Los datos se almacenan en CSV local y se sincronizan con MongoDB Atlas (base de datos compartida del grupo).

---

## Estructura

```
Proyecto_MercadoLibre/
├── notebooks/
│   ├── Scraper_MercadoLibre_ECommerce.ipynb    # Scraper de smartphones (Valentina)
│   ├── Scraper_Televisores_MercadoLibre.ipynb  # Scraper de TVs (Alondra)
│   ├── Scraper_Laptops_MercadoLibre.ipynb      # Scraper de laptops (Luis)
│   ├── Scraper_Tablets_MercadoLibre.ipynb      # Scraper de tablets (Kimberly)
│   ├── Scraper_Auriculares_MercadoLibre.ipynb  # Scraper de auriculares (Ariel)
│   ├── Scraper_Hornos_MercadoLibre.ipynb       # Scraper de hornos (Mayra)
│   ├── subir_datos_atlas.py                    # Sube todos los CSV a MongoDB Atlas
│   └── outputs/                                # CSVs y gráficos generados por el notebook
└── outputs/                                    # CSVs y evidencias del proyecto
    ├── smartphones_ml_YYYYMMDD_HHMMSS.csv
    ├── grafico_precios_descuentos.png
    ├── evidencia_docker_stats.png
    └── evidencia_mongodb_count.png
```

---

## Cómo ejecutar

### Opción A — Dentro de Docker (recomendado)

```bash
# Desde la raíz del repositorio
docker-compose up -d

# Abrir Jupyter Lab en el navegador
# http://localhost:8888
```

Navegar a `work/Proyecto_MercadoLibre/notebooks/` y abrir el notebook correspondiente.

### Opción B — Local (sin Docker)

Instalar dependencias:

```bash
pip install selenium pymongo dnspython undetected-chromedriver pandas beautifulsoup4 matplotlib seaborn openpyxl
```

> **Python 3.13:** si falla la instalación de `undetected-chromedriver`, ejecutar primero `pip install setuptools`.

Abrir el notebook en VS Code o Jupyter Lab y ejecutar todas las celdas en orden.

---

## Notebooks

### `Scraper_MercadoLibre_ECommerce.ipynb`

Scraper completo para la categoría **Smartphones y Celulares**.

| Celda | Descripción |
|-------|-------------|
| Instalación | `pip install` de dependencias requeridas |
| Imports | Librerías + configuración de carpeta `outputs/` |
| Clase `ScraperMercadoLibre` | Selenium + BeautifulSoup, paginación automática |
| Ejecución | Extrae 20 páginas (~900 productos) y guarda CSV |
| MongoDB local | Upsert en `mongodb://localhost:27017/` (solo si Docker está activo) |
| Análisis pandas | Estadísticas de precios y descuentos |
| Visualizaciones | Histograma de precios y pie de descuentos (PNG en `outputs/`) |
| Bitácora | JSON con resumen de la ejecución |

URL base:
```
https://listado.mercadolibre.cl/celulares-telefonos/celulares-smartphones/
```

### `Scraper_Televisores_MercadoLibre.ipynb`

Plantilla para compañeros. Modificar solo la **celda 0** con 3 valores:

```python
RESPONSABLE  = 'NombreApellido'
CATEGORIA    = 'televisores'
BASE_URL     = 'https://listado.mercadolibre.cl/televisores/'
NUM_PAGINAS  = 10
```

Sube automáticamente a la colección `televisores_mercadolibre` en Atlas al final.

---

## Subir datos a MongoDB Atlas

```bash
python notebooks/subir_datos_atlas.py
```

El script:
1. Lee todos los `smartphones_ml_*.csv` desde `outputs/`
2. Deduplica por `(titulo, pagina, responsable)`
3. Limpia la colección anterior en Atlas para evitar conflictos de índice
4. Hace upsert masivo en bloques de 500

**Base de datos Atlas:** `BigData_ECommerce`  
**Colección:** `smartphones_mercadolibre`

---

## Campos extraídos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `titulo` | string | Nombre completo del producto |
| `producto_id` | string | ID único del producto en MercadoLibre (ej: `MLC-1234567`) |
| `marca` | string | Marca extraída de lista de marcas conocidas (`null` si no se reconoce) |
| `precio_actual` | int | Precio de venta en CLP |
| `precio_original` | float | Precio antes del descuento (puede ser `null`) |
| `descuento_porcentaje` | int | Porcentaje de descuento (0 si no hay) |
| `tiene_descuento` | bool | `true` si hay descuento activo |
| `url` | string | URL del producto en MercadoLibre |
| `imagen_url` | string | URL de la imagen principal |
| `pagina` | int | Número de página de la búsqueda |
| `fecha_scraping` | string ISO 8601 | Fecha y hora de la captura |
| `grupo` | string | `"E-Commerce"` |
| `responsable` | string | Nombre del integrante |
| `categoria` | string | Categoría del producto (ej: `"smartphones"`) |

---

## Paginación MercadoLibre

MercadoLibre usa offsets de 48 productos por página:

```
Página 1: <BASE_URL>
Página 2: <BASE_URL>_Desde_49
Página 3: <BASE_URL>_Desde_97
Página n: <BASE_URL>_Desde_{(n-1)*48 + 1}
```

---

## Notas técnicas

- El scraper usa `undetected_chromedriver` para evitar bloqueos anti-bot. Si hay error de versión (`SessionNotCreatedException`), ajustar `version_main=` al número de versión de Chrome instalado.
- El entorno gráfico virtual (`DISPLAY=:99` + Xvfb) es necesario para correr Chrome sin cabeza dentro de Docker.
- PySpark está disponible solo dentro del contenedor Docker; fuera de él el notebook salta esa importación automáticamente.

---

## Hito 1 — Infraestructura y Captura de Datos

### Comando de ejecución

```bash
# Desde la raíz del repositorio (donde está el docker-compose.yml)
docker-compose up -d
```

Esto levanta tres contenedores:
- `bigdata_workspace` → Jupyter Lab + Spark + Chrome (puerto 8888)
- `bigdata_mongodb` → MongoDB local (puerto 27017)
- `bigdata_ui` → Mongo Express, interfaz web para MongoDB (puerto 8081)

---

### Evidencia 1 — Docker Stats

Captura de pantalla del comando `docker stats` mostrando el consumo de recursos de los contenedores activos.
> **Comando:** `docker stats`
![alt text](<outputs/Evidencia Docker Stats.png>)

---

### Evidencia 2 — Conteo de Documentos en MongoDB

Captura desde MongoDB Compass o terminal mostrando el total de documentos en la colección.

> **Comando en Mongo Shell:**
> ```js
> use BigData_ECommerce
> db.smartphones_mercadolibre.countDocuments()
> ```


---

### Tabla de Atributos por Integrante

Todos los scrapers comparten el mismo esquema de 12 campos:

| Campo | Tipo | Descripción | Integrante |
|-------|------|-------------|------------|
| `producto_id` | string | ID único del producto en MercadoLibre | Todos |
| `titulo` | string | Nombre completo del producto | Todos |
| `marca` | string | Marca extraída de lista conocida (`null` si no reconoce) | Todos |
| `precio_actual` | int | Precio de venta en CLP | Todos |
| `precio_original` | float | Precio antes del descuento (`null` si no aplica) | Todos |
| `descuento_porcentaje` | int | Porcentaje de descuento (0 si no hay) | Todos |
| `tiene_descuento` | bool | `true` si hay descuento activo | Todos |
| `url` | string | URL del producto en MercadoLibre | Todos |
| `imagen_url` | string | URL de la imagen principal | Todos |
| `pagina` | int | Número de página del resultado de búsqueda | Todos |
| `fecha_scraping` | string ISO 8601 | Fecha y hora exacta de la captura | Todos |
| `grupo` | string | Identificador del grupo (`"E-Commerce"`) | Todos |
| `responsable` | string | Nombre del integrante que realizó la captura | Todos |
| `categoria` | string | Categoría scrapeada (ej: `"smartphones"`) | Todos |

#### Categorías por integrante

| Integrante | Categoría scrapeada | Colección en Atlas | Docs |
|------------|--------------------|--------------------|------|
| Valentina Aróstica | Smartphones y Celulares | `smartphones_mercadolibre` | 820 |
| Alondra Segovia | Televisores | `televisores_mercadolibre` | 540 |
| Luis Molina | Laptops y Computadores | `laptops_mercadolibre` | — |
| Kimberly Neira | Tablets | `tablets_mercadolibre` | 572 |
| Ariel Peña | Auriculares y Audio | `auriculares_mercadolibre` | 567 |
| Mayra Gutierrez | Hornos | `hornos_mercadolibre` | 510 |
