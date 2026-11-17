"""
Paso 6: análisis por tamaño de municipio, pronóstico y ranking de prioridad de fumigación.

Entradas: datos/procesados/dataset_modelo.csv, dataset_pronostico.csv, grafo_centralidad.csv,
          resultados/metricas_por_semilla.csv
Salidas (resultados/):
  analisis_por_grupo.csv   AUC de la red con/sin grafo en municipios con datos densos vs escasos (2025)
  prioridad_2026_p1.csv    pronóstico para el periodo 1 de 2026 y ranking de prioridad
  figuras en documento/figuras/: metricas_modelos.png, prioridad_2026_p1.png

Prioridad = P(brote) × (1 + I_rel), con I_rel = intermediación / intermediación máxima ∈ [0, 1].
  La centralidad puede, como mucho, duplicar la prioridad de un municipio: el riesgo propio manda,
  y entre dos municipios con riesgo parecido va primero el que más conecta al resto
  (fumigarlo corta más caminos de contagio). Se usa (1 + I_rel) y no I_rel sola para que un
  municipio de alto riesgo con intermediación 0 no quede con prioridad 0.

Modelo final para el pronóstico: la red con grafo (misma arquitectura del paso 5), reentrenada con
TODOS los años etiquetados excepto 2020 (2018–2025), 20 semillas promediadas. El umbral es el
promedio de los umbrales elegidos en validación en el paso 5.
"""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[1]
PROC, RES, FIG = RAIZ / "datos" / "procesados", RAIZ / "resultados", RAIZ / "documento" / "figuras"
def _cargar(n, f):
    s = importlib.util.spec_from_file_location(n, RAIZ / "src" / f); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m
ds, md = _cargar("ds", "04_dataset.py"), _cargar("md", "05_modelo.py")
DENSOS = {8001, 8758, 8433, 8638, 8296, 8078}   # ≤ 12 % de periodos sin casos (calculado en el paso 1)


def ensamble(Xtr, ytr, Xs):
    probs = [[] for _ in Xs]
    for s in range(md.N_SEMILLAS):
        Xb, yb = md.sobremuestrear(Xtr, ytr, s)
        m = md.red(s).fit(Xb, yb)
        for i, X in enumerate(Xs):
            probs[i].append(m.predict_proba(X)[:, 1])
    return [np.mean(p, axis=0) for p in probs]


def analisis_por_grupo(d):
    tr, te = d[d.conjunto == "entrenamiento"], d[d.conjunto == "prueba"]
    ytr = tr.obj_brote.values.astype(int)
    out = []
    probs = {}
    for etiqueta, cols in (("sin grafo", ds.ENTRADAS_SIN_GRAFO), ("con grafo", ds.ENTRADAS)):
        esc = StandardScaler().fit(tr[cols])
        probs[etiqueta] = ensamble(esc.transform(tr[cols]), ytr, [esc.transform(te[cols])])[0]
    for grupo, mask in (("densos (6)", te.cod_mun.isin(DENSOS)), ("escasos (17)", ~te.cod_mun.isin(DENSOS)),
                        ("todos (23)", te.cod_mun.notna())):
        y = te.obj_brote.values[mask.values].astype(int)
        fila = {"grupo": grupo, "filas": int(mask.sum()), "brotes": int(y.sum())}
        for etiqueta in probs:
            p = probs[etiqueta][mask.values]
            fila[f"AUC_ROC {etiqueta}"] = roc_auc_score(y, p)
            fila[f"AUC_PR {etiqueta}"] = average_precision_score(y, p)
        out.append(fila)
    return pd.DataFrame(out).round(3)


def pronostico(d, pron, cen):
    cols = ds.ENTRADAS
    tr = d[d.conjunto != "excluido_2020"]
    esc = StandardScaler().fit(tr[cols])
    p = ensamble(esc.transform(tr[cols]), tr.obj_brote.values.astype(int), [esc.transform(pron[cols])])[0]
    umbral = pd.read_csv(RES / "metricas_por_semilla.csv").query("modelo == 'Red con grafo'")["umbral"].mean()
    r = pron[["cod_mun", "municipio", "obj_anio", "obj_periodo"]].copy()
    r["casos_ultimo_periodo"] = np.expm1(pron["inc_t"]).round(1)  # incidencia por 100 mil del último periodo
    r = r.rename(columns={"casos_ultimo_periodo": "incidencia_ultimo_periodo"})
    r["prob_brote"] = p.round(3)
    r["alerta"] = (p >= umbral).astype(int)
    c = cen.set_index("cod_mun")["intermediacion"]
    r["intermediacion_rel"] = r["cod_mun"].map(c / c.max()).round(3)
    r["prioridad"] = (r["prob_brote"] * (1 + r["intermediacion_rel"])).round(3)
    r = r.sort_values("prioridad", ascending=False).reset_index(drop=True)
    r.index = r.index + 1; r.index.name = "puesto"
    return r, umbral


def figuras(r, umbral):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(RES / "metricas_modelos.csv").query("conjunto == 'prueba'")
    orden = ["Persistencia", "Logística sin grafo", "Logística con grafo", "Red sin grafo", "Red con grafo"]
    m = m.set_index("modelo").loc[orden]
    met = ["sensibilidad", "precision", "F2", "AUC_ROC", "AUC_PR"]
    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(met)); w = 0.16
    colores = ["#9e9e9e", "#9cc3e0", "#1f5f8b", "#f4b97f", "#d9822b"]
    for i, (mod, col) in enumerate(zip(orden, colores)):
        err = [m.loc[mod].get(k + "_de", 0) if pd.notna(m.loc[mod].get(k + "_de", np.nan)) else 0 for k in met]
        ax.bar(x + (i - 2) * w, m.loc[mod, met], w, yerr=err, color=col, label=mod, capsize=2)
    ax.set_xticks(x); ax.set_xticklabels(["Sensibilidad", "Precisión", "F2", "AUC-ROC", "AUC-PR"])
    ax.set_ylim(0, 1); ax.set_ylabel("Valor en prueba (2025)")
    ax.set_title("Comparación de modelos en el conjunto de prueba (2025)", fontsize=10)
    ax.legend(fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.1)); ax.grid(axis="y", alpha=0.3)
    fig.savefig(FIG / "metricas_modelos.png", dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 6))
    rr = r.iloc[::-1]
    ax.barh(rr["municipio"].str.title(), rr["prob_brote"], color="#9cc3e0", label="P(brote)")
    ax.barh(rr["municipio"].str.title(), rr["prioridad"] - rr["prob_brote"], left=rr["prob_brote"],
            color="#1f5f8b", label="aporte de la intermediación")
    ax.axvline(umbral, color="#d9822b", ls="--", lw=1, label=f"umbral de alerta sobre P(brote) ({umbral:.2f})")
    ax.set_xlabel("Prioridad = P(brote) × (1 + intermediación relativa)")
    ax.set_title(f"Prioridad de fumigación — pronóstico {int(r.obj_anio.iloc[0])}, "
                 f"periodo {int(r.obj_periodo.iloc[0])}", fontsize=10)
    ax.legend(fontsize=7, loc="lower right")
    fig.savefig(FIG / "prioridad_2026_p1.png", dpi=200, bbox_inches="tight"); plt.close(fig)


def main():
    d = pd.read_csv(PROC / "dataset_modelo.csv")
    pron = pd.read_csv(PROC / "dataset_pronostico.csv")
    cen = pd.read_csv(PROC / "grafo_centralidad.csv")
    g = analisis_por_grupo(d)
    g.to_csv(RES / "analisis_por_grupo.csv", index=False)
    print(g.to_string(index=False))
    r, umbral = pronostico(d, pron, cen)
    r.to_csv(RES / "prioridad_2026_p1.csv")
    print(f"\nUmbral de alerta: {umbral:.3f}")
    print(r[["municipio", "incidencia_ultimo_periodo", "prob_brote", "alerta",
             "intermediacion_rel", "prioridad"]].to_string())
    figuras(r, umbral)
    print("Figuras: metricas_modelos.png, prioridad_2026_p1.png")


if __name__ == "__main__":
    main()
