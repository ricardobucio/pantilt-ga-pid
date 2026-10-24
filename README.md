# Pan-tilt virtual: PID optimizado con Algoritmo Genético
Proyecto de Cómputo Evolutivo (CETYS). Sin hardware todavía: la cámara de la Mac captura el cuadro completo (1280×720) y una **ventana recortada (480×360)** hace de "cámara del pan-tilt". Su centro lo mueven dos **servos simulados** (retardo puro + primer orden + límite de velocidad + límites de ángulo). Un PID por eje centra el objetivo de color; un AG optimiza las 6 ganancias.

## Instalación (MacBook Pro o Mac mini, Apple Silicon)
```bash
brew install uv                       # o: curl -LsSf https://astral.sh/uv/install.sh | sh
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/Desktop/pantilt-ga-pid"
uv venv -p 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```
> iCloud: el `.venv` se sincroniza también; si da problemas en la otra Mac, bórralo y vuelve a crearlo con los comandos de arriba.

## Comandos
| Comando | Qué hace |
|---|---|
| `pytest -q tests` | pruebas unitarias (servo, anti-windup, objetivo perdido, determinismo) |
| `python cli.py sim` | evalúa el PID manual en los escenarios sembrados |
| `python cli.py sim --gains 0.06,0.16,0.0004,0.05,0.15,0.001` | evalúa ganancias propias |
| `python cli.py ga` | corre el AG completo (config) y guarda resultados + comparación |
| `python cli.py ga --gens 5 --pop 12 --seed 1` | AG corto |
| `python cli.py compare` | manual vs mejor AG en escenarios idénticos |
| `python cli.py calibrate` | trackbars HSV con la cámara; `s` guarda en `config/user.json` |
| `python cli.py live` / `python cli.py live-best` | en vivo con ganancias manuales / mejores del AG (`--duration 20` para protocolo repetible) |
| `streamlit run app.py` | **UI completa**: AG, Comparar, Calibrar color, Seguimiento en vivo, Resultados |

### UI (Streamlit)
- **Inicio**: página de presentación (qué es el proyecto, qué es un PID, cómo funciona el AG, cómo leer resultados y cómo usar la app). Muestra la mejor corrida real guardada en `results/` (menor J) y su gráfica de convergencia. El botón morado lleva a la página del AG.
- Estilo: `pantilt/ui.py` (CSS, fuente Inter) y tema claro en `.streamlit/config.toml`.
- **Calibrar color**: sliders H/S/V mín–máx y área mínima, selector de índice de cámara, ▶ Iniciar / ■ Detener; muestra cámara + máscara en vivo. **💾 Guardar** escribe `config/user.json`.
- **Seguimiento en vivo**: ganancias manual / mejor AG (elige la corrida) / personalizadas, duración (0 = hasta Detener). Muestra la vista recortada con objetivo, centro, error, fps y ganancias, el cuadro completo y la gráfica de error. Al terminar o al Detener se libera la cámara y se guarda `results/<fecha>_live_<etiqueta>/` (trace.csv, error.png, summary.json) + fila en `results/index.csv`.
- La cámara se dibuja con `st.image` (no se usa `cv2.imshow` dentro de Streamlit). Las ventanas OpenCV siguen disponibles por CLI (`calibrate`, `live`).

La primera vez macOS pedirá permiso de **cámara** para Terminal/Cursor (Ajustes del Sistema › Privacidad y seguridad › Cámara).

## Estructura
```
config/default.json   parámetros (cámara, HSV, planta, PID, simulación, AG, pesos)
pantilt/plant.py      Plant (interfaz), VirtualPlant, SerialPlant (stub ESP32)
pantilt/pid.py        PID (anti-windup clamping, derivada sobre medición filtrada) + objetivo perdido
pantilt/vision.py     detección HSV, centroide, recorte
pantilt/sim.py        escenarios sembrados (escalones, senoidal, caminatas), ruido, latencia, pérdidas; métricas
pantilt/fitness.py    función objetivo normalizada por el PID manual
pantilt/ga.py         AG real: torneo k=3, BLX-α, mutación gaussiana con σ decreciente, elitismo 2, paro por estancamiento
pantilt/results.py    guardado CSV/JSON/PNG + results/index.csv
pantilt/tracker.py    LiveTracker: lógica en vivo sin GUI (usada por CLI y Streamlit)
pantilt/live.py       modo en vivo por CLI con ventanas OpenCV
app.py  cli.py  tests/  firmware/esp32_pantilt/ (borrador)
results/<fecha-hora>_<tipo>/   salidas de cada corrida
```

## Función objetivo
Para cada escenario s y métrica m: `m_norm = m(candidato) / m(PID manual)` (con piso y tope de 50). 
`J = media_s( Σ w_m · m_norm ) / Σ w_m` → **el PID manual vale J = 1; menor es mejor.**
Métricas: ITAE e IAE (|ex|+|ey|, px·s), tiempo fuera de la banda de ±15 px (s), cruces por cero del error (oscilación), Σ|Δu| (variación de comando, °), fracción de cuadros sin detección. Pesos en `config/default.json → fitness_weights`.

## Pasar al hardware (ESP32)
Todo el control usa la interfaz `Plant.command(pan_deg, tilt_deg, dt)`. Para el pan-tilt real:
1. Sube `firmware/esp32_pantilt` (arduino-cli + librería ESP32Servo).
2. En `live.py` reemplaza `VirtualPlant` por `SerialPlant(port="/dev/cu.usbserial-XXXX")` y usa el cuadro completo de la cámara del pan-tilt en vez del recorte (`ox=oy=0`).
3. Re-identifica `tau`, `dead_time` y `max_rate_dps` con un escalón real y vuelve a correr el AG.

## Honestidad de resultados
Los resultados de simulación describen el **sistema simulado** con los parámetros de `config`. No son mediciones del hardware real.
