# PRECOMMIT — xiso: does the LP climb its own stack? (the C3c common-cause attribution)

**Lane:** CROSS-ISO — C3c (price tail / scarcity) common-cause attribution
**Date:** 2026-09-22 · **Session:** `lp-stack-climb-attribution`
**Cost:** ZERO LP. 41 `fleet_only` rebuilds (~15 s each) + committed sidecars. No shard launched.
**Rules:** 32 `[R-SHARD]` (a) (the parent never solves), 29 `[R-SCREEN]` clause 0 (zero-LP phase 0),
1 `[R-STRUCT]` (attribution, not tuning — nothing armed, nothing swept, no keeper moves),
28 `[R-MECH-MATRIX]` (a) DO-NOT-REDO, 25 `[R-ISO-SCOPE]` (a measurement in one ISO fills no cell
in another).

> **Everything in §2–§4 is declared BEFORE any number is computed.** The threshold in §4 is fixed
> here and is not moved after measuring. This file is pushed before the probe is run.

---

## 1. The object

`price_tail` (**C3c**) is the single most widespread blemish in the program — a ledgered caveat
under rule 22 `[R-C3C]` in five ISOs, a FAIL in a sixth — and in three years of calibration
**nobody has attributed it**. Rule 22 calls it an "accepted model-class limitation"; that phrase
has never been backed by a measurement showing the limitation is in fact *model-class*.

Two lanes measured the same thing on 2026-09-21, independently, in different ISOs, and both times
as the reason an offer-curve lever was **refused at zero LP**:

- **PJM** (`docs/FINDING-pjm-h15-the-top-of-the-stack-is-not-the-defect-2026-09-21.md` §4) — in the
  market's top-1 % hours the keeper carries 27 393 / 20 196 / 16 416 MW of availability-aware idle
  thermal (26 / 20 / 15 %, 2023/24/25) while clearing $39.2 / $54.9 / $112.6 against $123.1 /
  $169.8 / $317.6. CC_REGULAR is 93.6–95.6 % loaded and coal 82.5–98.5 %, but CT_PEAKER runs at
  36.5 / 52.4 / 65.8 %. CC_REGULAR's `peak` band dispatches **0.000 MW in all 26 280 hours**.
- **SPP** (`docs/handoffs/RESULT-spp-70-thermal-stack-extent-2026-09-21.md` §0/§4) — "12–20 % of
  thermal capacity sits ABOVE the clearing price even in the top-10 load hours. The LP never
  reaches the top of the stack it already has." 2020: price tops at $36.21 against a most-expensive
  available row offering $68.36, 5.51 GW idle above the clearing price.

**The hypothesis under test:** the tail is not missing because the stack lacks height; it is missing
because **the clearing point never climbs**. If that holds across the fleet of ISOs it is a
model-class property and C3c has a named cause for the first time. If it does not, C3c is per-ISO
and each lane owns its own.

---

## 2. Population — declared in full

Each ISO's designated keeper (`frontend/data/backcast/keepers/<ISO>.json`) plus every run stamped
to it (rule 30 `[R-TOUCHPOINT-FOLD]` (a)). **41 ISO-years, 9 ISOs**, read from committed artifacts
only. No LIVE lane's branch is touched.

| ISO | keeper | bundle(s) | years |
|---|---|---|---|
| CAISO | `2026-09-20-caiso-290-leftedge` | `xiso8_leftedge_span` | 2022–2025 (4) |
| ERCOT | `2026-09-19-ercot266-mer-five-year` | `ercot_mer20260919_five_year` | 2021–2025 (5) |
| MISO | `2026-09-20-miso-264-anchor-vintage` | `miso264_anchor_span` | 2020–2025 (6) |
| NEISO | `2026-09-19-neiso112-mer-year-isolated` | `neiso112_mer_span` | 2020–2025 (6) |
| NWPP | `2026-09-20-nwpp-44-measured-take` | `nwpp44_takeorpay_reg` | 2023–2025 (3) |
| NYISO | `2026-09-20-nyiso247-fuel-invariance-disarm` | `nyiso247_fuelinv_span` | 2022–2025 (4) |
| PJM | `2026-09-20-pjm-h15-coalwindow-span` | `…_span` + folded `…_touchpoint` | 2020–2025 (6) |
| SOCO | `2026-09-20-soco57-measured-cc-heat` | `soco57_measured_cc_hr` | 2023–2025 (3) |
| SPP | `2026-09-20-spp-67-yearown-rate` | `spp67_yearown_span` + folded `…_rung` | 2019–2025 (7) |

**The PJM keeper moved under the brief.** The task cites `pjm-h17` and the h14 keeper; the file on
disk is `FINDING-pjm-h15-…` and PJM's designated keeper is now `…-pjm-h15-coalwindow-span`. This
lane measures the **current** keeper, so §1's PJM numbers are re-measured rather than quoted.

### 2.1 SOCO and NWPP carry no price series — declared before measuring, not discovered after

`scripts/calibration_verdict.py:755-765` and `:1200`: **SOCO and NWPP are price-unscored by owner
registration.** Southern Company publishes no LMP, no DA price and no hourly index; NWPP's two
candidate series were both refused. There is no `actual_lmp_hourly_SOCO.parquet` and no
`actual_lmp_hourly_NWPP.parquet`, both runs take the rubric v3.8 **PHYSICALLY-CALIBRATED (PRICE
UNSCORED)** class, and **C3c is never scored in either**.

Two consequences, both declared now:

1. **The C3c population is 7 ISOs, not 9.** The brief's "C3c is a CAVEAT in five of nine and a FAIL
   in MISO" is a statement about 7 scored ISOs (CAISO, ERCOT, MISO, NEISO, NYISO, PJM, SPP).
2. **The top-1 % window is undefined for SOCO and NWPP**, because it is defined on a price series
   they do not have. They are measured on a **load** window instead (§3.2), and that substitution
   is stated at the gate: a load window is a *tightness* window, not a price window, so those two
   ISOs can corroborate the mechanism but **cannot speak to the price tail directly**.

This is why §4 carries a robustness leg over the 7-ISO C3c population, declared here rather than
chosen after the count.

---

## 3. Measurement — every definition fixed here

### 3.1 The fleet side (zero LP)

`scripts/lib/bundle_fleet.reconstruct_bundle_fleet(bundle, year)` — the sanctioned `fleet_only`
rebuild, fidelity-guarded, carrying `replay_keeper.DERIVED_RUN_YEAR_INPUTS`. Never
`derive_pjm_ordc_overlay._run_year_kwargs` (drops 38 flags), never a hand-rolled kwargs subset.

**Availability-aware available capacity:** `av_cap[g,t] = pmax[g] × availability[g,t]`, from the
keeper's own rebuilt `FleetArrays`. **Never a max-over-year proxy** — an "idle" MW is one the LP
could actually have dispatched *in that hour*.

**Offer:** `mc_base[g,t]`, the LP's own base-cost offer array.

### 3.2 The window — top-1 % hours

`n = max(1, round(0.01 × T))` hours (T = 8760/8784 → **88**), taken as the n highest hours of:

- **the ISO's own actual RT series** — `data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet`,
  `rt` column, NaN hours excluded — for the 7 price-scored ISOs; and
- **the model's own total demand** for **SOCO and NWPP only**, per §2.1, declared as a substitution.

### 3.3 Thermal — fixed now, because the choice moves the answer

`fuel_type ∈ {coal, gas_cc, gas_cc_ccs, gas_ct, gas_st, oil}`. Excludes nuclear, hydro, wind, solar,
storage, import, biomass, OTHER. **Oil is IN**, matching the PJM precedent exactly (its 27 393 MW
includes ~4 GW of oil at 0–6 % utilisation); excluding it would lower every ISO's number, so the
choice is pre-registered rather than made against the threshold.

### 3.4 The join — the alphabet trap is removed, not worked around

The brief warns that the fleet's `efficiency_bin` and the sidecar's `klass` are different alphabets,
and that joining them naively inflated PJM's idle block by ~62 GW (83 GW / 59 % instead of
27 GW / 26 %). The PJM probe worked around it by keying on `Generator.fuel_type`.

**This lane removes the trap instead of routing around it**, by keying the fleet side on the
sidecar writer's *own* derivation (`scripts/run_calibration_full.py:410-430`):

```
k = plant_group[g]  if (iso != "ERCOT" and plant_group[g])  else _model_class_for_unit(...)
if k == "COAL": k = _coal_supply_class(plant_code[g])
```

which is **exactly** the `klass_base` the sidecar's `class_band_hourly` writes into its `klass`
column (`:753-758` groups on `klass_base`, then renames it to `klass`). Same function, same inputs
⇒ **exact alphabet**, ISO-agnostic, and it carries ERCOT's `efficiency_bin` path for free. The
`class_band_hourly` sidecar is also the correct one for the *pre*-re-attribution key: `class_hourly`'s
`klass` relabels a dual-fuel unit's oil hours into the pooled `oil` class and would undercount gas.

### 3.5 Dispatched

`hourly/class_band_hourly_<year>.parquet`, `pass == "P1"` (**P1 is the scored pass**), `mw` summed
over the bands of each class in §3.3's selection, averaged over §3.2's hours.

### 3.6 The reported quantities, per ISO-year

1. **Availability-aware idle thermal**, MW and % — `available − dispatched`, total and per class.
2. **Per-class utilisation** — `dispatched / available`.
3. **The highest AVAILABLE offer** — `max(mc_base[g,t])` over rows with `av_cap[g,t] > 0` — against
   the **model clearing price** (demand-weighted mean of `system_<year>.parquet` P1 `price` over
   zones) and the **market price**.
4. **Capacity offered above the clearing price** — `Σ av_cap[g,t]` where `mc_base[g,t] > price[t]`
   (the SPP-70 metric, exact from the fleet side; reported beside (1), which is the PJM metric, as a
   cross-check — the two are computed by different routes and should agree in sign and rough size).
5. **Whole-year dispatch of every `peak*` band**, per class (max and mean MW) — the PJM §3 inertness
   measurement, generalised.

### 3.7 Reconciliation gates — run before ANY number is reported

The brief's trap cost a wrong headline once; these make a repeat detectable rather than silent.

- **G1** — every class label the fleet side produces exists in the sidecar's `klass` vocabulary, or
  carries 0 MW of selected capacity.
- **G2** — every sidecar class the selection does *not* cover is listed with its MW. Nothing is
  silently dropped.
- **G3** — no class's dispatched MW exceeds its available MW by more than 0.5 % of available.

An ISO-year failing G1–G3 is reported **UNRECONCILED**, is excluded from the §4 count, and its
reason is named. It is never quietly repaired.

---

## 4. THE PRE-REGISTERED TWO-WAY VERDICT

**An ISO SHOWS THE SIGNATURE** iff the **median over its scored years** of §3.6(1)'s
*% availability-aware idle thermal in the top-1 % window* is **≥ 10 %**. (Median, so one outlier
year cannot swing an ISO in either direction.)

- **UNIVERSAL** — iff **≥ 6 of 9 ISOs** show the signature.
  ⇒ C3c's ledgered caveat has a named model-class cause, and the successor charter is a
  **DEMAND / RESERVE / COMMITMENT-REACH** one, not an offer-curve one.
- **PER-ISO** — otherwise.
  ⇒ name which ISOs have it; each is handed its own lane.

**Robustness leg (pre-registered, not chosen after the count):** the same test restricted to the
**7 price-scored ISOs** — the actual C3c population per §2.1 — at **≥ 5 of 7**. If the primary and
the robustness leg disagree, **both are reported and the verdict is stated as SPLIT**; neither is
selected after the fact.

---

## 5. What this lane does NOT do

- **It proposes no offer-curve lever.** Two lanes have now refused one on this exact evidence —
  PJM `measured_offer_surface` = **R** (`FINDING-pjm-offer-surface-noop-2026-07.md`, re-measured on
  the current keeper at h15 §3) and SPP refused in both admissible forms (RESULT-spp-70 §3).
  Re-testing either needs **new evidence, not a new framing** (rule 28 `[R-MECH-MATRIX]` (a)).
- **Nothing is armed, swept or promoted.** No keeper moves, no cell verdict is invented, no
  `ScenarioConfig` field is added. Rule 25 `[R-ISO-SCOPE]`: a measurement in PJM fills no cell in SPP.
- **It spends no LP.** If the question turns out to need one, this lane STOPS and writes the
  charter instead (rule 32 `[R-SHARD]` (a)).
- **It does not re-score any run.** Every determination stands exactly as committed.
