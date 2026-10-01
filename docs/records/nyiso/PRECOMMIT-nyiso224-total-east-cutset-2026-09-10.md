# PRECOMMIT — nyiso-224: the Upstate→east link is capped at the WRONG CUTSET

**Session:** nyiso-224 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Arm:** `nyiso_total_east_cutset_ttc` (new, default OFF)
**Control:** the committed keeper-recipe 2022 touchpoint bundle
`results/calibration/nyiso_fuelvintage_H2/` (run `2026-09-09-nyiso-221-fuelvintage-tp2022`),
rule 29(b) **form 4** — no control solve is spent. G-DRIFT below.
**Screen year:** **2022**, chosen on the mechanism's own measured footprint (§4), never on the residual.
**Written and pushed BEFORE any LP.** The parent runs no solve (rule 32 `[R-SHARD]` (a)).

---

## 0. The headline

**The 2022 C3a failure is an UPSTATE failure.** It is not the December archive gap, not the
price tail, and not a level. `Upstate_West` carries **63.5 %** of the whole 2022 price gap, and
the model prices it at **$33.71/MWh against a measured $60.61**. The mechanism is a
**cutset misalignment**: the model's single `Upstate_West → Capital_Hudson` link is the
A–E → F+ cutset — NYISO's **TOTAL EAST** — but it is capped at the posted **CENT EAST** DAM
TTC, a *nested sub-cutset* carrying about half the flow. The cap therefore sits **below the
measured cutset flow in 86.3 % of 2022 hours**, the link separates in **97.1 %** of hours
against a market whose binding sub-cutset is ≥95 % loaded in **10.0 %**, and the upstate price
pins at exactly **$1.40 in 42.9 %** of hours.

The defect is **chronic and gas-amplified**, which is why 2022 alone fails.

---

## 1. Phase 0 — ZERO LP, off the committed control

All numbers below are computed from `nyiso_fuelvintage_H2/hourly/*` (P1), the committed
`nyiso_fuelvintage_A` sidecars for 2023–2025, `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`,
the raw NYISO zonal RT LBMP zips under `data/raw/lmp-data/NYISO/`, and
`data/raw/NYISO/interface-flows/`. No solve was run.

### 1.1 The gap is 400 hours, and it is not the tail alone

| bucket (actual RT $/MWh) | hours | model LW | actual LW | contribution to the LW gap |
|---|---|---|---|---|
| < 100 | 7,241 | 59.64 | 56.93 | **−20.6 %** (model too HIGH) |
| 100–150 | 975 | 100.30 | 119.71 | +24.5 % |
| 150–200 | 284 | 115.02 | 169.84 | +20.4 % |
| 200–300 | 159 | 147.24 | 236.79 | +19.1 % |
| 300–500 | 79 | 119.36 | 368.55 | +26.8 % |
| ≥ 500 | 22 | 100.02 | 1129.03 | +29.7 % |

The **400 most under-priced hours carry 100.0 %** of the +$10.45 LW gap; the top 100 carry
56.8 %. Deciles 1–7 of the actual-price distribution contribute **negatively**.

### 1.2 It is present against DAY-AHEAD too, so it is not RT volatility

| year | model LW | DA LW | RT LW | model vs DA | model vs RT |
|---|---|---|---|---|---|
| **2022** | 69.92 | 77.43 | 80.37 | **−9.7 %** | −13.0 % |
| 2023 | 33.65 | 32.79 | 32.05 | +2.6 % | +5.0 % |
| 2024 | 40.15 | 38.87 | 38.13 | +3.3 % | +5.3 % |
| 2025 | 61.60 | 65.33 | — | **−5.7 %** | — |

72 % of the RT gap is already there against DA — the market this LP most resembles. The two
**high-gas** years under-shoot; the two **cheap-gas** years over-shoot.

### 1.3 The gap is ZONAL, and it is upstate (2022, full year)

Model zonal price vs measured NYISO zonal RT LBMP (`WEST GENESE CENTRL NORTH MHK VL` →
`Upstate_West`; `CAPITL HUD VL` → `Capital_Hudson`; `MILLWD DUNWOD` → `Lower_Hudson`;
`N.Y.C.` → `NYC`; `LONGIL` → `Long_Island`):

| model zone | model | measured | gap | load TWh | contribution |
|---|---|---|---|---|---|
| **Upstate_West** | **33.71** | **60.61** | **+26.89** | 52.91 | **+9.32 (63.5 %)** |
| Long_Island | 91.78 | 107.92 | +16.14 | 20.10 | +2.12 |
| Capital_Hudson | 86.54 | 98.27 | +11.73 | 21.26 | +1.63 |
| NYC | 89.17 | 93.19 | +4.02 | 49.74 | +1.31 |
| Lower_Hudson | 88.94 | 93.92 | +4.99 | 8.68 | +0.28 |

Upstate's gap is **large in every month** (+8.7 to +49.0), i.e. it is not an event, a season
or a tail.

### 1.4 On identical months the model INVERTS the two years

Feb, Mar, Apr, May, Jun, Sep — same six months, both years:

| | 2022 model / measured | 2024 model / measured |
|---|---|---|
| **Upstate_West** | **20.59 / 48.62 (−57.6 %)** | 32.39 / 27.42 (+18.1 %) |
| NYC | 82.31 / 78.10 (+5.4 %) | 35.71 / 31.76 (+12.4 %) |

The market says 2022 upstate was **77 % dearer** than 2024 upstate. The model says it was
**36 % cheaper**.

### 1.5 The model's upstate price is PINNED, and the pin is the link

Model `Upstate_West` price distribution, same six months:

| year | share < $5 | 20th–50th percentile | mean NYC−Upstate spread | share of hours spread > $20 |
|---|---|---|---|---|
| **2022** | **42.9 %** | **all exactly $1.40** | **$59.71** | **97.1 %** |
| 2023 | 15.9 % | 1.40 … 22.57 | $13.41 | 20.6 % |
| 2024 | 0.0 % | 26.90 … 29.44 | $2.95 | 0.5 % |
| 2025 | 0.0 % | 29.51 … 37.16 | $7.91 | 5.5 % |

Measured 2022 NYC−Upstate is **$32.6**, not $59.71. Slack is 360 MWh (NYC only) and dump is
**0.0** — nothing is being spilled; the zones are simply decoupled.

---

## 2. The mechanism, measured on NYISO's own postings

The five-zone reduction folds NYISO load zones **A–E** into `Upstate_West`, so the one
`Upstate_West → Capital_Hudson` link **is** the A–E → F+ cutset. NYISO's name for that cutset
is **TOTAL EAST**. `constants.NYISO_INTERFACE_TTC_BY_MONTH` caps it at the posted **CENT EAST**
DAM TTC — a nested sub-cutset.

| year | model cap (CENT EAST) | measured TOTAL EAST mean flow | measured CENTRAL EAST mean flow | hours the cap is BELOW the measured cutset flow | energy the cap cannot carry |
|---|---|---|---|---|---|
| **2022** | **1,825 MW** | **3,170.7 MW** | 1,544.4 MW | **86.3 %** | **12.261 TWh** (mean deficit 1,399.6 MW) |
| 2023 | 1,750 MW | 3,004.8 MW | 1,328.3 MW | 95.8 % | 11.077 TWh |
| 2024 | 2,850 MW | 3,219.5 MW | 1,758.6 MW | 61.3 % | 5.505 TWh |
| 2025 | 2,850 MW | 3,129.0 MW | 1,664.0 MW | 58.2 % | 5.686 TWh |

This is rule 14 `[R-ACCURATE]`'s misalignment exception **verbatim**: *"a single GTC that is
one of several parallel paths our reduced network collapses into one link."*

**Why 2022 alone fails, when the misalignment is chronic.** Because upstate is pinned at its
cheapest offer whenever the link separates, the *price* error is (downstate marginal cost −
$1.40) × the separated share. That scales with gas. 2022 mean Transco Z6 NY is $6.67/MMBtu
against ~$3 in 2023; the same structural error costs +2.6 % of over-pricing in 2023 and
−9.7 % of under-pricing in 2022. §1.2's four-year DA table is the same statement.

**What this is NOT, and the DO-NOT-REDO check (rule 30(a)).**
- It is **not** `measured_interface_limits` (NYISO cell **G**, nyiso-109/169). That refusal is
  *"the posted limits do not bind"* / *"the measured congestion is invariant to whether they
  bind"*. The new evidence is the opposite quantity: the incumbent cap sits **below the
  measured flow of the cutset the link represents** in 86–96 % of hours. That is not a
  limit that fails to bind.
- It is **not** *"re-estimating the Central-East limit"*, which nyiso-169 explicitly warned
  against on the `nyiso_central_east_measured_ttc` cell (**K**, and it stays K and stays
  armed for what it is). The CENT EAST posting is correct **for CENT EAST**; the claim here
  is that CENT EAST is the wrong boundary for this link.
- nyiso-169's own conclusion — *"the model OVER-separates the link it under-prices
  (Upstate_West→Capital_Hudson 82–99 % of hours vs a market congested 15–55 %)"* — is
  **reproduced here on 2022 (97.1 %)** and is the object this arm addresses. What is new is
  the boundary diagnosis, the 2022 magnitude (63.5 % of the year's gap) and the
  gas-amplification that explains the year pattern.
- nyiso-125's identification refusal on `Upstate_West` is about the **external border**
  envelope, where `SCH - PJ - NY` spans the cutset and no posting separates the legs.
  `TOTAL EAST` is a single unambiguous **internal** cutset row with zero attribution freedom.

---

## 3. The arm

`ScenarioConfig.nyiso_total_east_cutset_ttc: bool = False` — armed via
`--set nyiso_total_east_cutset_ttc=true`. On the one seam
`pipeline/ttc.py::apply_iso_monthly_ttc`, `constants.NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH`
**REPLACES** `NYISO_INTERFACE_TTC_BY_MONTH` for that link — the two never stack (rule 19
`[R-ONE-MECH]`). Every other link, every other ISO, every forecast and every unarmed run is
byte-identical (test `test_nyiso_total_east_cutset_ttc_replaces_central_east`; default
`cache_key` `ee3430288b1771e7` on main **and** at HEAD; armed `d68ac8dad9c84c38`).

**Construction — INHERITED, NOT CHOSEN (rule 21 `[R-DOF]`: ZERO free parameters).** Verbatim
the construction already armed for NYISO's border links by `nyiso_seam_deliverability_envelope`
(nyiso-125, cell **K**): the **p90 of the directionally-clipped measured transfer** within each
bin. The bin is the calendar month — the bin the incumbent table already uses — rounded to
25 MW, that table's own rounding. Source is the same MIS producer as the CENT EAST table;
derive script `scripts/data/derive_nyiso_total_east_envelope.py`; backcast-only on the
identical classification. 2022 (MW): `5425 5500 4350 2650 3325 3825 4275 4400 3700 3150 2225 4675`.

**A VARIANT ALREADY KILLED IN PHASE 0, BEFORE ANY LP.** The *pure posted TOTAL EAST limit*
(mean 6,408 MW in 2022) would bind in **~0–1 %** of hours — overshooting the measured congested
band on the far side and making the link effectively inert. It is refused here and is not what
this arm does.

---

## 4. Screen year — chosen on FOOTPRINT, never on the residual (rule 29)

| year | incumbent cap | reconciled envelope mean | **footprint** | binding share, incumbent | binding share, armed |
|---|---|---|---|---|---|
| **2022** | 1,825 MW | 3,879.6 MW | **+2,054.6 MW** | 86.3 % | 9.85 % |
| 2023 | 1,750 MW | 3,656.9 MW | +1,906.9 MW | 95.8 % | 9.86 % |
| 2024 | 2,850 MW | 4,072.5 MW | +1,222.5 MW | 61.3 % | 9.84 % |
| 2025 | 2,850 MW | 4,051.5 MW | +1,201.5 MW | 58.2 % | 9.86 % |

**2022 has the largest measured footprint** and is the screen year. It happens also to be the
failing year; the selection rule is the footprint column and would pick 2022 if 2022 passed.

---

## 5. THE PRE-REGISTERED STRUCTURAL GATE — a STOP gate, never a residual gate

The gate below is fixed before the solve. **It may kill the arm; it may not promote one.**
It is nowhere a function of C3a, C3b or any residual (rule 1 `[R-STRUCT]`).

**G-1 — the link stops over-separating, and does not go inert.** The armed run's share of
2022 hours in which `NYC − Upstate_West > $20` must fall to **within [8 %, 60 %]**.
Pre-registered because the measured band is 10.0 % (CENT EAST ≥95 % loaded) to 55 %
(nyiso-169's posted-MCC-non-zero upper bound). Incumbent 97.1 %.
**FAIL if > 60 % (nothing moved) or < 8 % (the link went inert).**

**G-2 — the $1.40 pin clears.** Share of 2022 Feb/Mar/Apr/May/Jun/Sep hours with
`Upstate_West < $5` must fall from **42.9 %** to **below 15 %** (2023's incumbent value on
the same measure, i.e. a level the model already reaches in a year it passes).
**FAIL if ≥ 15 %.**

**G-3 — the footprint is confined to the one link.** The armed run's `Capital_Hudson →
Lower_Hudson`, `Lower_Hudson → NYC` and `NYC → Long_Island` TTC columns must be byte-identical
to the control's, and the arm must touch no fuel, fleet, offer or reserve array.
**FAIL on any non-TTC input difference.**

**G-4 — direction is not selectable.** Upstate price must RISE and downstate price must FALL,
in the same solve. **FAIL if both move the same way** (that would mean the change is acting
through something other than the link).

**G-5 — no non-target load-bearing criterion flips PASS → FAIL.** Scored in the parent
(§7). C1 and C2 2022 already FAIL/PASS as recorded; a **new** failure in C2 or C4 stops the arm.

### Falsification tests registered AGAINST the arm

1. **F-1 — energy conservation.** Total 2022 system energy must move by < 0.05 TWh. A cutset
   limit re-places energy between zones; it does not create it.
2. **F-2 — the arm must NOT fix 2023/2024 in the same direction.** 2023 and 2024 model upstate
   is already *above* measured. If the arm raises upstate everywhere, it must make 2023/2024
   **worse**, and I say so here in advance. An arm that improves every year in every zone is
   an arm acting through a fitted channel, not a cutset limit.
3. **F-3 — the incumbent path must survive untouched.** Unarmed 2022 must reproduce the
   control's committed hourlies exactly.

**Predictions, stated before the solve so they can miss.**
- G-1 lands in **[9 %, 25 %]**. G-2 lands **< 5 %**.
- 2022 Upstate_West annual model price rises from **33.71** to somewhere in **[45, 62]**.
- 2022 NYC falls from **89.17** by **$3–12**.
- 2022 C3a improves but **does not clear ±10 %**: predicted **−4 % to −9 %** (from −13.9 %).
- 2023 and 2024 C3a get **worse** (F-2), predicted to **+5 to +9 %**, and 2024 may cross the
  +10 % bar. **If it does, that is a real cost of a correct input and it is reported at full
  magnitude, not absorbed** (rules 1/14).

---

## 6. G-DRIFT (rule 29(b)) — the keeper's committed bundle IS the control

`git diff c430970e HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` (control `nyiso_fuelvintage_H2`,
`git_sha` `c430970e`). 19 files. Every hunk on the backcast path is **INERT for NYISO**:

| file | classification |
|---|---|
| `config/constants.py` | **comment-only** — no non-comment line changed |
| `config/scenarios.py` | four new fields (`caiso_dsw_lateevening_clean`, `spp_curtailment_ceiling`, `spp_curtail_depth_wind`, `nyiso_hub_gap_month_level`, `ercot_ep_gas_basis_receipts_fallback`), **all default-off and all absent from the keeper recipe** |
| `data/fuel/hubs.py` | the `nyiso_hub_gap_month_level` gate — **default off, absent from the recipe** |
| `data/outages.py` | 11 **PJM** plant ids added to `ST_GAS_PEAKER_PLANTS`; no NYISO plant |
| `data/renewables.py`, `data/curtailment_share.py`, `runner.py` | gated `iso == "SPP"` |
| `data/fuel/basis/ercot.py` | ERCOT branch |
| `model/interchange/{__init__,caiso,spec}.py` | CAISO branch |
| `config/solve_surface_declared.py` | adds a NYISO fingerprint **declaration**; changes the cache key only, not the LP |
| `scripts/run_calibration*.py`, `scripts/lib/holdout_policy.py` | CLI / `[R-HOLDOUT]` removal; not solve-affecting |
| `data/raw/_validation-source/*.json`, `data/raw/reference/spp_curtailment_share.csv` | **scoring**-side and SPP; not on the solve path |

**All INERT ⇒ G-CTRL form 4 is valid and NO CONTROL SOLVE IS SPENT.**

---

## 7. Execution (rule 32 `[R-SHARD]`)

- The **parent** does phase 0, the implementation, this PRECOMMIT, the SHA pin, then
  composition, gate evaluation, scoring, dashboard registration and the promotion question.
  **The parent runs no LP.**
- **One shard, one year, ≤ 20 min**: 2022, `replay_keeper.py … --set nyiso_total_east_cutset_ttc=true`,
  its own `--out-dir`, its own branch, pinned to this doc's 40-char SHA.
- Shards **cannot** score C3a/C3b (the `lmp` clean partition cannot be built in a fresh
  container — `curate_lmp.py` raises `KeyError: 'MGHG'` on a CAISO file, a pre-existing defect
  no shard may repair). Shards report raw model prices, class TWh and
  `legitimacy_diagnostics`; **all scoring happens in the parent** (rule 32(d)).
- The full 2022–2025 span is spent **only if the screen clears §5**. Rule 16 `[R-ALLYEARS]`
  is untouched: the screen bundle is a throwaway probe, never registered, never a keeper.
- Rule 31 `[R-RETAIN]`: nothing is deleted, the bundle family is `.gitignore`d, and the
  promotion question is put to the owner explicitly before the session ends.

## 8. Governance

- **Rule 1 `[R-STRUCT]`** — structural; the authorized offer-curve channel is **NOT** used.
  `authorized_price_tuning` = **NONE**. The gate is structural and is a STOP gate.
- **Rule 13/14** — the basis. Same producer, same recipe, identical construction forward.
- **Rule 19 `[R-ONE-MECH]`** — one seam; the cutset table REPLACES the CENT EAST table.
- **Rule 21 `[R-DOF]`** — **zero** new free parameters; the p90/month/25 MW construction is
  inherited from an already-armed NYISO mechanism, not selected here.
- **Rule 24 `[R-REGISTRY]`** — one `ScenarioConfig` field, in `run_config.json`; no env knob,
  no hardcoded dict, no `getattr` fallback literal in the offer path.
- **Rule 25 `[R-ISO-SCOPE]`** — NYISO-only seam; every other ISO's cell is `.`.
- **Rule 30 `[R-MECH-MATRIX]`** — base row + a cell in all seven shards, this PR. Also closes
  nyiso-223's missed duty (c) in `SPP.js`. **Known pre-existing red, not this lane's:**
  `spp_curtailment_ceiling` has no cell in `SPP.js` (red on `main` before this PR).
