"""Experimente E1 bis E5 über feste Pläne (nie ein einzelner Zufalls-Seed). Jede Funktion liefert Zeilen für Tabelle, Diagramm und Verdikt.

E1 Optimum und Heuristiken gegen die Zahl der Widersprüche (Größe der Lösung, Komponente, Runden), E2 größere Pläne, E3 Kanten- gegen Knotenversion,
E4 Wirkung der Reduktionsregeln, E5 Zufallsähnliche Pläne und Aufwand des Lösers (Runden und Bedingungen, keine Sekunden)."""

from statistics import median

import kau_algorithm as A
import kau_constants as C
import kau_scenario as S


def _back_count(n, out, share):
    return round(share * S.edge_count(n, out))


def compare_rows(n=C.E1_N, out=C.E1_OUT, backs=C.E1_BACKS, seeds=C.E1_SEEDS) -> list[dict]:
    """E1: je Zahl der Widersprüche die kleinste Lösung (exakt), die Heuristik von Eades, Lin und Smyth und die Greedy-Abdeckung (nur auf aufzählbaren Plänen)."""
    rows = []
    for back in backs:
        ks, opt, els, greedy_equal, greedy_done, less, els_equal, els_gap, comp, comp_edges, rounds, cons = [], [], [], 0, 0, 0, 0, [], [], [], [], []
        for s in seeds:
            inst = S.make_instance(n, out, back, s)
            adj = inst.adj
            k = len(inst.reversed_edges)
            res = A.exact_fas(adj, time_limit=60)
            e = A.els_fas(adj)
            g = A.greedy_cover(adj, C.GREEDY_CYCLE_BUDGET)
            ks.append(k)
            opt.append(res.size)
            els.append(e.size)
            less += res.size < k
            els_equal += e.size == res.size
            els_gap.append(e.size - res.size)
            if g is not None:
                greedy_done += 1
                greedy_equal += g.size == res.size
            comps = A.nontrivial_components(adj)
            comp.append(max((len(c) for c in comps), default=0))
            comp_edges.append(sum(len(adj[v]) for c in comps for v in c))
            rounds.append(res.rounds)
            cons.append(res.constraints)
        rows.append({"back": back, "n": n, "instances": len(seeds), "k": median(ks), "exact": median(opt), "less_than_k": less, "els": median(els), "els_equal": els_equal,
                     "els_gap_max": max(els_gap), "greedy_done": greedy_done, "greedy_equal": greedy_equal, "greedy_skipped": len(seeds) - greedy_done,
                     "component": median(comp), "component_edges": median(comp_edges), "rounds": median(rounds), "constraints": median(cons)})
    return rows


def scale_rows(ns=C.E2_NS, out=C.E2_OUT, share=C.E2_SHARE, seeds=C.E2_SEEDS) -> list[dict]:
    """E2: größere Pläne mit festem Anteil an Widersprüchen: kleinste Lösung gegen ELS und Größe der Komponente."""
    rows = []
    for n in ns:
        back = _back_count(n, out, share)
        data = []
        for s in seeds:
            inst = S.make_instance(n, out, back, s)
            res = A.exact_fas(inst.adj, time_limit=60)
            e = A.els_fas(inst.adj)
            comps = A.nontrivial_components(inst.adj)
            data.append((len(inst.reversed_edges), res.size, e.size, max((len(c) for c in comps), default=0), res.rounds, res.constraints))
        rows.append({"n": n, "back": back, "instances": len(seeds), "k": median(d[0] for d in data), "exact": median(d[1] for d in data), "els": median(d[2] for d in data),
                     "els_gap_max": max(d[2] - d[1] for d in data), "component": median(d[3] for d in data), "rounds": median(d[4] for d in data), "constraints": median(d[5] for d in data)})
    return rows


def vertex_rows(n=C.E3_N, out=C.E3_OUT, backs=C.E3_BACKS, seeds=C.E3_SEEDS) -> list[dict]:
    """E3: Kanten- gegen Knotenversion (Median der kleinsten Lösungen); die Knotenversion ist nie größer."""
    rows = []
    for back in backs:
        edges, nodes, never_larger = [], [], True
        for s in seeds:
            adj = S.make_instance(n, out, back, s).adj
            a, b = A.exact_fas(adj, time_limit=60).size, A.exact_fas(adj, vertex=True, time_limit=60).size
            edges.append(a)
            nodes.append(b)
            never_larger = never_larger and b <= a
        rows.append({"back": back, "n": n, "instances": len(seeds), "edge_version": median(edges), "vertex_version": median(nodes), "never_larger": never_larger})
    return rows


def rules_rows(cases=C.E4_CASES, out=C.E4_OUT, seeds=C.E4_SEEDS) -> list[dict]:
    """E4: Wirkung der Reduktionsregeln der Knotenversion: Aufgaben auf Kreisen vor den Regeln, Rest danach, Zahl der Pläne, die die Regeln allein lösen."""
    rows = []
    for n, share in cases:
        back = _back_count(n, out, share)
        before, rest_nodes, rest_edges, taken, alone = [], [], [], [], 0
        for s in seeds:
            adj = S.make_instance(n, out, back, s).adj
            red = A.reduce_fvs(adj)
            before.append(sum(len(c) for c in A.nontrivial_components(adj)))
            rest_nodes.append(len(red.rest_nodes))
            rest_edges.append(sum(len(red.rest_adj[v]) for v in red.rest_nodes))
            taken.append(len(red.taken))
            alone += not red.rest_nodes
        rows.append({"n": n, "share": share, "back": back, "instances": len(seeds), "before": median(before), "rest_nodes": median(rest_nodes), "rest_edges": median(rest_edges),
                     "taken": median(taken), "alone": alone})
    return rows


def hardness_rows(cases=C.E5_CASES, seeds=C.E5_SEEDS, time_limit=C.E5_TIME_LIMIT) -> list[dict]:
    """E5: zufallsähnliche Pläne (die Hälfte der Beziehungen umgedreht): Größe der Lösung, Runden und Bedingungen des Lösers; Status je Plan."""
    rows = []
    for n, out in cases:
        back = S.edge_count(n, out) // 2
        data = []
        for s in seeds:
            adj = S.make_instance(n, out, back, s).adj
            res = A.exact_fas(adj, time_limit=time_limit)
            data.append((res.size, A.els_fas(adj).size, res.rounds, res.constraints, res.status))
        rows.append({"n": n, "out": out, "back": back, "instances": len(seeds), "exact": [d[0] for d in data], "els": [d[1] for d in data],
                     "rounds": [d[2] for d in data], "constraints": [d[3] for d in data], "optimal": sum(d[4] == "optimal" for d in data)})
    return rows
