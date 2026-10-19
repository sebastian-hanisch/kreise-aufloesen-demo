"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Pläne, Grenzen inklusive, Gleichstände, Regler-Extreme, Zeitgrenze."""

import kau_algorithm as A
import kau_constants as C
import kau_evaluation as ev
import kau_scenario as S

from conftest import MINI


def test_exactly_two_tasks_with_and_without_a_cycle():
    """n = 2: der kleinste Fall, in dem es etwas zu streichen gibt."""
    assert A.exact_fas(((1,), ())).size == 0
    res = A.exact_fas(((1,), (0,)))
    assert res.size == 1 and res.status == "optimal" and A.exact_fas(((1,), (0,)), vertex=True).size == 1


def test_empty_plan_and_single_task():
    for adj in ((), ((),)):
        assert A.exact_fas(adj).size == A.exact_fas(adj, vertex=True).size == A.els_fas(adj).size == 0
        assert A.greedy_cover(adj).size == 0 and A.reduce_fvs(adj).rest_nodes == () and A.nontrivial_components(adj) == []


def test_the_smallest_slider_plan_is_valid():
    a = ev.analyse(ev.Settings(C.N_MIN, C.OUT_MIN, C.BACK_MIN, 1))
    assert a.inst.n == 6 and a.inst.m == 3 and not a.has_cycle and ev.validate(a) == []


def test_more_contradictions_than_relations_are_capped_and_stay_acyclic():
    a = ev.analyse(ev.Settings(C.N_MIN, C.OUT_MIN, C.BACK_MAX, 1))
    assert len(a.inst.reversed_edges) == a.inst.m == 3 and not a.has_cycle


def test_the_largest_slider_plan_finishes_with_a_status_and_validates():
    """Worst-Case am Regler-Maximum (n = 100, Grad 3,5, alle Widersprüche, kürzeste Zeitgrenze): kein Hänger, zulässige Lösung, Status ausgewiesen. Keine Zeit-Assertion."""
    a = ev.analyse(ev.Settings(C.N_MAX, C.OUT_MAX, C.BACK_MAX, 3, C.TIME_LIMITS[0]))
    assert a.exact.status in ("optimal", "time_limit") and a.vertex.status in ("optimal", "time_limit") and ev.validate(a) == []


def test_every_time_limit_value_gives_a_valid_run_on_a_small_plan():
    for limit in C.TIME_LIMITS:
        a = ev.analyse(ev.Settings(20, 2.0, 5, 3, limit))
        assert a.exact.status == "optimal" and ev.validate(a) == []


def test_the_largest_plan_without_contradictions_is_acyclic_and_cheap():
    a = ev.analyse(ev.Settings(C.N_MAX, C.OUT_MAX, 0, 3, 1))
    assert not a.has_cycle and a.exact.size == 0 and a.exact.rounds == 0 and ev.validate(a) == []


def test_ties_in_greedy_prefer_the_smaller_edge():
    """Zwei gleich belegte Beziehungen: die kleinere gewinnt (dokumentierte Regel)."""
    adj = MINI["zwei_disjunkt"][0]                      # zwei getrennte Dreiecke: jede Beziehung liegt auf genau einem Kreis
    assert A.greedy_cover(adj).removed == ((0, 1), (3, 4))


def test_a_self_loop_is_always_struck_in_every_version():
    adj = MINI["schleife"][0]
    assert A.exact_fas(adj).removed == ((0, 0),) and A.exact_fas(adj, vertex=True).removed == (0,) and A.els_fas(adj).removed == ((0, 0),)


def test_bounds_are_inclusive():
    """Reglergrenzen gelten inklusive: n = 6 und n = 100, Widersprüche 0 und 200 sind erlaubt."""
    for n in (C.N_MIN, C.N_MAX):
        for back in (C.BACK_MIN, C.BACK_MAX):
            assert S.make_instance(n, 2.0, back, 1).n == n


def test_a_tiny_deadline_never_returns_an_infeasible_set():
    for name, (adj, _, _) in MINI.items():
        r = A.exact_fas(adj, time_limit=0.0)
        assert A.is_feedback_edge_set(adj, r.removed) and r.lower_bound is not None and r.lower_bound <= r.size, name
        v = A.exact_fas(adj, vertex=True, time_limit=0.0)
        assert A.is_feedback_vertex_set(adj, v.removed), name
