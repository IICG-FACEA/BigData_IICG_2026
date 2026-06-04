from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
import pymongo, certifi
import yfinance as yf
import pandas as pd
from datetime import datetime


service = Service(r"C:\Users\Nicole\Desktop\Clase Big Data\drivers\geckodriver.exe")
options = Options()
options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"  # ajusta si tu Firefox está en otra carpeta

driver = webdriver.Firefox(service=service, options=options)
driver.get("https://www.google.com")
print(driver.title)
driver.quit()


def ejecutar_extraccion():
    url = "https://www.investing.com/indices/germany-30-historical-data"
    
    service = Service(r"C:\Users\Nicole\Desktop\Clase Big Data\drivers\geckodriver.exe")
    options = Options()
    options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
    
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    time.sleep(5)
    filas = driver.find_elements(By.XPATH, '//table[@class="common-table"]/tbody/tr')

    datos_finales = []
    for fila in filas:
        columnas = fila.find_elements(By.TAG_NAME, 'td')
        if len(columnas) >= 6:
            fecha_str = columnas[0].text
            try:
                fecha = datetime.strptime(fecha_str, "%b %d, %Y")  # ej: "May 15, 2024"
            except:
                continue

            # Filtrar solo entre 15/05/2024 y 15/05/2026
            if datetime(2024, 5, 15) <= fecha <= datetime(2026, 5, 15):
                datos_finales.append({
                    "Fecha": fecha_str,
                    "Precio": columnas[1].text,
                    "Máximo": columnas[2].text,
                    "Mínimo": columnas[3].text,
                    "Cierre": columnas[4].text,
                    "Variación": columnas[5].text,
                    "grupo": "Nicole_Team"
                })

    driver.quit()
    print("Scraping completo. Registros obtenidos:", len(datos_finales))
    return datos_finales[:500]  # limitar a 500

# --- PASO 2: GUARDAR EN MONGODB ---
def guardar_en_mongo(datos, db_name="BigData_UCN", collection_name="dax_html"):
    uri = "mongodb+srv//Finanzasymercado:ternurines123@cluster0.uia9vsi.mongodb.net/?retryWrites=true&w=majority"
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
    db = client[db_name]
    coleccion = db[collection_name]
    coleccion.insert_many(datos)
    print("Datos guardados en MongoDB:", len(datos))

# --- PASO 3: COMPLEMENTAR CON YAHOO FINANCE ---
def extraer_yahoo():
    dax = yf.Ticker("^GDAXI")
    df = dax.history(start="2024-05-15", end="2026-05-15")

    # Renombrar columnas
    df = df.rename(columns={
        "Date": "Fecha",
        "Open": "Apertura",
        "High": "Máximo",
        "Low": "Mínimo",
        "Close": "Precio",
        "Volume": "Volumen"
    })

    print("Yahoo Finance datos obtenidos:", len(df))
    return df

# --- MAIN ---
if __name__ == "__main__":
    datos_dax = ejecutar_extraccion()
    guardar_en_mongo(datos_dax)
    datos_yahoo = extraer_yahoo()
    print(datos_yahoo.head())
