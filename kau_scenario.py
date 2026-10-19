"""Szenario: Aufgabenabhängigkeiten mit verdeckter Wunschreihenfolge (derselbe Generator wie in di-kreis-demo, Stück 1 der Reihe).

Die Aufgaben 0 bis n-1 tragen zufällige Nummern. Eine verdeckte Wunschreihenfolge `plan` ordnet sie; jede Beziehung „a vor b“ läuft
zunächst von früh nach spät. Dann werden `back` Beziehungen umgedreht: das sind die Widersprüche (Rückwärtskanten). Ob daraus ein
gerichteter Kreis entsteht, hängt an der Erreichbarkeit, nicht an der Zahl der Widersprüche. Der Zufall kommt nur aus `random.Random.random()`
(Mersenne-Twister, über Python-Versionen und Plattformen gleich), damit Zahlen in Tests und README reproduzierbar bleiben."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Instance:
    adj: tuple[tuple[int, ...], ...]   # adj[a] = Aufgaben, die nach a kommen sollen (aufsteigend sortiert)
    plan: tuple[int, ...]              # verdeckte Wunschreihenfolge: plan[i] = Aufgabe an Position i
    reversed_edges: frozenset          # die umgedrehten Beziehungen als (a, b)

    @property
    def n(self) -> int:
        return len(self.adj)

    @property
    def m(self) -> int:
        return sum(len(w) for w in self.adj)

    def position(self) -> tuple[int, ...]:
        """position()[v] = Stelle von Aufgabe v in der Wunschreihenfolge."""
        pos = [0] * self.n
        for i, v in enumerate(self.plan):
            pos[v] = i
        return tuple(pos)


def _below(rng: random.Random, k: int) -> int:
    """Gleichverteilte ganze Zahl 0 bis k-1 aus rng.random() (versionsstabil)."""
    return int(rng.random() * k)


def edge_count(n: int, avg_out: float) -> int:
    """Zahl der Beziehungen: n mal mittlerer Ausgangsgrad, höchstens alle Paare."""
    return min(int(round(n * avg_out)), n * (n - 1) // 2)


def make_instance(n: int, avg_out: float, back: int, seed: int) -> Instance:
    """Deterministisch aus (n, avg_out, back, seed). `back` wird auf die Zahl der Beziehungen begrenzt."""
    rng = random.Random(seed)
    plan = list(range(n))
    for i in range(n - 1, 0, -1):               # Fisher-Yates mit rng.random()
        j = _below(rng, i + 1)
        plan[i], plan[j] = plan[j], plan[i]
    pos = [0] * n
    for i, v in enumerate(plan):
        pos[v] = i
    m = edge_count(n, avg_out)
    edges: set[tuple[int, int]] = set()
    while len(edges) < m:
        a, b = _below(rng, n), _below(rng, n)
        if a == b:
            continue
        if pos[a] > pos[b]:
            a, b = b, a
        edges.add((a, b))
    edge_list = sorted(edges)
    k = max(0, min(int(back), len(edge_list)))
    idx = list(range(len(edge_list)))
    for i in range(k):                           # Teilmischung: die ersten k Plätze
        j = i + _below(rng, len(idx) - i)
        idx[i], idx[j] = idx[j], idx[i]
    flip = set(idx[:k])
    adj: list[list[int]] = [[] for _ in range(n)]
    flipped = set()
    for i, (a, b) in enumerate(edge_list):
        if i in flip:
            adj[b].append(a)
            flipped.add((b, a))
        else:
            adj[a].append(b)
    return Instance(tuple(tuple(sorted(w)) for w in adj), tuple(plan), frozenset(flipped))


def from_adjacency(adj, plan=None) -> Instance:
    """Instanz aus fester Adjazenz (Mini-Instanzen in Tests); ohne Plan gilt die Nummernfolge."""
    adj_t = tuple(tuple(sorted(w)) for w in adj)
    plan_t = tuple(plan) if plan is not None else tuple(range(len(adj_t)))
    return Instance(adj_t, plan_t, frozenset())
