from pathlib import Path

import pandas as pd


CARPETA_RAW = Path("data/raw")
RUTA_REPORTE = Path("docs/revision_archivos_raw.csv")


def main() -> None:
    archivos = sorted(CARPETA_RAW.glob("*.csv"))

    if not archivos:
        raise FileNotFoundError(
            f"{CARPETA_RAW.resolve()}"
        )

    resultados = []

    for ruta_csv in archivos:
        dataframe = pd.read_csv(
            ruta_csv,
            dtype="string",
            encoding="utf-8-sig",
        )

        if "DEPARTAMENTO" not in dataframe.columns:
            resultados.append(
                {
                    "archivo": ruta_csv.name,
                    "filas": dataframe.shape[0],
                    "columnas": dataframe.shape[1],
                    "departamentos": "",
                    "cantidad_municipios": "",
                    "municipios": "",
                    "estado": "no está la columna DEPARTAMENTO",
                }
            )
            continue

        departamentos = (
            dataframe["DEPARTAMENTO"]
            .dropna()
            .astype("string")
            .str.strip()
            .unique()
            .tolist()
        )

        departamentos = sorted(
            str(departamento)
            for departamento in departamentos
        )

        if "MUNICIPIO" in dataframe.columns:
            municipios = (
                dataframe["MUNICIPIO"]
                .dropna()
                .astype("string")
                .str.strip()
                .unique()
                .tolist()
            )

            municipios = sorted(
                str(municipio)
                for municipio in municipios
            )
        else:
            municipios = []

        resultados.append(
            {
                "archivo": ruta_csv.name,
                "filas": dataframe.shape[0],
                "columnas": dataframe.shape[1],
                "departamentos": " | ".join(departamentos),
                "cantidad_municipios": len(municipios),
                "municipios": " | ".join(municipios),
                "estado": (
                    "Correcto"
                    if len(departamentos) == 1
                    else "Revisar"
                ),
            }
        )

    reporte = pd.DataFrame(resultados)

    RUTA_REPORTE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    reporte.to_csv(
        RUTA_REPORTE,
        index=False,
        encoding="utf-8-sig",
    )

    print(reporte.to_string(index=False))
    print()


if __name__ == "__main__":
    main()