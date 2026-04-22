# Grupo 1 — E-commerce & Precios
**Curso:** Big Data para la toma de decisiones — Universidad Católica del Norte  
**Objetivo Estratégico:** Monitoreo de inflación y competencia en e-commerce chileno  
**Fuentes:** MercadoLibre Chile  

---

## Hito 1 — Infraestructura y Captura de Datos

### Business Case

**1. Situación Problema**  
Los retailers y consumidores toman decisiones de compra y fijación de precios sin visibilidad en tiempo real del mercado. Las variaciones de precio en categorías tecnológicas (smartphones, laptops, TVs) ocurren diariamente, pero no existe un sistema automatizado que registre y analice esos cambios de forma histórica.

**2. Propuesta de Valor**  
Mediante scraping automatizado de MercadoLibre, capturamos precios, descuentos y atributos de producto en múltiples categorías. Esto permite detectar tendencias de inflación por categoría, identificar patrones de descuento, y comparar competitividad entre marcas con datos reales y actualizados.

**3. Análisis de las 4V**

| V | Justificación |
|---|--------------|
| **Volumen** | Se requieren >3.000 registros (500 por integrante) para obtener representatividad estadística por categoría y detectar variaciones de precio con significancia. |
| **Variedad** | Cada documento captura 12 atributos distintos: precio actual, precio original, descuento, marca, título, URL, imagen, página, fecha, grupo, responsable y categoría. |
| **Veracidad** | Los datos se limpian eliminando valores nulos en precios, descartando registros sin título, y validando que los precios sean numéricos (int/float). El upsert evita duplicados. |
| **Velocidad** | En retail de tecnología los precios cambian diariamente. El scraper debe ejecutarse al menos cada 24 horas para que el análisis no quede obsoleto. |

---

### Cómo ejecutar el proyecto

**Requisito:** Docker Desktop instalado y corriendo.

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd avancesproyectobigdata2026-1e-commerce-precios

# 2. Levantar los contenedores
docker-compose up -d

# 3. Acceder a Jupyter Lab
# Abrir en el navegador: http://localhost:8888

# 4. Ejecutar el scraper
# Abrir: Proyecto_MercadoLibre/notebooks/Scraper_MercadoLibre_ECommerce.ipynb
# Ejecutar todas las celdas

# 5. Subir datos a MongoDB Atlas (base de datos compartida)
python Proyecto_MercadoLibre/notebooks/subir_datos_atlas.py
```

**Servicios disponibles:**
| Servicio | URL |
|---------|-----|
| Jupyter Lab | http://localhost:8888 |
| MongoDB local | mongodb://localhost:27017 |
| Mongo Express (UI) | http://localhost:8081 |
| Spark UI | http://localhost:4040 |
| Escritorio visual | http://localhost:6080 |

---

### Tabla de Atributos por Integrante

| Campo | Tipo | Descripción | Integrante |
|-------|------|-------------|-----------|
| `titulo` | string | Nombre completo del producto | Todos |
| `marca` | string | Marca o tipo de producto | Todos |
| `precio_actual` | int | Precio de venta en CLP | Todos |
| `precio_original` | float | Precio antes del descuento en CLP | Todos |
| `descuento_porcentaje` | int | Porcentaje de descuento aplicado | Todos |
| `tiene_descuento` | bool | Indica si el producto tiene descuento activo | Todos |
| `url` | string | URL del producto en MercadoLibre | Todos |
| `imagen_url` | string | URL de la imagen principal del producto | Todos |
| `pagina` | int | Número de página del resultado de búsqueda | Todos |
| `fecha_scraping` | datetime | Fecha y hora exacta de la captura | Todos |
| `grupo` | string | Identificador del grupo (E-Commerce) | Todos |
| `responsable` | string | Nombre del integrante que realizó la captura | Todos |

### Colecciones en MongoDB Atlas (`BigData_ECommerce`)

| Colección | Categoría scrapeada | Responsable | Docs |
|-----------|-------------------|-------------|------|
| `smartphones_mercadolibre` | Smartphones y celulares | Valentina | 621 |
| `laptops_mercadolibre` | Laptops y computadores | _(pendiente)_ | — |
| `televisores_mercadolibre` | Televisores | _(pendiente)_ | — |
| `tablets_mercadolibre` | Tablets | _(pendiente)_ | — |
| `auriculares_mercadolibre` | Auriculares y audio | _(pendiente)_ | — |
| `electrodomesticos_mercadolibre` | Electrodomésticos | _(pendiente)_ | — |

---

### Evidencias

> **Evidencia 1 — Docker Stats**  
> _(Cada integrante debe reemplazar esta línea con su captura de `docker stats`)_  
> Comando: `docker stats`

> **Evidencia 2 — Conteo de documentos en MongoDB**  
> _(Cada integrante debe reemplazar esta línea con su captura del conteo)_  
> Comando en Mongo Shell: `db.smartphones_mercadolibre.countDocuments()`

---

### Estructura del repositorio

```
avancesproyectobigdata2026-1e-commerce-precios/
├── docker-compose.yml
├── Dockerfile
├── Proyecto_MercadoLibre/
│   ├── notebooks/
│   │   ├── Scraper_MercadoLibre_ECommerce.ipynb   # Scraper principal
│   │   └── subir_datos_atlas.py                   # Subida a MongoDB Atlas
│   └── outputs/
│       └── smartphones_ml_*.csv                   # Datos scrapeados
├── Semana 1 Configuración del Entorno/
├── Semana 2 Scrapping Estatico/
├── Semana 3 Scraping Dinamico/
├── Semana 4 Mongo DB/
├── Semana 5 MongoDB-Spark/
└── Semana 6 Anti-bot Entorno Visual para Selenium/
```

---

### Conexión a MongoDB Atlas (base compartida del grupo)

```python
URI = "mongodb+srv://valentinaarostica_db_user:ecommerce@cluster0.gxkvvjs.mongodb.net/BigData_ECommerce?appName=Cluster0"
```

Base de datos: `BigData_ECommerce`
