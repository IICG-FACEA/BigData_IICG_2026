# Contenido de scrapers/scraper_RodOrt.py
 import os
 from selenium import webdriver
 # ... (todos los imports que ya tienes)

 def ejecutar_extraccion():
     datos_finales = []
     # ... (toda su logica de Selenium para extraer)...

     for bloque in bloques:
         # Extrae...
         datos_finales.append({
              "identificador": nombre,
              "valor": precio,
              "grupo": "FyM_Team" # Su identificador
        })

     return datos_finales