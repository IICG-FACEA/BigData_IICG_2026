import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NOMBRE_GRUPO     = "G1_Amazon_ValentinaArostica"
CATEGORIA_PRODUCTO = "Smartphones"
URL_BUSQUEDA     = "https://www.amazon.es/s?k=smartphones"


def ejecutar_extraccion():
    """
    Extrae smartphones de Amazon.es y retorna una lista de diccionarios
    con los campos estandarizados del grupo: identificador, valor, categoria, grupo.
    """
    datos_finales = []
    driver        = None

    os.system("pkill -9 chrome")
    os.system("pkill -9 chromedriver")
    os.system("rm -rf /tmp/.com.google.Chrome.*")

    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        driver = webdriver.Chrome(options=options)
        driver.get(URL_BUSQUEDA)

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
            )
        )
        time.sleep(3)

        bloques = driver.find_elements(
            By.CSS_SELECTOR, "div[data-component-type='s-search-result']"
        )

        for bloque in bloques:
            try:
                nombre = bloque.find_element(By.TAG_NAME, "h2").text.strip()
                if not nombre:
                    continue
                precio_texto  = bloque.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                precio_limpio = precio_texto.replace(".", "").replace(",", "").strip()
                precio        = float(precio_limpio) if precio_limpio.isdigit() else 0.0

                datos_finales.append({
                    "identificador": nombre,
                    "valor":         precio,
                    "categoria":     CATEGORIA_PRODUCTO,
                    "grupo":         NOMBRE_GRUPO,
                    "fecha_captura": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            except:
                continue

    except Exception as e:
        print(f"Error en scraper ValentinaArostica: {e}")

    finally:
        if driver is not None:
            driver.quit()

    print(f"[ValentinaArostica] Productos extraídos: {len(datos_finales)}")
    return datos_finales
