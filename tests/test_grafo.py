"""
Caso de prueba con resultado conocido para el grafo (calculado a mano) y comparación con networkx.

Subgrafo de 5 municipios del área metropolitana, con las aristas reales del grafo del proyecto:

        Puerto Colombia (PCO)
              |
        Barranquilla (BAQ)
           /        \\
     Galapa (GAL) — Soledad (SOL)
           \\        /
           Malambo (MAL)

Aristas: BAQ–PCO, BAQ–GAL, BAQ–SOL, GAL–SOL, GAL–MAL, SOL–MAL   (6 aristas, 5 nodos)

Cálculo a mano
--------------
Grado:      BAQ 3, SOL 3, GAL 3, MAL 2, PCO 1

Cercanía C(v) = (n-1) / Σ d(v,u), con n-1 = 4:
  BAQ: d = 1(SOL)+1(GAL)+1(PCO)+2(MAL) = 5  -> 4/5 = 0.8
  SOL: 1(BAQ)+1(GAL)+1(MAL)+2(PCO)     = 5  -> 0.8
  GAL: igual que SOL                         -> 0.8
  MAL: 1(SOL)+1(GAL)+2(BAQ)+3(PCO)     = 7  -> 4/7 ≈ 0.5714
  PCO: 1(BAQ)+2(SOL)+2(GAL)+3(MAL)     = 8  -> 0.5

Intermediación (pares no adyacentes y sus caminos más cortos):
  PCO–SOL: PCO-BAQ-SOL                          -> BAQ +1
  PCO–GAL: PCO-BAQ-GAL                          -> BAQ +1
  PCO–MAL: PCO-BAQ-SOL-MAL y PCO-BAQ-GAL-MAL    -> BAQ +1, SOL +1/2, GAL +1/2
  BAQ–MAL: BAQ-SOL-MAL y BAQ-GAL-MAL            -> SOL +1/2, GAL +1/2
  Total: BAQ 3, SOL 1, GAL 1, MAL 0, PCO 0
  Normalizada (÷ (n-1)(n-2)/2 = 6): BAQ 0.5, SOL 1/6, GAL 1/6

Presión de vecinos con pesos inventados w(BAQ,SOL)=1, w(BAQ,GAL)=0.5, w(BAQ,PCO)=0.5,
el resto 0.25, e incidencias BAQ=10, SOL=20, GAL=0, MAL=40, PCO=4:
  P(BAQ) = (1·20 + 0.5·0 + 0.5·4) / (1+0.5+0.5) = 22/2 = 11
  P(MAL) = (0.25·0 + 0.25·20) / 0.5 = 10
  P(PCO) = (0.5·10) / 0.5 = 10
"""
import sys
from pathlib import Path
import pandas as pd
import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import grafo_lib as gl

NODOS = ["BAQ", "SOL", "GAL", "MAL", "PCO"]
ARISTAS = [("BAQ", "PCO"), ("BAQ", "GAL"), ("BAQ", "SOL"), ("GAL", "SOL"), ("GAL", "MAL"), ("SOL", "MAL")]
ADY = gl.lista_adyacencia(NODOS, ARISTAS)
cerca = lambda a, b: abs(a - b) < 1e-9


def test_grado():
    assert gl.grado(ADY) == {"BAQ": 3, "SOL": 3, "GAL": 3, "MAL": 2, "PCO": 1}


def test_cercania():
    esperado = {"BAQ": 0.8, "SOL": 0.8, "GAL": 0.8, "MAL": 4 / 7, "PCO": 0.5}
    obtenido = gl.cercania(ADY)
    assert all(cerca(obtenido[v], esperado[v]) for v in NODOS), obtenido


def test_intermediacion():
    esperado = {"BAQ": 3, "SOL": 1, "GAL": 1, "MAL": 0, "PCO": 0}
    obtenido = gl.intermediacion(ADY)
    assert all(cerca(obtenido[v], esperado[v]) for v in NODOS), obtenido
    norm = gl.intermediacion(ADY, normalizada=True)
    assert cerca(norm["BAQ"], 0.5) and cerca(norm["SOL"], 1 / 6)


def test_presion_vecinos():
    w = {}
    for a, b in ARISTAS:
        w[(a, b)] = w[(b, a)] = 0.25
    for a, b, v in [("BAQ", "SOL", 1), ("BAQ", "GAL", 0.5), ("BAQ", "PCO", 0.5)]:
        w[(a, b)] = w[(b, a)] = v
    inc = {"BAQ": 10, "SOL": 20, "GAL": 0, "MAL": 40, "PCO": 4}
    p = gl.presion_vecinos(ADY, w, inc)
    assert cerca(p["BAQ"], 11) and cerca(p["MAL"], 10) and cerca(p["PCO"], 10), p


def test_contra_networkx_grafo_completo():
    """Nuestros algoritmos deben coincidir con networkx en el grafo real de 23 municipios."""
    ar = pd.read_csv(Path(__file__).resolve().parents[1] / "datos" / "procesados" / "grafo_aristas.csv")
    nodos = sorted(set(ar["a"]) | set(ar["b"]))
    ady = gl.lista_adyacencia(nodos, zip(ar["a"], ar["b"]))
    G = nx.Graph(); G.add_nodes_from(nodos); G.add_edges_from(zip(ar["a"], ar["b"]))
    b_nx, c_nx = nx.betweenness_centrality(G, normalized=False), nx.closeness_centrality(G)
    b, c = gl.intermediacion(ady), gl.cercania(ady)
    assert all(cerca(b[v], b_nx[v]) for v in nodos)
    assert all(cerca(c[v], c_nx[v]) for v in nodos)


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f(); print("OK ", nombre)
