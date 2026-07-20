import limpiarcsvcrudos
import revisiones
import unirdata
import diagnostico
import descargaAutomatica 

menu = '1'
print('Bienvenido al proyecto 1')

while menu != '0':
    print('- MENÚ -')
    print('1. Descarga automatica de los archivos desde la página de MINEDUC')
    print('2. Análisis del estado inicial de los datos')
    print('0. Salir')

    menu = input('Seleccione una opción:')
    print('')

    if menu == '1':
        print('-- Descarga automatica de los archivos desde la página de MINEDUC --')
        descargaAutomatica.descarga_archivos()
    elif menu == '2':
        try:
            dataframe = diagnostico.cargar_datos()
        except FileNotFoundError as error:
            print(error)
            continue

        submenu = ''
        while submenu != '0':
            print()
            print('-- Análisis del estado inicial de los datos --')
            print('a. Número de registros y variables')
            print('b. Tipo de dato de cada variable')
            print('c. Cantidad y porcentaje de valores faltantes por variable')
            print('d. Cantidad de valores únicos')
            print('e. Cantidad de registros duplicados exactos')
            print('f. Variables con valores fuera de dominio o inconsistentes')
            print('g. Variables con formatos inconsistentes (espacios, mayúsculas, mojibake)')
            print('h. Identificación de problemas potenciales de calidad de datos')
            print('i. Ejecutar todo el diagnóstico y exportar reporte (docs/diagnostico_inicial.csv)')
            print('0. Volver al menú principal')

            submenu = input('Seleccione una opción:')

            if submenu == 'a':
                print(diagnostico.num_registros_variables(dataframe).to_string(index=False))

            elif submenu == 'b':
                print(diagnostico.tipos_dato(dataframe).to_string(index=False))

            elif submenu == 'c':
                print(diagnostico.valores_faltantes(dataframe).to_string(index=False))

            elif submenu == 'd':
                print(diagnostico.valores_unicos(dataframe).to_string(index=False))

            elif submenu == 'e':
                cantidad, ejemplos = diagnostico.duplicados_exactos(dataframe)
                print(f'Duplicados exactos: {cantidad}')
                if cantidad:
                    print(ejemplos.to_string(index=False))

            elif submenu == 'f':
                print('-- f. Variables con valores fuera de dominio o inconsistentes --')
                diagnostico.imprimir_fuera_dominio(diagnostico.valores_fuera_dominio(dataframe))
 
                print()
                print('-- Categorías con posibles variantes de escritura --')
                categorias_df = diagnostico.categorias_similares(dataframe)
                print(categorias_df.to_string(index=False) if not categorias_df.empty else 'Sin hallazgos.')

            elif submenu == 'g':
                print(diagnostico.formatos_inconsistentes(dataframe).to_string(index=False))
                resultado = diagnostico.patrones_formato(dataframe)
                print(resultado.to_string(index=False) if not resultado.empty else 'Sin hallazgos.')

            elif submenu == 'h':
                faltantes_df = diagnostico.valores_faltantes(dataframe)
                cantidad_duplicados, _ = diagnostico.duplicados_exactos(dataframe)
                fuera_dominio_df = diagnostico.valores_fuera_dominio(dataframe)
                formato_df = diagnostico.formatos_inconsistentes(dataframe)
                patrones_df = diagnostico.patrones_formato(dataframe)
                categorias_df = diagnostico.categorias_similares(dataframe)

                problemas = diagnostico.problemas_potenciales(
                    faltantes_df, cantidad_duplicados, fuera_dominio_df, formato_df, patrones_df, categorias_df
                )
                for problema in problemas:
                    print(f'- {problema}')

            elif submenu == 'i':
                diagnostico.main()

            elif submenu == '0':
                print('Volviendo al menú principal')

            else:
                print('Seleccione una opción válida')

    elif menu == '0':
        print('Gracias por utilizar el programa')

    else:
        print('Seleccione una opción')