# CAISO locational AS requirement mechanism — handoff (2026-07-10)

Successor to the caiso-70 arc (`results/calibration/FINDING-caiso70-bridge-decrowding-negative-2026-07-10.md`
— read it first). That FINDING closed probe #1 (RA-bridge de-crowding: negative; the ablation's
CT lift is an evening commitment/seam effect) and scoped probe #2: the award→energy channel
exists as machinery (`caiso_commitment_posture`, ported and tested this session) but is
**ex-ante inert on the system-wide BAL-002 requirement** (~2.2–2.7 GW) because un-postured free
reserve supply (hydro ≥ 6.6 GW full-nameplate ramp10, fast-start CT ≥ 4.3 GW offline ramp,
batteries ~5–8 GW over a trivial 0.5 h SOC gate) covers it several times over. **Do not solve
that configuration.** The binding driver must be locational.

## What landed this session (all pushed)

1. `caiso_commitment_posture` (scenarios.py + reserve_config.py `_caiso_design` + tests in
   `tests/test_commitment_posture.py::TestCaisoPortSharesMechanism`): the MISO/PJM
   `_posture_pool_params` lever verbatim — U/SU columns on non-fast-start pergen pools, joint
   headroom re-anchored, CEMS min-load coupling, NREL startup charge, online ramp gate. Zero
   fitted parameters, default off, first design composing posture with the storage duration
   gate. Read only under `energy_reserve_coopt + caiso_reserve_coopt`.
2. `scripts/fetch_caiso_oasis.py --datasets asreq`: DAM `AS_REQ` → `data/raw/CAISO-AS/` —
   hourly MW **minimum and maximum per AS region** (`AS_CAISO`, `AS_SP26`, `AS_NP26`, `_EXP`
   variants) and product (SR spin / NR non-spin / RU / RD), 2023–2025 (train years only; Jan-2023
   verified retrievable). Columns: `ANC_REGION, ANC_TYPE, XML_DATA_ITEM
   ({SP,NS,RU,RD}_REQ_{MIN,MAX}_MW), MW, OPR_DT, OPR_HR`.
3. caiso-70 + ablation registered (probes, negative result); caiso-70 is the **first CAISO
   bundle with C6 governance PASS** — reuse its `calibration_attestation.json` as the template.

## The build (caiso-71), in order

1. **Finish the AS_REQ intake** via the `data-intake` skill: schema
   (`ancillary-services.schema.yaml` already exists — extend for CAISO or add a
   caiso partition), curation to clean parquet, README with the query provenance. Raw CSVs
   land from the fetch; keep the min AND max series (max = anti-concentration cap, also real).
2. **Sub-regional reserve families in `_caiso_design`**: add zone-masked spin/non-spin families
   from the measured regional MINIMA — `AS_SP26 → {LA_BASIN, SDGE, SP15_rest}`,
   `AS_NP26 → {NP15, ZP26}` (Path 26 is the regional boundary; the split topology makes the
   masks expressible). Keep the system requirement (BAL-002 formula or the measured `AS_CAISO`
   series — decide and document; the measured series is rule-13 admissible and preferable per
   rule 14). The family machinery (`balance_zone_mask`) already supports this — no dispatch.py
   change for the families themselves.
3. **Honesty check before solving** (the caiso-70 lesson — cheap arithmetic first): compute
   whether the SP26 minima can be served for free by IN-REGION un-postured supply (SoCal
   fast-start CT offline ramp + SoCal storage + SoCal hydro). The structural leak to watch: the
   single co-drawn R column lets OFFLINE fast-start CT back **spin**, which is not real (spin
   must be synchronized). If the leak covers the minima, the required increment is the
   PJM-style sync product split with P0-online scoping (`pjm_reserve_pergen_sync` pattern,
   `build_pjm_reserve_p1_prep`) — note the product split (`pergen_col_pool`) is **mutually
   exclusive with posture_pools** in `dispatch._build_reserve_rows_pergen` today; composing
   them is a dispatch.py extension. The P0-online sync-scoping route avoids that exclusivity
   and may be the cheaper first probe.
4. **Probe caiso-71** (pre-register the A/B): caiso-70 recipe (SP15 split, drag off,
   startup-aware bridge) with `caiso_scarcity_pricing=False` (mutually exclusive with the
   co-opt), `energy_reserve_coopt=True`, `caiso_reserve_coopt=True`,
   `caiso_commitment_posture=True`, + the regional families. All flags ride the
   `prb_overrides` channel (caiso-62/66/70 precedent; script template
   `scripts/probes/_caiso_g61b_decrowd_ab.py`). 2023–2025 one bundle, main + zero-forcing
   ablation, both registered as probes. Success directions: CT_PEAKER up from ~0.9 toward
   4.6/5.2/3.1 TWh **evening-loaded** (D-1 profile_r > 0.8 is the shape gate the drag used to
   carry); evening λ toward measured; 2024/25 local tail forms (hrs>$200: actual 35/8, model
   currently 0/0); C8 stays clean (the posture is not a floor — no D-2 id); the 2023 system
   tail (530 spurious hours) should NOT grow.

## Discipline reminders

- Train years only; LOYO within 2023–2025 before proposing anything; never touch
  2022/2019/H1-2026 (rule 22). The AS_REQ fetch is already clamped to 2023–2025.
- One mechanism per phenomenon (rule 19): if the regional-AS mechanism commits evening gas,
  reconcile with the RA bridge's role (both act on gas commitment — enumerate D-2 before
  stacking; the bridge is midday-gap, the AS hold is evening, so windows should not overlap,
  but verify).
- Rubric is v2.4; caiso-69's stored metrics are v2.2 — re-score for comparisons, don't read
  stored statuses.
- Register every solve (main + ablation) the session it completes; CAISO registry is at 15/15
  after caiso-70 — the next registration must prune the oldest (2026-07-06-caiso51-statmode-v2)
  sidecar + payload in the same commit.
