"""Kreise auflösen: wie wenig muss man streichen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Reihe „Ordnung und Abhängigkeit“: Welche wenigen Beziehungen (oder Aufgaben) muss man streichen, damit der Plan aufgeht? Zerlegung in
Komponenten, Heuristik von Eades, Lin und Smyth, Greedy-Abdeckung und exakte Lösung (ILP mit nachgeladenen Kreisbedingungen); Knotenversion mit Reduktionsregeln.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import kau_algorithm as A
import kau_constants as C
import kau_evaluation as ev
import kau_experiments as ex
from kau_layout import dunkles_design, kopf_css
from kau_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kau_visualization import (
    build_arc_figure,
    build_compare_figure,
    build_compare_rows_figure,
    build_components_figure,
    build_hardness_figure,
    build_heuristics_figure,
    build_rules_figure,
    build_rules_rows_figure,
    build_scale_figure,
    build_vertex_figure,
)

st.set_page_config(page_title="Kreise auflösen: wie wenig muss man streichen – Sebastian Hanisch", layout="wide")

_i = ev._i


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _compare():
    return ex.compare_rows()


@st.cache_data(show_spinner=False)
def _scale():
    return ex.scale_rows()


@st.cache_data(show_spinner=False)
def _vertex():
    return ex.vertex_rows()


@st.cache_data(show_spinner=False)
def _rules():
    return ex.rules_rows()


@st.cache_data(show_spinner=False)
def _hardness():
    return ex.hardness_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kau_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("✂️ Kreise auflösen: wie wenig muss man streichen")
st.markdown(
    """
Ein Plan mit Kreisen geht nicht auf. Wer ihn reparieren soll, fragt: **Welche wenigen Beziehungen muss man streichen**, damit er kreisfrei wird? Das ist das **Feedback Arc Set**; streicht man stattdessen Aufgaben, ist es das **Feedback Vertex Set**.
Die Zahl der Widersprüche ist dafür ein schlechtes Maß: Das Optimum liegt meist **weit darunter**, die bekannte **Heuristik** von Eades, Lin und Smyth verliert mit wachsender Widersprüchlichkeit den Anschluss,
und die **Greedy-Abdeckung** aus Stück 2 braucht alle Kreise. Exakt geht es trotzdem schnell: erst in **Komponenten zerlegen**, dann ein ILP mit **nachgeladenen Kreisbedingungen**.

Das ist das dritte Stück der Reihe **Ordnung und Abhängigkeit**. Einen Kreis belegen zeigt Stück 1 (**di-kreis-demo**), alle Kreise zählen Stück 2 (**alle-kreise-demo**).
Weiter unten: die Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So löst man Kreise auf", expanded=True):
    st.markdown(
        """
1. **Zerlegen:** Kreise liegen nur innerhalb **starker Zusammenhangskomponenten**. Jede Komponente wird für sich gelöst, der Rest des Plans ist schon in Ordnung.
2. **Heuristik (Eades–Lin–Smyth):** Eine Reihenfolge der Aufgaben bauen (Senken nach hinten, Quellen nach vorn, sonst die Aufgabe mit dem größten Unterschied aus Aus- und Eingrad nach vorn); gestrichen werden die Beziehungen, die **rückwärts** laufen. Schnell, aber ohne Gütegarantie.
3. **Greedy-Abdeckung:** Die Beziehung streichen, die die meisten **noch offenen Kreise** enthält, und wiederholen. Braucht alle Kreise (Stück 2), ist also nur auf aufzählbaren Plänen berechenbar.
4. **Exakt:** Ein ILP minimiert die Zahl gestrichener Beziehungen unter der Bedingung „von jedem bekannten Kreis wird mindestens eine Beziehung gestrichen“. Kreise werden **nachgeladen**: lösen, in der Lösung verbliebene Kreise suchen, als Bedingung ergänzen, wiederholen, bis keiner bleibt.
5. **Knotenversion:** Erst **Reduktionsregeln** (Aufgabe ohne Vorgänger oder Nachfolger weg, Eigenschleife muss in die Lösung, Aufgabe mit nur einem Vorgänger oder Nachfolger in diesen hineinziehen), dann das ILP auf dem Rest.
6. **Zeitgrenze:** Der Löser läuft höchstens so lange, wie in der Seitenleiste steht; danach gilt der **Status** „Zeitgrenze erreicht“: zulässige, aber nicht bewiesene Lösung mit einer bewiesenen unteren Schranke.

| Begriff | Bedeutung |
|---|---|
| **Feedback Arc Set** | kleinste Menge von Beziehungen, deren Streichen den Plan kreisfrei macht |
| **Feedback Vertex Set** | kleinste Menge von Aufgaben mit derselben Wirkung |
| **Komponente** | Aufgaben, die sich gegenseitig erreichen; nur dort liegen Kreise |
| **Nachgeladene Bedingung** | ein Kreis, der in der aktuellen Lösung noch übrig ist und als Bedingung ins ILP kommt |
| **Reduktionsregel** | eine Umformung, die die kleinste Lösung nicht ändert, den Plan aber verkleinert |
| **Status** | „optimal“ (bewiesen), „Zeitgrenze erreicht“ (nicht bewiesen) oder „Heuristik“ (ohne Aussage) |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Plan**")
    n = st.slider("Aufgaben n", *bounds("n_slider"), key="n_slider", help="Wie viele Aufgaben der Plan hat.")
    out = st.slider("Beziehungen je Aufgabe", *bounds("out_slider"), key="out_slider", step=C.OUT_STEP,
                    help="Mittlerer Ausgangsgrad: Zahl der Beziehungen „A vor B“ geteilt durch die Zahl der Aufgaben (höchstens alle Paare).")
    back = st.slider("Widersprüche", *bounds("back_slider"), key="back_slider",
                     help="Wie viele Beziehungen gegen die Wunschreihenfolge umgedreht werden (höchstens so viele, wie es Beziehungen gibt). Bei sehr vielen ist der Plan fast ein Zufallsgraph.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Löser und Anzeige**")
    limit = st.selectbox("Zeitgrenze des Lösers", list(C.TIME_LIMITS), format_func=lambda s: f"höchstens {s} Sekunden", key="limit_select",
                         help="Der exakte Löser (Kantenversion und Knotenversion) bricht nach dieser Zeit ab; der Status wird dann ausgewiesen.")
    method = st.selectbox("Angezeigtes Verfahren", list(C.METHODS), format_func=C.METHOD_NAMES.get, key="method_select",
                          help="Welche Lösung im Bild gezeichnet wird. Der Vergleich im Tab „Vergleichen“ zeigt immer alle Verfahren.")

sync_query_params({"n_slider": int(n), "out_slider": float(out), "back_slider": int(back), "seed_input": int(seed), "limit_select": int(limit), "method_select": method})

settings = ev.Settings(int(n), float(out), int(back), int(seed), int(limit))
with st.spinner("Löse den Plan..."):
    a = _analysis(settings)
inst = a.inst
problems = ev.validate(a)
for p in problems:
    st.error(f"Prüfung fehlgeschlagen: {p}")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
real_back = len(inst.reversed_edges)
st.caption(f"{_i(inst.n)} Aufgaben, {_i(inst.m)} Beziehungen, davon {_i(real_back)} gegen die Wunschreihenfolge umgedreht"
           + (f" (gewünscht: {_i(settings.back)}, es gibt nicht mehr Beziehungen)." if real_back < settings.back else ".") + " Aufgaben sind ab 1 nummeriert.")
ex_res = a.exact
m1, m2, m3, m4 = st.columns(4)
m1.metric("Widersprüche", _i(real_back), delta="so viele Beziehungen wurden umgedreht", delta_color="off")
m2.metric("Kleinste Lösung (Beziehungen)", _i(ex_res.size), delta=("bewiesen" if ex_res.status == "optimal" else f"nicht bewiesen, mindestens {_i(ex_res.lower_bound or 0)}"), delta_color="off")
m3.metric("Kleinste Lösung (Aufgaben)", _i(a.vertex.size), delta=("bewiesen" if a.vertex.status == "optimal" else "nicht bewiesen"), delta_color="off")
# Delta immer „mein Wert minus Referenz“; weniger gestrichene Beziehungen sind besser, deshalb delta_color="inverse".
diff = a.els.size - ex_res.size
m4.metric("Heuristik (Eades–Lin–Smyth)", _i(a.els.size), delta=f"{diff:+,} gegen exakt".replace(",", ".") if diff else "gleich exakt", delta_color="inverse" if diff else "off")

tab_solve, tab_compare, tab_vertex = st.tabs(["✂️ Lösen", "⚖️ Vergleichen", "🔘 Aufgaben statt Beziehungen"])

# --- Tab 1: Lösen --------------------------------------------------------------------------------------------------------------------------

with tab_solve:
    res = a.result(method)
    if not a.has_cycle:
        st.success("Der Plan ist kreisfrei: Es muss nichts gestrichen werden.")
        st.plotly_chart(build_arc_figure(inst), width="stretch", key="arc_none")
    elif res is None:
        st.warning(f"Die Greedy-Abdeckung ist nicht berechenbar: Die Kreise dieses Plans sind nicht innerhalb von {_i(C.GREEDY_CYCLE_BUDGET)} Kreisen aufzählbar (Stück 2). Wählen Sie ein anderes Verfahren in der Seitenleiste.")
        st.plotly_chart(build_arc_figure(inst), width="stretch", key="arc_none_greedy")
    else:
        s1, s2, s3 = st.columns(3)
        s1.metric(C.METHOD_NAMES[method], f"{_i(res.size)} Beziehungen", delta=ev.STATUS_NAMES[res.status] if method == "exakt" else "ohne Güteaussage" if method != "widersprueche" else "Wissen des Erzeugers", delta_color="off")
        gap = res.size - ex_res.size
        s2.metric("Abstand zur kleinsten Lösung", _i(gap) if ex_res.status == "optimal" else "–", delta=("trifft das Optimum" if gap == 0 else f"{gap:+,} Beziehungen".replace(",", ".")) if ex_res.status == "optimal" else "Optimum nicht bewiesen",
                  delta_color="off" if gap == 0 or ex_res.status != "optimal" else "inverse")
        order = A.order_after(inst.adj, res.removed)
        s3.metric("Nach dem Streichen", "kreisfrei ✓" if order is not None else "Kreis bleibt ✗", delta="zulässige Reihenfolge existiert" if order is not None else "Lösung unzulässig", delta_color="off")
        st.plotly_chart(build_arc_figure(inst, struck_edges=res.removed), width="stretch", key="arc_solve")
        st.caption("Gestrichene Beziehungen rot gepunktet. Oben blau die Beziehungen in Richtung der Wunschreihenfolge (Pfeile von links nach rechts), unten violett die Widersprüche (von rechts nach links).")
        if order is not None:
            shown = order[:30]
            st.markdown("**Eine zulässige Reihenfolge nach dem Streichen** (Stück 1 liefert sie): " + " → ".join(ev.label(v) for v in shown) + (" → …" if len(order) > 30 else ""))
        table = pd.DataFrame({"Beziehung": [ev.format_edge(e) for e in res.removed], "gegen die Wunschreihenfolge": ["ja" if e in inst.reversed_edges else "nein" for e in res.removed]})
        with st.expander(f"Die {_i(res.size)} gestrichenen Beziehungen"):
            st.dataframe(table, hide_index=True, width="stretch", height=min(400, 40 + 35 * len(table)))
            st.caption("Das Optimum streicht oft Beziehungen, die in der Wunschreihenfolge nach vorn laufen („nein“): Es kommt nicht darauf an, welche Beziehungen der Erzeuger umgedreht hat.")

# --- Tab 2: Vergleichen --------------------------------------------------------------------------------------------------------------------

with tab_compare:
    if not a.has_cycle:
        st.success("Kein Kreis, also nichts zu vergleichen.")
    else:
        rows = []
        for key in C.METHODS:
            r = a.result(key)
            if r is None:
                rows.append({"Verfahren": C.METHOD_NAMES[key], "Gestrichen": "–", "Abstand zum Optimum": "–", "Status": "nicht berechenbar (Kreise nicht aufzählbar)"})
            else:
                gap = "–" if ex_res.status != "optimal" else _i(r.size - ex_res.size)
                rows.append({"Verfahren": C.METHOD_NAMES[key], "Gestrichen": _i(r.size), "Abstand zum Optimum": gap, "Status": ev.STATUS_NAMES[r.status] if key == "exakt" else ev.STATUS_NAMES["heuristic"]})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        with c1:
            entries = [(C.METHOD_NAMES[k], a.result(k).size, None) for k in C.METHODS if a.result(k) is not None]
            st.plotly_chart(build_compare_figure(entries), width="stretch", key="chart_compare")
            st.caption("Zahl der gestrichenen Beziehungen je Verfahren; die Widersprüche selbst zurückzudrehen kennt nur der Erzeuger des Plans.")
        with c2:
            st.plotly_chart(build_components_figure(a.components), width="stretch", key="chart_components")
            comp_nodes = sum(len(c) for c in a.components)
            st.caption(f"Die Komponenten mit Kreis: {len(a.components)} mit zusammen {_i(comp_nodes)} von {_i(inst.n)} Aufgaben. Der Löser sieht nur diese.")
        q1, q2, q3 = st.columns(3)
        q1.metric("Runden des Lösers", _i(a.exact.rounds), delta="lösen und Kreise nachladen", delta_color="off")
        q2.metric("Kreisbedingungen", _i(a.exact.constraints), delta="nachgeladen und vorab", delta_color="off")
        q3.metric("Status", ev.STATUS_NAMES[a.exact.status].split(" (")[0], delta=f"untere Schranke {_i(a.exact.lower_bound or 0)}" if a.exact.status != "optimal" else "bewiesen", delta_color="off")
        if a.exact.status != "optimal":
            st.warning("Die Zeitgrenze wurde erreicht: Die gezeigte Lösung ist zulässig, aber nicht bewiesen kleinste. Mit mehr Zeit in der Seitenleiste oder weniger Beziehungen je Aufgabe wird das Ergebnis bewiesen.")

# --- Tab 3: Aufgaben statt Beziehungen -----------------------------------------------------------------------------------------------------

with tab_vertex:
    if not a.has_cycle:
        st.success("Kein Kreis, also nichts zu streichen.")
    else:
        red, vtx = a.reduction, a.vertex
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Von den Regeln genommen", _i(len(red.taken)), delta="Eigenschleifen und gezogene Aufgaben", delta_color="off")
        t2.metric("Rest nach den Regeln", f"{_i(len(red.rest_nodes))} Aufgaben", delta="das ILP löst nur diesen Rest" if red.rest_nodes else "die Regeln lösen alles", delta_color="off")
        t3.metric("Kleinste Lösung (Aufgaben)", _i(vtx.size), delta=ev.STATUS_NAMES[vtx.status].split(" (")[0], delta_color="off")
        t4.metric("Gegenüber Beziehungen", f"{_i(vtx.size)} statt {_i(a.exact.size)}", delta="eine Aufgabe ersetzt mehrere Beziehungen" if vtx.size < a.exact.size else None, delta_color="off")
        comp_nodes = sum(len(c) for c in a.components)
        st.plotly_chart(build_rules_figure(inst.n, comp_nodes, red.steps), width="stretch", key="chart_rules")
        st.caption("Aufgaben im Rest nach jedem Schritt der Reduktionsregeln. " + ", ".join(f"{name}: {_i(k)}×" for name, k in red.counts.items()) + ".")
        st.plotly_chart(build_arc_figure(inst, struck_vertices=vtx.removed), width="stretch", key="arc_vertex")
        st.caption("Gestrichene Aufgaben rot durchgekreuzt; ihre Beziehungen sind blass gezeichnet. Nach dem Streichen: " + ("kreisfrei ✓." if A.is_feedback_vertex_set(inst.adj, vtx.removed) else "es bleibt ein Kreis ✗."))
        st.markdown("**Gestrichene Aufgaben:** " + (", ".join(ev.label(v) for v in vtx.removed) if vtx.removed else "keine"))

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie wenig muss man streichen, und wie gut sind die Faustregeln?")
_show(ev.verdict_question(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

with st.spinner("Rechne die Experimente (einmalig, einige Sekunden)..."):
    rows_c, rows_s, rows_v, rows_r, rows_h = _compare(), _scale(), _vertex(), _rules(), _hardness()

st.subheader("🔬 Experiment 1: Wie klein ist das Optimum, wie gut sind die Faustregeln?")
st.caption(f"{C.E1_N} Aufgaben, mittlerer Ausgangsgrad {C.E1_OUT:g}, je Zeile {len(C.E1_SEEDS)} feste Pläne; Median. Die Greedy-Abdeckung ist nur auf Plänen berechenbar, deren Kreise aufzählbar sind (Budget {_i(C.GREEDY_CYCLE_BUDGET)} Kreise).")
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(build_compare_rows_figure(rows_c), width="stretch", key="chart_compare_rows")
with c2:
    st.plotly_chart(build_heuristics_figure(rows_c), width="stretch", key="chart_heuristics")
_show(ev.verdict_compare(rows_c))

st.subheader("🔬 Experiment 2: Größere Pläne")
st.caption(f"Mittlerer Ausgangsgrad {C.E2_OUT:g}, {int(C.E2_SHARE * 100)} % der Beziehungen umgedreht, je Größe {len(C.E2_SEEDS)} feste Pläne; Median. Der exakte Löser braucht nur die Komponenten mit Kreis.")
st.plotly_chart(build_scale_figure(rows_s), width="stretch", key="chart_scale")
_show(ev.verdict_scale(rows_s))

st.subheader("🔬 Experiment 3: Beziehungen oder Aufgaben streichen?")
st.caption(f"{C.E3_N} Aufgaben, mittlerer Ausgangsgrad {C.E3_OUT:g}, je Zeile {len(C.E3_SEEDS)} feste Pläne; kleinste Lösung im Median.")
st.plotly_chart(build_vertex_figure(rows_v), width="stretch", key="chart_vertex")
_show(ev.verdict_vertex(rows_v))

st.subheader("🔬 Experiment 4: Wie weit kommen die Reduktionsregeln allein?")
st.caption(f"Mittlerer Ausgangsgrad {C.E4_OUT:g}, je Fall {len(C.E4_SEEDS)} feste Pläne; Knotenversion, Median.")
st.plotly_chart(build_rules_rows_figure(rows_r), width="stretch", key="chart_rules_rows")
_show(ev.verdict_rules(rows_r))

st.subheader("🔬 Experiment 5: Zufallsähnliche Pläne und der Aufwand des Lösers")
st.caption(f"Die Hälfte der Beziehungen umgedreht (der Plan ist fast ein Zufallsgraph), je Fall {len(C.E5_SEEDS)} feste Pläne, Zeitgrenze {C.E5_TIME_LIMIT} Sekunden. Aufwand in Runden und Kreisbedingungen, nicht in Sekunden.")
st.plotly_chart(build_hardness_figure(rows_h), width="stretch", key="chart_hardness")
_show(ev.verdict_hardness(rows_h, C.E5_TIME_LIMIT))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Synthetische Pläne mit verdeckter Wunschreihenfolge** | Echte Abhängigkeiten haben Stufen und Gruppen; wie klein das Optimum dort ist und wie gut die Heuristik, zeigt diese Demo nicht. | - |
| **Alle Beziehungen gleich schwer** | Kostet das Streichen mancher Beziehungen mehr als anderer, ist das ein anderes (gewichtetes) Problem; die kleinste Zahl ist dann nicht die billigste Lösung. | - |
| **Das Optimum ist nicht eindeutig** | Meist gibt es mehrere gleich kleine Lösungen; die Demo zeigt eine. Welche man wählt, hängt an Kosten und Fachwissen. | - |
| **Zeitgrenze statt Beweis** | Bei dichten, zufallsähnlichen Plänen steigt die Zahl der Runden stark (Experiment 5); nach der Zeitgrenze ist die Lösung zulässig, aber nicht bewiesen kleinste (Status „Zeitgrenze erreicht“). | - |
| **Greedy-Abdeckung braucht alle Kreise** | Ist ihre Zahl nicht aufzählbar, ist das Verfahren nicht berechenbar; die Demo meldet das, statt zu raten. | Stück 2 der Reihe |
| **Heuristik ohne Gütegarantie** | Die Heuristik von Eades, Lin und Smyth kann deutlich über dem Optimum liegen (Experiment 1 und 2); eine Approximationsgarantie gibt es hier nicht. | - |
| **Größe** | Bis {C.N_MAX} Aufgaben und Ausgangsgrad {C.OUT_MAX:g}; darüber wird der exakte Löser schnell sehr teuer. | - |
| **Kemeny-Rangaggregation** | Dasselbe Problem auf vollständigen Vergleichen (Turnieren) ist die Kemeny-Aggregation; sie ist hier nicht Thema. | Ranking-Linie |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein gerichteter Graph $G = (V, E)$ mit $n = |V|$ Aufgaben und $m = |E|$ Beziehungen. **Gesucht:** eine kleinste Menge $F \subseteq E$ (Feedback Arc Set), sodass $G - F$ kreisfrei ist, oder eine kleinste Menge $S \subseteq V$ (Feedback Vertex Set) mit $G - S$ kreisfrei.

| Symbol | Bedeutung |
|---|---|
| $F$, $S$ | gestrichene Beziehungen bzw. Aufgaben |
| $\mathcal{C}$ | Menge der Kreise von $G$ |
| $x_e$ | Entscheidungsvariable: 1, wenn die Beziehung $e$ gestrichen wird |
| $\pi$ | eine Reihenfolge der Aufgaben |

**Über Reihenfolgen.** Das kleinste Feedback Arc Set ist die kleinste Zahl rückwärts laufender Beziehungen über alle Reihenfolgen:

$$\min_{F} |F| \;=\; \min_{\pi} \; \big|\{ (a, b) \in E : \pi(a) \ge \pi(b) \}\big|.$$

**Als ILP.** Mit einer Variable $x_e \in \{0, 1\}$ je Beziehung:

$$\min \sum_{e \in E} x_e \quad \text{unter} \quad \sum_{e \in C} x_e \ge 1 \;\; \text{für alle } C \in \mathcal{C}.$$

Es gibt zu viele Kreise, um alle Bedingungen aufzuschreiben; man startet mit wenigen und lädt Kreise nach, die die aktuelle Lösung noch enthält.

**Zerlegung.** Kreise liegen innerhalb starker Komponenten $K_1, \dots, K_r$; das Problem zerfällt:

$$\min |F| \;=\; \sum_{j=1}^{r} \min |F_j|,$$

wobei $F_j$ ein Feedback Arc Set von $G[K_j]$ ist.

**Aufgaben statt Beziehungen.** Jede gestrichene Beziehung lässt sich durch eine ihrer Endaufgaben ersetzen, also gilt für die kleinsten Lösungen

$$\min |S| \;\le\; \min |F|.$$

**Literatur.** P. Eades, X. Lin, W. F. Smyth: *A fast and effective heuristic for the feedback arc set problem*, Information Processing Letters 47 (6), 1993, S. 319–323. A. Baharev, H. Schichl, A. Neumaier, T. Achterberg: *An exact method for the minimum feedback arc set problem*, ACM Journal of Experimental Algorithmics 26 (1), Art. 1.4, 2021, DOI 10.1145/3446429. M. Grötschel, M. Jünger, G. Reinelt: *Comments on „An exact method for the minimum feedback arc set problem“*, ACM Journal of Experimental Algorithmics 27, Art. 1.3, 2022, DOI 10.1145/3545001 (eine ältere Formulierung mit Dreiecksungleichungen ist mit moderner Technik konkurrenzfähig). Die Knotenversion mit Reduktionsregeln: *Reduction Rules and ILP Are All You Need: Minimal Directed Feedback Vertex Set*, arXiv 2208.01119.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
