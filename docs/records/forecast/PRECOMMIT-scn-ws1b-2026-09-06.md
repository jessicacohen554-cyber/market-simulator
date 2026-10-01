# PRECOMMIT — SCN-WS1b: six-ISO carbon paired probe + NEISO/ERCOT T1-F ladder

**Lane:** SCN-WS1b · **Branch:** `claude/scn-ws1b-carbon-probe-70cqt8` · **Date:** 2026-09-06
**Model:** `claude-opus-5` (rule 27 `[R-PUSH]`; this lane writes no `src/`)
**Charter:** plan `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §7 "WS-1b"
(= §3 WS-1 items 4–6); desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#3.
**DATA PROFILE:** `all` · **Rule 29 `[R-SCREEN]`:** this document is pushed **before the first
solve**. Nothing below may be edited after a result is seen; corrections are appended and dated.

---

## 0. Preconditions, verified with `git log` before starting

| precondition | verified |
|---|---|
| SCN-WS0 all six items on `main` | `d5be0216` (PR #4877 merge) — `scenario` registration kind (`c95f59de`), `--set` (`e6464bde`), `report_scenario_deltas.py` (`cf7170f4`), `collate_scenario_campaign.py` (`a248c8ac`), the REF base YAMLs (`e6464bde`), the G-E4 rider (`47ba0610`) |
| SCN-WS1a on `main` (G-C2 + G-C3 closed, matrix rows minted) | `0bdcebd8` (PR #4887 merge); rows minted at `717de664`; CAISO T0 scored at `a147362b` |
| desk pin | `ea273339` present in this branch's history; branch cut from `eb8ae4db` (later `main`) |
| `data/clean` (FF plan §2.4 HARD prerequisite) | absent on this container; `scripts/regenerate_clean.py` started before any solve, ~55 min, budgeted |

---

## 1. CARD GATE — the reduced form, and why

**Owner box D-1 is OPEN** (desk ledger §2 at my start: *"RE-PRESENTED r#2 on new evidence"*,
recorded ruling column empty; no ruling in any refresh). SCN-WS1a's item 1 has therefore **not**
landed, and `carbon_price_path` still carries **REPLACE** semantics.

**This lane therefore runs the reduced arm — `--set carbon_price_delta=25` — and NOT
`carbon_price_path=mid`.** The reason, measured, not asserted: under REPLACE an explicit
non-`zero` path nulls the state programme adder (`cap_and_trade.py:289-291`), so a path-written
arm is a carbon-price **CUT** of $16–$102/t on CAISO / NYISO / NEISO in every one of 25 horizon
years (`FINDING-scn-ws1a-2026-09-05.md` §0.1). A campaign row labelled "federal carbon price"
would report LOWER carbon on three of my six ISOs and **the pair's premise would be inverted** —
the D23 lesson, one field over. `carbon_price_delta` is additive on the resolved signal after the
whole precedence chain, so it is a genuine +$25/t increase in every ISO with or without a
programme. §2 proves that with a number, before any solve.

If D-1 reads **FLOOR** in ledger §2 at a future session's start **and** SCN-WS1a's item 1 has
landed, the charter's full form (`carbon_price_path=mid`) is the arm to run instead. It does not
at mine.

## 1.1 The ladder form for leg 2 — chosen HERE, before any result

The charter offers two forms while D-1 is open: invent delta rungs (+$10/+$25/+$50), or run REF +
the single +$25 rung and say the ladder waits on D-1. **I choose neither of those literally: I run
the ladder that is already COMMITTED in `configs/scenario_campaign_matrix.yaml` — `CARB-LO` /
`CARB-MID` / `CARB-HI` = `carbon_price_delta` **15 / 25 / 50** $/t — and name them as delta
rungs, never as RFF paths.**

Reason: SCN-WS0 already landed exactly this reduced-form ladder in the committed campaign case
set, with the same reasoning this lane was handed, and wrote *"25 is the level SCN-WS1b's
reduced-form probe is chartered on"* into the file. Inventing a parallel +10/+25/+50 set would
fork the campaign's case names from the committed ones for no gain; running the committed rungs
keeps leg 2's output directly comparable to every later campaign leg. The rungs stay
**ILLUSTRATIVE pending owner card D-2**, exactly as the YAML says, and the FINDING will name them
`CARB-LO/MID/HI (delta rungs +$15/+$25/+$50 on the resolved signal)` — never "RFF low/mid/high".
I do not edit that file (it is SCN-WS4b's); leg 2 passes a carbon-only *subset* of it, written
under `docs/handoffs/scn-ws1b/`, so no owned file is touched.

---

## 2. Phase 0 — the zero-LP census (rule 29 step 0; instrument + outputs committed)

Instrument: `docs/handoffs/scn-ws1b/phase0-census-2026-09-06.py`
(`.json` / `.txt` outputs beside it). It builds each ISO's config with
`scripts/run_full_horizon.reference_config(iso, 2026, 2030, cmc=False)` — the **same builder the
solves use** — so this is the config the arms actually receive, not a reconstruction.

### 2.1 The arm is a genuine +$25/t increase in all six ISOs, in every year

Resolved carbon signal, $/tCO2, `policy.carbon.resolve_carbon_price`:

| ISO | arm | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|
| ERCOT | REF | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ERCOT | ARM | 25.0000 | 25.0000 | 25.0000 | 25.0000 | 25.0000 |
| CAISO | REF | 30.0242 | 32.1259 | 34.3747 | 36.7809 | 39.3556 |
| CAISO | ARM | 55.0242 | 57.1259 | 59.3747 | 61.7809 | 64.3556 |
| PJM | REF | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| PJM | ARM | 25.0000 | 25.0000 | 25.0000 | 25.0000 | 25.0000 |
| MISO | REF | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| MISO | ARM | 25.0000 | 25.0000 | 25.0000 | 25.0000 | 25.0000 |
| NYISO | REF | 23.6363 | 25.2908 | 27.0612 | 28.9555 | 30.9824 |
| NYISO | ARM | 48.6363 | 50.2908 | 52.0612 | 53.9555 | 55.9824 |
| NEISO | REF | 26.0545 | 27.8783 | 29.8298 | 31.9179 | 34.1521 |
| NEISO | ARM | 51.0545 | 52.8783 | 54.8298 | 56.9179 | 59.1521 |

**Δ = exactly +25.0000 in every cell, all six ISOs, all five years.** (Compare the path form: a
cut of $16–$102/t on the three programme ISOs. §1's choice is this table.)

### 2.2 The leakage surface — which ISOs *can* leak, established before the solve

Every import pseudo-generator `model.interchange.import_nodes.build_import_generators` builds at
2026, with the disclosure factor `results.emissions.import_tranche_ef` returns for it. The LP
itself holds **every** import `emission_rate_co2` at zero; the EF below is the reported-only line.

| ISO | import pseudo-gens | carbon-bearing (EF > 0) | carbon-bearing MW | border carbon priced on imports? |
|---|---|---|---|---|
| **ERCOT** | **0** | **0** | 0 | — (no import node at all) |
| **MISO** | **0** | **0** | 0 | — (`IMPORT_ZONE` names `MISO_external`, but `IMPORT_TRANCHES` has no MISO entry, so no tranche is built) |
| CAISO | 6 | 3 (DSW_CCGT 0.37, DSW_CT 0.55, WECC_scarcity 0.428) | 7,000 | **YES** — the CARB border adjustment, `0.428 × resolved price`, rides the tranche VOM |
| PJM | 2 | 2 (both 0.428 default) | 4,000 | no |
| NYISO | 7 | 6 (all 0.428 default; only HQ_hydro is zero-EF) | 5,585 | no |
| NEISO | 6 | 4 (NB_north, NYISO_CT_base, NYISO_CT_peak, import_scarcity; Highgate + HQ_PhaseII zero-EF) | 2,465 | no |

### 2.3 CCS retrofit availability

`ccs_retrofit_available_year = 2028` in **all six** ISOs. **The 2026 T0 therefore cannot show a
retrofit response at all** — that is a construction fact, declared here so no §3 gate row reads
one, and so a null in leg 1 is never reported as an absence of response. Leg 2 (2026–2030) covers
2028–2030 and can.

---

## 3. THE PRECOMMIT PROPER

### 3.1 Screen year, arm, construction

- **Screen year: 2026** — named here, before any solve. It is the T0's single year and the year
  the mechanism's own measured footprint is fully live: §2.1 shows the resolved Δ is +25.00 in
  2026 exactly as in every later year, so the mechanism is at full strength in the screen year.
  It is **not** chosen for any residual (there is no residual — this is a forecast pair, and rule
  29 forbids a residual-driven screen year in any case).
- **Arms:** `REF` (the committed campaign base posture) and `CARB` = REF + the single override
  `carbon_price_delta=25.0`.
- **Construction:** `scripts/run_full_horizon.py --iso <ISO> --start-year 2026 --end-year 2026
  --out-dir results/scn-ws1-probe/<iso>/<ARM> [--set carbon_price_delta=25]` — byte-for-byte
  SCN-WS0's own T0 construction (`reference_config(..., cmc=False)` + `apply_set_overrides` +
  `solve_and_summarize`), which is what makes my six pairs comparable with the committed
  `scn-ws0-smoke` pair.
- **Control (rule 29 clause b): the REF arm of each pair IS the control.** These are forecast
  pairs, so the control is not a keeper differencing question — both arms are solved at the same
  HEAD, in the same session, with one field between them. No control solve is spent beyond the
  six REF arms the pair definition requires, and **NEISO's REF/CARB pair additionally
  re-measures SCN-WS0's committed 2026 pair at a later HEAD**, which is a free G-DRIFT read: if
  NEISO REF/CARB reproduce `16.3081 / 13.5987` Mt and `$52.13 / $62.28`, every solve-path change
  between `c95f59de` and my HEAD is inert for NEISO 2026; if they do not, the difference is
  reported as drift, not as a carbon result.

### 3.2 Expected sign, order of magnitude and footprint — PER ISO, before the solve

The arithmetic every row below is an instance of: a carbon price enters `mc` as
`emission_rate × carbon_price`, so an hour whose marginal unit has rate `r` re-clears
`+25 × r` $/MWh higher, and the load-weighted price rises by `25 ×` the **generation-weighted
mean rate of the marginal unit across hours**. Repo rates (`constants.CO2_RATES`): gas_cc
0.36–0.43, gas_ct 0.51–0.65, gas_st 0.59, coal 0.88–1.08, oil 1.00. So:
gas-CC-marginal hours ⇒ **+$9.0–10.8/MWh**; gas-CT-marginal ⇒ **+$12.8–16.3**;
coal-marginal ⇒ **+$22.0–27.0**; VRE/nuclear/storage-marginal ⇒ **+$0**.

| ISO | Δ load-weighted price, predicted | Δ CO2, predicted | coal→gas re-order? | note |
|---|---|---|---|---|
| **ERCOT** | **+$6–10/MWh** — gas-CC marginal in most hours, coal in some, and a material tail of wind/solar-marginal (zero-Δ) hours pulls the average down | **−1 to −5 %** | **YES, visible** — ERCOT carries coal; expect coal CO2 to fall proportionally more than gas CO2 | no import node ⇒ the whole response must be in-fleet |
| **CAISO** | **+$9–11/MWh** — gas-CC marginal in most hours (WS-1a measured +$9.82 on this exact arm/year) | **−2 to −4 %** | trivial — CAISO's coal is ~359 GWh, so any re-order is too small to read | the only ISO whose imports also get dearer |
| **PJM** | **+$10–18/MWh** — a genuine mix of gas-CC- and coal-marginal hours | **−4 to −10 %** | **YES, strongly** — the largest coal fleet of the six | import tranches are only 4 GW of scarcity blocks |
| **MISO** | **+$12–22/MWh** — the most coal-marginal fleet, so the highest predicted price response of the six | **−5 to −12 %** | **YES, strongly** | no import node ⇒ in-fleet only |
| **NYISO** | **+$9–14/MWh** — gas-CC and gas-CT marginal; no coal | **−2 to −6 %** | **NO — no coal in the fleet**; a coal row appearing at all would itself be a footprint failure | 6 carbon-bearing import tranches, none border-priced |
| **NEISO** | **+$9–11/MWh** — gas-CC marginal nearly always (WS-0 measured +$10.15 on this exact arm/year) | **−12 to −18 %** (WS-0 measured −16.6 %; a reproduction) | **NO — no coal** | the reproduction/G-DRIFT arm |

**Footprint claimed, all six ISOs:** the response is confined to (a) **fossil generation rows** —
gas_cc, gas_ct, gas_st, coal, oil — whose `mc` moves by `rate × 25`; (b) **import tranches**,
which move because the in-ISO stack around them moved (and, on CAISO alone, because their own
border adder moved); (c) the **prices** those rows set; and (d) whatever **zero-carbon rows**
(biomass, hydro, VRE, storage, nuclear) pick up displaced energy at an **unchanged offer**. No
zero-carbon row's offer may move. No capacity build/retire/retrofit response is expected in 2026
(§2.3), and none is required for a pass.

### 3.3 THE STOP GATE — structural, STOP-only, fixed before the solve

Rule 29: *it may kill an arm; it may never promote one; it is never "did the residual move".*
Nothing below reads a residual, a benchmark, or an actual. Evaluated **per ISO**:

| # | Check | Kills the arm if |
|---|---|---|
| **G1 premise** | `resolve_carbon_price(CARB, 2026) − resolve_carbon_price(REF, 2026)` = **+25.0000** exactly | the resolver does not see the override, i.e. the pair is not the pair |
| **G2 direction — CO2** | in-ISO `emissions_mt` **does not rise**: `CO2(CARB) ≤ CO2(REF)` | CO2 rises under a carbon price |
| **G3 direction — price** | load-weighted price **does not fall**: `p(CARB) ≥ p(REF)` | price falls under a carbon price |
| **G4 magnitude** | `Δp` lies within the ISO's §3.2 predicted band, **or** is reconciled to the measured marginal-fossil mix (`Δp / 25` must land inside the `[min, max]` span of the ISO's own fossil `CO2_RATES`, i.e. `Δp/25 ∈ [0, 1.08]`) | `Δp/25 > 1.08` (above the dirtiest unit in the repo's own rate table — no marginal unit could produce it) or `Δp < 0` |
| **G5 footprint — fossil confinement** | every by-fuel CO2 **decrease** is a fossil class, and `Σ emissions_by_fuel_mt` still equals `emissions_mt` at the scalar's grain | a zero-carbon class books CO2, or the partition breaks |
| **G6 footprint — no offer contamination** | zero-carbon generation classes may change **volume** (they pick up displaced energy) but the *import* line must not book in-ISO CO2: `emissions_by_fuel_mt["import"] == 0.0` in both arms | an import MWh inflates the scored in-ISO total |
| **G7 no non-target load-bearing flip** | the 14 forecast invariants (`check_forecast_invariants`) do not go from 0 FAIL on REF to ≥1 FAIL on CARB for a reason unrelated to carbon | the arm breaks something the carbon price has no business breaking |
| **G8 unserved energy** | `unserved_mwh` does not become non-zero in CARB while zero in REF | a price adder made the system infeasible to serve |

A **G4 band miss that stays inside `[0, 1.08]`** is a **reported miss, not a kill** — the band is
my prediction and the arithmetic bound is the structure; §4 says so in advance, and a band miss
is written up as a miss (§4) rather than quietly re-banded.

### 3.4 Pre-declared LEAKAGE direction and magnitude — PER ISO (the WS-0 duty)

Routed from `FINDING-scn-ws0-2026-09-05.md` §5 item 2. `import_co2_mt_reported` is reported
**beside** `emissions_mt` for every ISO, as a number, in the FINDING — including the zeros.

| ISO | predicted Δ `import_co2_mt_reported` | reasoning, stated before the solve |
|---|---|---|
| **ERCOT** | **exactly 0.0000** | no import node exists (§2.2). A non-zero value would be a defect, not a result. |
| **MISO** | **exactly 0.0000** | no import tranche is built (§2.2). **This zero is a MODEL-BOUNDARY artifact, not a physical claim** — MISO trades heavily with PJM and SPP in reality; the model simply has no seam for it, so MISO's headline CO2 cut carries **no leakage disclosure at all** and must be read as an upper bound on the real reduction. Flagged here so the null is not read as "MISO does not leak". |
| **CAISO** | **≈ 0, and the smallest of the four seam ISOs** — possibly exactly 0.0000 | **CAISO is the one ISO whose imports also pay the carbon.** The CARB border adjustment is `0.428 × resolved price`, so a +$25/t arm makes DSW_CCGT +$9.25, DSW_CT +$13.75 and the unspecified block +$10.70/MWh **more** expensive at the same time as in-state gas (WS-1a §0.3). The zero-EF tranches (PNW hydro, midC, DSW solar) do **not** get dearer, so the substitution should go to **uncarbonized** import — WS-1a measured exactly that at 2026 (+2,228 GWh, all DSW_solar_PV, EF 0). **Predicted: a near-zero import-CO2 delta, and the structural contrast that carries the finding.** |
| **PJM** | **UP, +0.2 to +1.5 Mt** | the two scarcity tranches ($46 / $60 VOM, 4 GW, EF 0.428) pay no border carbon while PJM's coal `mc` rises ~+$24/MWh, so they get relatively cheaper. Bounded above by 4 GW × 8760 h × 0.428 ≈ 15 Mt, but the tranches are priced as scarcity blocks and should clear only in a modest number of hours. |
| **NYISO** | **UP, +0.5 to +2.5 Mt** | six carbon-bearing tranches at $26–$153 VOM, none border-priced, against a fleet whose gas `mc` rises +$9–16/MWh. The two PJM rungs ($32.24 / $40.13) and IESO ($26.36) sit squarely inside that spread. |
| **NEISO** | **UP, ≈ +1.7 to +2.0 Mt** | the reproduction: WS-0 measured **+1.8548 Mt**, all of it on `NYISO_CT_peak` (+4.318 TWh). Same ISO, same year, same arm ⇒ same answer, unless HEAD drifted. |

**The fraction I predict is displaced, per seam ISO** (the number WS-0 asked for): **NEISO ≈ 65 %**
(reproduction), **NYISO ≈ 20–50 %**, **PJM ≈ 5–20 %**, **CAISO ≈ 0 %**, **ERCOT / MISO
undisclosable (no seam)**.

**My honest expectation of where this precommit is most likely wrong:** the CAISO row. It is the
only one that predicts a *null* on a mechanism that produced a two-thirds displacement on NEISO,
and it rests on the border adder being large enough to hold the carbon-bearing rungs out of
merit — which was true at WS-1a's 2026 CAISO prices ($55 load-weighted vs $79/$127/$193 rungs)
but has a thin margin on the DSW_CCGT rung as prices rise. WS-0's own precommit predicted "low
single-digit percent" and measured 16.6 %; **§4 of the FINDING will report every miss in this
section at full magnitude with the reasoning that produced it**, whichever way it goes.

### 3.5 Leg 2 — the T1-F ladder (declared now, run after leg 1 clears)

- **NEISO then ERCOT**, 2026–2030, `market-sim matrix --config
  configs/scenarios/<iso>_scenario_base_2026_2030.yaml --matrix
  docs/handoffs/scn-ws1b/carbon-ladder-cases.yaml --workers 2`. Four cases: `REF` (no override) +
  `CARB-LO/MID/HI` = `carbon_price_delta` 15 / 25 / 50 (§1.1). 5 solve-years per case, inside the
  §2.1b cap; **NEVER both ISOs at once**, and never alongside a PJM/MISO/CAISO leg (rule 12; this
  is a 15 GB / 4-core box).
- Scored with `scripts/report_scenario_deltas.py --reference-case REF` and
  `scripts/collate_scenario_campaign.py` on the two ISOs; invariants I1–I14 per leg; FC-6 P1 on
  the REF/`CARB-MID` pair.
- **Expected, pre-declared:** monotone in the rung — CO2 falls and price rises monotonically from
  REF → LO → MID → HI in each year, and Δ scales roughly linearly in the rung where the marginal
  mix is unchanged (sub-linear where the rung re-orders the stack). **2028–2030 is where a CCS
  retrofit response first becomes possible** (§2.3); at `CARB-HI` (+$50/t) I expect a retrofit
  response on ERCOT before NEISO, since D50/D65's own evidence is that the repaired capex scaling
  closes ERCOT's screen at carbon 0 and NEISO's does not close under RGGI.
- **Honest-unfit line, standing (plan §4):** a deployment delta in either ISO is a delta between
  two runs that share that ISO's live FC-1 defects. **I will not quote a HOLD ISO's 2030 mix as a
  result.**

---

## 4. Budget and what would make me stop

Measured anchors (FF plan §2.4) × arms, 2026 only for leg 1: ERCOT 2.4, NEISO 1.5, PJM 5.6,
MISO 10–13, CAISO 8, NYISO 4 min/solve-year ⇒ **≈ 82 min of LP for the twelve T0 arms**, plus
≈ 55 min once for `data/clean`. Leg 2 ≈ 30 min (NEISO, 4 × 5 yr) + ≈ 48 min (ERCOT) of LP,
`--workers 2` within each ISO. Concurrency: 2 invocations only for ERCOT/NEISO/NYISO; **1**
whenever PJM, MISO or CAISO is solving.

**I stop and report rather than continue if:** any ISO's arm fails G1/G2/G3/G5/G6 (a kill), a
solve OOMs twice at the rule-12 concurrency, or any deliverable would require editing a file
outside this lane's regions (then it is routed to SCN-DESK in the FINDING, per the charter).

**Files this lane may write:** `results/` registrations, this PRECOMMIT and the FINDING,
`docs/handoffs/scn-ws1b/*`, plan §5.1 + ledger §3 Carbon rows, and the six matrix cells (last
commit, one appended line per ISO, after `git fetch origin main` + rebase).
**Files this lane may NOT touch, and will not:** `policy/carbon.py`, `policy/cap_and_trade.py`,
`interchange/spec.py`, `runner.py`, `model/lp/rows.py`, `policy/federal_ces.py`,
`config/scenarios.py`'s `federal_ces_*` block, `configs/scenario_campaign_matrix.yaml`,
`results/export.py`, `results/cache.py`, `scripts/register_forecast_run.py`,
`scripts/report_scenario_deltas.py`, `frontend/data/forecast/program-status.json`.
