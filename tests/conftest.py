"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Teure Experimente laufen einmal je Testlauf (`lru_cache`) und werden von Claims-, Verdikt- und Mutationstests gemeinsam genutzt."""

import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def diamond_chain(k):
    """k Rauten hintereinander (3i -> 3i+1 und 3i+2 -> 3i+3) mit einer Rückkante vom Ende zum Anfang: 2^k Kreise, aber eine einzige Beziehung löst alle."""
    n = 3 * k + 1
    adj = [[] for _ in range(n)]
    for i in range(k):
        adj[3 * i] += [3 * i + 1, 3 * i + 2]
        adj[3 * i + 1].append(3 * i + 3)
        adj[3 * i + 2].append(3 * i + 3)
    adj[3 * k].append(0)
    return tuple(tuple(sorted(w)) for w in adj)


# Von Hand gerechnete Mini-Instanzen: Name -> (Adjazenz, kleinstes Feedback Arc Set, kleinstes Feedback Vertex Set)
MINI = {
    "leer": ((), 0, 0),
    "dag": (((1, 2), (3,), (3,), ()), 0, 0),
    "schleife": (((0,), (0,)), 1, 1),                                    # Eigenschleife an 0 (und 1 -> 0): nur die Schleife zählt
    "dreieck": (((1,), (2,), (0,)), 1, 1),
    "zwei_dreiecke": (((1,), (2,), (0, 3), (1,)), 1, 1),                 # Kreise (0,1,2) und (1,2,3) teilen die Beziehung 1 -> 2
    "zwei_disjunkt": (((1,), (2,), (0,), (4,), (5,), (3,)), 2, 2),
    "k3": (((1, 2), (0, 2), (0, 1)), 3, 2),                              # 6 Beziehungen, jede Reihenfolge lässt 3 rückwärts laufen; 2 Aufgaben streichen
    "k4": (((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2)), 6, 3),
    "kreis_dahinter": (((1,), (2,), (1, 3), (4,), ()), 1, 1),            # 0 -> 1, Kreis 1 <-> 2, dahinter 2 -> 3 -> 4
    "rauten3": (diamond_chain(3), 1, 1),                                 # 8 Kreise, eine Rückkante löst alle
}


@pytest.fixture
def mini():
    return MINI


@lru_cache(maxsize=None)
def cached(name):
    """Einmal je Testlauf berechnete Experimente (Name der Funktion in kau_experiments)."""
    import kau_experiments as ex
    return getattr(ex, name)()


def dp_min_back_edges(adj):
    """Orakel: Mindestzahl rückwärts laufender Beziehungen über alle Reihenfolgen, per DP über Teilmengen (n <= 12); Eigenschleifen zählen immer."""
    n = len(adj)
    loops = sum(1 for a in range(n) if a in adj[a])
    inf = 10 ** 9
    best = [inf] * (1 << n)
    best[0] = 0
    for mask in range(1 << n):
        if best[mask] == inf:
            continue
        for v in range(n):
            if mask >> v & 1:
                continue
            back = sum(1 for w in adj[v] if w != v and (mask >> w & 1))
            nm = mask | 1 << v
            if best[mask] + back < best[nm]:
                best[nm] = best[mask] + back
    return best[(1 << n) - 1] + loops
