"""Zweige der Hauptansicht (Nullspalte-Lehre): Jeder Weg, den die App zeigt, kommt in mindestens einem Preset oder einer festen Instanz vor.

Ein Preset, das seine Beschreibung nicht einlöst (z. B. „Greedy braucht alle Kreise“ mit berechenbarer Greedy-Lösung), fällt hier auf.
Zeitabhängig ist nur der Status „Zeitgrenze erreicht“ im Preset „Zeitgrenze erreicht“: der Plan braucht bis zum Beweis ein Vielfaches der einen Sekunde."""

import pytest

import kau_algorithm as A
import kau_constants as C
import kau_evaluation as ev
import kau_scenario as S


def _a(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["n"], p["out"], p["back"], p["seed"], p["limit"]))


def test_lehrbeispiel_needs_fewer_strikes_than_there_are_contradictions():
    a = _a("Lehrbeispiel (12 Aufgaben)")
    assert a.exact.status == "optimal" and a.exact.size < len(a.inst.reversed_edges) and a.has_cycle


def test_the_optimum_is_far_below_the_number_of_contradictions():
    a = _a("Weniger als die Widersprüche")
    assert a.exact.status == "optimal" and a.exact.size * 2 <= len(a.inst.reversed_edges) and a.greedy is not None and a.greedy.size == a.exact.size


def test_the_heuristic_misses_the_optimum_by_a_lot():
    a = _a("Die Heuristik liegt daneben")
    assert a.exact.status == "optimal" and a.els.size >= 2 * a.exact.size


def test_the_greedy_cover_is_not_computable_in_its_preset():
    a = _a("Greedy braucht alle Kreise")
    assert a.greedy is None and a.exact.status == "optimal" and "nicht berechenbar" in ev.verdict_question(a)[1]


def test_the_rules_alone_solve_the_vertex_version_in_their_preset():
    a = _a("Regeln lösen alles")
    assert a.reduction.rest_nodes == () and a.vertex.status == "optimal" and a.vertex.size == len(a.reduction.taken) and a.vertex.rounds == 0


def test_the_rules_leave_a_rest_for_the_ilp_in_their_preset():
    a = _a("Regeln reichen nicht")
    assert len(a.reduction.rest_nodes) >= 10 and a.vertex.rounds >= 1 and a.vertex.size > len(a.reduction.taken)


def test_the_time_limit_preset_reports_an_unproven_but_feasible_solution():
    a = _a("Zeitgrenze erreicht")
    assert a.exact.status == "time_limit" and A.is_feedback_edge_set(a.inst.adj, a.exact.removed)
    assert 0 <= a.exact.lower_bound <= a.exact.size and "Zeitgrenze erreicht" in ev.verdict_question(a)[1]


def test_an_acyclic_plan_has_nothing_to_strike():
    a = ev.analyse(ev.Settings(12, 2.0, 0, 1))
    assert not a.has_cycle and a.exact.size == a.vertex.size == a.els.size == 0 and a.greedy.size == 0 and ev.validate(a) == []
    assert ev.verdict_question(a)[0] == "success"


def test_every_method_is_available_in_some_preset():
    assert {"exakt", "els", "greedy"} <= {p["method"] for p in C.PRESETS.values()}


def test_a_plan_where_striking_the_contradictions_is_optimal_exists():
    """Die Widersprüche sind manchmal selbst das Optimum (ein einziger Widerspruch, der einen Kreis schließt): beide Zweige „kleiner als k“ und „gleich k“ kommen vor."""
    equal = fewer = 0
    for s in range(40):
        inst = S.make_instance(30, 3.0, 1, s)
        res = A.exact_fas(inst.adj)
        equal += res.size == len(inst.reversed_edges) and res.size > 0
        fewer += res.size < len(inst.reversed_edges)
    assert equal >= 1 and fewer >= 1


@pytest.mark.parametrize("name", [n for n in C.PRESETS if n != "Zeitgrenze erreicht"])
def test_every_preset_passes_the_validation(name):
    assert ev.validate(_a(name)) == []


def test_the_time_limit_preset_passes_the_validation_too():
    assert ev.validate(_a("Zeitgrenze erreicht")) == []
