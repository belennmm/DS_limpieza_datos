"""
Diagnóstico del estado inicial de los datos (Proyecto 1, punto 3, incisos a-h).

Este módulo NO modifica los datos. Solo los lee y genera tablas y
estadísticas de diagnóstico, tal como pide la guía: "Este análisis debe
estar respaldado por tablas y estadísticas generadas usando código."

Reutiliza:
- unirdata.OUTPUT: ruta del dataset ya unido (data/interim/establecimientos_todos_raw.csv)
- limpiarcsvcrudos.PATRON_CODIGO: regex de formato de CODIGO
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

import limpiarcsvcrudos
import unirdata


RUTA_DATOS = unirdata.OUTPUT
CARPETA_DOCS = Path("docs")
RUTA_REPORTE = CARPETA_DOCS / "diagnostico_inicial.csv"

# Catálogos de referencia para el inciso f (valores fuera de dominio).
# Nota: son un punto de partida razonable; deben ajustarse/confirmarse
# contra el catálogo oficial del MINEDUC si se dispone de él.
DEPARTAMENTOS_VALIDOS = {
    "GUATEMALA", "EL PROGRESO", "SACATEPEQUEZ", "CHIMALTENANGO", "ESCUINTLA",
    "SANTA ROSA", "SOLOLA", "TOTONICAPAN", "QUETZALTENANGO", "SUCHITEPEQUEZ",
    "RETALHULEU", "SAN MARCOS", "HUEHUETENANGO", "QUICHE", "BAJA VERAPAZ",
    "ALTA VERAPAZ", "PETEN", "IZABAL", "ZACAPA", "CHIQUIMULA", "JALAPA",
    "JUTIAPA",
}

SECTORES_VALIDOS = {"OFICIAL", "PRIVADO", "COOPERATIVA", "MUNICIPAL"}

NIVELES_VALIDOS = {"PREPRIMARIA", "PRIMARIA", "BASICO", "DIVERSIFICADO"}

PATRON_TELEFONO = r"^\d{8}$"

# -------------------------------------------------------------------------
# Carácter de reemplazo Unicode (U+FFFD). Aparece cuando un archivo se
# decodificó con una codificación distinta a la que realmente tenía
# (mojibake), por ejemplo "P�REZ" en vez de "PÉREZ". text_codif() en
# limpiarcsvcrudos.py puede "tener éxito" con cp1252/latin-1 sin lanzar
# UnicodeDecodeError y aun así dejar texto corrupto, así que hay que
# detectarlo aparte.
# -------------------------------------------------------------------------
CARACTER_CORRUPTO = "\ufffd"


def cargar_datos(ruta: Path = RUTA_DATOS) -> pd.DataFrame:
    """Carga el dataset unido. No hace ninguna limpieza."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta.resolve()}. "
            "Ejecute primero limpiarcsvcrudos.py y luego unirdata.py."
        )

    return pd.read_csv(ruta, dtype="string", encoding="utf-8-sig")


# ---------------------------------------------------------------------
# a. Número de registros y variables
# ---------------------------------------------------------------------
def num_registros_variables(dataframe: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "metrica": ["registros", "variables"],
            "valor": [dataframe.shape[0], dataframe.shape[1]],
        }
    )


# ---------------------------------------------------------------------
# b. Tipo de dato de cada variable
# ---------------------------------------------------------------------
def tipos_dato(dataframe: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "variable": dataframe.columns,
            "tipo_dato": [str(dataframe[columna].dtype) for columna in dataframe.columns],
        }
    )


# ---------------------------------------------------------------------
# c. Cantidad y porcentaje de valores faltantes por variable
# ---------------------------------------------------------------------
def valores_faltantes(dataframe: pd.DataFrame) -> pd.DataFrame:
    total_filas = dataframe.shape[0]
    conteo = dataframe.isna().sum()
    porcentaje = (conteo / total_filas * 100).round(2)

    return pd.DataFrame(
        {
            "variable": dataframe.columns,
            "faltantes": conteo.values,
            "porcentaje_faltantes": porcentaje.values,
        }
    ).sort_values(by="faltantes", ascending=False, ignore_index=True)


# ---------------------------------------------------------------------
# d. Cantidad de valores únicos
# ---------------------------------------------------------------------
def valores_unicos(dataframe: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "variable": dataframe.columns,
            "valores_unicos": [
                dataframe[columna].nunique(dropna=True) for columna in dataframe.columns
            ],
        }
    )


# ---------------------------------------------------------------------
# e. Cantidad de registros duplicados exactos
# ---------------------------------------------------------------------
def duplicados_exactos(dataframe: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    cantidad = int(dataframe.duplicated(keep="first").sum())

    columnas_orden = list(dataframe.columns)
    ejemplos = (
        dataframe.loc[dataframe.duplicated(keep=False)]
        .sort_values(by=columnas_orden)
        .head(10)
    )

    return cantidad, ejemplos


# ---------------------------------------------------------------------
# f. Variables con valores fuera de dominio o inconsistentes
# ---------------------------------------------------------------------
# Patrones Regex Globales para Validación
# ---------------------------------------------------------------------
# Detecta cualquier combinación de solo guiones, guiones bajos, puntos,
# signos de interrogación, asteriscos, espacios o barras (ej: '-', '__', '---------')
PATRON_BASURA = re.compile(r"^[\s\-_.\?*#/\\=]+$")
PATRON_CON_NUMEROS = re.compile(r"\d")
PATRON_TELEFONO = r"^\d{8}$"
STATUS_VALIDOS: set[str] = set()
AREAS_VALIDAS: set[str] = set()
CARACTER_CORRUPTO = "\ufffd"
TOKENS_NULOS_DISFRAZADOS = {
    "N/A", "N.A", "NA", "S/N", "S/D", "SD",
    "NULL", "NUL", "NONE",
    ".", "..", "...",
    "SIN DATO", "SIN DATOS", "SIN INFORMACION", "SIN INFORMACIÓN",
    "NO APLICA", "NO DISPONIBLE", "NO REGISTRA", "NINGUNO", "NINGUNA",
    "DESCONOCIDO", "DESCONOCIDA", "0",
}
 
PATRON_GUIONES = r"^-+$"  # "-", "--", "---", "-------", etc.


def es_texto_invalido(valor: str) -> bool:
    """Valida si un texto es solo relleno basura o si contiene números no deseados."""
    val_str = str(valor).strip()
    if not val_str:
        return False
 
    return bool(PATRON_BASURA.match(val_str) or PATRON_CON_NUMEROS.search(val_str))
 
 
def valores_fuera_dominio(dataframe: pd.DataFrame) -> pd.DataFrame:
    resultados = []
 
    # 1. Variables categóricas (dominio por lista de permitidos + filtro de símbolos/números)
    categorias_config = {
        "DEPARTAMENTO": DEPARTAMENTOS_VALIDOS,
        "SECTOR": SECTORES_VALIDOS,
        "NIVEL": NIVELES_VALIDOS,
        "STATUS": STATUS_VALIDOS,
        "AREA": AREAS_VALIDAS,
    }
 
    for columna, lista_validos in categorias_config.items():
        if columna not in dataframe.columns:
            continue
 
        valores = dataframe[columna].dropna().astype("string").str.strip().str.upper().unique()
        valores = [valor for valor in valores if valor]
 
        invalidos = []
        for valor in valores:
            es_basura = bool(PATRON_BASURA.match(valor))
            tiene_numeros = bool(PATRON_CON_NUMEROS.search(valor))
            no_esta_en_lista = bool(lista_validos and valor not in lista_validos)
 
            if es_basura or tiene_numeros or no_esta_en_lista:
                invalidos.append(valor)
 
        invalidos = sorted(set(invalidos))
        resultados.append(
            {
                "variable": columna,
                "valores_invalidos": len(invalidos),
                "ejemplos": ", ".join(invalidos) if invalidos else "Ninguno",
            }
        )
 
    # 2. Variables de nombres/personas/geografía (no deben tener números ni ser símbolos)
    columnas_nombres = ["SUPERVISOR", "DIRECTOR", "MUNICIPIO"]
    for columna in columnas_nombres:
        if columna not in dataframe.columns:
            continue
 
        valores = dataframe[columna].dropna().astype("string").str.strip().unique()
        valores = [valor for valor in valores if valor]
 
        invalidos = sorted(valor for valor in valores if es_texto_invalido(valor))
 
        resultados.append(
            {
                "variable": columna,
                "valores_invalidos": len(invalidos),
                "ejemplos": ", ".join(invalidos) if invalidos else "Ninguno",
            }
        )
 
    # 3. CODIGO (patrón + símbolos)
    if "CODIGO" in dataframe.columns:
        codigos = dataframe["CODIGO"].dropna().astype("string").str.strip()
        codigos = codigos[codigos != ""]
 
        patron_codigo = getattr(limpiarcsvcrudos, "PATRON_CODIGO", r"^[A-Z0-9-]+$")
 
        mascara_invalidos = ~codigos.str.match(patron_codigo, na=False) | codigos.str.match(PATRON_BASURA, na=False)
        invalidos = sorted(codigos[mascara_invalidos].unique())
 
        resultados.append(
            {
                "variable": "CODIGO",
                "valores_invalidos": len(invalidos),
                "ejemplos": ", ".join(invalidos) if invalidos else "Ninguno",
            }
        )
 
    # 4. TELEFONO (patrón + símbolos)
    if "TELEFONO" in dataframe.columns:
        telefonos = dataframe["TELEFONO"].dropna().astype("string").str.strip()
        telefonos = telefonos[telefonos != ""]
 
        mascara_invalidos = ~telefonos.str.match(PATRON_TELEFONO, na=False) | telefonos.str.match(PATRON_BASURA, na=False)
        invalidos = sorted(telefonos[mascara_invalidos].unique())
 
        resultados.append(
            {
                "variable": "TELEFONO",
                "valores_invalidos": len(invalidos),
                "ejemplos": ", ".join(invalidos) if invalidos else "Ninguno",
            }
        )
 
    return pd.DataFrame(resultados)
 
# -------------------------------------------------------------------------
# Impresión "resumen primero, detalle después" en vez de una sola tabla
# ancha. Cuando "ejemplos" trae muchos valores (ej. ESTABLECIMIENTO con
# 182 inválidos), meterlo en una columna de la tabla obliga a pandas a
# rellenar con espacios todas las demás filas para alinear el ancho, lo
# que deja huecos gigantes al imprimir. Separando resumen y detalle se
# evita ese problema y además queda más legible.
# -------------------------------------------------------------------------
def imprimir_fuera_dominio(fuera_dominio_df: pd.DataFrame) -> None:
    if fuera_dominio_df.empty:
        print("Sin hallazgos.")
        return
 
    resumen = fuera_dominio_df[["variable", "valores_invalidos"]]
    print(resumen.to_string(index=False))
 
    con_invalidos = fuera_dominio_df[fuera_dominio_df["valores_invalidos"] > 0]
    if con_invalidos.empty:
        return
 
    print()
    print("Detalle de valores inválidos por variable:")
    for _, fila in con_invalidos.iterrows():
        print(f"- {fila['variable']} ({fila['valores_invalidos']}):")
        print(f"    {fila['ejemplos']}")

# ---------------------------------------------------------------------
# g. Variables con formatos inconsistentes
# ---------------------------------------------------------------------
def formatos_inconsistentes(dataframe: pd.DataFrame) -> pd.DataFrame:
    resultados = []

    columnas_texto = [
        columna for columna in dataframe.columns if dataframe[columna].dtype == "string"
    ]

    for columna in columnas_texto:
        serie = dataframe[columna].dropna().astype("string")

        espacios_borde = int((serie != serie.str.strip()).sum())
        espacios_multiples = int(serie.str.contains(r"\s{2,}", regex=True, na=False).sum())

        # -----------------------------------------------------------
        # Caracteres corruptos (mojibake): "P�REZ", "QUI�ONEZ", etc.
        # -----------------------------------------------------------
        mascara_corruptos = serie.str.contains(CARACTER_CORRUPTO, regex=False, na=False)
        caracteres_corruptos = int(mascara_corruptos.sum())

        resultados.append(
            {
                "variable": columna,
                "espacios_borde": espacios_borde,
                "espacios_multiples": espacios_multiples,
                "caracteres_corruptos": caracteres_corruptos,
                "ejemplos_corruptos": ", ".join(serie.loc[mascara_corruptos].unique()[:5]),
            }
        )

    if "TELEFONO" in dataframe.columns:
        telefonos = dataframe["TELEFONO"].dropna().astype("string")
        con_letras = int(telefonos.str.contains(r"[A-Za-z]", regex=True, na=False).sum())

        for fila in resultados:
            if fila["variable"] == "TELEFONO":
                fila["con_letras"] = con_letras

    return pd.DataFrame(resultados)


# ---------------------------------------------------------------------
# g (extra). Patrones de formato heterogéneos dentro de una misma columna.
# Por ejemplo DISTRITO trae al menos 3 esquemas distintos en los datos
# reales: "22-01-1221", "22-001", "22-99-0210". formatos_inconsistentes()
# no lo detectaba porque solo revisaba espacios/mayúsculas, no la
# "forma" del valor.
# ---------------------------------------------------------------------
def _firma_formato(valor: str) -> str:
    """Convierte un valor en una firma de forma: dígitos -> N, letras -> A."""
    firma = re.sub(r"[0-9]", "N", str(valor))
    firma = re.sub(r"[A-Za-zÀ-ÿ]", "A", firma)
    return firma


def patrones_formato(dataframe: pd.DataFrame, columnas: tuple[str, ...] = ("CODIGO", "DISTRITO")) -> pd.DataFrame:
    resultados = []

    for columna in columnas:
        if columna not in dataframe.columns:
            continue

        serie = dataframe[columna].dropna().astype("string").str.strip()
        if serie.empty:
            continue

        firmas = serie.map(_firma_formato)
        conteo_firmas = firmas.value_counts()
        patron_mas_comun = conteo_firmas.index[0]

        minoritarios = serie.loc[firmas != patron_mas_comun]

        resultados.append(
            {
                "variable": columna,
                "cantidad_patrones_distintos": int(conteo_firmas.shape[0]),
                "patron_mas_comun": patron_mas_comun,
                "valores_con_patron_distinto": int(minoritarios.shape[0]),
                "ejemplos_patron_distinto": ", ".join(minoritarios.unique()[:5]),
            }
        )

    return pd.DataFrame(resultados)


# ---------------------------------------------------------------------
# f/g (extra). Categorías escritas de diferentes maneras (ej. "Guatemala"
# vs "GUATEMALA" vs "Guatemla"), buscado de forma genérica en cualquier
# columna con cardinalidad baja (candidata a ser categórica), no solo en
# las que ya tenían catálogo hardcodeado (DEPARTAMENTO/SECTOR/NIVEL).
# Esto cubre columnas nuevas como AREA, STATUS, MODALIDAD, JORNADA, PLAN
# sin tener que adivinar su catálogo oficial completo.
# ---------------------------------------------------------------------
def _normalizar_categoria(valor: str) -> str:
    texto = str(valor).strip().upper()
    texto = "".join(
        caracter for caracter in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(caracter)
    )
    texto = re.sub(r"[^A-Z0-9]+", " ", texto).strip()
    return texto


def categorias_similares(dataframe: pd.DataFrame, maximo_valores_unicos: int = 60) -> pd.DataFrame:
    resultados = []

    for columna in dataframe.columns:
        if dataframe[columna].dtype != "string":
            continue

        serie = dataframe[columna].dropna().astype("string")
        valores_unicos_columna = serie.unique()

        if not (1 < len(valores_unicos_columna) <= maximo_valores_unicos):
            continue

        grupos: dict[str, list[str]] = {}
        for valor in valores_unicos_columna:
            clave = _normalizar_categoria(valor)
            grupos.setdefault(clave, []).append(valor)

        grupos_con_variantes = {clave: variantes for clave, variantes in grupos.items() if len(variantes) > 1}

        if grupos_con_variantes:
            ejemplos = "; ".join(" | ".join(variantes) for variantes in list(grupos_con_variantes.values())[:5])
            resultados.append(
                {
                    "variable": columna,
                    "grupos_con_variantes": len(grupos_con_variantes),
                    "ejemplos": ejemplos,
                }
            )

    return pd.DataFrame(resultados)


# ---------------------------------------------------------------------
# h. Identificación de problemas potenciales de calidad de datos
# ---------------------------------------------------------------------
def problemas_potenciales(
    faltantes_df: pd.DataFrame,
    cantidad_duplicados: int,
    fuera_dominio_df: pd.DataFrame,
    formato_df: pd.DataFrame,
    patrones_df: pd.DataFrame | None = None,
    categorias_df: pd.DataFrame | None = None,
) -> list[str]:
    problemas = []

    con_faltantes = faltantes_df.loc[faltantes_df["faltantes"] > 0, "variable"].tolist()
    if con_faltantes:
        problemas.append(f"Valores faltantes en: {', '.join(con_faltantes)}")

    if cantidad_duplicados > 0:
        problemas.append(f"{cantidad_duplicados} registros duplicados exactos")

    for _, fila in fuera_dominio_df.iterrows():
        if fila["valores_invalidos"] > 0:
            problemas.append(
                f"{fila['variable']}: {fila['valores_invalidos']} valores fuera de dominio"
            )

    for _, fila in formato_df.iterrows():
        if fila.get("espacios_borde", 0) > 0 or fila.get("espacios_multiples", 0) > 0:
            problemas.append(f"{fila['variable']}: posibles problemas de formato de texto")

        con_letras = fila.get("con_letras", 0)
        if pd.notna(con_letras) and con_letras > 0:
            problemas.append(f"{fila['variable']}: contiene letras en un campo numérico")

        # -------------------------------------------------------------
        # Nuevo: caracteres corruptos (mojibake, ej. "P�REZ")
        # -------------------------------------------------------------
        caracteres_corruptos = fila.get("caracteres_corruptos", 0)
        if pd.notna(caracteres_corruptos) and caracteres_corruptos > 0:
            problemas.append(
                f"{fila['variable']}: {int(caracteres_corruptos)} valores con caracteres "
                "corruptos (posible problema de codificación/encoding)"
            )

    # -------------------------------------------------------------
    # Nuevo: patrones de formato heterogéneos (ej. DISTRITO con varios
    # esquemas: "NN-NN-NNNN" vs "NN-NNN" vs "NN-NN-NNNN" con "99")
    # -------------------------------------------------------------
    if patrones_df is not None:
        for _, fila in patrones_df.iterrows():
            if fila["cantidad_patrones_distintos"] > 1:
                problemas.append(
                    f"{fila['variable']}: {fila['cantidad_patrones_distintos']} patrones de "
                    f"formato distintos ({fila['valores_con_patron_distinto']} valores no "
                    "siguen el patrón más común)"
                )

    # -------------------------------------------------------------
    # Nuevo: categorías escritas de diferentes maneras
    # -------------------------------------------------------------
    if categorias_df is not None:
        for _, fila in categorias_df.iterrows():
            problemas.append(
                f"{fila['variable']}: {fila['grupos_con_variantes']} categorías con posibles "
                "variantes de escritura"
            )

    if not problemas:
        problemas.append("No se detectaron problemas evidentes con las reglas actuales.")

    return problemas


def generar_diagnostico(dataframe: pd.DataFrame) -> dict:
    """Corre los incisos a-h y devuelve todo en un diccionario."""
    faltantes_df = valores_faltantes(dataframe)
    cantidad_duplicados, ejemplos_duplicados = duplicados_exactos(dataframe)
    fuera_dominio_df = valores_fuera_dominio(dataframe)
    formato_df = formatos_inconsistentes(dataframe)
    # ------------------------------------------------------------------
    # Nuevo: patrones de formato heterogéneos y categorías con variantes
    # ------------------------------------------------------------------
    patrones_df = patrones_formato(dataframe)
    categorias_df = categorias_similares(dataframe)

    return {
        "registros_variables": num_registros_variables(dataframe),
        "tipos_dato": tipos_dato(dataframe),
        "faltantes": faltantes_df,
        "valores_unicos": valores_unicos(dataframe),
        "duplicados_cantidad": cantidad_duplicados,
        "duplicados_ejemplos": ejemplos_duplicados,
        "fuera_dominio": fuera_dominio_df,
        "formato_inconsistente": formato_df,
        "patrones_formato": patrones_df,
        "categorias_similares": categorias_df,
        "problemas_potenciales": problemas_potenciales(
            faltantes_df, cantidad_duplicados, fuera_dominio_df, formato_df, patrones_df, categorias_df
        ),
    }


def exportar_reporte(resultado: dict, ruta_reporte: Path = RUTA_REPORTE) -> None:
    """Aplana el diagnóstico a una sola tabla larga (variable/metrica/valor) y la exporta."""
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)

    filas = []

    for _, fila in resultado["registros_variables"].iterrows():
        filas.append({"seccion": "a_registros_variables", "variable": "", "metrica": fila["metrica"], "valor": fila["valor"]})

    for _, fila in resultado["tipos_dato"].iterrows():
        filas.append({"seccion": "b_tipo_dato", "variable": fila["variable"], "metrica": "tipo_dato", "valor": fila["tipo_dato"]})

    for _, fila in resultado["faltantes"].iterrows():
        filas.append({"seccion": "c_faltantes", "variable": fila["variable"], "metrica": "faltantes", "valor": fila["faltantes"]})
        filas.append({"seccion": "c_faltantes", "variable": fila["variable"], "metrica": "porcentaje_faltantes", "valor": fila["porcentaje_faltantes"]})

    for _, fila in resultado["valores_unicos"].iterrows():
        filas.append({"seccion": "d_valores_unicos", "variable": fila["variable"], "metrica": "valores_unicos", "valor": fila["valores_unicos"]})

    filas.append({"seccion": "e_duplicados_exactos", "variable": "", "metrica": "duplicados_exactos", "valor": resultado["duplicados_cantidad"]})

    for _, fila in resultado["fuera_dominio"].iterrows():
        filas.append({"seccion": "f_fuera_dominio", "variable": fila["variable"], "metrica": "valores_invalidos", "valor": fila["valores_invalidos"]})
        # -------------------------------------------------------------
        # Corregido: antes se calculaba "ejemplos" en valores_fuera_dominio()
        # pero nunca se exportaba al CSV, así que se sabía CUÁNTOS valores
        # inválidos había pero no CUÁLES.
        # -------------------------------------------------------------
        if fila.get("ejemplos"):
            filas.append({"seccion": "f_fuera_dominio", "variable": fila["variable"], "metrica": "ejemplos", "valor": fila["ejemplos"]})

    for _, fila in resultado["formato_inconsistente"].iterrows():
        for metrica in ("espacios_borde", "espacios_multiples", "caracteres_corruptos", "con_letras"):
            if metrica in fila and pd.notna(fila[metrica]):
                filas.append({"seccion": "g_formato_inconsistente", "variable": fila["variable"], "metrica": metrica, "valor": fila[metrica]})
        for metrica in ("ejemplos_corruptos",):
            if metrica in fila and fila.get(metrica):
                filas.append({"seccion": "g_formato_inconsistente", "variable": fila["variable"], "metrica": metrica, "valor": fila[metrica]})

    # ----------------------------------------------------------------
    # Nuevo: patrones de formato heterogéneos (ej. DISTRITO)
    # ----------------------------------------------------------------
    for _, fila in resultado["patrones_formato"].iterrows():
        filas.append({"seccion": "g_patrones_formato", "variable": fila["variable"], "metrica": "cantidad_patrones_distintos", "valor": fila["cantidad_patrones_distintos"]})
        filas.append({"seccion": "g_patrones_formato", "variable": fila["variable"], "metrica": "patron_mas_comun", "valor": fila["patron_mas_comun"]})
        filas.append({"seccion": "g_patrones_formato", "variable": fila["variable"], "metrica": "ejemplos_patron_distinto", "valor": fila["ejemplos_patron_distinto"]})

    # ----------------------------------------------------------------
    # Nuevo: categorías con variantes de escritura
    # ----------------------------------------------------------------
    for _, fila in resultado["categorias_similares"].iterrows():
        filas.append({"seccion": "f_categorias_similares", "variable": fila["variable"], "metrica": "grupos_con_variantes", "valor": fila["grupos_con_variantes"]})
        filas.append({"seccion": "f_categorias_similares", "variable": fila["variable"], "metrica": "ejemplos", "valor": fila["ejemplos"]})

    for indice, problema in enumerate(resultado["problemas_potenciales"], start=1):
        filas.append({"seccion": "h_problemas_potenciales", "variable": "", "metrica": f"problema_{indice}", "valor": problema})

    pd.DataFrame(filas).to_csv(ruta_reporte, index=False, encoding="utf-8-sig")


def main() -> None:
    dataframe = cargar_datos()

    print(f"Diagnóstico sobre: {RUTA_DATOS.resolve()}")
    print()

    print("a. Número de registros y variables")
    print(num_registros_variables(dataframe).to_string(index=False))
    print()

    print("b. Tipo de dato de cada variable")
    print(tipos_dato(dataframe).to_string(index=False))
    print()

    print("c. Cantidad y porcentaje de valores faltantes por variable")
    faltantes_df = valores_faltantes(dataframe)
    print(faltantes_df.to_string(index=False))
    print()

    print("d. Cantidad de valores únicos")
    print(valores_unicos(dataframe).to_string(index=False))
    print()

    print("e. Cantidad de registros duplicados exactos")
    cantidad_duplicados, ejemplos_duplicados = duplicados_exactos(dataframe)
    print(f"Duplicados exactos: {cantidad_duplicados}")
    if cantidad_duplicados:
        print(ejemplos_duplicados.to_string(index=False))
    print()

    print("f. Variables con valores fuera de dominio o inconsistentes")
    fuera_dominio_df = valores_fuera_dominio(dataframe)
    print(fuera_dominio_df.to_string(index=False))
    print()

    print("g. Variables con formatos inconsistentes")
    formato_df = formatos_inconsistentes(dataframe)
    print(formato_df.to_string(index=False))
    print()

    # ------------------------------------------------------------------
    # Nuevo: patrones de formato heterogéneos y categorías con variantes
    # ------------------------------------------------------------------
    print("g (extra). Patrones de formato heterogéneos por columna (ej. DISTRITO)")
    patrones_df = patrones_formato(dataframe)
    print(patrones_df.to_string(index=False) if not patrones_df.empty else "Sin hallazgos.")
    print()

    print("f/g (extra). Categorías con posibles variantes de escritura")
    categorias_df = categorias_similares(dataframe)
    print(categorias_df.to_string(index=False) if not categorias_df.empty else "Sin hallazgos.")
    print()

    print("h. Identificación de problemas potenciales de calidad de datos")
    problemas = problemas_potenciales(
        faltantes_df, cantidad_duplicados, fuera_dominio_df, formato_df, patrones_df, categorias_df
    )
    for problema in problemas:
        print(f"- {problema}")
    print()

    resultado = generar_diagnostico(dataframe)
    exportar_reporte(resultado)
    print(f"Reporte exportado: {RUTA_REPORTE.resolve()}")


if __name__ == "__main__":
    main()