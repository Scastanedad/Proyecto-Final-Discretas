"""
Paso 0 (opcional): extrae los casos de dengue del Atlántico desde los Excel del SIVIGILA.

Entrada : datos/crudos/xlsx/Datos_<AÑO>_210.xlsx  (descargados del Portal SIVIGILA 4.0,
          https://portalsivigila.ins.gov.co/Paginas/Buscador.aspx, evento "Dengue", código 210)
Salida  : datos/crudos/dengue_atlantico_2018_2025.csv

El Atlántico se identifica por COD_DPTO_O == 8 (departamento de ocurrencia/procedencia).
Barranquilla (08001) está incluida dentro del Atlántico en estos archivos.
Los archivos son grandes (2024 pesa ~200 MB), por eso se leen en modo streaming.
"""
from pathlib import Path
import csv
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_XLSX = RAIZ / "datos" / "crudos" / "xlsx"
SALIDA = RAIZ / "datos" / "crudos" / "dengue_atlantico_2018_2025.csv"
ANIOS = range(2018, 2026)
COLUMNAS = ["COD_EVE", "FEC_NOT", "SEMANA", "ANO", "COD_DPTO_O", "COD_MUN_O", "INI_SIN",
            "TIP_CAS", "PAC_HOS", "CON_FIN", "AJUSTE", "nom_est_f_caso",
            "Departamento_ocurrencia", "Municipio_ocurrencia"]


def main():
    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ARCHIVO_ANO"] + COLUMNAS)
        for anio in ANIOS:
            ruta = CARPETA_XLSX / f"Datos_{anio}_210.xlsx"
            hoja = load_workbook(ruta, read_only=True).active
            filas = hoja.iter_rows(values_only=True)
            encabezado = list(next(filas))
            idx = [encabezado.index(c) for c in COLUMNAS]
            i_dpto = encabezado.index("COD_DPTO_O")
            n = 0
            for fila in filas:
                if fila[i_dpto] is not None and int(fila[i_dpto]) == 8:
                    w.writerow([anio] + [fila[i] for i in idx])
                    n += 1
            print(f"{anio}: {n} casos del Atlántico")


if __name__ == "__main__":
    main()
