# RESULT — closeout-B W0 phase 3: the EIA-860 settlement re-solve, all nine ISOs (2026-10-02)

Lane: closeout-B W0 phase 3 (session_018DsgkLcN1h8NQc2yJegmdN), chartered by the Backcast close-out desk (session_017wUwd6xxLRQKAYiT8G722P).
PRECOMMIT: `PRECOMMIT-closeout-b-w0-phase3-2026-10-02.md`.

What the lane did: it re-solved each ISO's keeper recipe plus the ten W0 EIA-860 settlement backcast defaults (owner ruling R-2), one year per shard (rules 32/34/36). It then composed the years with `scripts/probes/_w0_compose_span.py`, scored them with `calibration_verdict.py`, and promoted with `promote_keeper.py` on structure (rule 1).

## 1. Determinations

The solve SHA recorded below is the one each leg actually solved at, read from the leg's `meta.git_sha` (desk 10:08).

| ISO | Keeper run | PR | Solve SHA(s) | Determination before → after | Notes |
|---|---|---|---|---|---|
| NYISO | `2026-10-02-w0-nyiso` | #7041 (merged) | 306f2c00 | CALIBRATED → CALIBRATED | Denominator yields. |
| CAISO | `2026-10-02-w0-caiso` | #7044 (merged) | 306f2c00 | NOT-YET → NOT-YET | Denominator yields. Since superseded by the closeout-CAISO arms. |
| ERCOT (W0) | `2026-10-02-w0-settlement` | #7045 (merged), replay fix #7048 | 306f2c00 | NOT-YET → NOT-YET | Forward 2025 C3a went −9.4 → −10.0 % (flipped to FAIL). |
| SOCO | `2026-10-02-w0-soco-fix2` | #7055 (merged; supersedes #7043) | 2019–21 306f2c00, 2022 837556d2, 2023–25 25da6022 | CALIBRATED-WITH-CAVEATS → NOT-YET | Owner: "Promote". C2 CC_REGULAR fails 2019 and 2021 (+3.6 pp). COAL_PRB 2022 is repaired by the denominator fixes. |
| ERCOT (L1) | `2026-10-02-closeout-l1-coal-fuel` | #7066 (merged) | 106d6bb7 | NOT-YET → NOT-YET | Owner: "Override + promote" (K2). 2022 C1 CC_REGULAR and 2025 C3a both move FAIL → PASS. |
| NEISO | `2026-10-02-w0-neiso` | #7070 (merged) | 306f2c00 (byte-inert through fix-2) | CALIBRATED → CALIBRATED | Owner: "Override + promote" on the §3b kill (2025 C3a +6.6 → +3.8 %). |
| PJM | `2026-10-02-w0-pjm-fix2` | #7069 (merged) | 2019–23 25da6022, 2024–25 ce8820dd | NOT-YET → NOT-YET | C1 CC_REGULAR moves FAIL → PASS in 2020, 2022 and 2023. 2025 C3a and C3b move PASS → FAIL. |
| MISO | `2026-10-02-w0-miso-fix2` | #7074 (merged) | 25da6022 (all seven legs) | NOT-YET → NOT-YET | price_mean moves FAIL → PASS (2020 C3a +11.6 → +9.6 %). fuelmix and price_shape still FAIL. Train 2023–25 stays CALIBRATED. |
| NWPP | `2026-10-02-w0-nwpp-fix2` | #7076 (merged) | 25da6022 (all seven legs; 2019 re-solved because the kept 306f2c00 leg recorded the NWPP-owned rule-26 field at a non-inert value) | NOT-YET → NOT-YET | fuelmix moves FAIL → PASS (2025 CC_REGULAR +9.60 → +7.91 TWh, on the kept bench parts). price_mean, price_shape and dispatch_corr still FAIL. C3a 2023–25: −23.1 / −30.7 / −4.6 %. |
| SPP | `2026-10-02-w0-spp107` (HELD; not promoted). Successor: the relief re-solve `w0-spp107r` | none (owner: "Hold, fix derate first") | b27b19c4 (all seven legs) | NOT-YET → NOT-YET; **train 2023–25 CALIBRATED → NOT-YET** | C1 ST_GAS crosses its volume band in 2024 (−7.85 → −8.16 TWh) and 2025 (−7.61 → −8.26 TWh). C3c 2025 is then no longer the lone failure, so price_tail goes CAVEAT → FAIL. Owner: "Hold, fix derate first". spp-107 stays the keeper, and the bundle is kept locally (rule 31). #7046 (spp-100) was superseded by the owner's merge of #7025. |

PJM card, verbatim per the desk: **before→after mixes W0, the renewables fix (#7040), and the incumbent's off-lockfile solver stack (highspy 1.15.1 vs locked 1.14.0); not separated, by design.**

## 2. Owner rulings recorded (decision cards, 2026-10-02, relayed by the desk)

1. **ERCOT L1:** "Override + promote". K2 is overridden. Promoted in #7066 from closeout-ERCOT's canonical legs: 2019 from `l1`, 2020–25 from `l1b`.
2. **NEISO §3b:** "Override + promote". Promoted in #7070.
3. **SOCO:** "Promote". The HOLD on #7055 was lifted and the PR merged.
4. **Capacity census:** "Sign all three". The census is signed for NYISO, CAISO and ERCOT.
5. **NEISO C3c:** "Sign + adjacent-year carry" for the 2019–20 reserve-requirement gaps. It is not armed here: if it changes the solve surface it becomes a separate arm.
6. **R-4 coal basis:** "930-aligned A".
7. **IMM licence, DAM-proxy census and census gate:** as recommended. Raw IMM data stays out of the repo; the DAM-proxy census is chartered; the census gate stays presence-only.
8. **SPP (relayed by the desk):** "Hold, fix derate first", then "Investigate, then fix". After the zero-LP overlap result, the owner chose **"Drop band on rated rows"**, i.e. option (a). That is #7081: the MMU ambient Jun–Sep share is skipped on rows carrying a published seasonal pair, and SolveEpoch 2026-10-02e re-keys backcast SPP. There is no re-solve yet. Next is a zero-LP FINDING on the ST_GAS driver, then one SPP re-solve carrying both fixes.
9. **NWPP bench parts:** "Keep old figures, fix later". The bench re-render is reverted in #7076, so the `nwpp_demand_plant_basis` anchor CSV, the keeper and its test stay consistent. **Chartered follow-up:** decouple the anchor from roster-dependent parts, then re-derive it and re-solve NWPP.
10. **Replay fidelity:** "fix it now". That is #7078 (merged).
11. **SPP ST_GAS stack (desk, 22:48):** run the zero-LP pre-check first, with the reading and threshold fixed in a PRECOMMIT, and arm `wefor_residual` for ST_GAS only if the measured evidence shows a double count.
   - `docs/records/spp/PRECOMMIT-spp-w0-stgas-wefor-relief-2026-10-02.md` was pushed at 37af3ccf, before any compute.
   - G1 PASSES: pooled 2023–25, the measured overlay X is 0.534 against the applied statistical W of 0.191.
   - Hence `wefor_residual = 0.0` on `["ST_GAS"]`, frozen in `spp-w0-stgas-relief-identification.json`.
   - Seven shards (`w0-spp107r-*`) were launched at main 15a351a1, carrying #7081 and the relief. The promotion question follows in its own PR.

## 3. Data drift (labelled on every card, not W0)

The 2025-only injected must-run (biomass + OTHER) rose between each incumbent and its W0 re-solve. The incumbents carried a partial 2025 EIA-923; the current data has the complete year. No price actuals changed.

| ISO | 2025 must-run change |
|---|---|
| MISO | +6.5 TWh |
| PJM | +5.3 TWh |
| SOCO | +4.4 TWh |
| CAISO | +2.4 TWh |
| NWPP | +1.5 TWh |
| NEISO | +1.2 TWh |
| SPP | +0.3 TWh |
| NYISO | +0.25 TWh |
| ERCOT | +0.24 TWh |

- **Earlier years:** 2019–2024 are equal, except ERCOT 2019–22 (+0.07 to +0.09) and MISO 2019 (−0.02).
- **2025 C1 actuals:** these also moved with the rebench (ERCOT CC_REGULAR +6.3, CAISO +1.2).
- **Retroactive (desk):** this drift applies to the already-merged NYISO (#7041), CAISO (#7044) and ERCOT (#7045) promotions, at +0.25, +2.4 and +0.24 TWh.

## 4. The denominator fixes and the mixed-SHA composes

- **#7047 (837556d2):** the Scherer in-year exit-dilution defect (D-1).
- **#7049 (25da6022, fix-2):** the live-roster denominator. The sub-gate field `unit_outage_dispatched_bin_live_denominator` was deleted (rule 26). SolveEpoch 2026-10-02d re-keys MISO, NWPP, PJM and SOCO.
- **Re-solve rule (desk 14:31):** every leg whose LP inputs are not byte-identical between its solve SHA and 25da6022 re-solves at 25da6022. That is 21 legs. Each kept leg carries the zero-LP proof `W0-phase3/KEPT-LEG-INERT-PROOF-2026-10-02.md`, which chains three results: the G-DRIFT audit, #7047's `inert_sweep.json`, and the fix-2 sweep §4.
- **Composer (`_w0_compose_span.py`):**
  - It now takes `--pinned-sha YEAR=SHA` per leg.
  - A mixed-SHA compose requires `--inert-proof` and writes a `mixed_solve_sha.json` sidecar. The sidecar is not in meta: replay binds every meta key to a solve kwarg.
  - It accepts a deleted rule-26 knob only when it is recorded off on both sides.
  - Every leg must share one `solve_surface` fingerprint.

## 5. Infrastructure defects found and fixed

1. **ERCOT keeper replay (#7048).** The meta base came from the 2019 validation leg, with no partition. The fix added `scripts/lib/replay_recipe.py` and `promote_keeper` preflight 0d.
2. **Rule-26 deletion registry on the recorded side (#7052, desk).**
3. **Fields registered after the solve (#7057, CAISO lane).** `spp_mmu_offer_repair` (#7025) failed 0d on every pre-#7025 bundle. This lane fixed it independently, but main's `_registered_after_solve` is the one implementation kept.
4. **`stamp_config_partition.build_block` (#7069/#7070).** An inert rule-26-deleted field recorded by an older leg became a phantom per-year overlay, which `replay_keeper` refused. It is now dropped via the same deletion registry.
5. **`promote_keeper` with `config_partition` keepers (ERCOT, MISO, SPP).** Partition configs stay on the outgoing run id (E12/S1). Re-keyed by hand each time. **Follow-up.**
6. **`fleet_only` rebuild skips the strict clean-partition check.** This caused the SOCO 5 TWh rebuild gap; with the hydro-plant-modes partition present, the rebuild matches the solved bundle within 0.9 MWh/unit. **Follow-up:** `rebuild_fleet` should call `check_clean_partitions(strict=True)`.
7. **FINDING (desk 10:47):** `promote_keeper` / `audit_keepers` should refuse a keeper whose run_config environment is off the lockfile. The PJM incumbent was on highspy 1.15.1. **Follow-up.**
8. **`replay_recipe` set normalisation (#7074).** The resolved config holds a frozenset where `run_config` records a sorted list, which gave a false preflight-0d mismatch on MISO `temp_derate_classes`.
9. **Composer rule-26 tolerance.** The composer accepted an explicit `unit_outage_dispatched_bin_live_denominator=False` on NWPP 2019 under a generic "off on both sides" test. NWPP owns that field, so False is not inert, and preflight 0d caught it. The composer now uses replay_keeper's deletion registry; NWPP 2019 was re-solved at 25da6022.
10. **FINDING: attestation text.** `w0_attest.py` wrote "replayed … at 306f2c00" on the SOCO (#7055) and PJM (#7069) attestations, but those legs are mixed-SHA. The per-year truth is each bundle's `mixed_solve_sha.json`. The helper takes the SHA as an argument from NWPP onward.
11. **Replay of pre-W0 keepers armed the W0 defaults (#7078, fixed).** `meta.json` never carries the W0 fields. A pre-W0 `run_config` records six of them as False and lacks the other two. `replay_keeper` resolved all of them to today's True: spp-107 2024 replayed with 6 config diffs.
   - `flipped_default_overlay` now pins every flipped-default field to its recorded value, or to `registration_time_default` when absent.
   - The preflight's after-solve excuse compares against that same absent-equivalent value.
   - spp-107 now replays with 0 diffs, and the W0 keepers are unchanged.
   - After #7076, spp107EXR_span is the only pre-W0 keeper on main.
12. **Stamper (`stamp_w0_matrix.py`, scratchpad).** The NWPP gates string carries JS-only escapes, so the stamper now splices the prior text raw.
13. **Registry parity sweeps every local `results/calibration/` dir.** Leg dirs must be staged outside the repo tree during promotion. Not a code defect.

## 6. Root-cause items routed (not fixed here)

- **Retiring-plant last-year over-run.** +9.5 TWh over 19 rows; wind-down conduct is not represented. Routed to the MISO and SOCO lanes.
- **Census PHANTOM rows.** Oklaunion 2021–25 and Frontera pre-entry: the census tool counts rated MW that has 0 available MWh. A census-tool defect.
- **Census top-12 truncation.** A census-tool defect.
- **NEISO.** The 2019 oil heat-rate share is 0, and the impossible oil heat rates remain in the keeper. NEISO-lane items.
- **SPP MMU × seasonal basis (rule 19; zero-LP, measured on fleet_only rebuilds).**
  - The overlap is real. An MMU fossil row carrying a seasonal pair takes its published summer frac (the `not _mmu_row` guard covers only the flat-class branch) and also the Jun–Sep ambient band.
  - Size, Jun–Sep: 169 / 158 / 196 MW in 2023 / 24 / 25, of which ST_GAS is 8 / 8 / 28. The ambient band is 401 / 312 / 312 MW; the W0 summer cut is 841 / 1,240 / 1,374 MW.
  - spp-107 already carried the same pairing, with net-summer pmax plus the band.
  - The guard as written would return 0.8–1.4 GW, not the overlap. Option (a), dropping the ambient band on paired rows, returns about 160–200 MW.
  - **The SPP train-tier ST_GAS failure is not this.** `W0-phase3/FINDING-spp-w0-stgas-availability-2026-10-02.md` attributes it field by field at zero LP. This corrects the earlier note that W0 adds zero-availability rows.
    - The driver is `commission_year_cod_fallback`: −166 MW annual mean available in 2024. True commission years arm the age-escalated statistical WEFOR, ST_GAS 0.147 → 0.214.
    - That statistical WEFOR stacks on SPP's measured outage layer with no residual relief (rule 19).
    - The +568 MW of pmax (`partial_plant_exit_carry`) moves availability by −3 MW.
    - Recommendation: keep the fallback (rule 14) and reconcile the stack through the existing WEFOR residual relief, after a zero-LP pre-check.
- **CC_REGULAR over-dispatch on the measured W0 fleet.** SOCO 2019/2021; next root-cause item for the SOCO lane (rule 14).

## 7. Operations

- **Shards:** run in env "Full access", at most 6 concurrent.
  - PJM ran swap-first, with ceiling + swap ≥ 17 GiB.
  - MISO 2023 was OOM-killed once (13.36 GiB + 2 GiB swap) and relaunched swap-first, with a 24 GiB hard stop.
- **Chunked transport:** MISO dispatch above 100 MiB went as `split -b 90M` chunks plus a `.sha256`, reassembled and checked at verify.
- **Shard branches:** several were deleted from origin before compose (PJM 2019/2020/2024/2025 and MISO 2021/2025, among others). Their verified bytes were held locally until promotion (rule 34).
- **NWPP 2019 fix-2 solve:** P0 2,622 s (406k simplex iterations, cold) and P1 4,004 s (warm), single-threaded, peak 6.06 GiB. Solver output is off (`model.py:672`), so a long silent solve looks stalled; a py-spy dump showed it inside `h.run()`.
- **Follow-ups:**
  - SOCO solve-profile `hydro_plant_modes`.
  - The environment setup script's `freshen` fetch fails intermittently.
  - `source_revision` was ignored on early launches.
  - Rate limits.
