# PREREG — nyiso-205: is `cheapest_first` the right operator for the Capital_Hudson `ST_GAS` `tmax 31.1` limb?

**Session:** nyiso-205, NYISO backcast calibration. **Branch:**
`claude/nyiso-capital-hudson-operator-chqu85`, off `main` `bdfb3095`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — unchanged by this
session unless an arm is earned, screened and promoted, none of which is presumed here.

Written **before** any measurement is read. Numbers land in the FINDING, not here.

---

## 1. The statements the charter requires this PREREG to carry

- **THERE ARE NO RUBRIC FAILURES TO FIX, AND THIS IS NOT A CALIBRATION-TUNING SESSION.** NYISO
  reads **fails 0** on the keeper (grade 7/8); **C3c is the lone ledgered caveat**, is
  non-downgrading under rubric v3.3 / v3.6, and **is not an objective of this session**. No
  criterion is being hunted. Rule 1 `[R-STRUCT]` forbids selecting a mechanism because a residual
  moved, and nothing here is selected that way: the object is chosen because a **measurement that
  has never been taken on this limb** (nyiso-203 §5, taken on the NYC limb) determines whether the
  limb's distribution operator is the one its own market's conduct supports.
- **THE OFFER-CURVE CHANNEL IS OWNER COURT AND IS NOT TAKEN.** The `offer_curve_by_group` band
  multipliers (`committed` / `econ_low` / `econ_high` / `peak`) are the authorized price-tuning
  channel under rule 1's 2026-09-05 carve-out, and its condition (c) — set ex ante by the owner,
  never swept against the gates — means a lane may not take it. This session does not touch it.
- **MARKERS ARE NOT MINE.** `complete` is WITHDRAWN (Q5, nyiso-192) and `frontier` is withdrawn on
  the determination limb; re-entry to either is an explicit **owner** act. Neither is edited,
  prepared, or treated as earned. Card **C-19 / Q51 stays PARKED**. Rule 22 `[R-HOLDOUT]`:
  **2023–2025 is the entire world of this session** — no out-of-training year is solved, scored or
  registered.
- **The decision card `DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` §5/§5.1 stays UNRULED.**
  This session does not rule it and does not rely on a ruling of it.
- **DO-NOT-REDO is respected.** The Capital_Hudson membership arm is refused in **both** forms
  (2480+8006, nyiso-204; 2480 alone, nyiso-204b) and is not re-tested. Astoria 8906 membership
  (closed negative ×4), the whole-year lay-up census as a membership test for a seasonal limb, the
  duct-tranche lever, `nyiso_ct_peaker_bands_measured` and `cc_duct_peaking_row_scoped` are all
  untouched. No matrix cell marked `R`/`I`/`G` is re-tested.

## 2. The object

The live **Capital_Hudson `ST_GAS` `tmax 31.1` step limb** (`floor_pct = 0.0973 =
commit_frac 0.8105 × min_stable_pct 0.12`, `min_event_hours = 48`, `exclude_plant_codes` empty)
carries an **empty `distribution` column** in
`data/raw/reference/reliability_floor_coeffs_NYISO.csv`, so it falls through to the
`ReliabilityFloorSpec` dataclass default **`cheapest_first`**.

The question is whether `cheapest_first` is the operator this limb's own market conduct supports —
the mirror of the question nyiso-203 §5 asked and answered for the **NYC persistent-base** limb
(there: `pro_rata` **supported**, `cheapest_first` **REFUTED**, g/a ratios 1.22 / 1.25 / 0.57).
**That measurement has never been taken on Capital_Hudson.**

**Why the operator and not the membership.** nyiso-204b §3 named the instrument the evidence
actually points at: 2480's D-4 conviction is that its meter reads zero in **100 %** of the
153 h / 23 h **the cheapest-first fill reaches it** — a fact about which hours a *zonal* target
selects at the **bottom** of the stack, not about who belongs in the class. The candidate objects
are therefore the **fill order** or the **target level**, and this session takes the fill order.

**What the two operators do, stated before measuring** (`model/interchange/core.py`
`_distribute_group_floor` vs the `pro_rata` branch of `_apply_frac`): both size the same hourly
quantity, `frac × Σ available capacity` over the selected rows, so **the delivered aggregate MW is
identical** and the operators differ **only in which units carry it**. `cheapest_first` sorts rows
by heat rate and fills each to its available cap until the target is exhausted; `pro_rata` floors
every row at `frac ×` its own available capacity, so a plant's share equals its **available-capacity
share** exactly. This is why the operator is a strictly cleaner object than the membership edit
nyiso-204 refused: the membership edit shrank the target base by ~60 % (a level change by the back
door, rules 21 / 23), while an operator swap **moves no MW in aggregate**.

## 3. DOF status — stated honestly, before measuring

**This is NOT zero-DOF in the way the membership edit was claimed to be, and I am not claiming it
is.**

- **What it does not add.** No new `ScenarioConfig` field, no new coefficient, no re-derivation.
  `floor_pct = 0.0973` is untouched and un-re-derived (rule 23 `[R-FROZEN-DERIVE]`: no source data
  has updated, and none is consulted for a level).
- **What it *is*.** A change to the limb's `distribution` column — i.e. **a mechanism change on a
  live keeper limb**, and a *selection between two operators the engine already offers*. Under
  rule 21 `[R-DOF]` that selection is **one binary free parameter** whose identification source
  must be the measured conduct itself, not a residual. If an arm is proposed it carries that entry
  in the DOF ledger, identified as *"operator selected on measured hot-day generation-vs-available
  share, Capital_Hudson ST_GAS, 2023–2025 CAMPD"* — never *"price residual"*, never *"gates"*.
- **Where the DOF cost is lowest, and it is worth saying plainly:** the coefficient's own
  identification is a **class-aggregate** statistic (`commit_frac 0.8105 × min_stable_pct 0.12`,
  n = 65 observations of the whole class), which is the basis `pro_rata` applies per unit and
  `cheapest_first` applies to a zonal aggregate. Both readings use the same frozen number.

## 4. Phase 0 — the measurement, pre-registered (rule 29 `[R-SCREEN]` step 0, ZERO LP)

Taken on the limb's **own** binding window, reconstructed from the engine's own code path
(`iso_zone_tmax` → `tmax > 31.1 °C` → `_bridge_flagged_runs(min_event_hours = 48)`), which
`_nyiso204b_ch_exclusion_variants.py` already reproduces at **504 / 432 / 600 h** for 2023 / 2024 /
2025. Availability comes from the keeper bundle's reconstructed `FleetArrays` (`fleet_only`, the
same `reconstruct_bundle_fleet` path every nyiso-19x/20x phase 0 uses); generation comes from
CAMPD unit-level hourly `grossLoad`, summed to plant grain to match the meter.

Per plant (2625 Bowline, 8006 Roseton, 2480 Danskammer) per year, in the limb's binding hours:

1. **gen share** = plant Σ metered `grossLoad` ÷ class Σ.
2. **avail share** = plant Σ (`pmax × availability`) ÷ class Σ — which **is** `pro_rata`'s
   allocation share, exactly.
3. **g/a ratio** = (1) ÷ (2). *nyiso-203 §5's test, verbatim.*
4. **`cheapest_first`'s own allocation share**, computed by running the shipped
   `_distribute_group_floor` kernel on the reconstructed arrays — not by my arithmetic.
5. **Manufactured energy** `Σ max(0, floor − metered)` per plant under **each** operator — the
   do-no-harm statistic, and the same one nyiso-203 §6 used.

**Robustness, pre-registered so it cannot be chosen after the fact:** the g/a ratios are also
reported over `{binding hours} × {flagged-unbridged hours}` and over `{all hours of flagged days}`,
exactly as nyiso-203 spanned quantile × day-type. A conclusion that survives only one cut is
reported as not surviving.

## 5. The decision rule, fixed in advance

- **If the three plants share the hot-day commitment roughly in proportion to available
  capacity** (g/a ratios clustered near 1, no plant near zero) — `pro_rata` is the operator the
  meters support and `cheapest_first` is asserting a concentration the meters deny. That is a
  **positive** phase-0 result and it licenses *proposing* an arm; it does not by itself promote
  one.
- **If the meters instead show the commitment concentrated on the cheapest plant** — roughly what
  `cheapest_first` allocates — then **`cheapest_first` is CONFIRMED**, the D-4 rows on 2480 are
  simply the honest bottom of a correctly-ordered stack, and **that is a CLEAN NEGATIVE and a FULL
  RESULT**: it is reported and the session **stops**. No third option is sought. Rule 20
  `[R-FORCED-BUDGET]` leg (a) then stays open with its cheapest instrument closed, which is a
  finding, not a failure.
- **Phase 0 GATES the solve** (rule 29). No screen year is pre-registered here because no solve is
  yet earned. **If** phase 0 supports an arm, a single screen year is pre-registered in an
  addendum **before** the screen runs, chosen by **the mechanism's own measured footprint** — the
  year in which the operator swap moves the most floor MW between plants — **never** by residual
  size. Only a screen that clears its pre-registered structural gate earns
  `--year 2023 2024 2025` as ONE invocation and ONE bundle. A screen bundle is **never registered**
  and is **DELETED BEFORE MERGE** (rule 29(c)).

## 6. Rule 29(b) — G-DRIFT, and why no control solve is spent

The keeper's **committed bundle is the control** (G-CTRL form 4). Form 4's validity is established
**empirically, not by reading hunks**, exactly as the charter requires: re-running
`scripts/probes/nyiso198_rebuild_checks.py --year 2024` at this HEAD must leave `git diff`
**clean** — i.e. the committed `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically
off the same `reconstruct_bundle_fleet` path every phase-0 number here comes from. The result of
that check is recorded in the FINDING. *(That probe prints its own `"VERDICT": "STOP"` — the
nyiso-198 duct-peaking gate for `cc_duct_peaking_row_scoped`, an already-adjudicated `R` cell. It
is part of the committed record, is not a drift signal, and nothing here re-opens it.)*

## 7. What this session will not do

- Not re-test any membership on this limb (both forms refused; DO-NOT-REDO).
- Not re-derive `floor_pct`, on the reduced base or any other (rule 23, no source-data trigger).
- Not touch `offer_curve_by_group` (owner court, §1).
- Not touch any marker, any other ISO (rule 25 `[R-ISO-SCOPE]`), or any other ISO's matrix shard.
- Not fix the pre-existing HEAD test failures listed in the charter; they are measured and
  reported, and they belong to the capx / FF-readiness / SCN-WS5A-LOAD lanes.

---

## Addendum §A — one pre-registered cut replaced, BEFORE any number was read

§4's third robustness cut was *"all hours of flagged calendar days"*. Writing the probe showed it
is **degenerate**: `iso_zone_tmax` returns a **daily** tmax broadcast hourly, so the raw day gate
is already constant within a calendar day and that cut is **identical to the second cut by
construction** — it would have reported the same numbers twice and looked like corroboration.

It is replaced by **the binding window narrowed to h14–21**, the evening peak hours this very
(zone, class)'s own `CH_ST_ev` ramp family targets (disarmed on the keeper by
`reliability_floor_overrides`). That cut is not degenerate and asks the sharper question: does the
proportionality hold when the system is actually tight, or only across the overnight hours a 48 h
bridge sweeps into the window?

**Timestamp discipline:** the substitution is recorded here, and in `_limb_masks`'s docstring, in
the commit that adds the probe — i.e. **before the clean tree finished rebuilding and before the
probe was ever executed**. No measurement existed when it was made.

**Also recorded before measuring — a provenance census, and it is stated AGAINST the framing this
session started from.** Across all six ISOs' live floor limbs, `cheapest_first` is the *majority*
operator (37 of 50: ERCOT 5/5, MISO 12/12, NEISO 6/6, PJM 14/14 all default), so an empty
`distribution` column is the program-wide norm, **not** an anomaly. What is true, and is the
narrower claim this session makes, is that **NYISO is the outlier in the other direction**: 12 of
its 13 live limbs name `pro_rata` explicitly, and the Capital_Hudson `ST_GAS` `tmax 31.1` step is
the **only** NYISO limb that defaults. On the keeper specifically — where
`reliability_floor_overrides` disarms all five evening ramp families — exactly **three** limbs are
live: the NYC and Long_Island persistent-24 h bases (both `pro_rata`) and this step. Provenance is
context for *how the cell got its value*; it is **not** evidence about which value is right, and
the verdict is read off the meters in §4, not off this census. Rule 25 `[R-ISO-SCOPE]`: the census
is descriptive only and **nothing is proposed, transferred, or concluded for any other ISO**.
