"""
Paso 1: construye la tabla de casos de dengue por municipio y periodo epidemiológico.

Entrada : datos/crudos/dengue_atlantico_2018_2025.csv   (un caso por fila, ver 00_extraer_sivigila.py)
          datos/procesados/municipios_atlantico.csv      (los 23 municipios del Atlántico)
Salida  : datos/procesados/casos_mun_periodo.csv
          columnas: anio, periodo, cod_mun, municipio, casos   (23 x 13 x 8 = 2.392 filas)

Decisiones (ver BITACORA.md):
  * Cada caso se ubica en la semana epidemiológica de su INICIO DE SÍNTOMAS (INI_SIN),
    no en la de notificación, porque refleja cuándo ocurrió el contagio.
  * Semana epidemiológica: inicia el domingo; la semana 1 es la que contiene el 4 de enero
    (mismo criterio del INS / CDC-MMWR).
  * Periodo epidemiológico = ceil(semana / 4); la semana 53 (cuando existe) va al periodo 13.
  * Se excluyen casos con municipio desconocido (COD_MUN_O = 0) y casos descartados (AJUSTE 6 o D).
  * Las combinaciones municipio-periodo sin casos se rellenan con 0.

Uso:
  python src/01_casos.py                 # desde el CSV de casos crudos
  python src/01_casos.py --desde-celdas  # desde datos/procesados/_celdas_nocero.txt
"""
import sys
import math
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CRUDO = RAIZ / "datos" / "crudos" / "dengue_atlantico_2018_2025.csv"
CELDAS = RAIZ / "datos" / "procesados" / "_celdas_nocero.txt"
MUNICIPIOS = RAIZ / "datos" / "procesados" / "municipios_atlantico.csv"
SALIDA = RAIZ / "datos" / "procesados" / "casos_mun_periodo.csv"
ANIOS = list(range(2018, 2026))
PERIODOS = list(range(1, 14))


def inicio_anio_epi(anio: int) -> date:
    """Domingo que inicia la semana 1 (la semana que contiene el 4 de enero)."""
    j4 = date(anio, 1, 4)
    return j4 - timedelta(days=(j4.weekday() + 1) % 7)  # weekday(): lunes=0 ... domingo=6


def semana_epi(d: date) -> tuple[int, int]:
    anio = d.year
    if d < inicio_anio_epi(anio):
        anio -= 1
    elif d >= inicio_anio_epi(anio + 1):
        anio += 1
    return anio, (d - inicio_anio_epi(anio)).days // 7 + 1


def periodo_de_semana(semana: int) -> int:
    return min(math.ceil(semana / 4), 13)


def parsear_fecha(texto) -> date | None:
    """Fechas del SIVIGILA en formato d/m/aaaa (a veces con hora)."""
    if not isinstance(texto, str) or not texto.strip():
        return None
    d, m, a = texto.split()[0].split("/")[:3]
    return date(int(a), int(m), int(d))


def conteo_desde_crudo() -> pd.DataFrame:
    df = pd.read_csv(CRUDO, dtype=str)
    n0 = len(df)
    df = df[~df["AJUSTE"].isin(["6", "D"])]
    df = df[pd.to_numeric(df["COD_MUN_O"], errors="coerce").fillna(0).astype(int) != 0]
    print(f"Casos leídos: {n0} | tras excluir descartados y municipio desconocido: {len(df)}")

    anios, periodos = [], []
    for ini, ano, sem in zip(df["INI_SIN"], df["ANO"], df["SEMANA"]):
        f = parsear_fecha(ini)
        a, s = semana_epi(f) if f else (int(ano), int(sem))  # respaldo: semana de notificación
        anios.append(a)
        periodos.append(periodo_de_semana(s))
    df = df.assign(anio=anios, periodo=periodos,
                   cod_mun=8000 + df["COD_MUN_O"].astype(int))
    df = df[df["anio"].isin(ANIOS)]
    return df.groupby(["anio", "periodo", "cod_mun"]).size().rename("casos").reset_index()


def conteo_desde_celdas() -> pd.DataFrame:
    registros = [tuple(map(int, x.split(","))) for x in CELDAS.read_text().strip().split(";")]
    return pd.DataFrame(registros, columns=["anio", "periodo", "cod_mun", "casos"])


def main():
    conteo = conteo_desde_celdas() if "--desde-celdas" in sys.argv else conteo_desde_crudo()
    mun = pd.read_csv(MUNICIPIOS)
    malla = pd.MultiIndex.from_product([ANIOS, PERIODOS, mun["cod_mun"]],
                                       names=["anio", "periodo", "cod_mun"]).to_frame(index=False)
    tabla = (malla.merge(conteo, how="left", on=["anio", "periodo", "cod_mun"])
                  .merge(mun, on="cod_mun"))
    tabla["casos"] = tabla["casos"].fillna(0).astype(int)
    tabla = tabla[["anio", "periodo", "cod_mun", "municipio", "casos"]]
    tabla.to_csv(SALIDA, index=False)
    print(f"Guardado {SALIDA.name}: {len(tabla)} filas, {tabla['casos'].sum()} casos")


if __name__ == "__main__":
    main()
