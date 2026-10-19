"""Szenario: Erzeugung ist deterministisch, die Zahl der Beziehungen und Widersprüche stimmt, die Wunschreihenfolge erklärt die Richtungen."""

import kau_algorithm as A
import kau_scenario as S


def test_same_input_gives_the_same_instance_and_the_seed_matters():
    a = S.make_instance(30, 2.0, 3, 17)
    assert a == S.make_instance(30, 2.0, 3, 17)
    assert a != S.make_instance(30, 2.0, 3, 18)


def test_number_of_relations_is_n_times_degree_capped_by_all_pairs():
    assert S.make_instance(12, 2.0, 0, 1).m == 24
    assert S.edge_count(6, 6.0) == 15 and S.make_instance(6, 6.0, 0, 1).m == 15
    assert S.edge_count(100, 3.5) == 350


def test_without_contradictions_every_relation_points_forward_in_the_plan():
    inst = S.make_instance(50, 3.0, 0, 4)
    pos = inst.position()
    assert all(pos[a] < pos[b] for a in range(inst.n) for b in inst.adj[a])
    assert inst.reversed_edges == frozenset() and A.is_acyclic(inst.adj)


def test_exactly_back_relations_point_backwards_and_striking_them_restores_a_dag():
    for back in (1, 2, 7):
        inst = S.make_instance(60, 3.0, back, 9)
        pos = inst.position()
        backwards = {(a, b) for a in range(inst.n) for b in inst.adj[a] if pos[a] > pos[b]}
        assert len(backwards) == back and backwards == set(inst.reversed_edges)
        assert A.is_feedback_edge_set(inst.adj, sorted(inst.reversed_edges))


def test_back_is_capped_at_the_number_of_relations_and_reversing_all_stays_acyclic():
    inst = S.make_instance(8, 1.0, 100, 3)          # 8 Beziehungen, alle umgedreht
    assert len(inst.reversed_edges) == inst.m == 8 and A.is_acyclic(inst.adj)


def test_plan_is_a_permutation_and_there_are_no_self_loops_or_duplicates():
    inst = S.make_instance(40, 4.0, 5, 2)
    assert sorted(inst.plan) == list(range(40))
    for a in range(inst.n):
        assert a not in inst.adj[a] and len(set(inst.adj[a])) == len(inst.adj[a]) and list(inst.adj[a]) == sorted(inst.adj[a])


def test_same_generator_as_the_first_two_pieces_of_the_series():
    """Dieselbe Instanz wie im Lehrbeispiel von di-kreis-demo (12 Aufgaben, Grad 2, ein Widerspruch, Seed 7): Kreis 5 → 7 → 12 → 5 ab 1 gezählt."""
    inst = S.make_instance(12, 2.0, 1, 7)
    assert inst.m == 24 and len(inst.reversed_edges) == 1
    comps = A.nontrivial_components(inst.adj)
    assert len(comps) == 1 and {4, 6, 11} <= set(comps[0])


def test_from_adjacency_defaults_to_the_numbering():
    inst = S.from_adjacency([[2], [], []])
    assert inst.plan == (0, 1, 2) and inst.adj == ((2,), (), ())
