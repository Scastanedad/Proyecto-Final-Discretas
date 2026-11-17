# Predicción de brotes de dengue en el Atlántico

Proyecto final de Matemáticas Discretas (MAT 4021, Grupo 4), Universidad del Norte.
Profesor: Iván Gómez.

Integrantes: Samuel Castañeda, Amir Diago y Andrés Mendible.

Repositorio: https://github.com/Scastanedad/Proyecto-Final-Discretas

## De qué trata

El proyecto intenta anticipar en qué municipios del Atlántico habrá un brote de dengue en el
siguiente periodo epidemiológico (4 semanas) y en qué orden convendría fumigar. Para eso usamos:

- Un **grafo** de los 23 municipios: hay arista entre dos municipios si comparten frontera, y
  las aristas tienen un peso de gravedad según población y distancia. Las centralidades (grado,
  cercanía e intermediación) se calculan con BFS y con el algoritmo de Brandes, programados por
  nosotros en `src/grafo_lib.py` sin usar librerías de grafos.
- Una **red neuronal** (perceptrón multicapa 14 → 16 → 8 → 1) que predice si habrá brote,
  comparada con una regla de persistencia y con una regresión logística.
- Un **ranking de prioridad**: probabilidad de brote × (1 + intermediación relativa).

Todos los datos son reales y públicos (SIVIGILA, DANE y Open-Meteo) y ya vienen incluidos en el
repositorio, así que no hay que descargar nada para correrlo.

## Requisitos

- Python 3.10 o superior (lo probamos con 3.10 y 3.14).
- Las librerías de `requirements.txt`: pandas, numpy, openpyxl, shapely, networkx, matplotlib y
  scikit-learn.

## Instalación

```bash
git clone https://github.com/Scastanedad/Proyecto-Final-Discretas.git
cd Proyecto-Final-Discretas
python -m venv .venv
```

Activar el entorno virtual:

- Windows: `.venv\Scripts\activate`
- Linux / macOS: `source .venv/bin/activate`

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Cómo ejecutarlo

Los scripts están numerados y se corren en ese orden desde la carpeta raíz del proyecto. Cada uno
lee lo que dejó el anterior en `datos/procesados/`.

```bash
python src/01_casos.py
python src/02_poblacion_clima.py
python src/03_grafo.py
python src/04_dataset.py
python src/05_modelo.py
python src/06_prioridad.py
python src/07_figuras_descriptivas.py
```

| Script | Qué hace | Qué genera |
|---|---|---|
| `01_casos.py` | Asigna cada caso a su semana y periodo epidemiológico (por fecha de inicio de síntomas) y cuenta casos por municipio y periodo. | `datos/procesados/casos_mun_periodo.csv` |
| `02_poblacion_clima.py` | Une población y clima por periodo y calcula la incidencia por 100 mil habitantes y la anomalía de lluvia. | `panel_base.csv`, `clima_mun_periodo.csv` |
| `03_grafo.py` | Construye el grafo desde los polígonos del DANE, calcula pesos, centralidades y la presión de los vecinos. | `grafo_aristas.csv`, `grafo_centralidad.csv`, `panel_grafo.csv`, figura del grafo |
| `04_dataset.py` | Define la etiqueta de brote, los rezagos y la división por años (entrenamiento / validación / prueba). | `dataset_modelo.csv`, `dataset_pronostico.csv`, `umbrales_brote.csv` |
| `05_modelo.py` | Entrena y compara los cinco modelos; la red se entrena con 20 semillas. Es el paso más lento (unos 20 segundos). | `resultados/metricas_modelos.csv`, `metricas_por_semilla.csv`, `predicciones_prueba.csv`, `modelo_red.pkl` |
| `06_prioridad.py` | Compara municipios densos y escasos, hace el pronóstico del periodo 1 de 2026 y el ranking de fumigación. | `resultados/prioridad_2026_p1.csv`, `analisis_por_grupo.csv`, figuras |
| `07_figuras_descriptivas.py` | Figuras de casos por año y de estacionalidad. | `documento/figuras/*.png` |

Al final, los números de las tablas del documento quedan en la carpeta `resultados/`. Como las
semillas están fijas, al correrlo de nuevo deben salir los mismos valores.

### Paso opcional: extraer los datos del SIVIGILA

El archivo `datos/crudos/dengue_atlantico_2018_2025.csv` ya está en el repositorio. Solo si se
quiere regenerar desde cero, hay que descargar del
[Portal SIVIGILA](https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx) los Excel del evento
Dengue (código 210) de 2018 a 2025, guardarlos como `datos/crudos/xlsx/Datos_<AÑO>_210.xlsx` y
correr:

```bash
python src/00_extraer_sivigila.py
```

No los subimos porque pesan varios cientos de MB.

## Pruebas

Hay 11 pruebas con resultado conocido. Se corren así:

```bash
python tests/test_semana_epi.py
python tests/test_grafo.py
python tests/test_dataset.py
```

- `test_semana_epi.py`: fechas cuya semana epidemiológica se conoce (por ejemplo, que 2020 tuvo 53 semanas).
- `test_grafo.py`: un subgrafo de 5 municipios (Barranquilla, Soledad, Galapa, Malambo y Puerto
  Colombia) cuyo grado, cercanía e intermediación calculamos a mano; además compara nuestros
  algoritmos con NetworkX en el grafo completo de 23 municipios.
- `test_dataset.py`: revisa que no haya fuga de información (los umbrales usan solo años de
  entrenamiento y los rezagos solo miran al pasado).

Si todo está bien, cada prueba imprime `OK`.

## Estructura del repositorio

```
datos/
  crudos/        datos originales: casos SIVIGILA, población DANE, límites MGN 2018,
                 coordenadas DIVIPOLA y clima diario de Open-Meteo
  procesados/    tablas intermedias que generan los scripts
src/             scripts del proyecto (numerados en orden) y grafo_lib.py
tests/           pruebas con resultado conocido
resultados/      métricas, predicciones y ranking de prioridad
documento/       informe (main.tex), diapositivas en Beamer (diapositivas.tex) y figuras
requirements.txt dependencias de Python
```

## Compilar el documento y las diapositivas

Desde la carpeta `documento/` (o subiendo esa carpeta a Overleaf):

```bash
pdflatex main.tex
pdflatex main.tex
pdflatex diapositivas.tex
pdflatex diapositivas.tex
```

Se compila dos veces para que salgan bien las referencias cruzadas. Las referencias bibliográficas
están dentro del mismo `.tex`, así que no hace falta BibTeX.

## Resultados principales

- En el año de prueba (2025) la red detectó el 88 % de los brotes un periodo antes, frente al 68 %
  de la regla de persistencia (AUC-ROC 0,83 frente a 0,77).
- La red no le ganó a la regresión logística, y agregar la presión de los vecinos no mejoró la
  predicción (−0,005 ± 0,031 en AUC-PR en 20 semillas).
- Donde el grafo sí sirvió fue para decidir: Sabanalarga y Baranoa son los municipios con mayor
  intermediación, es decir, los puentes entre el área metropolitana y el sur del departamento.

## Fuentes de datos

- Instituto Nacional de Salud. Portal SIVIGILA 4.0, microdatos del evento Dengue (210), 2018–2025.
- DANE. Serie municipal de población por área 2018–2042 (actualización post-COVID, 2025).
- DANE. Marco Geoestadístico Nacional 2018, límites municipales.
- DANE. DIVIPOLA, códigos y coordenadas de municipios (datos.gov.co, gdxc-w37w).
- Open-Meteo. Historical Weather API, modelo ECMWF IFS de 9 km (2018–2025).
