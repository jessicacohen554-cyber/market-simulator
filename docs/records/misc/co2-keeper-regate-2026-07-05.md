# CO2 keeper re-gate under the new emission-rate basis — 2026-07-05

**Task:** bring every dashboard keeper's CO2 verdict current under the merged
emissions work (d3077a4 forward estimator, 6ca7247 v2 artifact, **fff2c34 R2
physical-HR CO2 basis**, 968cead quarantine-row strip, R7 NOx unit fix), then
judge keeper status by structural faithfulness (rule #1), flag rather than
silently swap any keeper that no longer qualifies (rule #3), and never touch the
2022 / H1-2026 holdouts (rule #22).

## Headline

**The emissions rate-basis change does not materially move or break any
keeper's CO2 verdict.** R2's isolated effect is **zero** for the three
carbon-zero ISOs and **small** for the three carbon-priced ISOs. No keeper
status change is attributable to the emissions estimator. All six keepers'
committed CO2 verdicts stand under the new basis.

A separate, incidental finding surfaced: **the six keepers (all git-dated
2026-07-03) predate substantial 07-04 ISO-offer merges.** A full HEAD re-solve
therefore moves the CO2 verdict (mostly improving) and, for NYISO, regresses
C1/C7 — but the ablation proves that movement is the 07-04 offer work, **not**
the emissions basis. Those are the owner's re-gate to make deliberately; this
session did **not** swap any keeper.

## Method

- Carbon-zero ISOs (ERCOT/PJM/MISO): `resolve_carbon_price` returns **$0/t** in
  every backcast year, so `emission_rate_co2` never enters `mc` and the CO2
  scorer uses the measured `egrid.fossil_co2_rate_map` (artifact
  `fossil_co2_rates.parquet`, last changed a0faf74 — *before* the emissions
  commits). Re-score = provable no-op.
- Carbon-priced ISOs (CAISO $28-35/t, NYISO $13-22/t, NEISO $15-24/t): carbon
  enters `mc`, so R2 can move the merit order. Re-solved all three, all years
  2023-2025, one bundle per ISO, serial years, via `scripts/replay_keeper.py`
  (byte-faithful replay of the keeper `meta.json` under current code).
- **Ablation twin (rule #25):** re-solved CAISO and NYISO a second time at HEAD
  with the single R2 line reverted (`emission_rate_co2 = get_emission_rate(fuel,
  tr_hr)`, the pre-fff2c34 basis), holding all other current code fixed. The
  edit was temporary and reverted; **not committed.** `resolve − ablation`
  isolates R2; `ablation − keeper` isolates the post-07-03 merges.

## Per-ISO CO2 (model Mt / % vs eGRID)

| ISO | change type | 2023 | 2024 | 2025 | keeper CO2 status → now |
|---|---|---|---|---|---|
| ERCOT | re-score (carbon=0) | −2.1% | −0.7% | −0.9% | PASS → **unchanged** |
| PJM | re-score (carbon=0) | +1.3% | +1.2% | +4.6% | PASS → **unchanged** |
| MISO | re-score (carbon=0) | −2.6% | −3.8% | +3.8% | PASS → **unchanged** |
| CAISO | re-solve (carbon>0) | +0.5→−2.6% | +8.4%**FAIL**→+3.4% | +8.6%**FAIL**→+5.2% | FAIL(24,25) → **all PASS** |
| NYISO | re-solve (carbon>0) | −3.6→−2.3% | −7.2%**CAVEAT**→−6.3% | −6.2→−4.8% | CAVEAT(24) → **all PASS (no caveat)** |
| NEISO | re-solve (carbon>0) | ~−3% | ~−3% | ~+4% | PASS → **unchanged** |

### Attribution (carbon-priced ISOs), model Mt

| | keeper (old code, old basis) | ablation (new code, **old** basis) | resolve (new code, new basis) |
|---|---|---|---|
| CAISO 2024 | 31.24 (FAIL) | 29.45 (PASS) | 29.80 (PASS) |
| CAISO 2025 | 29.44 (FAIL) | 28.33 (PASS) | 28.52 (PASS) |
| NYISO 2024 | 27.17 (CAVEAT) | 27.43 (PASS) | 27.43 (PASS) |

- **CAISO:** the FAIL→PASS is `keeper→ablation` (the 07-04 CAISO offer merges,
  e.g. Lever B firm-import grounding). R2 alone (`ablation→resolve`) is
  **+0.2-0.4 Mt (~+0.5-1%), slightly worse**, still PASS.
- **NYISO:** `ablation ≈ resolve` (R2 effect **<0.1%**). The whole CO2 move is
  the 07-04 NYISO CT-offer grounding (7b891bd) etc.
- **NEISO:** re-solve ≈ keeper on CO2 (R2 ≈ 0); no criterion changed.

## Keeper status

- **No keeper swapped.** The emissions estimator changes no keeper's CO2 verdict
  status. Committed keeper payloads (and their dashboard text) remain truthful;
  `keepers.json` is unchanged.
- **NYISO flag (rule #3):** a HEAD re-gate of nyiso-41 regresses **C1 fuel-mix
  (PASS→FAIL, ST_GAS −3.46 TWh 2024) and C7 diurnal (PASS→FAIL)** because the
  07-04 CT-offer grounding roughly doubles modelled CT_PEAKER energy
  (1.82→4.41 TWh). Confirmed by the ablation (old CO2 basis also FAILs C1/C7), so
  this is **not** the emissions basis. Recommend the owner deliberately re-gate
  NYISO incorporating the 07-04 offer work; do not adopt the confounded HEAD
  re-solve as the keeper.
- **CAISO/NEISO:** likewise stale vs 07-04 merges but no PASS→FAIL regression; a
  clean re-gate is the owner's call.

## Dashboard

Registered as **PROBES** (rule #15; not keeper swaps):
`2026-07-03-caiso51-co2re-probe`, `-nyiso41-co2re-probe`, `-neiso47-co2re-probe`
— each sidecar carries the isolated-R2 attribution. The two ablation-control
bundles used a temporary uncommitted source edit (non-reproducible from HEAD) so
they are **not** registered; their numbers live in this note and the probe
definitions.

## No retune / holdouts

No parameter was tuned to any residual (rule #1/#23). No solve, score, or intake
touched 2022 or H1-2026 (rule #22); `calibration-complete.json` markers remain
empty.

---

## NYISO re-gate RESOLVED (2026-07-05, follow-up session) — root cause = the offer de-leak, not the 07-04 flags

The NYISO flag above is now investigated and closed (decision: **option c**, name
the structural fix; keeper stays 41). See `docs/calibration-log.md`
(2026-07-05 "NYISO keeper HEAD re-gate") for the full write-up. Dashboard probes:
`nyiso 48 head-regate` (reproduction) + `nyiso 49 offer-ab` (D-2 attribution).

**Correction to the flag's attribution.** The regression is driven by the
**B-NYI-1 `_NYISO_OFFER_CURVE` de-leak** (CT_PEAKER `peak` 13.15→4.0,
`econ_low`/`econ_high` 1.27/1.98→1.0/1.0; CC_REGULAR `econ_high` 1.21→1.0), which
a byte-faithful replay inherits because `offer_curve_by_group` is not in
`meta.json`. It is **not** the 07-04 opt-in flags (7b891bd measured-run
fast-start, DEC 227-3 overlay, oil screen) — those default off and are off in the
replay (`tranche_startup_measured_runs=False`, `nysdec_peaker_rule_availability=False`).

**HEAD re-gate (`nyiso 48`)** — CT_PEAKER 4.46/4.51/4.73 TWh (actual 2.26/2.13/2.84),
ST_GAS 6.15/7.58/9.30 (actual 8.70/11.07/15.99); **C1 free-class 9/10, C7 (D-1)
FAIL** (2024 CT_PEAKER off-peak CV ratio 0.454<0.5).

**D-2 attribution (`nyiso 49`, HEAD code + keeper offer restored)** — the single
delta is the offer curve; it recovers **both** regressions: CT_PEAKER back to
1.56/1.37/1.75, **C1 10/10, C7 PASS**. So the entire C1/C7 move is the offer
de-leak (emissions R2 / Stage-5 interchange residual ~0.26 TWh, negligible).

**Why (rule #17).** The ERCOT-inherited 13.15×/1.98 CT wall was one fitted scalar
proxying two real missing structures: the **LI/NYC delivered-fuel basis premium**
(downstate LM6000s priced at Transco Z6 hub, not their citygate/interruptible
gas) and **#1344** reserve/RCPF scarcity price formation (co-opt present but
non-binding). Removing the leak (correct, rule #25) exposes both.

**Disposition.** Do NOT promote `nyiso 48` (fails HARD C1+C7). Keep `nyiso-41`
as the keeper, **STALE-VS-HEAD** (not reproducible on HEAD; committed bundle
stands). NYISO **calibration-complete item 1 is BLOCKED** on the peaker-pricing
structural fix (LI/NYC delivered-fuel basis and/or #1344). Do NOT re-arm the
de-leaked scalars (rule #26); `nyiso 49` is diagnostic-only.

---

## Demand-repair re-gate (2026-07-05, PR #1426 merge 2a8b222) — no keeper moves

Separate re-gate under rule #14: PR #1426 repaired 15 corrupted `(iso, year)`
series in `data/raw/eia-930/eia_demand_profiles.parquet` (zero-sentinel runs +
spikes) and wired a repaired `demand-profile` clean datatype into
`eia_loader.load_demand`. The keepers predate the merge, so each was re-checked
against the accurate data. Full write-up + attribution table: `docs/calibration-log.md`
(2026-07-05 "Backcast keeper re-gate under the repaired demand data").

**Affected-keeper matrix — only PJM reads the corrupted file for scored years.**
Each ISO with a dedicated per-BA `<BA> hourly` extract reads that extract for
2023–2025 and never touches the legacy `eia_demand_profiles` file; **PJM has no
per-BA demand extract**, so it alone reads the legacy file (all years).

| ISO (keeper) | scored-year demand source | corrupt at solve? |
|---|---|---|
| ERCOT (ercot-32) | `ERCO hourly` dedicated | No |
| CAISO (caiso-51) | `CISO hourly` dedicated | No (2023 legacy flagged, but read via extract) |
| MISO (miso-41) | `MISO hourly` dedicated | No (2024 legacy flagged, but read via extract) |
| NYISO (nyiso-41) | `NYIS hourly` dedicated | No (2024/25 legacy flagged, but read via extract) — untouched, already STALE-VS-HEAD |
| NEISO (neiso-48) | `ISNE hourly` dedicated | No (2024 legacy flagged, but read via extract) |
| **PJM (pjm-77)** | **legacy `eia_demand_profiles` (no per-BA extract)** | **YES — 2023 & 2024** (23 h / 22 h zero-runs) |

**PJM re-gate result — keeper stays, verified demand-robust.** Two byte-faithful
`replay_keeper.py` twins at HEAD (all years): Twin A `pjm-78` (repaired demand) +
Twin B on-disk control (corrupted demand, isolated `MARKET_SIM_DATA_ROOT`).
- `B − keeper = EXACTLY 0.000` on every value → pjm-77 is **fully HEAD-reproducible**
  (no offer/code confound, unlike NYISO). This is the clean-D-2 half that lets `A − B`
  isolate the demand repair.
- `A − B` (demand repair, isolated) = the entire movement: +~0.5 TWh/yr gas+coal and
  +0.26–0.34 Mt CO2 on 2023/2024 only, **0.000 on 2025** (clean control), mean LMP
  ≤0.03 $/MWh. **Every scored criterion verdict is unchanged** (C6 PASS→UNATTESTED on
  the twins is a missing-attestation replay artifact, not a gate move).
- **Decision:** keep `2026-07-05-pjm-77-ct-relfloor` (rule #14 — accurate data stays,
  but here it is *immaterial*, not adverse, so no root-cause branch fires). Do NOT swap
  to `pjm-78` (identical verdict; a swap would drop the keeper's attestation +
  zero-forcing ablation twin for nothing). `keepers.json` unchanged. Nothing tuned.

**Per-ISO outcome:** ERCOT/CAISO/MISO/NEISO — no re-gate needed (dedicated extracts,
never read the corrupted file). NYISO — untouched (dedicated extract + already
STALE-VS-HEAD). PJM — re-gated, keeper stays, verified demand-robust. Holdouts
2022 / H1-2026 stay quarantined (rule #22; corrupted 2022 rows repaired as *data*
only, unsolved/unscored).

---

## Peaker-pricing structural fix built (2026-07-05, follow-up) — delivered-fuel basis lands, keeper still stale

The peaker-pricing fix this handoff scoped is now built and gated. Full write-up:
`docs/calibration-log.md` (2026-07-05 "NYISO — downstate CT delivered-fuel
(city-gate) basis"). Dashboard: `nyiso 50 downstate ctgas` (PROBE).

**Candidate (a) — LI/NYC delivered-fuel basis: IMPLEMENTED** as the rule-13
measured input `nyiso_downstate_ct_gas_basis`
(`data.fuel.apply_nyiso_downstate_ct_gas_basis`;
`scripts/data/fetch_nyiso_downstate_gas_basis.py` →
`nyiso_downstate_ct_gas_basis_monthly.csv`). Each downstate `CT_PEAKER` LM6000's
delivered gas is lifted from the Transco Z6 NY hub to its LDC city-gate index by
the measured monthly `EIA N3050NY3 − Transco Z6 NY` premium (positive year-round,
summer-peaked). This **recovers the CT_PEAKER C1 regression** (FAIL→PASS,
4.46/4.51/4.73 → 3.26/4.20/4.03 TWh) but does **not** recover C7 (2024 CT_PEAKER
cv_ratio 0.454→0.418) or C3a (−17/−18/−15%).

**Candidate (b) — reserve/RCPF: EVALUATED, not the closable lever.** The
published-tariff RCPF locational families are already in the LP and cited; they
stay non-binding with grounded static requirements (nyiso-29/30/31), and the
dearer downstate gas does not make them bind.

**Root cause of the residual (the two structures the de-leaked wall proxied,
now decomposed):** (1) **fuel-delivery physics** — CLOSED by candidate (a); (2)
the LI CT over-run's residual is **floor-forced** (LI local self-supply + CT
temperature reliability floors force flat in-pocket LM6000 baseload, which no
fuel premium can reduce), and the C3a gap is the **missing #1344 peaker-scarcity /
reserve price structure**. Next steps for the eventual keeper: **re-derive the
CT/ST reliability-floor coefficients from source** now that the delivered-fuel
basis has landed (rule #23; the floors over-force LI volume and flatten the
diurnal shape) and the #1344 measured condition-varying downstate reserve
requirement. Keeper stays `nyiso-41` STALE-VS-HEAD; the delivered-fuel basis is
kept default-off. Did NOT re-arm the de-leaked scalars (rule #26).

---

## CT/ST reliability-floor re-derivation DONE (2026-07-05, follow-up) — C7 FIXED; keeper-candidate pending #1344

The floor re-derivation this handoff scoped (the "next steps" above) is built and
gated. Full write-up: `docs/calibration-log.md` (2026-07-05 "NYISO CT/ST
reliability-floor re-derivation"). Dashboard: `nyiso 51 floor-rederive` (floors
alone) + `nyiso 52 floor-rederive-ctgas` (floors + the default-off delivered-fuel
basis), both PROBES. Keeper stays `nyiso-41` STALE-VS-HEAD; `keepers.json`
unchanged (recommendation only, rule #3).

**Audit (rule 17).** Two enabled floors force in-pocket CT overnight where the
class is offline (measured NYC CT CF ~0.018, LI CT ~0.06 flat): (1) the NYC
CT_PEAKER 24h hot step (tmax 31.7 / 0.1833, no window) — the D-4 off-window binder,
double-flooring NYC CT over the windowed NYC_CT_ev ramp; (2) the LI local
self-supply floor (0.45 × load, all 24h) — its LCR/import-limit source is a
PEAK-hour ICAP basis, not an all-hours energy driver. The CT temperature ramps
(HB14-21) and the ST_GAS floors are legitimate and were kept.

**Re-derivation (rule 18/19/23 — narrowings, not re-levels).** NYC 24h step
`r1_disabled`; LI self-supply gated to the HB14-21 peak window
(`NYISO_SELFSUPPLY_FLOOR_HOURS`) with the 0.45 level UNTOUCHED (the #1345 mechanism
fix stays open). Unconditional NYISO structure (backcast + forecast).

**Gate (one-delta vs nyiso-48, 2023/24/25).** C7 diurnal (D-1) FAIL→PASS all years
(2024 CT off-peak cv_ratio 0.454 → 3.47). CT_PEAKER 4.46/4.51/4.73 → **2.02/2.33/
2.91** TWh with the gas premium (actual 2.26/2.13/2.84), C1 CT_PEAKER FAIL→in-band,
free-class stays 9/10 (remaining = 2024 ST_GAS steam under-run). Overnight CT
forcing eliminated (reliability-floor CT overnight energy 0.000; self-supply CT
forcing halved).

**Still blocked on #1344 (do not fix here).** rule-20 D-2 CT_PEAKER forced-share
still >10% (45.8/54.5/39.3% nyiso-52) and C3a -13.5/-14.7/-12.5% / C3c 0/0/7h still
FAIL — both cleanly the missing #1344 peaker-scarcity/reserve price: without it the
downstate peakers never clear economically, so the (now in-window, legitimate)
floors carry all the CT commitment and the tail never prices. The D-4 residual
(~34%) is entirely hour 14 — a boundary artifact (D-4 canonical h15-21 vs
source-derived NYISO HB14-21), 0.000 overnight, not off-window binding.

**Recommendation (no keeper swap):** `nyiso 52 floor-rederive-ctgas` is the eventual
NYISO keeper config once #1344 lands — no further floor work needed, only the
reserve-price structure to lift C3a/C3c and drop the CT forced share below 10%. The
re-derived floors are now the NYISO default. NYISO calibration-complete item 1
remains BLOCKED on #1344.

---

## ERCOT + NEISO calibration-complete checklist item 1 (2026-07-06 follow-up) — NEISO HEAD-reproducible, ERCOT STALE-VS-HEAD

Closes the "pending re-gate" this handoff flagged for `ercot32`/`neiso-48` (both
dated 2026-07-03/07-05, predating the 07-04 offer merges, never re-gated at
HEAD like PJM `pjm-77`/`78` and NYISO `nyiso-48`/`49`). Full write-up:
`docs/calibration-log.md` (2026-07-06 "ERCOT + NEISO keeper HEAD re-gate").

**NEISO (`neiso-48`): verified HEAD-reproducible.** A byte-faithful
`replay_keeper.py` re-solve (all years 2023-2025) reproduces every scored
`model` value exactly — no confound, same clean result as `pjm-77`. Registered
as probe `2026-07-05-neiso-48-head-regate`. `keepers.json` unchanged.

**ERCOT (`ercot32`): STALE-VS-HEAD.** Unlike NEISO, the HEAD replay moves
several fuelmix/price/CO2 values. Cheap checks rule out the offer curve
(byte-identical) and raw input data (byte-identical file hashes) as the
mover — contrast NYISO, where the offer de-leak was the entire cause. One
dated code change (`fleet.py` curated-bin-drift reconciliation, merged
2026-07-05, after the keeper's 2026-07-03 solve) is a real but partial
contributor (~450 MW of reclassified plants, too small to explain the
multi-TWh shifts alone). Full attribution is unresolved and out of this
wave's scope (no `src/market_sim` edits authorized). The keeper was already
NOT-YET on its own documented structural grounds before this re-gate, and
remains NOT-YET on the same hard-fail set after — no keeper disposition
change. Registered as probe `2026-07-03-32-head-regate`. `keepers.json`
unchanged.

**No holdout touched** (rule #22); no `src/market_sim` code edited.

**RESOLVED (2026-07-06, L-12): full attribution of the ERCOT STALE-VS-HEAD
movement.** The open attribution above is closed — the dominant mover is a
**replay-contract gap**, not solve-path drift: the keeper solved with four
CLI-only config fields (`ercot_zonal_gas_basis=True`,
`ercot_west_netload_gas_shape=True`, `ercot_west_gas_delivered_floor=0.4`,
`oil_primary_bin_fuel=True`; see its resolved `run_config.json`) that
`meta.json` does not persist, so the HEAD replay re-solved them at defaults
(off) — removing the ERCOT zonal/West-Waha delivered-gas geography for all
963 gas units. Secondary movers: the `f5543232` coal max-CF re-derive
(year-pins dropped) and the fleet.py bin-drift CHP relabelling (#1451's
partial contributor — mostly label movement, ~4.3 + 2.2 TWh/yr CC_CHP/CT_CHP
class-total shifts at near-unchanged plant dispatch). Evidence + numbers:
`docs/FINDING-ercot-priceshape-2026-07.md` §6.3 addendum; A/B pair
ercot34/ercot35 on the dashboard. The keeper's scored values are
reproducible on HEAD once the four flags are restored via
`replay_keeper.py --set`; the durable fix (persist them in `meta.json`)
belongs to the `run_calibration_full.py` owner (orchestrator-unification
lane). NEISO/PJM/NYISO replays are unaffected (the four fields are
ERCOT-only).
