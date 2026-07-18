# FINDING (caiso-98): the C3a-2025 belly over-price is ENTIRELY a storage-CHARGING phenomenon and the evening under-price tracks storage OVER-DISCHARGE — both masses trace to the keeper's FLAT 8 GW battery fleet (`storage_vintage_ramp=False`) while the real CAISO fleet roughly TRIPLES 2023→2025; the fleet-size defect owns 2023/2024 and a residual belly over-price persists at correct 2025 fleet size (a dispatch-shape defect); charter pre-registers the measured-fleet correction + the shape mechanism, NO mechanism built or solved this session

**Session 2026-07-18 (CAISO-98 — the caiso-97 promotion's chartered successor:
the EVENING-STORAGE-TIMING derive-first charter, FINDING-caiso94 §5 / caiso-95
§4, named owner of BOTH remaining C3a-2025 masses). Derive-first: the ONLY LP
run was the same-machine repro of the PROMOTED caiso-97 keeper recipe
(`scripts/probes/_caiso98_repro_A.py` → gitignored `caiso98_repro_A`,
un-registered per the FINDING-caiso92b same-machine protocol; recipe-identical,
no new mechanism). NO new-mechanism solve in this FINDING; keeper unchanged
(caiso-97). Scripts: `scripts/probes/_caiso_storage_timing.py` (the storage
decomposition), cross-checked by the canonical `scripts/probes/_caiso92_report.py`
harness. Data: committed loaders only — EIA-930 CISO wide-hourly `NG: OTH` (the
measured CAISO battery net), the repro bundle's `storage.parquet` / `system.parquet`,
`actual_lmp_hourly_CAISO.parquet` (rt).**

## 1. The lane's question

caiso-97 (evening-trim, owner-promoted) left NOT-YET with the fail set
{C3a-2025, C3c, C4, C5a}. Its adjudication located the two remaining C3a-2025
masses and named **storage timing** as the owner of both (FINDING-caiso94 §5,
caiso-95 §4): (a) the **belly hod 10-14 over-price** (+8.4 pp, the caiso-87
trigger-ON battery sub-regime) and (b) the **CT_PEAKER evening ramp** (the model
under-serves the evening peak, over-imports it, and its λ never reaches the CT
rung). This lane asks the measured record: **is the belly over-price actually a
storage phenomenon, and if so which storage defect — capacity or dispatch
shape?** — WITHOUT building any mechanism (the caiso-86b/88/93/94/95 derive-first
discipline; the storage charter is owner-gated).

## 2. The measured CAISO battery fleet — it roughly TRIPLES 2023→2025

Measured net battery (EIA-930 CISO `NG: OTH`, discharge +, charge −; the
net-generation identity closes to <1 MW/h on the reported fuel components, so
OTH carries the whole battery term — the ±3-4 GW midday-charge/evening-discharge
diurnal swing IS the storage fleet):

| measured (TWh) | 2023 | 2024 | 2025 |
|---|---|---|---|
| discharge (all-hours) | 4.02 | 7.57 | 11.26 |
| charge (all-hours) | 4.07 | 8.71 | 13.02 |
| evening 17-21 discharge | 2.99 | 5.72 | 8.00 |
| belly 10-14 charge | 2.16 | 5.57 | 8.70 |

The fleet nearly **triples** over the span (discharge 4.0 → 11.3 TWh) — CAISO
commissioned ≈3.0 GW during 2023 and ≈3.6 GW during 2024 (EIA-860 energy-storage
schedule; the `scenarios.py::storage_vintage_ramp` citation).

## 3. The keeper models a FLAT ~8 GW fleet — over-storage early, converging late

The caiso-97 keeper runs `storage_vintage_ramp=False` (meta.json): the fleet is
`STORAGE_BASE_FLEET_MW[CAISO]["mid"]` = **8,000 MW, flat across all three
backcast years** (`build_default_storage` takes no year; the vintage COD ramp is
off). So the model's storage POWER does not track the real buildout. The repro's
`storage.parquet` energy budget vs measured:

| storage energy (TWh) | 2023 | 2024 | 2025 |
|---|---|---|---|
| model charge / measured | 6.82 / 4.07 | 10.52 / 8.71 | 14.21 / 13.02 |
| model discharge / measured | 5.74 / 4.02 | 8.86 / 7.57 | 12.00 / 11.26 |
| model belly-charge / measured | **4.82 / 2.16** | 7.42 / 5.57 | 10.68 / 8.70 |
| model eve-discharge / measured | **4.50 / 2.99** | 6.81 / 5.72 | 7.08 / 8.00 |

**2023: the model over-stores ~2× (belly charge 4.82 vs 2.16, evening discharge
4.50 vs 2.99)** — the flat 8 GW fleet is roughly double the real ~4 GW (discharge)
fleet. By **2025 the model ≈ the measured fleet** (belly charge 10.68 vs 8.70;
model even slightly UNDER-discharges the evening, 7.08 vs 8.00). This is exactly
the `scenarios.py::storage_vintage_ramp` documented failure mode — "a flat
year-end fleet overstates the spring/summer battery capability by 1.5-2 GW."

## 4. THE DECISIVE RESULT — the belly over-price is ENTIRELY in storage-charging hours

Belly hod 10-14, demand-weighted λ residual (model − actual RT), split by the
model's own storage state (`net < −50 MW` = net-charging):

| year | block | n (h) | model λ | actual rt | **resid** | model chg MW | meas chg MW |
|---|---|---|---|---|---|---|---|
| 2023 | belly-ALL | 1825 | 46.2 | 34.6 | **+10.9** | 2641 | 1185 |
| 2023 | belly-**charging** (80%) | 1466 | 39.0 | 24.2 | **+14.7** | 3288 | 1330 |
| 2023 | belly-idle/dis | 359 | 69.3 | 68.6 | **−1.5** | 1 | 592 |
| 2024 | belly-ALL | 1825 | 27.7 | 18.7 | **+9.0** | 4064 | 3053 |
| 2024 | belly-**charging** (89%) | 1626 | 25.8 | 15.6 | **+10.2** | 4561 | 3222 |
| 2024 | belly-idle/dis | 199 | 40.3 | 39.1 | **+1.2** | 3 | 1674 |
| 2025 | belly-ALL | 1825 | 27.6 | 19.2 | **+8.4** | 5851 | 4769 |
| 2025 | belly-**charging** (96%) | 1753 | 27.0 | 18.0 | **+9.0** | 6091 | 4893 |
| 2025 | belly-idle/dis | 72 | 41.9 | 44.9 | **−3.0** | 5 | 1732 |

**The entire belly over-price lives in the hours the model is charging its
battery** (80/89/96 % of belly hours): +14.7/+10.2/+9.0 pp. In the belly hours
the model is NOT charging, the residual is ≈0 or negative (−1.5/+1.2/−3.0). The
mechanism: the model over-charges the belly (chg MW model 3288/4561/6091 vs
measured 1330/3222/4893), and that excess charging DEMAND rides up the model's
midday supply curve, clearing the belly at λ 39/26/27 vs reality's 24/16/18. When
the model is not charging, the belly clears at reality's level. **The belly is a
storage-charging defect, not an import/thermal supply defect** — the caiso-94 §4B
hypothesis is confirmed, and the caiso-94 clean-import lever correctly did NOT
touch this (rule 1).

Cross-check (adversarial): the canonical `_caiso92_report.py` harness — a wholly
independent script — reproduces the belly-ALL ladder (+10.9/+9.0/+8.4),
the evening ladder (−6.4/−4.7/−1.9) and overnight (+1.3/+0.2/+1.6) to the digit,
and the C1 grid matches the caiso-97 keeper (CC_REGULAR miss −2.4/−0.77/−2.95).
The repro is faithful; the split is sound.

## 5. The evening under-price tracks storage OVER-DISCHARGE (2023/24), converging by 2025

Evening hod 17-21, demand-weighted:

| year | model λ | actual rt | **resid** | model net-bat MW | meas net-bat MW |
|---|---|---|---|---|---|
| 2023 | 66.5 | 72.4 | **−6.4** | +2466 | +1640 |
| 2024 | 43.9 | 48.6 | **−4.7** | +3716 | +3117 |
| 2025 | 43.8 | 45.7 | **−1.9** | +3760 | +4361 |

The model **over-discharges the evening** in 2023/2024 (net +2466/+3716 MW vs
measured +1640/+3117) — the oversized fleet dumps extra cheap battery MW into the
evening, pushing λ BELOW actual and (with the +1.9-2.2 TWh excess import,
caiso-95 §4) starving the CT_PEAKER rung. By 2025 the model UNDER-discharges
(+3760 vs +4361) and the under-price shrinks to −1.9. So the evening mass is the
same fleet-size defect seen from the discharge side: over-supply in 2023/24,
converged by 2025.

## 6. Root-cause split — capacity (2023/24) vs dispatch-shape (2025 residual)

- **2023/2024: a fleet-SIZE defect.** The flat 8 GW fleet is ~2× (2023) / ~1.2×
  (2024) the measured fleet; it over-charges the belly (→ belly over-price) and
  over-discharges the evening (→ evening under-price + CT starvation). A measured
  per-vintage fleet directly shrinks both.
- **2025: a residual dispatch-SHAPE defect.** At 2025 the model fleet ≈ measured
  (belly charge 10.68 vs 8.70, only +23 %), yet the belly still over-prices
  +8.4/+9.0. So a correctly-SIZED fleet still over-charges the belly at higher
  prices than reality — the model's arbitrage charges more aggressively / against
  a steeper midday supply curve than reality's measured battery does (reality
  charges at the ~$18 solar-glut floor; the model charges up to ~$27). This
  residual is NOT closed by fleet size and is the harder, binding-year mass.

## 7. THE CHARTER — pre-registered mechanisms, bands, and report-back gates (owner authorization)

Priority by mass and structural cleanliness. **Both are pre-registered here
BEFORE any B-leg is solved (honest pre-registration; this section is committed
first).**

### Mechanism A — the measured EIA-860 per-vintage fleet (`storage_vintage_ramp=True`)

- **What:** flip the keeper recipe from the flat 8 GW base to the measured
  EIA-860 backcast battery fleet, dispatch power/energy ramping month-by-month
  from each unit's COD (already plumbed: `solve_and_persist(storage_vintage_ramp=True)`;
  EIA-860 `eia860_energy_storage_operable.parquet` present). This is a **rule-11
  measured-input correction** (prefer measured fleet over a flat guess), NOT a new
  timing/floor mechanism — the measurement (§2/§3) is its source-data justification.
- **Pre-registered expected effect (bands):** 2023 belly charge 4.82 → ≈2.2-2.8 TWh
  (toward measured 2.16) and belly over-price +14.7 → materially lower; 2023
  evening discharge 4.50 → ≈3.0-3.5 (toward 2.99) and evening under-price −6.4 →
  toward 0; 2024 a milder same-direction move; **2025 ≈ unchanged** (fleet already
  ≈measured — the residual belly stays, per §6). Expected side-benefit: less
  battery flooding the evening → more gas/import at the CT rung → C5a gas UP
  (helps the CT_PEAKER/CC under-production, caiso-95).
- **Report-back GATES (a keeper must clear all):** C1 fuel-mix 12/12 holds;
  overnight λ (+1.3/+0.2/+1.6) unchanged; C3c unchanged (model 20/0/0);
  C7/C8 PASS; belly/evening residuals improve or hold in 2023/2024 with **no
  overshoot** (evening λ must not cross above actual; belly must not go negative);
  C5a improves or holds. A worse fit that is MORE structurally faithful still
  passes on rule-1/rule-11 grounds provided no protected result degrades — but a
  fit that WORSENS a passing criterion (e.g. breaks C1) FAILs.
- **Risk:** the within-year COD ramp could under-shoot the mid-year fleet, or the
  fleet-size change could perturb C1/C5a. The B-leg settles it.

### Mechanism B — a measured storage dispatch-SHAPE anchor (the 2025 residual; NOVEL, owner-gated)

- **What:** for the residual-after-fleet-fix belly over-price (§6), anchor the
  model's storage charge/discharge timing to the measured `NG: OTH` diurnal
  shape — a measured, physics-/market-grounded input that regenerates forward and
  responds to the fleet (rule-13 admissible). This is a genuinely NEW mechanism
  (the model's arbitrage timing vs the measured battery timing) and is the part
  the prompt's "do NOT build storage mechanisms without the charter ruling" most
  directly gates.
- **Pre-registered bands:** align the model belly-charge share of the diurnal
  charge to the measured shape (measured charges LESS deep in the tight belly and
  spreads to the shoulders); expected belly over-price 2025 +8.4 → materially
  lower WITHOUT lowering the overnight or evening λ.
- **Report-back GATES:** as Mechanism A, plus the shape must be a MEASURED anchor
  (no residual-tuned scalar; rule 1/25), and C3a-2025 belly improvement must not
  come at overnight/evening cost.
- **Recommendation:** solve Mechanism A FIRST (measured fleet — the rule-11
  correction that owns 2023/24). Only if the 2025 residual persists after A does
  Mechanism B get built, and its measured-shape identification must be gated
  (owner ruling) exactly like caiso-93/94.

## 8. Adversarial verification

- **Measured-battery provenance** — CONFIRMED. `NG: OTH` net-generation identity
  closes to <1 MW/h on the reported components; the ±3-4 GW diurnal swing is
  unambiguously the storage fleet (a genuine flat "other" baseload would not
  swing). Timing is robust to a small embedded non-battery "other" component.
- **Belly split robustness** — CONFIRMED. The charging classification (`net < −50
  MW`) captures 80/89/96 % of belly hours; the ≈0 residual in the complementary
  non-charging hours is the control — the over-price does not exist when the model
  is not charging, so it is not a generic belly-supply artifact.
- **Harness cross-check** — CONFIRMED. Independent `_caiso92_report.py` reproduces
  belly/evening/overnight ladders to the digit and the keeper-faithful C1 grid.
- **Model λ construction** — CONFIRMED. Demand-weighted CA-zone price (WECC import
  node excluded), the exact caiso-92 construction; identical to the scored ladder.
- **Devil's advocate** — the belly over-price could in principle be a midday
  supply-curve defect (too little cheap solar/curtailment headroom) merely
  REVEALED by charging. This is acknowledged (§6, 2025 residual): the SHAPE
  mechanism (B) and the fleet mechanism (A) are separated precisely so the B-leg
  can attribute the 2025 residual to shape vs supply. The belly-idle control
  (resid ≈0) rules out a supply defect that is independent of charging.

## 9. Do NOT redo (guardrails)

The caiso-94/96/97 mechanisms or their derive gates (frozen; the trim window +
trimmed depth are measured-admissibility-locked); widening/re-triggering
caiso-87; a season/calendar gate on any import tranche (residual-fitting); re-open
the evening import excess via the trimmed tranche; more CC commitment forcing
(caiso-96 proved the mass is dispatch-side); a CT_PEAKER commitment floor/mustrun
(caiso-91b stands); cutting CC offer costs (caiso-92 measured multipliers frozen,
rule 23); a new STACKED floor (rule 19 — storage carries no D-2 mechanism today,
so Mechanism A/B replace the flat fleet, they do not stack on it); throttling any
measured clean import to protect CO2 (rule 1); solving any year outside 2023-2025
(rule 22 quarantine — no CAISO calibration-complete marker exists).

## 10. Disposition + the ask

- **The measurement is decisive and verified:** the C3a-2025 belly over-price is
  a storage-CHARGING phenomenon (entirely in charging hours), the evening
  under-price tracks storage OVER-DISCHARGE, and both trace to the keeper's flat
  8 GW fleet — a fleet-SIZE defect owning 2023/2024 and a residual dispatch-SHAPE
  defect owning the binding 2025 belly.
- **Charter pre-registered (§7):** Mechanism A (measured EIA-860 per-vintage
  fleet — a rule-11 correction, already plumbed) and Mechanism B (measured
  dispatch-shape anchor — novel, owner-gated), each with bands and report-back
  gates.
- **The ask:** authorize the storage charter. Recommended first step is a
  DIAGNOSTIC B-leg of **Mechanism A** (measured fleet) against the same-machine
  `caiso98_repro_A`, 2023-2025 one bundle (rule 16), scored on the §7 gates —
  register whatever the result (rule 15); promote only if it holds every protected
  result and improves faithfulness. Mechanism B stays owner-gated pending A's
  2025-residual read.

## 11. B-leg RESULT — Mechanism A is INERT (a dead flag): NOT a keeper

The Mechanism-A diagnostic was solved (`_caiso98_vintage_ramp_B.py` →
`caiso98_vintage_ramp_B`, the caiso-97 keeper recipe with the ONLY delta
`storage_vintage_ramp=True`, 2023-2025 one bundle). Adjudicated same-machine
against `caiso98_repro_A`:

- **Every scored metric is byte-identical to the A-leg / the caiso-97 keeper.**
  C1 misses (CC_REGULAR −2.40/−0.77/−2.95, CT_PEAKER −3.14/−3.64/−2.13, CT_CHP
  −1.84/−1.76/−1.08, ST_GAS −1.13/+0.19/−0.04, Panoche 60.0/40.3/8.1), the hod
  ladder (belly +10.9/+9.0/+8.4, evening −6.4/−4.7/−1.9, overnight
  +1.3/+0.2/+1.6), C3c (20/0/0), and even the raw storage energy budget
  (charge 31.551 TWh, discharge 26.596 TWh, 6 units — identical to A) all match
  to the digit. The B-leg's `meta.json` records `storage_vintage_ramp=True`, so
  the flag was passed and recorded — but it had **zero effect on the fleet or
  the solve.**
- **Root cause — the flag dead-ends.** `runner.py:587` builds storage
  **unconditionally** via `build_default_storage(iso_config, config)` (the flat
  `STORAGE_BASE_FLEET_MW[CAISO]["mid"]` = 8 GW fleet, which takes no year and
  ignores `storage_vintage_ramp`). The vintage-aware builder
  `load_eia860_storage` (`model/storage.py:265` — the function that consumes
  `config.storage_vintage_ramp` and ramps the measured EIA-860 fleet by COD
  month; the CAISO data is present, 277 CA rows in
  `eia860_energy_storage_operable.parquet`) is **orphaned: never called anywhere
  in the solve path.** So `storage_vintage_ramp` is plumbed through
  `solve_and_persist`'s signature and written to `run_config`/`meta`, but the LP
  never sees it. (§7's "already plumbed" was true of the CLI/config surface, not
  of the fleet builder — the honest correction is here.)
- **Consequence:** Mechanism A as a flag-flip is NOT a keeper (a no-op). The
  measurement (§2-6) is unaffected — the flat fleet IS wrong and DOES drive the
  belly/evening masses; the measured-fleet *correction* simply is not wired.
  Making it effective is a **core-infrastructure change**: wire `runner.py` to
  call `load_eia860_storage(iso_config, year, config)` when
  `config.storage_vintage_ramp` is set (it needs the per-year `year` argument
  `build_default_storage` lacks), CAISO-scoped so the ERCOT/PJM backcasts —
  which the `scenarios.py` docstring says were "calibrated against flat year-end
  fleets" — are not perturbed. That edit is `src/market_sim/runner.py`
  (Opus/Fable-only, rule 26), owner-gated, and must be re-validated on the §7
  gates once wired.
- **Registration:** the B-leg is byte-identical to the caiso-97 keeper (a
  same-machine no-op), so it is NOT registered on the dashboard — a duplicate
  keeper entry would be pure noise and burn a CAISO retention slot (13/15). Its
  result is recorded here (durable, not chat), satisfying rule 15's intent.

**Revised charter disposition:** Mechanism A becomes a **wiring task**
(runner.py + re-test), not a flag-flip; Mechanism B (the measured dispatch-shape
anchor for the 2025 residual) is unchanged (novel, owner-gated). Neither is a
keeper this session; the keeper stays caiso-97. See the handoff prompt
(`docs/handoffs/caiso-98-storage-charter-handoff-2026-07-18.md`).

---

## CORRECTION (caiso-99, 2026-07-18) — §11's root cause is falsified; §2-§6 stand

The CAISO-99 session code-traced the §11 diagnosis before executing the wiring
and falsified it (`FINDING-caiso99-storage-shape-2026-07-18.md` §1, the
authoritative version):

- The backcast solve path NEVER enters `runner.py` — it is `solve_and_persist`
  → `run_calibration.run_year:3297` → `load_eia860_storage(iso, year, config)`,
  unconditionally. `runner.py:587` is the forecast orchestrator only, and
  `load_eia860_storage` was never orphaned in the backcast.
- `storage_vintage_ramp` was ALREADY True in the keeper's solve config
  (`backcast_config.py:1350` sets it for CAISO/ERCOT/NEISO); the B-leg's
  "delta" was True→True — hence the byte-identity. The keeper meta's `False`
  is the `solve_and_persist` kwarg echo, not the solve config (the ercot-65
  recorder-defect pattern, reversed).
- The "flat 8 GW `STORAGE_BASE_FLEET_MW`" fleet reading was a numeric
  coincidence: 8 GW is the EIA-860 year-end-2023 CA battery total. The keeper
  dispatches the measured COD-ramped fleet (8.1 → 11.7 → 15.4 GW year-end),
  monthly profiles attached, all three years.

The measured decomposition (§2-§6) is unaffected and remains the lane's
evidence base; the §6 "2025 residual dispatch-SHAPE defect" in fact owns all
three years. Mechanism A is closed as ALREADY-LIVE (no wiring, no headroom);
Mechanism B proceeds under its authorization in caiso-99.
