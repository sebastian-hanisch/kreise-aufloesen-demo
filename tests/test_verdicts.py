"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds; ohne diese Datei überleben fast alle Mutanten der Verdikt-Arithmetik."""

import dataclasses

import kau_algorithm as A
import kau_evaluation as ev
import kau_scenario as S

from conftest import MINI


def _analysis(name):
    adj = MINI[name][0]
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset(A.exact_fas(adj).removed))
    return ev.analyse_instance(inst, ev.Settings())


# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

def test_question_without_a_cycle():
    kind, text = ev.verdict_question(_analysis("dag"))
    assert kind == "success" and "kreisfrei" in text and "nichts gestrichen" in text


def test_question_names_optimum_heuristic_greedy_and_nodes():
    kind, text = ev.verdict_question(_analysis("k3"))                                  # kleinste Lösung 3 bei 3 Widersprüchen (die Lösung selbst)
    assert kind == "info"
    assert "**Es genügt, 3 Beziehungen zu streichen** (bewiesen kleinste Zahl), so viele, wie der Plan Widersprüche hat (3)." in text
    assert "Die Heuristik von Eades, Lin und Smyth trifft mit 3 Beziehungen das Optimum; die Greedy-Abdeckung trifft mit 3 Beziehungen das Optimum." in text
    assert "Als Aufgaben gerechnet genügen 2 Aufgaben." in text


def test_question_uses_singular_and_fewer_than_the_contradictions():
    a = _analysis("zwei_dreiecke")
    a = dataclasses.replace(a, inst=S.Instance(a.inst.adj, a.inst.plan, frozenset({(0, 1), (1, 2), (3, 1)})))      # drei „Widersprüche“, das Optimum ist 1
    text = ev.verdict_question(a)[1]
    assert "**Es genügt, 1 Beziehung zu streichen**" in text and "weniger als die Zahl der Widersprüche (3)" in text and "Als Aufgaben gerechnet genügt 1 Aufgabe." in text


def test_question_names_the_gap_of_a_heuristic_and_a_missing_greedy():
    a = _analysis("k3")
    worse = dataclasses.replace(a, els=dataclasses.replace(a.els, removed=a.els.removed + ((0, 2),)), greedy=None)
    text = ev.verdict_question(worse)[1]
    assert "streicht 4 Beziehungen (1 mehr als nötig)" in text and "die Greedy-Abdeckung ist nicht berechenbar, weil die Kreise nicht aufzählbar sind" in text


def test_question_with_more_strikes_than_contradictions():
    a = _analysis("k3")
    fewer = dataclasses.replace(a, inst=S.Instance(a.inst.adj, a.inst.plan, frozenset({(0, 1)})))
    assert "mehr als die Zahl der Widersprüche (1)" in ev.verdict_question(fewer)[1]


def test_question_with_a_time_limit_names_the_bound_and_the_proof_status():
    a = _analysis("k3")
    timed = dataclasses.replace(a, exact=dataclasses.replace(a.exact, status="time_limit", lower_bound=2),
                                vertex=dataclasses.replace(a.vertex, status="time_limit"))
    kind, text = ev.verdict_question(timed)
    assert kind == "warning" and "**Zeitgrenze erreicht:**" in text
    assert "zulässige, aber nicht bewiesene Lösung mit 3 Beziehungen; bewiesen ist nur, dass mindestens 2 Beziehungen nötig sind" in text
    assert "(die Heuristik von Eades, Lin und Smyth streicht 3 Beziehungen, der Plan hat 3 Widersprüche)" in text and "(nicht bewiesen)" in text


# --- E1 ---------------------------------------------------------------------------------------------------------------------------------

def _c(k, exact, els, els_equal, greedy_done, greedy_equal, less=30, gap=5, n=30):
    return {"back": k, "n": 40, "instances": n, "k": k, "exact": exact, "less_than_k": less, "els": els, "els_equal": els_equal, "els_gap_max": gap, "greedy_done": greedy_done,
            "greedy_equal": greedy_equal, "greedy_skipped": n - greedy_done, "component": 20, "component_edges": 70, "rounds": 1, "constraints": 20}


def test_compare_names_optimum_heuristic_and_greedy():
    rows = [_c(2, 1, 1, 25, 30, 30, less=24), _c(8, 3, 5, 6, 30, 26), _c(24, 8, 12.5, 0, 13, 6, gap=10)]
    kind, text = ev.verdict_compare(rows)
    assert kind == "info"
    assert "im Median 3 bei 8 Widersprüchen und 8 bei 24, in 30 von 30 Plänen kleiner als die Zahl der Widersprüche" in text
    assert "trifft das Optimum in 25 von 30 Plänen bei 2 Widersprüchen, in 0 von 30 bei 24 (bis 10 Beziehungen zu viel)" in text
    assert "trifft es in 62 von 73 berechenbaren Plänen; bei 24 Widersprüchen sind 17 von 30 Plänen nicht berechenbar" in text


def test_compare_warns_if_the_optimum_exceeds_the_number_of_contradictions():
    assert ev.verdict_compare([_c(2, 3, 3, 1, 1, 1), _c(4, 3, 3, 1, 1, 1)])[0] == "warning"


# --- E2 ---------------------------------------------------------------------------------------------------------------------------------

def _s(n, k, exact, els, comp, rounds=1, cons=40):
    return {"n": n, "back": k, "instances": 10, "k": k, "exact": exact, "els": els, "els_gap_max": 3, "component": comp, "rounds": rounds, "constraints": cons}


def test_scale_names_every_size_and_the_solver_effort():
    kind, text = ev.verdict_scale([_s(60, 9, 3, 3.5, 17, 1.5, 14.5), _s(200, 30, 7, 13.5, 85.5, 1.5, 84.5)])
    assert kind == "info"
    assert "bei 60 Aufgaben (9 Widersprüche) 3 gegen 3,5 der Heuristik; bei 200 Aufgaben (30 Widersprüche) 7 gegen 13,5 der Heuristik" in text
    assert "Die größte Komponente hat bei 200 Aufgaben 85,5 Aufgaben; der Löser braucht im Median 1,5 Runden und 84,5 Kreisbedingungen." in text
    assert ev.verdict_scale([_s(60, 9, 3, 3, 17)])[0] == "warning"                 # Heuristik trifft das Optimum: kein Abstand


# --- E3 ---------------------------------------------------------------------------------------------------------------------------------

def _v(back, edge, vertex, ok=True):
    return {"back": back, "n": 40, "instances": 20, "edge_version": edge, "vertex_version": vertex, "never_larger": ok}


def test_vertex_names_both_versions_and_the_property():
    kind, text = ev.verdict_vertex([_v(4, 1, 1), _v(8, 3, 2.5), _v(16, 6, 4)])
    assert kind == "info"
    assert "bei 4 Widersprüchen 1 Beziehung oder 1 Aufgabe; bei 8 Widersprüchen 3 Beziehungen oder 2,5 Aufgaben; bei 16 Widersprüchen 6 Beziehungen oder 4 Aufgaben" in text
    assert "in allen Plänen höchstens so groß wie die Kantenversion." in text
    assert ev.verdict_vertex([_v(4, 1, 1, ok=False)])[0] == "warning" and "nicht in allen Plänen" in ev.verdict_vertex([_v(4, 1, 1, ok=False)])[1]


# --- E4 ---------------------------------------------------------------------------------------------------------------------------------

def _r(n, share, before, rest_nodes, rest_edges, alone, taken=3):
    return {"n": n, "share": share, "back": 9, "instances": 20, "before": before, "rest_nodes": rest_nodes, "rest_edges": rest_edges, "taken": taken, "alone": alone}


def test_rules_name_the_share_solved_alone_and_the_remaining_core():
    rows = [_r(60, 0.05, 21.5, 0, 0, 17), _r(100, 0.05, 48, 0, 0, 17), _r(200, 0.15, 142, 63, 258, 0)]
    kind, text = ev.verdict_rules(rows)
    assert kind == "info"
    assert "Bei 5 % Widersprüchen lösen die Regeln die Knotenversion allein: bei 60 Aufgaben in 17 von 20, bei 100 Aufgaben in 17 von 20 Plänen." in text
    assert "Bei 15 % Widersprüchen und 200 Aufgaben bleibt im Median ein Rest von 63 von 142 Aufgaben und 258 Beziehungen (allein gelöst in 0 von 20)." in text


def test_rules_without_a_high_share_row_and_a_warning_when_they_never_solve_alone():
    assert "Bei 15 %" not in ev.verdict_rules([_r(60, 0.05, 21.5, 0, 0, 17)])[1]
    assert ev.verdict_rules([_r(60, 0.05, 21.5, 5, 10, 0)])[0] == "warning"


# --- E5 ---------------------------------------------------------------------------------------------------------------------------------

def _h(n, exact, els, rounds, cons, optimal=3):
    return {"n": n, "out": 3.0, "back": 10, "instances": 3, "exact": exact, "els": els, "rounds": rounds, "constraints": cons, "optimal": optimal}


def test_hardness_names_sizes_rounds_and_status():
    rows = [_h(30, [13, 13, 12], [16, 17, 19], [8, 5, 4], [58, 48, 50]), _h(100, [27, 26, 28], [51, 47, 45], [32, 8, 25], [175, 151, 171])]
    kind, text = ev.verdict_hardness(rows, 30)
    assert kind == "info"
    assert "30 Sekunden Zeitgrenze: bei 30 Aufgaben: kleinste Lösung 12 bis 13 gegen 16 bis 19 der Heuristik, 4 bis 8 Runden, 48 bis 58 Bedingungen" in text
    assert "bei 100 Aufgaben: kleinste Lösung 26 bis 28 gegen 45 bis 51 der Heuristik, 8 bis 32 Runden, 151 bis 175 Bedingungen. Bewiesen optimal in 6 von 6 Läufen." in text


def test_hardness_warns_if_a_run_hit_the_time_limit():
    rows = [_h(30, [13], [16], [4], [48], optimal=0)]
    assert ev.verdict_hardness(rows, 30)[0] == "warning"
