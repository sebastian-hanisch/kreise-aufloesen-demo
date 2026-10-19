"""Kennzahlen, Prüfung der Ergebnisse und Verdikte. Verdikte sind reine Funktionen (Art, Text): Zahlen kommen aus den Zeilen, nie aus dem Text.

Aufgaben sind in der Anzeige ab 1 nummeriert (`label`); im Kern ab 0. Jedes Ergebnis des Lösers trägt einen Status: „optimal“ (bewiesen), „Zeitgrenze“ (zulässig,
aber nicht bewiesen, mit unterer Schranke) oder „Heuristik“ (ohne Güteaussage)."""

from dataclasses import dataclass

import kau_algorithm as A
import kau_constants as C
from kau_scenario import Instance, make_instance

STATUS_NAMES = {"optimal": "optimal (bewiesen)", "time_limit": "Zeitgrenze erreicht (nicht bewiesen)", "heuristic": "Heuristik (ohne Güteaussage)"}


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    out: float = C.DEFAULT_OUT
    back: int = C.DEFAULT_BACK
    seed: int = C.DEFAULT_SEED
    limit: int = C.DEFAULT_TIME_LIMIT


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: Instance
    baseline: A.FeedbackResult              # die Widersprüche selbst zurückdrehen (nur der Erzeuger kennt sie)
    els: A.FeedbackResult
    greedy: A.FeedbackResult | None         # None: die Kreise sind nicht aufzählbar
    exact: A.FeedbackResult                 # kleinste Menge zu streichender Beziehungen (oder beste bekannte bei Zeitgrenze)
    vertex: A.FeedbackResult                # kleinste Menge zu streichender Aufgaben (Regeln + ILP)
    reduction: A.Reduction
    components: tuple[tuple[int, ...], ...]

    @property
    def has_cycle(self) -> bool:
        return bool(self.components)

    def result(self, method: str):
        return {"widersprueche": self.baseline, "els": self.els, "greedy": self.greedy, "exakt": self.exact}[method]


def label(v: int) -> str:
    return str(v + 1)


def format_edge(edge) -> str:
    return f"{label(edge[0])} → {label(edge[1])}"


def analyse(settings: Settings) -> Analysis:
    return analyse_instance(make_instance(settings.n, settings.out, settings.back, settings.seed), settings)


def analyse_instance(inst: Instance, settings: Settings) -> Analysis:
    """Alle Verfahren auf einer gegebenen Instanz (Tests bauen Mini-Instanzen von Hand)."""
    adj = inst.adj
    comps = tuple(tuple(c) for c in A.nontrivial_components(adj))
    baseline = A.FeedbackResult(tuple(sorted(inst.reversed_edges)), "heuristic")
    els = A.els_fas(adj)
    greedy = A.greedy_cover(adj, C.GREEDY_CYCLE_BUDGET)
    exact = A.exact_fas(adj, time_limit=settings.limit)
    vertex, reduction = A.fvs_with_rules(adj, time_limit=settings.limit)
    return Analysis(settings, inst, baseline, els, greedy, exact, vertex, reduction, comps)


def validate(a: Analysis) -> list[str]:
    """Unabhängige Prüfung vor der Anzeige: leere Liste, wenn alles stimmt; sonst die verletzten Regeln."""
    adj, problems = a.inst.adj, []
    for name, res in (("Widersprüche zurückdrehen", a.baseline), ("Eades–Lin–Smyth", a.els), ("Greedy-Abdeckung", a.greedy), ("Exakt", a.exact)):
        if res is not None and not A.is_feedback_edge_set(adj, res.removed):
            problems.append(f"Die Lösung des Verfahrens „{name}“ macht den Plan nicht kreisfrei (oder enthält Beziehungen, die es nicht gibt).")
    if not A.is_feedback_vertex_set(adj, a.vertex.removed):
        problems.append("Die Lösung der Knotenversion macht den Plan nicht kreisfrei.")
    if a.exact.status == "optimal":
        for name, res in (("Widersprüche zurückdrehen", a.baseline), ("Eades–Lin–Smyth", a.els), ("Greedy-Abdeckung", a.greedy)):
            if res is not None and res.size < a.exact.size:
                problems.append(f"Das Verfahren „{name}“ streicht weniger als das bewiesene Optimum.")
        if any(A.is_feedback_edge_set(adj, [x for x in a.exact.removed if x != e]) for e in a.exact.removed):
            problems.append("Die bewiesen kleinste Lösung enthält eine Beziehung, die man weglassen könnte.")
        if a.vertex.status == "optimal" and a.vertex.size > a.exact.size:
            problems.append("Die Knotenversion ist größer als die Kantenversion.")
    if a.exact.lower_bound is not None and a.exact.lower_bound > a.exact.size:
        problems.append("Die untere Schranke liegt über der Größe der Lösung.")
    if not a.has_cycle and (a.exact.size or a.vertex.size):
        problems.append("Der Plan ist kreisfrei, aber es wird etwas gestrichen.")
    return problems


# --- Zahlenformat --------------------------------------------------------------------------------------------------------------------------

def _i(x) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _dec(x) -> str:
    """Zahl mit Komma; ganze Werte ohne Nachkommastelle."""
    x = float(x)
    return _i(x) if x == int(x) else f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def beziehungen(k: int) -> str:
    return "1 Beziehung" if k == 1 else f"{_i(k)} Beziehungen"


def aufgaben(k: int) -> str:
    return "1 Aufgabe" if k == 1 else f"{_i(k)} Aufgaben"


def _count(x, singular: str, plural: str) -> str:
    """„1 Beziehung“, „2,5 Aufgaben“ (Mediane dürfen Kommazahlen sein)."""
    return f"1 {singular}" if float(x) == 1 else f"{_dec(x)} {plural}"


def widersprueche(k: int) -> str:
    return "1 Widerspruch" if k == 1 else f"{_i(k)} Widersprüche"


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def _compare_text(label_text: str, size: int, opt: int) -> str:
    if size == opt:
        return f"{label_text} trifft mit {beziehungen(size)} das Optimum"
    return f"{label_text} streicht {beziehungen(size)} ({_i(size - opt)} mehr als nötig)"


def verdict_question(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Wie wenig muss man streichen, und wie gut sind die Faustregeln?"""
    if not a.has_cycle:
        return "success", "**Der Plan ist kreisfrei:** Es muss nichts gestrichen werden."
    k = len(a.inst.reversed_edges)
    ex = a.exact
    nodes = f"Als Aufgaben gerechnet {'genügt' if a.vertex.size == 1 else 'genügen'} {aufgaben(a.vertex.size)}" + ("" if a.vertex.status == "optimal" else " (nicht bewiesen)") + "."
    if ex.status != "optimal":
        return "warning", (f"**Zeitgrenze erreicht:** Der Löser hat eine zulässige, aber nicht bewiesene Lösung mit {beziehungen(ex.size)}; bewiesen ist nur, dass mindestens {beziehungen(ex.lower_bound or 0)} nötig sind "
                           f"(die Heuristik von Eades, Lin und Smyth streicht {beziehungen(a.els.size)}, der Plan hat {widersprueche(k)}). Mit mehr Zeit oder weniger Beziehungen je Aufgabe wird das Ergebnis bewiesen. {nodes}")
    if ex.size < k:
        rel = f"weniger als die Zahl der Widersprüche ({_i(k)})"
    elif ex.size == k:
        rel = f"so viele, wie der Plan Widersprüche hat ({_i(k)})"
    else:
        rel = f"mehr als die Zahl der Widersprüche ({_i(k)})"
    greedy = ("die Greedy-Abdeckung ist nicht berechenbar, weil die Kreise nicht aufzählbar sind" if a.greedy is None else _compare_text("die Greedy-Abdeckung", a.greedy.size, ex.size))
    return "info", (f"**Es genügt, {beziehungen(ex.size)} zu streichen** (bewiesen kleinste Zahl), {rel}. {_compare_text('Die Heuristik von Eades, Lin und Smyth', a.els.size, ex.size)}; {greedy}. {nodes}")


def verdict_compare(rows: list[dict]) -> tuple[str, str]:
    """E1: kleinste Lösung und Heuristiken gegen die Zahl der Widersprüche."""
    first, mid, last = rows[0], rows[len(rows) // 2], rows[-1]
    done = sum(r["greedy_done"] for r in rows)
    equal = sum(r["greedy_equal"] for r in rows)
    text = (f"Die kleinste Lösung ist im Median {_dec(mid['exact'])} bei {_dec(mid['k'])} Widersprüchen und {_dec(last['exact'])} bei {_dec(last['k'])}, in {last['less_than_k']} von {last['instances']} Plänen "
            f"kleiner als die Zahl der Widersprüche. Die Heuristik von Eades, Lin und Smyth trifft das Optimum in {first['els_equal']} von {first['instances']} Plänen bei {_dec(first['k'])} Widersprüchen, "
            f"in {last['els_equal']} von {last['instances']} bei {_dec(last['k'])} (bis {last['els_gap_max']} Beziehungen zu viel). Die Greedy-Abdeckung trifft es in {equal} von {done} berechenbaren Plänen; "
            f"bei {_dec(last['k'])} Widersprüchen sind {last['greedy_skipped']} von {last['instances']} Plänen nicht berechenbar.")
    return ("info" if all(r["exact"] <= r["k"] for r in rows) else "warning"), text


def verdict_scale(rows: list[dict]) -> tuple[str, str]:
    """E2: größere Pläne, kleinste Lösung gegen die Heuristik."""
    last = rows[-1]
    parts = "; ".join(f"bei {_i(r['n'])} Aufgaben ({_dec(r['k'])} Widersprüche) {_dec(r['exact'])} gegen {_dec(r['els'])} der Heuristik" for r in rows)
    text = (f"Mediane der kleinsten Lösung: {parts}. Die größte Komponente hat bei {_i(last['n'])} Aufgaben {_dec(last['component'])} Aufgaben; der Löser braucht im Median {_dec(last['rounds'])} Runden "
            f"und {_dec(last['constraints'])} Kreisbedingungen.")
    return ("info" if last["els"] > last["exact"] else "warning"), text


def verdict_vertex(rows: list[dict]) -> tuple[str, str]:
    """E3: Kanten- gegen Knotenversion."""
    last = rows[-1]
    parts = "; ".join(f"bei {_dec(r['back'])} Widersprüchen {_count(r['edge_version'], 'Beziehung', 'Beziehungen')} oder {_count(r['vertex_version'], 'Aufgabe', 'Aufgaben')}" for r in rows)
    ok = all(r["never_larger"] for r in rows)
    text = f"Kleinste Lösung im Median: {parts}. Die Knotenversion ist " + ("in allen Plänen höchstens so groß wie die Kantenversion." if ok else "nicht in allen Plänen höchstens so groß wie die Kantenversion.")
    return ("info" if ok and last["vertex_version"] <= last["edge_version"] else "warning"), text


def verdict_rules(rows: list[dict]) -> tuple[str, str]:
    """E4: Wirkung der Reduktionsregeln."""
    low = [r for r in rows if r["share"] <= 0.05]
    high = [r for r in rows if r["share"] > 0.05]
    alone = ", ".join(f"bei {_i(r['n'])} Aufgaben in {r['alone']} von {r['instances']}" for r in low)
    text = f"Bei {_dec(round(100 * low[0]['share']))} % Widersprüchen lösen die Regeln die Knotenversion allein: {alone} Plänen."
    if high:
        h = high[-1]
        text += (f" Bei {_dec(round(100 * h['share']))} % Widersprüchen und {_i(h['n'])} Aufgaben bleibt im Median ein Rest von {_dec(h['rest_nodes'])} von {_dec(h['before'])} Aufgaben "
                 f"und {_dec(h['rest_edges'])} Beziehungen (allein gelöst in {h['alone']} von {h['instances']}).")
    return ("info" if all(r["alone"] > 0 for r in low) else "warning"), text


def verdict_hardness(rows: list[dict], limit: int) -> tuple[str, str]:
    """E5: zufallsähnliche Pläne, Aufwand des Lösers in Runden und Bedingungen."""
    last = rows[-1]
    parts = "; ".join(f"bei {_i(r['n'])} Aufgaben: kleinste Lösung {min(r['exact'])} bis {max(r['exact'])} gegen {min(r['els'])} bis {max(r['els'])} der Heuristik, {min(r['rounds'])} bis {max(r['rounds'])} Runden, "
                      f"{min(r['constraints'])} bis {max(r['constraints'])} Bedingungen" for r in rows)
    total = sum(r["instances"] for r in rows)
    opt = sum(r["optimal"] for r in rows)
    text = f"Zufallsähnliche Pläne (die Hälfte der Beziehungen umgedreht), {limit} Sekunden Zeitgrenze: {parts}. Bewiesen optimal in {opt} von {total} Läufen."
    return ("info" if opt == total and last["rounds"] and max(last["rounds"]) >= max(rows[0]["rounds"]) else "warning"), text
