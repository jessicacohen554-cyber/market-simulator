# Calibration Log — SPP

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for SPP calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## Lane state at file creation (2026-09-07, lane SPP-34)

**No keeper exists.** SPP was registered as the seventh ISO on 2026-09-06 by
lane SPP-20 (`docs/handoffs/FINDING-spp-20-2026-09-06.md`); the first-ever solve
and the first keeper are lane **SPP-40**'s, whose four preconditions are
SPP-30 / SPP-31 / SPP-32 / SPP-53 (plan §4 critical path, owner ruling r#5). So
`frontend/data/backcast/keepers/SPP.json` does not exist yet, and this lane has
no run to score, no determination and no gates.

Program docs: `docs/multi-iso/spp-addition-plan-2026-09.md` (charters, cards,
wave graph, lane table), `docs/handoffs/spp-desk-ledger-2026-09.md` (live state
— **the ledger wins where the two diverge**), `docs/multi-iso/spp-data-audit.md`
(the Phase-0 census). Lever queue: `docs/mechanism-testing-matrix.md` §5.7;
cell verdicts `docs/codebase-site/data/mechanism-matrix/SPP.js`.

Two facts every SPP session inherits, so nobody rediscovers them in a residual:

- **The N↔S TTC is a Tier-3 placeholder that cannot bind** (48,700 MW = the
  North zone's own EIA-860 2025 ER summer capability). No public document states
  an SPP North↔South transfer capability — SPP-13 swept all four candidates and
  found the rated interface data is NDA / CEII
  (`docs/handoffs/FINDING-spp-13-2026-09-06.md` §0). Until lever **SPP-53**
  reconciles one, an SPP solve is a **two-zone copperplate on price**, and
  SPP-40's P7 STOP gate ("link binds in the measured direction/season") cannot
  be met. Never tune the placeholder to a price residual (rules 1 / 13 / 14).
- **The published hubs are a two-point spread, not a zonal price.**
  `SPPNORTH_HUB` ≈ Nebraska, `SPPSOUTH_HUB` ≈ central Oklahoma
  (`docs/multi-iso/spp-data-audit.md` §6.1), so the scoring benchmark is a
  narrower object than the zones it grades. State this at the gate rather than
  absorbing it.

Holdout tiers (rule 22 `[R-HOLDOUT]`): SPP holds **neither** marker — no
`complete`, no `final` — so 2019–2022 and H1-2026 are unsolvable, unscorable and
unregisterable for SPP at both the CLI year gate and the registration gate. The
training window is **2023–2025**, and rule 16 `[R-ALLYEARS]` binds from day one
(`audit_keepers._MULTI_YEAR_ISOS` already lists SPP): a single-year SPP keeper is
refused.

## Pre-push checklist (STANDING — every session in this lane, before every push)

`.claude/hooks/ruff-prepush-gate.sh` (`PreToolUse` on
`Bash|mcp__github__push_files`) refuses a push whose *own* changed `.py` files
fail either gate, and names them plus the fix. It is check-only — it never edits
your tree (rule 27 `[R-PUSH]`). Run the two commands yourself anyway: a hook can
be disabled, a session can run without it, and it deliberately does not gate the
whole tree. Run from the repo root and confirm **exit 0** before staging:

```
uv run ruff format --check .
uv run ruff check .
```

**Tree-wide, not just your own files.** `.github/workflows/ci.yml` runs exactly
these two commands over the whole tree, so a formatting miss anywhere turns the
lane's PR red — and the next lane's too.

**If it fails, format only the files it names**, then verify the change carries
no semantic delta before pushing — `git diff -w` is NOT sufficient (ruff reflows
split and join lines, and adds magic trailing commas plus grouping parens, all of
which survive `-w`). Compare the parsed tree instead:
`ast.dump(ast.parse(before)) == ast.dump(ast.parse(after))` per file.

---

## 2026-09-07 — spp-1: SPP-40 first SPP solve — rule-29(a) screen (2024) KILLED at the P7 STOP gate

**Result: SCREEN KILLED on the direction leg; the full span was NOT spent; no bundle registered, no
keeper.** Records: `docs/handoffs/PRECOMMIT-spp-40-2026-09-07.md` (pushed at `45d02b0e` before the
solve) and `docs/handoffs/FINDING-spp-40-2026-09-07.md` (every screen number; the bundle
`_spp40_screen` was deleted before merge, rule 29(c)).

- **Recipe**: the all-defaults backcast (`run_calibration_full.py --iso SPP --year 2024`, no other
  flag; `passes ["P1"]`, `commitment false`, `outage_source historic`, served EIA-930 interchange per
  P2, N↔S link 3,400 MW per SPP-53), every offer band **1.0**. Zero-LP phase 0 found SPP coal
  inheriting the generic ERCOT-fitted `COAL` bands (0.90 committed / 1.45 peak) — corrected before the
  solve by the SPP-scoped `_SPP_OFFER_CURVE` identity merge (`pipeline/backcast_config.py`, rule 25;
  six keepers unmoved, 0 surface rows moved). `authorized_price_tuning = NONE`.
- **Screen 2024** (146 s wall, 4.82 GB peak RSS; P0 78.7 s / P1 23.3 s): the 3,400 MW link is LIVE —
  at bound 1,776 h (20.3 %): **877 h N→S, 899 h S→N**. Pre-registered STOP *"S→N > N→S"* fired by
  22 h against a market 1.7:1 N→S dominant. Season leg passed (Spearman +0.14). Fuel mix all within
  [0.1×, 10×]: coal 0.94, gas_cc 0.85, **gas_ct 1.78**, gas_st 0.78, nuclear 0.98, wind 1.12
  (un-recurtailed gross-up delivered in full), hydro 1.00. 0 MWh unserved; **7 negative hours vs
  1,172 measured**; load-weighted price $26.37 vs RT $23.31 / DA $25.92; mean |S−N| zonal spread
  **$0.99 vs $17.23 measured**.
- **Structural reading**: South (Oklahoma / Panhandle) wind and CC export north overnight until the
  link binds, where the market traps that energy inside Oklahoma (`oklahoma_internal` binds 60–68 %
  of hours), curtails it and prices it negative — SPP-57 corroborated as the first lever (P1
  ranking). Nothing tuned; the TTC not moved. Routed: FINDING-spp-53 §6 O-1 / O-2; SPP-57; the
  `NG: WND` 2023 slip on the wind-input path (new); the CT/CC/ST gas split (commitment physics).
- **Desk action**: re-issue SPP-40 with the direction leg re-cut ex ante as a dominance ratio (or
  accept the corridor's bidirectionality) — one ~8-minute full-span solve; the branch carries the
  rule-25 fix, the PRECOMMIT and the FINDING (`build_status.ISO_ORDER += SPP` is the re-issue's,
  landed with `status/SPP.js`).
- Matrix shard: `measured_interface_limits` U → O; `keeper` / `gates` empty. Rule 22: only 2024
  (training tier) solved; nothing registered.

## 2026-09-07 — spp-2: SPP-40 full span 2023–2025 → FIRST SPP KEEPER `2026-09-07-spp-1-baseline` (owner direction)

**Result: PROMOTED — determination NOT-YET.** Owner direction, verbatim: *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress that may still be a
keeper."* The same all-defaults recipe as spp-1 (PRECOMMIT §2; every offer band 1.0; N↔S 3,400 MW;
served interchange) solved 2023+2024+2025 in ONE invocation (369 s wall, **5.25 GB peak RSS** —
memory class `per_plant=True, co_opt=False, peak_gb=5.3`), bundle `results/calibration/spp40_baseline_B`
(+ `hourly/`), registered, `keepers/SPP.json` created, `index.json` += SPP, `status/SPP.js` built,
`bench/SPP/{2023,2024,2025}` written, attestation + `legitimacy_diagnostics.json` committed. **This
bundle is the rule-29(b) control for every later SPP lane** (P7). Record: `FINDING-spp-40-2026-09-07.md` §7.

| criterion | 2023 | 2024 | 2025 | status |
|---|---|---|---|---|
| C1 fuel-mix | CC −2.8 TWh (+3.7 pp), **CT +6.7**, ST −9.2, **COAL_PRB −62.6 / LIGNITE −8.4 (class crosswalk)** | **CT +10.3**, COAL_PRB −58.9 / LIGNITE −8.5 | SKIPPED (preliminary 923) | **FAIL** |
| C2 family volume | PASS | PASS | skipped | PASS |
| C3a mean LMP | **+14.1 %** | in band (−3.7 % vs DA) | **+21.7 %** | **FAIL** |
| C3b NRMSE | 0.239 | 0.228 | 0.283 | **FAIL** |
| C3c tail >$200 | 0 h vs 42 | 3 vs 59 | 24 vs 68 | FAIL (not lone → no standing-rule caveat) |
| C4 dispatch r | PASS | PASS | PASS | PASS |
| C6 governance | attested; `authorized_price_tuning` NONE | | | PASS |
| C8 forced share | PASS | PASS | PASS | PASS |
| C5a CO2 (reported) | −67.1 % | −60.8 % | −66.9 % | the COAL-class drop below |

- **Two input/crosswalk defects found by the score, not by dispatch (routed, never patched):** (i) the
  benchmark scores SPP coal as `COAL_PRB` / `COAL_LIGNITE` while the model dispatches one `COAL` class
  (`coal_supply` is empty on every SPP plant), so C1's coal rows fail by construction and the coal CO2
  (~70 Mt) is absent from C5a's by-class sum — an EIA-923 fuel-type supply-class crosswalk SPP-30
  did not derive; (ii) the 2025 hydro budget reads 0.02 TWh (EIA-923 preliminary vintage, SPP-31
  §1.2) against ~8.8 TWh, and 2025 carries **2,007 MWh unserved in 6 hours** (Jul 24 14:00, Jul 30
  13–14:00, Dec 21 10–12:00; VOLL $2,000) — the missing hydro surfacing as scarcity; 2023/2024 have
  zero unserved energy.
- **Link (P7 evidence, three years):** at bound 2023 **1,702 N→S / 275 S→N**, 2024 878 / 897, 2025
  **1,245 / 373** — the 2024 tie that killed the screen is year-specific; the measured N→S-dominant
  direction holds in 2023 and 2025. Mean |S−N| zonal spread still ~$1 vs $12–17 measured; negative
  hours 9 / 7 / 6 vs ~1,000–1,170; wind 1.07 / 1.11 / 1.11× EIA-930 (0.0 % re-curtailment).
- **C1/C4-2023 wind: UNSCORED pending SPP-41** (r#6 addendum; the h3907 +3.5857 TWh EIA-930 slip on the
  bench path). 2024/2025 clean. *(DISCHARGED 2026-09-07 by lane SPP-43: the re-solve on the SPP-41 screened loader landed `bench/SPP/2023` wind 106.634 -> 103.049 and scored C1/C4-2023 wind at +10.68 %, the same value 2024/2025 read. See `docs/handoffs/FINDING-spp-43-2026-09-07.md` §3–§4.)*
- Gas basis: the run log records no 2025 basis fallback line (the per-plant EIA-923 delivered path
  served every year; state-series basis not consulted).
- Rule 22: 2023–2025 only; SPP holds no marker. Rule 25: nothing crossed. Lever queue corroborated:
  **SPP-57 first**, then the coal supply-class crosswalk (a data lane, zero DOF), then SPP-51.

## 2026-09-07 — spp-3: SPP-42 coal supply-class crosswalk (R-7) + 2025 hydro vintage repair (R-8) → SECOND SPP KEEPER `2026-09-07-spp-2-crosswalk-hydro`

**Result: PROMOTED — determination NOT-YET (unchanged headline; nothing flipped PASS→FAIL vs spp-1).**
Record: `docs/handoffs/FINDING-spp-42-2026-09-07.md`. Bundle `results/calibration/spp42_crosswalk_B` (+ `hourly/`),
457 s wall, **5.55 GB peak RSS**. Control = the spp-1 keeper's committed bundle (rule 29(b) form 4; G-DRIFT since
its `git_sha` 4639a309: one changed solve-path file, `scripts/lib/transmission_expansion/spp.py`, forecast-only —
INERT). Precondition: **SPP-41 has NOT landed** (no branch, no commit, no FINDING on `origin/main` at 40b54ce7;
r#7 re-issued it as v2, unlaunched), so C1/C4-2023 wind stays UNSCORED.

- **R-7 crosswalk** (`scripts/data/derive_coal_supply.py --iso SPP` → `coal_supply_SPP.csv`): 29 plants, 27 prb / 2
  lignite (2817, 6469), 0 unclassified, 19,846.7 MW unchanged. `_SPP_OFFER_CURVE` extended to all five coal keys
  (identity bands; rule 25) because the tag routes each plant to the ERCOT-lineage `COAL_PRB`/`COAL_LIGNITE`
  entry. Zero-LP `fleet_only` census, before/after, all three years: `mc_base`, fuel prices, availability,
  `min_gen`, every bound **byte-identical for every LP unit** — a scoring-class change only, so the charter's 2023
  screen was not spent (rule 29's inert clause). Benchmark side: the same tag stops the CAMPD backfill mis-firing on
  untagged coal plants (`mapped = COAL` never matched an EIA-923 row, so every coal plant looked under-reported and
  its CAMPD net was booked across its class shares — ~2.1 / 1.9 / 1.9 TWh of spurious `ST_GAS` in 2023/24/25); the
  vintage reconciliation then redistributes, so every fossil actual moved (`bench/SPP/*` re-rendered; 2024/2025
  totals identical, 2023's 284.10 → 288.20 TWh = the EIA-930 figure that still carries the h3907 slip → SPP-41).
- **R-8 hydro** (`--hydro-backfill-year 2024 --hydro-eia930-monthly`, the pair every multi-year keeper carries,
  every year per rule 22): 2025 0.0233 → **8.8299 TWh** (21 plants backfilled, level pinned); 2023/2024 8.4003 →
  8.3441 / 8.7023 → 8.9731. **2025 screen** (rule 29(a)): unserved **2,007 MWh in 6 h → 89.3 MWh in 1 h**; hydro
  8.82 vs 8.83. The charter gate's literal "unserved → 0" leg **NOT met**; the residual hour (12-21 11:00) is
  SPP-South at $2,000 behind the N→S link at its 3,400 MW bound with North at $18 — the SPP-57 object — and the
  lane proceeded on rule 14 (a measured level is not a lever a gate can decline), stated in FINDING §2.3.
- **Scorecard** (rubric v3.6): C1 FAIL — 2024 CC_REGULAR −8.6 TWh / CT_PEAKER +9.9 TWh only; **every 2023 class in
  band** (COAL_PRB −2.6, LIGNITE −1.5, CC −4.6, CT +6.1, ST −7.8 TWh); 2025 skipped. C2 PASS. C3a FAIL 2023
  +14.1 %; 2024 +7.5 % PASS; **2025 +21.7 % → +7.2 % PASS**. C3b FAIL 2023 0.239 / 2024 0.229; **2025 0.283 → 0.189
  PASS**. C3c FAIL 0 / 3 / **1** h vs 42 / 59 / 68 (not lone). C4 PASS (r 0.93–0.97). C6 PASS (attested,
  `authorized_price_tuning` NONE). C8 PASS. **C5a CO2 −66.5 / −60.0 / −66.9 % → −3.1 / −3.3 / +1.2 %** (the ~70 Mt
  that fell out of the by-class sum). Load-weighted price $27.88 / $26.36 / **$29.97** (was $34.03).
- **Differenced against spp-1**: 2023 coal +0.08 TWh, hydro −0.06, link 1,696 / 272 h at bound (was 1,702 / 275);
  2024 coal −0.15, hydro +0.27, link 877 / 895; 2025 coal −2.4, CC −2.0, CT −2.7, ST −1.7, hydro +8.8, link
  **1,573 / 228** (was 1,245 / 373), negative hours 8 / 7 / 6 unchanged, mean |S−N| $0.93 / $1.00 / $1.35.
- **New, ROUTED (P9; nothing repaired):** the raw EIA-930 SWPP `Demand` series carries **stuck identical-value
  runs** — 2025 **698 h in 19 runs** (155 h from 12-15 14:00 at a flat 37,455 MW; 109 h from 05-19; 82 h from
  10-07), 2024 396 h (96 h from 03-19), 2023 36 h; `Net generation` flat in the same windows, `Demand forecast`
  varying hour by hour. Every 2025 unserved hour (keeper and screen) sits inside the December window.
- Records: `keepers/SPP.json` re-keyed (spp-1 kept on the dashboard as the prior keeper until the next
  registration prunes it), `status/SPP.js` rebuilt, matrix shard keeper + gates stamped and
  `hydro_vintage_input_repair` U → K, §5.7 header, attestation (3 ledger entries, 1 residual, 0 tuned scalars),
  `legitimacy_diagnostics.json`; screen bundle deleted before merge (29c). Rule 22: 2023–2025 only.
- Desk recommendation (FINDING §7): **SPP-57 next**, then the CT/CC/ST split as a commitment-physics question.

**Next shorthand: spp-4.**

## 2026-09-07 — spp-4: SPP-57 Oklahoma pocket (third zone, FCITC chain links) — rule-29(a) screen (2025) KILLED at the STOP gate

**Result: KILLED — not a keeper candidate; full span not spent; nothing registered; topology NOT landed.**
Record: `docs/handoffs/PRECOMMIT-spp-57-2026-09-07.md` (pushed at `910fd5b1` before any limit or price was read;
addendum A re-pinned the control to keeper-2 after SPP-42 landed mid-lane) + `FINDING-spp-57-2026-09-07.md` +
`docs/handoffs/spp57/`. Control = `spp42_crosswalk_B` (rule 29(b) form 4; G-DRIFT from its sha `33034499`: four
CAISO-keyed hunks + its own recorded `backcast_config.py` change — all INERT). Screen bundle deleted before the
PR (29c); every number is in the FINDING.

- **Design (zero-LP, all landed as record):** `SPP-Oklahoma` = OKGE + GRDA + WFEC + w_OK·CSWS, w_OK = the measured
  EIA-861 PSO / (PSO + SWEPCO) retail-sales ratio **0.5216 (2023) / 0.5383 (2024) / hold-last 2025**
  (`data/raw/eia-861/`); static shares N 0.5125 / OK 0.2830 / S 0.2045; chain N↔OK↔S with the N↔S link retired.
  Both TTCs by the SPP-53 FCITC construction on a three-point spread (third point = the residual-South price from
  `SPS_SPS` + 28–29 named SWEPCO/AECC SLs, `actual_lmp_hourly_area_SPP.parquet`): **N↔OK 6,500 MW** (n_s_corridor ∪
  oklahoma_internal, 26 N→OK-loaded constituents, 25,116 h; corridor-only 3,355, Oklahoma-set-only 7,164; LOYO
  3,681 / 11,478 / 7,767), **OK↔S 6,700 MW** in its data-named S→OK direction (19 constituents, 18,715 h; the
  OK→S SPS-tie reading 10,700; LOYO 4,254 / 8,892 / 14,218). R1–R4 pass on both. Measured spreads (RT): |OK−N|
  12.13 / 17.23 / 15.18, |S−OK| 9.82 / 21.78 / 19.03, signed S−OK **+1.15 / +3.42 / +11.29** — the residual South
  reads DEARER than the Oklahoma hub (the PRECOMMIT's ex-ante sign guess was wrong; the direction was data-named).
- **Screen 2025** (keeper-2 recipe + topology; P0 84.5 s / P1 22.6 s, 159 s wall, 5.13 GB): **N↔OK at bound 215 h
  (2.5 % < 5 %)**, all N→OK; **OK↔S at bound 0 h**; model OK−N +0.08 (sign matches), **S−OK 0.00 vs measured
  +11.29 (mismatch)**; re-curtailment **0.00 %**; unserved 0 (control 89 MWh); negative hours **0** (control 6);
  load-weighted $30.20 (control $29.97); fuel families within band except the reference's own 2025 hydro defect.
  STOP on legs (i), (ii), (iii). The union rule pooled western-Oklahoma delivery elements (Gracemont–Anadarko
  6,658 h) into the N→OK set and the same elements into the S→OK set — the double attribution the config comment
  stated before the solve, now measured as two inert pipes. Reported from the screen's own flows, never re-cut:
  at 3,400 MW the N↔OK link would sit at/over bound **2,065 h (1,931 N→OK / 134 OK→N)**; at ~3,400 the OK↔S link
  622 h (603 S→OK).
- **Owner asked in-session whether this is a keeper candidate: NO** — the arm removed the one binding structure
  the keeper has (3,400 MW N↔S, 1,573 / 228 h) and added none; structure regressed, not just the gates.
- Records: solve path restored byte-identical to keeper-2's two zones (`solve_surface_register --diff` 0 moved;
  persisted identity 24/24); sidecars `rtbm_bc_oklahoma_limits_2026.parquet` (1,083,301 rows) and
  `actual_lmp_hourly_area_SPP.parquet` landed with README / SOURCES / SHA256SUMS rows; the three-zone implementation
  is the branch's design commit (cited in the FINDING) for the re-issue. Matrix shard: `measured_interface_limits`
  stays O, SPP-57 evidence appended. Rule 22: 2025 only, training tier.


## 2026-09-07 — spp-5: SPP-57b Oklahoma pocket, constituent sets re-declared (SPP-57 R-12) — rule-29(a) screen (2025) KILLED at the STOP gate

**Result: KILLED — not a keeper candidate; full span not spent; nothing registered; topology NOT landed.**
Record: `docs/handoffs/PRECOMMIT-spp-57b-2026-09-07.md` (pushed at `42ed8ff6` before any number was derived) +
`FINDING-spp-57b-2026-09-07.md` + `docs/handoffs/spp57b/`. Control = keeper-2 `spp42_crosswalk_B` (rule 29(b) form 4;
G-DRIFT from `33034499` → `dcb609f4`: 9 hunks, all INERT for a 2025 backcast; the SPP-41 wind screen LIVE in 2023
only, reproduced by the census). Screen bundle deleted before the PR (29c).

- **Construction (B′), declared ex ante:** N↔OK = `n_s_corridor` ALONE → SPP-53's **3,400 MW** unchanged (12 fwd /
  7 rev constituents; reverse reading 4,200); OK↔S = `sps_tie` ALONE on (p_S − p_OK) → **10,700 MW, OK→S-named**
  (4 identified: Potter County 10,705 / 3,850, SPSNMTIES 11,409, SPPSPSTIES 3,602; 6,177 h; NO S→OK-identified
  constituent; p25/p75 3,850 / 10,705; LOYO 8,395 / 10,490 / 14,796; R1–R4 pass, R2 by 3.5 %). `oklahoma_internal`
  EXCLUDED from both by a group rule (25 / 24 of its rows identify on the two spreads). The desk's expected
  3,000–4,000 was wrong — the weighted median lands on the most-binding, smallest-ψ constituent; not re-cut.
- **Screen 2025** (keeper-2 recipe + topology; P0 108.0 s / P1 35.9 s, 211.9 s total, 4.93 GB): **N↔OK at bound
  2,061 h (23.5 %), 1,920 N→OK / 141 OK→N (93.2 %) — live, PASS** (SPP-57's union pipe: 215 h); **OK↔S 0 h — STOP**;
  OK−N +1.77 (sign match vs +0.15); **S−OK 0.00 vs +11.29 — STOP**; **re-curtailment 0.00 % — STOP**; **unserved
  444.3 MWh in 2 h (h8507 243.0 + h8508 201.3, SPP-South) vs the control's 89.3 in h8507 — STOP (new hour)**;
  fuel families in band (hydro vs the reference's 0.02 defect, R-15, not a miss). Load-weighted $30.54 (control
  $29.97); negative hours 4 (control 6; measured ~1,018); CC −3.4 / ST_GAS +2.2 TWh vs control.
- **The structural result:** the model's residual South EXPORTS into Oklahoma in every hour above the median (OK↔S
  flow p50 −1,188 / p1 −4,682; OK→S max +3,133), while the `sps_tie` identification is OK→S-loaded (the ties bind
  on imports INTO the Panhandle; measured S−OK +11.29). No OK→S-named rating ≥ 3,400 can be live in its own
  direction; at ~3,400 the link would be live 638 h, all S→OK, and fail the direction leg. The residual bubble
  (SPS wind + SWEPCO thermal on one copperplate) is the defect — routed to SPP-54 (R-17), re-ranked ahead of any
  third re-issue; the unserved rise to SPP-54 / desk (R-18); the ψ width to SPP-58 (R-20).
- Records: solve path restored byte-identical to `origin/main` (`solve_surface_register --diff` 0 moved; persisted
  identity green); the three-zone implementation under (B′) is the branch's design commit `7bfe047d`. Matrix
  shard: `measured_interface_limits` stays O, SPP-57b evidence appended. Rule 22: 2025 only, training tier.


## 2026-09-07 — spp-6: keeper-2's recipe re-solved on the SPP-41 screened wind input — REGISTERED, **NOT PROMOTED** (the pre-declared rule stopped)

**Result: `2026-09-07-spp-3-screened-input` registered; `keepers/SPP.json` UNTOUCHED; keeper-1 and keeper-2
NOT pruned. Determination NOT-YET on the same four criteria as keeper-2.** Record:
`docs/handoffs/PRECOMMIT-spp-43-2026-09-07.md` (pushed at `623184f3` before the solve) +
`FINDING-spp-43-2026-09-07.md`. Control = `spp42_crosswalk_B` (rule 29(b) form 4; G-DRIFT from its sha
`33034499`: 11 files, all hunks INERT except the SPP-41 seam, LIVE for SPP 2023 only — `backcast_config.py`'s
five coal keys are keeper-2's OWN recipe, already in its committed `run_config`). Rule 29(a): the object
exists in one year, so the screen and the full span are the same solve (exemption stated ex ante).

- **The recipe is keeper-2's, machine-verified, not asserted:** 0 differences across 289 `meta.json` keys
  outside provenance and 0 across all 820 `run_config.scenario_config` fields. Of eight shared-input
  fingerprints exactly one moved — `eia930 facff98b252a → 017f3b3531c0`, the seam, isolated.
- **Zero-LP phase 0 (in the PRECOMMIT):** table 0b reproduced to the digit — 2023 wind 106,634.4740 →
  103,048.7595 GWh the only mover; LP bound 114,082.7166 → 114,055.2406 (**−27.4760 GWh**); a 27-array
  identity census moved `wind_cf` and nothing else in 2023 (**one hour**, h3907, −27,476.0 MWh) and
  **nothing at all** in 2024/2025.
- **THE STRUCTURAL RESULT.** SPP's wind bound is the delivered EIA-930 series grossed up by the SPP-32
  measured reference curtailment rate **0.096501** (factor **1.106808**, year-invariant, both legs measured
  from two independent SPP publications) with **0.0 % LP re-curtailment**, so `model/delivered` **must**
  equal 1.10681 every year. Before: 2023 **1.06985** (dev 0.03696), 2024/2025 exact. **After: all three
  exact to five decimals (dev 0.00000).** The seam restores a construction identity in exactly the year the
  artifact sat in — measured without reference to any residual.
- **C1/C4-2023 wind, SCORED for the first time** (discharging the "UNSCORED pending SPP-41" lines): model
  114.052 vs actual 103.049, **+10.68 %** — the same +10.68 % 2024 and 2025 already read. Wind is a
  delivered-pinned row, excluded from the C1 gate and from skill claims, so this is a consistency
  statement, not a pass/fail.
- **Bench (SPP-41 §8 R-10, discharged):** `bench/SPP/2023` wind **106.634 → 103.049** — the screened
  EIA-930 value, i.e. the run-side 0.90 completeness test still fires (not the EIA-923 total 102.1214) —
  and `classFull` **288.201 → 284.616**. **The wind class alone moved**; the other 16 classes are
  byte-identical and 2024/2025 parts are unchanged. R-10's "spread across fossil classes" reading is wrong.
- **Scorecard: unchanged from keeper-2 in every cell.** C1 FAIL (2024 CC_REGULAR −8.60 / CT_PEAKER +9.94
  only; every 2023 class in band), C2 PASS, C3a FAIL 2023 +14.1 %, C3b FAIL 0.239 / 0.229, C3c FAIL
  0 / 3 / 1 h vs 42 / 59 / 68, C4 / C6 / C8 PASS, C5a −3.1 / −3.3 / +1.2 %. That is the honest reading:
  27 GWh in one hour of one year cannot move a criterion, and the repair's justification is rules 13/14 and
  the identity above, never the residual.
- **WHY NO PROMOTION.** The PRECOMMIT's promotion rule required, as leg (i), that the **2024 and 2025 P1
  objectives be IDENTICAL to keeper-2's**. They are not (2025 P1 −150,671,250.73 vs −150,674,071.8, +2,821
  = 1.87e-5; keeper-2's 2024 P1 objective was never recorded at all). Legs (ii), (iii) and (iv) are all MET
  — 2023 moves only where wind can move it, nothing flips PASS → FAIL in either direction, and the DOF
  ledger is unchanged at 3 entries / 1 residual / 0 tuned scalars. The mover is **named, not hidden**: the
  2024/2025 **P0** objectives are identical to the cent and every LP input array is byte-identical, so the
  LP is provably the same; `P1 basis seed: ON` carries 2023's genuinely-changed basis across years and a
  degenerate LP lands a different vertex of the same optimal face (1–2 GWh on 291/302 TWh, prices within
  0.0015 $/MWh). But leg (i) fails as written, and re-cutting a gate after seeing the result is what
  rules 1 and 29 forbid — so the lane registered and stopped, as its own rule directs.
- **The card the desk owes (R-16):** may an SPP keeper's committed 2024/2025 numbers move to a different
  vertex of the *same* LP when the recipe is byte-identical and only 2023's input changed? Yes → spp-43 is
  keeper-3 and one registration prunes keeper-1 + keeper-2. No → keeper-2 stands and spp-43 is a registered
  non-keeper carrying the repaired 2023. **Until then SPP's dashboard carries three runs — a stated,
  deliberate overhang against rule 15's keeper-only retention, not an oversight.**
- **Zero-LP reports delivered, neither applied:** (a) **R-15** — the reference's SPP 2025 hydro is the
  EIA-923 preliminary **0.0233 TWh** because `_incomplete_renewable_fuels` iterates the literal tuple
  `("wind","solar")`; hydro's ratio 0.0026 is the worst of the three yet it alone is left unswapped, even
  though SPP is declared first-order in `_EIA923_EXTRA_FUELS_BY_ISO`. The proposed one-rule, zero-parameter
  repair reaches **5 cells in 4 ISOs** (SPP/MISO/NEISO 2025 hydro, NEISO 2025 oil, **NYISO 2023 oil**), so
  it is a shared-file desk card. (b) **plant 6193 = Harrington** IS in the EIA-860 SWPP fleet — three units,
  1,018 MW, SPP-South — carried as **`gas_st`**, and there is **no crosswalk row** because the derive
  classifies the fleet's coal set and 6193 is not in it. EIA-860 **vintage_2023 has all three units `SUB`
  coal**; vintage_2024 converts unit 1 to `NG`. A mid-conversion station whose fleet fuel type tracks
  neither vintage — a fleet-population question, and repairing it would *widen* the C1-2023 ST_GAS gap.
- Rule 28(b): **no cell moved and the shard was not stamped** — no mechanism was tested (the `run_config`
  diff against keeper-2 is empty). Rule 22: 2023–2025 only; SPP holds no marker. Rule 29(c): nothing owed —
  no screen or control bundle was produced.

**OWNER RULING, in-session (the card this entry raised as R-16), verbatim:** *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress that may still be a
keeper."* **PROMOTED to the THIRD SPP KEEPER `2026-09-07-spp-3-screened-input`.** The ruling's conditional is
not reached: no gate regresses at all (the determination is identical in every cell) and structural
integrity strictly improves. The leg-(i) finding is not withdrawn — keeper-2's 2024/2025 P1 objectives are
genuinely not reproduced, and stopping rather than re-cutting the lane's own gate was right; the owner was
the party to decide. Executed: `keepers/SPP.json` re-keyed; **keeper-1 and keeper-2 PRUNED** (rule 15
keeper-only retention — SPP now carries the designated keeper alone), with **no `--force-uncite` and no
dangling citation** (the shard names its predecessors by lane and FINDING, and the SPP-42-local
`keeper_previous` field, read by no script and carried by no other ISO, was dropped); `status/SPP.js`
rebuilt; the SPP matrix shard's keeper + gates stamps updated with **no cell verdict moved** (no mechanism
was tested). Gates re-run green after the promotion: `audit_keepers --check` PASS,
`check_registry_payload_parity` OK (19 runs, 52 bundle dirs), `check_mechanism_matrix` 0,
`check_bench_freshness` 0 STALE, `check_golden_manifest` OK. Remaining rubric failures are inherited and
untouched: the 2024 CT/CC/ST gas split (C1, C3a-2023) and the price-shape family (C3b / C3c / spread /
negative hours).


## 2026-09-07 — spp-7: SPP-44 SPP gas commitment bridge (`spp_gas_commitment_bridge`) — rule-29(a) screen (2023) KILLED at the STOP gate

**Result: KILLED — not a keeper candidate; full span not spent; nothing registered; the field landed default-off.**
Record: `docs/handoffs/PRECOMMIT-spp-44-2026-09-07.md` (pushed before any solve) + `FINDING-spp-44-2026-09-07.md` +
`docs/handoffs/spp44/`. Control = keeper-2 for 2024/2025 and, because the SPP-41 seam is LIVE for 2023 (G-DRIFT
hunk 6), a flag-free 2023 re-solve of keeper-2's recipe at HEAD for the screen year (rule 29(b)'s LIVE-hunk
clause; measured dispatch effect of the seam: wind −25 GWh, every criterion row unchanged). Both bundles deleted
before the PR (29c); every number is in the FINDING.

- **Measured (zero-LP):** CAMPD 2023–2025 plant-basis min-load CC_REGULAR **0.209** / ST_GAS **0.090** (per-unit
  0.440 / 0.266 reported, not used — caiso-135 basis adjudication); min-run cap-wtd p25 **15 / 5 h**; LOYO folds
  within ±0.013. Rule-18 census on keeper-2's fleet: 23 CC + 31 ST_GAS plants clear the gate (min-down 4–12 h,
  $35–50/MW); every CT row fails on its 1 h min-down. Footprint 4,209 / 1,545 / 2,656 GWh → screen year 2023.
- **Screen 2023** (P0 identical to the control's by construction; P1 obj −31.53 M → −30.27 M): the bridge fired —
  7,091 unit-hours, **0.414 TWh** of floor (CC 0.355 / ST 0.059), 1,019 segments none > 24 h, D-2 forced share 0.5 %
  on both classes; the commitment-real screen dropped 62 % / 78 % of the CC / ST P0 runs as phantom. **STOP on (i)**:
  CC window agreement with CAMPD 0.694 vs a 0.76 bar (chance 0.660; ST_GAS 0.968 passes). **STOP on (iii)**: D-4
  unit-conduct FAIL at five laid-up plants (CC 201 / 3604 / 8000 / 55178, ST 3485). (ii) pass: ΔE(CC+ST) +0.180
  TWh inside [0.104, 0.829]; CT −0.044 = "CT not displaced" (coal −0.124 is what the floor displaces). (iv) pass.
- **Structural reading:** a bridge can only refuse to stop a unit the model started; SPP's gas split is units the
  model never starts (ST_GAS at zero in 5,914 h where the real fleet holds ~835 MW). Routed R-17 (the object → the
  band channel or a measured commitment-STATE input, new PRECOMMIT), R-18 (lay-up membership prerequisite), R-19 /
  R-20 (to SPP-43).
- Records: seven keeper keys unmoved; solve surface 0 moved; matrix row + 7 cells; SPP cells
  `spp_gas_commitment_bridge` and `gas_commitment_bridge` U → R; `keepers/SPP.json` untouched.

## 2026-09-07 — spp-8: SPP MERIT-ORDER / MHR rotation — **BOTH candidate arms REFUSED at phase 0, ZERO LP spent**

Lane SPP MERIT-ORDER (Opus), branch `claude/spp-merit-order-mhr-rotation-cbx1pu` off `origin/main`
`e042a9f5`. **PRECOMMIT `docs/handoffs/PRECOMMIT-spp-merit-order-2026-09-07.md` and FINDING
`docs/handoffs/FINDING-spp-merit-order-2026-09-07.md` pushed BEFORE any LP — and no LP followed.**
Control = keeper-3 `2026-09-07-spp-3-screened-input` / `spp43_screened_B` (`git_sha 623184f3`), rule
29(b) form 4. **`keepers/SPP.json` untouched; no bundle created, none registered, nothing to prune.**

- **G-DRIFT re-run from 623184f3 → ALL HUNKS INERT, all three years.** 13 files, two mechanisms:
  `spp_gas_commitment_bridge` (SPP-44 — its P1 hook returns `None` unless the field is set AND
  `iso == "SPP"`; default `False`, absent from the keeper's recipe) and
  `ercot_zonal_spread_ep_referenced` (ercot-255 — new bool, default `False`, ERCOT-only basis code).
  Form 4 is now valid for **2023 too**: the price-family lane's one LIVE hunk (the SPP-41 seam) is
  *inside* keeper-3. No control solve earned, none spent.
- **Target, reproduced on keeper-3:** steepening `MHR(>95pct)/MHR(25-75pct)` measured **2.3375 /
  2.0993 / 2.1069** vs keeper **1.5620 / 1.5163 / 1.6187**; the model is **+29.0 / +25.5 / +13.8 %**
  too dear in the middle and **−13.9 / −9.4 / −12.6 %** too cheap at the top. A rotation, not a level.
- **Phase 0, zero LP, on-recipe `fleet_only` rebuilds + the keeper's committed hourlies.** Every SPP
  band multiplier is **1.0**, so a plant's four tranches are **price-identical**. Two consequences:
  (a) **`pct_peaking` is INERT on price by measurement** — CT 7.0→40.0 and CC 8.0→30.0 move the LP
  supply curve by **3.83 MW** and total pmax by **5.16 of 59,613 MW**, killing the handoff's arm 2;
  (b) any marginal-*band* statistic is degenerate and is used as evidence nowhere.
- **Who is marginal** (two identifications, agreeing; Method A median |mc − price| = **$0.0000**,
  99.3–99.5 % within $0.50; Method B cap-weighted over every row within $0.25): **CT_PEAKER is the
  marginal class in 24–27 % of MEDIAN-load hours** and 49–60 % of top hours; coal ≈ CC ≈ CT each
  ~25 % at mid load. **That overlap is what bounds every offer lever** — a per-class multiplier lifts
  the middle nearly as much as the top.
- **And the middle is not an offer object:** at mid load the model leaves **3,084 / 3,725 / 2,829 MW**
  of *available* coal and **3,271 / 2,898 / 3,261 MW** of *available* CC idle (util 0.51–0.75) while
  dispatching 1.9–2.7 GW of peakers.
- **ARM A — `tranche_startup_amortization` + v3 `tranche_startup_measured_runs`: REFUSED.** Rule 19
  ADMITS it on SPP by the exact test that refused it on ERCOT (ERCOT-145 §1: fitted CT margins
  +$13/+$35/+$292–451 vs a $2.9–4.0 measured amortization = stacking; **SPP's same rows carry
  $0.00**). SPP's own artifact derived and committed: `campd_ct_run_lengths_SPP.csv` — 51 facilities
  / 138 units / **50,460 measured runs**, class-fallback median **9.0 h** (SPP's CTs run longer than
  every other ISO's: NYISO 4, CAISO 4, ERCOT 6, PJM 7, MISO 10 h). Footprint 384 rows /
  **11,600–11,631 MW**, max markup **$2.14/MWh** cap-wt on CT econ+peak. At that MAXIMUM the ratio
  moves **+0.147 / +0.676 / +1.008 %** against a pre-registered **≥ +10 %** — STOP by 10–68× — and
  the LEVEL moves the wrong way (×1.0230 / ×1.0228 / ×1.0188). Granting the un-computable CC-peak
  leg a 9 h (or 4 h) horizon turns rotation **negative in two of three years**.
- **ARM B — the PER-CLASS differentiated offer curve: REFUSED, and the price-family lane's open
  question is CLOSED.** Derived by one declared rule from SPP's own realized prices: COAL_PRB
  **0.7838** / COAL_LIGNITE 0.8152 / CC_REGULAR 0.8028 / CT_PEAKER **0.8880** / CT_CHP 0.8019 /
  ST_GAS 0.8949 / ST_CHP 0.8271 — the whole set spans **0.784–0.895**, i.e. SPP's own data says the
  classes are barely differentiated (peaker-over-coal separation **+13.3 %** against a ~30 % deficit).
  Ratio **+4.006 / +2.029 / +3.312 %** against ≥ +10 %, at LW level **0.8614 / 0.8608 / 0.8522**. The
  same LEVEL lever the uniform quadruple was.
- **The gate's threshold was INHERITED UNCHANGED** from the price-family lane's pre-registered G-2
  (ratio must rise ≥ 10 % of control), so it cannot have been cut to fit. The zero-LP **re-clearing
  predictor** was **VALIDATED against that lane's SOLVED 2025 arm**: LP-measured LW −9.05 % vs
  predicted −8.11/−9.12 %; LP-measured rotation +0.52 % vs predicted +2.09 % — i.e. the instrument
  **OVER-STATES rotation ≈ 4×**, reported against interest, and the bias can only make the gate
  easier. Self-check is strict: only the **25.9–28.6 %** of hours where an all-1.0 reconstruction
  returns the keeper's own price EXACTLY are retained.
- **Reported at full magnitude, routed not fitted:** wind **+11.00 / +11.67 / +11.80 TWh** over
  actual (the largest single class error); `CT_PEAKER` **+6.78 / +10.06 / +11.06** with `ST_GAS`
  **−7.49 / −5.12 / −10.27** and `CC_REGULAR` **−4.26 / −8.24 / −10.19**; and the NEW measured lead —
  SPP's ST_GAS fleet pays a **+29.3 % / +0.1 % / +7.9 %** delivered-gas premium over the CT fleet
  (model fuel $4.149/2.930/4.118 vs $3.210/2.927/3.818 per MMBtu) and its under-run tracks it. That
  is a rule-14 `[R-ACCURATE]` question about `gas_plant_monthly_fuel_pricing`, not this lane's channel.
- **Checked, not assumed:** `energy_reserve_coopt` cannot be armed for SPP —
  `model/reserves/spec.py::get_reserve_design` raises `ValueError` for SPP. The whole
  AS-opportunity-cost layer is structurally absent, and it is the strongest routed lead for the
  top-of-stack leg (SPP publishes its own RTBM reserve MCP, `data/raw/spp-or-mcp/`, 2023–2025).
- **Records:** SPP shard cells `tranche_startup_amortization` **U → R** (covers v2+v3; v4 stays `U`,
  never part of the arm) and `offer_curve_by_group` **R evidence widened** from "uniform quadruple"
  to any per-band or per-class multiplier set. `campd_ct_run_lengths_SPP.csv` committed (rule 23, the
  ERCOT-145 precedent). Rule 29(c) has nothing to delete: no screen ran.

## 2026-09-07 — spp-9: SPP-58 ψ₂ — the second, independent shift-factor identification (zero-LP): OUTSIDE the band on every object; `ttc_mw` untouched; card served

**Result: no keeper touched, no solve, no value edited.** Record: `docs/handoffs/PRECOMMIT-spp-58-2026-09-07.md`
(pushed `da1bb516` before any PTDF) + `FINDING-spp-58-2026-09-07.md` + `docs/handoffs/spp58/` (the reduced DC
network, the element map, ψ₂ per constituent, the aggregates).

- **Construction:** ψ₂ = DC PTDF (OTDF where the contingency resolves) on a reduced network from public HIFLD
  line geometry (17,873 features, 2023 vintage) + EIA-860 plants, generator-weighted bubble pairs; price-free.
  Option (a) unavailable (no flow column in the served RTBM schema; no measured intra-BA interchange), option (b)
  absent (the Public Data Guide v35 lists no shift-factor product). Interconnection cleaning (owner + geography +
  ERCOT CREZ station list + tie cuts) verified by EIA-860 BA codes: only Kiamichi and Denison Dam remain ERCOT-coded
  in the Eastern component. K1–K4 hold (cut-set identities 1.000; line sign agreement 7/8).
- **Verdicts (band = 1.92×, declared ex ante):** N→S like-for-like T*₂ 11,022 vs T*₁ 4,919 on the same subset and
  vs the standing 3,400 — OUTSIDE (ψ₂ lands on ψ₁'s drop-2024 fold, 11,121); S→N 13,175 vs 4,206 — OUTSIDE;
  `sps_tie` **1,600 vs 10,705** — OUTSIDE the other way (the ties are the cut-set, ψ ≈ 1, T* ≈ limit-at-bind).
  Potter County width COLLAPSED (ψ₂ 0.369 / 0.311 = 1.19; OTDF > PTDF, the reverse of ψ₁). Double attribution of
  the western-Oklahoma elements is REAL physics (loaded by both transfers). Franklin 161/69 — 44 % of the corridor's
  hours and ψ₁'s median — is UNRESOLVABLE (no sub-115 kV public line data).
- **Structural reading:** ψ₁ assigns the 115/161 kV under-lay elements sensitivities (0.035–0.365) the topology does
  not support (≤ 0.026, mostly ≤ 0.005); the 345 kV backbone elements agree in sign and order. Sensitivities
  (transformer X ×0.5/×2, inner box) move no verdict; a wind→gas transfer composition moves ψ₂ toward ψ₁.
- Routed: R-21 the card (both identifications side by side; `ttc_mw` stays 3,400 by the rule), R-22 SPP-54's rating
  input 1,600 MW, R-23 a 69 kV under-lay source, R-24 a proper HIFLD intake, R-25 the cleaning rule as record.
  Rule 28(b): no mechanism tested, no cell moved; `measured_interface_limits` evidence appended (stays O). Rule 22:
  2023–2025 weights only.

## 2026-09-07 — spp-10: SPP-55 VRL-based scarcity as an in-LP Contingency Reserve demand curve — KILLED AT ZERO LP at the pre-solve half of the STOP gate (INERT)

**Result: KILLED — no solve spent (rule 29 step 0); not a keeper candidate; nothing registered; the SPP reserve entry
landed default-off under the existing `energy_reserve_coopt` gate (no new field).**
Record: `docs/handoffs/PRECOMMIT-spp-55-2026-09-07.md` (its own commit, before the implementation) +
`FINDING-spp-55-2026-09-07.md` + `docs/handoffs/spp55/`. Control = keeper-3 (G-DRIFT `623184f3` → HEAD all-INERT).

- **The object, from SPP's own protocols (not the VRLs):** the Contingency Reserve Demand Curve — scarcity factor
  0.25 / 0.5 / 1.0 × (Safety-Net Energy Offer Cap $1,000 + Contingency Reserve Offer Cap $100) = **$275 / $550 /
  $1,100 per MW** (Protocols v119 §4.1.5(1)(a) / §4.1.5.2); the posted RTBM Supp MCP is exactly one of those three
  values in every 2023–2025 short interval and the Spin MCP maxima are the curve + the $250 spin VRL stacked on it.
  Requirement = 0.964 × 1.2 × hourly MSSC (RSG Operating Process 0820EXT00002 §4.1–4.3: largest single unit ≥ 600 MW
  × availability; Wolf Creek 1 → 1,500 MW vs posted cleared medians 1,514 / 1,484). Six published constants, one
  MEASURED share, zero tuned. One BAA-wide family, MISO-RBDC form (`model/reserves/spec.py::_spp_design`).
- **Measured footprint (zero LP):** 140 / 117 / 109 five-minute short intervals in 68 / 45 / 37 events of median length
  ONE interval; 4 / 3 / 7 hour-long shortage hours; **1 / 0 / 0 of the 42 / 59 / 68 C3c hours coincide with any reserve
  shortage** (shortage hours price at a median $32–36; the tail is RT-only and mostly system-wide).
- **Pre-solve gate:** keeper-3's reserve-eligible headroom (min 2,884 / 1,169 / 2,399 MW; p1 6.3–7.0 GW) is below the
  requirement in **0 / 1 / 0** hours and in **no** measured shortage hour (3.4–17× the requirement there) → leg (i)(a)
  = 0.00 in every year; the row cannot bind where SPP posts shortage. INERT; the screen year (2025, named ex ante) was
  not solved. A ~10-minute verification solve is offered to the desk, not run.
- **Structural reading:** SPP's reserve scarcity is a 5-minute ramp/capacity object an hourly perfect-foresight LP
  without a deliverability bound clears out of 6–18 GW of slow-unit headroom (miso-38 gate 4 on SPP's own data) —
  making the family LIVE is SPP-56's deliverability question (R-22); C3c is a 5-minute RT price-formation object no
  hourly lever reaches (R-21, the ledgered model-class caveat). Routed R-21…R-25.
- Records: cell `energy_reserve_coopt` U → **I**; three cells annotated, not moved; §5.7 item 5; plan §5 / §9 rows;
  `keepers/SPP.json` untouched; 0 new fields, solve surface 0 moved, every keeper key unmoved by construction.

**Next shorthand: spp-11.**


## 2026-09-07 — spp-11: SPP-54 SPS / Texas-Panhandle pocket (third zone) — DESIGN LANDED on the branch; the R-18 wind reconciliation STOPPED before any solve; the link rating WAITS for SPP-58

**Result: NO SOLVE SPENT — not a keeper candidate (nothing to grade); design complete on the design commit `8d427adc`;
topology NOT landed on main (solve path restored byte-identical, the SPP-57/57b posture).** Record:
`docs/handoffs/PRECOMMIT-spp-54-2026-09-07.md` (pushed at `c9742b58` before any limit, ψ, price or flow was read) +
`FINDING-spp-54-2026-09-07.md` + `docs/handoffs/spp54/`. Control = keeper-3 `spp43_screened_B` (rule 29(b) form 4;
G-DRIFT `623184f3` → `9708d69e`: 13 files, all INERT — SPP-44 default-off, ercot-255 ERCOT-only, two surface
declarations; solve surface 0 moved).

- **Design (A), the pocket:** `SPP-SPS` = NM whole + a 42-county SPS Texas set (26 Panhandle + 15 South Plains +
  Gaines; the T/D-owner field read as corroboration only: 10,156 of 12,167 MW report SPS); residual `SPP-South` = OK +
  AR + LA + SWEPCO/PSO Texas; `SPS → SPP-SPS` on the load side with NO sub-allocation (its own EIA-930 token; CSWS
  whole). Static shares **0.5125 / 0.3616 / 0.1259** (SPS 0.1251 / 0.1266 / 0.1260 by year); hourly Σ = 1 to 2.2e-16.
  Census on keeper-3's recipe (2025): SPS 19 plants / 84 units / 6,799 MW thermal (gas 5,715; Tolk coal 1,067) +
  4,654 MW wind (18.05 TWh) + 284 MW solar against 38.06 TWh (3,345–6,368 MW) — thermally self-sufficient at peak,
  an exporter overnight; B_plaus SPS 2,676–3,054 / South 10,476–11,953 (→ **R2 = 10,476 MW**: the record's SPP-57-ψ
  reading 10,700 would fail it; the ITP-interface readings 3,602 / 3,850 pass).
- **Design (B), the link:** ONE `SPP-South ↔ SPP-SPS` link, positive = South→SPS = into the Panhandle; named
  direction South→SPS from the `sps_tie` set's own binding direction, and — unlike SPP-57b — NOT in conflict with
  the bubble's balance (the pocket's scarce hours are import hours; its export never reaches 3,400). Rating rule =
  SPP-53's FCITC median over the `sps_tie` set with SPP-57's L_f / hours and **SPP-58's ψ₂** (R-20). **Not filled:
  SPP-58 has not landed**; `_spp_config` carries the slot, the rule and a "must not be solved" note (SPS is an
  island until then).
- **Design (C), the SPP-57b R-18 reconciliation — the lane's result:** C-1 identity Σ_z cap·cf = delivered ×
  1.106808 to **6e-16** every hour, all years; C-2 no overflow lost; **C-3 STOP at h8509** (2025-12-21 13:00): the
  South+SPS region's margin **+440 MW (two-zone wind) → −545 MW (three-zone)** at identical demand, availability and
  3,400 MW import, through the regional wind potential 1,807 → 821 MW. C-4 attribution: the North's annual potential
  rises **+1.38 / +1.47 / +1.91 TWh** under the split, **75–85 % from the residual South's own six-site sample
  changing** (Oklahoma-only vs the old mixed OK+Panhandle six), NOT from the SPS shape (−0.56 / −0.55 / −0.74). The
  builder's six-site MEAN LEVEL is load-bearing in the redistribution — R-18's mechanism, measured. Not repaired
  in-lane (rules 23 / 29); routed **R-21** to the desk (candidate: a zone's level from its whole fleet, zero DOF).
- **Design (D):** every registry gained `SPP-SPS` (config, zone map + coordinate limb refined for the OK Panhandle
  strip, crosswalk, fallback allocation, gas-basis TX rows re-keyed to SPS, reference renewables block, wind parquets,
  `iso-topologies.json` — which also corrects the 48,700 SPP-53 left there), tests (145 SPP + 965 related green);
  `solve_surface_register --diff` 299 → 299 **0 moved**; persisted identity 24/24; parity OK; `audit_keepers` PASS;
  `check_mechanism_matrix` 0. All of it is `8d427adc`; the branch's final state restores the solve path (and the
  three-zone parquets, which the two-zone loader would silently accept) to `origin/main` bytes.
- **Not done, by rule:** no rating on the SPP-57 ψ table; no solve without a rating; no solve past the C-3 STOP; no
  builder change after its result was seen; nothing registered; `keepers/SPP.json` untouched. Rule 22: nothing solved.
- **SPP-58 landed during the merge rebase (FINDING Addendum A):** its one line for this lane is T*₂ = **1,600 MW**
  on the South-rest → SPS pair (LOYO 1,618–1,636; passes R2 / R3 / R4 with room; band verdict OUTSIDE vs ψ₁'s
  10,705, the card pending) — recorded, not written into `_spp_config`; the solve stays blocked by C-3.
- Routed: R-21 (builder level rule → SPP-DESK card, gates every three-zone SPP solve), R-22 (`SPSNMTIES`
  membership → SPP-58), R-23 (R2 = 10,476 → SPP-58 / the follow-up), R-24 (gate leg (iii) sign for an importing
  pocket → desk), R-25 (`iso-topologies.json` staleness → site). Matrix shard: `measured_interface_limits` stays O,
  SPP-54 evidence appended (no mechanism tested, rule 28(b)).


## 2026-09-07 — spp-12: SPP-51 priced seams (MISO / AECI / ERCOT, cards P2/P3) — three adjudications LANDED; arm KILLED at rule-29 PHASE 0 on the measured record, NO LP spent

- **Lane** SPP-51 (Fable) · `docs/handoffs/PRECOMMIT-spp-51-2026-09-07.md` · `FINDING-spp-51-2026-09-07.md` ·
  control keeper-3 (`623184f3`, G-DRIFT all INERT). **No solve, no bundle, no registration, keeper untouched.**
- **Adjudications (spec.py SPP list only; producer; tests):** (a) SPP-33 R1 — `derive_neighbor_hr_by_year.py`
  anchor map is now PER ISO (`NEIGHBOR_LMP_ANCHORS`), SPP anchored on MISO-West / MISO-South zonal rows, SPP hub
  (declared PROXY) and ERCOT system; an ISO with no map or a declared anchor with no rows FAILS, an unanchored
  neighbour is printed (was: one wrong-anchor row, two seams silently dropped); PJM/MISO tables byte-identical.
  (b) SPP-33 R2 — the seam multiplies `(HH + gas_basis) × HR`; flat HRs re-built on that construction as the mean of
  the measured `hr_by_year`: MISO split into `MISO_West` 10.12/11.02/10.52 (flat 10.55, 3,550 MW → SPP-North) and
  `MISO_South` 9.52/10.09/9.28 (9.63, 2,450 MW → SPP-South; split = measured tie |flow| share 59/41 on SPP's own
  meter), AECI 10.30/12.08/8.32 (10.23), ERCOT 23.70/15.87/10.76 (16.78); the legs' equal-weight mean reproduces
  SPP-33's 9.82/10.55/9.90 exactly. (c) ERCOT limit 820 → **835 MW** (rule 14: the measured clip on EIA-930 and
  SPP's own meter, corr +1.0000, all three years; misalignment stated; ERCOT's own row untouched).
- **Blocker found:** SPP has no `IMPORT_ZONE` / `IMPORT_NODE_LINKS`, so `--priced-interchange` builds NO seam at
  HEAD and only drops the served schedule; the one-bus repair is a free wheel around the SPP-53 3,400 MW corridor
  (the `split_miso_south_external_node` defect). Two-bus topology designed, ROUTED (R-a), not built.
- **Phase 0 (rule 29(0)):** screen year **2024** named on footprint (gross 9.706 TWh through the three seams).
  Pre-solve gate P0-b, declared before computed: MEASURED SPP hub − MEASURED anchor, hurdle ±2, vs the EIA-930
  direction, ≥ 0.55 non-hold sign agreement on the MISO seam. **FAIL**: MISO_West 0.485/**0.436**/0.479,
  MISO_South 0.501/**0.482**/0.484 (RT; DA the same), corr(spread, import) ≈ 0; ERCOT 0.56–0.61 (weak pass,
  cannot be armed alone under the all-or-nothing switch); AECI degenerate (anchor = SPP's own hub — keeper-3's
  price residual over the hub would become 5–19 TWh/yr of seam import by construction). The SPP↔MISO seam is a
  spread-blind schedule — miso-233's own reading from the other side (corr +0.041/−0.020/+0.050). **Killed;
  the ~150 s screen deliberately not spent.** Residual-blind: no C3a/C3b/C3c read.
- Records: seven keeper keys unmoved by construction (`spec.py` outside the solve surface; no `ScenarioConfig`
  change; cache-key + solve-surface tests green); MISO's SPP-seam constants untouched (hunks confined to the SPP
  list); SPP cells `priced_interchange` / `reference_price_interface` U → R (fc U); plan §5 row LANDED;
  `keepers/SPP.json` untouched; **NO P15 candidate**. Routed: R-a topology, R-b the schedule-shaped seam form
  (miso-233 mirrored from SPP's side, or ERCOT-only priced), R-c elasticity keys (R3), R-d ERCOT-side 820 vs 835.

**Next shorthand: spp-13.**

## 2026-09-07 — spp-13: SPP-46 the C1-2024 gas split — BOTH R-17 candidates KILLED at rule-29 PHASE 0, ZERO LP; the object is a measured-input plausibility defect on three seams (EIA-923 own-month prices, plant-level eGRID heat rates, Harrington's fuel vintage) + a self-commitment residual — ROUTED`

- **Lane** SPP-46 (Fable) · `docs/handoffs/PRECOMMIT-spp-46-2026-09-07.md` · `FINDING-spp-46-2026-09-07.md` ·
  `docs/handoffs/spp46/` · control keeper-3 (`623184f3`, G-DRIFT 7 hunk groups all INERT). **No solve, no bundle, no
  registration, keeper untouched, no field / constant / parameter added.**
- **Phase 0.1 (CAMPD census):** the CT over-run is mid/low-load (2024: 6.5 / 3.2 / 1.3 TWh mid / low / top-decile);
  the ST_GAS committed-state footprint is 2.4 / 0.3 / 1.0 TWh against 8.0 / 5.1 / 7.9 TWh under-runs, ≤ 0.44 TWh of
  it in never-started hours.
- **Phase 0.2 (keeper-3's own arrays):** CT and ST_GAS dispatch sit on their own mc (0 ST_GAS hours outside the
  in-merit band); the 2024 CT over-run sits ~entirely on rows whose OWN input is implausible — Pioneer 57881 eGRID
  heat rate 3.43 (+5.0 TWh), Elk / Mustang 4 / Mustang CC at $0.11–0.41 and NEGATIVE own-reported gas (+8.1 TWh) —
  while the 110 clean CT plants reproduce to −0.24 TWh; ST_GAS: Harrington 1,018 MW as $1.48 gas steam while CAMPD
  burns coal (+5.8), Muskogee / Seminole / Riverside on low-volume $7–72 months (−3.8), the clean OG&E / PSO / SWEPCO
  steam cohort −5.9. SPP-state EIA-923 gas frame: 91 plant-months ≤ $0.50, 31 negative, 206 ≥ $10 of 5,707; no
  screen at the seam.
- **Adjudication:** (A) P0-anchored online-hours leg reach ≤ 0.25 of the gap (over-bound) — KILLED; measured-state
  form fails rule 13 — INADMISSIBLE. (B) reach needs CT ×2.0 / ST ×0.6 / CC ×0.7 (±6–17 % level; derived set moves CT
  0.00) and would compensate the input defect — KILLED / REFUSED (rule 14, playbook §6.2). Screen not reached.
- **Routed:** SPP-46 R-1 (F923 own-month plausibility screen [0.5, 2.0] × N3045 state reference; predicted 2024
  CC +4.3 / CT −4.2 / COAL +4.0 / ST −4.2 (Harrington) at +3.2 % level), R-2 (CT physical HR floor, Pioneer),
  R-3 (`egrid_family_heat_rates` for SPP, Northeastern / Earl F Wisdom), R-4 (Harrington fuel vintage, bench too),
  R-5 (the self-commitment residual, a market-design build, re-measured after R-1…R-4), R-6…R-8 notes.
- **Cells:** `offer_curve_by_group` R (widened to the volume object), `spp_gas_commitment_bridge` /
  `gas_commitment_bridge` R (online-hours leg), `gas_plant_monthly_pricing` **U → K** (stale seed; keeper-3 arms it;
  the seam defect recorded), `egrid_family_heat_rates` / `measured_ct_heat_rates` U (named as the repairs).
- **P15:** no candidate; recommend R-1…R-4 issued before any further gas-split lever (~7 min LP for the span).

---

## 2026-09-07 — spp-14: SPP-47 EIA-923 incomplete-vintage swap loop extended to each ISO's own extra benchmarked fuels — **LANDED repo-wide, 6 cells, ZERO LP, every determination unchanged**

- **Lane** SPP-47 (Opus) · `docs/handoffs/FINDING-spp-47-2026-09-07.md` · owner ruling **P16** (r#12) on
  SPP-43 §6 / SPP-57 R-15, both **DISCHARGED**. **No solve, no bundle, no registration, keeper untouched.**
- **The change:** one executable line in `build_calibration_reference.py::_incomplete_renewable_fuels` —
  `("wind","solar")` → `("wind","solar") + _EIA923_EXTRA_FUELS_BY_ISO.get(iso, ())`. Same 0.80 threshold,
  same EIA-930 authority, same per-fuel evaluation, **zero new parameters** (rules 5/21/23 — a construction
  repair, not a re-derivation). The existing `ref <= 0.0` guard already implements "fuels EIA-930 reports",
  so MISO oil is skipped and keeps its EIA-923 value; ISOs with no extras (ERCOT/PJM/CAISO) are unreachable.
- **Cells moved: SIX, not five.** SPP-43 §6's five reproduce to the digit — SPP 2025 hydro 0.0233→**8.8299**
  (ratio 0.0026), MISO 2025 hydro 0.9697→**9.8768** (0.0982), NEISO 2025 hydro 0.0907→**5.1207** (0.0177),
  NEISO 2025 oil 0.9092→**1.2411** (0.7326), NYISO 2023 oil 0.4217→**2.1745** (0.1939). The **sixth** is
  **NYISO 2022 oil 1.8437→4.8854** (0.3774), outside SPP-43's 2023–2025 sweep: a rule-22 validation-tier
  reference block, where the 2026-08-06 amendment *requires* consistent application (data, not score — no
  2022 was solved, scored or registered). Nearest non-mover MISO 2024 hydro **0.8420**.
- **Diff, leaf-by-leaf over 6,890 leaves, three ways:** base rebuild → patched rebuild **6 changed, 0
  added/removed** (the rule, alone); committed → base rebuild **325 changed, all `CAISO.*.renewables`**
  (upstream drift from merge `5a910016`, left unbuilt under G9 — routed R-3); committed → what was written
  **6**. In-place build was `--isos SPP MISO NEISO NYISO`; every ISO block and year key preserved, no
  `*_renewable_capacity.csv` moved.
- **Determinations (committed artifacts only, no solve):** all seven keepers **UNCHANGED** and the entire
  scorer report **byte-identical** — ERCOT/PJM/CAISO/NYISO/NEISO/MISO CALIBRATED, SPP NOT-YET. By
  construction: `calibration_verdict.py` never reads this file; its live consumers are two solve-time
  *printed* tables and the gitignored `clean/validation` curation.
- **Bench freshness 0 STALE before AND after, stdout byte-identical**; `build_calibration_reference.py` is in
  neither `PAYLOAD_SOURCES` nor `BUILDER_SOURCES` and the edit is outside `src/market_sim/{data,config}`.
  **`bench/SPP/` NOT touched, no other ISO's part touched, no desk routed on item 4.** All six gates exit 0
  before and after with byte-identical output. New test `test_calibration_reference_extra_fuel_guard.py`
  (8 cases, 3 of which correctly FAIL at HEAD); suite run 3× — with the change the failure set equals HEAD's
  exactly (7, all pre-existing and out of scope); one further first-run failure was a full-suite flake that
  passed at HEAD, passed on the repeat and passes in isolation both ways.
- **Routed:** R-1 three swaps land in COMPLETE vintages (NYISO 2022/2023 report *more* than EIA-930 — a
  dual-fuel attribution disagreement, not incompleteness; gating extras on `eia923_incomplete` is a scope
  question the ruling did not put to this lane); R-2 the reference and the bench part now disagree on **oil**
  for NYISO 2022/2023 + NEISO 2025 (bench routes hydro to EIA-930, keeps oil on EIA-923 — nothing scored
  moves; reconciling means changing a bench builder); R-3 CAISO's 325-leaf renewables re-derivation;
  R-4 `regenerate_clean.py demand-profile` is a silent precondition for rebuilding this file.

**Next shorthand: spp-14.**

---

## 2026-09-07 — spp-15: SPP-48 the per-zone wind LEVEL rule repaired in the shared builder (SPP-54 R-21); no solve
Owner ruling P17 executed: R-LEVEL — each zone's wind shape is the capacity-weighted mean over its WHOLE operable
fleet, replacing the six-largest-plants subsample whose per-zone level bias was an undeclared free parameter
multiplying the redistribution's split (the six sites covered 13.8 %–100 % of a zone's capacity depending on the
zone). Shared construction expressed once in scripts/lib/wind_shape.py (no ISO name, no per-ISO constant,
test-enforced); both builders reduced to ISO wrappers; _SAMPLES_PER_ZONE deleted, not raised (rule 26); net -1 free
parameter; physics, schema, gates and every ScenarioConfig field unchanged; solve surface 299 -> 299, 0 moved.
Identity legs PASS on both ISOs, all years (Sum_z cap_z cf_z = M(t) to <= 8.7e-16; 0 lost-overflow hours; system
total moved 0.000 MW; cap_z/C_z = 1.0 in every zone). Partition consistency is exact under R-LEVEL (0.0 MW) and
violated by 15 % of annual energy / 4.6 GW in an hour under the retired rule. SPP-54's C-3 STOP DISSOLVED: 0 hours
newly infeasible, three-zone minus two-zone margin 0.000000 MW in every window hour, h8509 -75 MW in both maps
(as-built reproduced exactly at -545 / +440). Isolation proof: the retired rule regenerated over the new module is
byte-identical to the committed parquets. Deltas: SPP two-zone North +1.915 / +2.304 / +2.131 TWh (South equal and
opposite), up to 9.0 GW in a zone-hour -> keeper-3 needs a re-baseline; MISO Plains +1.4...+1.8 TWh, Illinois
-7...-8 %, up to 4.6 GW -> routed to MISO's desk. Solve path restored to origin/main's bytes; no parquet on the
solve path regenerated or committed (SPP-46 is solving against keeper-3 in parallel). Zero LP.
FINDING: docs/handoffs/FINDING-spp-48-2026-09-07.md

---

## 2026-09-08 — spp-16: SPP-49 (Fable) — BOTH INPUT-SEAM REPAIRS LANDED REPO-WIDE (owner ruling P19) — the EIA-923 own-month gas-price plausibility screen as a REGISTERED GATE (default ON, 18 armed backcast keys re-key, 0 off-target) and the simple-cycle heat-rate floor as a CONSTRUCTION; zero LP; SPP-46's attribution reproduced pre and post; SPP / MISO / PJM owe re-solves`

- **Lane** SPP-49 · `docs/handoffs/PRECOMMIT-spp-49-2026-09-08.md` (`395c9417`, before either seam file was edited) ·
  `FINDING-spp-49-2026-09-08.md` · `docs/handoffs/spp49/`. **No solve, no bundle, no registration, no keeper shard,
  status, bench, sidecar or log touched.**
- **Adjudication**: seam 1 (`plant_prices.py`) = registered gate `f923_gas_price_plausibility_screen`, default ON via the
  (b′-1) route, because a desk can legitimately want its raw series (Permian / Waha); seam 2 (`eia860.py`) =
  construction, because a sub-9.0 non-CHP simple-cycle rate has no reading (CHP plants excluded post-PRECOMMIT, rule 19).
- **Data**: EIA `N3045<ST>3` for every state + US, 2018–2026 (`data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv`).
- **Keys**: 18 move ex ante = 18 ex post, all armed backcast configs (six keepers), 0 off-target; seam 2 zero by
  arithmetic, epoch text routed (R-3).
- **SPP footprint** (2024): 60 low / 11 negative / 25 high plant-months on 19 plants; Pioneer 3.43 → 9.0. Attribution
  reproduced: Pioneer +5,013 → +1,650, CT fuel_low +8,963 → +3,223, ST_GAS fuel_low +6,136 → +1,493, clean cohorts put.
  Realised pooled re-clearing 2024 CT −8.5 / ST −4.1 / CC +5.6 / COAL +6.6 TWh at +4.7 % level; 2025 CT −8.8; 2023 CT −3.6.
- **Other ISOs**: MISO CT +3.6 / +2.5 / +1.0 TWh at −1.5 / −2.2 / −1.4 % (the HIGH tail, opposite sign); PJM small; CAISO /
  NEISO / NYISO inert on seam 1 (hub overlay / all in band); ERCOT unreachable and inert. **Re-solves owed: SPP (SPP-50),
  MISO, PJM; CAISO / NYISO on the letter; NEISO reproduces; ERCOT nothing.**
- **Cells**: `f923_gas_price_plausibility_screen` row added; SPP **K** (input path), MISO / PJM **U**, CAISO / NEISO /
  NYISO **I**, ERCOT **·**.
- **Routed**: R-1 CLI flag, R-2 the `iso_monthly_gas_prices` consumer, R-3 epoch text, R-4 Harrington, R-5 Permian
  reference, R-6 Pioneer nameplate, R-7 F923 state scope, R-8 MISO high-tail volume census, R-9 PJM pin.

## 2026-09-08 — spp-17: SPP-50 the batched re-baseline (SPP-48 wind R-LEVEL + SPP-49's two input seams) SOLVED and REGISTERED; recommend promote, served as P15
Owner sequencing ruling P19b executed: the wind re-baseline and the input re-baseline as ONE full-span
solve, so the keeper that emerges is identified against the FINAL input surface. Keeper-3's recipe
re-solved byte for byte -- machine-verified, not asserted: 0 differences across 297 meta.json keys
outside provenance, 0 across every scenario_config field present in both configs, all 8 shared-input
fingerprints unmoved; the 5 config differences are all fields that did not EXIST at keeper-3's sha (four
at default False, each classified INERT in the PRECOMMIT's G-DRIFT audit before the solve; the fifth is
the declared f923 seam gate at the P19 default True). Three inputs moved and nothing else: R-LEVEL wind
(North +1.915/+2.304/+2.131 TWh, South equal and opposite, system total 0.000000), seam 1 (fuel_prices on
484/499/482 rows), seam 2 (heat_rate on 32 rows -- the declared 21 gas CT / 1,141.8 MW plus 11 oil rows /
25.3 MW at the same IC plants). PROMOTION LEGS: (ii) wind identity MET in all three years, 1.10680 /
1.10678 / 1.10681 against the 1.106808 construction with LP re-curtailment 0.00058/0.00172/0.00030 % --
TIGHTER than keeper-3's, so the 3,400 MW seam absorbs the re-split without re-curtailing; (iii)
attribution reproduces SPP-49 0.5 TO THE GWh on every row (Pioneer -3,362.3, CT fuel_low -5,739.1, ST_GAS
fuel_low -4,642.8, ST_GAS clean +6.2) and the clean cohorts stay put; (iv) MET as written -- C2/C4/C6/C8
all PASS->PASS, DOF 3 entries / 0 tuned scalars / authorized_price_tuning NONE, and SPP-48 DELETES one
free parameter; (i) NOT MET on the letter of its own iff -- 17 of 22 LP input arrays bit-identical with
the fleet unchanged, but emission_rate moved on exactly the 21 clamped rows as the exact algebraic
consequence of the heat-rate clamp (ratio identical to 4.4e-16, inert because SPP's carbon price is 0.0).
Reported as a defect in the lane's declaration, NOT re-cut after the result. DETERMINATION NOT-YET, same
four criteria and same grade summary as keeper-3. C1 SUBSTANTIALLY REPAIRED: the two targeted 2024 rows
FIXED (CC_REGULAR -8.60 -> -2.94, CT_PEAKER +9.94 -> +1.91), COAL_PRB -4.80 -> +0.26, summed absolute
class error 31.69 -> 16.45 TWh in 2024 and 22.91 -> 15.67 in 2023, free-class 10/12 -> 11/12; ONE new
failing row, ST_GAS-2024 -5.12 -> -8.71, whose root cause is the ALREADY-ROUTED Harrington fuel vintage
(the screen removes the fake $1.48 gas, not the coal the plant burned). PRICE LEVEL WORSE IN EVERY YEAR
and reported at full magnitude: C3a +14.1/+7.5/+7.2 -> +15.0/+12.1/+14.2 % (2024 and 2025 flip PASS ->
FAIL at the year level), C3b 2025 0.189 -> 0.253 PASS -> FAIL, reported C2-2025 gas -12.6 -> -23.5 % and
coal -1.9 -> +8.1 %. The realised LP response reproduces SPP-49's ZERO-LP pooled prediction on every class
of every year (2024 CT -8.06 vs -8.46, CC +5.74 vs +5.60, COAL +5.66 vs +6.63). RECOMMENDATION: PROMOTE on
structural grounds per rule 1 -- two proven measured-input repairs, net -1 free parameter, nothing tuned,
no mechanism added -- and NOT because a residual moved; keeper-3's better 2024/2025 price level was
produced by gas at $0.16/MMBtu, which is the unreal mechanism rule 1 forbids reaching a number through.
Case against stated in full: three per-year load-bearing cells flip PASS -> FAIL, the determination does
not improve, C1 gains a gated failing row, 2025's reported C2 pair worsens on both legs, and leg (i)
misses. keepers/SPP.json UNTOUCHED, keeper-3 NOT pruned -- the promotion is card P15. Bundle is on local
disk, gitignored from the PRECOMMIT commit onward (rule 31: nothing deleted), and will NOT survive this
ephemeral container.
FINDING: docs/handoffs/FINDING-spp-50-2026-09-08.md
OWNER RULING P15 (SPP desk r#15, 2026-09-08), recorded by the desk after the lane closed: **PROMOTION
DECLINED — keeper-3 stands.** Verbatim: "I think we just open the price level and don't bother promoting."
SPP-50 remains a REGISTERED, non-promoted run on the dashboard (sidecar + payload committed; its bundle did
NOT survive the lane's ephemeral container, so no hourly/ sidecars exist and a later promotion would cost a
full ~13 min re-solve). The repaired wind parquets STAY on main by the same ruling, so keeper-3 is knowingly
carried as a keeper that does not reproduce from the repository's own wind input — an accepted, recorded
condition, and the reason rule 29(b) form 4 no longer holds unqualified for SPP (desk note, r#15).

## 2026-09-09 — spp-19: SPP-51c — the oversupply curtailment ALLOCATION is built, screened, KILLED on its own gate and PROMOTED anyway by owner ruling; and SPP's actual-LMP sidecar was on UTC

**Two owner instructions, both executed in-session.** *"Just fix it so it's not on utc anymore and
then fix so results are local time."* and *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a keeper."*

**THE CLOCK DEFECT, found while validating the instrument and not looked for.**
`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` — the series C3a/C3b/C3c score SPP
against — was indexed on **SPP's GMT market interval** while the model's 8760 calendar is **fixed
Central Standard Time**. Rubric v2.4 scores C3a against `rt_lw`, the committed hourly actual
weighted by the same measured demand the model dispatches — an **hour-matched** pairing — so the
offset landed on a load-bearing criterion. Direction and magnitude were fixed by physical markers
**before any scored number was computed**: EIA-930 solar peaks at index 12/13 (solar noon) and load
at 17; the sidecar's RT peaked at 22/23; SPP's own explicitly GMT-stamped GenMix load peaks at UTC
hour 22, the very index the sidecar peaked at. A **six-ISO census isolates the defect to SPP alone**
(CAISO/PJM/MISO/NEISO lag 0, NYISO −1, ERCOT +2, SPP +5) — the other six go through
`derive_actual_lmp._STD_TZ`; SPP's sidecar is staged pre-built by `build_spp_lmp_reference.py` and
bypassed it. **The magnitude is a CONSTANT +6, not the seasonal 6/5 the first lag-scan reading
suggested** — corrected in-session on a measurement against GenMix restricted to the DST months,
where the two hypotheses differ (fixed CST wins in all three years, corr 0.9913/0.9391/0.9652 vs
0.9815/0.9309/0.9588). Repaired at the source plus a `--repair-clock` re-index (the portal is
blocked and the raw exports are not committed, so the emitted sidecars cannot be re-fetched).
**A pure re-indexing, verified:** sorted value sets identical, equal-hour annual means unchanged to
four decimals, RT peak hour 23/22/23 → **17/16/17** matching load's 17, `actual_amplitude`'s SPP
`rt_peak_hour` 23/22/23 → 17/16/17 and `rt_trough_hour` 7 → 1 with `rt_range` essentially unmoved.
`rt_lw` **24.438/24.531/27.957 → 25.133/25.450/28.598**. `actual_tail.json` regenerated with a
**zero diff**, which also proves no other ISO moved. **EVERY SPP C3a/C3b NUMBER OLDER THAN
2026-09-09 IS ON THE UNREPAIRED CLOCK AND IS NOT COMPARABLE.** Stale and deliberately not
regenerated (rule 25): the SPP sidecar is a neighbour anchor for `derive_miso_seam_ladders.py` and
`derive_neighbor_hr_by_year.py` — MISO's and PJM's desks' call.

**THE MECHANISM.** `vre_curtailment_oversupply_allocation` (gated, default off, ISO-agnostic)
re-allocates the **hours** of SPP's measured wind curtailment and changes **no annual total**. The
flat gross-up `delivered/(1−0.096501)` is flat to 99.94/99.93/99.98 % of hours and delivered is
already net of curtailment, so the measured 9.65 % was spread uniformly — everywhere except where it
happened. The field water-fills the **same frozen annual energy** onto the lowest-net-load hours at
the level λ (16.15/16.48/17.58 GW) that makes the annual identity hold. **Zero new free parameters**;
DOF ledger unchanged at 3 entries / 1 residual; annual potential identical to the flat rule's in
every year (rule 23 untouched).

**THE SCREEN KILLED IT AND THE LANE SAID SO.** 2025, named by largest reallocated energy (13.587
TWh), not by residual. It **created SPP's negative-price regime for the first time** — 177
interior-wind hours, 159 system-LW hours < $0 from a control of essentially zero, pricing at
**exactly −$26.00** — and still missed every band: G-1a 177 vs a predicted 871 (band 348–2178),
G-1b 159 vs 592 (band 237–1480), G-3 the wind identity 1.10681 → 1.10489. G-2 also failed as
written (53.67 % vs 90 %) but **was mis-specified by the lane** — it measured against the flat
bound, which the mechanism moves in every hour by construction; the property it meant to test reads
100.0 % and is a diagnostic, never a gate pass. Phase-0 bars **F-2 (≥45 %, got 40.75/42.68/43.71 %)
and F-4 (+3.0–8.0 GW, got +2.63/+2.38/+3.11) also MISSED** and are reported in the words they were
written in.

**ROOT CAUSE, AND IT RE-POINTS THE OBJECT.** The LP **absorbs 98.2 %** of the concentrated headroom
by displacing thermal instead of spilling wind: in the 2,848 allocated 2025 hours where wind did not
go interior, thermal averaged 8,454 MW and still had **8,200 MW of turn-down available** (2,624 with
over 2 GW spare), and the model's thermal **annual minimum is 254.3 MW across a ~40 GW fleet**
because SPP carries zero commitment floors and zero bridges. That is **direct measured evidence
against SPP-51b's own sizing note**, which placed the deficit on the wind side. The binding limb is
**R-2**, and rule 19 requires any successor floor to be **reconciled with** this allocation, never
stacked on it.

**PROMOTED ANYWAY — SPP KEEPER 4, `2026-09-09-spp-51c-oversupply-curtailment`.** Full span in ONE
invocation; the 2025 P0 objective reproduces the screen's to the cent (188,653,999.5344). All three
runs **re-scored on the same repaired bench**: C1 failing rows keeper-3 **2** / SPP-50 1 / **this 1**
(2024 ST_GAS −8.23, the routed Harrington object); C3a failing years keeper-3 1 (+11.0 %) / SPP-50
**2** (+11.9, +11.6) / **this 1** (2025 +10.3 %); C3b failing years keeper-3 2 / SPP-50 **3** /
**this 1** (2025 0.204). **Against its own control it is better on every criterion and worse on
none.** C2/C4/C6/C8 PASS; C5a −2.4/−1.8/+3.1 %; D-10 free-class 11/12. **Determination NOT-YET**,
unchanged — C3c fails all three years (no scarcity mechanism at all; SPP-55) and C3a/C3b-2025 are
marginal. **The failed gate is not withdrawn**; the owner overrode the lane's recommendation on the
standing structural-improvement rule.

**Retention (rules 15/31):** bundle slimmed to keeper-3's committed shape (3.1 MB); the 121 MB of
`dispatch/`/`floors/`/extra hourly parts **moved to a gitignored sibling, not deleted**. SPP is now
at **keeper-only retention** (one registered run), which required converting this lane's predecessor
citations to lane/FINDING form — the convention keeper-3's own note recorded. DOF labels carried
forward from keeper-3's committed ledger; the builder-vs-committed discrepancy stays **SPP-50 R-3**.
**Disclosed:** the post-solve report stage was killed (~4.8 GB, no traceback) after the 2025
price-duration block — the LP completed and wrote every hourly sidecar, and `metrics.json` is a
registration artifact, not a solve one. Cell `vre_curtailment_oversupply_allocation` **R → K**.
Records: `docs/handoffs/FINDING-spp-51c-2026-09-09.md` (+ ADDENDUM 2),
`PRECOMMIT-spp-51c-2026-09-09.md` + ADDENDUM.

---

## 2026-09-10 — spp-20: SPP-52a PROMOTED to keeper 5 by owner ruling — the authorized-channel −7 % fossil offer level; C3a and C3b both CLEAN for the first time, and SPP is ONE ROW from CALIBRATED

**Owner instruction, verbatim:** *"Determine if spp 52a should have been promoted. If so, promote and then
launch a fresh spp calibration backcast session to close the rubric and reach frontier / complete. If it
shouldn't be promoted, then still launch the next calibration session off 51c"*. **ZERO LP** (rule 32
`[R-SHARD]` (a): this session is an orchestrator and solved nothing). The adjudication was made on the
committed artifacts of BOTH runs, re-scored by this session rather than read off the producing lane's report.

**DETERMINATION: PROMOTE.** SPP-52a (`2026-09-09-spp-52a-fossil-offer`, bundle `spp52a_fossil93`) is keeper 5,
superseding keeper 4 (lane SPP-51c). The producing lane had deliberately left the matrix cell at `O` — *"O not
K because PROMOTION IS THE OWNER'S ACT and has not been ruled"* — which is exactly the posture rule 31
`[R-RETAIN]` asks for, and the question it left open is the one this session answered.

**WHY, ON THE SCORER'S OWN OUTPUT — IT STRICTLY DOMINATES ITS PREDECESSOR.** Both bundles re-scored with
`scripts/calibration_verdict.py` on the same repaired-clock bench, so this is like-for-like:

| criterion | keeper 4 (SPP-51c) | **SPP-52a** |
|---|---|---|
| C1 fuel-mix (LOAD) | FAIL — 2024 ST_GAS −8.23 TWh | FAIL — same single row, **−8.13 TWh** |
| C2 system volume (LOAD) | PASS | PASS |
| **C3a mean LMP (LOAD)** | **FAIL** — 2025 +10.3 % | **PASS** — +1.36 / −0.61 / +3.61 % |
| **C3b price shape (LOAD)** | **FAIL** — 2025 NRMSE 0.204 | **PASS** — 0.1647 / 0.1762 / 0.1755 |
| C3c price tail (SUPP) | FAIL all three years | FAIL all three years (0 / 4 / 2 h vs 42 / 59 / 68) |
| C4 / C6 / C8 | PASS | PASS |
| grade summary | grade 4 of 8, **4 fails** | grade **6 of 8, 2 fails**, 0 caveats of any kind |
| per year | 2023 CALIBRATED · 2024 NOT-YET · **2025 NOT-YET** | 2023 CALIBRATED · 2024 NOT-YET · **2025 CALIBRATED-WITH-CAVEATS** |

Better on two load-bearing criteria, marginally better on the third's failing row, **worse on nothing gated**.
This is **the first SPP run for which C3a and C3b both PASS**.

**THE CARVE-OUT CONDITIONS WERE VERIFIED, NOT ASSUMED.** Checked against the run's own `run_config.json`:
all ten registered fossil classes at **0.93** on exactly the four bands (`committed`/`econ_low`/`econ_high`/
`peak`); **no** `phys_*` field, **no** `econ_low_share`, **no** `pct_peaking` (CT_PEAKER keeps 0.526 / 7.0,
COAL_PRB 0.55, ST_GAS 0.5 / 15.0); the three `*_INTERMEDIATE` curves untouched at peak 2.25 / 3.0 / 2.2; no
adder, offset, haircut or proxy anywhere; ONE config across all three scored years; the value is **the owner's
own number**, declared in `PRECOMMIT-spp-52a-2026-09-09.md` before the solve and **never swept** — exactly one
multiplier was ever solved. Declared in the attestation's `authorized_price_tuning` block against the scorer's
six-field schema, so **C6 PASSES**, and carried as a ledgered free parameter (identification *"price residual,
authorized channel (rules 1/13 amendment 2026-09-05)"*, **DOF `n_residual` 1 → 2**; entries stay at 3 because
the schema counts `offer_curve_by_group` as one entry carrying a dict).

**WHY RULE 1 `[R-STRUCT]`'s FIRST HALF IS NOT ENGAGED.** Its "a level-tuned run that is missing real structure
is still not a keeper" clause targets a run that trades structure for level. This run carries **exactly** keeper
4's structure — same mechanism set, same curtailment allocation, same inputs, one field different — so there is
no more-structural alternative it beats, and nothing was given up. The measured level response is **−6.00 /
−5.91 / −6.03 %, flat to 0.12 pp across three years**: the signature of a **level** lever, which **CONFIRMS the
price-family lane's G-2 steepening refusal rather than overturning it**. Nothing rotates the stack and no shape
claim is made.

**REPORTED AGAINST THE PROMOTION, at full magnitude:** the determination does **NOT** change (NOT-YET), and a
passing C3a is not a calibrated ISO. The reported-only **D-A diurnal amplitude FALLS ~2 pp** — 36.9 / 35.2 /
28.9 % of measured against keeper 4's 38.9 / 36.8 / 30.3 % — because a level cut compresses the absolute
hour-of-day range. **SPP's price surface is still too FLAT and has NO TAIL**, and every structural object keeper
4 named is still open and is **not** closed by this promotion: the thermal-commitment floor (SPP-51b R-2, the
measured binding limb — the LP absorbs 98.2 % of the concentrated curtailment headroom, thermal annual minimum
254.3 MW across a ~40 GW fleet), the zonal spread (R-3, measured |N−S| 12.13 / 17.23 / 15.18 against a model
~1), and scarcity (SPP-55). A tuned level does not substitute for any of them.

**THE FINDING THAT SETS THE NEXT LANE'S TARGET — SPP IS ONE ROW FROM CALIBRATED.** Verified against this
keeper's own scored JSON (`protective: 0`, `ledgered: 0`, `commercial_band: 0`, ledgered budget **1**, free):
**C3c is now the ONLY supporting-tier failure.** If C1's single 2024 ST_GAS row is repaired, C3c becomes the
**LONE** failure and the rubric v3.3 C3c standing rule (rule 22 `[R-C3C]`) reclassifies it to a ledgered caveat
— **every guard is already satisfied** (governance PASSES, C3c is supporting tier, it is never a PASS, and the
single ledgerable slot is free). **SPP WOULD THEN READ CALIBRATED.** The per-year table makes the same point
independently: 2023 is already CALIBRATED and 2025 is CALIBRATED-WITH-CAVEATS (blocked only by the preliminary
EIA-923 vintage, a DATA limit, not a model one); **2024 alone holds the ISO, and `fuelmix` alone holds 2024.**
That makes **SPP-46 R-4 / desk register R-ax — Harrington 6193's fuel vintage** (carried as `gas_st` at
$1.48/MMBtu in 2023–24 while CAMPD burns coal on all three boilers, converting in 2025) — the highest-value next
lever, ahead of the thermal floor and scarcity. It is a **data-vintage repair, not a new mechanism**.

**PROMOTION SURFACES TOUCHED (SPP's own files only, rule 25 `[R-ISO-SCOPE]`):** `keepers/SPP.json` (keeper +
note); `status/SPP.js` rebuilt via `build_status.py --iso SPP` (`shared.js` byte-unchanged); the mechanism-matrix
SPP shard (keeper/gates stamps, `offer_curve_by_group` **O → K**, rule 28(b)) and its §5.7 prose header;
`prune_iso_runs.py --iso SPP` removed the superseded keeper 4's three stores (rule 15 keeper-only retention;
its FINDING docs are retained and git history is the record). **`calibration-complete.json` NOT touched** — SPP
is absent from both blocks and reads NOT-YET, so there is nothing to re-key.

**THE R-T DUTY WAS DISCHARGED, AND THE ROW WAS STALE BY TWO PROMOTIONS.** `program-status.json`'s SPP
`gate.a_keeper_marker` still named the **THIRD** keeper (`2026-09-07-spp-3-screened-input`): the SPP-51c lane
promoted keeper 4 on 2026-09-09 without re-keying it, which is exactly the multi-PR staleness window R-T exists
to make zero. Recorded against that lane rather than smoothed over; no ruling is sought. Re-keyed here in the
promotion commit — `check_gate_a_provenance.py` listed SPP before the edit and does not after. **The gate verdict
is unaffected** (fail before, fail after): SPP is absent from the `complete` block on both sides and the marker
did not move, so this changes identity and determination text only.

**GATES AT THIS SESSION'S TIP:** `audit_keepers.py` **PASS** (0 failures, 0 warnings; SPP "all checks passed" on
the new keeper). `check_gate_a_provenance.py` clean for SPP. `check_mechanism_matrix.py` exit 0 with **no SPP
warning**. `check_registry_payload_parity.py` is **RED and it is NOT this promotion's**: seven dead ERCOT bundles
(`ercot262_arm_2021-2025`, `ercot264_repro_2023/2025`) fail identically at HEAD, with **zero** SPP rows on either
side — ERCOT's desk's Class-E clean-up under rule 29(c), routed, not touched here (rule 25).

**Retention (rule 31 `[R-RETAIN]`):** the keeper's bundle including its `hourly/` sidecars is **committed**, so
the next lane differences against it with **no re-solve** — the cost that lane SPP-50's dead container imposed is
not repeated here.

**Next shorthand: spp-21.** Next lane issued this session: **SPP-61**, the Harrington fuel-vintage repair.

---

## 2026-09-10 — spp-21: SPP-61 the Harrington fuel-vintage repair — the charter's BENCH SIDE IS FALSIFIED at zero LP, and the model-side arm is KILLED at the rule-29 screen gate G3 on a prerequisite it exposed

**ONE year of LP, in one shard** (rule 32 `[R-SHARD]`: this session orchestrated and solved nothing).
**Determination UNCHANGED — `NOT-YET`, keeper 5 `2026-09-09-spp-52a-fossil-offer`.** Nothing registered
(a rule-29 screen never is), no keeper moved, `keepers/SPP.json` and `calibration-complete.json` untouched.
Record: `docs/handoffs/PRECOMMIT-spp-61-2026-09-10.md` (pushed before the solve) and
`docs/handoffs/FINDING-spp-61-2026-09-10.md`.

**THE CHARTER'S TWO-SIDED PREMISE IS FALSE, AND PHASE 0 PROVED IT BEFORE ANY LP.** The charter had the
benchmark booking Harrington's coal under `ST_GAS` (`e_ann` 3.44 / 2.23 TWh). It does not. The SPP EIA-923
bench frame is **completely inert to the EIA-860 vintage — 0 klass rows differing by >1 MWh in 2023, 2024
or 2025**, even though `_fleet_group_by_code` moves for 26 / 17 / 0 plants; the **BTM frame is inert too**.
The bench already books Harrington as **`COAL_PRB` 3.1775 / 2.0590 / 0.0000 TWh**, because `_classify_f923`
buckets every EIA-923 row by *its own* reported fuel and the CAMPD backfill never fires for the plant. What
the charter saw is the per-plant **display panel** (`plants["6193"].group = "ST_GAS"`), a different object
from `classFull`. **So C1's ACTUAL cannot move**: the 2024 `ST_GAS` actual of 20.101 TWh carries **0.175 TWh**
of Harrington, not 2.23 — and the charter's arithmetic for closing C1 rested entirely on that bench move.
**The warrant is untouched**: rule 14 `[R-ACCURATE]` / rule 13 `[R-MEASURED]` owe the repair because the
model's fuel vintage IS wrong and the accurate data exists. *"It would close C1" was the PRIZE, never the
JUSTIFICATION* — so the arm was screened, not dropped.

**THE ONE SEAM, and it needed ZERO code change.** `ScenarioConfig.eia860_vintage_tracks_solve_year`
(pjm-167, dataclass default `False`) — **the first arm of that mechanism anywhere, in any ISO** — through
`replay_keeper --set`, the registered generic `prb_overrides` channel. **Not one file under `src/` or
`scripts/` was edited by this lane.** It lands Harrington exactly on its vintage: **2023 → 1,018.0 MW all
`COAL`; 2024 → 679.0 `COAL` + 339.0 `ST_GAS`; 2025 → unchanged** (no `vintage_2025/`, and that is the right
answer — the units' own filed repower dates are 2/2025, 3/2025, 6/2025).

**SCREEN YEAR 2023, named in the PRECOMMIT by MEASURED FOOTPRINT** (1,018.0 MW reclassified vs 679.0;
3.1775 vs 2.0590 TWh of measured coal) — the opposite of residual-chasing, since the failing C1 row is 2024.

**GATES — 4 of 5 pass; G3 stops the arm.** G1 fleet identity PASS. **G2 footprint confinement PASS EXACTLY:
94 plants move in 2023 and 63 in 2024, and ZERO are unexplained** by that year's own EIA-860 release
differing from the canonical snapshot (`results/calibration/_spp61_g2_footprint.json`). G5 bench inertness
PASS. G4 PASS on what was measured — system volume **+0.0054 TWh**, mean price **24.69 → 24.87 $/MWh
(+0.72 %)**; **C3b went UNMEASURED** (no channel from this session to a cloud shard) and that is stated, not
glossed. **G3 FAIL ⇒ STOP**, and the split matters: its **magnitude** limb PASSES — coal-family net
**+2.825 TWh** against Harrington's measured 3.1775 TWh, right size, right direction, energy conserving —
while its **identity** limb FAILS: `COAL_PRB` **FELL 0.94 TWh** and **4.3551 TWh appeared in a bare `COAL`
class the SPP benchmark has no row for**.

**ROOT CAUSE — THE SAME DEFECT, ONE LAYER DOWN** (measured at zero LP): `coal_supply_class(6193)` returns
**`''`** because `scripts/data/derive_coal_supply.py` builds its coal census from
`load_fleet_from_csv(iso, iso_config)` with **no vintage** — the very registry this repair exists to fix —
so Harrington is absent from `coal_supply_SPP.csv` (29 rows) and falls through the entire resolution ladder.
The bench resolves it only via the EIA-923 receipt code (`_coal_supply_class(6193,"SUB")` → `COAL_PRB`).
**Successor `R-ay` is a PREREQUISITE, not an alternative — re-run the arm before it lands and it reproduces
this exactly.** Its admissibility under rule 23 `[R-FROZEN-DERIVE]` rests on the cited change being a change
in the derive's **own input** (its census reads a registry now shown wrong for the solved year), **not** a
residual that moved, and the successor's PRECOMMIT must say so explicitly.

**REPORTED AGAINST THE REPAIR, at full magnitude:** as screened it would **BREAK 2023's currently-passing
C1 `ST_GAS` row** — gm ≈ **8.073 → 6.80** against 15.020 actual, ≈ **−8.22 TWh** outside the ±8.00 band,
from 1.05 TWh of headroom (an estimate, labelled one: `gmModel` carries an `OTHER_FOSSIL` reclassification
this session cannot reconstruct outside registration). That is **not** why the arm stopped — C1 is the
TARGET criterion and was deliberately excluded from the gate, because under rule 1 `[R-STRUCT]` a
structurally-correct mechanism is never rejected for moving its own residual the wrong way. Also reported:
the arm is a **whole-registry swap of 2.7–3.2 GW**, wider than the charter anticipated; G2 shows every moved
row is justified, but a successor must own that width rather than wave it through on Harrington's account.

**ZERO new free parameters** (rule 21 `[R-DOF]`) — selection is by calendar year alone; the keeper's DOF
ledger is unchanged (`n_residual` 2, entries 3) and its `offer_curve_by_group` authorized-tuning block was
replayed **verbatim** at 0.93 on the four bands. **RULE 25 `[R-ISO-SCOPE]` CLEAN BY CONSTRUCTION**: a
per-run flag registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its declared `False`, no shared default flipped —
**zero other ISOs move** and every pre-existing key of all seven ISOs is byte-stable. **Routed, not touched:**
`run_calibration_full.py` builds the bench `group_by_code` at line 5286, *before* `run_year` sets the year's
vintage at line 5396 — measured effect for SPP **exactly zero**, so it is recorded for the ISOs where the
CAMPD backfill does fire rather than repaired blind here.

**G-DRIFT — no control solve was spent** (rule 29(b) form 4). The SPP **solve-surface fingerprint at HEAD is
`7ab7e3b0c4741dc3`, 182 rows, 0 moved — byte-identical** to the keeper's recorded value, and all **17**
changed files since the keeper's `basis_sha` `fc927c2f…` classify **INERT** with reasons. Corroborated: the
committed keeper re-scored at HEAD reproduces its published determination and **every C1 row exactly**
(2024 `ST_GAS` model 11.970 / actual 20.101 / −8.13 TWh). **Every number in this entry was re-derived in
this session; none is quoted from a predecessor lane's prose.**

**Cells (rule 28(b)):** `eia860_vintage_tracks_solve_year` **U → O** — *open*, deliberately **not `R`**. The
mechanism is not rejected; it is blocked on a named prerequisite, and `R` would trip rule 28(a)'s
do-not-redo discipline against a repair rule 14 actually owes.

**Retention (rule 31 `[R-RETAIN]`): NOTHING was `rm`'d and nothing is promotable.** The screen bundle lived
on shard A's own ephemeral container, was never pushed by design (rule 29(c)), and does not survive it.
Re-spending it costs ~3 min of LP for the one year, ~7 min for the span.

**Next shorthand: spp-22.** Next lever: **R-ay** (the vintage-aware coal supply-class census), then the
charter §7 queue unchanged — SPP-51b R-2 the thermal-commitment floor, R-3 the zonal spread, SPP-55/56
scarcity / C3c.
