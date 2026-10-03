# Third-Party Audit — Market Simulator (2026-10, AUDIT-B)

**STATUS: RECORD** — written 2026-10-03 at `origin/main` @ `d7ff7c20113fc724f7b681b7b4f0ffa774d775ef`.
Successor to `docs/audit/third-party-audit-2026-08.md` (2026-08-15 @ `9f48419`).

**Auditor stance.** Independent assessment; the auditor did not build this model
and has no stake in it being good. Scorer-only on committed artifacts: no LP was
solved, no keeper moved, no rubric band changed. Every per-ISO determination
quoted here was computed in-session by
`scripts/calibration_verdict.py::iso_determination` (the same function the
Calibration Status page runs) from the committed keeper bundles under
`results/calibration/`. Comparator claims draw on public documentation of the
named tools; anything the auditor could not confirm is marked *unverified*.

**Method.** Five parallel read-only lanes, each a standalone record under
`docs/audit/2026-10/`:

| Lane | File | Scope |
|---|---|---|
| A | `A-lp-dispatch-commitment.md` | LP formulation, pricing, commitment bridges, storage, transmission, reserves, solver |
| B | `B-capacity-policy-forecast.md` | capacity evolution, policy layer, forecast-uncertainty layer, forecast program |
| C | `C-data-calibration-governance.md` | data contract, calibration evidence, governance regime, delta vs 2026-08 gap register |
| D1/D2 | `D1-site-drift-concept-pages.md`, `D2-site-drift-calibration-pages.md` | codebase-site HTML drift found and corrected |
| E | `E-model-positioning-matrix.md` | comparator positioning matrix refresh (PLEXOS, Aurora, EnCompass, GenX, PyPSA-USA, Switch, ReEDS, IPM, NEMS, RESOLVE, Dispa-SET, Sienna) |

The public summary is the site page `docs/codebase-site/model-audit.html`.

---

## 1. Executive summary

1. **What it is.** A nine-region (ERCOT, CAISO, PJM, MISO, NYISO, NEISO, SPP,
   NWPP, SOCO), full-8760, zonal, pure-LP dispatch simulator (224 modules,
   ≈198k lines (wc -l) under `src/market_sim/`) whose prices are LP duals, with two
   passes per year (P0 base-cost → P1 bid-cost), three ISO-exclusive P1-native
   commitment bridges instead of MIP unit commitment, renewables as bounded
   decision variables, in-LP reserves with ORDC/RCPF scarcity structure, and a
   myopic one-pass annual capacity-evolution wrapper over 2026–2050. Three
   regions (SPP, NWPP, SOCO) were added since the 2026-08 audit.
2. **The governance regime remains the model's most distinctive asset**, and it
   has grown: 36 stable-ID rules (30 in August), a sharded solve regime
   (rules 32–36: one year per container, no cross-year state, parent composes
   and promotes in one command), a solve-surface fingerprint in the cache key,
   a per-ISO mechanism-matrix ledger, DOF ledgers on every keeper and a
   promotion script that refuses to shrink the year set.
3. **The out-of-sample claim was withdrawn, not strengthened.** The three-tier
   holdout regime was removed on 2026-09-09 by owner instruction (rule 22,
   rule-history §18; `calibration-complete.json` now opens "AUTHORIZES
   NOTHING"). Every year 2019–2025 may be solved, scored and registered; no
   year is a certified out-of-sample number. In August this model was stricter
   than any surveyed comparator on holdout discipline; today it is an
   in-sample calibration with unusually transparent accounting. The
   compensating move, v3.13 (2026-09-30), makes every registered year gate the
   ISO headline, worst-of.
4. **Under that rule, two of nine ISOs read CALIBRATED at HEAD: NEISO
   (2019–2025) and NYISO (2021–2025).** The other seven are NOT-YET, every one
   on a 2019–2021 fuel-mix or dispatch-correlation rung and/or a 2022–2025
   price-level or price-shape rung (§3 table). In August PJM was the sole
   CALIBRATED ISO; its W0 keeper now fails fuelmix 2019–2021 and
   price_mean/price_shape 2022 and 2025. The dashboard computes this
   correctly; prose in several keeper shards (SPP most visibly) still describes
   the superseded "2023–2025 designated span, earlier years reported not
   gating" posture. That drift is recorded, not repaired, here (the keeper
   shards are a lane's own surface).
5. **Every keeper was re-promoted on 2026-10-02 under the W0 EIA-860
   settlement** (`docs/backcast-closeout-plan-2026-10.md` §2.1), which replaced
   per-lane fleet censuses with owner-filed EIA-860 vintages. This is the
   right structural move under rules 13/14 and it is the proximate reason the
   2019–2021 fuel-mix rungs regressed: the fleet is now what was actually
   there, and the merit order no longer absorbs the difference.
6. **Where it sits.** Closest in class to a production-cost model (PLEXOS,
   Aurora, EnCompass ST) with a light long-term wrapper; not a capacity-expansion
   model (ReEDS, GenX, IPM, NEMS) and not a nodal market clone (SCED/SCUC). Its
   distinguishing choices are pure LP (no MIP commitment), duals-as-prices with
   explicit scarcity structure, and a published, machine-scored hindcast
   against actuals that no surveyed comparator matches in transparency. Its
   distinguishing gaps are nodal transmission, MIP commitment, intertemporal
   capacity optimisation and transmission expansion.

**Addendum 2026-10-03 (post-SHA).** `main` re-keyed the SPP keeper to
`2026-10-02-w0-spp107r` (identity re-key by `promote_keeper.py`) after the
audit SHA. Recomputed with `iso_determination`: still NOT-YET, now also
failing price_mean 2024 and price_shape 2024 beside the gates listed in §1.4.
The site page carries the updated row; the lane reports stand at `d7ff7c20`.

**Addendum 2 (2026-10-03, rulings).** Recomputed on `main` after the merge of
rubric v3.18/v3.19 (owner rulings R-34, R-40) and the NWPP re-promotion to
`2026-10-03-nwpp-next-22b-w0`: NEISO and NYISO CALIBRATED, seven NOT-YET.
CAISO's price_mean 2021 fail is now a v3.19 reference-coverage caveat; its
dispatch_corr and fuelmix 2019–2021 rungs still fail. NWPP's new keeper
fails dispatch_corr 2019/2023/2024, fuelmix 2019/2024/2025 and price 2023–2024.
Owner rulings on this audit: holdout stays removed (claims are in-sample);
rule 37 `[R-RUBRIC-FREEZE]` freezes the rubric between promotions; the
posture family is documented in spec §1.6 and CLAUDE.md; the attestation
schema, env-knob recording, forecast-board rows and completeness rows are
delivered (`docs/audit/2026-10/G1`–`G6`).

## 2. Lane findings (ranked)

### 2.1 LP, dispatch and commitment (lane A)

- **A1 — An undocumented fourth commitment mechanism.** `model/lp/rows.py::_build_posture_energy_rows`
  adds continuous commitment-state and start-up pool columns with min-load,
  start-counting and min-up/down rows, a clustered-UC LP relaxation gated by
  `ScenarioConfig.spp_commitment_posture` (`config/scenarios.py:9457`, default
  off). It carries its mechanism-matrix row (`mechanism-matrix.js` id
  `spp_commitment_posture`, rule 28 satisfied; the lane's "zero mentions"
  reading was corrected at composition) but appears in neither the spec,
  `CLAUDE.md` nor `docs/codebase/`, which present the three bridges as the
  complete set. Rule 19 asks that it be enumerated beside them. Engineering.
- **A2 — Relaxed-LP price formation is the largest structural divergence from
  production-cost and ISO practice.** No binaries, no uplift, no convex-hull
  pricing; the rule-1 band multipliers partly absorb the gap. This is a known,
  owner-ruled design choice (CLAUDE.md "Dispatch and commitment"); the audit
  records it as the single biggest reason the 2022–2025 price-shape rungs are
  the open front. Owner decision, unchanged since August.
- **A3 — Spec/code mismatch on ramping.** Spec §1.9 says "no inter-hour
  generator ramp-rate constraints"; `rows.py::_build_ramp_rows` exists
  (default off). Fix the spec sentence to "default off". Engineering.
- **A4 — Stale code reference.** `docs/codebase/02-lp-dispatch.md` and `03-…`
  still cite a ~2,400-line `dispatch.py` with `DispatchModel` at lines
  1653–2149 (now a 34-line facade; class at `model/lp/model.py:68`) and
  describe a three-pass P0→P1→P2 production sequence. Engineering (`/sync-docs`).
- **A5 — Env-var solve knobs.** `MARKET_SIM_HIGHS_LEAN` and
  `MARKET_SIM_WARMSTART` can change which degenerate dual HiGHS returns and are
  not part of the solve-surface fingerprint as far as the lane could verify.
  Rule 24 tension; either fingerprint them or document why they are inert.
  Engineering.
- Verified clean: no Python loops over hours in the LP builders, no magic
  numbers found in the builders, renewables are bounded variables, prices are
  duals, storage ε tiebreaker present, full 8760.

### 2.2 Capacity evolution, policy and forecast (lane B)

- **B1 — Investment is myopic one-pass on prior-year prices**
  (`model/capacity_evolution/new_entry.py:616`), no foresight. Structurally
  below every capacity-expansion comparator (ReEDS, GenX, IPM, NEMS, RESOLVE)
  and the spec itself calls it a screening model (spec line ~909). This is rule
  10 by design; the audit's point is that forward numbers from it are
  equilibrium-free and must be labelled so. Owner decision.
- **B2 — No transmission expansion.** Only a default-off committed-project
  registry (`config/scenarios.py:2690`, `data/transmission_expansion.py`);
  TTCs are static to 2050. Every comparator in the CEM class builds
  transmission. Owner decision.
- **B3 — The forecast program is at T1 (proof-of-concept) for every ISO**, no
  full-solve authorisation, FC-1 fails for all but NYISO, and the ERCOT reserve
  margin reads −1.5 % by 2030 in `program-status.json` (2026-09-06). No forward
  number is quotable. The gate-(a) board is stale against the 2026-10-02
  keepers. Engineering (refresh the board), owner (authorise or not).
- **B4 — Stale code reference.** `docs/codebase/03-capacity-and-commitment.md:8-48`
  has the retire-before-CCS order, says fossil filed dates are a no-op, and
  cites `capacity.py:1412` (now a 32-line shim); code runs CCS→retire and
  honours fossil dates by default (`evolve.py:556,687,804`;
  `scenarios.py:5303`). Engineering (`/sync-docs`).
- **B5 — Since August** the fossil filed-date channel, CO2-scaled CCS capex,
  the PJM clearing / adequacy / accreditation-vintage arms and the PJM/MISO
  sector gate were armed on ≤ 5-year A/B comparisons; nothing has been
  exercised at the 25-year horizon and the uncertainty band (PB-5) is still
  unproduced. Risk, not a defect.

### 2.3 Data, calibration evidence and governance (lane C)

- **C1 — No ISO has out-of-sample evidence.** The holdout regime was removed
  2026-09-09 and zero locked-test years were ever spent before that, so the
  program has never produced a certified out-of-sample number.
  `docs/calibration-and-validation-methodology.md` still says
  "holdout-tested" (drift). Owner decision (restore a protected year or label
  every claim in-sample); engineering (fix the methodology doc).
- **C2 — Two of nine ISOs CALIBRATED (NEISO 2019–2025, NYISO 2021–2025)**
  versus one of six in August; PJM was demoted by the v3.13 worst-of extension
  to every registered year. Every NOT-YET ISO passes its 2023–2025 rungs except
  ERCOT (price_mean 2024) and NWPP (price 2023–2024); the misses are 2019–2022
  fuel-mix and price. The lane read `status/<ISO>.js`; the auditor recomputed
  the same values with `iso_determination` (§1.4 table on the site page).
- **C3 — Rubric amendments v3.10 → v3.17 landed in five days**, each admitting
  a named failing cell to the caveat ledger. The scores did not move; what is
  ledgerable did. This is the self-certification pattern the August audit
  warned about (gap O5) and it is now the main threat to the rubric's
  credibility. Owner decision: freeze the rubric between promotions.
- **C4 — Attestation schema is not fixed.** Bundles carry lane-named blocks
  (`miso267`, `neiso109`, `spp85`, …) and `authorized_price_tuning` appears
  only in NYISO's attestation. The rule-21 DOF ledger is present in every
  bundle as `calibration_attestation.json::free_parameters` (the lane's
  "no `dof_ledger.json`" reading was a file-name expectation, corrected here),
  but its shape differs by lane. Engineering: one schema, validated in
  `audit_keepers.py`.
- **C5 — Keeper-only retention (rule 15) erased the public rejected-run
  registry** the August audit singled out as unmatched by any comparator;
  rejections now survive only as records and mechanism-matrix cells. The O4
  CAMPD outage seam (14–37 %) remains open with no freeze attached.

## 3. Delta since the 2026-08 audit

| Then (2026-08-15 @ `9f48419`) | Now (2026-10-03 @ `d7ff7c20`) |
|---|---|
| 6 ISOs; 30 rules | 9 regions (SPP, NWPP, SOCO added); 36 rules |
| Three-tier holdout active, spend frozen; two validation touchpoints spent | Holdout removed (rule 22); every year solvable; no out-of-sample number |
| PJM sole CALIBRATED; NYISO/NEISO with caveats; 3 NOT-YET | NEISO, NYISO CALIBRATED on every registered year; 7 NOT-YET (v3.13 worst-of) |
| Rubric v2.x; per-lane fleet censuses | Rubric v3.17; W0 EIA-860 vintages in every keeper (2026-10-02) |
| Multi-year runs, cross-year warm start default-on in CLIs | One year per shard container, cold (rules 32–36) |
| Public rejected-run registry on the dashboard | Keeper-only retention; rejections live in records and the mechanism matrix |
| Gap register O1–O8 | O4 (CAMPD outage seam) open; O5 (self-certification) re-opened by C3; O8 closed with the NEISO keeper; others per lane C §6 |

## 4. Site drift corrected in this PR

See `docs/audit/2026-10/D1-site-drift-concept-pages.md` and
`D2-site-drift-calibration-pages.md` for the full was → now log. Headlines:
index and config-reference now say nine regions; lp-core says warm start is
off by default (rule 36); capacity-evolution carries the 0–7 order;
model-validity no longer advertises the holdout ladder and cites rule 22 and
rule-history §18; results-calibration, calibration-rubric and mechanism-matrix
read rubric v3.17 and the current purpose of `calibration-complete.json`. A new
page, `model-audit.html`, carries this audit's summary and the computed
per-ISO table. Not resolved here: the animated capacity flowchart's step data,
the rubric version history past 3.17, the data-completeness note on SPP/NWPP/
SOCO, the pre-v3.13 prose in the SPP and ERCOT keeper shards, and
`docs/codebase/02`–`03` (`/sync-docs`).

## 5. Recommendations

**Owner.** (1) Restore a protected year or label every calibration claim
in-sample, on the status page and in forecast gate (a). (2) Freeze the rubric
between promotions; an amendment that admits a failing cell is a promotion
decision, not a scoring fix. (3) Rule on the fourth commitment mechanism
(A1): document it in the spec beside the bridges or delete it (rule 26). (4) Rule on whether any 2026–2050 number may be
quoted before the forecast program leaves T1 and the uncertainty band exists.

**Engineering.** (1) Rewrite every keeper shard's determination prose to the
v3.13 reading, or render only the computed value. (2) One attestation schema,
validated by `audit_keepers.py`. (3) `/sync-docs` on `docs/codebase/02`, `03`,
spec §1.9, the methodology doc's "holdout-tested" sentence and
`pipeline/solve.py:60`. (4) Fingerprint or prove inert the env-var solve knobs
(A5). (5) Refresh the forecast gate-(a) board against the 2026-10-02 keepers.
(6) Fix the capacity flowchart step data and extend the rubric history to 3.17.

---

*Read-only at `d7ff7c20`, 2026-10-03. Lane reports are the evidence; this
document is the composition. Determinations recomputed in-session from
committed bundles; no LP solved.*
