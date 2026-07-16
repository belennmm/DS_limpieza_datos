from pathlib import Path
from io import StringIO
import re
import pandas as pd


CARPETA_ENTRADA = Path("data/csv_originales" )
CARPETA_SALIDA = Path("data/raw")
RUTA_CAMBIOS = Path("docs/data_prep.csv" )

ENCABEZADOS_REQUERIDOS ={
    "CODIGO",
    "DISTRITO" ,
    "DEPARTAMENTO",
    "MUNICIPIO" ,
    "ESTABLECIMIENTO",
    "DIRECCION",
    "TELEFONO",
    "NIVEL" ,
    "SECTOR" ,
}


def text_codif(ruta: Path ) -> tuple[str, str] :

    codificaciones = [
        "utf-8-sig",
        "utf-8" ,
        "cp1252" ,
        "latin-1" ,
    ]


    for codificacion in codificaciones:
        try:
            contenido = ruta.read_text(encoding=codificacion)
            if "CODIGO" in contenido.upper(): return contenido, codificacion
        except UnicodeDecodeError: continue

    raise UnicodeError(f"No se pudo {ruta.name}.")


def locate_encabezado(lineas: list[str]) -> int:
    
    for indice, linea in enumerate(lineas):
        texto = linea.upper()
        contiene_columnas_clave = (
            "CODIGO" in texto
            and "DISTRITO" in texto
            and "DEPARTAMENTO" in texto
            and "MUNICIPIO" in texto
            and "ESTABLECIMIENTO" in texto
        )

        if contiene_columnas_clave: return indice

    raise ValueError("No está el encabezado.")


def normalizar_nombrecolumn(nombre: object) -> str :
    name_limpio = str(nombre).strip().upper()
    name_limpio = re.sub(r"\s+", "_", name_limpio )
    return name_limpio



def nuevo_archivo(ruta_csv: Path ) -> tuple[ pd.DataFrame, dict]:
    """solo la tabla con data """
    contenido, codificacion = text_codif(ruta_csv )
    lineas = contenido.splitlines( )

    indice_encabezado = locate_encabezado(lineas)

    content = "\n".join(lineas[indice_encabezado:])

    dataframe = pd.read_csv(
        StringIO(content) ,
        sep=";",
        dtype="string" ,
        engine="python" ,
    )

    columns_originales = dataframe.columns.tolist()
    cantidad_filas_originales = dataframe.shape[0 ]

    patron_codigo = r"^\d{2}-\d{2}-\d{4}-\d{2}$"

    filas_validas = (
        dataframe["CODIGO"]
        .astype("string")
        .str.strip()
        .str.match(patron_codigo, na=False)
    )

    filas_eliminadas = int((~filas_validas).sum())






    dataframe = dataframe.loc[filas_validas].copy()

    columns_sinnombre = [
        columna
        for columna in dataframe.columns
        if str(columna).strip().lower().startswith("unnamed" )
    ]

    dataframe = dataframe.drop(
        columns=columns_sinnombre,
        errors="ignore" ,
    )


    dataframe.columns = [
        normalizar_nombrecolumn(columna)
        for columna in dataframe.columns 
    ]

    columns_faltantes = sorted(ENCABEZADOS_REQUERIDOS - set( dataframe.columns) )

    metadatos = {
        "archivo_origen": ruta_csv.name,
        "codificacion_utilizada": codificacion,
        "lineas_anteriores_omitidas": indice_encabezado,

        "filas_originales_desde_encabezado": cantidad_filas_originales  ,
        "filas_eliminadas": filas_eliminadas,
        "filas_datos": dataframe.shape[0 ],
        "columnas_originales": len(columns_originales ) ,
        "columnas_finales": dataframe.shape[ 1] ,
        "columnas_sin_nombre_eliminadas":  ", ".join(map(str, columns_sinnombre) ),
        "columnas_requeridas_faltantes":  ", ".join(columns_faltantes),


        "estado": (
            "Correcto"
            if not columns_faltantes
            else "ver columnas"
        ) ,
    }

    return dataframe, metadatos


def new_export(
    ruta_salida: Path,
    dimensiones_esperadas: tuple[int, int],

) -> None:
    """confirmar aca"""
    verificacion = pd.read_csv(
        ruta_salida,
        dtype="string",
        encoding="utf-8-sig",
    )

    if verificacion.shape != dimensiones_esperadas:
        raise ValueError(
            f"lo que se espera: {dimensiones_esperadas} ; "
            f"output obtenido: {verificacion.shape}."
        )


def main() -> None:
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    RUTA_CAMBIOS.parent.mkdir(parents=True, exist_ok=True)

    archivos_csv = sorted(CARPETA_ENTRADA.glob("*.csv"))

    if not archivos_csv:raise FileNotFoundError( f" no el CSV en {CARPETA_ENTRADA.resolve()}" )

    print(f"encontrados: {len(archivos_csv)}")
    print()

    cambios = []

    for ruta_csv in archivos_csv:
        try:
            dataframe, metadatos = nuevo_archivo(ruta_csv)

            nombre_base = (ruta_csv.stem .replace(" ", "_") .replace("(", "").replace(")", "") )

            nombre_salida = f"{nombre_base}_new.csv"

            ruta_salida = CARPETA_SALIDA / nombre_salida

            dataframe.to_csv(
                ruta_salida,
                index=False,
                encoding="utf-8-sig",
            )

            new_export( ruta_salida, dataframe.shape, )

            metadatos["archivo_generado"] = nombre_salida
            cambios.append(metadatos)

            print(
                f"[Todo bien] {ruta_csv.name } -- {nombre_salida} | "
                f"{dataframe.shape[0]} filas, "
                f"{ dataframe.shape[1  ]} columnas |  "
                f"{ metadatos['lineas_anteriores_omitidas'] } "
            )



        except Exception as error:
            cambios.append(
                {
                    "archivo_origen": ruta_csv.name,
                    "archivo_generado": "",
                    "codificacion_utilizada": "",
                    "lineas_anteriores_omitidas": "",
                    "filas_originales_desde_encabezado": "",
                    "filas_eliminadas": "",
                    "filas_datos": "",
                    "columnas_originales": "",
                    "columnas_finales": "",
                    "columnas_sin_nombre_eliminadas": "",
                    "columnas_requeridas_faltantes": "",
                    "estado": f"Error: {error}",
                }
            )

            print(f"error {ruta_csv.name}: {error}")

    df_cambios = pd.DataFrame(cambios)

    df_cambios.to_csv(
        RUTA_CAMBIOS,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(f"nuevos: {RUTA_CAMBIOS.resolve()}")


if __name__ == "__main__":main()