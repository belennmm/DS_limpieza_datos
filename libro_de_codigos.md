# Libro de Códigos — Establecimientos Educativos (Nivel Diversificado)

## Información general del conjunto de datos

- **Fecha de extracción:** 16/07/2026
- **Fuente de los datos:** Se obtuvo esta información de la página oficial del Ministerio de Educación de Guatemala (MINEDUC), a partir de archivos por departamento, únicamente del nivel Diversificado. Disponible en: https://www.mineduc.gob.gt/BUSCAESTABLECIMIENTO_GE/
- **Versión del conjunto limpio:** v1.0 (generado el 20/07/2026)
- **Número de registros:** 11,867
- **Número de variables (dataset unificado):** 18 (17 originales + 1 derivada: ORIGEN)

---

## CODIGO
a. **Descripción:** Código único que identifica a cada establecimiento educativo.
b. **Tipo de dato:** String
c. **Dominio permitido:** Alfanumérico con guiones (funciona como identificador, no como valor numérico)
d. **Valores posibles:** 11,867 valores únicos (uno por establecimiento)
e. **Tratamiento de limpieza:** Ninguno; no se detectaron problemas.
f. **Variables derivadas:** No aplica.

## DISTRITO
a. **Descripción:** Código del distrito educativo al que pertenece el establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Código alfanumérico administrativo (1,681 valores únicos)
d. **Valores posibles:** Diversos patrones de escritura, todos válidos como identificador.
e. **Tratamiento de limpieza:** No se aplicó corrección; las variaciones de formato no afectan su validez como identificador. 532 valores faltantes (4.48%).
f. **Variables derivadas:** No aplica.

## DEPARTAMENTO
a. **Descripción:** Nombre del departamento donde se encuentra el establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal — los 22 departamentos oficiales de Guatemala.
d. **Valores posibles:** 23 valores únicos originales (incluía "CIUDAD CAPITAL" como valor inválido).
e. **Tratamiento de limpieza:** Se reemplazó "CIUDAD CAPITAL" por "GUATEMALA".
f. **Variables derivadas:** No aplica.

## MUNICIPIO
a. **Descripción:** Nombre del municipio donde se ubica el establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal — listado oficial de municipios de Guatemala.
d. **Valores posibles:** 352 valores únicos originales (22 correspondían a "ZONA 1"–"ZONA 25", que no son municipios).
e. **Tratamiento de limpieza:** Los valores tipo "ZONA n" se reemplazaron por "GUATEMALA", ya que esas zonas pertenecen a ese municipio.
f. **Variables derivadas:** No aplica.

## ESTABLECIMIENTO
a. **Descripción:** Nombre oficial del establecimiento educativo.
b. **Tipo de dato:** String
c. **Dominio permitido:** Texto libre (nombre propio institucional)
d. **Valores posibles:** 6,312 valores únicos.
e. **Tratamiento de limpieza:** Ninguno. 5 valores faltantes (0.04%).
f. **Variables derivadas:** No aplica.

## DIRECCION
a. **Descripción:** Dirección física del establecimiento educativo.
b. **Tipo de dato:** String
c. **Dominio permitido:** Texto libre (números, letras, símbolos)
d. **Valores posibles:** 7,439 valores únicos.
e. **Tratamiento de limpieza:** Ninguno. 76 valores faltantes (0.64%).
f. **Variables derivadas:** No aplica.

## TELEFONO
a. **Descripción:** Número telefónico de contacto del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Numérico como texto; sin longitud fija (puede incluir varios números, guiones o espacios).
d. **Valores posibles:** 6,571 valores únicos; 213 identificados con formato inconsistente (múltiples números, longitudes distintas, separadores variados).
e. **Tratamiento de limpieza:** Los valores con formato inconsistente/no estandarizable se reemplazaron por "DESCONOCIDO" (afecta a menos del 10% de los datos). Los 946 valores faltantes (7.97%) también quedan como "DESCONOCIDO".
f. **Variables derivadas:** No aplica.

## SUPERVISOR
a. **Descripción:** Nombre del supervisor responsable del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Texto libre (nombre propio)
d. **Valores posibles:** 1,280 valores únicos; 2 valores inválidos detectados (uno compuesto solo por guiones, otro con error de escritura "ACEVED0").
e. **Tratamiento de limpieza:** El valor de solo guiones se reemplazó por "DESCONOCIDO"; el error de escritura se corrigió manualmente (0 → O). 535 valores faltantes (4.51%).
f. **Variables derivadas:** No aplica.

## DIRECTOR
a. **Descripción:** Nombre del director del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Texto libre (nombre propio)
d. **Valores posibles:** 5,514 valores únicos; 28 valores inválidos (guiones de distinta longitud, puntos, "0").
e. **Tratamiento de limpieza:** Todos los valores inválidos y faltantes (1,733 registros, 14.6%) se reemplazaron por el placeholder "DESCONOCIDO" para no perder los registros completos.
f. **Variables derivadas:** No aplica.

## NIVEL
a. **Descripción:** Nivel educativo que ofrece el establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal, un solo valor posible en este dataset.
d. **Valores posibles:** "Diversificado" (1 valor único).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## SECTOR
a. **Descripción:** Tipo de administración del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Oficial, Privado, Cooperativa, Municipal (4 valores únicos).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## AREA
a. **Descripción:** Clasificación geográfica del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Urbana, Rural (3 valores únicos según el conteo — verificar la tercera categoría en el dataset).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## STATUS
a. **Descripción:** Estado de funcionamiento del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Abierta, Cerrada temporalmente, Cerrada definitivamente, entre otras (5 valores únicos).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## MODALIDAD
a. **Descripción:** Modalidad educativa en la que opera el establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Monolingüe, Bilingüe (2 valores únicos).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## JORNADA
a. **Descripción:** Jornada en la que se imparten clases.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Matutina, Vespertina, Nocturna, Doble, entre otras (6 valores únicos).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## PLAN
a. **Descripción:** Tipo de plan de estudios o modalidad de atención.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal.
d. **Valores posibles:** Diario, Fin de semana, entre otros (13 valores únicos).
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## DEPARTAMENTAL
a. **Descripción:** Dirección Departamental de Educación responsable del establecimiento.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal (identificador administrativo del origen del registro).
d. **Valores posibles:** 26 valores únicos.
e. **Tratamiento de limpieza:** Ninguno.
f. **Variables derivadas:** No aplica.

## ORIGEN *(variable derivada)*
a. **Descripción:** Identifica el archivo de origen del cual proviene cada registro dentro del conjunto de datos unificado.
b. **Tipo de dato:** String
c. **Dominio permitido:** Categórica nominal, correspondiente a los nombres/identificadores de cada archivo individual analizado.
d. **Valores posibles:** Un valor por cada archivo fuente unido en el dataset final.
e. **Tratamiento de limpieza:** No aplica (variable generada en el proceso de unificación, no proviene de los archivos originales).
f. **Variables derivadas:** Es en sí misma la variable derivada del proceso de integración de archivos.

---

## Nota adicional (transversal a todo el dataset)

Durante la limpieza también se eliminaron las líneas de encabezado (26 líneas) y el pie de página variable de cada archivo original (formato tipo HTML al descargarse, no CSV crudo), así como las columnas completamente vacías en todos los registros, ya que no aportaban información.
