"""Jede Einheit an den von Hand gerechneten Mini-Instanzen (conftest.MINI), DEMO-PLAYBOOK §1b.

Handrechnungen stehen als Kommentar neben dem erwarteten Wert."""

import pytest

import kau_algorithm as A

from conftest import MINI, diamond_chain


def _adj(name):
    return MINI[name][0]


@pytest.mark.parametrize("name", list(MINI))
def test_exact_edge_version_finds_the_hand_computed_optimum(name):
    adj, fas, _ = MINI[name]
    res = A.exact_fas(adj)
    assert res.size == fas and res.status == "optimal" and res.lower_bound == fas and A.is_feedback_edge_set(adj, res.removed)


@pytest.mark.parametrize("name", list(MINI))
def test_exact_vertex_version_finds_the_hand_computed_optimum(name):
    adj, _, fvs = MINI[name]
    res = A.exact_fas(adj, vertex=True)
    assert res.size == fvs and res.status == "optimal" and A.is_feedback_vertex_set(adj, res.removed)


@pytest.mark.parametrize("name", list(MINI))
def test_the_rules_plus_ilp_find_the_same_vertex_optimum(name):
    adj, _, fvs = MINI[name]
    res, red = A.fvs_with_rules(adj)
    assert res.size == fvs and A.is_feedback_vertex_set(adj, res.removed) and set(red.taken) <= set(res.removed)


@pytest.mark.parametrize("name", list(MINI))
def test_every_heuristic_is_feasible_and_never_better_than_the_optimum(name):
    adj, fas, _ = MINI[name]
    els = A.els_fas(adj)
    assert A.is_feedback_edge_set(adj, els.removed) and els.size >= fas and els.status == "heuristic"
    greedy = A.greedy_cover(adj)
    assert greedy is not None and A.is_feedback_edge_set(adj, greedy.removed) and greedy.size >= fas


def test_triangle_els_strikes_the_closing_edge():
    assert A.els_order(_adj("dreieck")) == (0, 1, 2) and A.els_fas(_adj("dreieck")).removed == ((2, 0),)       # kein Quell-/Senkenknoten: 0 wandert nach vorn


def test_els_puts_sources_first_and_sinks_last():
    adj = _adj("dag")
    order = A.els_order(adj)
    assert order[0] == 0 and order[-1] == 3 and A.els_fas(adj).removed == ()


def test_els_is_optimal_on_the_complete_digraphs_with_three_and_four_tasks():
    assert A.els_fas(_adj("k3")).size == 3 and A.els_fas(_adj("k4")).size == 6


def test_greedy_cover_picks_the_most_covered_edge_with_the_smaller_edge_on_ties():
    res = A.greedy_cover(_adj("k3"))
    assert res.removed == ((0, 1), (0, 2), (1, 2))              # von Hand: erst (0,1) (2 Kreise), dann (0,2), dann (1,2)
    chain = diamond_chain(3)
    assert A.greedy_cover(chain).removed == ((9, 0),)            # die Rückkante liegt auf allen 8 Kreisen


def test_greedy_cover_gives_up_if_the_cycles_cannot_be_enumerated():
    assert A.greedy_cover(_adj("k4"), max_cycles=5) is None and A.greedy_cover(_adj("k4"), max_cycles=20) is not None


def test_enumerate_cycles_counts_and_aborts_like_the_known_numbers():
    assert len(A.enumerate_cycles(_adj("k4"))[0]) == 20 and len(A.enumerate_cycles(diamond_chain(3))[0]) == 8
    cycles, aborted = A.enumerate_cycles(_adj("k4"), max_cycles=10)
    assert aborted and len(cycles) == 11


def test_components_split_the_plan_into_independent_problems():
    assert A.nontrivial_components(_adj("kreis_dahinter")) == [[1, 2]]
    assert A.nontrivial_components(_adj("zwei_disjunkt")) == [[0, 1, 2], [3, 4, 5]]
    assert A.nontrivial_components(_adj("dag")) == [] and A.nontrivial_components(_adj("schleife")) == [[0]]
    assert sorted(map(tuple, A.sccs(_adj("k3")))) == [(0, 1, 2)]


def test_the_exact_solver_reports_rounds_and_constraints():
    res = A.exact_fas(_adj("zwei_dreiecke"))
    assert res.rounds >= 1 and res.constraints >= 2                # kürzester Kreis durch jede Beziehung: mindestens die beiden Dreiecke
    assert A.exact_fas(_adj("dag")).rounds == 0 and A.exact_fas(_adj("dag")).constraints == 0


def test_time_limit_zero_returns_a_feasible_unproven_solution_with_status():
    adj = _adj("k4")
    res = A.exact_fas(adj, time_limit=0.0)
    assert res.status == "time_limit" and A.is_feedback_edge_set(adj, res.removed) and res.lower_bound <= 6
    resv = A.exact_fas(adj, vertex=True, time_limit=0.0)
    assert resv.status == "time_limit" and A.is_feedback_vertex_set(adj, resv.removed)


def test_remove_helpers_and_the_order_after_striking():
    adj = _adj("dreieck")
    assert A.remove_edges(adj, [(2, 0)]) == ((1,), (2,), ())
    assert A.remove_vertices(adj, [1]) == ((), (), (0,))                      # Aufgabe 1 weg: 2 -> 0 bleibt, 0 -> 1 entfällt
    assert A.order_after(adj, [(2, 0)]) == (0, 1, 2) and A.order_after(adj, []) is None
    assert A.order_after(adj, [1], vertex=True) == (2, 0)


def test_checkers_reject_wrong_answers():
    adj = _adj("dreieck")
    assert A.is_feedback_edge_set(adj, [(0, 1)]) and not A.is_feedback_edge_set(adj, []) and not A.is_feedback_edge_set(adj, [(0, 2)])
    assert not A.is_feedback_edge_set(adj, [(0, 1), (0, 1)])                # doppelt
    assert A.is_feedback_vertex_set(adj, [2]) and not A.is_feedback_vertex_set(adj, []) and not A.is_feedback_vertex_set(adj, [7])
    assert A.is_acyclic(_adj("dag")) and not A.is_acyclic(adj) and A.topological_order(adj) is None


def test_reduction_rules_solve_a_triangle_alone():
    red = A.reduce_fvs(_adj("dreieck"))
    assert red.taken == (2,) and red.rest_nodes == () and red.counts["R3 Grad 1"] == 2 and red.counts["R1 Eigenschleife"] == 1
    assert red.steps[0] == ("Ausgangslage (ohne Eigenschleifen)", 3, 3)


def test_reduction_rules_remove_tasks_outside_cycles_and_keep_the_core():
    red = A.reduce_fvs(_adj("kreis_dahinter"))
    assert red.taken == (2,) and red.rest_nodes == () and red.counts["R2 Grad 0"] >= 1
    k4 = A.reduce_fvs(_adj("k4"))
    assert k4.taken == () and k4.rest_nodes == (0, 1, 2, 3) and sum(k4.counts.values()) == 0                # jede Aufgabe hat Ein- und Ausgrad 3


def test_self_loop_rule_takes_the_task():
    red = A.reduce_fvs(((0, 1), (0,)))
    assert 0 in red.taken and red.counts["R1 Eigenschleife"] >= 1
    res, _ = A.fvs_with_rules(((0, 1), (0,)))
    assert res.removed == (0,)


def test_els_order_follows_the_documented_sink_and_source_sequence():
    # DAG 0 -> 1, 0 -> 2, 1 -> 3, 2 -> 3. Von Hand: Senke 3 nach hinten; dann Quellen in aufsteigender Reihenfolge: 0, danach 1 und 2 (werden nach dem Entfernen von 0 zu Quellen)
    assert A.els_order(_adj("dag")) == (0, 1, 2, 3)


def test_the_vertex_heuristic_prefers_a_self_loop_and_then_the_hub():
    hub = ((1, 2, 3), (0,), (0,), (0,))                          # drei Kreise durch die Aufgabe 0
    assert A._heuristic_vertices(hub) == (0,)
    with_loop = ((1, 2, 3), (0,), (0, 2), (0,))                  # Aufgabe 2 hat eine Eigenschleife und muss zuerst genommen werden
    removed = A._heuristic_vertices(with_loop)
    assert 2 in removed and A.is_feedback_vertex_set(with_loop, removed)


def test_solutions_are_returned_sorted():
    res = A.exact_fas(_adj("zwei_disjunkt"))
    assert res.removed == tuple(sorted(res.removed)) and len(res.removed) == 2
    assert A.exact_fas(_adj("zwei_disjunkt"), vertex=True).removed == tuple(sorted(A.exact_fas(_adj("zwei_disjunkt"), vertex=True).removed))
    assert A.greedy_cover(_adj("zwei_disjunkt")).removed == tuple(sorted(A.greedy_cover(_adj("zwei_disjunkt")).removed))
