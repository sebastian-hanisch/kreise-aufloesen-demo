"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Hauptbild ist das Bogendiagramm aus den Stücken 1 und 2: die Aufgaben stehen in ihrer verdeckten Wunschreihenfolge auf einer Linie, Beziehungen nach vorn laufen
als Bögen darüber, Widersprüche (gegen die Reihenfolge) als Bögen darunter; die Pfeilrichtung folgt daraus. Gestrichene Beziehungen sind rot gepunktet,
gestrichene Aufgaben rot durchgekreuzt."""

import math

import plotly.graph_objects as go

import kau_constants as C
from kau_evaluation import _dec, label

ARC_POINTS = 14


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _arc(xa, xb, n, upward, points=ARC_POINTS):
    span = abs(xb - xa)
    h = max(0.07, span / max(1, n - 1)) * (1 if upward else -1)
    xs = [xa + (xb - xa) * i / points for i in range(points + 1)]
    ys = [h * math.sin(math.pi * i / points) for i in range(points + 1)]
    return xs, ys


def _trace(edges, pos, n, color, width, dash=None):
    xs, ys = [], []
    for a, b in edges:
        ax, ay = _arc(pos[a], pos[b], n, pos[a] < pos[b])
        xs += ax + [None]
        ys += ay + [None]
    if not xs:
        return None
    line = dict(color=color, width=width)
    if dash:
        line["dash"] = dash
    return go.Scatter(x=xs, y=ys, mode="lines", line=line, hoverinfo="skip", showlegend=False)


def build_arc_figure(inst, struck_edges=(), struck_vertices=(), height=None):
    """Bogendiagramm der Aufgaben in Wunschreihenfolge; `struck_edges` gepunktet in Rot, `struck_vertices` durchgekreuzt (ihre Beziehungen blass)."""
    n = inst.n
    pos = inst.position()
    fig = go.Figure()
    gone_edges = set(struck_edges)
    gone_nodes = set(struck_vertices)
    edges = [(a, b) for a in range(n) for b in inst.adj[a]]
    width = 1.2 if n <= 40 else (0.8 if n <= 100 else 0.5)
    pale = [e for e in edges if e[0] in gone_nodes or e[1] in gone_nodes]
    plain = [e for e in edges if e not in gone_edges and e not in set(pale)]
    for up in (True, False):
        tr = _trace([e for e in plain if (pos[e[0]] < pos[e[1]]) == up], pos, n, C.COLOR_FORWARD if up else C.COLOR_BACKWARD, width)
        if tr:
            fig.add_trace(tr)
    tr = _trace(pale, pos, n, "rgba(150,150,150,0.25)", width)
    if tr:
        fig.add_trace(tr)
    tr = _trace(sorted(gone_edges), pos, n, C.COLOR_STRUCK, 3.2, dash="dot")
    if tr:
        fig.add_trace(tr)
    labelled = n <= 40
    nodes = list(range(n))
    fig.add_trace(go.Scatter(
        x=[pos[v] for v in nodes], y=[0] * n, mode="markers+text" if labelled else "markers",
        marker=dict(size=22 if labelled else (9 if n <= 100 else 5), color=C.COLOR_NODE,
                    line=dict(color=[C.COLOR_STRUCK if v in gone_nodes else "#333" for v in nodes], width=[3 if v in gone_nodes else 1 for v in nodes])),
        text=[label(v) for v in nodes] if labelled else None, textposition="middle center", textfont=dict(color="#222", size=11),
        hovertext=[f"Aufgabe {label(v)}: Platz {pos[v] + 1} der Wunschreihenfolge" for v in nodes], hoverinfo="text", showlegend=False))
    if gone_nodes:
        gone = sorted(gone_nodes)
        fig.add_trace(go.Scatter(x=[pos[v] for v in gone], y=[0] * len(gone), mode="markers", marker=dict(symbol="x", size=26 if labelled else 14, color=C.COLOR_STRUCK, line=dict(width=3, color=C.COLOR_STRUCK)),
                                 hoverinfo="skip", showlegend=False))
    fig.update_xaxes(title_text="Wunschreihenfolge (verdeckt) →", range=[-0.8, n - 0.2], showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-1.12, 1.12], showticklabels=False, showgrid=False, zeroline=True, zerolinecolor="rgba(128,128,128,0.35)")
    _base(fig, height or 380)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=40))
    return fig


def build_compare_figure(entries):
    """Zahl der gestrichenen Beziehungen je Verfahren: `entries` ist eine Liste (Name, Größe, Farbe oder None)."""
    palette = [C.COLOR_BAR2, C.COLOR_LINE, C.COLOR_BAR3, C.COLOR_BAR]
    names = [e[0] for e in entries]
    fig = go.Figure(go.Bar(x=names, y=[e[1] for e in entries], marker_color=[e[2] or palette[i % len(palette)] for i, e in enumerate(entries)],
                           text=[str(e[1]) for e in entries], textposition="outside", cliponaxis=False))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="gestrichene Beziehungen")
    return _base(fig, 340)


def build_components_figure(components):
    """Größe der Komponenten, in denen Kreise liegen können (nur diese muss der Löser lösen)."""
    sizes = sorted((len(c) for c in components), reverse=True)
    xs = [f"{i + 1}" for i in range(len(sizes))]
    fig = go.Figure(go.Bar(x=xs, y=sizes, marker_color=C.COLOR_BAR, hovertemplate="Komponente %{x}: %{y} Aufgaben<extra></extra>"))
    fig.update_xaxes(title_text="Komponente (nach Größe)", type="category")
    fig.update_yaxes(title_text="Aufgaben in der Komponente")
    return _base(fig, 300)


def build_rules_figure(n_total, on_cycles, steps):
    """Aufgaben im Rest nach jedem Schritt der Reduktionsregeln."""
    xs = ["im Plan", "in Komponenten mit Kreis"] + [s[0] for s in steps[:1]] + [f"Runde {i}" for i in range(1, len(steps))]
    ys = [n_total, on_cycles] + [s[1] for s in steps]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=[C.COLOR_LINE, C.COLOR_LINE, C.COLOR_BAR2] + [C.COLOR_BAR] * (len(xs) - 3), text=[str(y) for y in ys], textposition="outside", cliponaxis=False))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Aufgaben")
    return _base(fig, 340)


def build_compare_rows_figure(rows):
    """E1: kleinste Lösung, Heuristik und Widersprüche (Median) je Zahl der Widersprüche."""
    xs = [f"{r['k']:g} Widersprüche" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["k"] for r in rows], name="Widersprüche (zurückdrehen)", marker_color=C.COLOR_BAR2))
    fig.add_trace(go.Bar(x=xs, y=[r["els"] for r in rows], name="Eades–Lin–Smyth", marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(x=xs, y=[r["exact"] for r in rows], name="kleinste Lösung (exakt)", marker_color=C.COLOR_BAR))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="gestrichene Beziehungen (Median)")
    return _base(fig, 380)


def build_heuristics_figure(rows):
    """E1: in wie viel Prozent der Pläne die Heuristiken das Optimum treffen, und wie viele Pläne die Greedy-Abdeckung berechnen kann."""
    xs = [r["k"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["els_equal"] / r["instances"] for r in rows], mode="lines+markers", name="Eades–Lin–Smyth trifft das Optimum", line=dict(color=C.COLOR_LINE, width=3)))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["greedy_equal"] / r["instances"] for r in rows], mode="lines+markers", name="Greedy-Abdeckung trifft das Optimum", line=dict(color=C.COLOR_BAR3, width=3)))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["greedy_done"] / r["instances"] for r in rows], mode="lines+markers", name="Greedy-Abdeckung berechenbar", line=dict(color=C.COLOR_BAR3, width=2, dash="dot")))
    fig.update_xaxes(title_text="Widersprüche (Median)", tickvals=xs)
    fig.update_yaxes(title_text="Anteil der Pläne (%)", range=[-3, 103])
    return _base(fig, 360)


def build_scale_figure(rows):
    """E2: kleinste Lösung gegen Heuristik je Plangröße (Median)."""
    xs = [f"{r['n']} Aufgaben ({r['k']:g} Wid.)" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["els"] for r in rows], name="Eades–Lin–Smyth", marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(x=xs, y=[r["exact"] for r in rows], name="kleinste Lösung (exakt)", marker_color=C.COLOR_BAR))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="gestrichene Beziehungen (Median)")
    return _base(fig, 340)


def build_vertex_figure(rows):
    """E3: Kanten- gegen Knotenversion (Median)."""
    xs = [f"{r['back']} Widersprüche" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["edge_version"] for r in rows], name="Beziehungen streichen", marker_color=C.COLOR_BAR2))
    fig.add_trace(go.Bar(x=xs, y=[r["vertex_version"] for r in rows], name="Aufgaben streichen", marker_color=C.COLOR_BAR))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="kleinste Lösung (Median)")
    return _base(fig, 340)


def build_rules_rows_figure(rows):
    """E4: Aufgaben auf Kreisen vor den Regeln und Rest danach (Median), je Fall."""
    xs = [f"{r['n']} Aufgaben, {_dec(100 * r['share'])} % Wid." for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["before"] for r in rows], name="Aufgaben in Komponenten mit Kreis", marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(x=xs, y=[r["rest_nodes"] for r in rows], name="Rest nach den Regeln", marker_color=C.COLOR_BAR2))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Aufgaben (Median)")
    return _base(fig, 340)


def build_hardness_figure(rows):
    """E5: kleinste Lösung und Heuristik (Median) je Fall; die Runden stehen im Hover."""
    xs = [f"{r['n']} Aufgaben, Grad {r['out']:g}" for r in rows]
    med = lambda v: sorted(v)[len(v) // 2]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[med(r["els"]) for r in rows], name="Eades–Lin–Smyth", marker_color=C.COLOR_LINE))
    fig.add_trace(go.Bar(x=xs, y=[med(r["exact"]) for r in rows], name="kleinste Lösung (exakt)", marker_color=C.COLOR_BAR,
                         customdata=[[med(r["rounds"]), med(r["constraints"])] for r in rows], hovertemplate="%{x}: %{y}; Runden %{customdata[0]}, Bedingungen %{customdata[1]}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="gestrichene Beziehungen (Median)")
    return _base(fig, 340)
