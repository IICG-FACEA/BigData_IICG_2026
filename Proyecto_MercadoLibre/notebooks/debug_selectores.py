# DEBUG: Ver qué HTML está recibiendo Selenium

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# Configurar Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)

url = "https://listado.mercadolibre.cl/celulares-telefonos/celulares-smartphones/"
driver.get(url)

# CLAVE: Esperar más tiempo
print("⏳ Esperando carga de página...")
time.sleep(5)  # Aumentar de 3 a 5 segundos

# Guardar HTML completo para revisar
html_completo = driver.page_source
with open('outputs/debug_mercadolibre.html', 'w', encoding='utf-8') as f:
    f.write(html_completo)

print("✓ HTML guardado en outputs/debug_mercadolibre.html")

# Probar diferentes selectores
soup = BeautifulSoup(html_completo, 'html.parser')

print("\n🔍 PROBANDO SELECTORES:\n")

# Selector 1: ui-search-layout__item
test1 = soup.select('li.ui-search-layout__item')
print(f"1. li.ui-search-layout__item → {len(test1)} encontrados")

# Selector 2: Alternativa
test2 = soup.select('li[class*="ui-search"]')
print(f"2. li[class*='ui-search'] → {len(test2)} encontrados")

# Selector 3: Otra alternativa
test3 = soup.select('div.ui-search-result')
print(f"3. div.ui-search-result → {len(test3)} encontrados")

# Selector 4: Contenedor general
test4 = soup.select('[class*="search-result"]')
print(f"4. [class*='search-result'] → {len(test4)} encontrados")

# Ver las primeras clases encontradas
print("\n📋 CLASES EN EL HTML:")
all_divs = soup.find_all(['li', 'div'], limit=20)
for i, div in enumerate(all_divs[:10]):
    if div.get('class'):
        print(f"{i+1}. {div.get('class')}")

driver.quit()
print("\n💡 Abre outputs/debug_mercadolibre.html y busca manualmente el contenedor de productos")