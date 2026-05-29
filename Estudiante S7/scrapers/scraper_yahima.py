# =========================
# IMPORTS GENERALES
# =========================
# Librerías para automatizar el navegador, esperar elementos,
# manejar pausas humanas y limpiar algunos valores de texto.
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIGURACIÓN GENERAL
# =========================
# Estas variables identifican el scraper como "mio" y ayudan a mantener trazabilidad
# de quién extrajo cada dato.
NOMBRE_GRUPO = "YHadfeg_Amazon"
BUSQUEDA = "laptop"
URL_OBJETIVO = f"https://www.amazon.com/s?k={BUSQUEDA}"


def iniciar_navegador_visible():
    """
    Crea y devuelve un navegador Chrome visible dentro del contenedor.
    Se usa visible para poder intervenir manualmente si Amazon muestra
    captcha o validación humana.
    """
    options = Options()

    # Ruta del navegador dentro del contenedor Docker
    options.binary_location = "/usr/bin/google-chrome"

    # Opciones de estabilidad para Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,768")

    # User-Agent para que la navegación se parezca a un navegador real
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )

    # Se crea el driver
    driver = webdriver.Chrome(service=Service(), options=options)
    return driver


def extraer_texto_seguro(elemento, selectores_css):
    """
    Intenta obtener el texto de un subelemento probando varios selectores CSS.
    Si no encuentra ninguno, devuelve None.
    """
    for selector in selectores_css:
        try:
            texto = elemento.find_element(By.CSS_SELECTOR, selector).text.strip()
            if texto:
                return texto
        except Exception:
            continue
    return None


def limpiar_precio(precio_texto):
    """
    Convierte el precio capturado como texto a número flotante.
    Si no logra convertirlo, devuelve None.
    """
    if not precio_texto:
        return None

    # Elimina símbolos y deja solo números y punto decimal
    texto = precio_texto.replace("$", "").replace(",", "").strip()

    try:
        return float(texto)
    except Exception:
        return None


def detectar_bloqueo(driver):
    """
    Revisa señales básicas de bloqueo real en Amazon.
    Se apoya sobre todo en el título de la página, que suele ser
    más confiable que buscar solo en el HTML.
    """
    titulo = driver.title.lower()
    html = driver.page_source.lower()

    if "robot" in titulo or "captcha" in titulo:
        return True

    if "enter the characters you see below" in html:
        return True

    if "sorry, we just need to make sure you're not a robot" in html:
        return True

    return False


def abrir_producto_en_nueva_pestana(driver, url_producto):
    """
    Abre un producto en una nueva pestaña para capturar información detallada
    como marca, disponibilidad, categoría y descripción.
    """
    driver.execute_script("window.open(arguments[0], '_blank');", url_producto)
    driver.switch_to.window(driver.window_handles[-1])


def cerrar_pestana_actual(driver):
    """
    Cierra la pestaña actual y vuelve a la pestaña principal del listado.
    """
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def capturar_detalle_producto(driver):
    """
    Captura atributos del detalle del producto.
    Devuelve un diccionario con categoría, marca, disponibilidad y descripción.
    """
    detalle = {
        "categoria": None,
        "marca": None,
        "disponibilidad": None,
        "descripcion": None,
    }

    try:
        # Espera breve para que cargue la página del producto
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        # ========= CATEGORÍA =========
        # Se intenta primero desde breadcrumb
        try:
            categorias = driver.find_elements(By.CSS_SELECTOR, "#wayfinding-breadcrumbs_feature_div ul li")
            categorias_limpias = [c.text.strip() for c in categorias if c.text.strip()]
            if categorias_limpias:
                detalle["categoria"] = " > ".join(categorias_limpias)
        except Exception:
            pass

        # ========= MARCA =========
        # Se intenta desde tabla de detalles o bullets técnicos
        posibles_selectores_marca = [
            "#bylineInfo",
            "tr.po-brand td.a-span9 span",
            "tr.po-brand td.a-span9",
            "tr.a-spacing-small td.a-span9 span",
        ]
        marca = None
        for selector in posibles_selectores_marca:
            try:
                marca = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                if marca:
                    break
            except Exception:
                continue

        if marca:
            detalle["marca"] = marca.replace("Brand:", "").replace("Visit the", "").replace("Store", "").strip()

        # ========= DISPONIBILIDAD =========
        posibles_selectores_stock = [
            "#availability span",
            "#availabilityInsideBuyBox_feature_div",
            "#outOfStock span",
        ]
        for selector in posibles_selectores_stock:
            try:
                stock = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                if stock:
                    detalle["disponibilidad"] = stock
                    break
            except Exception:
                continue

        # ========= DESCRIPCIÓN =========
        # Primero intenta con el bullet principal
        posibles_selectores_descripcion = [
            "#feature-bullets ul li span",
            "#productDescription span",
            "#productFactsDesktopExpander p span",
        ]

        descripciones = []
        for selector in posibles_selectores_descripcion:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                textos = [e.text.strip() for e in elementos if e.text.strip()]
                if textos:
                    descripciones = textos[:3]
                    break
            except Exception:
                continue

        if descripciones:
            detalle["descripcion"] = " | ".join(descripciones)

    except Exception:
        pass

    return detalle


def ejecutar_extraccion():
    """
    Función principal del scraper.
    Abre Amazon, permite intervención humana si hay bloqueo, captura
    productos del listado y entra al detalle de algunos para completar
    los campos requeridos.
    
    Esta función retorna una lista de diccionarios, tal como pide la guía
    para que luego el archivo main.py pueda integrar los datos del grupo. 
    """
    driver = None
    datos_finales = []

    try:
        # =========================
        # 1. INICIAR NAVEGADOR
        # =========================
        driver = iniciar_navegador_visible()
        print("Abriendo Amazon...")
        driver.get(URL_OBJETIVO)

        # =========================
        # 2. PAUSA DE INTERVENCIÓN HUMANA
        # =========================
        # Se deja una pausa para que puedas revisar en VNC si aparece captcha
        # y resolverlo manualmente antes de continuar.
        print("\nACCIÓN REQUERIDA:")
        print("1. Ve a http://localhost:6080/vnc.html")
        print("2. Revisa si Amazon muestra captcha o validación.")
        print("3. Si aparece, resuélvelo manualmente.")
        print("4. Cuando veas el listado de productos, vuelve aquí.")
        input("\nPresiona ENTER para continuar con la extracción...")

        # =========================
        # 3. VERIFICAR BLOQUEO
        # =========================
        if detectar_bloqueo(driver):
            print("Bloqueo detectado. No se continuará con la extracción.")
            return datos_finales

        print("Sin bloqueo evidente. Iniciando scraping...")

        # =========================
        # 4. ESPERAR LISTADO DE PRODUCTOS
        # =========================
        # Se espera a que aparezcan los bloques principales del resultado.
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.s-result-item[data-component-type='s-search-result']")
            )
        )
        time.sleep(2)

        productos = driver.find_elements(
            By.CSS_SELECTOR,
            "div.s-result-item[data-component-type='s-search-result']"
        )

        print(f"Bloques encontrados en el listado: {len(productos)}")

        # =========================
        # 5. RECORRER PRODUCTOS
        # =========================
        # Se recorren varios productos del listado. Puedes ajustar el límite.
        for i, producto in enumerate(productos[:8], start=1):
            try:
                # ---------- NOMBRE DEL PRODUCTO ----------
                nombre_producto = extraer_texto_seguro(producto, [
                    "h2 span",
                    "a h2 span",
                ])

                # ---------- URL DEL PRODUCTO ----------
                url_producto = None
                try:
                    enlace = producto.find_element(By.CSS_SELECTOR, "h2 a")
                    url_producto = enlace.get_attribute("href")
                except Exception:
                    pass

                # ---------- PRECIO ----------
                # Amazon suele separar entero y decimal en distintos spans.
                precio_entero = extraer_texto_seguro(producto, [
                    "span.a-price-whole"
                ])
                precio_decimal = extraer_texto_seguro(producto, [
                    "span.a-price-fraction"
                ])

                precio = None
                if precio_entero:
                    if precio_decimal:
                        precio_texto = f"{precio_entero}.{precio_decimal}"
                    else:
                        precio_texto = precio_entero
                    precio = limpiar_precio(precio_texto)

                # ---------- RATING ----------
                rating = extraer_texto_seguro(producto, [
                    "span.a-icon-alt"
                ])

                # ---------- NÚMERO DE REVIEWS ----------
                numero_reviews = extraer_texto_seguro(producto, [
                    "span.a-size-base.s-underline-text",
                    "a[href*='customerReviews'] span.a-size-base",
                ])

                # Valores por defecto del detalle
                categoria = None
                marca = None
                disponibilidad = None
                descripcion = None

                # ---------- ENTRAR AL DETALLE ----------
                # Solo entra al detalle si existe enlace. Esto permite
                # completar campos que no siempre vienen en el listado.
                if url_producto:
                    abrir_producto_en_nueva_pestana(driver, url_producto)

                    detalle = capturar_detalle_producto(driver)
                    categoria = detalle["categoria"]
                    marca = detalle["marca"]
                    disponibilidad = detalle["disponibilidad"]
                    descripcion = detalle["descripcion"]

                    cerrar_pestana_actual(driver)

                # ---------- CONSTRUIR REGISTRO ----------
                # El registro mantiene nombres consistentes para facilitar
                # la integración posterior con Spark.
                registro = {
                    "nombre_producto": nombre_producto,
                    "precio": precio,
                    "rating": rating,
                    "numero_reviews": numero_reviews,
                    "categoria": categoria,
                    "marca": marca,
                    "disponibilidad": disponibilidad,
                    "descripcion": descripcion,
                    "grupo": NOMBRE_GRUPO,
                    "fuente": "Amazon",
                    "busqueda": BUSQUEDA,
                    "fecha_captura": time.strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Se agrega solo si al menos hay nombre
                if registro["nombre_producto"]:
                    datos_finales.append(registro)
                    print(f"Producto {i} agregado: {registro['nombre_producto'][:60]}")

            except Exception as e:
                print(f"Error en producto {i}: {e}")
                continue

        print(f"\nExtracción finalizada. Registros capturados: {len(datos_finales)}")
        return datos_finales

    except Exception as e:
        print(f"Error general en el scraper: {e}")
        return datos_finales

    finally:
        if driver:
            driver.quit()
            print("Navegador cerrado.")