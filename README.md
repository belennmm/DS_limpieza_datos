# Obtención y limpieza de datos 

Este proyecto realiza la obtención, diagnóstico, limpieza y validación de datos de establecimientos educativos de Guatemala que ofrecen el nivel específico de **Diversificado**.

## Integrantes

- Belén Monterroso 
- Melisa Mendizábal
- Renato Rojas 

## Fuente de los datos

Los datos fueron obtenidos del portal oficial del Ministerio de Educación de Guatemala: 
<https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/>

La data utilizada en este proyecto corresponde específicamente a establecimientos del nivel DIVERSIFICADO. 

## Requisitos

Para ejecutarlo es necesario tener instalado:

- Python 3.10 o una versión más reciente
- `pip`
- Git
- Conexión a Internet para realizar la descarga automática

Las dependencias utilizadas se encuentran en `requirements.txt`:

```text
pandas
requests
beautifulsoup4
lxml
xlrd>=2.0.1
jupyter
rapidfuzz
```

## Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/belennmm/DS_limpieza_datos.git
cd DS_limpieza_datos
```

### 2. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el programa principal

Desde la raíz del proyecto, ejecutar:

```bash
python src/main.py
```

El programa presenta el siguiente menú:

```text
Seleccione una opción
- MENÚ -
1. Descarga automatica de los archivos desde la página de MINEDUC
2. Análisis del estado inicial de los datos
3. Limpieza del conjunto de datos
0. Salir
Seleccione una opción:
```


### Opción 1: descarga automática

Los archivos obtenidos se almacenan en:

```text
data/csv_originales/
```

### Opción 2: análisis del estado inicial

Los resultados se almacenan en archivos dentro de:

```text
docs/
```

### Opción 3: limpieza del conjunto de datos

El archivo final se almacena en:

```text
data/processed/establecimientos_limpio.csv
```

### Nota:
> El portal del MINEDUC puede modificar su estructura, lo que podría requerir actualizar el script de descarga.