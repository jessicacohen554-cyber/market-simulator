# FINDING (miso-109): MISO's hydro LEVEL now comes from EIA-923 `HY` — the
# PS-inclusive `NG: WAT` pin is refused, and `hydro_budget_nameplate_aware` is
# then PROVABLY INERT at MISO

**Session:** miso-109 (lever queue §5.4 item 6 — the miso-108 prescription)
**Date:** 2026-07-30
**Verdict:** LEVEL FIX **landed** (rule 14 `[R-ACCURATE]`);
`hydro_budget_nameplate_aware` at MISO **`U` → `I`**, adjudicated with **no
solve**. **Rule 25:** every parameter derived from MISO's own data; no
CAISO/PJM verdict transferred.
**Runs:** `miso109_control_A` (keeper recipe at HEAD, contaminated level) and
`miso109_hy_level_B` (same HEAD, corrected level) — a single-delta A/B, both
registered (rule 15).

---

## 1. The defect, re-measured on MISO's own data

miso-108 established it; this session re-derived every number from the raw
sources before touching code
(`scripts/probes/_miso109_hydro_level_audit.py`, §1–§3).

The LP's hydro units are EIA-923 prime mover `HY` — conventional inflow hydro
alone; `data/hydro.py` excludes `PS` because pumped storage is a storage
resource, not inflow. The MISO keeper pinned those units' **monthly energy
level** to EIA-930 `NG: WAT`. MISO files **no `NG: PS` column**, so its
`NG: WAT` is a conventional-hydro **plus pumped-storage-discharge** series.

Three signatures, each independently checkable:

| signature | measurement |
|---|---|
| (a) no `NG: PS` column | MISO's extract carries `COL, NG, NUC, WAT, SUN, WND, BAT, OTH` — PS has nowhere to go |
| (b) breaches its own nameplate | `NG: WAT` peaks **3,535 / 3,964 MW** (2023 / 2024) against **2,478.4 MW** of conventional `HY` nameplate — **580 / 826 h/yr** above it — beside a **2,416.8 MW** PS fleet (Ludington 1,978.8, Taum Sauk 408, Degray 30) |
| (c) never negative | **zero** negative-`WAT` hours in any year 2018–2025, so pumping is not netted and the contamination is one-way gross discharge. EIA-923 `PS` net generation is **negative** every year (−0.840 / −1.033 TWh — the round-trip loss), the opposite sign |

The gap against what the units actually are:

| year | 930 `NG: WAT` (pinned level) | 923 `HY` (the units) | gap |
|------|--------------:|---------:|----:|
| 2023 | 9.979 TWh | 8.789 TWh (165 plants) | **+1.190 TWh / +13.5 %** |
| 2024 | 10.710 TWh | 9.042 TWh (165 plants) | **+1.669 TWh / +18.5 %** |
| 2025 | 9.872 TWh | *early release, 14 plants — **not differenced*** | — |

The control run's own solve log states the defect outright:
`MISO 2023 hydro budget pinned to monthly target total 9979.0 GWh (was 8789.4
GWh)`.

**Two small restatements of miso-108's figures, both deliberate.** (i) 2024's
gap is **+1.669 TWh / +18.5 %**, not +1.701 / +18.8 %: miso-108 summed the raw
extract (8,784 h, 10.742 TWh) while the model's own loader drops Feb 29 and
sums 8,760 (10.710 TWh). The loader figure is the one that gets pinned, so it
is the one quoted. (ii) The nameplate-breach hour counts are 580 / 826, one
hour off miso-108's 580 / 827, for the same leap-day reason.

**The 2025 trap, honoured.** MISO's 2025 EIA-923 filing is an early release
carrying **14 `HY` plants against 165**. The naive 2025 gap reads +8.902 TWh /
+918 % — that measures **source coverage**, not the defect, and overstates it
~5×. Every year-over-year difference in this session is gated on plant coverage
first (probe §3 prints the census and refuses to difference a partial filing).

## 2. What the fix is — and what it deliberately is NOT

**The fix.** A BA listed in the new
`constants.EIA930_PS_FOLDED_INTO_WAT` registry has its `NG: WAT` level pin
**refused** (and logged); its monthly hydro level stays on **EIA-923 `HY`** —
the same series, and the same plant population, the per-plant budget is already
built from. Level and units become one population. Zero free parameters: this
*removes* a mechanism rather than adding one, so the DOF ledger improves.
Forward-reproducible (rule 13 `[R-MEASURED]`): 923 `HY` regenerates every year
and responds to hydrology — it is the same admissibility class the per-plant
budget already relies on.

**What was refused, and why — the alternative is killed on measurement, not
preference.** miso-108 offered a second option: keep `NG: WAT` for the monthly
*shape* and rescale it to the 923 `HY` level, documented under rule 14's
boundary-misalignment clause. That requires a reconciliation constant, and this
session measured whether one is identifiable (probe §4). **It is not:**

* MISO's conventional share of `NG: WAT` **drifts 0.9937 → 0.8442** across
  2019–2024 (spread **0.15**) — a factor fitted on any pair of years is wrong
  by ~15 % on another.
* The **monthly** gap changes sign by month in **4 of the 5** complete-filing
  years (2019: 2 sign changes, 2020: 6, 2021: 4, 2023: 4, 2024: 0), so the
  discrepancy is not a single scalable contaminant at all — it is PS discharge
  (positive, Jun–Sep, +197 to +356 GWh in July/August of **every** year) net of
  an opposing boundary difference in the other months.

A fitted constant would therefore be a free parameter with no forward story,
barred by rules 5 `[R-NO-MAGIC]` / 13 / 22 `[R-DOF]`. **No offset, haircut or
scale factor was tuned against any price or dispatch residual** (rules 13 / 23).

**The cost, stated plainly.** Dropping the pin also drops the measured *monthly
shape* of the 2025 water year, which for 2025 now comes from the 2024 backfill
(146 of 160 plants, 8.108 of 9.077 TWh). That is a real loss of year-specific
information, and it is accepted because the shape being discarded is itself
PS-distorted (summer-inflated by exactly the Jul/Aug signature above). The
matched-plant panel gives an independent read on how much was lost: the 14
plants reporting in **both** 2024 and 2025 generated **+3.8 %** more in 2025
(0.9344 → 0.9697 TWh), i.e. 2025 was slightly **wetter**, while the
contaminated `NG: WAT` said 2025 was **7.8 % drier** than 2024. The two
disagree in *sign*, which is further evidence the 930 series' year-over-year
movement at MISO is dominated by PS cycling, not hydrology.

## 3. Rule 19 `[R-ONE-MECH]` — what else acts on this phenomenon

Enumerated before changing anything. The keeper carries
`hydro_dispatch_envelope=False`, `hydro_min_flow_floor=False`,
`hydro_ror_split=False`, `hydro_budget_nameplate_aware=False`. The monthly
level pin is therefore the **only** mechanism acting on MISO hydro energy
placement: nothing is stacked, and the fix **replaces** the level in place
rather than layering on its residual.

**Standing hazard, recorded not actioned.** The dispatch *envelope*
(`HYDRO_ENVELOPE_PERCENTILE`) and the *min-flow floor*
(`HYDRO_MIN_FLOW_PERCENTILE`) are also built from hourly `NG: WAT` and inherit
the same contamination. Both are default-off and off in MISO's keeper, so
nothing is wrong today — but arming either at a listed ISO needs its own source
fix first, and EIA-923 is monthly so it offers no hourly substitute. Flagged in
the constant's citation and in the matrix.

## 4. E1 sign statement — declared BEFORE the solve

The fix removes **1.19 / 1.67 / 0.79 TWh** of zero-marginal-cost hydro from the
LP (2023 / 2024 / 2025). That energy must be re-served by the marginal unit, so
**fossil volume and mean LMP must rise**. Against the keeper's scored position
— under-priced in every year (**−1.4 % / −6.7 % / −14.3 %**, 2025 a ledgered
caveat), a far-too-thin tail (**1 h vs 30 h**, 6 h vs 37 h, 0 h vs 88 h above
$200), and under-producing **7 of 8** fossil classes in 2023 (net −14.4 TWh)
— the fix was predicted to move **C1 and C3a in the helpful direction**, and
C3c weakly the same way.

**This prediction is a hazard, not a justification.** A correction that happens
to help is the easiest kind to accept for the wrong reason. Rule 14 mandates
the accurate input *whichever way the residual moves*; the sign was written
down first precisely so a favourable result could not be read as the reason.
Magnitude was also predicted small: ~0.5 % of MISO's ~250 TWh energy, nowhere
near enough to close a −14.3 % price miss.

## 5. The A/B

*(filled from the two registered runs — see §5 table below.)*

## 6. Step 2 — `hydro_budget_nameplate_aware` is INERT on the corrected level

The mechanism only changes **how a level *target* is distributed** across
plant-months: `load_hydro_budget` documents and implements
`nameplate_aware_target` as *ignored when `monthly_target_mwh` is `None`*. With
the level corrected there **is** no target, so there is nothing to re-allocate.

Measured, not merely argued (probe §6) — budgets built both ways, all three
years:

| year | corrected level (923 `HY`) | with the pinned level (930 `NG: WAT`) |
|------|---|---|
| 2023 | 8.7894 TWh — **identical**, L1 **0.000 GWh** | 9.9790 TWh — differs, L1 **259.3 GWh** |
| 2024 | 9.0420 TWh — **identical**, L1 **0.000 GWh** | 10.7103 TWh — differs, L1 **454.2 GWh** |
| 2025 | 9.0772 TWh — **identical**, L1 **0.000 GWh** | 9.8718 TWh — differs, L1 **171.3 GWh** |

So the MISO cell is **`I`**, and no solve was spent on it — the correct
sequencing under rules 1 / 14 / 19, which is exactly why miso-108 refused to
arm it first.

The right-hand column is the more interesting half: **the mechanism's entire
apparent signal at MISO was the defect**. What the nameplate-aware allocator
was "fixing" on the pinned level was plant-months pushed above their own
`nameplate × hours` ceiling — by the pumped-storage energy that did not belong
in the level at all. Fix the level and the symptom disappears with it. (Rule
25: this says nothing about CAISO's or PJM's `K` verdicts, which rest on their
own levels.)

## 7. Cross-ISO screen — all six ISOs, the standing audit item CLOSED

The three-signature check is mechanical and portable, so it was run everywhere
(probe §1–§3). **Rule 25: each row is evidence for that ISO's own lane, never a
transferred verdict.**

| ISO | `NG: PS` col | h/yr above conv. nameplate | neg. `WAT` h | 930 vs 923 `HY` | verdict |
|------|---|---|---|---|---|
| ERCOT | no | 0 | 0 | — | clean (no PS fleet; 567 MW of hydro total) |
| CAISO | no | **0 every year** | 1–121 | — | clean — the negative hours show pumping **is** netted |
| PJM | no | **1,249–1,612** | 0 | **+52.9 % … +79.6 %** | **DEFECT, the largest** |
| MISO | no | 332–826 | 0 | +13.5 % / +18.5 % | **DEFECT — fixed here** |
| NYISO | no | 0–33 (≤0.007 TWh) | 0 | **−4.0 % … −6.1 %** | clean — the bias runs the **opposite** way |
| NEISO | **yes**, from Nov 2024 | 63–276, **0 in 2025** | 0–1 | +2.7 % … +10.1 % | **TIME SPLIT**, not a standing fold |

Neither PJM nor NEISO is switched on in the registry here, on purpose:

* **PJM** is a live defect on a live keeper (+6.5–7.0 TWh/yr, ~60–80 % of its
  923 budget). Adding `"PJM"` to the registry is a one-line change, but it
  moves PJM's keeper and therefore owes PJM's own A/B, re-gate and registration
  — its lane, not this one.
* **NEISO** needs a *per-window* treatment rather than a switch, because its own
  filing changes mid-series: PS is folded into `WAT` through Oct 2024 and split
  out from Nov 2024 (2025 shows zero breach hours and a 1,359 MW max against
  1,926 MW of nameplate). A flat refusal would discard good post-split data.
* **NYISO** needs nothing: it shows none of the three signatures, and its 923
  `HY` *exceeds* `NG: WAT` by 4–6 % every year — an under-count, a different
  question with the opposite sign.

## 8. Governance

* **Rule 12 `[R-PARALLEL]`** — years solved **sequentially**, one fresh year per
  process, chained with `--reuse-solved` (`scripts/probes/_miso109_chain.sh`);
  peak RSS ~12 GB against a 15 GB box, ~13.3 min/year.
* **Rule 16 `[R-ALLYEARS]`** — both arms cover **2023, 2024, 2025**, one bundle
  each.
* **Rule 22 `[R-HOLDOUT]`** — only 2023–2025 solved or scored. MISO carries no
  calibration-complete marker; no holdout year was touched.
* **Rule 15 `[R-DASHBOARD]`** — both arms registered in-session.
* **Rule 26 duty (b)/(c)** — `hydro_budget_nameplate_aware`'s MISO cell updated
  to `I` in the same session, and the level fix carries its own matrix row.
* **Same-HEAD control, not the committed keeper.** `git diff` from the keeper's
  registration commit to HEAD touches **21 files under `src/market_sim/`**, so a
  bit-equality control against the committed bundle was never pre-registered
  (the miso-106 G3 lesson). The A/B is control-at-HEAD vs candidate-at-HEAD,
  single delta.
* **Infrastructure fix shipped alongside** — `--reuse-solved` did not carry the
  `hourly/` sidecars forward, so a rule-12 per-year chain produced bundles with
  class-hour holes in exactly the years it reused. Fixed with tests
  (`_copy_reused_year`), and verified end-to-end on both arms of this session.
