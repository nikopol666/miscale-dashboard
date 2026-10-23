# Body composition calculations

Only **weight** and **electrical impedance** are directly measured by the Xiaomi Mi
Body Composition Scale 2. Body fat, muscle, water, protein, bone and visceral fat are
**estimates**, not measurements or medical diagnoses. Their error can be large,
particularly at high BMI. They are best used for trends under consistent measurement
conditions, not as absolute clinical values.

## BMR

The dashboard estimates basal metabolic rate (kcal/day) from sex, age and weight
using the **Schofield (1985) equations**, as published by FAO/WHO/UNU. The earlier
legacy formula could show a fictitious 5000 kcal/day; this sentinel is removed.

Reference table:
https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/339317/SACN_Dietary_Reference_Values_for_Energy.pdf

The model is a population estimate, not a measurement of an individual's metabolic
rate. For clinically important energy planning, indirect calorimetry is the reference
method. For severe obesity, a 2024 systematic review found WHO and Harris-Benedict
performed relatively well on average, while individual error still varied:
https://pubmed.ncbi.nlm.nih.gov/38548479/

## Other values

The legacy impedance-derived Xiaomi-style formulas are retained for continuity,
with fixes to the male/female visceral fat branches and with numeric guardrails.
Artificial jumps to 75% body fat, 8 kg bone mass and 120 kg muscle mass were removed.
These changes eliminate programming anomalies; they do not prove the underlying
impedance-derived estimates are clinically accurate.

To recalculate an existing profile's previously stored metrics, save that profile
again in the dashboard UI. New weigh-ins use the current formula automatically.
