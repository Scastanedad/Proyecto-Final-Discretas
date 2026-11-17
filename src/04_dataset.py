"""
Paso 4: etiqueta de brote y dataset para el modelo.

Entrada : datos/procesados/panel_grafo.csv
Salida  : datos/procesados/dataset_modelo.csv   (una fila = municipio m, periodo t; objetivo = brote en t+1)
          datos/procesados/umbrales_brote.csv   (umbral de incidencia por municipio y periodo del año)

Etiqueta (brote en el periodo t+1 del municipio m):
    brote = 1  si  incidencia(t+1) > media + 1·DE   de la incidencia de m en ese mismo periodo del año,
                   calculadas SOLO con los años de entrenamiento
               y   casos(t+1) >= 3   (para que pasar de 0 a 1 caso no cuente como brote)

Variables de entrada (todas conocidas al final del periodo t):
    inc_t, inc_t1, inc_t2          log(1 + incidencia) en t, t-1, t-2
    vec_t, vec_t1                  log(1 + presión de vecinos) en t, t-1          <- aporte del grafo
    lluvia_anom_t .. lluvia_anom_t3 anomalía de lluvia en t, t-1, t-2, t-3 (mm)
    temp_t, hum_t                  temperatura y humedad medias en t
    sen_per, cos_per               periodo del año del OBJETIVO (t+1) en forma circular
    log_pob                        log de la población

División temporal (por el año del periodo OBJETIVO):
    entrenamiento 2018, 2019, 2021, 2022, 2023 | validación 2024 | prueba 2025
    Filas cuyo objetivo cae en 2020 se excluyen (decisión "años de pandemia", opción B).
    Los rezagos se calculan sobre la serie completa ANTES de excluir 2020.
"""
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "datos" / "procesados"
ENTRENAMIENTO, VALIDACION, PRUEBA = [2018, 2019, 2021, 2022, 2023], [2024], [2025]
MIN_CASOS_BROTE = 3

ENTRADAS_SIN_GRAFO = ["inc_t", "inc_t1", "inc_t2",
                      "lluvia_anom_t", "lluvia_anom_t1", "lluvia_anom_t2", "lluvia_anom_t3",
                      "temp_t", "hum_t", "sen_per", "cos_per", "log_pob"]
ENTRADAS_GRAFO = ["vec_t", "vec_t1"]
ENTRADAS = ENTRADAS_SIN_GRAFO + ENTRADAS_GRAFO


def umbrales(panel):
    ref = panel[panel["anio"].isin(ENTRENAMIENTO)]
    u = ref.groupby(["cod_mun", "periodo"])["incidencia_100k"].agg(["mean", "std"]).reset_index()
    u["umbral_inc"] = u["mean"] + u["std"]
    return u[["cod_mun", "periodo", "umbral_inc"]]


def construir():
    p = pd.read_csv(PROC / "panel_grafo.csv").sort_values(["cod_mun", "anio", "periodo"])
    p["t_idx"] = (p["anio"] - 2018) * 13 + p["periodo"] - 1          # índice continuo del periodo
    u = umbrales(p)
    p = p.merge(u, on=["cod_mun", "periodo"], how="left")
    p["brote"] = ((p["incidencia_100k"] > p["umbral_inc"]) & (p["casos"] >= MIN_CASOS_BROTE)).astype(int)

    g = p.groupby("cod_mun", group_keys=False)
    inc, vec = np.log1p(p["incidencia_100k"]), np.log1p(p["presion_vecinos"])
    p["inc_t"], p["vec_t"] = inc, vec
    for k in (1, 2):
        p[f"inc_t{k}"] = inc.groupby(p["cod_mun"]).shift(k)
    p["vec_t1"] = vec.groupby(p["cod_mun"]).shift(1)
    p["lluvia_anom_t"] = p["lluvia_anomalia"]
    for k in (1, 2, 3):
        p[f"lluvia_anom_t{k}"] = g["lluvia_anomalia"].shift(k)
    p["temp_t"], p["hum_t"] = p["temp_media"], p["humedad_media"]
    p["log_pob"] = np.log(p["poblacion_total"])

    # Objetivo: brote en t+1 (y datos de ese periodo para identificarlo)
    for col in ["brote", "anio", "periodo", "casos", "incidencia_100k"]:
        p[f"obj_{col}"] = g[col].shift(-1)
    p["brote_actual"] = p["brote"]                               # para la línea base de persistencia
    # Periodo objetivo también para la última fila (pronóstico): el siguiente al actual
    p["obj_periodo"] = p["obj_periodo"].fillna(p["periodo"] % 13 + 1)
    p["obj_anio"] = p["obj_anio"].fillna(p["anio"] + (p["periodo"] == 13))
    ang = 2 * np.pi * (p["obj_periodo"] - 1) / 13
    p["sen_per"], p["cos_per"] = np.sin(ang), np.cos(ang)

    ultimo = p["t_idx"] == p["t_idx"].max()
    pron = p[ultimo].dropna(subset=ENTRADAS).copy()               # pronóstico: periodo siguiente al último dato
    pron["obj_anio"] = pron["obj_anio"].astype(int)
    d = p.dropna(subset=ENTRADAS + ["obj_brote"]).copy()
    d["obj_anio"] = d["obj_anio"].astype(int)
    d["conjunto"] = np.select([d["obj_anio"].isin(ENTRENAMIENTO), d["obj_anio"].isin(VALIDACION),
                               d["obj_anio"].isin(PRUEBA)], ["entrenamiento", "validacion", "prueba"],
                              default="excluido_2020")
    cols = (["cod_mun", "municipio", "anio", "periodo", "obj_anio", "obj_periodo", "conjunto",
             "brote_actual", "obj_brote", "obj_casos", "obj_incidencia_100k"] + ENTRADAS)
    pron["conjunto"] = "pronostico"
    return d[cols], u, pron[cols]


def main():
    d, u, pron = construir()
    pron.to_csv(PROC / "dataset_pronostico.csv", index=False)
    print(f"dataset_pronostico.csv: {len(pron)} filas (objetivo {int(pron.obj_anio.iloc[0])}, "
          f"periodo {int(pron.obj_periodo.iloc[0])})")
    u.to_csv(PROC / "umbrales_brote.csv", index=False)
    d.to_csv(PROC / "dataset_modelo.csv", index=False)
    print(f"dataset_modelo.csv: {len(d)} filas, {len(ENTRADAS)} entradas")
    r = d.groupby("conjunto")["obj_brote"].agg(filas="count", brotes="sum", tasa="mean").round(3)
    print(r.to_string())


if __name__ == "__main__":
    main()
