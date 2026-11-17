"""
Paso 5: entrenamiento y comparación de modelos.

Entrada : datos/procesados/dataset_modelo.csv  (paso 4)
Salidas : resultados/metricas_modelos.csv      métricas en validación (2024) y prueba (2025)
          resultados/metricas_por_semilla.csv  red con/sin grafo, una fila por semilla
          resultados/predicciones_prueba.csv   probabilidades de la red completa en 2025
          resultados/modelo_red.pkl            red completa (semilla 0) + escalador + umbral

Modelos comparados (mismo objetivo: ¿brote en el periodo siguiente?):
  1. Persistencia:  "si hay brote ahora, habrá brote en el siguiente periodo".
  2. Regresión logística sin grafo / con grafo.
  3. Red neuronal (perceptrón multicapa) sin grafo / con grafo.
     Arquitectura: entradas -> 16 (ReLU) -> 8 (ReLU) -> 1 (sigmoide), optimizador Adam,
     regularización L2 (alpha), 400 épocas máx. con parada temprana interna.

Decisiones:
  * Desbalance de clases: en entrenamiento se repiten (sobremuestreo) los ejemplos de brote hasta
    igualar a los de no-brote. La logística usa class_weight="balanced" (equivalente).
  * Escalado: media y desviación calculadas SOLO con entrenamiento.
  * Umbral de decisión: se elige en VALIDACIÓN maximizando F2 (pondera la sensibilidad 2 veces más
    que la precisión: no detectar un brote es peor que una falsa alarma). La prueba (2025) no se toca
    hasta el final.
  * Variabilidad: la red se entrena con N_SEMILLAS semillas distintas y se reporta media ± DE.
"""
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, fbeta_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import importlib.util

RAIZ = Path(__file__).resolve().parents[1]
PROC, RES = RAIZ / "datos" / "procesados", RAIZ / "resultados"
RES.mkdir(exist_ok=True)
_spec = importlib.util.spec_from_file_location("ds", RAIZ / "src" / "04_dataset.py")
ds = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ds)
N_SEMILLAS = 20
UMBRALES = np.round(np.arange(0.05, 0.96, 0.01), 2)


def metricas(y, prob, umbral):
    pred = (prob >= umbral).astype(int)
    return {"sensibilidad": recall_score(y, pred, zero_division=0),
            "precision": precision_score(y, pred, zero_division=0),
            "F1": fbeta_score(y, pred, beta=1, zero_division=0),
            "F2": fbeta_score(y, pred, beta=2, zero_division=0),
            "AUC_ROC": roc_auc_score(y, prob) if len(set(prob)) > 1 else 0.5,
            "AUC_PR": average_precision_score(y, prob)}


def mejor_umbral(y, prob):
    f2 = [fbeta_score(y, (prob >= u).astype(int), beta=2, zero_division=0) for u in UMBRALES]
    return float(UMBRALES[int(np.argmax(f2))])


def sobremuestrear(X, y, semilla):
    rng = np.random.default_rng(semilla)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    extra = rng.choice(pos, size=len(neg) - len(pos), replace=True)
    idx = rng.permutation(np.concatenate([neg, pos, extra]))
    return X[idx], y[idx]


def red(semilla):
    return MLPClassifier(hidden_layer_sizes=(16, 8), activation="relu", solver="adam", alpha=1e-2,
                         learning_rate_init=1e-3, max_iter=400, early_stopping=True,
                         validation_fraction=0.15, n_iter_no_change=25, random_state=semilla)


def main():
    d = pd.read_csv(PROC / "dataset_modelo.csv")
    tr, va, te = (d[d.conjunto == c] for c in ("entrenamiento", "validacion", "prueba"))
    ytr, yva, yte = (x["obj_brote"].values.astype(int) for x in (tr, va, te))
    filas, por_semilla = [], []

    # 1. Persistencia (no se entrena; su "probabilidad" es 0 o 1)
    for nombre, x, y in (("validacion", va, yva), ("prueba", te, yte)):
        filas.append({"modelo": "Persistencia", "conjunto": nombre, "umbral": 0.5,
                      **metricas(y, x["brote_actual"].values.astype(float), 0.5)})

    for etiqueta, cols in (("sin grafo", ds.ENTRADAS_SIN_GRAFO), ("con grafo", ds.ENTRADAS)):
        esc = StandardScaler().fit(tr[cols])
        Xtr, Xva, Xte = (esc.transform(x[cols]) for x in (tr, va, te))

        # 2. Regresión logística
        lr = LogisticRegression(class_weight="balanced", max_iter=5000, C=1.0).fit(Xtr, ytr)
        pva, pte = lr.predict_proba(Xva)[:, 1], lr.predict_proba(Xte)[:, 1]
        u = mejor_umbral(yva, pva)
        for nombre, y, p in (("validacion", yva, pva), ("prueba", yte, pte)):
            filas.append({"modelo": f"Logística {etiqueta}", "conjunto": nombre, "umbral": u,
                          **metricas(y, p, u)})

        # 3. Red neuronal, varias semillas
        acumulado = []
        for s in range(N_SEMILLAS):
            Xb, yb = sobremuestrear(Xtr, ytr, s)
            m = red(s).fit(Xb, yb)
            pva, pte = m.predict_proba(Xva)[:, 1], m.predict_proba(Xte)[:, 1]
            u = mejor_umbral(yva, pva)
            mt, mv = metricas(yte, pte, u), metricas(yva, pva, u)
            por_semilla.append({"modelo": f"Red {etiqueta}", "semilla": s, "umbral": u,
                                **{f"val_{k}": v for k, v in mv.items()},
                                **{f"prueba_{k}": v for k, v in mt.items()}})
            acumulado.append(pte)
            if etiqueta == "con grafo" and s == 0:
                pickle.dump({"modelo": m, "escalador": esc, "umbral": u, "entradas": cols},
                            open(RES / "modelo_red.pkl", "wb"))
        if etiqueta == "con grafo":
            te_out = te[["cod_mun", "municipio", "obj_anio", "obj_periodo", "obj_casos", "obj_brote"]].copy()
            te_out["prob_brote"] = np.mean(acumulado, axis=0).round(4)
            te_out.to_csv(RES / "predicciones_prueba.csv", index=False)

    ps = pd.DataFrame(por_semilla)
    ps.to_csv(RES / "metricas_por_semilla.csv", index=False)
    for nombre, g in ps.groupby("modelo"):
        for conj, pref in (("validacion", "val_"), ("prueba", "prueba_")):
            fila = {"modelo": nombre, "conjunto": conj, "umbral": round(g["umbral"].mean(), 3)}
            for k in ("sensibilidad", "precision", "F1", "F2", "AUC_ROC", "AUC_PR"):
                fila[k] = g[pref + k].mean()
                fila[k + "_de"] = g[pref + k].std()
            filas.append(fila)

    res = pd.DataFrame(filas).round(3)
    res.to_csv(RES / "metricas_modelos.csv", index=False)
    cols = ["modelo", "umbral", "sensibilidad", "precision", "F1", "F2", "AUC_ROC", "AUC_PR"]
    for conj in ("validacion", "prueba"):
        print(f"\n=== {conj.upper()} ===")
        print(res[res.conjunto == conj][cols].to_string(index=False))
    # Comparación pareada red con vs sin grafo (misma semilla)
    a = ps[ps.modelo == "Red con grafo"].set_index("semilla")
    b = ps[ps.modelo == "Red sin grafo"].set_index("semilla")
    for k in ("prueba_AUC_PR", "prueba_AUC_ROC", "prueba_F2"):
        dif = a[k] - b[k]
        print(f"{k}: con - sin grafo = {dif.mean():+.3f} ± {dif.std():.3f} "
              f"(gana con grafo en {int((dif > 0).sum())}/{len(dif)} semillas)")


if __name__ == "__main__":
    main()
