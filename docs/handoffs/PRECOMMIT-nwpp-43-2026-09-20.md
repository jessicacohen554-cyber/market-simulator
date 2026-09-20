# PRECOMMIT — nwpp-43: the chartered lever is ALREADY ARMED, and the C4 root cause re-routes

**Lane:** NWPP-43 · **Date:** 2026-09-20 · **Branch:** `claude/nwpp-43-campd-binning`
**Base SHA:** `8e50966d18ac588d673f626e8cefd350ef37f814`
**Keeper / control:** `2026-09-20-nwpp42-measured-coal-heat`, bundle `results/calibration/nwpp42_coalhr_span`
**LP spent by this session: ZERO** (rule 32(a) `[R-SHARD]`). Every number below is zero-LP.

---

## 0. The one-paragraph version

The lane was chartered to close C4 coal by **giving NWPP per-plant CAMPD binning**.
Phase 0 measured that **NWPP already has it**, and has had it since its first keeper.
Adding `NWPP` to `CAMPD_BINNING_ISOS` — the only gate the charter names — is a
**measured no-op: LP units +0, coal pmax +0.000 MW, every coal band identical**. The
premise three lanes carried ("the structural successor is per-plant CAMPD binning,
**blocked on `bin_assignments_NWPP.csv`**") is false three times over: that file is on
no solve path; `thermal_tranches_NWPP.csv` is committed and *is* the artifact the
synthesis reads; and the backcast orchestrator gates the synthesis on
`plant_level_fleet`, **not** on `CAMPD_BINNING_ISOS`. **No LP should be spent on this
arm.** The real defect is named, quantified and re-routed in §3–§5: NWPP's coal offer
stack has **no rising curve above must-run** — committed / econlo / econhi / peak sit
within **$0.51/MWh of each other** — so coal is binary, and it flips wholesale on the
gas price. The best-grounded successor is the **measured take-or-pay / regulated
committed band**, whose exact offer delta is measured in §5 and whose **overshoot risk
is stated rather than hidden** in §6. One scoping question is put to the owner in §7
because deciding it from the residual is what rule 1 `[R-STRUCT]` forbids.

---

## 1. (a) What must `bin_assignments_<ISO>.csv` contain? — NOTHING. It is not on a solve path.

The charter asked what the file must hold and whether NWPP's coal plants can be binned
from NWPP's own CAMPD record with zero free parameters. The question dissolves:

| claim | status | evidence |
|---|---|---|
| `bin_assignments_<ISO>.csv` feeds per-plant binning | **FALSE** | `fleet_to_bins` never reads it. Its only consumers are `ct_intermediate_plants` / `st_gas_intermediate_plants` (`campd_bins.py:2746`), **both default-off in this keeper** (`ct_intermediate_split=false`, `st_gas_intermediate=false`), plus offline derive scripts. |
| the per-plant artifact is missing for NWPP | **FALSE** | `data/raw/_processed-legacy/thermal_tranches_NWPP.csv` is **committed and tracked**, 68 rows, **12 COAL rows** carrying per-plant `committed_pct` / `mustrun_pct` / `online_frac` / `p25_cf` / `median_cf`. |
| NWPP takes the legacy aggregate path | **FALSE for the backcast** | `scripts/run_calibration.py:3853-3891` — the backcast's **own copy** of the synthesis — gates on `campd_bins is None and plant_level_fleet and thermal_tranche_overrides(iso)`. `backcast_config.py:1792` sets `plant_level_fleet=(iso != "ERCOT")`, so NWPP qualifies. `CAMPD_BINNING_ISOS` gates only `runner.py`'s `load_or_synthesize_bins` — **the forecast path**. |

**Zero free parameters, and none were needed**: the shares are the committed artifact's
own measured values. Derived, not chosen.

---

## 2. (b) Owner ruling N8 / gate G21 — NO REVISION IS NEEDED, because it is already inert here

N8 (NWPP desk sitting #4, 2026-09-14), verbatim: *"LEGACY HEAT-RATE BINS FOR THE FIRST
KEEPER; CAMPD PER-PLANT AS A LEVER … so `use_campd_bins=False`."* Gate **G21** gives the
reason: 939 plants × 5 zones would be the largest per-plant LP the repo holds, and CEMS
reaches only 30.98 % of footprint nameplate.

Three measured corrections, none of which asks the owner to move the ruling:

1. **`use_campd_bins` already reads `True`** in the keeper's own recipe — N8's stated
   consequence was never implemented as written. It is inert only because of the
   frozenset, which the backcast does not consult.
2. **G21's memory premise does not bind this lever.** Measured at the real control:
   **641 LP units in BOTH legs.** The per-plant path is already what runs; there is no
   6× LP to pay for. (The 939-plant figure counts the whole footprint — 36.3 % of it
   hydro — and only *thermal* plants are ever binned: 105 bin rows, 76 of them coal.)
3. **The ruling still governs the FORECAST path**, which `CAMPD_BINNING_ISOS` alone
   gates and which NWPP has not yet entered (card N9, no forecast lane).

**So this lane does not need N8 revisited and does not route around it.** What the
record needs is a correction, not a ruling: the "blocked on `bin_assignments_NWPP.csv`"
sentence is carried verbatim by the NWPP-41 and NWPP-42 attestations, by
`FINDING-nwpp-42` §1/§8, by the keeper shard note and by mechanism-matrix §5.9, and it
is wrong in all of them.

---

## 3. The measured no-op — the arm this lane was chartered to solve

`scripts/probes/_nwpp43_binning_phase0.py`, rebuilding the keeper's own recipe through
the sanctioned `run_year(..., fleet_only=True)` path, control vs `NWPP` added to
`CAMPD_BINNING_ISOS`, 2024:

| | CONTROL (as shipped) | ARM (NWPP in the frozenset) | Δ |
|---|---|---|---|
| LP units | 641 | 641 | **+0** |
| COAL LP units | 76 | 76 | **+0** |
| COAL pmax | 8,103.6 MW | 8,103.6 MW | **+0.000 MW** |
| COAL hard `pmin` | 0.0 MW | 0.0 MW | 0.0 |
| COAL band MW | mustrun 2,630.2 · committed 2,733.3 · econlo 1,417.9 · econhi 1,160.1 · peak 162.1 | **identical** | — |

Independently corroborated: a standalone `load_or_synthesize_bins` call with the
frozenset patched returns **105 bin rows / 76 coal tranche units / 8,103.6 MW** — the
same fleet the control already has. And the keeper's committed
`class_band_hourly_2024.parquet` carries `mustrun`/`committed`/`econlo`/`econhi`/`peak`
for COAL and *no* `mustrun` for gas — the exact `bins_to_fleet` signature — matching
SOCO's and SPP's sidecars, the other two "legacy-bin" ISOs.

---

## 4. What C4 actually fails on — measured, and it is NOT a binning defect

### 4.1 The coal stack has no rising curve above must-run

Cap-weighted mean assembled P0 offer (`mc_base`, the array the LP is handed):

| year | CC_REGULAR | COAL_BIT mustrun | committed | econlo | econhi | peak |
|---|---|---|---|---|---|---|
| 2023 | $50.52 | $4.50 | $36.02 | $33.66 | $33.66 | $34.89 |
| 2024 | **$22.81** | $4.50 | $42.09 | $42.19 | $42.19 | $42.60 |
| 2025 | **$26.81** | $4.50 | $43.07 | $43.41 | $43.41 | $43.74 |

**The whole 2,872 MW above must-run is priced within $0.51/MWh.** That is not a stack,
it is a step: a fuel-free block at $4.50, a $37.6 cliff, then one flat shelf. A fleet
shaped like that cannot produce the measured diurnal amplitude (measured peak/trough
1.183 / 1.237 / 1.311 against a model ≈1.02) no matter how it is binned — **per-plant
binning was never going to fix it**, which §3 now confirms by measurement.

### 4.2 And the shelf flips wholesale on the gas price

2023 CC $50.52 ⇒ every COAL_BIT band **below** CC ⇒ COAL_BIT 16.79 TWh (actual 14.59,
model **+2.19 over**). 2024 CC $22.81 ⇒ the shelf is **+$19.3 above** CC ⇒ 7.48 TWh
(actual 12.83, **−5.35**). 2025 CC $26.81 ⇒ **+$16.3 above** ⇒ 6.94 TWh (actual 18.21,
**−11.27**). In 2024 and 2025 COAL_BIT is **83.5 % and 86.1 % must-run** — the shelf
contributes almost nothing.

### 4.3 The fuel price is NOT the defect — limb ruled out

Implied model COAL_BIT fuel 2024 = $(42.19−4.50)/11.03 = **$3.42/MMBtu**, against the
measured EIA-923 quantity-weighted **$3.659** (4 plants). COAL_PRB $2.463 / $2.134 /
$2.066. The prices are measured and right; Utah bituminous genuinely rose ~28 % in 2024
while gas collapsed. **The model's SRMC arithmetic is correct and the plants still ran.**

---

## 5. (c) The re-routed lever, and its exact zero-LP prediction

**What the real plants are.** NWPP coal is **63.7 % regulated** by EIA-860
`Regulatory Status` — and **COAL_BIT, the deficit class, is 81.7 % regulated**
(2,998 of 3,668 MW: Hunter, Huntington, Bonanza, North Valmy). PRB is only 44.3 %.
The deficit is concentrated in the most-regulated class — a structural signature, not a
residual pattern. A cost-of-service utility does not offer its rate-based, contracted
mine-mouth coal on SRMC against gas; it self-commits.

**And the fuel is contracted, measured.** Derived here from the **committed**
`data/raw/coal-receipts/` corpus (EIA-923 Page 5 Purchase Type) by the **identical
quantity-weighted construction** the other seven ISOs' tables use — zero free
parameters, and **no network fetch** (the existing deriver reads the absent `f923_*.zip`;
the corpus carries the same columns):

| plant | share | breakdown | | plant | share | breakdown |
|---|---|---|---|---|---|---|
| 3845 Centralia | 1.0000 | C:100% | | 8066 Jim Bridger | 1.0000 | C:100% |
| 4158 Dave Johnston | 1.0000 | C:100% | | 8069 Huntington | 0.9888 | C:99%;S:1% |
| 4162 Naughton | 1.0000 | C:100% | | 8224 North Valmy | 0.5611 | NC:46%;S:44%;C:10% |
| 6076 Colstrip | 1.0000 | C:100% | | 50951 Sunnyside | 1.0000 | T:100% |
| 6101 Wyodak | 1.0000 | C:100% | | 55749 Hardin | 0.7612 | C:76%;S:24% |
| 6165 Hunter | 0.9816 | C:98%;S:2% | | 56224 TS Power | 0.9047 | C:90%;S:10% |
| 7790 Bonanza | 1.0000 | C:100% | | | | |

13 of 17 plants classified. **`coal_takeorpay_NWPP.csv` has never been derived** — the
file exists for ERCOT/CAISO/MISO/NEISO/NYISO/PJM/SPP and not NWPP — so
`coal_takeorpay_from_data` and `coal_committed_takeorpay_regulated` are **provably
inert** for NWPP today (`campd_tranche_fuel_frac` requires `takeorpay_by_plant` to carry
the plant). **This is the NWPP-41 defect class exactly**: an underived artifact making a
real mechanism silently do nothing.

**THE ARM.** Derive `coal_takeorpay_NWPP.csv`; arm `coal_takeorpay_from_data=True` +
`coal_committed_takeorpay_regulated=True` for NWPP in `backcast_config` (the
`iso.upper() == "MISO"` idiom already there). `coal_committed_takeorpay_regulated` is
**not currently plumbed into `backcast_config` at all** and would be added.

**THE MEASURED OFFER DELTA** (`p0d`, all three years, control vs arm) — **perfectly
confined and two-sided**:

| year | class · band | n | MW | ctl | arm |
|---|---|---|---|---|---|
| 2024 | COAL_BIT committed | 4 | 811.5 | $46.31 | **$10.53** |
| 2024 | COAL_BIT mustrun | 3 | 590.3 | $4.50 | **$12.54** |
| 2024 | COAL_PRB committed | 5 | 1,395.0 | $27.82 | **$4.50** |
| 2024 | COAL_PRB mustrun | 1 | 92.0 | $4.50 | **$8.99** |

**13 rows move of 641; NON-COAL ROWS MOVED: 0, in every year.** It is not a subsidy: the
spot-heavy plants' must-run gets **dearer** (North Valmy 0.5611, Hardin 0.7612,
TS Power 0.9047 now pay for their spot remainder) while the contracted regulated
committed band gets cheaper. Moved capacity 2,888.8 MW, identical all three years.

**(c) THE PREDICTION, in the §6.1 currency the charter demands.** COAL_BIT committed
811.5 MW crosses from $19.3 **above** CC to $12.3 **below** it, so it should run
near-continuously: upper bound 811.5 MW × 8760 h = 7.11 TWh against ~0.32 TWh today,
i.e. **+6.8 TWh gross, ≈ +5.5 to +6.0 TWh after availability and outage derates**,
against a 2024 COAL_BIT deficit of **−5.35 TWh**. COAL_BIT mustrun rising to $12.54
stays well under CC $22.81, so ~0 is given back.

---

## 6. (d) THE KILL CONDITION — pre-registered, on 2024, and it can fire BOTH ways

The charter required a condition that can actually discriminate, on the year where the
deficit lives. NWPP-42's fired on neither year but **would** have on 2024; **2024 is
therefore this lane's kill year**, named before any solve.

> **KILL — INERT limb:** 2024 **COAL_BIT** rises by **< 2.0 TWh** against the committed
> keeper ⇒ verdict **I (inert)**, not a keeper. (The arm is predicted to move it
> +5.5–6.0 TWh; anything under 2.0 means the committed band did not clear and the
> mechanism is not doing what §5 says it does.)
>
> **KILL — OVERSHOOT limb:** 2024 **COAL_BIT** overshoots the actual 12.832 TWh by
> **> 2.0 TWh** (i.e. model > 14.83), **or** any C1 coal row leaves its
> ±min(max(2 % ISO-load, 3 % actual-gen), 8 TWh) / ±3 pp band in any year ⇒ verdict
> **R (rejected)**. Not renegotiable after the fact.

**THE OVERSHOOT RISK IS REAL AND IS NOT BURIED.** Two independent reasons the arm may
fail its own second limb, both visible now:

1. **PRB is over-served.** COAL_PRB committed 1,395 MW goes to $4.50 — upper bound
   +7.9 TWh against a 2024 PRB deficit of only **−1.36 TWh**.
2. **2023 is already over.** COAL_BIT 2023 is **+2.193 TWh over** actual (the one row
   NWPP-42 degraded). This arm pushes it further over, toward the ±8 TWh band.

**Contested prior art, cited rather than glossed.** `coal_committed_takeorpay_sunk_fixed`
exists precisely to *suppress* this discount, and its rationale is physics, not an ISO
verdict: *"a take-or-pay contract is an obligation over an accounting period, not a
per-hour price … discounting the committed band as well subsidises the MARGINAL MWh in
all 8760 h (rules 17/19, miso-96)."* A successor must answer that argument, not ignore
it. Rule 28(d) keeps MISO's verdict out of NWPP's cell, but the reasoning travels.

---

## 7. THE ONE QUESTION FOR THE OWNER — because answering it from the residual is forbidden

`coal_prb_committed_dispatchable` would scope the committed-band discount to
**bituminous only**, excluding PRB (MISO measured PRB committed bands cycling
price-responsively even at regulated plants — miso-111). Scoping it that way removes
exactly the overshoot in §6(1) and leaves the arm pointed at the deficit class.

**Which is precisely why I will not choose it here.** Picking the scope that makes the
gate pass is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, and NWPP's own
measured conduct does **not** discriminate: the p25→median CF spread is ~9–20 pts in
both ranks (BIT: Hunter 9.5, Huntington 15.5, North Valmy 7.1; PRB: Colstrip 8.7,
Wyodak 9.6, Hardin 14.0, Naughton 39.5). The scope must be fixed **ex ante**, by ruling
or by an independent measurement, before any LP is spent.

---

## 8. Carried, absorbed nowhere

- Energy balance **−10.02 TWh in 2025** against a ±3.0 tol (NWPP-40's served-interchange
  construction).
- **Chief Joseph's pond-balance dual** constant at −325.17 $/kcfs·h for 5,808 hours of
  2025 with pond = 0 and spill = 0 — untouched again; still the first cascade question.
- **C5a CO2** a reported-only FAIL in all three years (−14.4 / −23.5 / −20.6 %).
- **2023 COAL_BIT +2.193 TWh** is NWPP's nearest thing to a C1 headroom constraint.
- **Jim Bridger (8066)** is absent from `thermal_tranches_NWPP.csv` and takes the
  `_DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"]` (45/5/2) fallback for 1,049 MW — found here,
  not this lane's to fix, but it is an estimate standing where a measurement could.
- The cross-ISO PRB-proxy defect open in MISO / PJM / SPP — not this lane's.
- `results/calibration/caiso279_ablate_dswcouple_span` remains a pre-existing
  `check_registry_payload_parity` RED with 34 TRACKED files — CAISO's, not this lane's.
