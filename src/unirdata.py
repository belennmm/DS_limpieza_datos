from pathlib import Path
import pandas as pd

CARPETA_ENTRADA = Path("data/raw")
CARPETA_SALIDA = Path("data/interim")

OUTPUT = CARPETA_SALIDA / "establecimientos_todos_raw.csv"
DETAIL = Path("docs/detail_union.csv" )


def load_archivo(ruta_csv: Path  ) -> pd.DataFrame:

    dataframe = pd.read_csv(
        ruta_csv,
        dtype="string",
        encoding="utf-8-sig" ,
    )

    dataframe["origen"] = ruta_csv.name

    return dataframe


def main() -> None:

    CARPETA_SALIDA.mkdir(parents=True , exist_ok = True)
    DETAIL.parent.mkdir(parents= True, exist_ok = True )
    archivos_csv = sorted(CARPETA_ENTRADA.glob("*.csv"))

    if not archivos_csv:raise FileNotFoundError(  f"no hay data en{CARPETA_ENTRADA.resolve( ) }")

    dataframes = []
    resumen = []
    columnas_referencia = None

    for ruta_csv in archivos_csv:
        dataframe = load_archivo(ruta_csv)

        columnasactual = dataframe.columns.drop("origen").tolist()

        if columnas_referencia is None: columnas_referencia = columnasactual

        buenaestructura = columnasactual == columnas_referencia

        resumen.append({"archivo": ruta_csv.name  , "filas" : dataframe.shape[ 0],  "columnas_datos" : len(columnasactual),"estructura_correcta": buenaestructura ,} )

        if not buenaestructura:raise ValueError(f"{ruta_csv.name} tiene otra estructura ")

        dataframes.append(dataframe)

    data_unido = pd.concat( dataframes, ignore_index=True, )



    data_unido.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    verificacion = pd.read_csv(
        OUTPUT,
        dtype="string",
        encoding="utf-8-sig",
    )

    if verificacion.shape != data_unido.shape:
        raise ValueError(
            f"Las dimensiones cambiaron al exportar. "
            f"Esperado: {data_unido.shape}; "
            f"obtenido: {verificacion.shape}."
        )

    df_resumen = pd.DataFrame(resumen)

    df_resumen.to_csv(
        DETAIL,
        index=False,
        encoding="utf-8-sig",
    )



    print(f"se unieron {len(archivos_csv)} archivos")
    print(f"filas: {data_unido.shape[0]}")
    print(f"columas: {data_unido.shape[1]}")
    print(f"nuevo output: {OUTPUT.resolve()}")
    print(f"resumen del detalle: {DETAIL.resolve()}")


if __name__ == "__main__":  main()