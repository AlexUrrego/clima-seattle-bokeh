"""
Visualización interactiva del clima diario de Seattle (2012-2015) con Bokeh
===========================================================================

Dataset : seattle_weather.csv (1.461 registros diarios; fuente: repositorio público vega-datasets)
Variables: date, precipitation (mm), temp_max (°C), temp_min (°C), wind (m/s), weather (categoría)

Interacciones incluidas
-----------------------
1. Filtro por año (menú desplegable).
2. Filtro por tipo de clima (botones de selección múltiple).
3. Ventana del promedio móvil (deslizador).
4. Selección por caja sobre la serie temporal. Los días elegidos se resaltan
   en el diagrama de dispersión y se recalculan las barras y el panel de
   resumen.
5. Selección por lazo o por caja en el diagrama de dispersión, que actualiza
   las demás vistas (la vinculación funciona en los dos sentidos).
6. Hover con los datos de cada día, zoom, paneo y reset con las herramientas
   de Bokeh.

Uso
---
    pip install bokeh pandas
    python visualizacion_clima_seattle.py

Genera `visualizacion_clima_seattle.html` (autocontenido, funciona sin servidor
ni conexión a Internet) y lo abre en el navegador.
"""

import sys
import pandas as pd

from bokeh.layouts import column, row
from bokeh.models import (
    BoxSelectTool, CategoricalColorMapper, CheckboxButtonGroup, ColumnDataSource,
    CustomJS, Div, HoverTool, LassoSelectTool, Legend, LegendItem, RangeTool,
    Select, Slider,
)
from bokeh.plotting import figure, save, output_file, show
from bokeh.resources import INLINE

CSV = "clima_seattle.csv"
SALIDA = "visualizacion_clima_seattle.html"

# ---------------------------------------------------------------- 1. Datos
df = pd.read_csv(CSV, parse_dates=["date"])
df["temp_avg"] = (df["temp_max"] + df["temp_min"]) / 2
df["year"] = df["date"].dt.year.astype(str)
df["ts"] = df["date"].astype("datetime64[ms]").astype(
    "int64")  # ms desde 1970 (eje datetime de Bokeh)
df["ma"] = df["temp_avg"]                                 # se recalcula en JS

TIPOS = ["sun", "fog", "drizzle", "rain", "snow"]
COLORES = ["#f2a900", "#8a8d91", "#4bb3c9", "#1f5fbf", "#9b59b6"]
ETIQ = {"sun": "Sol", "fog": "Niebla",
        "drizzle": "Llovizna", "rain": "Lluvia", "snow": "Nieve"}
AÑOS = ["Todos"] + sorted(df["year"].unique())

cols = ["ts", "temp_max", "temp_min", "temp_avg",
        "ma", "precipitation", "wind", "weather", "year"]
# datos completos (inmutables)
full = {c: df[c].tolist() for c in cols}
source = ColumnDataSource(data={c: df[c].tolist() for c in cols}, name="src")

# Fuente del gráfico de barras (conteo por tipo de clima)
bar_src = ColumnDataSource(
    data=dict(tipo=[ETIQ[t] for t in TIPOS], cuenta=[0] * 5, color=COLORES), name="bar_src")

cmap = CategoricalColorMapper(factors=TIPOS, palette=COLORES)

# ------------------------------------------- 2. Gráfico principal (serie temporal)
TOOLS = "xpan,xwheel_zoom,reset,save"
p_ts = figure(title="Temperatura diaria (°C): seleccione un rango con la caja para vincular las demás vistas",
              x_axis_type="datetime", height=330, width=1000, tools=TOOLS,
              active_scroll="xwheel_zoom", toolbar_location="above")
p_ts.line("ts", "temp_max", source=source, color="#d1495b",
          alpha=0.35, legend_label="Máx. diaria")
p_ts.line("ts", "temp_min", source=source, color="#2e86ab",
          alpha=0.35, legend_label="Mín. diaria")
p_ts.line("ts", "ma", source=source, color="#222222",
          line_width=2.5, legend_label="Promedio móvil")
pts = p_ts.scatter("ts", "temp_avg", source=source, size=4,
                   color={"field": "weather", "transform": cmap},
                   selection_color={"field": "weather", "transform": cmap},
                   nonselection_alpha=0.12, alpha=0.8)
p_ts.add_tools(BoxSelectTool(dimensions="width", renderers=[pts]))
p_ts.add_tools(HoverTool(renderers=[pts], tooltips=[
    ("Fecha", "@ts{%F}"), ("Clima",
                           "@weather"), ("T. máx", "@temp_max{0.0} °C"),
    ("T. mín", "@temp_min{0.0} °C"), ("Lluvia", "@precipitation{0.0} mm"),
    ("Viento", "@wind{0.0} m/s")], formatters={"@ts": "datetime"}))
p_ts.yaxis.axis_label = "°C"
p_ts.legend.location = "top_left"
p_ts.legend.click_policy = "hide"
p_ts.legend.orientation = "horizontal"

# Vista general con RangeTool (navegación de la ventana de tiempo)
p_rng = figure(height=90, width=1000, x_axis_type="datetime", y_axis_type=None,
               tools="", toolbar_location=None, x_range=(df["ts"].min(), df["ts"].max()))
p_rng.line("ts", "temp_avg", source=source, color="#555", alpha=0.7)
rt = RangeTool(x_range=p_ts.x_range)
rt.overlay.fill_color = "navy"
rt.overlay.fill_alpha = 0.15
p_rng.add_tools(rt)
p_rng.ygrid.grid_line_color = None

# ------------------------------------------- 3. Dispersión (temperatura vs viento)
p_sc = figure(title="Temperatura máxima vs. viento (tamaño = precipitación)",
              height=340, width=500, tools="pan,wheel_zoom,reset", toolbar_location="above")
sc = p_sc.scatter("temp_max", "wind", source=source, alpha=0.7,
                  size="size", color={"field": "weather", "transform": cmap},
                  selection_color={"field": "weather", "transform": cmap},
                  nonselection_alpha=0.08)
p_sc.add_tools(LassoSelectTool(renderers=[sc]), BoxSelectTool(renderers=[sc]))
p_sc.add_tools(HoverTool(renderers=[sc], tooltips=[
    ("Fecha", "@ts{%F}"), ("Clima",
                           "@weather"), ("T. máx", "@temp_max{0.0} °C"),
    ("Viento", "@wind{0.0} m/s"), ("Lluvia", "@precipitation{0.0} mm")],
    formatters={"@ts": "datetime"}))
p_sc.xaxis.axis_label = "Temperatura máxima (°C)"
p_sc.yaxis.axis_label = "Viento (m/s)"
# tamaño del marcador proporcional a la precipitación (raíz para suavizar valores extremos)
source.data["size"] = [4 + (v ** 0.5) * 2.2 for v in df["precipitation"]]
full["size"] = list(source.data["size"])

# ------------------------------------------- 4. Barras (conteo por clima)
p_bar = figure(x_range=[ETIQ[t] for t in TIPOS], title="Días por tipo de clima (según selección)",
               height=340, width=480, tools="", toolbar_location=None)
p_bar.vbar(x="tipo", top="cuenta", width=0.7, source=bar_src, color="color")
p_bar.xgrid.grid_line_color = None
p_bar.y_range.start = 0
p_bar.yaxis.axis_label = "N.º de días"
p_bar.add_tools(HoverTool(tooltips=[("Clima", "@tipo"), ("Días", "@cuenta")]))

# ------------------------------------------- 5. Panel de resumen
resumen = Div(width=1000, height=40, name="resumen",
              styles={"font-size": "14px", "background": "#f4f6f8", "padding": "8px 12px",
                      "border-radius": "6px"})

# ------------------------------------------- 6. Widgets
sel_year = Select(title="Año", value="Todos", options=AÑOS, width=140)
chk_tipo = CheckboxButtonGroup(labels=[ETIQ[t] for t in TIPOS], active=list(range(5)),
                               button_type="primary", width=420)
sld_ma = Slider(title="Ventana del promedio móvil (días)",
                start=1, end=60, step=1, value=14, width=260)

# ------------------------------------------- 7. Lógica JS (sin servidor)
js_filtrar = CustomJS(args=dict(src=source, full=full, sel=sel_year, chk=chk_tipo, sld=sld_ma,
                                tipos=TIPOS, bar=bar_src, div=resumen, p=p_ts, rt=rt),
                      code="""
const n = full.ts.length, w = sld.value;
const año = sel.value, activos = chk.active.map(i => tipos[i]);

// 1) promedio móvil sobre los días del año elegido
const idxAño = [];
for (let i = 0; i < n; i++) if (año === 'Todos' || full.year[i] === año) idxAño.push(i);
const ma = {};
for (let k = 0; k < idxAño.length; k++) {
  let s = 0, c = 0;
  for (let j = Math.max(0, k - w + 1); j <= k; j++) { s += full.temp_avg[idxAño[j]]; c++; }
  ma[idxAño[k]] = s / c;
}
// 2) filtrar por tipo de clima y reconstruir la fuente
const keys = Object.keys(full), out = {};
keys.forEach(k => out[k] = []);
out['ma'] = [];
for (const i of idxAño) {
  if (!activos.includes(full.weather[i])) continue;
  keys.forEach(k => { if (k !== 'ma') out[k].push(full[k][i]); });
  out['ma'].push(ma[i]);
}
src.selected.indices = [];
src.data = out;
// ajustar la ventana temporal (el RangeTool controla el rango del gráfico principal)
let a, b;
if (año === 'Todos') { a = Math.min(...full.ts); b = Math.max(...full.ts); }
else if (out.ts.length) { a = out.ts[0]; b = out.ts[out.ts.length - 1]; }
if (a !== undefined) { setTimeout(() => { p.x_range.setv({start: a, end: b}); rt.overlay.setv({left: a, right: b}); }, 50); }
""")

js_resumen = CustomJS(args=dict(src=source, tipos=TIPOS, bar=bar_src, div=resumen), code="""
const d = src.data, sel = src.selected.indices;
const idx = sel.length ? sel : Array.from(d.ts.keys());
const cnt = {}; tipos.forEach(t => cnt[t] = 0);
let sT = 0, sP = 0, sW = 0, mx = -1e9, mn = 1e9;
for (const i of idx) {
  cnt[d.weather[i]]++; sT += d.temp_avg[i]; sP += d.precipitation[i]; sW += d.wind[i];
  mx = Math.max(mx, d.temp_max[i]); mn = Math.min(mn, d.temp_min[i]);
}
const m = idx.length || 1;
bar.data = Object.assign({}, bar.data, {cuenta: tipos.map(t => cnt[t])});
const alcance = sel.length ? `<b>${sel.length}</b> días seleccionados` : `<b>${idx.length}</b> días (sin selección: se muestran todos)`;
div.text = `${alcance} &nbsp;|&nbsp; T. media: <b>${(sT/m).toFixed(1)} °C</b> &nbsp;|&nbsp; Máx. / mín. absolutas: <b>${idx.length ? mx.toFixed(1) : '–'} / ${idx.length ? mn.toFixed(1) : '–'} °C</b> &nbsp;|&nbsp; Lluvia total: <b>${sP.toFixed(0)} mm</b> &nbsp;|&nbsp; Viento medio: <b>${(sW/m).toFixed(1)} m/s</b>`;
""")

for w in (sel_year, chk_tipo, sld_ma):
    w.js_on_change("value" if w is not chk_tipo else "active", js_filtrar)
source.selected.js_on_change("indices", js_resumen)
source.js_on_change("data", js_resumen)

# ------------------------------------------- 8. Leyenda de colores (HTML)
leyenda = Div(text="<b>Color = clima:</b> " + " &nbsp; ".join(
    f"<span style='color:{c}'>●</span> {ETIQ[t]}" for t, c in zip(TIPOS, COLORES)))
titulo = Div(text="<h2 style='margin:0'>Explorador interactivo del clima de Seattle (2012-2015)</h2>"
                  "<span style='color:#555'>Seleccione días en la serie temporal o en el diagrama de dispersión; "
                  "todas las vistas se actualizan.</span>", width=1000)

controles = row(sel_year, sld_ma, column(
    Div(text="<b>Tipos de clima</b>", margin=(0, 0, 0, 0)), chk_tipo))
layout = column(titulo, controles, leyenda, p_ts,
                p_rng, resumen, row(p_sc, p_bar))

# Inicializar valores (barras/resumen) con todos los datos
bar_src.data["cuenta"] = [int((df["weather"] == t).sum()) for t in TIPOS]
resumen.text = (f"<b>{len(df)}</b> días (sin selección: se muestran todos) | T. media: "
                f"<b>{df['temp_avg'].mean():.1f} °C</b> | Lluvia total: <b>{df['precipitation'].sum():.0f} mm</b> | "
                f"Viento medio: <b>{df['wind'].mean():.1f} m/s</b>")

output_file(SALIDA, title="Clima de Seattle - Bokeh")
save(layout, resources=INLINE)
print(f"Archivo generado: {SALIDA}")
if "--no-abrir" not in sys.argv:
    show(layout)
