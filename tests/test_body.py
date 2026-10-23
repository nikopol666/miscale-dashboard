from datetime import date

from app.body import age_on, compute


def test_age():
    assert age_on(date(1990, 6, 15), date(2026, 6, 14)) == 35
    assert age_on(date(1990, 6, 15), date(2026, 6, 15)) == 36


def test_without_impedance_only_basic_metrics():
    out = compute(80, None, 178, date(1990, 1, 1), True, date(2026, 1, 1))
    assert out["bmi"] == 25.2
    assert "bmr" in out and "visceral_fat" in out
    assert "body_fat" not in out


def test_with_impedance_is_plausible():
    out = compute(80, 500, 178, date(1990, 1, 1), True, date(2026, 1, 1))
    assert 10 < out["body_fat"] < 35
    assert abs(out["fat_mass"] + out["lean_mass"] - 80) < 0.05
    assert 50 < out["muscle_mass"] < 70
    assert 45 < out["water"] < 65


def test_higher_impedance_means_more_fat():
    low = compute(80, 400, 178, date(1990, 1, 1), True, date(2026, 1, 1))
    high = compute(80, 700, 178, date(1990, 1, 1), True, date(2026, 1, 1))
    assert high["body_fat"] > low["body_fat"]


def test_female_formulas():
    out = compute(60, 550, 165, date(1995, 5, 5), False, date(2026, 1, 1))
    assert 15 < out["body_fat"] < 45

def test_bmr_over_legacy_male_limit_keeps_formula():
    # Previously this valid measurement jumped to an artificial 5000 kcal.
    out = compute(132, 510, 180, date(1989, 1, 1), True, date(2026, 10, 23))
    assert out["bmr"] == 2387
    assert out["body_fat"] > 0


def test_bmr_over_legacy_female_limit_keeps_formula():
    out = compute(240, None, 168, date(1994, 1, 1), False, date(2026, 1, 1))
    assert out["bmr"] == 2796
    assert out["bmr"] != 5000


def test_bmr_has_no_discontinuity_near_old_limit():
    low = compute(127, None, 180, date(1989, 1, 1), True, date(2026, 10, 23))["bmr"]
    high = compute(128, None, 180, date(1989, 1, 1), True, date(2026, 10, 23))["bmr"]
    assert 0 < high - low < 25
