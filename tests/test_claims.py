"""Jede Zahl im README (Abschnitt „Befunde“) wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Mediane über feste Pläne, nie ein einzelner Zufalls-Seed. Größen kleinster Lösungen sind eindeutig und damit plattformrobust (der Zielwert des ILP ist
eindeutig, auch wenn mehrere gleich kleine Lösungen existieren); **Runden und Bedingungen des Lösers** hängen vom Löser ab und stehen hier nur als Bänder."""

import kau_algorithm as A
import kau_constants as C
import kau_evaluation as ev
import kau_scenario as S

from conftest import MINI, cached


def test_the_optimum_is_far_below_the_number_of_contradictions_and_the_heuristics_drift():
    rows = cached("compare_rows")
    assert {r["instances"] for r in rows} == {30} and {r["n"] for r in rows} == {40}
    got = [(r["back"], r["exact"], r["less_than_k"], r["els"], r["els_equal"], r["els_gap_max"], r["greedy_done"], r["greedy_equal"], r["component"]) for r in rows]
    assert got == [(2, 1, 24, 1, 25, 5, 30, 30, 4), (4, 2, 30, 2, 16, 4, 30, 30, 8), (8, 3, 30, 5, 6, 6, 30, 26, 20), (12, 5, 30, 7, 2, 7, 29, 22, 27),
                   (16, 6, 30, 9, 0, 6, 26, 18, 29), (24, 8, 30, 12.5, 0, 10, 13, 6, 32.5)]
    assert [r["component_edges"] for r in rows] == [16.5, 34, 69.5, 88, 95, 104]
    assert all(1 <= r["rounds"] <= 3 and r["constraints"] >= 1 for r in rows)                  # Band: der Löser braucht meist ein bis zwei Runden


def test_larger_plans():
    rows = cached("scale_rows")
    assert [(r["n"], r["k"], r["exact"], r["els"], r["els_gap_max"], r["component"]) for r in rows] == [(60, 9, 3, 3.5, 4, 17), (100, 15, 5, 7, 7, 40), (200, 30, 7, 13.5, 10, 85.5)]
    assert all(1 <= r["rounds"] <= 3 for r in rows)


def test_edge_against_vertex_version():
    rows = cached("vertex_rows")
    assert [(r["back"], r["edge_version"], r["vertex_version"], r["never_larger"]) for r in rows] == [(4, 1, 1, True), (8, 3, 2.5, True), (16, 6, 4, True)]


def test_reduction_rules():
    rows = cached("rules_rows")
    assert [(r["n"], r["back"], r["before"], r["rest_nodes"], r["rest_edges"], r["taken"], r["alone"]) for r in rows] == [
        (60, 9, 21.5, 0, 0, 2, 17), (100, 15, 48, 0, 0, 3.5, 17), (200, 30, 77, 0, 0, 4.5, 15), (200, 90, 142, 63, 258, 1, 0)]


def test_random_like_plans_are_solved_optimally_with_growing_effort():
    rows = cached("hardness_rows")
    assert [(r["n"], r["back"], r["exact"], r["els"], r["optimal"]) for r in rows] == [
        (30, 45, [13, 13, 12], [16, 17, 19], 3), (60, 90, [20, 18, 20], [28, 27, 29], 3), (100, 150, [27, 26, 28], [51, 47, 45], 3)]
    for r in rows:                                                                             # Band: Runden und Bedingungen wachsen nicht in die Tausende
        assert all(1 <= x <= 100 for x in r["rounds"]) and all(10 <= x <= 400 for x in r["constraints"])


def test_verdict_texts_quote_the_readme_numbers():
    assert "in 30 von 30 Plänen kleiner als die Zahl der Widersprüche" in ev.verdict_compare(cached("compare_rows"))[1]
    assert "trifft es in 132 von 158 berechenbaren Plänen; bei 24 Widersprüchen sind 17 von 30 Plänen nicht berechenbar" in ev.verdict_compare(cached("compare_rows"))[1]
    assert "bei 200 Aufgaben (30 Widersprüche) 7 gegen 13,5 der Heuristik" in ev.verdict_scale(cached("scale_rows"))[1]
    assert "bei 16 Widersprüchen 6 Beziehungen oder 4 Aufgaben" in ev.verdict_vertex(cached("vertex_rows"))[1]
    assert "bei 60 Aufgaben in 17 von 20, bei 100 Aufgaben in 17 von 20, bei 200 Aufgaben in 15 von 20" in ev.verdict_rules(cached("rules_rows"))[1]


def test_the_known_numbers_of_the_mini_instances():
    """K3 hat 3 und K4 hat 6 Streichungen (jede Reihenfolge lässt die Hälfte der Beziehungen rückwärts laufen), 2 und 3 Aufgaben; eine Kette aus Rauten braucht eine."""
    assert [A.exact_fas(MINI[k][0]).size for k in ("k3", "k4", "rauten3")] == [3, 6, 1]
    assert [A.exact_fas(MINI[k][0], vertex=True).size for k in ("k3", "k4", "rauten3")] == [2, 3, 1]


def test_the_slider_maximum_has_the_documented_edge_count():
    assert S.edge_count(C.N_MAX, C.OUT_MAX) == 350 and C.BACK_MAX == 200
