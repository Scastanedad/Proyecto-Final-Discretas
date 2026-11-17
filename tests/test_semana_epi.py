"""Casos de resultado conocido para la semana epidemiológica (calendario INS / CDC-MMWR)."""
import importlib.util
from datetime import date
from pathlib import Path

ruta = Path(__file__).resolve().parents[1] / "src" / "01_casos.py"
spec = importlib.util.spec_from_file_location("casos", ruta)
casos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(casos)

CONOCIDOS = [
    (date(2018, 11, 3), (2018, 44)),   # caso de ejemplo del archivo 2018: INI_SIN 3/11/2018
    (date(2018, 12, 30), (2019, 1)),   # la semana 1 de 2019 empieza el domingo 30/12/2018
    (date(2020, 12, 31), (2020, 53)),  # 2020 tuvo 53 semanas
    (date(2021, 1, 2), (2020, 53)),
    (date(2021, 1, 3), (2021, 1)),
    (date(2024, 1, 1), (2024, 1)),
]

def test_semanas():
    for d, esperado in CONOCIDOS:
        assert casos.semana_epi(d) == esperado, (d, casos.semana_epi(d), esperado)

def test_periodos():
    assert casos.periodo_de_semana(1) == 1
    assert casos.periodo_de_semana(4) == 1
    assert casos.periodo_de_semana(5) == 2
    assert casos.periodo_de_semana(52) == 13
    assert casos.periodo_de_semana(53) == 13

if __name__ == "__main__":
    test_semanas(); test_periodos(); print("Pruebas OK")
