"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Spezifikationen."""

import kau_constants as C
import kau_evaluation as ev
import kau_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX, name
        assert C.OUT_MIN <= p["out"] <= C.OUT_MAX and abs(p["out"] / C.OUT_STEP - round(p["out"] / C.OUT_STEP)) < 1e-9, name   # auf dem Reglerraster
        assert C.BACK_MIN <= p["back"] <= C.BACK_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert p["limit"] in C.TIME_LIMITS and p["method"] in C.METHODS, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["n"], first["out"], first["back"], first["seed"], first["limit"]) == ev.Settings()
    assert first["method"] == C.DEFAULT_METHOD


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_name_their_allowed_values():
    assert P.SETTING_SPECS["limit_select"].choices == C.TIME_LIMITS and P.SETTING_SPECS["method_select"].choices == C.METHODS
    assert C.DEFAULT_TIME_LIMIT in C.TIME_LIMITS and set(C.METHOD_NAMES) == set(C.METHODS) and list(C.TIME_LIMITS) == sorted(C.TIME_LIMITS)


def test_the_slider_maximum_allows_a_half_reversed_plan_of_the_largest_size():
    """Der Regler „Widersprüche“ reicht bis zur Hälfte der Beziehungen des größten Plans (n = 100, Grad 3,5): dort wird der Plan zufallsähnlich."""
    assert C.BACK_MAX >= C.N_MAX * C.OUT_MAX // 2
