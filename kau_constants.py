"""Konstanten: Regler-Grenzen, Raster der Experimente, Farben und Presets."""

# Rechenbudget am Regler-Maximum (n = 100, Ausgangsgrad 3,5, also m = 350 Beziehungen):
#   Zerlegung in Komponenten O(n + m); ELS O(n^2); exakter Löser: ILP mit nachgeladenen Kreisbedingungen (Zahl der Runden wächst mit der Dichte; bei n = 100 und
#   Ausgangsgrad 4 wären es über 100 Runden), deshalb eine Zeitgrenze und ein ausgewiesener Status; Greedy-Abdeckung braucht alle Kreise (Kreisbudget).
N_MIN, N_MAX, DEFAULT_N = 6, 100, 12
OUT_MIN, OUT_MAX, OUT_STEP, DEFAULT_OUT = 0.5, 3.5, 0.5, 2.0   # mittlerer Ausgangsgrad
BACK_MIN, BACK_MAX, DEFAULT_BACK = 0, 200, 3                   # umgedrehte Beziehungen (Widersprüche)
SEED_MAX, DEFAULT_SEED = 999999, 18
TIME_LIMITS = (1, 3, 10, 30)                                   # Zeitgrenze des exakten Lösers in Sekunden (je Lauf)
DEFAULT_TIME_LIMIT = 10
GREEDY_CYCLE_BUDGET = 20000                                    # so viele Kreise darf die Greedy-Abdeckung höchstens aufzählen
METHODS = ("widersprueche", "els", "greedy", "exakt")
METHOD_NAMES = {"widersprueche": "Widersprüche zurückdrehen", "els": "Eades–Lin–Smyth (Heuristik)", "greedy": "Greedy-Abdeckung (meistbelegte Beziehung)", "exakt": "Exakt (ILP)"}
DEFAULT_METHOD = "exakt"

# Feste Instanzen und Raster der Experimente (nie ein einzelner Zufalls-Seed als Befund)
E1_N, E1_OUT, E1_BACKS, E1_SEEDS = 40, 3.0, (2, 4, 8, 12, 16, 24), tuple(range(7000, 7030))
E2_NS, E2_OUT, E2_SHARE, E2_SEEDS = (60, 100, 200), 3.0, 0.05, tuple(range(13000, 13010))
E3_N, E3_OUT, E3_BACKS, E3_SEEDS = 40, 3.0, (4, 8, 16), tuple(range(14000, 14020))
E4_CASES, E4_OUT, E4_SEEDS = ((60, 0.05), (100, 0.05), (200, 0.05), (200, 0.15)), 3.0, tuple(range(15000, 15020))
E5_CASES, E5_SEEDS, E5_TIME_LIMIT = ((30, 3.0), (60, 3.0), (100, 3.0)), tuple(range(17000, 17003)), 30

# Farben
COLOR_STRUCK = "#d62728"
COLOR_FORWARD = "rgba(76,120,168,0.45)"
COLOR_BACKWARD = "rgba(148,103,189,0.65)"
COLOR_NODE = "#f2f2f2"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e45756"
COLOR_BAR = "#2F6B65"
COLOR_BAR2 = "#ff9f1c"
COLOR_BAR3 = "#59a14f"

PRESETS = {
    "Lehrbeispiel (12 Aufgaben)": {"n": DEFAULT_N, "out": DEFAULT_OUT, "back": DEFAULT_BACK, "seed": DEFAULT_SEED, "limit": DEFAULT_TIME_LIMIT, "method": "exakt"},
    "Weniger als die Widersprüche": {"n": 40, "out": 3.0, "back": 8, "seed": 6, "limit": DEFAULT_TIME_LIMIT, "method": "exakt"},
    "Die Heuristik liegt daneben": {"n": 40, "out": 3.0, "back": 16, "seed": 6, "limit": DEFAULT_TIME_LIMIT, "method": "els"},
    "Greedy braucht alle Kreise": {"n": 40, "out": 3.0, "back": 24, "seed": 2, "limit": DEFAULT_TIME_LIMIT, "method": "greedy"},
    "Regeln lösen alles": {"n": 100, "out": 3.0, "back": 15, "seed": 7, "limit": DEFAULT_TIME_LIMIT, "method": "exakt"},
    "Regeln reichen nicht": {"n": 100, "out": 3.0, "back": 40, "seed": 1, "limit": DEFAULT_TIME_LIMIT, "method": "exakt"},
    "Zeitgrenze erreicht": {"n": 100, "out": 3.5, "back": 175, "seed": 1, "limit": 1, "method": "exakt"},
}
PRESET_HELP = {
    "Lehrbeispiel (12 Aufgaben)": "Zwölf Aufgaben, drei Widersprüche: eine einzige gestrichene Beziehung genügt. Das ist die Voreinstellung.",
    "Weniger als die Widersprüche": "40 Aufgaben, acht Widersprüche: das Optimum streicht deutlich weniger Beziehungen als es Widersprüche gibt.",
    "Die Heuristik liegt daneben": "16 Widersprüche: die Heuristik von Eades, Lin und Smyth streicht mehr als doppelt so viele Beziehungen wie nötig.",
    "Greedy braucht alle Kreise": "24 Widersprüche auf 40 Aufgaben: die Kreise sind nicht aufzählbar, die Greedy-Abdeckung ist nicht berechenbar.",
    "Regeln lösen alles": "100 Aufgaben, 15 Widersprüche: die Reduktionsregeln lösen die Knotenversion ganz ohne Löser.",
    "Regeln reichen nicht": "100 Aufgaben, 40 Widersprüche: nach den Regeln bleibt ein Rest, den das ILP lösen muss.",
    "Zeitgrenze erreicht": "Ein dichter, fast zufälliger Plan mit nur einer Sekunde Zeit: der Löser meldet den Status „Zeitgrenze“ mit einer zulässigen, aber unbewiesenen Lösung.",
}
