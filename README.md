# Brotes de dengue en el Atlántico — Proyecto final Matemáticas Discretas

Predice qué municipios del Atlántico tendrán un brote de dengue en el siguiente periodo
epidemiológico (4 semanas), combinando una red neuronal con un grafo de municipios vecinos.

## Requisitos
Python 3.10+. Instalar dependencias: `pip install -r requirements.txt`

## Cómo ejecutar
```bash
python src/00_extraer_sivigila.py      # (opcional) desde los Excel del SIVIGILA en datos/crudos/xlsx/
python src/01_casos.py                 # casos por municipio y periodo -> casos_mun_periodo.csv
python src/02_poblacion_clima.py       # población + clima por periodo -> panel_base.csv
python src/03_grafo.py                 # grafo, centralidades, presión de vecinos -> panel_grafo.csv
python src/04_dataset.py               # etiqueta de brote y variables -> dataset_modelo.csv
python src/05_modelo.py                # entrena y compara 5 modelos -> resultados/metricas_modelos.csv (~20 s)
python src/06_prioridad.py             # pronóstico y ranking de fumigación -> resultados/prioridad_2026_p1.csv
python src/07_figuras_descriptivas.py  # figuras descriptivas para el documento

python tests/test_semana_epi.py        # pruebas con resultado conocido (calendario epidemiológico)
python tests/test_grafo.py             # pruebas con resultado conocido (grafo, calculado a mano)
python tests/test_dataset.py           # sin fuga de información del futuro ni de validación/prueba
```

## Estructura
```
datos/crudos/       datos originales (SIVIGILA, DANE, clima)
datos/procesados/   tablas listas para el modelo
src/                scripts numerados en orden de ejecución
tests/              pruebas con resultado conocido
documento/          informe en LaTeX y figuras
resultados/         métricas, predicciones y ranking de prioridad
BITACORA.md         registro de lo hecho y las decisiones
```

## Fuentes
- Instituto Nacional de Salud. Portal SIVIGILA 4.0 — microdatos, evento Dengue (210), 2018–2025.
- DANE. Serie municipal de población por área 2018–2042 (actualización post-COVID, 2025).
- DANE. Marco Geoestadístico Nacional 2018 — límites municipales.
- DANE. DIVIPOLA — códigos y coordenadas de municipios (datos.gov.co, gdxc-w37w).
- Open-Meteo. Historical Weather API, modelo ECMWF IFS 9 km (2018–2025).
