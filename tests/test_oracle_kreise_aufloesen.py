"""Orakel-Test kreise-aufloesen-demo: Feedback Arc/Vertex Set gegen DP über Teilmengen, Brute Force und networkx (DEMO-PLAYBOOK §12).

Unabhängiger Rechenweg: die Mindestzahl rückwärts laufender Beziehungen über alle Reihenfolgen (DP über Teilmengen, n <= 11), das Absuchen aller Teilmengen
von Beziehungen bzw. Aufgaben (kleine Pläne), `networkx` für Kreisfreiheit und Komponenten. Feste Instanzen (range, kein Zufall), zusammen weit unter 10 Sekunden."""

import itertools
import random

import pytest

import kau_algorithm as A
import kau_scenario as S

from conftest import dp_min_back_edges

nx = pytest.importorskip("networkx")


def _graph(adj):
    g = nx.DiGraph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from((a, b) for a in range(len(adj)) for b in adj[a])
    return g


def _plans(count=150, nmin=5, nspan=7):
    """Feste Pläne: kleine Größen, dünn bis dicht, ein bis viele Widersprüche."""
    for s in range(count):
        n = nmin + s % nspan
        yield S.make_instance(n, (1.5, 2.0, 3.0)[s % 3], (1, 2, 4, 6)[s % 4], 500 + s)


def test_exact_arc_set_equals_the_dp_over_orderings():
    nonzero = 0
    for inst in _plans():
        res = A.exact_fas(inst.adj)
        assert res.size == dp_min_back_edges(inst.adj) and res.status == "optimal", inst.adj
        nonzero += res.size > 0
    assert nonzero >= 80                                                    # genug Pläne mit Kreis, damit der Test etwas prüft


def test_exact_arc_set_equals_the_smallest_subset_found_by_brute_force():
    for inst in _plans(60, 4, 4):
        adj = inst.adj
        edges = A.edge_list(adj)
        best = next(k for k in range(len(edges) + 1) if any(A.is_feedback_edge_set(adj, c) for c in itertools.combinations(edges, k)))
        assert A.exact_fas(adj).size == best


def test_exact_vertex_set_equals_the_smallest_subset_found_by_brute_force():
    for inst in _plans(100, 5, 6):
        adj = inst.adj
        best = next(k for k in range(len(adj) + 1) if any(A.is_feedback_vertex_set(adj, c) for c in itertools.combinations(range(len(adj)), k)))
        assert A.exact_fas(adj, vertex=True).size == best == A.fvs_with_rules(adj)[0].size


def test_every_solution_is_feasible_and_a_proven_optimum_is_minimal():
    for inst in _plans(80):
        adj = inst.adj
        res = A.exact_fas(adj)
        assert nx.is_directed_acyclic_graph(_graph(A.remove_edges(adj, res.removed)))
        for e in res.removed:                                                # nichts davon kann man weglassen
            assert not A.is_feedback_edge_set(adj, [x for x in res.removed if x != e])


def test_heuristics_are_feasible_and_never_better_than_the_optimum():
    worse_els = worse_greedy = 0
    for inst in _plans(120, 6, 8):
        adj = inst.adj
        opt = A.exact_fas(adj).size
        els = A.els_fas(adj)
        assert A.is_feedback_edge_set(adj, els.removed) and els.size >= opt
        greedy = A.greedy_cover(adj)
        assert greedy is not None and A.is_feedback_edge_set(adj, greedy.removed) and greedy.size >= opt
        worse_els += els.size > opt
        worse_greedy += greedy.size > opt
    assert worse_els >= 10                                                  # beide Zweige kommen vor: die Heuristik trifft das Optimum und verfehlt es
    assert worse_greedy >= 0


def test_the_vertex_optimum_is_at_most_the_arc_optimum_and_never_larger_than_the_contradictions():
    strictly = 0
    for inst in _plans(120, 6, 8):
        adj = inst.adj
        fvs, fas = A.exact_fas(adj, vertex=True).size, A.exact_fas(adj).size
        assert fvs <= fas <= len(inst.reversed_edges)
        strictly += fvs < fas
    assert strictly >= 5


def test_reduction_rules_plus_ilp_on_the_rest_equal_the_ilp_on_the_whole_plan():
    solved_alone = 0
    for inst in _plans(150, 8, 20):
        adj = inst.adj
        res, red = A.fvs_with_rules(adj)
        assert res.size == A.exact_fas(adj, vertex=True).size and A.is_feedback_vertex_set(adj, res.removed)
        solved_alone += not red.rest_nodes
        for v in red.rest_nodes:                                             # der Rest besteht nur aus Aufgaben auf Kreisen des Restes
            assert red.rest_adj[v] and any(v in red.rest_adj[u] for u in range(len(adj)))
    assert solved_alone >= 20


def test_components_equal_networkx_and_the_solution_lies_inside_them():
    for inst in _plans(100, 6, 10):
        adj = inst.adj
        g = _graph(adj)
        ref = sorted(sorted(c) for c in nx.strongly_connected_components(g) if len(c) > 1)
        assert sorted(A.nontrivial_components(adj)) == ref
        inside = {v for c in ref for v in c}
        assert all(a in inside and b in inside for a, b in A.exact_fas(adj).removed)


def test_the_size_does_not_depend_on_the_numbering_of_tasks():
    rng = random.Random(5)
    for inst in _plans(60, 6, 6):
        adj = inst.adj
        n = len(adj)
        perm = list(range(n))
        rng.shuffle(perm)
        renamed = [[] for _ in range(n)]
        for a in range(n):
            for b in adj[a]:
                renamed[perm[a]].append(perm[b])
        renamed = tuple(tuple(sorted(w)) for w in renamed)
        assert A.exact_fas(adj).size == A.exact_fas(renamed).size and A.exact_fas(adj, vertex=True).size == A.exact_fas(renamed, vertex=True).size


def test_striking_the_contradictions_always_leaves_a_plan_without_cycles():
    for inst in _plans(100, 6, 10):
        assert A.is_feedback_edge_set(inst.adj, sorted(inst.reversed_edges))


def test_random_digraphs_without_a_planted_order_are_solved_exactly_too():
    rng = random.Random(11)
    for _ in range(40):
        n = rng.randrange(6, 11)
        adj = [[] for _ in range(n)]
        for _e in range(rng.randrange(n, 3 * n)):
            a, b = rng.randrange(n), rng.randrange(n)
            if b not in adj[a]:
                adj[a].append(b)
        adj = tuple(tuple(sorted(w)) for w in adj)
        assert A.exact_fas(adj).size == dp_min_back_edges(adj)
