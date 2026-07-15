# HANDOFF — CAISO price-residual candidate campaign (post Jan-2023 backfill)

Written 2026-07-14 by the OASIS-backfill session. Evidence base:
`docs/DIAGNOSIS-caiso-lmp-jan2023-backfill-2026-07.md`. Keeper under test:
`2026-07-13-caiso-80-supply-demand` (bundle
`results/calibration/caiso80_supply_consistent_demand`). Verdict NOT-YET on
C3a (+18.5/+28.3/+32.2% vs RT lw), C3b (NRMSE 0.296/0.401/0.354), C3c, C4.

## Mission
Run single-delta test bundles off the caiso-80 keeper recipe to identify
which structural variable(s) close the price residual, ranked by the
diagnosis lanes: Lane T (soft-month floor too high — the C3a body) and
Lane W (winter seam mispricing — Jan-2023 +48% / Jan-2024 −19%). Promotion is
the owner's call; the deliverable is registered, scored bundles + a ranked
findings note.

## Ground rules (repo CLAUDE.md; the ones this campaign trips over)
- Rule 1: structure first. NO offer-curve tuning (caiso-80 B3 contraindication
  stands). Never reject a measured input because the fit worsens (rule 14).
- Rule 16: every bundle solves `--year 2023 2024 2025` in ONE invocation;
  years sequential (rule 12); ≤2 concurrent CAISO invocations (plant-level).
- Rule 20 (amended 2026-07-14): NO ablation twin — do not build one.
- Rule 15: every completed run (keeper or rejected probe) is registered on
  the dashboard and pushed the same session (`calibration-report` skill).
- Rule 22: structural mechanism changes score leave-one-year-out within
  2023–2025 before any promotion recommendation. No years outside 2023–2025.
- Rules 23/24: measured-parameter derivations cite their source-data change;
  every new tunable lives in ScenarioConfig and the run_config.
- §4 of the diagnosis lists adjudicated dead ends — do not re-run them.

## Mechanics
- Single-delta probe: `python scripts/replay_keeper.py
  results/calibration/caiso80_supply_consistent_demand --set KEY=JSON
  --out-dir results/calibration/<probe-name> --note "<why>"` (the sanctioned
  prb_overrides channel; the recorder defect that once stomped explicit
  kwargs was fixed 2026-07-13 — verify each probe's run_config.json records
  the delta).
- Score: `python scripts/calibration_verdict.py --run-id <id>` after
  registration (`scripts/dashboard_add_run.py`, then `build_manifest.py`).
- A/B read: compare against the keeper's registered statuses, not local
  re-prints (cross-machine HiGHS spread is a known ±band-edge hazard —
  caiso-80 entry).
- Push: text via `mcp__github__push_files`; for binary-bearing commits this
  environment's session git proxy accepted normal fast-forward `git push`
  (2026-07-14 session; the api.github.com Data API is proxy-blocked).

## Step 0 (no new mechanism) — measure the keeper's trough + January hourly
The committed payload only has monthly `pMon`. Regenerate the keeper's hourly
parquets ONCE (`replay_keeper.py … --out-dir <scratch>` with NO --set), then:
(a) model hours ≤$0 / <$15 / >$200 per month vs the actual hub series
(`actual_lmp_hourly_CAISO.parquet`; actual ≤$0: 227/755/561 DA hours
2023/24/25) — confirms how much of Lane T is trough-depth vs shoulder-level;
(b) January-2023 hourly decomposition: which unit class/import tranche is
marginal in the model's >$200 hours, and what the seam corridors priced.
(c) run `scripts/compare_caiso_intertie_formula_vs_measured.py` for the seam
formula-vs-measured gap on 2024/25.

## Candidate matrix (one bundle each, ranked; stop-loss: if a candidate's
delta on C3a/C3b is within solver spread and its mechanism evidence is
negative, register it as a probe and move on)

**W1 — measured January seam (data intake, then re-solve).** The 2023
intertie series starts at hour 2040; before that the per-hub corridors ride
the static fitted ladder, in exactly the +48% month. **The Jan 1–25 intertie
DA prices are ALREADY in the committed hourly aggregate** (2026-07-14 session
follow-up: `CAISO_dam_hourly_2023.csv` now carries `MALIN_5_N101`,
`CAPTJACK_5_N003`, `PALOVRDE_ASR-APND` rows — Jan DA means Malin $147.8 /
Palo Verde $143.0). Build the Jan window of
`wecc_intertie_lmp_hourly_CAISO.parquet` from those rows on
`fetch_caiso_intertie_lmp.py`'s convention (LMP column already = MCE+MCC+MCL
[+MGHG≈0 at these nodes]; MALIN = mean of its two nodes). Then re-solve the
keeper recipe unchanged (the parquet is the delta — note it in run_config
note). Rule-14 framing: replaces a fitted ladder with measured prices in the
miss month, whichever way the residual moves. Missing Jan days + Feb arrive
via the fixed `fetch-caiso-oasis-bulk.yml` workflow (extractor rglob fix,
same session) whenever the owner re-dispatches it.

**T2 — per-hub midday negative tail.** First a no-LP check (step 0a/0c):
does the keeper's Path-46 corridor price dip ≤$0 midday like the measured
Palo Verde series? If the corridor already carries the measured negative
hub hours but the MODEL price still floors ~$0, find what binds (import
tranche MW cap midday? in-state committed CC min-gen? storage charging).
Candidate flags (read their ScenarioConfig docstrings first — some are
superseded by `caiso_per_hub_intertie=True`): the per-hub-native analogue of
`caiso_import_solar_shape` (build if missing), `caiso_bidir_intertie` is
already superseded — do NOT arm alongside per-hub.

**T3 — in-state solar negative-offer depth.** `negative_renewable_offers` is
armed; audit the CAISO solar credit depth (REC/PTC value in
`compute_dispatch_credits`) against the observed DA floor distribution
(p1 −$7.3, min −$18.7 in 2023; deeper in 2024/25). Any change must cite a
measured credit source (rule 23), not the residual.

**W2 — winter import legs.** `caiso_import_gas_coupling=true` (gas-set DSW
tranches track the measured commodity delta — pairs with the armed
`gas_hub_basis_overlay`) and/or `caiso_per_year_import_caps=true`. Targets
Jan-2024 UNDER as much as Jan-2023 OVER: check both months' direction in the
A/B.

**T4 — overnight committed-CC floor.** B1 found +0.6…+2.5 GW round-the-clock
CC over-commitment; overnight price rides committed-CC cost. The RA bridge
min-load (measured 0.26) and `caiso_ra_bridge_decommit` govern this — look
for a MEASURED overnight commitment driver (60-day disclosure analogue, CEMS
overnight-online MW) before touching any floor; rule 19 (enumerate D-2
mechanisms first) and the caiso-81 refutation apply.

**S — tail.** Do not chase separately: W1 should collapse the 2023 spurious
tail; the missing 2024 local tail is out-of-representation (hourly LP) and
stays a documented C3c limitation unless a measured local driver emerges.

## Reporting
One findings note (`results/calibration/FINDING-caiso-campaign-<date>.md`)
ranking candidates by registered A/B deltas (C3a/C3b/C3c/C4 + LOYO for any
promotion candidate), plus the diagnosis doc updated with step-0 measurements.
Keep the top-15 CAISO retention when registering (prune inert probes).
