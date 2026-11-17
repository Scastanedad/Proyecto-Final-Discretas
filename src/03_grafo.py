"""
Paso 3: grafo de municipios del Atlántico.

Entradas:
  datos/crudos/limites_atlantico_mgn2018.geojson   límites municipales (DANE, MGN 2018)
  datos/crudos/coordenadas_municipios.csv           cabeceras (DIVIPOLA)
  datos/crudos/poblacion_atlantico_2018_2025.csv    población (DANE)
  datos/procesados/panel_base.csv                   panel del paso 2
Salidas (datos/procesados/):
  grafo_aristas.csv     a, b, frontera_km, distancia_km, peso_gravedad (normalizado a [0,1])
  grafo_centralidad.csv grado, fuerza, cercania, intermediacion, intermediacion_norm
  panel_grafo.csv       panel_base + presion_vecinos (incidencia ponderada de los vecinos)
Figura: documento/figuras/grafo_atlantico.png

Modelo:
  * Vértices: los 23 municipios.
  * Arista {a,b} si los municipios comparten frontera de al menos FRONTERA_MIN_KM.
    (Contactos más cortos son esquinas o artefactos de la cartografía.)
  * Peso de gravedad: w(a,b) = Pa·Pb / d(a,b)², con P = población promedio de los años de
    entrenamiento y d = distancia entre cabeceras (km). Se normaliza dividiendo por el máximo.
"""
import itertools, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
from shapely.geometry import shape
import grafo_lib as gl

RAIZ = Path(__file__).resolve().parents[1]
CRUDOS, PROC = RAIZ / "datos" / "crudos", RAIZ / "datos" / "procesados"
FIG = RAIZ / "documento" / "figuras"
FRONTERA_MIN_KM = 1.0
KM_POR_GRADO = 111.0                      # aproximación válida a la latitud del Atlántico (~11° N)
ANIOS_ENTRENAMIENTO = [2018, 2019, 2021, 2022, 2023]


def aristas_por_frontera():
    g = json.loads((CRUDOS / "limites_atlantico_mgn2018.geojson").read_text(encoding="utf-8"))
    geo = {8000 + int(f["properties"]["MPIO_CCDGO"]): shape(f["geometry"]) for f in g["features"]}
    filas = []
    for a, b in itertools.combinations(sorted(geo), 2):
        if geo[a].distance(geo[b]) * KM_POR_GRADO > 0.5:
            continue
        # Longitud de frontera compartida: intersección de los polígonos ligeramente engrosados
        inter = geo[a].buffer(0.0005).intersection(geo[b].buffer(0.0005))
        frontera = inter.length / 2 * KM_POR_GRADO
        filas.append((a, b, round(frontera, 2)))
    return pd.DataFrame(filas, columns=["a", "b", "frontera_km"])


def main():
    coords = pd.read_csv(CRUDOS / "coordenadas_municipios.csv").set_index("cod_mun")
    pob = pd.read_csv(CRUDOS / "poblacion_atlantico_2018_2025.csv")
    P = pob[pob["anio"].isin(ANIOS_ENTRENAMIENTO)].groupby("cod_mun")["poblacion_total"].mean()
    nombres = coords["municipio"].to_dict()

    contactos = aristas_por_frontera()
    descartadas = contactos[contactos["frontera_km"] < FRONTERA_MIN_KM]
    ar = contactos[contactos["frontera_km"] >= FRONTERA_MIN_KM].copy()
    ar["distancia_km"] = [round(gl.haversine_km(coords.at[a, "latitud"], coords.at[a, "longitud"],
                                                coords.at[b, "latitud"], coords.at[b, "longitud"]), 2)
                          for a, b in zip(ar["a"], ar["b"])]
    ar["peso_bruto"] = [P[a] * P[b] / d ** 2 for a, b, d in zip(ar["a"], ar["b"], ar["distancia_km"])]
    ar["peso_gravedad"] = (ar["peso_bruto"] / ar["peso_bruto"].max()).round(6)
    ar["mun_a"], ar["mun_b"] = ar["a"].map(nombres), ar["b"].map(nombres)
    ar = ar.drop(columns="peso_bruto")
    ar.to_csv(PROC / "grafo_aristas.csv", index=False)
    print(f"Contactos entre polígonos: {len(contactos)} | descartados (< {FRONTERA_MIN_KM} km): "
          f"{len(descartadas)} | aristas: {len(ar)}")
    for _, r in descartadas.iterrows():
        print(f"   descartado: {nombres[r.a]} – {nombres[r.b]} ({r.frontera_km} km)")

    nodos = list(coords.index)
    ady = gl.lista_adyacencia(nodos, zip(ar["a"], ar["b"]))
    peso = {}
    for a, b, w in zip(ar["a"], ar["b"], ar["peso_gravedad"]):
        peso[(a, b)] = peso[(b, a)] = w
    assert gl.es_conexo(ady), "El grafo debería ser conexo"

    cen = pd.DataFrame({
        "municipio": pd.Series(nombres),
        "grado": pd.Series(gl.grado(ady)),
        "fuerza": pd.Series(gl.fuerza(ady, peso)).round(4),
        "cercania": pd.Series(gl.cercania(ady)).round(4),
        "intermediacion": pd.Series(gl.intermediacion(ady)).round(3),
        "intermediacion_norm": pd.Series(gl.intermediacion(ady, normalizada=True)).round(4),
    })
    cen.index.name = "cod_mun"
    cen.sort_values("intermediacion", ascending=False).to_csv(PROC / "grafo_centralidad.csv")
    print(f"Nodos: {len(nodos)} | aristas: {len(ar)} | conexo: sí")
    print(cen.sort_values("intermediacion", ascending=False).head(6).to_string())

    # Presión de contagio de los vecinos, periodo por periodo
    panel = pd.read_csv(PROC / "panel_base.csv")
    partes = []
    for (anio, per), g in panel.groupby(["anio", "periodo"]):
        inc = dict(zip(g["cod_mun"], g["incidencia_100k"]))
        pv = gl.presion_vecinos(ady, peso, inc)
        partes.append(g.assign(presion_vecinos=g["cod_mun"].map(pv).round(3)))
    panel = pd.concat(partes).sort_values(["anio", "periodo", "cod_mun"])
    panel.to_csv(PROC / "panel_grafo.csv", index=False)
    print(f"panel_grafo.csv: {len(panel)} filas")

    dibujar(ar, cen, coords)


def dibujar(ar, cen, coords):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    g = json.loads((CRUDOS / "limites_atlantico_mgn2018.geojson").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(8, 9))
    for f in g["features"]:
        geom = shape(f["geometry"])
        for poly in getattr(geom, "geoms", [geom]):
            x, y = poly.exterior.xy
            ax.fill(x, y, color="#eef2f5", ec="#9aa8b4", lw=0.6)
    wmax = ar["peso_gravedad"].max()
    for _, r in ar.iterrows():
        ax.plot([coords.at[r.a, "longitud"], coords.at[r.b, "longitud"]],
                [coords.at[r.a, "latitud"], coords.at[r.b, "latitud"]],
                color="#1f5f8b", lw=0.6 + 4 * (r.peso_gravedad / wmax) ** 0.5, alpha=0.7, zorder=2)
    for cod, r in cen.iterrows():
        ax.scatter(coords.at[cod, "longitud"], coords.at[cod, "latitud"],
                   s=40 + 12 * r.intermediacion, color="#d9822b", ec="black", lw=0.5, zorder=3)
        ax.annotate(r.municipio.title(), (coords.at[cod, "longitud"], coords.at[cod, "latitud"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points", zorder=4)
    ax.set_title("Grafo de municipios del Atlántico\n"
                 "aristas = frontera compartida (grosor ∝ peso de gravedad); "
                 "tamaño del nodo ∝ intermediación", fontsize=9)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(FIG / "grafo_atlantico.png", dpi=200, bbox_inches="tight")
    print("Figura: documento/figuras/grafo_atlantico.png")


if __name__ == "__main__":
    main()
