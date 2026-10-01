# PRE-REGISTRATION — nyiso-181 (`stgas-floor` lane): the 2023 `ST_GAS` OVER-generation object

**Session:** nyiso-181 (`claude/nyiso-181-stgas-floor`), NYISO backcast-calibration track, 2026-09-03.
**Committed and pushed BEFORE the first measurement of this session.** Nothing below was
written after seeing a decomposition of the object.
**Keeper at entry: `2026-09-02-nyiso-177-vintage-matched`**
(`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target grade 5,
fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**.

---

## 0. DISCLOSURE — everything already read at writing time

Per the nyiso-180/181 discipline, the reads held **before** any gate below was written:

1. **The scorer, re-run on the keeper** (`calibration_verdict.py --run-id 2026-09-02-nyiso-177-vintage-matched`):
   the ONLY failing C1 cell is `FAIL 2023 ST_GAS: +3.86 TWh, share +3.2pp [MODEL MISS]`.
   2025 `ST_GAS` is **SKIPPED** (preliminary EIA-923 vintage, 3/10 prior plants missing).
2. **Class energies.** Keeper `class_hourly` P1 `ST_GAS`: **11.999 / 9.799 / 10.014 TWh**;
   plus the nyiso-180 §5 dual-fuel `oil` undercount **+0.021 / +0.034 / +0.154** ⇒ true class
   **12.020 / 9.833 / 10.168**. Bench `classFull` actual: **8.141 / 9.913 / 13.712 TWh**.
   Deltas **+3.879 / −0.080 / −3.544**. **The measured class MOVES 8.1 → 9.9 → 13.7 while the
   model is flat-to-falling 12.0 → 9.8 → 10.2** — the model has the wrong between-year sign.
3. **The D-2 mechanism attribution** (committed `legitimacy_diagnostics.json`), `ST_GAS`:
   `reliability_floor` **2.3604 / 2.6376 / 2.2908 TWh** (16.9 / 22.4 / 18.4 % of class);
   `nyiso_gas_commitment_bridge` **0.1135 / 0.1622 / 0.1664 TWh** (0.8 / 1.4 / 1.3 %).
   D-2 verdict `pass` (0.1767 of class ≤ the 0.30 merchant cap in 2023).
4. **Every D-4 row for both mechanisms**, including the two 2023 `unit-conduct` FAILs
   (plants 2480, 2500 — 0.0009 + 0.0099 TWh, 0.4 % of the mechanism between them) and the
   per-plant `measured_zero_share` column.
5. **The limb registry** `data/raw/reference/reliability_floor_coeffs_NYISO.csv` in full, and
   the keeper's five `reliability_floor_overrides` disarming the NYC/LI/CH `tmax` **evening
   ramp** families.
6. **`run_d4`'s implementation** (`scripts/legitimacy_diagnostics.py:1055-1230`), including the
   `ct_only` skip, the substituted-row skip, and the fact that the conduct rider scores a
   plant's **own binding hours** on a **median** bar.
7. **The merged parallel lane** (`FINDING-nyiso181-itm-degeneracy`, PR #4654): the ITM
   statistic is retired, and the offer-reconstruction gap is CLOSED to `max|d| = 0` by the two
   omitted terms (RGGI carbon + `apply_gas_offer_margin`). **This session therefore does not
   re-open the reconstruction side quest the brief named — it is already closed** — and uses
   the LP's own installed `mc` throughout.
8. **The unmerged lane** PR #4656 (`claude/nyiso-180-per-generator-dispatch`), whose bundle
   `results/calibration/nyiso180_unitdispatch` commits `hourly/unit_hourly_stgas_<year>.parquet`.
   **That bundle is NOT on `main`.** Its provenance is gated in §2 I1/I2 below and the
   dependency is disclosed in every result.

**NOT read at writing time, and this is the point of the pre-registration:** any split of the
2023 `ST_GAS` dispatch into forced / marginal / economic, any per-hour join of forced energy to
the measured CAMPD series, and any between-year decomposition.

---

## 1. RULE 19 `[R-ONE-MECH]` — every mechanism that floors `ST_GAS` on this keeper

Enumerated **before** anything is proposed, from the limb CSV + the keeper's
`reliability_floor_overrides` + the D-2 rows. The probe re-derives this list mechanically and
**S1 fires if it differs**.

| # | mechanism | limb | driver | window | `floor_pct` | distribution | armed? |
|---|---|---|---|---|---|---|---|
| L1 | `reliability_floor` | NYC × `ST_GAS` × `tmax` @ **−50.0 °C** | *degenerate* — every day is flagged | **none ⇒ all 24 h** | 0.175 | `pro_rata` | **YES** |
| L2 | `reliability_floor` | Long_Island × `ST_GAS` × `tmax` @ **−50.0 °C** | *degenerate* — every day is flagged | **none ⇒ all 24 h** | 0.262 | `pro_rata` | **YES** (excl. plant 2517, nyiso-140) |
| L3 | `reliability_floor` | Capital_Hudson × `ST_GAS` × `tmax` @ 31.1 °C | hot day (zone p95 tmax) | none ⇒ all 24 h of a flagged day, `min_event_hours` 48 | 0.0973 | `cheapest_first` | **YES** |
| L4 | `reliability_floor` | `NYC_ST_ev` ramp (14–21) | tmax ramp 25→38 °C | h14-21 | 0.185→1.0 | `pro_rata` | **no** — keeper override |
| L5 | `reliability_floor` | `LI_ST_ev` ramp (14–21) | tmax ramp 25→37.55 °C | h14-21 | 0.35→0.882 | `pro_rata` | **no** — keeper override |
| L6 | `reliability_floor` | `CH_ST_ev` ramp (14–21) | tmax ramp 25→38 °C | h14-21 | 0.0→0.32 | `pro_rata` | **no** — keeper override |
| L7 | `reliability_floor` | CH / NYC / LI / Upstate_West × `ST_GAS` × `tmin`, Upstate_West × `tmax` | cold / hot | — | — | — | **no** — `enabled=False` in the CSV |
| B1 | `nyiso_gas_commitment_bridge` | `ST_GAS` leg | P0 run pattern + min-run 13 h | P0-detected runs | `min_load_frac` 0.239 | — | **YES** |

**Exactly two armed mechanisms floor `ST_GAS`: `reliability_floor` (L1–L3) and the gas
commitment bridge (B1).** Nothing else in the eleven armed mechanisms puts a lower bound on an
`ST_GAS` column (nyiso-180 §7's inventory, re-confirmed here: the LCR/TSL and seam rows act on
links / import generators, the loss surface on `Flow` columns, `hydro_dispatch_envelope` on
hydro, `ramp_limits` is two-sided and rate-bounding).

**THE RULE-17 `[R-FLOOR-WINDOW]` POSITION OF L1 AND L2, STATED BEFORE MEASURING.**
Both declare (a) a driver — the CAMPD *when-available cool-day CF p25*, i.e. "these boilers
carry a persistent baseline" — and (b) a window, *all 24 h*, and (c) a forward story, the same
p25 re-derived from a forward CAMPD vintage. **So neither is a "no declared window" failure on
its face.** What is untested is leg (b)'s *evidence*: **a 24-h window makes D-4's `window` check
vacuous by construction** (off-window share is 0 because there is no off-window), which is
precisely why the owner added the per-unit conduct rider (nyiso-140 §5). That rider is a
**median** test on a plant's binding hours; it convicts a plant that is off in *most* binding
hours and acquits one that is off in *many*. **The hours themselves have never been measured.**

---

## 2. INSTRUMENT AND ITS CHECKS (fail ⇒ S1)

The instrument is the LP's **own installed offer and reduced cost**:
`nyiso180_unitdispatch/hourly/unit_hourly_stgas_<year>.parquet`
(`unit_id, plant_code, plant_group, fuel, zone, hour, mw, cap_mw, mc, red_cost`; 93 `ST_GAS` LP
units × 8,760 h), joined to the **keeper's own** `hourly/system_<year>.parquet` zonal `price`.
Floor matrices (`dispatch`, `min_gen`, `mechanism`) come from
`legitimacy_diagnostics.load_or_rebuild_floors` / `build_plant_matrices` — **the gate's own
basis, imported, not re-implemented** — and the measured plant view from that module's
`load_bench` / `bench_plant_view`, so every measured number here is the one D-4 itself scores on
(including its `ct_only` and substituted-row skips).

* **I1 — the unit bundle IS the keeper.** `class_hourly` and `system` in
  `nyiso180_unitdispatch` must equal the keeper's, cell for cell.
  **Bar: 0 of 122,640 class-hour cells and 0 of 52,560 zonal prices differ, all three years.**
  → **S1 IF NOT.** (PR #4656 claims a bit-identical replay; this session verifies it rather than
  inheriting it, because the bundle is not on `main`.)
* **I2 — the slice is the whole class.** Σ `mw` over the slice must equal the keeper's
  `class_hourly` `ST_GAS` **plus** the dual-fuel `oil` re-attribution.
  **Bar: |Δ| ≤ 0.001 TWh/yr.** → **S1 IF NOT.**
* **I3 — `red_cost` sign is a valid in/out-of-the-money test for this class.**
  Ω ≡ `red_cost` − (`mc` − `price[zone]`) is the net rent all non-energy rows charge.
  **Bar: p95 |Ω| ≤ \$0.01/MWh over `ST_GAS` unit-hours.** → **S1 IF NOT.**
  (nyiso-181 measured p95 Ω = 3e-06; this is a re-verification on the same artifact, and it is
  what licenses reading `mc > price` as "out of the money" without per-row duals.)

**The partition, fixed here.** Every `ST_GAS` unit-hour with `mw > 0` is assigned exactly once:

* **A — OUT OF THE MONEY (forced):** `mc > price[zone] + $0.01`.
* **B — MARGINAL:** `|mc − price[zone]| ≤ $0.01`.
* **C — IN THE MONEY (economic):** `mc < price[zone] − $0.01`.

A is split by `mechanism` (L1/L2/L3 vs B1 vs unattributed) on the D-2 matrices.

---

## 3. THE TWO HYPOTHESES, THEIR PREDICTIONS AND THEIR FALSIFIERS

Both are pre-declared, **graded at full magnitude**, and **not mutually exclusive** — the
deliverable is the split, not a winner.

### H1 — the floor binds in hours its own driver evidence does not justify (rule 17)

**P1a — RULE-17 VIOLATION.** Let `Z2023` = the reliability_floor's 2023 `ST_GAS` forced MWh
landing in hours where **that same plant's own same-year CAMPD meter reads exactly 0 MW**
(the D-4 measured series, `ct_only` plants excluded exactly as the rider excludes them).
**Prediction: `Z2023` / 2.3604 TWh ≥ 0.05** — the D-4 gate's own `d4_max_offwindow_share`, the
bar the owner already set for "floored energy outside its justified window", applied per hour
instead of per hour-of-day.
→ **FALSIFIED IF < 0.05.**

**P1b — MATERIAL CARRIER.** **Prediction: `Z2023` ≥ 0.97 TWh** (25 % of the +3.879 TWh miss).
→ **FALSIFIED IF < 0.97 TWh.** P1a and P1b are graded separately: a limb can violate rule 17
and still not carry the miss, and that outcome is reported as such rather than upgraded.

**P1c — SIGNATURE.** The convicted energy concentrates in a **small number of plants**:
the top-2 plants by `Z` hold ≥ 0.60 of `Z2023`.
→ **FALSIFIED IF < 0.60** (which would say the defect is the limb's *level*, not its
*membership* — a different and harder repair, and it would rule out the nyiso-140 repair form).

### H2 — the 2023 offer level is too cheap, so steam clears economically it should not

**P2a — UNFORCED EXCESS.** Let `U2023` = (model class 12.020 TWh − A2023) − measured 8.141 TWh:
the excess that survives deleting **every** forced MWh. **Prediction: `U2023` ≥ 0.97 TWh**
(25 % of the miss) ⇒ H2 CARRIES.
→ **FALSIFIED IF < 0.97 TWh** — i.e. the floors alone over-explain the miss and the economic
dispatch is not in excess.

**P2b — NO FLOOR INVOLVEMENT.** H2's own signature is `red_cost ≈ 0` (marginal) or `< 0` (at an
upper bound) with the unit **not** at a positive lower bound. **Prediction: the B+C share of
2023 `ST_GAS` dispatch exceeds its 2024 share by ≥ 5 pp** — the model clearing steam
economically in 2023 that it does not clear in 2024, which is the between-year sign the object
actually needs (disclosure §0.2).
→ **FALSIFIED IF < 5 pp.**

### P3 — the between-year falsifier, which binds on BOTH hypotheses

The floor is nearly flat (2.3604 / 2.6376 / 2.2908) while the miss swings +3.879 / −0.080.
**Prediction: Δ(A, 2023−2024) accounts for < 25 % of Δ(miss, 2023−2024) = +3.959 TWh.**
→ **FALSIFIED IF ≥ 25 %**, which would mean the forced term does carry the swing after all and
H1 is a bigger object than the flatness of the D-2 annual totals suggests.

---

## 4. STOP CONDITIONS AND WHAT A REPAIR MAY BE

* **S1 — instrument.** Any of I1/I2/I3 fails ⇒ **every H1/H2 verdict word is WITHHELD**, the
  numbers are reported as measured only, and no repair is proposed.
* **S2 — no carrier.** If **both** P1b and P2a fail, **no lever is opened.** The object is handed
  forward with its measured split and the session ships the measurement.
* **S3 — the repair form, fixed in advance.** If H1 convicts, the ONLY repair this session may
  attempt is the **nyiso-140 membership form**: an `exclude_plant_codes` entry on the convicted
  persistent-base limb, sourced from the **same pooled CAMPD conduct the limb's own `floor_pct`
  is derived from**, with `floor_pct` **UNCHANGED** and verified basis-matched (the excluded
  plant's removal must move the basis-matched p25 by less than the coefficient's own rounding,
  exactly as nyiso-140 verified 0.2666 vs the frozen 0.2620). **Zero free parameters
  (rule 21 `[R-DOF]`), zero magic numbers (rule 5), nothing re-derived against a residual
  (rule 23).**
* **S4 — what is forbidden, whatever the measurement says.** No level tuned to the residual; no
  year-specific parameter; no measured-outcome pin (rule 13 `[R-MEASURED]` — a same-year hourly
  availability gate on the floor would have no forward analogue and is **not** admissible even
  though it would close the gate); no new `ScenarioConfig` field; no under-generation lever; no
  re-opening of any DO-NOT-REDO cell (the loss surface, the post-solve transform, the
  capacity/label-basis mismatch, `ramp_envelopes`-as-dominant-carrier, the retired ITM
  statistic).
* **S5 — promotion discipline.** Any repair is solved **2023 + 2024 + 2025 in one invocation,
  years sequential** (rules 16 `[R-ALLYEARS]`, 12 `[R-PARALLEL]`), scored **leave-one-year-out**
  before any promotion is proposed, and **registered on the backcast dashboard in this session
  whatever its verdict** (rule 15 `[R-DASHBOARD]`) — keeper, candidate or rejected probe.
* **S6 — holdout.** Every year touched is 2023 / 2024 / 2025. NYISO holds neither `complete` nor
  `final`; **no marker is requested**; the locked-test freeze is untouched (rule 22).

## 5. Expected value, stated before the result

The most likely outcome on the disclosure already in hand is **P1a PASSES and P1b FAILS**: the
per-plant `measured_zero_share` column already visible in the committed D-4 rows implies a
`Z2023` of order 0.3–0.4 TWh — a genuine rule-17 violation, and roughly a tenth of the miss.
**That is a partial result and will be reported as one**, not inflated into an explanation of
the gate. If that is what lands, S2 does not fire only if P2a carries, and the honest headline
is a split, with the between-year sign (§0.2) named as the object the lane still owes.
