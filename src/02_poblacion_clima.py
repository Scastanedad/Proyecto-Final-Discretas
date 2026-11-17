"""
Paso 2: población (DANE) y clima (Open-Meteo) por municipio y periodo; une todo en un panel.

Entradas (datos/crudos/):
  poblacion_atlantico_2018_2025.csv  DANE, "Serie municipal de población por área 2018-2042"
                                     (PPED-AreaMun-2018-2042_VP.xlsx, versión post-COVID, ago-2025)
  clima_diario_2018_2025.csv         Open-Meteo Historical API, modelo ECMWF IFS (9 km), diario:
                                     precipitación (mm), temperatura media (°C), humedad relativa media (%)
  coordenadas_municipios.csv         DANE DIVIPOLA (datos.gov.co, gdxc-w37w): lat/lon de cada cabecera

Salidas (datos/procesados/):
  clima_mun_periodo.csv   anio, periodo, cod_mun, lluvia_mm, temp_media, humedad_media, dias,
                          lluvia_anomalia  (lluvia del periodo − promedio de ese periodo en los años
                          de ENTRENAMIENTO, por municipio; 2020 no entra por la pandemia)
  panel_base.csv          casos + población + incidencia por 100 mil + clima, 2.392 filas

Uso: python src/02_poblacion_clima.py
"""
import importlib.util
from datetime import date
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS = RAIZ / "datos" / "crudos"
PROC = RAIZ / "datos" / "procesados"
ANIOS_ENTRENAMIENTO = [2018, 2019, 2021, 2022, 2023]   # 2020 excluido (pandemia), 2024 val, 2025 prueba

# Reutiliza el calendario epidemiológico del paso 1
_spec = importlib.util.spec_from_file_location("casos", RAIZ / "src" / "01_casos.py")
casos_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(casos_mod)


def clima_por_periodo() -> pd.DataFrame:
    d = pd.read_csv(CRUDOS / "clima_diario_2018_2025.csv")
    fechas = [date.fromisoformat(f) for f in d["fecha"]]
    epi = [casos_mod.semana_epi(f) for f in fechas]
    d["anio"] = [a for a, _ in epi]
    d["periodo"] = [casos_mod.periodo_de_semana(s) for _, s in epi]
    d = d[d["anio"].between(2018, 2025)]
    c = (d.groupby(["anio", "periodo", "cod_mun"])
          .agg(lluvia_mm=("precipitacion_mm", "sum"),
               temp_media=("temp_media_c", "mean"),
               humedad_media=("humedad_media_pct", "mean"),
               dias=("fecha", "count"))
          .reset_index())
    # Anomalía de lluvia: se compara cada periodo con el promedio del MISMO periodo del año
    # en los años de entrenamiento (evita fuga de información de validación/prueba).
    ref = (c[c["anio"].isin(ANIOS_ENTRENAMIENTO)]
           .groupby(["cod_mun", "periodo"])["lluvia_mm"].mean().rename("lluvia_ref"))
    c = c.merge(ref, on=["cod_mun", "periodo"])
    c["lluvia_anomalia"] = c["lluvia_mm"] - c["lluvia_ref"]
    return c.drop(columns="lluvia_ref").round(3)


def main():
    clima = clima_por_periodo()
    clima.to_csv(PROC / "clima_mun_periodo.csv", index=False)
    print(f"clima_mun_periodo.csv: {len(clima)} filas")

    pob = pd.read_csv(CRUDOS / "poblacion_atlantico_2018_2025.csv")[["cod_mun", "anio", "poblacion_total"]]
    casos = pd.read_csv(PROC / "casos_mun_periodo.csv")
    panel = (casos.merge(pob, on=["cod_mun", "anio"], how="left")
                  .merge(clima, on=["anio", "periodo", "cod_mun"], how="left"))
    panel["incidencia_100k"] = (panel["casos"] / panel["poblacion_total"] * 1e5).round(3)
    faltantes = panel[["poblacion_total", "lluvia_mm"]].isna().sum().to_dict()
    panel.to_csv(PROC / "panel_base.csv", index=False)
    print(f"panel_base.csv: {len(panel)} filas | valores faltantes: {faltantes}")


if __name__ == "__main__":
    main()
