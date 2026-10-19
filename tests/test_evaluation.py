"""Auswertung: Analyse von Mini-Instanzen, Prüfung vor der Anzeige, Formate."""

import dataclasses

import kau_algorithm as A
import kau_evaluation as ev
import kau_scenario as S

from conftest import MINI


def _analysis(name, **kw):
    adj = MINI[name][0]
    reversed_edges = frozenset(A.exact_fas(adj).removed)        # Handbeispiel: die Widersprüche sind eine kleinste Lösung
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), reversed_edges)
    return ev.analyse_instance(inst, ev.Settings(**kw))


def test_analysis_of_the_complete_digraph_on_three_tasks():
    a = _analysis("k3")
    assert a.has_cycle and a.exact.size == 3 and a.vertex.size == 2 and a.els.size == 3 and a.greedy.size == 3 and a.baseline.size == 3
    assert a.components == ((0, 1, 2),) and a.reduction.rest_nodes == (0, 1, 2) and ev.validate(a) == []


def test_analysis_of_a_triangle_is_solved_by_the_rules_alone():
    a = _analysis("dreieck")
    assert a.vertex.size == 1 and a.reduction.rest_nodes == () and a.vertex.rounds == 0 and ev.validate(a) == []


def test_result_by_method_name():
    a = _analysis("zwei_dreiecke")
    assert a.result("exakt") is a.exact and a.result("els") is a.els and a.result("greedy") is a.greedy and a.result("widersprueche") is a.baseline


def test_validate_names_every_kind_of_error():
    a = _analysis("k3")
    bad_exact = dataclasses.replace(a, exact=dataclasses.replace(a.exact, removed=a.exact.removed[:1]))
    assert any("„Exakt“" in p for p in ev.validate(bad_exact))
    bad_els = dataclasses.replace(a, els=dataclasses.replace(a.els, removed=()))
    assert any("Eades" in p for p in ev.validate(bad_els))
    bad_greedy = dataclasses.replace(a, greedy=dataclasses.replace(a.greedy, removed=()))
    assert any("Greedy" in p for p in ev.validate(bad_greedy))
    bad_base = dataclasses.replace(a, baseline=dataclasses.replace(a.baseline, removed=()))
    assert any("Widersprüche zurückdrehen" in p for p in ev.validate(bad_base))
    bad_vertex = dataclasses.replace(a, vertex=dataclasses.replace(a.vertex, removed=()))
    assert any("Knotenversion macht" in p for p in ev.validate(bad_vertex))


def test_validate_catches_a_heuristic_that_beats_the_proven_optimum_and_a_non_minimal_solution():
    a = _analysis("k3")
    cheat = dataclasses.replace(a, els=dataclasses.replace(a.els, removed=a.els.removed[:2]))
    assert any("weniger als das bewiesene Optimum" in p or "nicht kreisfrei" in p for p in ev.validate(cheat))
    padded = dataclasses.replace(a, exact=dataclasses.replace(a.exact, removed=a.exact.removed + ((0, 2),)))
    problems = ev.validate(padded)
    assert any("weglassen" in p for p in problems) or any("doppelt" in p or "nicht kreisfrei" in p for p in problems)


def test_validate_catches_a_bound_above_the_size_and_a_strike_in_an_acyclic_plan():
    a = _analysis("k3")
    assert any("untere Schranke" in p for p in ev.validate(dataclasses.replace(a, exact=dataclasses.replace(a.exact, lower_bound=99))))
    dag = _analysis("dag")
    assert ev.validate(dag) == []
    fake = dataclasses.replace(dag, exact=dataclasses.replace(dag.exact, removed=((0, 1),)))
    assert any("kreisfrei" in p for p in ev.validate(fake))


def test_validate_catches_a_vertex_version_larger_than_the_edge_version():
    a = _analysis("dreieck")                      # Kantenversion 1; zwei gestrichene Aufgaben sind zulässig, aber größer
    big = dataclasses.replace(a, vertex=dataclasses.replace(a.vertex, removed=(0, 1)))
    assert any("größer als die Kantenversion" in p for p in ev.validate(big))


def test_labels_and_plurals():
    assert ev.label(0) == "1" and ev.format_edge((3, 8)) == "4 → 9"
    assert ev.beziehungen(1) == "1 Beziehung" and ev.beziehungen(1234) == "1.234 Beziehungen" and ev.aufgaben(1) == "1 Aufgabe" and ev.aufgaben(2) == "2 Aufgaben"
    assert ev.widersprueche(1) == "1 Widerspruch" and ev.widersprueche(8) == "8 Widersprüche"
    assert ev._count(1, "Beziehung", "Beziehungen") == "1 Beziehung" and ev._count(2.5, "Aufgabe", "Aufgaben") == "2,5 Aufgaben" and ev._count(0, "Aufgabe", "Aufgaben") == "0 Aufgaben"
    assert set(ev.STATUS_NAMES) == {"optimal", "time_limit", "heuristic"}
