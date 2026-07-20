import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib3

# Silenciar advertencias de SSL si la página del gobierno tiene certificado vencido
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def descarga_archivos():
    URL = "https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/"
    CARPETA_SALIDA = "data/csv_originales"

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print("1. Cargando la página y detectando campos del formulario...")
    res = session.get(URL, headers=headers, verify=False)
    soup = BeautifulSoup(res.text, "html.parser")

    # --- DETECCIÓN INTELIGENTE DE SELECTIONS POR CONTENIDO ---
    select_depto = None
    select_nivel = None

    for s in soup.find_all("select"):
        texto_opciones = " ".join([opt.text.upper() for opt in s.find_all("option")])
        if "ALTA VERAPAZ" in texto_opciones or "GUATEMALA" in texto_opciones:
            select_depto = s
        elif "DIVERSIFICADO" in texto_opciones:
            select_nivel = s

    # Detección del botón de búsqueda (generalmente es la primera imagen cliqueable del formulario)
    btn_buscar = None
    for inp in soup.find_all("input", attrs={"type": "image"}):
        alt_text = inp.get("alt", "").lower()
        src_text = inp.get("src", "").lower()
        name_text = inp.get("name", "").lower()
        if "buscar" in alt_text or "buscar" in src_text or "buscar" in name_text or "btn" in name_text:
            btn_buscar = inp
            break

    # Si no encontró un botón explícito por nombre, toma el primer input de tipo image
    if not btn_buscar:
        inputs_image = soup.find_all("input", attrs={"type": "image"})
        if inputs_image:
            btn_buscar = inputs_image[0]

    # Diagnóstico de seguridad
    if not select_depto or not select_nivel or not btn_buscar:
        print("\n--- DIAGNÓSTICO DE ERROR ---")
        print(f"Select Depto encontrado: {select_depto is not None}")
        print(f"Select Nivel encontrado: {select_nivel is not None}")
        print(f"Botón Buscar encontrado: {btn_buscar is not None}")
        raise ValueError("No se pudieron localizar los controles en el HTML de la página.")

    # Extraer valor para DIVERSIFICADO
    val_diversificado = None
    for opt in select_nivel.find_all("option"):
        if "DIVERSIFICADO" in opt.text.upper():
            val_diversificado = opt["value"]
            break

    # Extraer departamentos
    departamentos = []
    for opt in select_depto.find_all("option"):
        val = opt.get("value", "").strip()
        texto = opt.text.strip()
        if val and val != "0" and "SELECC" not in texto.upper():
            departamentos.append((val, texto))

    print(f"✓ Formulario detectado correctamente. Se encontraron {len(departamentos)} departamentos.\n")

    # --- PROCESAMIENTO E ITERACIÓN ---
    for i, (cod_depto, nombre_depto) in enumerate(departamentos, start=1):
        nombre_archivo = f"establecimiento ({i}).csv"
        ruta_completa = os.path.join(CARPETA_SALIDA, nombre_archivo)

        if os.path.exists(ruta_completa):
            print(f"[{i}/{len(departamentos)}] {nombre_depto} -> El archivo '{nombre_archivo}' ya existe. (Omitiendo)")
            continue

        print(f"[{i}/{len(departamentos)}] Descargando {nombre_depto}...")

        try:
            viewstate_input = soup.find("input", {"id": "__VIEWSTATE"})
            eventvalidation_input = soup.find("input", {"id": "__EVENTVALIDATION"})

            if not viewstate_input or not eventvalidation_input:
                # Si expira la sesión, volvemos a solicitar la página principal
                res = session.get(URL, headers=headers, verify=False)
                soup = BeautifulSoup(res.text, "html.parser")
                viewstate_input = soup.find("input", {"id": "__VIEWSTATE"})
                eventvalidation_input = soup.find("input", {"id": "__EVENTVALIDATION"})

            payload = {
                "__VIEWSTATE": viewstate_input["value"],
                "__EVENTVALIDATION": eventvalidation_input["value"],
                select_depto["name"]: cod_depto,
                select_nivel["name"]: val_diversificado,
                f"{btn_buscar['name']}.x": "10",
                f"{btn_buscar['name']}.y": "10",
            }

            res_search = session.post(URL, data=payload, headers=headers, verify=False)
            soup = BeautifulSoup(res_search.text, "html.parser")

            tablas = pd.read_html(res_search.text)
            tabla_resultados = None

            for t in tablas:
                if len(t) > 0 and t.shape[1] >= 5:
                    tabla_resultados = t
                    break

            if tabla_resultados is not None:
                tabla_resultados.to_csv(ruta_completa, index=False, encoding="utf-8-sig")
                print(f"   ✓ Guardado correctamente en '{ruta_completa}' ({len(tabla_resultados)} registros).")
            else:
                print(f"   - No se encontraron datos para {nombre_depto}.")

        except Exception as e:
            print(f"   ✕ Error procesando {nombre_depto}: {e}")

        time.sleep(1)

    print("\n¡Proceso finalizado!")

if __name__ == "__main__":
    descarga_archivos()