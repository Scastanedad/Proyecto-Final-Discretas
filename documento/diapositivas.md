# Diapositivas — Sustentación (10 minutos)

**Proyecto:** Predicción de brotes de dengue en los municipios del Atlántico con un grafo de municipios y una red neuronal
**Curso:** MAT 4021 Matemáticas Discretas — Grupo 4 — Prof. Iván Gómez
**Entrega:** PDF + diapositivas por Brightspace, domingo 15 de noviembre, 11:59 p. m.

> Reglas para armarlas: **una idea por diapositiva**, poco texto (lo que va aquí en "En pantalla"
> es lo máximo), letra grande, y las figuras de `documento/figuras/`. Lo que va en "Qué decir"
> es para el orador, **no** se pone en la diapositiva.

## Reparto y tiempos

| Persona | Diapositivas | Tema | Tiempo |
|---|---|---|---|
| Persona 1 | 1–3 | Problema, impacto y datos | 2:15 |
| Persona 2 | 4–5 | El grafo y los algoritmos | 2:30 |
| Persona 3 | 6–7 | Red neuronal y resultados | 2:30 |
| Persona 4 | 8–11 | Grafo vs. predicción, prioridad, demo y cierre | 2:45 |
| | | **Total** | **10:00** |

⚠️ **El 40 % es individual y todos responden preguntas sobre todo el proyecto.** Cada uno debe
poder explicar cualquier diapositiva, no solo la suya.

---

## Diapositiva 1 — Portada (Persona 1 · 0:15)

**En pantalla**
- Título: *¿Dónde fumigar primero? Predicción de brotes de dengue en el Atlántico con grafos y redes neuronales*
- Nombres de los 4 integrantes · MAT 4021 · Grupo 4 · Prof. Iván Gómez · Uninorte
- Imagen de fondo opcional: `grafo_atlantico.png` en tono suave

**Qué decir**
> "Buenos días. Nuestro proyecto responde una pregunta práctica: si los recursos para fumigar son limitados, ¿en qué municipio del Atlántico conviene intervenir primero?"

---

## Diapositiva 2 — El problema y por qué es de impacto (Persona 1 · 1:00)

**En pantalla**
- **49.308 casos** de dengue en el Atlántico entre 2018 y 2025 (SIVIGILA)
- **2026:** 3.441 casos a la semana 19 y **12 municipios en brote** (Gobernación)
- Tabla corta con las 4 condiciones de impacto:

| Condición | Nuestra respuesta |
|---|---|
| Afecta a alguien | 2,87 millones de habitantes, 23 municipios |
| Hay evidencia | Microdatos oficiales SIVIGILA (INS) |
| Se puede mejorar | % de brotes detectados un periodo antes |
| Se puede modelar | Grafo de municipios + red neuronal |

- Figura: `casos_por_anio.png`

**Qué decir**
> "El dengue es endémico aquí. Hoy se reacciona cuando el brote ya está; queremos anticiparlo cuatro semanas y además decidir el orden de intervención. El contagio no respeta límites municipales, por eso usamos un grafo."

---

## Diapositiva 3 — Datos reales (Persona 1 · 1:00)

**En pantalla**
- 5 fuentes públicas: **SIVIGILA** (casos) · **DANE** (población, límites, coordenadas) · **Open-Meteo** (clima diario)
- Unidad de tiempo: **periodo epidemiológico de 4 semanas** (13 por año, el que usa el INS)
- Panel final: 23 municipios × 13 periodos × 8 años = **2.392 filas**
- Figura: `estacionalidad.png`
- Frase destacada: **"El dengue llega 8–12 semanas después de la lluvia"** (correlación 0,06 sin rezago → 0,30 con 2 periodos)

**Qué decir**
> "Agrupamos por 4 semanas porque con semanas sueltas el 66 % de las celdas eran cero. Miren la figura: la lluvia sube en mayo y el dengue sube dos o tres periodos después. Eso es el ciclo del mosquito, y por eso le damos a la red la lluvia rezagada. Sacamos 2020 del entrenamiento porque la pandemia causó subregistro."

---

## Diapositiva 4 — El grafo (Persona 2 · 1:15)

**En pantalla**
- **G = (V, E, w)**
  - V = 23 municipios
  - {a, b} ∈ E si comparten **≥ 1 km de frontera** → **47 aristas**, grafo conexo
  - w(a, b) = Pₐ·P_b / d² (modelo de gravedad, normalizado)
- Figura grande: `grafo_atlantico.png`
- Recuadro: **Presión de vecinos** = promedio de la incidencia de los vecinos, ponderado por w → entra a la red

**Qué decir**
> "Las aristas no las pusimos a ojo: las calculamos desde los polígonos oficiales del DANE. Descartamos 4 contactos de menos de 300 metros, que eran esquinas. El peso de gravedad dice que dos municipios grandes y cercanos, como Barranquilla y Soledad, se contagian más entre sí."

---

## Diapositiva 5 — Algoritmos y caso de prueba (Persona 2 · 1:15)

**En pantalla**
- Centralidades programadas **por nosotros**: grado, cercanía (BFS), **intermediación (algoritmo de Brandes, O(V·E))**
- Fórmula: B(v) = Σ σₛₜ(v) / σₛₜ
- Subgrafo de 5 municipios (PCO–BAQ–GAL–SOL–MAL) con la tabla calculada a mano (Tabla 4 del documento)
- ✅ Coincide con el cálculo a mano y con NetworkX en el grafo completo · 11 pruebas automáticas pasan
- Resultado: **los puentes son Sabanalarga (0,37) y Baranoa (0,34), no Barranquilla (0,01)**

**Qué decir**
> "La intermediación cuenta cuántos caminos más cortos pasan por un municipio. Ejemplo: Barranquilla tiene intermediación 3 en este subgrafo, porque todo lo que sale de Puerto Colombia pasa por ella. En el grafo real, Barranquilla concentra el 56 % de los casos pero está en el borde; quienes conectan el norte con el sur son Sabanalarga y Baranoa."

---

## Diapositiva 6 — La red neuronal (Persona 3 · 1:15)

**En pantalla**
- Pregunta: **¿habrá brote en el municipio m el próximo periodo?** (sí/no)
- Brote = incidencia > media + 1 DE de ese periodo **y** ≥ 3 casos
- Diagrama de la red: **14 entradas → 16 → 8 → 1** (ReLU, salida sigmoide, Adam, L2)
- Entradas: incidencia (t, t-1, t-2) · lluvia rezagada (t a t-3) · temperatura · humedad · estación · población · **presión de vecinos (grafo)**
- Validación honesta:
  - Entrenamiento 2018–2023 (sin 2020) · Validación 2024 · **Prueba 2025**
  - Umbral elegido con **F2**: sensibilidad pesa el doble
  - 20 semillas

**Qué decir**
> "Dividimos por años, nunca al azar, para que el modelo no vea el futuro. Elegimos el umbral con F2 porque no detectar un brote es peor que una falsa alarma. La prueba de 2025 la usamos una sola vez, al final."

---

## Diapositiva 7 — Resultados (Persona 3 · 1:15)

**En pantalla**
- Figura: `metricas_modelos.png`
- Tabla resumida (prueba 2025):

| Modelo | Detecta brotes | Precisión | AUC-ROC |
|---|---|---|---|
| Persistencia ("si hay brote, seguirá") | 68 % | 0,72 | 0,77 |
| Regresión logística | 85 % | 0,52 | 0,84 |
| **Red neuronal** | **88 %** | 0,51 | 0,83 |

- Mensaje: **detectamos 20 puntos más de brotes que la regla simple**; el costo es más falsas alarmas

**Qué decir**
> "La red detecta el 88 % de los brotes de 2025, contra el 68 % de la regla de persistencia. A cambio, más o menos la mitad de las alertas son falsas: por cada brote real fumigaríamos un municipio de más. Algo honesto: la red empata con la regresión logística; con 1.400 filas no hay datos para que una red le saque ventaja."

---

## Diapositiva 8 — ¿El grafo ayudó a predecir? No. (Persona 4 · 1:00)

**En pantalla**
- Red con grafo − red sin grafo: AUC-PR **−0,005 ± 0,031** → gana solo en **7 de 20 semillas**
- Tampoco ayuda en municipios pequeños (AUC 0,827 vs 0,833)
- ¿Por qué?
  1. La incidencia propia ya resume casi todo
  2. Los brotes son **simultáneos**: mismo clima, misma temporada
  3. Solo vecinos dentro del Atlántico

**Qué decir**
> "Esperábamos que el grafo mejorara la predicción, y no lo hizo. No ajustamos nada para forzarlo: eso sería hacer trampa con los datos de prueba. La razón principal es que en el Atlántico todos los municipios tienen brote casi al mismo tiempo por la misma lluvia. Pero el grafo sí sirve para otra cosa…"

---

## Diapositiva 9 — Donde el grafo sí sirve: prioridad de fumigación (Persona 4 · 0:45)

**En pantalla**
- **Prioridad = P(brote) × (1 + intermediación relativa)**
- Figura: `prioridad_2026_p1.png`
- Top 5 para el periodo 1 de 2026: **1. Sabanalarga · 2. Ponedera · 3. Baranoa · 4. Polonuevo · 5. Galapa**

**Qué decir**
> "Predecir no es lo mismo que decidir. Si dos municipios tienen riesgo parecido, fumigamos primero el que más caminos de contagio corta. Por eso Sabanalarga y Baranoa suben al top 3 aunque su probabilidad no sea la más alta. La centralidad como mucho duplica la prioridad: el riesgo propio manda."

---

## Diapositiva 10 — Demostración del ejecutable (Persona 4 · 0:30)

**En pantalla**
- Terminal con:
  ```
  python src/06_prioridad.py
  python tests/test_grafo.py
  ```
- Mostrar la salida: ranking de prioridad + "OK" de las pruebas

**Qué decir**
> "Aquí el programa: entrena el modelo final, genera el ranking y las pruebas confirman los valores calculados a mano."

💡 **Plan B:** tener una captura de pantalla de la salida por si algo falla en vivo. `06_prioridad.py` tarda ~30 s; si no hay tiempo, mostrar solo las pruebas, que son instantáneas.

---

## Diapositiva 11 — Conclusiones y limitaciones (Persona 4 · 0:30)

**En pantalla**
- ✅ Con datos públicos se anticipa el **88 %** de los brotes un periodo antes
- ✅ La lluvia de hace **8–12 semanas** es la mejor señal climática
- ⚖️ Red neuronal = regresión logística con estos datos
- 🔀 El grafo **no** mejora la predicción, **sí** mejora la decisión: Sabanalarga y Baranoa son los puentes
- ⚠️ Limitaciones: subregistro por pandemia, casos notificados, sin movilidad real, sin vecinos de otros departamentos
- ➡️ Futuro: datos de movilidad real y simulación SIR sobre el grafo

**Qué decir**
> "Gracias. Quedamos atentos a sus preguntas."

---

## Preguntas probables y cómo responderlas

**Sobre el grafo**
- **¿Por qué frontera compartida y no distancia?** Es la definición más simple y verificable de "vecino"; la distancia ya entra en el peso de gravedad.
- **¿Por qué descartaron 4 aristas?** Medían menos de 300 m: esquinas o errores de cartografía. El siguiente contacto mide 2,1 km, así que el corte de 1 km es claro.
- **¿Por qué intermediación y no grado?** El grado dice cuántos vecinos tiene; la intermediación dice cuántas rutas pasan por ahí. Para cortar el contagio importa la segunda.
- **¿Complejidad de Brandes?** O(V·E): un BFS por cada vértice. Con V = 23 y E = 47 es instantáneo.
- **¿Por qué las centralidades no usan pesos?** Se explican y verifican a mano más fácil; los pesos entran en la presión de vecinos.

**Sobre la red y la evaluación**
- **¿Por qué no dividieron los datos al azar?** Porque el modelo vería el futuro: entrenaría con 2025 para predecir 2024.
- **¿Por qué F2 y no exactitud?** Con 15 % de brotes, decir siempre "no" da 85 % de exactitud y no sirve. F2 premia detectar brotes.
- **¿Por qué 20 semillas?** La red cambia según la inicialización; con una sola semilla una diferencia podría ser suerte.
- **¿Por qué la red no supera a la logística?** Pocos datos (~1.400 filas) y relaciones casi lineales. Es un resultado, no un fracaso.
- **¿Qué es el sobremuestreo?** Repetir ejemplos de brote para que la red no aprenda a decir siempre "no".

**Sobre los datos**
- **¿Por qué sacaron 2020?** Desde marzo los casos cayeron de 461 a entre 9 y 27 por periodo en Barranquilla: subregistro por COVID, no menos dengue.
- **¿Por qué 2021 sí?** Tuvo un brote real a fin de año, con 1.585 casos en un periodo; son ejemplos de brote valiosos.
- **¿Por qué el modelo de clima IFS?** ERA5 daba la misma celda a 8 municipios; IFS distingue 20 de 23.
- **¿Se puede verificar el pronóstico de 2026?** Todavía no: el SIVIGILA publica con 6–10 meses de retraso.

**La pregunta difícil**
- **"Si el grafo no mejora la predicción, ¿para qué está?"** Para decidir. La predicción dice *dónde hay riesgo*; el grafo dice *dónde intervenir rinde más*, porque corta más rutas de contagio. Además, medir que no ayuda es parte del método científico: lo probamos con 20 semillas y por grupos de municipios.

---

## Lista de verificación antes de entregar

- [ ] Poner los nombres reales de los integrantes 2, 3 y 4 en `main.tex` (portada) y en la diapositiva 1
- [ ] Compilar `main.tex` (Overleaf o local) y subir el PDF
- [ ] Armar las diapositivas en PowerPoint, Google Slides o Beamer con las figuras de `documento/figuras/`
- [ ] Ensayar con cronómetro: **10 minutos máximo**
- [ ] Probar la demo en el computador de la sustentación (`pip install -r requirements.txt`)
- [ ] Cada integrante lee `BITACORA.md` completa y corre el código al menos una vez
