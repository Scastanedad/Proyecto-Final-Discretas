"""
Pruebas del dataset del modelo: que no haya fuga de información del futuro ni de validación/prueba.
"""
from pathlib import Path
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "datos" / "procesados"
d = pd.read_csv(PROC / "dataset_modelo.csv")
panel = pd.read_csv(PROC / "panel_grafo.csv")
u = pd.read_csv(PROC / "umbrales_brote.csv")


def test_division_por_anio_objetivo():
    assert set(d[d.conjunto == "entrenamiento"].obj_anio) == {2018, 2019, 2021, 2022, 2023}
    assert set(d[d.conjunto == "validacion"].obj_anio) == {2024}
    assert set(d[d.conjunto == "prueba"].obj_anio) == {2025}
    assert set(d[d.conjunto == "excluido_2020"].obj_anio) == {2020}


def test_umbral_usa_solo_entrenamiento():
    """Recalcula a mano el umbral de un municipio y periodo con los años de entrenamiento."""
    x = panel[(panel.cod_mun == 8001) & (panel.periodo == 12) & panel.anio.isin([2018, 2019, 2021, 2022, 2023])]
    esperado = x.incidencia_100k.mean() + x.incidencia_100k.std()
    obtenido = u[(u.cod_mun == 8001) & (u.periodo == 12)].umbral_inc.iloc[0]
    assert abs(esperado - obtenido) < 1e-9


def test_rezagos_miran_al_pasado():
    """inc_t1 de (m, t) debe ser la incidencia de m en t-1, y el objetivo debe ser t+1."""
    p = panel.set_index(["cod_mun", "anio", "periodo"])
    fila = d[(d.cod_mun == 8758) & (d.anio == 2022) & (d.periodo == 1)].iloc[0]   # Soledad, 2022-P1
    assert abs(fila.inc_t1 - np.log1p(p.loc[(8758, 2021, 13), "incidencia_100k"])) < 1e-9   # cruza el año
    assert abs(fila.inc_t - np.log1p(p.loc[(8758, 2022, 1), "incidencia_100k"])) < 1e-9
    assert (fila.obj_anio, fila.obj_periodo) == (2022, 2)
    assert fila.obj_casos == p.loc[(8758, 2022, 2), "casos"]


def test_etiqueta_de_brote():
    """Brote = incidencia por encima del umbral Y al menos 3 casos."""
    m = d.merge(u, left_on=["cod_mun", "obj_periodo"], right_on=["cod_mun", "periodo"], suffixes=("", "_u"))
    esperado = ((m.obj_incidencia_100k > m.umbral_inc) & (m.obj_casos >= 3)).astype(int)
    assert (esperado.values == m.obj_brote.values).all()


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f(); print("OK ", nombre)
