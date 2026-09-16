# PRECOMMIT (pjm-h9c) — give PJM's 2020–2022 their OWN measured offer ladders

**Session** `pjm-h9` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main`
**ZERO LP IN THE PARENT** (rule 32 `[R-SHARD]` (a)). Written **before the corpus finished
downloading** and before any 2020–2022 ladder exists.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED**, and
re-verified at HEAD this session across all six registered years
(`docs/RESULT-pjm-h9b-sixyear-resolve-2026-09-16.md`: max |keeper − re-solve| = 0.073 TWh).

**No screen.** Rule 29 `[R-SCREEN]`'s screen-year regime was removed by owner instruction this
session; this goes straight to the full span, one shard per year (rule 34 `[R-SHARD-PROMOTABLE]`
(c), and per-year is forced anyway because PJM's keeper is partitioned).

---

## 1. THE DEFECT — measured, not argued

`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json` carries own-year ladders for
**2023, 2024, 2025 only**. PJM's registered span is **2020–2025**, so in the three held-out years
the armed mechanism falls through to the surface's **`pooled`** entry — a capacity-weighted blend
*of 2023–2025* — and prices 2020, 2021 and 2022 coal and gas-steam at an average of years that
had not happened yet.

The spread is not cosmetic. `LONG_RUN` at within-unit share 0.45 (PJM coal's `committed` rung):

| net-load bin | pooled | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| 0 | 8.025 | 8.575 | 8.825 | **6.825** |
| 1 | 7.725 | 8.225 | 8.325 | **6.475** |
| 2 | 7.825 | 8.125 | 8.525 | **6.725** |
| 3 | 7.775 | 7.975 | 8.475 | 7.075 |

Own-year values range over **2.0 implied-HR units** — ~$2/MWh at 2023 gas and more at 2021–22 gas,
on 12.5 GW. The pooled value is not a measurement of any of those years.

**PJM publishes the missing years.** DataMiner2's `energy_market_offers` retention is *indefinite
from 2017-11-01*; the corpus simply was never fetched below 2023.

## 2. THE FIX

Re-derive `scripts/data/derive_pjm_offer_midcurve.py` over **`--years 2020 2021 2022 2023 2024
2025`** so each year gets its own ladder and the pooled entry becomes the six-year blend.

* **Zero new `ScenarioConfig` fields, zero free parameters, nothing swept** (rules 21 `[R-DOF]`,
  24 `[R-REGISTRY]`). The mechanism already prefers `entry["years"][str(year)]` and falls back to
  `pooled` only when that key is missing (`offer_surfaces.py`); adding the keys changes which
  branch it takes, and nothing else.
* **Rule 23 `[R-FROZEN-DERIVE]` is satisfied by the SOURCE-DATA trigger, not by a residual.** The
  derive re-runs because the corpus gained 36 month-files it never had — the commit cites that
  data change and no number is chosen.
* **Rule 13 `[R-MEASURED]`**: PJM's own published offers, the same formulaic input the keeper
  already trusts for 2023–2025, keyed on a forward-native net-load percentile and a delivered-gas
  series — so it regenerates for a forecast year.
* **Rule 14 `[R-ACCURATE]` is the whole basis.** A pooled average standing in for measured data
  the publisher retains is exactly the estimate rule 14 says to replace, and the rule's
  misalignment exception cannot apply: it is the same construction on the same feed.

## 3. THE MEASUREMENT OWED BEFORE ANY SOLVE — and it may kill the arm's scope

`_unit_physics` computes each unit's physics medians over **every file it is given**, and
`_segments` classifies on those medians. **Adding 2020–2022 can therefore move a unit between
`CT_FAST` / `CC_LIKE` / `LONG_RUN`, which would change the 2023–2025 ladders too** — a fix that
was supposed to touch only the held-out years.

Pre-registered, before the derive runs:

* **D-1 SEGMENT STABILITY.** Report `segment_units` for the six-year derive against the frozen
  three-year counts (**CT_FAST 1064 · CC_LIKE 883 · LONG_RUN 216**). Any change is reported at
  full magnitude, with the moved units' capacity.
* **D-2 IN-SAMPLE LADDER DRIFT.** Report, per (segment, bin, share), `six_year_ladder(2023..2025)
  − frozen_ladder(2023..2025)`. **If the 2023–2025 ladders move, the arm is NOT confined to the
  held-out years and the RESULT says so in its headline** — it does not get described as a
  holdout-only repair.
* **D-3 REPRODUCTION FLOOR.** pjm-h9 already measured that the frozen surface is **no longer
  byte-reproducible** from PJM's live feed (129/432 cells; segment membership exact, per-bin
  capacity weight to 1.6e-3, median 0.10 implied-HR, sign-balanced, 2025 exact —
  `docs/RESULT-pjm-h9-comparator-admixture-bound-2026-09-16.md` §3). So D-2 is read **against that
  known floor**: a drift at or below ~0.10 implied-HR median is restatement noise, not the arm.

**None of D-1/D-2/D-3 is gated on a residual** (rule 1 `[R-STRUCT]`). They describe what the
re-derivation does to the input. They may narrow or kill the arm's scope; they cannot promote it.

## 4. THE SOLVE

**Six shards, one per year, 2020–2025**, pinned to the SHA that carries the re-derived surface.
2020–2022 take the `pjm_d4_4_TP` recipe, 2023–2025 the `pjm_d4_4_A` carve-out. Each pushes its
full bundle including `dispatch/<year>_P1.parquet` (rule 34 (a)).

**G-CTRL is form 4 and no control is solved** (rule 29 clause (b), which survives): the control is
`docs/RESULT-pjm-h9b-sixyear-resolve-2026-09-16.md`'s six bundles — the **same recipe, same HEAD,
same pinned SHA**, retrievable by full SHA. That is a tighter control than the committed keeper,
and it cost nothing extra because it is already solved.

**Expected effect: REPORTED, GATING NOTHING, and the sign is not predicted.** 2020–2022 gas prices
($2.0 / $3.9 / $6.4 HH) sit far outside the 2023–2025 pooling window, and the ladder is in implied
heat rate so it partially normalises — but offer *conduct* in those years is not the same, which
is the entire point of using own-year data. Whether COAL_BIT's 2020 **+22.84** and CC_REGULAR's
2021 **+17.01** / 2022 **+12.81** move toward or away from actual is **not a criterion** and does
not decide promotion (rules 1/14: a worse fit on an accurate input is a root cause to chase, never
a reason to revert).

## 5. WHAT IS NOT TOUCHED

* The keeper, its recipe, its registration and PJM's `CALIBRATED` headline.
* `gas_mid` (3.40 live) and the standing rule-23 wart — still unchartered.
* The registered `committed` multiplier 0.548, the `offer_curve_by_group` bands, and every
  `pjm_offer_midcurve_*` scope field — unchanged. **This adds data, not a knob.**
* pjm-h7's and pjm-h8's open promotions; the pjm-h9b six-year bundles (gitignored, recovery SHAs
  in `.gitignore`). Nothing deleted (rule 31 `[R-RETAIN]`).
* `data/raw/pjm-energy-offers/` stays **uncommitted** (PJM DataMiner2 redistribution restriction).
  Only the derived multiplier JSON is committed, which is the existing convention.

## 6. RULES

Rule 1 `[R-STRUCT]` (§3/§4 — no criterion reads a residual and nothing is selected by one) ·
rule 13 `[R-MEASURED]` · rule 14 `[R-ACCURATE]` (§2 — the basis; a pooled average replaced by the
publisher's own years) · rule 16 `[R-ALLYEARS]` / rule 34 `[R-SHARD-PROMOTABLE]` (c) (every
registered year solved, one shard each, full bundles) · rule 21 `[R-DOF]` (zero free parameters) ·
rule 23 `[R-FROZEN-DERIVE]` (§2 — re-derived on a SOURCE-DATA change, cited in the commit) ·
rule 24 `[R-REGISTRY]` (no new field) · rule 25 `[R-ISO-SCOPE]` (PJM's own offers and fleet) ·
rule 28 `[R-MECH-MATRIX]` (b) (the PJM shard cell is stamped in this session) · rule 29
`[R-SCREEN]` (screen regime removed this session; clause (b) form 4 used, no control solved) ·
rule 30(c) (held-out years never touch the determination) · rule 31 `[R-RETAIN]` (nothing deleted;
the promotion question goes to the owner) · rule 32 `[R-SHARD]` (a) (the parent runs no LP).
