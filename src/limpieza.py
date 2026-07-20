"""
Limpieza del conjunto de datos unido (parte 5 del pdf)

Aplica sobre data/interim/establecimientos_todos_raw.csv las reglas de
corrección definidas en el Plan de limpieza (parte 4) y crea:
- data/processed/establecimientos_limpio.csv -> dataset limpio final (parte 9)
- docs/registro_transformaciones.csv         -> tabla del punto 6 del pdf
- docs/informe_calidad.csv                   -> tabla comparativa de la parte 8
- docs/posibles_duplicados_parciales.csv     -> candidatos a duplicado parcial
                                                 para revisión manual (punto 5.g.ii)

No repite el trabajo de limpiarcsvcrudos.py (detección de encabezado/pie de
página del formato original tipo HTML, columnas completamente vacías, y
filtrado de CODIGO) ni el de unirdata.py (unión de los archivos por
departamento). Este script parte del CSV ya unido y se enfoca en las
correcciones descritas en el plan.
"""

from pathlib import Path
import re
import pandas as pd

try:
    from rapidfuzz import fuzz, process
except ImportError:  
    fuzz = None
    process = None

import diagnostico
import unirdata

RUTA_ENTRADA = unirdata.OUTPUT
CARPETA_SALIDA = Path("data/processed")
RUTA_SALIDA = CARPETA_SALIDA / "establecimientos_limpio.csv"
RUTA_REGISTRO_TRANSFORMACIONES = Path("docs/registro_transformaciones.csv")
RUTA_INFORME_CALIDAD = Path("docs/informe_calidad.csv")
RUTA_DUPLICADOS_PARCIALES = Path("docs/posibles_duplicados_parciales.csv")

PLACEHOLDER = "DESCONOCIDO"
UMBRAL_DUPLICADO_PARCIAL = 95  # score de similitud (0-100) de rapidfuzz. Se decidió por 95 porque con 90 todavía sacaba bastantes que no eran iguales

PATRON_BASURA = diagnostico.PATRON_BASURA
PATRON_TELEFONO = diagnostico.PATRON_TELEFONO
PATRON_ZONA = re.compile(r"^ZONA\s+\d+$", re.IGNORECASE)



def _es_texto_basura(valor) -> bool:
    """Solo símbolos/espacios/puntos/guiones, o el dígito '0' solo, usado
    como relleno en vez de un nombre real (ver DIRECTOR y SUPERVISOR)."""
    if pd.isna(valor):
        return False
    texto = str(valor).strip()
    if texto == "":
        return False
    return bool(PATRON_BASURA.match(texto)) or texto == "0"


def _nuevo_registro(variable, problema, transformacion, afectados, justificacion) -> dict:
    return {
        "variable": variable,
        "problema_detectado": problema,
        "transformacion": transformacion,
        "registros_afectados": afectados,
        "justificacion": justificacion,
    }


# Transformaciones (una función por variable, según el Plan de limpieza ; parte 4)
def limpiar_director(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    columna = "DIRECTOR"
    serie = df[columna].astype("string")

    mascara_faltante = serie.isna()
    mascara_basura = serie.apply(_es_texto_basura)
    mascara_total = mascara_faltante | mascara_basura

    df.loc[mascara_total, columna] = PLACEHOLDER
    registro.append(_nuevo_registro(
        columna,
        f"{int(mascara_faltante.sum())} valores faltantes (~14% del total) y "
        f"{int(mascara_basura.sum())} valores sin información real (solo símbolos, guiones o '0')",
        f"Se reemplazaron por el placeholder '{PLACEHOLDER}'",
        int(mascara_total.sum()),
        "El nombre del director no es relevante para el análisis agregado; eliminar las filas "
        "perdería ~14% de los datos. El placeholder evita dejar el campo vacío sin inventar "
        "información.",
    ))
    return df


def limpiar_telefono(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    columna = "TELEFONO"
    serie = df[columna].astype("string")

    mascara_faltante = serie.isna()
    mascara_invalida = serie.notna() & ~serie.str.match(PATRON_TELEFONO, na=False)
    mascara_total = mascara_faltante | mascara_invalida

    df.loc[mascara_total, columna] = PLACEHOLDER

    registro.append(_nuevo_registro(
        columna,
        f"{int(mascara_faltante.sum())} valores faltantes y {int(mascara_invalida.sum())} con "
        f"formato distinto al esperado (8 dígitos): varios números separados por guion, letras, "
        f"longitudes distintas, etc.",
        f"Se reemplazaron por el placeholder '{PLACEHOLDER}'",
        int(mascara_total.sum()),
        "El teléfono no se usa para análisis o predicción determinante en este proyecto; "
        "estandarizarlo con un placeholder evita perder registros completos por este campo.",
    ))
    return df


def limpiar_supervisor(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    columna = "SUPERVISOR"
    serie = df[columna].astype("string")

    # 1. Error de escritura puntual: "0" en vez de "O" (ej. "ACEVED0")
    mascara_typo = serie.str.contains(r"[A-Za-zÀ-ÿ]0(?![0-9])", regex=True, na=False)
    afectados_typo = int(mascara_typo.sum())
    df.loc[mascara_typo, columna] = serie.loc[mascara_typo].str.replace(
        r"(?<=[A-Za-zÀ-ÿ])0(?![0-9])", "O", regex=True
    )

    # 2. Valores basura (ej. solo guiones) -> placeholder
    serie_actualizada = df[columna].astype("string")
    mascara_basura = serie_actualizada.apply(_es_texto_basura)
    afectados_basura = int(mascara_basura.sum())
    df.loc[mascara_basura, columna] = PLACEHOLDER

    registro.append(_nuevo_registro(
        columna,
        "2 valores inválidos detectados en el diagnóstico: 1 compuesto solo por guiones/texto sin "
        "sentido, 1 nombre con error de escritura ('0' en vez de 'O')",
        f"El registro de guiones se reemplazó por '{PLACEHOLDER}'; el error de escritura se "
        f"corrigió reemplazando el '0' por 'O'",
        afectados_typo + afectados_basura,
        "Son casos puntuales (2 registros); no representan pérdida de información relevante.",
    ))
    return df


def limpiar_municipio(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    columna = "MUNICIPIO"
    serie = df[columna].astype("string").str.strip()
    mascara_zona = serie.str.match(PATRON_ZONA, na=False)
    afectados = int(mascara_zona.sum())

    df.loc[mascara_zona, columna] = "GUATEMALA"

    registro.append(_nuevo_registro(
        columna,
        f"{afectados} valores no correspondían a un municipio sino a una zona específica de la "
        f"ciudad (ej. 'ZONA 1', 'ZONA 10')",
        "Se reemplazaron por 'GUATEMALA', ya que esas zonas pertenecen al municipio de Guatemala",
        afectados,
        "El municipio es la unidad geográfica relevante para este análisis; se pierde el detalle "
        "de zona específica dentro de la ciudad, pero no la validez del análisis por municipio.",
    ))
    return df


def limpiar_departamento(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    columna = "DEPARTAMENTO"
    serie = df[columna].astype("string").str.strip().str.upper()
    mascara = serie == "CIUDAD CAPITAL"
    afectados = int(mascara.sum())

    df.loc[mascara, columna] = "GUATEMALA"

    registro.append(_nuevo_registro(
        columna,
        f"{afectados} registro(s) con el valor 'CIUDAD CAPITAL', que no pertenece al catálogo "
        f"oficial de departamentos",
        "Se corrigió al valor 'GUATEMALA'",
        afectados,
        "'Ciudad capital' se refiere al departamento de Guatemala; no existe como departamento "
        "propio en el catálogo oficial.",
    ))
    return df


def documentar_distrito_sin_cambios(registro: list[dict]) -> None:
    """DISTRITO no se corrige: solo se documenta la decisión, según el plan."""
    registro.append(_nuevo_registro(
        "DISTRITO",
        "3 patrones de formato distintos (ej. 'AA-AA-AAAA' vs 'AA-AAA'); 5109 valores no siguen "
        "el patrón más común",
        "Ninguna",
        0,
        "Es un código administrativo identificador; las variaciones de formato no afectan su "
        "validez mientras siga cumpliendo su función de identificador.",
    ))


def documentar_variables_sin_problemas(registro: list[dict]) -> None:
    """Variables donde el diagnóstico no encontró problemas (según el plan)."""
    sin_problemas = [
        "DIRECCION", "ESTABLECIMIENTO", "CODIGO", "STATUS", "DEPARTAMENTAL",
        "PLAN", "JORNADA", "MODALIDAD", "NIVEL", "AREA", "SECTOR",
    ]
    for columna in sin_problemas:
        registro.append(_nuevo_registro(columna, "Ninguno", "", 0, ""))


def normalizar_espacios(df: pd.DataFrame, registro: list[dict]) -> pd.DataFrame:
    """Trim + colapso de espacios múltiples en todas las columnas de texto.

    No estaba en el plan como punto propio, pero es necesario para cumplir
    el punto 5.c del PDF (normalización de texto) y para la prueba
    automática del punto 7 ("no existan espacios al inicio o final de
    textos"). El propio diagnóstico ya había detectado 4 casos de espacios
    múltiples en SUPERVISOR.
    """
    columnas_texto = [columna for columna in df.columns if df[columna].dtype == "string"]
    total_afectados = 0
    for columna in columnas_texto:
        serie = df[columna]
        no_nulos = serie.notna()
        limpio = serie.copy()
        limpio.loc[no_nulos] = (
            serie.loc[no_nulos].str.strip().str.replace(r"\s{2,}", " ", regex=True)
        )
        afectados = int(((limpio != serie) & no_nulos).sum())
        total_afectados += afectados
        df[columna] = limpio

    registro.append(_nuevo_registro(
        "todas las columnas de texto",
        "Espacios al inicio/final y espacios múltiples internos",
        "Se aplicó strip() y colapso de espacios internos a un solo espacio",
        total_afectados,
        "Estandariza el texto sin alterar el contenido semántico de los valores.",
    ))
    return df


# ---------------------------------------------------------------------
# Duplicados parciales (punto 5.g.ii): solo detección, sin fusión automática
# ---------------------------------------------------------------------

# Columnas que, si difieren entre dos registros con nombre/dirección
# parecidos, indican que en realidad son dos inscripciones legítimas y
# distintas del mismo establecimiento ante el MINEDUC (ej. el mismo
# colegio ofreciendo jornada matutina Y fin de semana, o el mismo colegio
# re-registrado con otro director/status tras un cambio administrativo; ambos casos cuentan como dos instituciones distintas),
# no un duplicado. 
# Probando, se detectó revisando manualmente candidatos: las columnas que más cambian entre pares "falso positivo" son 
# JORNADA, MODALIDAD, PLAN, DIRECTOR y STATUS.
COLUMNAS_DIFERENCIADORAS = ["JORNADA", "MODALIDAD", "PLAN", "DIRECTOR", "STATUS"]


def detectar_duplicados_parciales(
    df: pd.DataFrame,
    umbral: int = UMBRAL_DUPLICADO_PARCIAL,
    columnas_diferenciadoras: list[str] = COLUMNAS_DIFERENCIADORAS,
) -> pd.DataFrame:
    #Necesita tener rapidfuzz instalado

    if fuzz is None or process is None:
        raise ImportError(
            "Este análisis requiere 'rapidfuzz'. Instálalo con: "
            "pip install rapidfuzz --break-system-packages"
        )

    candidatos = []

    df_valido = df.dropna(subset=["ESTABLECIMIENTO", "DIRECCION"]).copy()
    df_valido["_texto"] = (
        df_valido["ESTABLECIMIENTO"].astype("string").str.upper().str.strip()
        + " | "
        + df_valido["DIRECCION"].astype("string").str.upper().str.strip()
    )

    columnas_contexto = ["CODIGO", "ESTABLECIMIENTO", *columnas_diferenciadoras]

    for (_departamento, _municipio), bloque_original in df_valido.groupby(
        ["DEPARTAMENTO", "MUNICIPIO"], sort=False
    ):
        if bloque_original.shape[0] < 2:
            continue

        bloque = bloque_original.reset_index(drop=True)
        textos = bloque["_texto"].tolist()
        matriz = process.cdist(textos, textos, scorer=fuzz.token_sort_ratio, workers=-1)

        n = len(textos)
        for i in range(n):
            for j in range(i + 1, n):
                score = matriz[i, j]
                if score < umbral:
                    continue

                fila_i = bloque.loc[i]
                fila_j = bloque.loc[j]

                # Descartar si son inscripciones distintas y legítimas
                # (mismo colegio, distinta jornada/modalidad/plan).
                difieren = any(
                    fila_i[columna] != fila_j[columna] for columna in columnas_diferenciadoras
                )
                if difieren:
                    continue

                candidato = {"similitud": round(float(score), 1)}
                for columna in columnas_contexto:
                    candidato[f"{columna.lower()}_1"] = fila_i[columna]
                    candidato[f"{columna.lower()}_2"] = fila_j[columna]
                candidatos.append(candidato)

    columnas_salida = ["similitud"] + [
        f"{columna.lower()}_{sufijo}" for columna in columnas_contexto for sufijo in (1, 2)
    ]
    if not candidatos:
        return pd.DataFrame(columns=columnas_salida)

    resultado = pd.DataFrame(candidatos)[columnas_salida]
    return resultado.sort_values("similitud", ascending=False, ignore_index=True)



# Métricas de calidad (punto 8): antes / después
def _metricas_calidad(df: pd.DataFrame) -> dict:
    faltantes_df = diagnostico.valores_faltantes(df)
    total_faltantes = int(faltantes_df["faltantes"].sum())
    total_celdas = df.shape[0] * df.shape[1]
    porcentaje = round(total_faltantes / total_celdas * 100, 2) if total_celdas else 0.0
    variables_con_na = int((faltantes_df["faltantes"] > 0).sum())

    duplicados_exactos, _ = diagnostico.duplicados_exactos(df)

    formato_df = diagnostico.formatos_inconsistentes(df)
    tiene_formato_malo = (
        (formato_df.get("espacios_borde", 0) > 0)
        | (formato_df.get("espacios_multiples", 0) > 0)
        | (formato_df.get("caracteres_corruptos", 0) > 0)
    )
    variables_formato_inconsistente = int(tiene_formato_malo.sum())

    categorias_df = diagnostico.categorias_similares(df)
    categorias_inconsistentes = (
        int(categorias_df["grupos_con_variantes"].sum()) if not categorias_df.empty else 0
    )

    return {
        "Registros": df.shape[0],
        "Variables": df.shape[1],
        "Valores faltantes": f"{total_faltantes} ({porcentaje}%)",
        "Variables con NA": variables_con_na,
        "Duplicados exactos": duplicados_exactos,
        "Variables con formato inconsistente": variables_formato_inconsistente,
        "Variables con tipo incorrecto": 0,  # todas string por diseño, ver Libro de Códigos
        "Categorías inconsistentes": categorias_inconsistentes,
        "Errores corregidos": 0,  # se completa en main() para "antes" y "después"
    }



# Validación del conjunto limpio (punto 7)
def validar_conjunto_limpio(df: pd.DataFrame) -> list[tuple[str, bool, str]]:
    resultados = []

    duplicados, _ = diagnostico.duplicados_exactos(df)
    resultados.append(("Sin registros duplicados exactos", duplicados == 0, f"encontrados: {duplicados}"))

    columnas_texto = [columna for columna in df.columns if df[columna].dtype == "string"]
    con_espacios_borde = 0
    for columna in columnas_texto:
        serie = df[columna].dropna()
        con_espacios_borde += int((serie != serie.str.strip()).sum())
    resultados.append((
        "Sin espacios al inicio o final de textos",
        con_espacios_borde == 0,
        f"celdas con espacios de borde: {con_espacios_borde}",
    ))

    telefonos = df["TELEFONO"].dropna().astype("string")
    telefonos_validos = telefonos.str.match(PATRON_TELEFONO, na=False) | (telefonos == PLACEHOLDER)
    resultados.append((
        "Teléfonos con formato consistente (8 dígitos o placeholder)",
        bool(telefonos_validos.all()),
        f"inválidos restantes: {int((~telefonos_validos).sum())}",
    ))

    departamentos = df["DEPARTAMENTO"].dropna().astype("string").str.upper().unique()
    fuera_de_catalogo = [d for d in departamentos if d not in diagnostico.DEPARTAMENTOS_VALIDOS]
    resultados.append((
        "Departamentos dentro del catálogo oficial",
        len(fuera_de_catalogo) == 0,
        f"fuera de catálogo: {fuera_de_catalogo}",
    ))

    zonas_restantes = int(
        df["MUNICIPIO"].astype("string").str.match(PATRON_ZONA, na=False).sum()
    )
    resultados.append((
        "Sin valores tipo 'ZONA N' en MUNICIPIO",
        zonas_restantes == 0,
        f"restantes: {zonas_restantes}",
    ))

    tipos_incorrectos = [columna for columna in df.columns if df[columna].dtype != "string"]
    resultados.append((
        "Todas las variables con el tipo de dato esperado (string)",
        len(tipos_incorrectos) == 0,
        f"con otro tipo: {tipos_incorrectos}",
    ))

    tiene_ciudad_capital = bool(
        (df["DEPARTAMENTO"].astype("string").str.upper() == "CIUDAD CAPITAL").any()
    )
    tiene_typo_supervisor = bool(
        df["SUPERVISOR"].astype("string").str.contains(r"[A-Za-zÀ-ÿ]0(?![0-9])", regex=True, na=False).any()
    )
    resultados.append((
        "Sin los valores inválidos detectados en el diagnóstico inicial",
        not tiene_ciudad_capital and not tiene_typo_supervisor,
        f"CIUDAD CAPITAL presente: {tiene_ciudad_capital}; typo tipo 'ACEVED0' presente: {tiene_typo_supervisor}",
    ))

    return resultados


def imprimir_validaciones(resultados: list[tuple[str, bool, str]]) -> bool:
    todo_ok = True
    for nombre, ok, detalle in resultados:
        estado = "OK" if ok else "FALLÓ"
        if not ok:
            todo_ok = False
        print(f"[{estado}] {nombre} -- {detalle}")
    return todo_ok



def limpiar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    registro: list[dict] = []

    df = limpiar_director(df, registro)
    df = limpiar_telefono(df, registro)
    df = limpiar_supervisor(df, registro)
    df = limpiar_municipio(df, registro)
    df = limpiar_departamento(df, registro)
    documentar_distrito_sin_cambios(registro)
    documentar_variables_sin_problemas(registro)
    df = normalizar_espacios(df, registro)

    return df, pd.DataFrame(registro)


def main() -> None:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    RUTA_REGISTRO_TRANSFORMACIONES.parent.mkdir(parents=True, exist_ok=True)

    df_original = diagnostico.cargar_datos(RUTA_ENTRADA)
    metricas_antes = _metricas_calidad(df_original)

    df_limpio, registro_df = limpiar(df_original.copy())
    metricas_despues = _metricas_calidad(df_limpio)
    metricas_despues["Errores corregidos"] = int(registro_df["registros_afectados"].sum())

    df_limpio.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")
    registro_df.to_csv(RUTA_REGISTRO_TRANSFORMACIONES, index=False, encoding="utf-8-sig")

    informe = pd.DataFrame({
        "Métrica": list(metricas_antes.keys()),
        "Antes": list(metricas_antes.values()),
        "Después": [metricas_despues[clave] for clave in metricas_antes.keys()],
    })
    informe.to_csv(RUTA_INFORME_CALIDAD, index=False, encoding="utf-8-sig")

    print(f"Dataset limpio exportado: {RUTA_SALIDA.resolve()}")
    print(f"Registro de transformaciones: {RUTA_REGISTRO_TRANSFORMACIONES.resolve()}")
    print(f"Informe de calidad: {RUTA_INFORME_CALIDAD.resolve()}")
    print()
    print(informe.to_string(index=False))
    print()

    print("Validación del conjunto limpio (punto 7):")
    resultados_validacion = validar_conjunto_limpio(df_limpio)
    imprimir_validaciones(resultados_validacion)
    print()

    print("Buscando posibles duplicados parciales (esto puede tardar unos segundos)...")
    try:
        duplicados_parciales_df = detectar_duplicados_parciales(df_limpio)
        duplicados_parciales_df.to_csv(RUTA_DUPLICADOS_PARCIALES, index=False, encoding="utf-8-sig")
        print(
            f"Candidatos a duplicado parcial encontrados: {duplicados_parciales_df.shape[0]} "
            f"-> {RUTA_DUPLICADOS_PARCIALES.resolve()}"
        )
        print("Son candidatos para revisión manual; no se fusionan automáticamente.")
    except ImportError as error:
        print(f"[Aviso] {error}")


if __name__ == "__main__":
    main()