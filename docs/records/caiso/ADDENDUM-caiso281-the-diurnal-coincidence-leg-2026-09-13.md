# ADDENDUM caiso-281 — the diurnal coincidence leg (Gate D), fixed before it is computed

**Charter:** `docs/PRECOMMIT-caiso281-is-the-marginal-hr-bias-a-measured-input-defect-2026-09-13.md`
**Date:** 2026-09-13 · **LP budget: still ZERO** · keeper unchanged.

## Why an addendum rather than a note in the RESULT

The charter's Gate C measured what it was written to measure and **did not kill**: the per-plant
2022↔2025 dispatch errors correlate at Pearson **+0.553**. The charter's ungated reporting items
then showed the fleet error is **≈100 % shape, ~0 % level**, with a repeating hour-of-day
signature in both years. That makes one further question decisive for naming the successor object
— *does the price error sit where the gas error sits?* — and the charter did not pre-register it.

Adding a measurement is fine; adding it **without a rule** is how a result gets chosen. So the
rule is fixed here and pushed before the number exists, exactly as caiso-280 did.

## Gate D — the rule

**Both series, both years (2022, 2025), from COMMITTED artifacts only:**

* **gas error** `E(h)` = Σ over CEMS gas plants of (model − actual) MW — the charter's Gate C
  series, already built from payload `plants[].m` and bench `plants[].campd`.
* **model price** `λ(h)` = demand-weighted mean over zones of `price` at `pass == "P1"` from the
  keeper bundle's `hourly/system_<year>.parquet` (2022: the folded rung's bundle).
* **actual price** `π(h)` = `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`, the
  canonical committed series the C3c scorer itself reads, with the **same `rt`→`da` NaN fallback**
  `render_calibration_html._actual_lmp_hourly` applies. No new construction is invented.
* **price error** `Δπ(h) = λ(h) − π(h)`.

**G-REPRO (a hard stop, not a formality):** the reconstruction must reproduce the committed 2022
model load-weighted price **94.069 $/MWh** and the gated actual **84.490 $/MWh** to within
**±0.15 $/MWh**. If it does not, the construction is a different object from the one C3a scores
and **Gate D is abandoned, not adjusted.**

**The metric:** Pearson *r* between `E` and `Δπ` across the **288 (month × hour-of-day) buckets**
of each year (bucket means of both series). Reported at 24-bucket hour-of-day grain as well.

**The sign is predicted here, before the number, and is allowed to be wrong:** more model gas in
an hour means the LP has cleared **deeper** into its own offer stack, so **`r > 0` is the
substitution story's prediction.** (An earlier scratch reading of caiso-280's over-import argued
the opposite sign; it is superseded by this written prediction, which is the one that counts.)

* **D-COINCIDENT:** `r ≥ +0.35` in **both** years → the price error and the gas-burn error are
  carried by the **same diurnal redistribution** → a common root exists and it is **timing**, not
  offer level.
* **D-KILL:** `|r| < 0.20` in either year → the two are separate objects; the handoff §4 direction
  dies on this limb whatever Gate C said.
* Otherwise **INDETERMINATE** — reported as such, and an indeterminate names no successor.

## What Gate D cannot do

It is an **association at bucket grain**, not a causal identification, and it is stated that way
in the RESULT. It can name a successor object for a later lane to test with an arm; it **cannot**
promote anything, cannot move a mechanism cell, and cannot license a multiplier at any value
(rule 1 `[R-STRUCT]` (c) is untouched). No LP is spent on it.
