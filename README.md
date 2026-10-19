# Kreise auflösen: wie wenig muss man streichen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-kreise-aufloesen-demo.streamlit.app/)** -->

Drittes Stück der Reihe **Ordnung und Abhängigkeit** (Arbeitstitel der Linie `dag-abhaengigkeiten`) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Bereich Graphentheorie. Zusammenfluss von `di-kreis-demo` (Stück 1: ein Kreis als Beleg) und `alle-kreise-demo` (Stück 2: alle Kreise, Belegung der Beziehungen); derselbe Generator, dieselbe Nummerierung. Vehikel: **Aufgabenabhängigkeiten** („A vor B“) mit verdeckter Wunschreihenfolge, bei der ein einstellbarer Teil der Beziehungen umgedreht wird (Widersprüche). Die Demo fragt: **Welche wenigen Beziehungen (oder Aufgaben) muss man streichen, damit der Plan aufgeht**, und wie gut sind Faustregeln gegenüber dem Optimum? Das ist das **Feedback Arc Set** und seine Knotenversion, das **Feedback Vertex Set**.

Nachbarn: `scc-demo` zerlegt Graphen in starke Zusammenhangskomponenten; die Kemeny-Aggregation (Ranking-Linie) ist dasselbe Problem auf vollständigen Vergleichen und wird hier nicht behandelt.

## Warum dieses Problem

Wer einen widersprüchlichen Plan reparieren soll, möchte so wenig wie möglich ändern. Die Zahl der Widersprüche scheint ein Maß dafür, ist aber ein schlechtes: Das Optimum liegt meist weit darunter. Und es gibt zwei Faustregeln, die verlockend sind (die Heuristik von Eades, Lin und Smyth; die Beziehung mit den meisten Kreisen streichen), deren Güte man erst am exakten Wert sieht.

## Befunde und Korrekturen gegenüber dem Plan

- **Zahlen des Einzelplans bestätigt, Bedingungen anders gezählt.** Optimum, Heuristik, Greedy-Abdeckung und Komponentengrößen sind mit dem Demo-Code und den festen Plänen identisch zur Vormessung. Die Zahl der Kreisbedingungen des Lösers ist kleiner (1,5 bis 52 statt 5,5 bis 88), weil die Demo gleiche Kreise nur einmal zählt; sie hängt außerdem vom Löser ab und steht deshalb nur als Größenordnung im README und nur als Band im Test.
- **Bei Zeitgrenze:** Der Löser liefert die letzte kreisfreie Zwischenlösung oder, wenn es keine gibt, die Lösung der Heuristik (Kantenversion) bzw. einer Gradheuristik (Knotenversion), jeweils mit dem Status „Zeitgrenze erreicht“ und der bis dahin bewiesenen unteren Schranke.
- **Regler „Widersprüche“ bis 200** (statt 100 im Plan), damit auch ein zur Hälfte umgedrehter Plan mit 100 Aufgaben und Grad 3,5 einstellbar ist (Preset „Zeitgrenze erreicht“).
- **Härtegrenze nur als Größenordnung.** Bei 100 Aufgaben und Ausgangsgrad 4 brauchte HiGHS in der Vormessung über 100 Runden und eine bis zweieinhalb Minuten je Plan (einmalig gemessen, kein Test); darum endet der Regler bei Grad 3,5 und der Löser hat eine Zeitgrenze.

## Modell

Aufgaben 0 bis n−1 mit zufälligen Nummern; eine **verdeckte Wunschreihenfolge** ordnet sie. Es gibt m = n · (mittlerer Ausgangsgrad) Beziehungen (höchstens alle Paare), jede zunächst von früh nach spät. Danach werden die einstellbaren **Widersprüche** umgedreht (nie mehr als Beziehungen). Der Zufall kommt aus `random.Random(seed).random()`. Die Widersprüche selbst zurückzudrehen ist immer eine zulässige Lösung (der Erzeuger kennt sie, die Verfahren nicht). Aufgaben sind in der Anzeige ab 1 nummeriert. Details und Formeln: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Zerlegung** in starke Komponenten (Kosaraju, iterativ): Kreise liegen nur darin, jede Komponente wird für sich gelöst.
- **Eades–Lin–Smyth** (1993): Reihenfolge aus Senken (nach hinten), Quellen (nach vorn) und der Aufgabe mit dem größten Unterschied aus Aus- und Eingrad; gestrichen werden die rückwärts laufenden Beziehungen. Keine Gütegarantie.
- **Greedy-Abdeckung:** auf allen Kreisen (Johnson, Stück 2) wiederholt die Beziehung streichen, die die meisten noch offenen Kreise enthält; nur berechenbar, wenn die Kreise innerhalb eines Budgets aufzählbar sind.
- **Exakt:** je Komponente ein ILP (`scipy.optimize.milp`, HiGHS) mit nachgeladenen Kreisbedingungen: Start mit dem kürzesten Kreis durch jede Beziehung, lösen, in der Lösung verbliebene Kreise als Bedingung ergänzen, wiederholen (Baharev u. a. 2021; die Gegenposition Grötschel u. a. 2022 steht im Expander der App). Zeitgrenze und Status werden immer ausgewiesen.
- **Knotenversion:** Reduktionsregeln (Eigenschleife → in die Lösung; Eingrad oder Ausgrad 0 → weg; Eingrad oder Ausgrad 1 → in Vorgänger bzw. Nachfolger hineinziehen), dann das ILP auf dem Rest.
- **Unabhängige Prüfer:** `is_feedback_edge_set`, `is_feedback_vertex_set`, Kreisfreiheit; die App prüft jede Lösung vor der Anzeige (zulässig, nicht besser als das bewiesene Optimum, nichts davon weglassbar, Knoten- höchstens Kantenversion).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Mediane über feste Pläne, nie ein einzelner Zufalls-Seed.

| Frage | Befund |
|---|---|
| Wie klein ist das Optimum? (40 Aufgaben, Grad 3, 30 Pläne je Zeile) | Bei 2 / 4 / 8 / 12 / 16 / 24 Widersprüchen genügen im Median **1 / 2 / 3 / 5 / 6 / 8** Beziehungen; ab 4 Widersprüchen ist das Optimum in **30 von 30** Plänen kleiner als die Zahl der Widersprüche (bei 2 in 24 von 30). |
| Wie gut ist die Heuristik von Eades, Lin und Smyth? | Median **1 / 2 / 5 / 7 / 9 / 12,5** Beziehungen; sie trifft das Optimum in **25 / 16 / 6 / 2 / 0 / 0 von 30** Plänen, im ungünstigsten Plan streicht sie bis zu **10** Beziehungen zu viel. Bei 200 Aufgaben und 30 Widersprüchen: 13,5 gegen 7. |
| Wie gut ist die Greedy-Abdeckung? | Sie trifft das Optimum in **30 / 30 / 26 / 22 / 18 / 6** Plänen, ist aber nur berechenbar, wenn die Kreise aufzählbar sind: bei 24 Widersprüchen in **13 von 30** Plänen (17 nicht berechenbar). |
| Warum geht der exakte Löser schnell? | Die größte Komponente hat im Median **4 / 8 / 20 / 27 / 29 / 32,5** von 40 Aufgaben; der Löser braucht im Median meist **eine bis zwei Runden** (Band 1 bis 3, lösungsabhängig). Bei 200 Aufgaben ist die größte Komponente **85,5** Aufgaben groß. |
| Aufgaben statt Beziehungen? (20 Pläne je Zeile) | Bei 4 / 8 / 16 Widersprüchen im Median **1 / 2,5 / 4** Aufgaben gegen **1 / 3 / 6** Beziehungen; die Knotenversion ist in allen 60 Plänen höchstens so groß wie die Kantenversion. |
| Wie weit kommen die Reduktionsregeln allein? (Knotenversion, 20 Pläne je Fall) | Bei 5 % Widersprüchen lösen sie den Plan allein in **17 / 17 / 15 von 20** Plänen (60 / 100 / 200 Aufgaben); bei 200 Aufgaben und 15 % bleibt im Median ein Rest von **63 von 142** Aufgaben und 258 Beziehungen (allein gelöst in 0 von 20). |
| Was ändert sich bei zufallsähnlichen Plänen? (die Hälfte umgedreht, je 3 Pläne) | Optimum **12 bis 13 / 18 bis 20 / 26 bis 28** Beziehungen bei 30 / 60 / 100 Aufgaben gegen **16 bis 19 / 27 bis 29 / 45 bis 51** der Heuristik; alle 9 Läufe bewiesen optimal innerhalb der Zeitgrenze von 30 Sekunden. |
| Ist der Löser korrekt? | Das exakte ILP stimmt mit der Mindestzahl rückwärts laufender Beziehungen über alle Reihenfolgen (DP über Teilmengen) auf **150** festen Plänen überein und mit dem Absuchen aller Teilmengen auf kleinen Plänen (Kanten- und Knotenversion); die Regeln plus ILP stimmen mit dem ILP auf dem ganzen Plan überein, `tests/test_oracle_kreise_aufloesen.py`. |

## Ehrliche Grenzen

- **Synthetische Pläne.** Verdeckte Zufallsordnung, keine echten Bau- oder Umschlagpläne; wie klein das Optimum und wie gut die Heuristik dort sind, zeigt die Demo nicht.
- **Alle Beziehungen gleich schwer.** Mit Kosten je Beziehung wäre es ein gewichtetes Problem; die kleinste Zahl ist dann nicht die billigste Lösung.
- **Das Optimum ist nicht eindeutig.** Die Demo zeigt eine von meist mehreren gleich kleinen Lösungen.
- **Zeitgrenze statt Beweis.** Bei dichten, zufallsähnlichen Plänen steigt der Aufwand des Lösers stark; nach der Zeitgrenze ist die Lösung zulässig, aber nicht bewiesen kleinste (der Status steht immer dabei).
- **Heuristik ohne Gütegarantie, Greedy nur auf aufzählbaren Plänen:** beides ist gemessen, nicht bewiesen.
- **Größe:** bis 100 Aufgaben und Ausgangsgrad 3,5.

## Tests

Das Verzeichnis `tests/` enthält zurzeit 163 Tests (Laufzeit eine bis zwei Minuten auf dem Entwicklungsrechner, vor allem die Experimente und die Oberflächentests):

- **Kern:** jede Einheit an von Hand gerechneten Mini-Instanzen (Dreieck, zwei Dreiecke mit gemeinsamer Beziehung, zwei getrennte Dreiecke, vollständige Digraphen mit 3 und 4 Aufgaben, Kreis mit Vorlauf, Kette aus Rauten, Eigenschleife); Zerlegung, Heuristik, Greedy, ILP, Regeln, Prüfer, Zeitgrenze 0.
- **Orakel** (`test_oracle_kreise_aufloesen.py`): DP über Teilmengen (Kanten), Absuchen aller Teilmengen (Kanten und Aufgaben), `networkx` für Kreisfreiheit und Komponenten; jede kleinste Lösung ist minimal; Heuristik und Greedy nie besser als das Optimum; Knoten- höchstens Kantenversion; Regeln plus ILP gleich ILP; zufällige Digraphen ohne verdeckte Ordnung.
- **Invarianten:** Größe unabhängig von der Nummerierung; die Widersprüche zurückzudrehen ist immer zulässig.
- **Zweige** (`test_branches.py`): jedes Preset löst seine Beschreibung ein (weniger als die Widersprüche, Heuristik daneben, Greedy nicht berechenbar, Regeln lösen alles, Regeln lassen Rest, Zeitgrenze).
- **Verdikte** (`test_verdicts.py`) an handgesetzten Werten; **Befunde** (`test_claims.py`) für jede Zahl dieses README (Runden und Bedingungen nur als Band).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Layout (Schnellstart oben, aktives Preset hervorgehoben), Footer, Laufzeit-Importe (scipy und numpy stehen in `requirements.txt`), Worst-Case am Reglermaximum (n = 100, Grad 3,5, kürzeste Zeitgrenze) ohne Zeit-Assertion.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Lösen, Vergleichen, Aufgaben statt Beziehungen, fünf Experimente |
| `kau_algorithm.py` | Kern: Komponenten, Heuristik, Greedy, exakter Löser (ILP), Reduktionsregeln, Prüfer |
| `kau_constants.py` | Regler-Grenzen, Raster der Experimente, Farben, Presets |
| `kau_evaluation.py` | Analyse, Prüfung vor der Anzeige, Verdikte |
| `kau_experiments.py` | Experimente über feste Pläne |
| `kau_layout.py` | Fester Kopf (Stylesheet) |
| `kau_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kau_scenario.py` | Pläne mit verdeckter Wunschreihenfolge (derselbe Generator wie in den Stücken 1 und 2) |
| `kau_visualization.py` | Plotly-Abbildungen (Bogendiagramm mit gestrichenen Beziehungen und Aufgaben, Experimente; Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx (Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen, Orakel, Zweige, Verdikte, Befunde, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Gewichtete Beziehungen** (Kosten je Beziehung) und **Approximationsgarantien**.
- **Kemeny-Rangaggregation:** Ranking-Linie.
- **Alle Kreise aufzählen:** Stück 2; hier nur als Grundlage der Greedy-Abdeckung.
- **Echte Pläne oder Dateiimport:** die Pläne sind synthetisch.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
