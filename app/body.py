"""Body composition estimates from a Mi Scale weight and impedance reading.

Weight and impedance are measured; the remaining outputs are model-based estimates.
BMR uses the published WHO/Schofield weight-and-age equations (kcal/day).
The impedance-derived estimates retain the dashboard's legacy Xiaomi-compatible model.
"""

from datetime import date


def age_on(birth: date, day: date) -> int:
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def _schofield_bmr(weight_kg: float, age: int, male: bool) -> float:
    """FAO/WHO/UNU Schofield (1985) weight-only BMR, in kcal/day."""
    if male:
        table = ((3, 59.512, -30.4), (10, 22.706, 504.3),
                 (18, 17.686, 658.2), (30, 15.057, 692.2),
                 (60, 11.472, 873.1), (float("inf"), 11.711, 587.7))
    else:
        table = ((3, 58.317, -31.1), (10, 20.317, 485.9),
                 (18, 13.38, 692.6), (30, 14.818, 486.6),
                 (60, 8.126, 845.6), (float("inf"), 9.082, 658.5))
    for upper_age, slope, intercept in table:
        if age < upper_age:
            return slope * weight_kg + intercept
    raise AssertionError("unreachable")


def compute(weight: float, impedance: int | None, height_cm: float, birth: date,
            male: bool, day: date | None = None) -> dict:
    day = day or date.today()
    age = age_on(birth, day)
    h = height_cm
    sex = 1 if male else 0
    out = {"bmi": round(weight / (h / 100) ** 2, 1), "age": age}

    out["bmr"] = round(min(max(_schofield_bmr(weight, age, male), 500), 5000))

    if sex == 0:
        if weight > h * 0.5 - 13:
            sub = h * 1.45 + h * 0.1158 * h - 120
            visceral = (weight * 500 / sub - 6) + age * 0.07
        else:
            # The previous version accidentally subtracted height twice and age once.
            visceral = weight * (0.691 - 0.0024 * h) - 0.027 * h - 10.5 + age * 0.07
    else:
        if h < weight * 1.6 + 63:
            sub = h * 0.0826 * h - h * 0.4
            visceral = weight * 305 / (sub + 48) - 2.9 + age * 0.15
        else:
            sub = 0.765 - h * 0.0015
            visceral = weight * sub - h * 0.143 + age * 0.15 - 5
    out["visceral_fat"] = round(min(max(visceral, 1), 50), 1)

    if not impedance:
        return out

    lbm_coeff = (h * 9.058 / 100) * (h / 100) + weight * 0.32 + 12.226 - impedance * 0.0068 - age * 0.0542

    lbm_sub = 0.8
    if sex == 0:
        lbm_sub = 9.25 if age <= 49 else 7.25
    coeff = 1.0
    if sex == 1 and weight < 61:
        coeff = 0.98
    elif sex == 0 and weight > 60:
        coeff = 0.96 * (1.03 if h > 160 else 1)
    elif sex == 0 and weight < 50:
        coeff = 1.02 * (1.03 if h > 160 else 1)
    fat = (1 - ((lbm_coeff - lbm_sub) * coeff) / weight) * 100
    # Avoid discontinuities like 63.01% jumping to exactly 75%.
    fat = min(max(fat, 5), 75)

    base = 0.245691014 if sex == 0 else 0.18016894
    bone = (base - lbm_coeff * 0.05158) * -1
    bone = bone + 0.1 if bone > 2.2 else bone - 0.1
    bone = min(max(bone, 0.5), 8)

    # Muscle is the residual of the lean mass after bone; no artificial 120kg spike.
    muscle = max(0, weight - fat * 0.01 * weight - bone)

    water = (100 - fat) * 0.7
    water *= 1.02 if water < 50 else 0.98
    water = min(max(water, 35), 75)
    protein = min(max(muscle / weight * 100 - water, 5), 32)

    out.update({
        "body_fat": round(fat, 1),
        "fat_mass": round(weight * fat / 100, 2),
        "muscle_mass": round(muscle, 2),
        "bone_mass": round(bone, 2),
        "water": round(water, 1),
        "protein": round(protein, 1),
        "lean_mass": round(weight - weight * fat / 100, 2),
    })
    return out
