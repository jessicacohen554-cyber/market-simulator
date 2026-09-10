# RESULT — nyiso-223: the hub-daily unpriced-day gap fill, four years

**Session:** nyiso-223 · **ISO:** NYISO · **Date:** 2026-09-10
**Arm:** `nyiso_hub_gap_month_level=true` on the keeper recipe, solved **2022 · 2023 · 2024 · 2025**
**Pre-registration:** `docs/PRECOMMIT-nyiso223-hub-gap-fill-2026-09-10.md`, pushed at
`ce4779ec` **before the first LP**. Correction: `docs/ADDENDUM-nyiso223-basis-correction-2026-09-10.md`.
**Control:** the committed keeper `2026-09-09-nyiso-221-fuelvintage-span` (G-CTRL form 4, all
G-DRIFT hunks INERT). **No control solve was spent.**
**Execution:** rule 32 `[R-SHARD]` — four per-year shards, the parent solved nothing.

---

## 0. The headline, in one line

**The arm is CORRECT, MEASURABLY WELL-BEHAVED, and BUYS ALMOST NOTHING.** It closes ~2.3 % of the
window it targets, changes no criterion verdict in any year, and leaves 2022 failing. Every
falsification test it registered against itself passes. **The promotion call is the owner's.**

---

## 1. Scorecard — every criterion at full magnitude

C3a is stated as the keeper's published value plus the **measured** load-weighted model delta
(the delta is what this run establishes; the absolute carries the keeper's own rounding).

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| model LW mean, keeper → **arm** | 69.920 → **69.822** | 32.3557 → **32.3600** | 38.6332 → **38.7081** | 58.3573 → **58.5074** |
| Δ $/MWh | **−0.098** | **+0.004** | **+0.075** | **+0.150** |
| **C3a** keeper → **arm** | −13.8 % → **−13.9 %** | +4.3 % → **+4.3 %** | +5.3 % → **+5.5 %** | −7.3 % → **−7.1 %** |
| C3a verdict (±10 %) | **FAIL** (unchanged) | PASS | PASS | PASS |
| **C3c** h > $300 (model / actual) | 8–10 / 101 | **2 / 10** | **0 / 13** | **3 / 42** |
| C3c model max $/MWh, keeper → arm | — | 326.4235 → **326.4235** | 217.864 → **217.674** | 323.5304 → **323.5304** |
| **C1** largest class move (basis A) | ≈ +0.05 CC_REGULAR ᵃ | **−0.0128** ST_GAS | **+0.0334** ST_GAS | **−0.0431** CC_CHP |
| C1 total energy move (TWh) | +0.000 | **−0.0017** | **−0.0020** | **−0.0040** |
| **C8** forced share | ST_GAS 0.2264 | ST_GAS 0.1615 | PASS | PASS |
| C8 verdict (cap 0.30 / 0.15) | **PASS** | **PASS** | **PASS** | **PASS** |
| D-4 off-window binding | FAIL (3 rows) | FAIL | — | FAIL (1 row) |
| D-4 in the **keeper** too? | (no control in shard) | **YES, identical** | — | **YES, same row** |

ᵃ inferred through the measured class-taxonomy offset — see §4 and the ADDENDUM.

**C3b (price-shape NRMSE) and the C3a %-errors could not be computed inside the shards**: the
`lmp` clean partition cannot be built in a fresh container (`curate_lmp.py` raises
`KeyError: 'MGHG'` on a CAISO file, a pre-existing defect the shards correctly declined to
repair). The model-side monthly means every shard reports are what a C3b re-score would consume,
and the price deltas are ≤ $0.15/MWh annual, so **no C3b movement of any consequence is possible**
— but that is an inference, and it is labelled as one.

**No criterion changes verdict in any year, in either direction.**

---

## 2. Predictions vs outcome — including the two that missed

| PRECOMMIT prediction | outcome | |
|---|---|---|
| C3a 2023 in **+4.1…+4.4 %** | **+4.3 %** | ✅ |
| C3a 2024 in **+5.2…+5.6 %** | **+5.5 %** | ✅ |
| C3a 2025 in **−7.4…−7.1 %** | **−7.1 %** | ✅ (at the edge) |
| C3c **unchanged at 2 / 0 / 3** | **exactly 2 / 0 / 3** | ✅ |
| 2024's $300 bar is unreachable (model max $226.8) | model max **$217.7**; 0 h | ✅ — the distance check nyiso-222 omitted |
| C1 **\|Δ\| < 0.05 TWh** per class | max **0.0431** (2025 CC_CHP) | ✅ |
| C8 within ±0.5 pp, no cap crossed | no cap crossed | ✅ |
| **This arm does NOT close 2022** | it does not | ✅ |
| **C3a 2022 in −13.6 % to −13.2 %** (a slight improvement) | **−13.9 %** — it got **WORSE** | ❌ **MISSED** |
| Shard brief: "2025's gap fill bites in **June and November**" | it bites in **JANUARY** (max \|Δ\| 7.587 $/MMBtu is a January day) | ❌ **MISSED** (my brief, corrected by the 2025 shard) |

### 2.1 The 2022 miss, stated rather than absorbed

I predicted 2022's C3a would improve by ~+$0.20/MWh. It **fell** $0.098. The sizing was right about
the target window and wrong about the rest of the year: I priced the Dec 22–31 lift and did not
price the mean-preserving offset that pays for it. Measured:

| 2022 window | keeper | arm | actual | move |
|---|---|---|---|---|
| **Dec 22–31** (the archive gap) | 63.87 | **66.68** | 187.19 | **+2.81** — closes **2.3 %** of a $123.32 gap |
| **Dec 1–21** (days with prints) | 71.83 | **69.39** | 72.39 | **−2.44** — away from a window the keeper matched to $0.56 |

**That second row is the arm's real cost and it is intrinsic, not a tuning error.** Mean
preservation is the property that makes the mechanism honest, and it is the same property that
makes it nearly useless here: lifting the unpriced days *must* lower the priced ones, and in 2022
the priced days were already right.

---

## 3. The three falsification tests the PRECOMMIT registered against the arm — ALL PASS

**These are the results that make the mechanism defensible, independent of what it buys.**

1. **Mean preservation in DISPATCH** (falsified if any class moved > 0.10 TWh). Largest move in
   any class in any year: **0.0431 TWh**. Total system energy moves ≤ 0.004 TWh. **PASS.**
   The 2025 shard strengthened the claim beyond what was registered: mean preservation holds
   **month by month**, every month identical to 4 dp, not merely annually.
2. **Confinement** (falsified if hours outside a gap month moved). 2023: 4,610 price-changed hours
   against 4,416 fuel-changed hours — the extra ~194 arrive through commitment/storage coupling,
   which is the LP's own propagation, not a leak. 2025's April, October and **December** have
   **zero** moved fuel hours, and December's price moved **+0.000 / +0.004** — a clean internal
   control. **PASS.**
3. **Direction is NOT selectable** (falsified if every year moved toward its residual). 2022's
   Dec 22–31 price **rises $2.81**; 2023's Dec 22–31 price **falls $1.02** — against the residual,
   in dispatch, exactly as the pre-solve fuel gate said it would (3.919 → 3.683 $/MMBtu).
   **PASS — and this is the strongest single argument that the arm is a construction repair rather
   than a fitted one.**

---

## 4. One shard number was WRONG and the parent corrected it

The 2022 shard reported `CC_REGULAR` worsening **+0.378 TWh**. It compared `class_hourly` (the LP's
dispatch classes) against `gmModel` (the scorer's classes, which carve out an `OTHER_FOSSIL`
bucket). Measured on **two independent committed controls**, that offset is **+0.3175** and
**+0.3292** TWh — reproducing to 0.012 TWh, with totals identical across bases on both. Corrected,
the move is **≈ +0.05 TWh**. Full record: `docs/ADDENDUM-nyiso223-basis-correction-2026-09-10.md`.

Both 2023 and 2025 shards independently reproduced the same two-basis hazard on their own years
(D-2 `class_total_twh` differs from `class_hourly` by −1.87 / +2.04 TWh on CC_REGULAR / ST_GAS in
2023). **Every C1 number in §1 is basis A on both sides.**

---

## 5. Phase 0 — the chartered lever was KILLED before any LP, and that stands as this session's largest result

Full evidence in the PRECOMMIT §0. In brief:

- NYISO's three **statewide** reserve families (`nyca_30min_total` / `nyca_10min_total` /
  `nyca_10min_spin`, $750–$775 RCPF) bind in **0 of 35,040** committed P1 hours across 2022–2025.
  The families that DO bind are the downstate pair whose **published** RCPF is **$25/MW**.
- In the 101 hours the market priced > $300 in 2022, the model's fleet sits at **32.8 %** (ST_GAS),
  **50.2 %** (CT_PEAKER), **1.6 %** (oil) of its own annual maximum. **There is no MW shortage in
  the model in the hours the market was short**, so no ORDC curve, requirement or shortage-pricing
  change can fire there.
- Model and market agree on **14 of 101** tight hours; the median model rank of the market's
  top-101 is **2,010 of 8,760**.

And the defect phase 0 found instead: **on the 504 December-2022 hours that HAVE measured Transco
Z6 NY prints the model is within −$0.55/MWh of actual; on the 240 hours of the archive gap it
misses by −$123.32** — 40 % of the whole annual gap in 2.7 % of the year. The prints are
**unrecoverable** (EIA published no Natural Gas Weekly Update between 2022-12-22 and 2023-01-12;
verified 404 on the archive pages and the index).

---

## 6. Governance

- **Rule 1 `[R-STRUCT]`** — structural mechanism; the authorized offer-curve channel is NOT used.
  `authorized_price_tuning` = **NONE**.
- **Rule 21 `[R-DOF]`** — **ZERO new free parameters**; DOF ledger carried verbatim.
- **Rules 13 / 14** — the basis. Identical construction forward; the repair replaces a fabricated
  level with the month's own measured one.
- **Rule 25 `[R-ISO-SCOPE]`** — NYISO's own daily-hub leg; every other ISO's cell is `.`.
- **Rule 27 `[R-PUSH]`** — in-place anchored edits; `ast` symbol diff shows zero removals; blobs
  verified against the pushed SHA.
- **Rule 28 `[R-MECH-MATRIX]`** — row + a cell in all seven shards, same PR; guard exits 0.
- **Rule 29 `[R-SCREEN]`** — step 0 killed the chartered arm and sized this one; form 4 control.
- **Rule 31 `[R-RETAIN]`** — see §8. **Nothing was deleted.**
- **Rule 32 `[R-SHARD]`** — the parent ran no LP. Four shards; the first three of the original four
  stopped correctly on an empty `data/clean` tree and named the fix; relaunched, all solved
  (6–12 min each, inside budget).

---

## 7. What this session ALSO established, for the next lane

1. **A shard container has NO `data/clean` tree, and `hydrate_data.py` does not build one.** A
   NYISO solve needs exactly two curations: `curate_capacity_deliverability.py --isos NYISO` and
   `curate_nyiso_interface_flows.py`. **Put them in every NYISO shard's setup block.**
2. **`curate_lmp.py` fails the whole `lmp` datatype on a CAISO `KeyError: 'MGHG'`**, so no shard
   can compute an actual-side C3a/C3b. This blocks every ISO's lane and is a `scripts/` repair the
   shards correctly refused to make. **It is the cheapest high-value fix available.**
3. **There is no message channel from a parent CCR session to a running shard**, so a shard's
   bundle cannot be retrieved before its container is reclaimed. Either the shard pushes its slim
   artifacts to a **non-`results/calibration/`** path (so the Class-E parity sweep never sees them),
   or the artifacts are lost. **This is the operational gap to close before the next fan-out.**

---

## 8. DISPOSITION — the promotion question, and it is the OWNER'S

**This lane does not self-promote and does not withhold.**

**For promotion.** It is a genuine rule-14 `[R-ACCURATE]` construction repair with **zero free
parameters**: it stops asserting a fabricated price level for calendar days the measured archive
never priced — a 10–13 day trailing December gap in **six of eight** archived years, i.e. exactly
the year's coldest days. It passes **all three** falsification tests it registered against itself,
including the decisive one: its per-year direction is not selectable, and 2023 moves *against* the
residual in dispatch. It changes **no verdict in any year**, so nothing is at risk on the gates.

**Against promotion.** It buys **almost nothing** — 2.3 % of its own target window — and it makes
2022's C3a **slightly worse** (−13.8 % → −13.9 %), because mean preservation pays for the lifted
gap days out of the priced days the keeper already had right. It does not touch the tail (C3c
identical in every year) and it does not touch the CC_REGULAR over-run.

**THE BUNDLES DO NOT SURVIVE.** All four arm bundles were written to **shard containers**, which
are ephemeral and already reclaimed or about to be. They are gitignored, they were **not deleted**
(rule 31), and there was no channel to retrieve them. **Every number this session will ever cite is
in this document and its PRECOMMIT** — which is what rule 29(c) intends — but **there is no
artifact to register.**

**Cost to promote, stated BEFORE any re-solve is launched (rule 31):** re-solving all four years
with slim artifacts pushed is **≈ 40 minutes of LP across four parallel shards** (measured: 6 min
2024, 12 min 2025, ~12 min 2022), plus the parent's composition, scoring and registration. **I have
not launched it.** Say the word and it runs; say no and the docs are the record.
