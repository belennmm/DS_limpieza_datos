from pathlib import Path
import pandas as pd


INPUT = Path("data/interim/establecimientos_todos_raw.csv" )
CARPETA_REPORTS = Path("reports/diagnostico_inicial" )

GENERAL = CARPETA_REPORTS / "resumen_general.csv"
VARIABLES =CARPETA_REPORTS / "resumen_variables.csv"
DUPLICADOS = CARPETA_REPORTS / "duplicados_exactos.csv"
MISSING =CARPETA_REPORTS /  "marcadores_ausencia.csv"
FORMATOS =CARPETA_REPORTS / "problemas_formato.csv"
DOMINIOS = CARPETA_REPORTS /  "valores_fuera_dominio.csv"
CATEGORIAS =  CARPETA_REPORTS / "categorias_observadas.csv"


MISSING_VALUES = {
    "",
    "N/A" ,
    "NA",
    "NULL",
    "NONE",
    "NAN",
    "-",
    ".",
    "--",
    "SIN DATO", "SIN INFORMACION", "SIN INFORMACIÓN",
    "NO APLICA",
}


DEPARTAMENTOS = {
    "ALTA VERAPAZ" ,
    "BAJA VERAPAZ",
    "CHIMALTENANGO",
    "CHIQUIMULA" ,
    "EL PROGRESO",
    "ESCUINTLA",
    "GUATEMALA",
    "HUEHUETENANGO",
    "IZABAL"  ,
    "JALAPA",
    "JUTIAPA",
    "PETEN",
    "QUETZALTENANGO" ,
    "QUICHE",
    "RETALHULEU",
    "SACATEPEQUEZ",
    "SAN MARCOS",
    "SANTA ROSA",
    "SOLOLA",
    "SUCHITEPEQUEZ"  ,
    "TOTONICAPAN",
    "ZACAPA",
    "CIUDAD CAPITAL",
}


COLUMNAS_CATEGORY = [
    "DEPARTAMENTO",
    "MUNICIPIO",
    "NIVEL" ,
    "SECTOR" ,
    "AREA",
    "STATUS" ,
    "MODALIDAD",
    "JORNADA",
    "PLAN" ,
]


def load_data() -> pd.DataFrame:

    if not INPUT.exists():raise FileNotFoundError( f"no está el archivo en {INPUT.resolve()}" )

    dataframe = pd.read_csv(
        INPUT,
        dtype="string",
        encoding="utf-8-sig" ,
    )

    return dataframe



def resumen_general(dataframe: pd.DataFrame, columnasdata: list[str]) -> None:

    duplicados = dataframe.duplicated(subset=columnasdata, keep=False )

    cantidad_missing = int(dataframe[columnasdata]. isna().sum().sum() )


    total_celdas = dataframe.shape[0] * len(columnasdata)

    porcentaje_missing = cantidad_missing / total_celdas *  100 if total_celdas > 0   else 0

    filas_duplicadas = int(duplicados.sum())

    if filas_duplicadas > 0:
        grupos_duplicados = int( dataframe.loc[duplicados ]
            .groupby(columnasdata , dropna=False)
            .ngroups
        )
    else: grupos_duplicados =0

    resumen = pd.DataFrame([
        {"metrica": "registros", "valor": dataframe.shape[0] },
        {"metrica": "variables_originales", "valor": len(columnasdata) },
        {"metrica": "variables_totales_con_origen", "valor": dataframe.shape[1] },
        {"metrica": "valores_faltantes", "valor": cantidad_missing } ,


        {"metrica": "porcentaje_faltantes", "valor": round(porcentaje_missing , 4) },
        {"metrica": "variables_con_faltantes", "valor": int((dataframe[columnasdata].isna().sum() > 0).sum()) },
        {"metrica": "filas_duplicadas_exactas", "valor": filas_duplicadas },
        {"metrica": "grupos_duplicados_exactos", "valor": grupos_duplicados } ,
    ])

    resumen.to_csv(
        GENERAL,
        index=False ,
        encoding="utf-8-sig",
    )



def resumen_variables(dataframe: pd.DataFrame) -> None:

    totalfilas = len(dataframe)
    resumen = [ ]

    for columna in dataframe.columns:

        missing = int(dataframe[columna].isna().sum())
        porcentaje = missing / totalfilas *   100 if totalfilas > 0 else 0

        resumen.append( {
            "variable": columna,
            "tipo_detectado": str(dataframe[columna].dtype) ,
            "registros": totalfilas,
            "valores_faltantes": missing,
            "porcentaje_faltantes": round(porcentaje , 4 ),
            "valores_no_faltantes": int(dataframe[columna].notna().sum()),
            "valores_unicos_sin_na": int(dataframe[columna].nunique(dropna=True) ) ,
            "valores_unicos_con_na": int(dataframe[columna].nunique(dropna=False)),
        })

    pd.DataFrame(resumen).to_csv(
        VARIABLES,
        index = False ,
        encoding="utf-8-sig",
    )



def check_duplicados(dataframe: pd.DataFrame , columnasdata: list[str]) -> None:

    mask = dataframe.duplicated(subset=columnasdata , keep=False)

    repetidos = dataframe.loc[mask].copy()

    if not repetidos.empty:
        repetidos.insert(0 , "indice_original", repetidos.index)
        repetidos = repetidos.sort_values(columnasdata)

    repetidos.to_csv(
        DUPLICADOS ,
        index=False,
        encoding="utf-8-sig",
    )



def check_missing(dataframe: pd.DataFrame) -> None:

    resultados = []

    for columna in dataframe.columns:

        valores = dataframe[columna].dropna().astype("string").str.strip().str.upper()
        conteos = valores.value_counts()

        for marcador in MISSING_VALUES:

            cantidad = int(conteos.get(marcador , 0))

            if cantidad > 0: resultados.append( { "variable": columna , "marcador": marcador,"cantidad": cantidad, })

    pd.DataFrame(
        resultados,
        columns=["variable", "marcador", "cantidad"]
    ).to_csv(
        MISSING,
        index = False,
        encoding="utf-8-sig",
    )



def check_formatos(dataframe: pd.DataFrame) -> None:

    resultados = []

    for columna in dataframe.columns:

        serie = dataframe[columna].dropna().astype("string")

        espaciosafuera = serie.ne(serie.str.strip())
        espaciosdobles = serie.str.contains(r"\s{2,}", regex=True , na=False)
        invisibles = serie.str.contains(r"[\t\r\n]", regex=True , na=False)

        problemas = {
            "espacios_inicio_o_final": int(espaciosafuera.sum()),
            "espacios_multiples": int(espaciosdobles.sum()),
            "tabulaciones_o_saltos": int(invisibles.sum()),
        }

        for problema , cantidad in problemas.items():

            if cantidad > 0:
                resultados.append({
                    "variable": columna,
                    "problema": problema,
                    "cantidad": cantidad,
                })


    if "CODIGO" in dataframe.columns:

        codigomalo = ~dataframe["CODIGO"].astype("string").str.strip().str.match(
            r"^\d{2}-\d{2}-\d{4}-\d{2}$",
            na = False,
        )

        resultados.append({
            "variable": "CODIGO",
            "problema": "formato_codigo_invalido",
            "cantidad": int(codigomalo.sum()),
        })


    if "TELEFONO" in dataframe.columns:

        telefonos = dataframe["TELEFONO"].dropna().astype("string").str.strip()

        ocho_digitos = telefonos.str.match(r"^\d{8}$", na = False)

        resultados.append({
            "variable": "TELEFONO",
            "problema": "telefono_no_tiene_8_digitos",
            "cantidad": int((~ocho_digitos).sum()),
        })

        letras = telefonos.str.contains(
            r"[A-Za-zÁÉÍÓÚÑáéíóúñ]",
            regex=True,
            na = False,
        )

        resultados.append({
            "variable": "TELEFONO",
            "problema": "telefono_con_letras",
            "cantidad": int(letras.sum()),
        })


    pd.DataFrame(
        resultados,
        columns=["variable", "problema", "cantidad"]
    ).to_csv(
        FORMATOS,
        index = False,
        encoding="utf-8-sig",
    )



def check_dominios(dataframe: pd.DataFrame) -> None:

    resultados = []

    if "DEPARTAMENTO" in dataframe.columns:

        departamentosdata = dataframe["DEPARTAMENTO"].dropna().astype("string").str.strip().str.upper()
        invalidos= departamentosdata[~departamentosdata.isin(DEPARTAMENTOS )]

        for valor , cantidad in invalidos.value_counts().items():

            resultados.append({
                "variable": "DEPARTAMENTO",
                "valor": valor,
                "cantidad": int(cantidad),
                "problema": "departamento_fuera_del_dominio",
            })


    if "NIVEL" in dataframe.columns:

        niveles = dataframe["NIVEL"].dropna().astype("string").str.strip().str.upper()
        nivelesmalos = niveles[niveles != "DIVERSIFICADO"]

        for valor , cantidad in nivelesmalos.value_counts().items():

            resultados.append({
                "variable": "NIVEL",
                "valor": valor,
                "cantidad": int(cantidad),
                "problema": "nivel_distinto_de_diversificado" ,
            })


    pd.DataFrame(
        resultados,
        columns=["variable", "valor", "cantidad", "problema"]
    ).to_csv(
        DOMINIOS,
        index = False,
        encoding="utf-8-sig",
    )





def save_categorias(dataframe: pd.DataFrame) -> None:

    resultados = []

    for columna in COLUMNAS_CATEGORY:

        if columna not in dataframe.columns:continue

        conteos = dataframe[columna].value_counts(dropna=False)

        for valor , cantidad in conteos.items():

            resultados.append({
                "variable": columna,
                "valor": "<NA>" if pd.isna(valor) else valor,
                "cantidad": int(cantidad),
            })

    pd.DataFrame(resultados).to_csv(
        CATEGORIAS,
        index=False,
        encoding="utf-8-sig",
    )



def main() -> None:

    CARPETA_REPORTS.mkdir(parents=True , exist_ok=True)

    dataframe = load_data()

    columnasdata = [ columna for columna in dataframe.columns  if columna.lower() != "origen" ]

    resumen_general(dataframe , columnasdata)
    resumen_variables(dataframe)
    check_duplicados(dataframe , columnasdata)
    check_missing(dataframe)
    check_formatos(dataframe)
    check_dominios(dataframe)
    save_categorias(dataframe)

    print("diagnóstico inicial done" )
    print(f"registros: {dataframe.shape[0 ]}" )
    print(f"variables: {dataframe.shape[1] }" )
    print(f"reports en: {CARPETA_REPORTS.resolve()}")


if __name__ == "__main__":  main()