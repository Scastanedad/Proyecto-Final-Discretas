"""
Paso 7: figuras descriptivas para el documento.
Salidas: documento/figuras/estacionalidad.png, documento/figuras/casos_por_anio.png
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1]
PROC, FIG = RAIZ / "datos" / "procesados", RAIZ / "documento" / "figuras"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    p = pd.read_csv(PROC / "panel_base.csv")
    q = p[p.anio != 2020].groupby("periodo")[["lluvia_mm", "incidencia_100k"]].mean()
    fig, ax1 = plt.subplots(figsize=(8, 3.6))
    ax1.bar(q.index, q["lluvia_mm"], color="#9cc3e0", label="Lluvia (mm por periodo)")
    ax1.set_xlabel("Periodo epidemiológico (4 semanas)"); ax1.set_ylabel("Lluvia promedio (mm)")
    ax1.set_xticks(range(1, 14))
    ax2 = ax1.twinx()
    ax2.plot(q.index, q["incidencia_100k"], color="#d9822b", marker="o", lw=2, label="Incidencia de dengue")
    ax2.set_ylabel("Incidencia promedio (por 100 mil hab.)")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper left")
    ax1.set_title("Estacionalidad: la incidencia sube 2–3 periodos después de la lluvia "
                  "(promedio 2018–2025 sin 2020, 23 municipios)", fontsize=9)
    fig.savefig(FIG / "estacionalidad.png", dpi=200, bbox_inches="tight"); plt.close(fig)

    c = pd.read_csv(PROC / "casos_mun_periodo.csv")
    t = c.assign(grupo=c["municipio"].where(c["municipio"].isin(["BARRANQUILLA", "SOLEDAD"]), "OTROS 21 MUNICIPIOS"))
    t = t.groupby(["anio", "grupo"]).casos.sum().unstack()[["BARRANQUILLA", "SOLEDAD", "OTROS 21 MUNICIPIOS"]]
    ax = t.plot(kind="bar", stacked=True, figsize=(8, 3.4), color=["#1f5f8b", "#9cc3e0", "#d9822b"], rot=0)
    ax.set_xlabel(""); ax.set_ylabel("Casos de dengue")
    ax.set_title("Casos de dengue en el Atlántico por año (SIVIGILA)", fontsize=9)
    ax.legend([s.title() for s in t.columns], fontsize=8)
    plt.savefig(FIG / "casos_por_anio.png", dpi=200, bbox_inches="tight"); plt.close()
    print("Figuras: estacionalidad.png, casos_por_anio.png")


if __name__ == "__main__":
    main()
