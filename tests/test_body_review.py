"""Guard against impossible jumps in Xiaomi-derived body metrics.

Cases are synthetic; neither profile nor readings belong to a real user.
"""

from datetime import date

from app.body import _schofield_bmr, compute


def test_who_schofield_adult_bmr_reference_values():
    assert round(_schofield_bmr(80, 36, True)) == 1791
    assert round(_schofield_bmr(60, 36, False)) == 1333
    assert round(_schofield_bmr(80, 28, True)) == 1897
    assert round(_schofield_bmr(60, 65, False)) == 1203


def test_heavier_profile_has_plausible_bmr_and_stable_composition():
    out = compute(132, 510, 180, date(1989, 1, 1), True, date(2026, 10, 23))
    assert out["bmr"] == 2387
    assert out["bmi"] == 40.7
    assert out["visceral_fat"] == 17.8
    assert out["body_fat"] == 41.3


def test_female_visceral_low_weight_branch():
    out = compute(60, 550, 165, date(1995, 5, 5), False, date(2026, 1, 1))
    assert 4 < out["visceral_fat"] < 6


def test_male_visceral_branch_uses_offset_threshold():
    out = compute(100, 480, 180, date(1989, 1, 1), True, date(2026, 10, 23))
    assert 10 < out["visceral_fat"] < 16


def test_high_weight_keeps_internal_mass_balance_without_sentinels():
    out = compute(230, 700, 180, date(1989, 1, 1), True, date(2026, 10, 23))
    assert abs(out["fat_mass"] + out["lean_mass"] - 230) < 0.02
    assert abs(out["muscle_mass"] + out["bone_mass"] - out["lean_mass"]) < 0.02
    assert 5 <= out["body_fat"] <= 75
    assert 35 <= out["water"] <= 75
    assert 5 <= out["protein"] <= 32


def test_without_impedance_does_not_generate_body_composition():
    out = compute(80, None, 178, date(1990, 1, 1), True, date(2026, 1, 1))
    assert "body_fat" not in out
    assert "bmr" in out
