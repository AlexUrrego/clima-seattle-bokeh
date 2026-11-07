# Explorador interactivo del clima de Seattle con Bokeh

Visualización interactiva del clima diario de Seattle entre 2012 y 2015, hecha con **Bokeh**. Genera un archivo HTML autocontenido que funciona sin servidor ni conexión a internet.

**[Ver demo](https://TU_USUARIO.github.io/clima-seattle-bokeh/visualizacion_clima_seattle.html)**

## Qué muestra este proyecto

- Varias vistas **vinculadas**: serie temporal, diagrama de dispersión, gráfico de barras y panel de resumen.
- Interacciones programadas con `CustomJS`, por lo que funcionan en el navegador sin necesidad de un servidor.
- Selección en dos sentidos: lo que se elige en un gráfico actualiza los demás.
- Uso de `RangeTool` para navegar por la ventana de tiempo.

## Interacciones

| Interacción                              | Qué hace                                                               |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| Menú de año                              | Filtra los datos por año                                               |
| Botones de tipo de clima                 | Muestra solo los tipos elegidos (sol, niebla, llovizna, lluvia, nieve) |
| Deslizador                               | Cambia la ventana del promedio móvil (1 a 60 días)                     |
| Selección por caja en la serie temporal  | Resalta esos días en la dispersión y recalcula barras y resumen        |
| Lazo o caja en el diagrama de dispersión | Actualiza las demás vistas                                             |
| Hover, zoom, paneo y reset               | Herramientas de Bokeh                                                  |

## Datos

`clima_seattle.csv` contiene **1.461 registros diarios** (2012-2015) con las columnas `date`, `precipitation` (mm), `temp_max` (°C), `temp_min` (°C), `wind` (m/s) y `weather`. Proviene del repositorio público `vega-datasets`.

## Cómo ejecutarlo

**Requisito:** Python 3.

```
pip install -r requirements.txt
python visualizacion_clima_seattle.py
```

Esto genera `visualizacion_clima_seattle.html` y lo abre en el navegador. Para generarlo sin abrirlo:

```
python visualizacion_clima_seattle.py --no-abrir
```
