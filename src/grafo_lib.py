"""
Algoritmos de grafos implementados a mano (sin librerías de grafos) para el proyecto.

El grafo es NO dirigido y se guarda como lista de adyacencia: dict[nodo] -> set(vecinos).
Las medidas topológicas (grado, cercanía, intermediación) ignoran los pesos: cuentan saltos
entre municipios vecinos. Los pesos de gravedad solo se usan para la "fuerza" y para la
presión de contagio de los vecinos.
"""
from collections import deque
import math


def lista_adyacencia(nodos, aristas):
    ady = {v: set() for v in nodos}
    for a, b in aristas:
        ady[a].add(b)
        ady[b].add(a)
    return ady


def grado(ady):
    """Número de vecinos de cada nodo."""
    return {v: len(ady[v]) for v in ady}


def bfs_distancias(ady, origen):
    """Distancia (en saltos) desde `origen` a cada nodo alcanzable. O(V + E)."""
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        v = cola.popleft()
        for w in ady[v]:
            if w not in dist:
                dist[w] = dist[v] + 1
                cola.append(w)
    return dist


def es_conexo(ady):
    return len(bfs_distancias(ady, next(iter(ady)))) == len(ady)


def cercania(ady):
    """Cercanía C(v) = (n-1) / suma de distancias de v a los demás (grafo conexo)."""
    n = len(ady)
    return {v: (n - 1) / sum(bfs_distancias(ady, v).values()) for v in ady}


def intermediacion(ady, normalizada=False):
    """
    Intermediación (betweenness) con el algoritmo de Brandes (2001), O(V·E).
    B(v) = suma, sobre pares {s,t} con s≠v≠t, de  (caminos más cortos s–t que pasan por v)
                                                  / (caminos más cortos s–t).
    En grafo no dirigido cada par se cuenta una vez (por eso se divide entre 2 al final).
    Normalizada: divide entre (n-1)(n-2)/2, el máximo posible.
    """
    B = {v: 0.0 for v in ady}
    for s in ady:
        pila = []
        predecesores = {v: [] for v in ady}
        sigma = {v: 0 for v in ady}      # número de caminos más cortos desde s
        sigma[s] = 1
        dist = {v: -1 for v in ady}
        dist[s] = 0
        cola = deque([s])
        while cola:                      # BFS que cuenta caminos más cortos
            v = cola.popleft()
            pila.append(v)
            for w in ady[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    cola.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    predecesores[w].append(v)
        delta = {v: 0.0 for v in ady}    # dependencia acumulada
        while pila:                      # se recorre en orden inverso de distancia
            w = pila.pop()
            for v in predecesores[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                B[w] += delta[w]
    B = {v: b / 2 for v, b in B.items()}
    if normalizada:
        n = len(ady)
        escala = (n - 1) * (n - 2) / 2
        B = {v: b / escala for v, b in B.items()}
    return B


def fuerza(ady, peso):
    """Grado ponderado: suma de los pesos de las aristas de cada nodo. peso[(a,b)] simétrico."""
    return {v: sum(peso[(v, w)] for w in ady[v]) for v in ady}


def presion_vecinos(ady, peso, valor):
    """
    Promedio ponderado del `valor` (p. ej. incidencia) de los vecinos de cada nodo:
        P(v) = Σ_w peso(v,w)·valor(w) / Σ_w peso(v,w)
    No incluye el valor del propio nodo.
    """
    out = {}
    for v in ady:
        tot = sum(peso[(v, w)] for w in ady[v])
        out[v] = sum(peso[(v, w)] * valor[w] for w in ady[v]) / tot if tot else 0.0
    return out


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en km sobre la superficie terrestre entre dos puntos (lat/lon en grados)."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
