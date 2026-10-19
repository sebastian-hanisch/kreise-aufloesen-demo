"""Kern der Demo: Kreise auflösen (Feedback Arc Set und Feedback Vertex Set). Standardbibliothek, für den exakten Löser `scipy.optimize.milp` (HiGHS).

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b); `adj[v]` sind die Aufgaben, die nach v kommen sollen.
Verfahren: `els_fas` (Eades-Lin-Smyth-Heuristik über eine Reihenfolge), `greedy_cover` (wiederholt die meistbelegte Beziehung streichen, braucht alle Kreise),
`exact_fas` (Zerlegung in starke Komponenten, je Komponente ein ILP mit nachgeladenen Kreisbedingungen) und für die Knotenversion `reduce_fvs`
(Reduktionsregeln) mit `exact_fas(..., vertex=True)` auf dem Rest. Unabhängige Prüfer: `is_feedback_edge_set`, `is_feedback_vertex_set`, `is_acyclic`.

Ergebnisse tragen immer einen **Status**: "optimal" (bewiesen), "time_limit" (Zeitgrenze erreicht: zulässige, aber nicht bewiesene Lösung mit unterer Schranke)
oder "heuristic" (Heuristik ohne Güteaussage)."""

import math
import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class FeedbackResult:
    removed: tuple                     # gestrichene Beziehungen ((a, b), ...) bzw. Aufgaben (v, ...), sortiert
    status: str                        # "optimal", "time_limit" oder "heuristic"
    rounds: int = 0                    # Runden des Lösers (je Komponente summiert)
    constraints: int = 0               # nachgeladene Kreisbedingungen (je Komponente summiert)
    lower_bound: int | None = None     # bewiesene untere Schranke (bei "optimal" gleich der Größe)

    @property
    def size(self) -> int:
        return len(self.removed)


@dataclass(frozen=True)
class Reduction:
    taken: tuple[int, ...]             # Aufgaben, die die Regeln schon in die Lösung genommen haben
    rest_adj: tuple                    # Restgraph (gleiche Nummerierung; gelöschte Aufgaben ohne Kanten)
    rest_nodes: tuple[int, ...]        # Aufgaben des Restes (auf einem Kreis des Restes)
    steps: tuple = ()                  # Verlauf: (Regel, Zahl der Aufgaben im Rest, Zahl der Beziehungen im Rest)
    counts: dict = field(default_factory=dict)   # Regel -> Zahl der Anwendungen


# --- Graphhilfen ---------------------------------------------------------------------------------------------------------------------------

def edge_list(adj) -> list[tuple[int, int]]:
    return [(a, b) for a in range(len(adj)) for b in adj[a]]


def sccs(adj) -> list[list[int]]:
    """Starke Zusammenhangskomponenten (Kosaraju, iterativ), je Komponente aufsteigend sortiert."""
    n = len(adj)
    seen = [False] * n
    order: list[int] = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, iter(adj[s]))]
        while stack:
            v, it = stack[-1]
            for w in it:
                if not seen[w]:
                    seen[w] = True
                    stack.append((w, iter(adj[w])))
                    break
            else:
                order.append(v)
                stack.pop()
    radj: list[list[int]] = [[] for _ in range(n)]
    for v in range(n):
        for w in adj[v]:
            radj[w].append(v)
    comp = [-1] * n
    comps: list[list[int]] = []
    for s in reversed(order):
        if comp[s] != -1:
            continue
        comp[s] = len(comps)
        members = [s]
        stack = [s]
        while stack:
            v = stack.pop()
            for u in radj[v]:
                if comp[u] == -1:
                    comp[u] = len(comps)
                    members.append(u)
                    stack.append(u)
        comps.append(sorted(members))
    return comps


def nontrivial_components(adj) -> list[list[int]]:
    """Komponenten, in denen ein Kreis liegen kann: mehr als eine Aufgabe oder eine Eigenschleife."""
    return sorted((c for c in sccs(adj) if len(c) > 1 or c[0] in adj[c[0]]), key=lambda c: c[0])


def topological_order(adj):
    """Kahn-Abbau; None, wenn der Graph einen Kreis hat."""
    n = len(adj)
    indeg = [0] * n
    for v in range(n):
        for w in adj[v]:
            indeg[w] += 1
    queue = deque(v for v in range(n) if indeg[v] == 0)
    order = []
    while queue:
        v = queue.popleft()
        order.append(v)
        for w in adj[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return order if len(order) == n else None


def is_acyclic(adj) -> bool:
    return topological_order(adj) is not None


def remove_edges(adj, edges):
    """Graph ohne die genannten Beziehungen."""
    gone = set(edges)
    return tuple(tuple(w for w in adj[v] if (v, w) not in gone) for v in range(len(adj)))


def remove_vertices(adj, vertices):
    """Graph ohne die genannten Aufgaben (sie bleiben als Platz ohne Beziehungen erhalten, die Nummerierung ändert sich nicht)."""
    gone = set(vertices)
    return tuple(() if v in gone else tuple(w for w in adj[v] if w not in gone) for v in range(len(adj)))


def is_feedback_edge_set(adj, edges) -> bool:
    """Unabhängiger Prüfer: nur vorhandene Beziehungen, keine doppelt, und danach kreisfrei."""
    edges = list(edges)
    present = set(edge_list(adj))
    return len(set(edges)) == len(edges) and all(e in present for e in edges) and is_acyclic(remove_edges(adj, edges))


def is_feedback_vertex_set(adj, vertices) -> bool:
    vertices = list(vertices)
    return len(set(vertices)) == len(vertices) and all(0 <= v < len(adj) for v in vertices) and is_acyclic(remove_vertices(adj, vertices))


def order_after(adj, removed, vertex=False):
    """Zulässige Reihenfolge nach dem Streichen (Kahn-Ordnung); None, wenn noch ein Kreis bleibt. Gestrichene Aufgaben fehlen in der Reihenfolge."""
    rest = remove_vertices(adj, removed) if vertex else remove_edges(adj, removed)
    order = topological_order(rest)
    if order is None:
        return None
    gone = set(removed) if vertex else set()
    return tuple(v for v in order if v not in gone)


def _cycle_nodes_through_edge(adj, a, b):
    """Aufgaben des kürzesten Kreises durch a -> b in Reihenfolge a, b, ..., Vorgänger von a."""
    if a == b:
        return (a,)
    parent = {b: None}
    queue = deque([b])
    while queue:
        v = queue.popleft()
        for w in adj[v]:
            if w not in parent:
                parent[w] = v
                if w == a:
                    path = [a]
                    while parent[path[-1]] is not None:
                        path.append(parent[path[-1]])
                    # path = a, Vorgänger von a, ..., b: umdrehen ergibt b, ..., a
                    return (a,) + tuple(reversed(path[1:]))
                queue.append(w)
    return None


def _cycle_edges(cycle):
    return [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]


# --- Eades-Lin-Smyth -----------------------------------------------------------------------------------------------------------------------

def els_order(adj) -> tuple[int, ...]:
    """Reihenfolge nach Eades, Lin und Smyth (1993): Senken kommen nach hinten, Quellen nach vorn, sonst wandert die Aufgabe mit dem größten Unterschied
    (Ausgrad minus Eingrad) nach vorn; Gleichstand: kleinere Nummer. Keine Gütegarantie für die Zahl der rückwärts laufenden Beziehungen."""
    n = len(adj)
    out = [set(w for w in adj[v] if w != v) for v in range(n)]
    inn: list[set] = [set() for _ in range(n)]
    for v in range(n):
        for w in out[v]:
            inn[w].add(v)
    alive = set(range(n))
    front: list[int] = []
    back: list[int] = []

    def remove(v):
        alive.discard(v)
        for w in out[v]:
            inn[w].discard(v)
        for u in inn[v]:
            out[u].discard(v)

    while alive:
        changed = True
        while changed:
            changed = False
            for v in sorted(alive):
                if v in alive and not out[v]:
                    back.append(v)
                    remove(v)
                    changed = True
            for v in sorted(alive):
                if v in alive and not inn[v]:
                    front.append(v)
                    remove(v)
                    changed = True
        if alive:
            v = max(sorted(alive), key=lambda x: len(out[x]) - len(inn[x]))
            front.append(v)
            remove(v)
    return tuple(front + back[::-1])


def els_fas(adj) -> FeedbackResult:
    """Beziehungen, die in der ELS-Reihenfolge rückwärts laufen (einschließlich Eigenschleifen): ein zulässiges, nicht bewiesen kleinstes Feedback Arc Set."""
    pos = {v: i for i, v in enumerate(els_order(adj))}
    back = tuple(sorted((a, b) for a in range(len(adj)) for b in adj[a] if pos[a] >= pos[b]))
    return FeedbackResult(back, "heuristic")


# --- Greedy auf den Kreisen ----------------------------------------------------------------------------------------------------------------

def enumerate_cycles(adj, max_cycles=20000):
    """Alle Elementarkreise nach Johnson (1975); bricht nach `max_cycles` ab. Gibt (Kreise, abgebrochen). Kreise: kleinste Aufgabe zuerst."""
    n = len(adj)
    cycles: list[tuple[int, ...]] = []
    for s in range(n):
        comp = _component(adj, s, set(range(s, n)))
        if len(comp) < 2 and s not in adj[s]:
            continue
        blocked: set[int] = set()
        blist = {v: set() for v in comp}
        path = [s]

        def unblock(u):
            stack = [u]
            while stack:
                x = stack.pop()
                if x in blocked:
                    blocked.discard(x)
                    stack.extend(blist[x])
                    blist[x].clear()

        def circuit(v):
            found = False
            blocked.add(v)
            for w in adj[v]:
                if w not in comp:
                    continue
                if w == s:
                    cycles.append(tuple(path))
                    if len(cycles) > max_cycles:
                        return None
                    found = True
                elif w not in blocked:
                    path.append(w)
                    got = circuit(w)
                    path.pop()
                    if got is None:
                        return None
                    found = found or got
            if found:
                unblock(v)
            else:
                for w in adj[v]:
                    if w in comp:
                        blist[w].add(v)
            return found

        if circuit(s) is None:
            return cycles, True
    return cycles, False


def _component(adj, s, allowed):
    fwd = {s}
    stack = [s]
    while stack:
        v = stack.pop()
        for w in adj[v]:
            if w in allowed and w not in fwd:
                fwd.add(w)
                stack.append(w)
    pred: dict[int, list[int]] = {}
    for v in fwd:
        for w in adj[v]:
            if w in fwd:
                pred.setdefault(w, []).append(v)
    bwd = {s}
    stack = [s]
    while stack:
        v = stack.pop()
        for u in pred.get(v, ()):
            if u not in bwd:
                bwd.add(u)
                stack.append(u)
    return fwd & bwd


def greedy_cover(adj, max_cycles=20000):
    """Wiederholt die Beziehung streichen, die die meisten noch offenen Kreise enthält (Gleichstand: kleinere Beziehung). Braucht alle Kreise;
    gibt None zurück, wenn sie nicht innerhalb von `max_cycles` aufzählbar sind."""
    cycles, aborted = enumerate_cycles(adj, max_cycles)
    if aborted:
        return None
    open_cycles = [set(_cycle_edges(c)) for c in cycles]
    chosen = []
    while open_cycles:
        cover: dict = {}
        for c in open_cycles:
            for e in c:
                cover[e] = cover.get(e, 0) + 1
        best = min(cover, key=lambda e: (-cover[e], e))
        chosen.append(best)
        open_cycles = [c for c in open_cycles if best not in c]
    return FeedbackResult(tuple(sorted(chosen)), "heuristic")


# --- Exakt: Komponenten + ILP mit nachgeladenen Kreisbedingungen --------------------------------------------------------------------------

def _heuristic_vertices(adj) -> tuple[int, ...]:
    """Zulässiges Feedback Vertex Set ohne Güteaussage: wiederholt die Aufgabe mit dem größten Produkt aus Ein- und Ausgrad in einer Komponente streichen."""
    removed: list[int] = []
    cur = adj
    while True:
        comps = nontrivial_components(cur)
        if not comps:
            return tuple(sorted(removed))
        indeg = [0] * len(cur)
        for v in range(len(cur)):
            for w in cur[v]:
                indeg[w] += 1
        pick = max((v for c in comps for v in c), key=lambda v: (indeg[v] * len(cur[v]) + (1 if v in cur[v] else 0) * 10**6, -v))
        removed.append(pick)
        cur = remove_vertices(cur, [pick])


def exact_fas(adj, vertex=False, time_limit=10.0) -> FeedbackResult:
    """Kleinstes Feedback Arc Set (oder, mit `vertex=True`, Feedback Vertex Set) per ILP.

    Der Plan zerfällt in starke Komponenten, jede wird für sich gelöst. In jeder Komponente minimiert ein ILP die Zahl der gestrichenen Beziehungen (Aufgaben),
    und zwar unter Kreisbedingungen "von jedem bekannten Kreis wird mindestens eine Beziehung (Aufgabe) gestrichen". Alle Kreise vorab aufzuzählen ist unmöglich;
    deshalb startet man mit dem kürzesten Kreis durch jede Beziehung, löst, sucht in der Lösung verbliebene Kreise und lädt sie nach, bis keiner mehr bleibt.
    Zeitgrenze `time_limit` in Sekunden für den ganzen Lauf: danach gilt Status "time_limit" mit zulässiger Lösung (Heuristik oder letzte kreisfreie Zwischenlösung)
    und der bis dahin bewiesenen unteren Schranke."""
    from scipy.optimize import LinearConstraint, milp   # lazy: schwerer Import erst, wenn er gebraucht wird

    deadline = time.monotonic() + time_limit
    removed: list = []
    rounds_total = constraints_total = lower = 0
    status = "optimal"
    for comp in nontrivial_components(adj):
        members = set(comp)
        sub = {v: tuple(w for w in adj[v] if w in members) for v in comp}
        idx = {v: i for i, v in enumerate(comp)}
        sadj = tuple(tuple(idx[w] for w in sub[v]) for v in comp)
        edges = edge_list(sadj)
        nvar = len(sadj) if vertex else len(edges)
        eidx = {e: i for i, e in enumerate(edges)}
        rows: list = []
        seen_rows: set = set()

        def add_row(cycle):
            key = frozenset(cycle) if vertex else frozenset(_cycle_edges(cycle))
            if key in seen_rows:
                return False
            seen_rows.add(key)
            row = np.zeros(nvar)
            if vertex:
                for v in cycle:
                    row[v] = 1
            else:
                for e in _cycle_edges(cycle):
                    row[eidx[e]] = 1
            rows.append(row)
            return True

        for a, b in edges:
            cyc = _cycle_nodes_through_edge(sadj, a, b)
            if cyc:
                add_row(cyc)
        solution = None                      # kreisfreie Lösung dieser Komponente (lokale Nummern), falls gefunden
        bound = 0
        timed_out = False
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            rounds_total += 1
            res = milp(c=np.ones(nvar), integrality=np.ones(nvar), bounds=(0, 1),
                       constraints=[LinearConstraint(np.array(rows), lb=1, ub=np.inf)], options={"time_limit": max(0.05, remaining)})
            if res.x is None or res.status not in (0, 1):
                timed_out = True
                break
            if res.status == 1:
                timed_out = True            # Zeitgrenze im ILP: Lösung nicht bewiesen
                bound = max(bound, math.ceil((getattr(res, "mip_dual_bound", None) or 0) - 1e-6))
            else:
                bound = int(round(res.fun))
            x = np.round(res.x).astype(int)
            if vertex:
                chosen = [i for i in range(nvar) if x[i]]
                rest = remove_vertices(sadj, chosen)
            else:
                chosen = [edges[i] for i in range(nvar) if x[i]]
                rest = remove_edges(sadj, chosen)
            added = 0
            for cc in nontrivial_components(rest):
                cyc = _shortest_cycle_in(rest, cc)
                if cyc and add_row(cyc):
                    added += 1
            if not added:
                solution = chosen
                break
            if timed_out:
                break
        constraints_total += len(rows)
        lower += bound
        if timed_out:
            status = "time_limit"
        if solution is not None:
            removed.extend(comp[i] for i in solution) if vertex else removed.extend((comp[a], comp[b]) for a, b in solution)
        elif vertex:
            graph = tuple(sub[v] if v in members else () for v in range(len(adj)))
            removed.extend(_heuristic_vertices(graph))
        else:
            graph = tuple(sub[v] if v in members else () for v in range(len(adj)))
            pos = {v: i for i, v in enumerate(els_order(graph))}
            removed.extend((a, b) for a in comp for b in sub[a] if pos[a] >= pos[b])
    removed_t = tuple(sorted(removed))
    return FeedbackResult(removed_t, status, rounds_total, constraints_total, len(removed_t) if status == "optimal" else lower)


def _shortest_cycle_in(adj, nodes):
    """Kürzester Kreis in den Aufgaben `nodes` (Breitensuche von jeder Aufgabe aus); Folge von Aufgaben."""
    best = None
    for s in nodes:
        parent = {s: None}
        queue = deque([s])
        found = None
        while queue and found is None:
            v = queue.popleft()
            for w in adj[v]:
                if w == s:
                    found = v
                    break
                if w not in parent:
                    parent[w] = v
                    queue.append(w)
        if found is not None:
            cyc = [found]
            while cyc[-1] != s:
                cyc.append(parent[cyc[-1]])
            cyc = tuple(reversed(cyc))
            if best is None or len(cyc) < len(best):
                best = cyc
    return best


# --- Reduktionsregeln für die Knotenversion -----------------------------------------------------------------------------------------------

def reduce_fvs(adj) -> Reduction:
    """Reduktionsregeln für das Feedback Vertex Set (nur Aufgaben streichen):
    R1 Eigenschleife: die Aufgabe muss in die Lösung. R2 Eingrad oder Ausgrad 0: die Aufgabe liegt auf keinem Kreis, weg damit.
    R3 Eingrad 1 (Vorgänger u): die Aufgabe wird in u hineingezogen (Kanten u -> w statt v -> w); Ausgrad 1 entsprechend. Entsteht dabei eine Eigenschleife, gilt R1.
    Jede Regel ändert den kleinsten Wert nicht: Lösung der Regeln plus Lösung des Restes ist eine kleinste Lösung des Plans."""
    n = len(adj)
    out = {v: set(adj[v]) - {v} for v in range(n)}
    inn: dict[int, set] = {v: set() for v in range(n)}
    for v in range(n):
        for w in out[v]:
            inn[w].add(v)
    alive = set(range(n))
    taken: list[int] = []
    counts = {"R1 Eigenschleife": 0, "R2 Grad 0": 0, "R3 Grad 1": 0}
    steps: list[tuple] = []

    def edges_alive():
        return sum(len(out[v]) for v in alive)

    def drop(v):
        alive.discard(v)
        for w in out.pop(v):
            inn[w].discard(v)
        for u in inn.pop(v):
            out[u].discard(v)

    for v in range(n):
        if v in adj[v]:
            drop(v)
            taken.append(v)
            counts["R1 Eigenschleife"] += 1
    steps.append(("Ausgangslage (ohne Eigenschleifen)", len(alive), edges_alive()))
    changed = True
    while changed:
        changed = False
        for v in sorted(alive):
            if v not in alive:
                continue
            if not out[v] or not inn[v]:
                drop(v)
                counts["R2 Grad 0"] += 1
                changed = True
            elif len(inn[v]) == 1 or len(out[v]) == 1:
                if len(inn[v]) == 1:
                    (u,) = inn[v]
                    succ = set(out[v])
                    drop(v)
                    new = [(u, w) for w in succ]
                else:
                    (w,) = out[v]
                    pred = set(inn[v])
                    drop(v)
                    new = [(u, w) for u in pred]
                counts["R3 Grad 1"] += 1
                changed = True
                loop_at = None
                for a, b in new:
                    if a == b:
                        loop_at = a
                    elif a in alive and b in alive:
                        out[a].add(b)
                        inn[b].add(a)
                if loop_at is not None and loop_at in alive:
                    drop(loop_at)
                    taken.append(loop_at)
                    counts["R1 Eigenschleife"] += 1
        steps.append(("nach einer Runde der Regeln", len(alive), edges_alive()))
    rest_nodes = tuple(sorted(alive))
    rest_adj = tuple(tuple(sorted(out[v])) if v in alive else () for v in range(n))
    return Reduction(tuple(sorted(taken)), rest_adj, rest_nodes, tuple(steps), counts)


def fvs_with_rules(adj, time_limit=10.0):
    """Knotenversion: erst die Regeln, dann ILP auf dem Rest. Gibt (Ergebnis, Reduktion); das Ergebnis enthält die Aufgaben der Regeln und des Restes."""
    red = reduce_fvs(adj)
    if not red.rest_nodes:
        return FeedbackResult(red.taken, "optimal", 0, 0, len(red.taken)), red
    res = exact_fas(red.rest_adj, vertex=True, time_limit=time_limit)
    removed = tuple(sorted(red.taken + res.removed))
    lower = len(red.taken) + (res.lower_bound or 0)
    return FeedbackResult(removed, res.status, res.rounds, res.constraints, len(removed) if res.status == "optimal" else lower), red
