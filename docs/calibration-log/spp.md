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

## 2026-09-10 — spp-21 (session ercot-266): SPP-58 wind curtailment CEILING — built, screened, and one plumbing bug of mine caught by the shard

**LANE ORIGIN, and why an ERCOT session is writing in SPP's log.** The prompt for ercot-266 offered
ERCOT's named open object (C3c-2021 February breadth) *or* a live rubric failure elsewhere, and it named
SPP as the highest-value alternative with an already-scoped lane. ERCOT's object is **data-blocked** —
the daily Waha/HSC series has been surveyed three times and no free public source carries a Texas hub, so
closing it is an owner procurement decision, not a modelling one. SPP is **one row** from CALIBRATED. The
session took SPP and touched **only SPP's files** (rule 25 `[R-ISO-SCOPE]`), plus the ERCOT-lane cleanup
ercot-265 left owed.

**THE PRIZE, measured rather than assumed.** SPP-52a's promotion closed `price_mean` and `price_shape`,
so SPP now fails on exactly **two** criteria, not the four the 2026-09-09 PRECOMMIT recorded:

| criterion | tier | status | detail |
|---|---|---|---|
| `fuelmix` (C1) | load-bearing | **FAIL** | **2024 `ST_GAS` −8.13 TWh — the SINGLE failing row in the whole 3-year table** |
| `price_tail` (C3c) | supporting | FAIL | 0 / 4 / 2 h vs 42 / 59 / 68 h > $200 |

C3c is the only LEDGERABLE criterion. **If C1-2024 closes, a lone C3c reads CAVEAT under rubric v3.3 and
SPP reads CALIBRATED.** That is the stake — it is stated as the stake and is **not** a gate: no gate in
this lane reads a target residual (rule 1 `[R-STRUCT]`).

**PHASE 0, zero LP, on the CURRENT keeper's committed artifacts.** `renewable_bound_provenance` = 
`forecast_uncurtailed` in all three years: the delivered EIA-930 profile grossed up by SPP's frozen
measured reference rate (9.65 %), a construction whose own stated precondition is *"real headroom,
**endogenously re-curtailed**"*. Reconstructing the keeper's own wind bound at HEAD and differencing
against its committed dispatch:

| year | wind bound | wind dispatch | **re-curtailed** | hours at the bound |
|---|---:|---:|---:|---:|
| 2023 | 114.055 TWh | 113.757 | **0.261 %** | 65.0 % |
| 2024 | 120.992 TWh | 120.723 | **0.223 %** | 97.6 % |
| 2025 | 122.255 TWh | 122.043 | **0.174 %** | 65.8 % |

**A 40–60× miss on the mechanism's own precondition** — and measured on a keeper that ALREADY arms
SPP-51c's oversupply water-fill, so the water-fill moved the headroom to the low-net-load hours and the
LP took it anyway. The cause is written in this repo's own code: `renewables.py` keeps NYISO OUT of
`_UNCURTAILED_FALLBACK_ISOS` because *"its curtailment is locally driven and the reduced network can't
re-curtail a gross-up"*. **SPP is IN that set on identical facts** — the 2-zone reduction collapses the
SPS / Texas-Panhandle and western Kansas / Oklahoma export pockets, so nothing can spill wind bid at its
−$26/MWh PTC floor.

**BUILT: `spp_curtailment_ceiling` + `spp_curtail_depth_wind`** — SPP's own instance of the ERCOT-precedented
reduced-form ceiling, `1 − depth × congestion_share(net-load decile, hour, season)` on the wind bound,
both zones, **no solar** (SPP's solar bound is `delivered_pinned`, so there is no gross-up headroom to
remove). Rule 25: **nothing transfers** — ERCOT's depth, table and corridor attribution stay ERCOT's.

- **SHAPE** from SPP's published RTBM binding-constraint archive (`data/raw/spp-binding-constraints`,
  landed 2026-09-08 — the predecessor PRECOMMIT recorded it token-blocked and **that blocker is gone**),
  measured binding incidence only. **The union saturates** — 91.0 % of 2024's 5-minute intervals carry a
  binding constraint — so a fraction-of-intervals share encodes no shape; the derive uses the **count** of
  simultaneously binding constraints, which discriminates with the physically right sign. Share by
  net-load decile (0 = lowest net load = highest wind): **0.488** 0.434 0.384 0.321 0.267 0.219 0.199
  0.198 0.204 **0.226** — monotone-falling 0→7 at 2.5× range, with a real load-driven uptick at 8–9 left
  in rather than smoothed out. 866 of 960 cells populated.
- **CLOCK, a real trap and it was caught.** The archive's `Interval` column is SPP local time WITH DST
  (GMT offset 6 h in January, 5 h in July) while the model runs FIXED CST. Every timestamp is rebuilt from
  `GMTIntervalEnd` at a constant −6 h with 29 February dropped. This is the same defect repaired for SPP's
  LMP sidecar in `86e45462`; deriving off `Interval` would have shifted the whole summer half by an hour.
- **LEVEL** from SPP's published measured curtailment MW (MMU ASOM, both legs metered), **one pooled value
  across every scored year**: 0.288137. **Reported at full magnitude: the per-year implied depth spread is
  19.9 %** (0.2565 / 0.3139 / 0.2917) — looser than ERCOT's "stable structural constant" claim and not
  dressed up as one. What IS tight is the shape (weighted-mean share 0.331 / 0.336 / 0.339, 2.5 %), so the
  spread is SPP's published curtailment MW moving 1,097 → 1,483 → 1,382, which is how a depth × shape
  decomposition should behave. **Zero free parameters**: the table's (0,1] rescale carries no leverage
  because depth is centred on the published MW after it.
- **Rule 19 `[R-ONE-MECH]` ENFORCED IN CODE**: `renewables.py` skips `_oversupply_uncurtailed_cf` whenever
  the ceiling is armed, so the ceiling **replaces** the water-fill and the two can never both be live. The
  swap is **energy-neutral on the basis** (annual potential identical to the milli-TWh in all three years),
  so every TWh the arm removes is the ceiling's.

**PRE-SOLVE ARITHMETIC (zero LP).** The 2024 bound falls **120.992 → 109.226 TWh, −11.766 TWh (9.72 %)** —
against the −12.5 TWh SPP's own measured rate implies, and landing essentially ON the 109.317 TWh EIA-930
delivered. G-3's concentration premise holds at the table level: decile 0 carries **21.41 %** of the
removal against a flat 10 %, monotone decreasing to 3.69 % at decile 9.

**G-DRIFT (rule 29(b)) — no control solve spent.** The keeper's own `git_sha` `c1393878` is **unreachable**
(a solve-time sha on an auto-deleted branch); declared, and the audit base substituted with `d77c184e`, the
keeper's registration commit. All eighteen changed solve-path files classify **INERT for SPP** with reasons
cited — the load-bearing ones being that `IMPORT_ZONE` carries no SPP key and all 42 seam flags are False;
that the 11 plant ids added to `ST_GAS_PEAKER_PLANTS` (consumed **ungated**, so this needed a real check)
are all EIA-860 `BA = PJM` with **zero overlap** against SPP's 828 `SWPP` plants; and that
`_PARTIAL_EXIT_WINDOW_START` is read only under `partial_plant_exit_carry`, `False` here. The
`_validation-source` bench DID move, so the control was **re-scored at HEAD** — **every criterion status is
identical to its committed `metrics.json`**, so the bench move does not reach SPP and G-CTRL form 4 holds.
`check_bench_freshness --iso SPP`: 3 parts, **0 STALE**, all three reproduce at HEAD; the SOFT engine-drift
note is a commit COUNT, not a measured difference, and the fingerprint test that IS the measured check says
the parts are current.

**THE SCREEN SHARD CAUGHT A PLUMBING BUG OF MINE, AND IT MATTERS MORE THAN THE SCHEDULE SLIP.** The first
shard stopped at its HARD STOP and produced no bundle: `run_calibration_full.py` **parsed**
`--spp-curtailment-ceiling` and then never read `args.spp_curtailment_ceiling` into either
`solve_and_persist` call site, so both new flags were accepted silently and dropped and the invocation
reduced to **the control**. There is **no error, no warning, and a bundle that would have looked like a
solved arm** — had the shard not been told to grep the log for a message the mechanism must emit, this
would have returned a clean, complete **null-effect** result and minted an `I` verdict about a mechanism
that never ran. Its proof did not rely on reading my code: the solve's own log showed the oversupply
water-fill firing, which the rule-19 supersession forbids when the ceiling is armed, so the ceiling was
provably off inside the solve. It then killed the process at ~6 min rather than spend 25 more on a control
solve rule 29(b) forbids, and refused to patch `scripts/` itself. Right on all three counts.

Fixed at both call sites and **verified two-sided at zero LP** by intercepting `solve_and_persist`: before,
`<<< NOT DELIVERED >>>`; after, `True` with the depth falling through to its dataclass default. Guarded by
`tests/unit/data/test_spp_curtailment_ceiling.py::test_cli_flags_reach_the_solve_seam`, **confirmed to fail
against the un-fixed file and pass against the fixed one** — a guard never shown to fail is not a guard.
Routed rather than absorbed: a crude static sweep finds **31 of 244** ScenarioConfig-named flags without
the literal `args` hop, but most are delivered by other routes (`ercot_ep_gas_basis_receipts_fallback`
among them, which demonstrably worked in the ERCOT keeper), so separating a real silent drop from a
different delivery pattern needs the runtime probe run across all 244 — **named with its size, not
attempted here**.

**A SECOND DEFECT OF MINE, also caught before any arm existed.** PRECOMMIT gate G-4 read *"slack and dump
stay exactly 0.0"*. The shard measured the **control** at **177.596 MWh** of slack in 2024, so G-4 was
**unsatisfiable by any run including the incumbent** and discriminated nothing — I carried the clause
forward from the predecessor PRECOMMIT without measuring the incumbent's baseline, which is what phase 0 is
for. Re-cut to the strictest satisfiable form (dump exactly 0.000; slack ≤ 2× the control) in
`docs/handoffs/ADDENDUM-spp58-the-flag-was-parsed-and-dropped-and-my-G4-was-unsatisfiable-2026-09-10.md`,
**written while no arm result existed**, so it is not a gate re-cut in the light of the result it decides.

**NO CELL VERDICT IS MINTED.** `spp_curtailment_ceiling` stays **`U`** in SPP's matrix shard and
`vre_reference_rate_curtailment_grossup` stays `U`: the shard tested the CLI, not the mechanism (rule
28(b) — a footprint measured at zero LP is not a verdict, the same discipline SPP-51b applied).

**ERCOT-LANE CLEANUP DISCHARGED IN THIS SESSION** (recorded here for continuity; the ERCOT log carries it
too): both ERCOT keeper-stamp surfaces re-pointed to `2026-09-09-ercot265-receipts-fallback`, matrix
anchors repaired, and `results/shard-staging/ercot265/` removed after **proving** all 30 of its sidecars
hash byte-identical to the registered keeper bundle. **And it corrects the handoff**: `prune_iso_runs.py
--iso ERCOT`, recorded as blocked and suspected of leaving ERCOT over-retained, prunes **nothing** — all six
non-keeper ERCOT runs are PROTECTED as governance citations. `check_registry_payload_parity` stays **RED**
on the seven dead ERCOT bundles and is **deliberately not cleared**: rule 31 `[R-RETAIN]` puts that behind
an owner ruling on ercot-262 promotion.

**Next shorthand: spp-22.**

## spp-61 — 2026-09-10

**KEEPER 6 PROMOTED: `2026-09-10-spp-61-vintage`** (bundle `results/calibration/spp61_vintage`),
over keeper 5 `2026-09-09-spp-52a-fossil-offer`, **by owner ruling in-session** — verbatim: *"Is this
a recommended keeper candidate? If so plz promote... If structural integrity improves but gates
regress that may still be a keeper."*

**The run:** keeper 5's recipe plus **exactly one** change —
`ScenarioConfig.eia860_vintage_tracks_solve_year = true`, armed per-run through the registered
`--set` channel on `replay_keeper.py`. Zero code change, zero shared default flipped, zero new
tunable. One `--years 2023 2024 2025` invocation, years sequential (rules 12 / 16), 655 s wall.
**First arm of this field in any committed run, in any ISO.**

**Promoted on structure, not on score — the score gets worse.** Unarmed, every backcast year resolved
against the canonical EIA-860 2025 Early Release, giving a registry of 60,749.0 / 60,739.9 / 60,739.9
MW across three years — a fleet that barely evolves, the pjm-167 defect. Armed: −2,715.4 MW (2023) /
−3,175.3 MW (2024). Harrington 6193 lands on its own vintage (1,018.0 MW `COAL` in 2023; 679.0 `COAL`
+ 339.0 `ST_GAS` in 2024; 1,018.0 `ST_GAS` in 2025, correctly). Warrant: rule 14 `[R-ACCURATE]` and
rule 1 `[R-STRUCT]`.

**Reported at full magnitude:** C1 goes from ONE failing row to TWO — 2023 `ST_GAS` −8.38 TWh (it had
been PASSING on 1.05 TWh of headroom) and 2024 `ST_GAS` −9.71 TWh (from −8.13). C5a CO2
(reported-only) −2.6/−2.0/+3.0 → −5.6/−3.1/+2.9 %. D-10 15/16·11/12 → 14/16·10/12. C2 / C3a / C3b /
C4 / C6 / C8 PASS on both; C3c FAILs on both. **Determination NOT-YET on both, identical basis
(`fuelmix, price_tail`)** — the promotion costs no status. Improving besides the fleet: D-A diurnal
amplitude 36.9/35.2 → 38.5/38.1 %, and **2025 diurnal phase repairs OFF → OK**.

**Keeper 5's own bet is measured and lost:** its note projected that repairing this row would leave
C3c the lone failure and make SPP read CALIBRATED under rule 22. It does not. Half the premise was
falsified at zero LP by this lane's phase 0 — the EIA-923 bench frame is completely inert to the
EIA-860 vintage (0 rows > 1 MWh) and already books Harrington's coal as `COAL_PRB`.

**Screen (rule 29):** year 2023, named by measured footprint, not the residual year. G3 coal family
+2.8178 TWh inside the pre-registered +1.0/+4.5 band with `ST_GAS` falling; G4 no non-target
load-bearing flip. Screen bundle gitignored, never registered, retained on disk (rule 31).

**Routed, not buried:** model `ST_GAS` was already 6.95 / 8.13 TWh below actual *before* the arm; the
arm removes capacity that did not exist in those years and so removes a **compensating error**. The
residual is a gas-steam merit-order / offer defect, not a fleet-vintage defect — **the next lane's
object**, and the only thing between SPP and the rule-22 lone-C3c path to CALIBRATED.

**Matrix (rule 28(b)):** `eia860_vintage_tracks_solve_year` **U → K** in SPP's shard only; rule 28(d)
fills no other ISO's cell. **Routed not touched:** `run_calibration_full` builds the bench
`group_by_code` before `run_year` sets the year's vintage — measured effect for SPP exactly zero.

Records: `docs/handoffs/PRECOMMIT-spp-61-2026-09-10.md`, `docs/handoffs/RESULT-spp-61-2026-09-10.md`.
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

**Next shorthand: spp-22.** *(SUPERSEDED by the spp-22 entry below; R-ay landed 2026-09-10.)* Next lever: **R-ay** (the vintage-aware coal supply-class census), then the
charter §7 queue unchanged — SPP-51b R-2 the thermal-commitment floor, R-3 the zonal spread, SPP-55/56
scarcity / C3c.

## spp-22 — 2026-09-10

**Lane SPP-62 · R-ay, the coal supply-class census vintage repair · KEEPER 7 PROMOTED
(`2026-09-10-spp-62-vintage-census`, bundle `results/calibration/spp62_span`) by owner ruling
in-session.** PRECOMMIT `docs/handoffs/PRECOMMIT-spp-62-2026-09-10.md` (pushed at
`67feede7403240374091cc73a536d836ba6d08c4` before any solve); FINDING
`docs/handoffs/FINDING-spp-62-2026-09-10.md`; shard reports
`docs/handoffs/SHARD-spp62-screen-2023.md` + `SHARD-spp62-span.md`.

**LP spent: 2 shards, 590 s total** — a 150 s rule-29 screen (2023) and a 440 s full span
(2023/2024/2025, ONE invocation). Rule 32 `[R-SHARD]`: this session ran no LP in its own
container; the span shard was the only registerable one (protocol §3).

**THE OBJECT.** `scripts/data/derive_coal_supply.py` built its coal census from
`load_fleet_from_csv(iso, iso_config)` with NO VINTAGE — the canonical 2025 Early Release, in
which Harrington (6193) reads `NG` — for every solved year. A plant that burned coal in the
solved year but had been re-fuelled by the snapshot's vintage was therefore absent from
`coal_supply_SPP.csv` (29 rows), got no rank, fell through all four resolver steps to `''`, and
landed in a bare `COAL` class the SPP EIA-923 benchmark has no row for. **ONE SEAM:**
`_coal_census()` unions the canonical snapshot with each solved year's own `vintage_<year>/`
release, behind a new `--census-vintage` argument whose **default is today's construction**.

**WHAT IT CLOSES IS A SCORING BLIND SPOT, NOT A RESIDUAL.** Keeper 6 books **4.3551 TWh (2023)**
and **2.0670 TWh (2024)** of coal dispatch in that bare class. Re-scored at HEAD, **that energy
appears in NO C1 row, passing or failing** — it is scored against nothing, and `COAL_PRB` reads
low by exactly the missing amount. This is the prerequisite SPP-61's own FINDING §4 root-caused
and routed as R-ay ("a PREREQUISITE, not an alternative"); keeper 6 was promoted before it landed.

**PHASE 0, ZERO LP, and it decided the lane.**

| measurement | result |
|---|---|
| pre-patch script vs committed CSV | **BYTE-IDENTICAL** (md5 `5a71bd95bf10a732af980086e541ffa3`) — the anchor that makes the census below exact |
| census, canonical / v2023 / v2024 / v2025 | 29 / 31 / 30 / absent→canonical; **union over the span = 31** |
| impact on the 29 incumbent rows | **ALL BYTE-IDENTICAL** — `2 insertions(+), 0 deletions` |
| added rows | `6193,prb,generation,26193400.3,1,prb:100%` · `10862,prb,generation,156101.0,1,prb:100%` |
| SPP fleet under the keeper's own registry | **1,012 generators, every field byte-identical** |
| all seven ISOs' fleets | **byte-identical**; 6193 / 10862 in SPP's fleet ONLY (3 and 1 gens) |
| committed run_configs reading a non-canonical registry | **0 of 46** |
| default derive path, SPP / PJM / MISO / NEISO | **all four byte-identical** to the pre-patch script |

The census is a **membership filter** and each rank is computed from that plant's own EIA-923
rows, so widening it can only ADD rows — the measurement confirms the construction rather than
getting lucky.

**RULE 23 `[R-FROZEN-DERIVE]` — the crux, argued before the solve.** The cited trigger is a change
in the **DERIVE'S OWN INPUT** (its census read an EIA-860 registry measured wrong for the solved
year; the correct release was already committed on disk), **not a residual that moved**. Three
facts carry it without leaning on any residual: (a) the rank is not a choice — `SUB` → `prb` at
100 % of ranked weight, by the same arithmetic that ranks the other 29 plants; (b) the repair is
**inert for every committed run**; (c) it moves the target residual the **wrong way**, which a
fitted change does not do.

**RULE 19 `[R-ONE-MECH]`: no fifth resolver.** Both new plants were unresolved by all four ladder
steps, so no existing resolution changes hands — 7902 Pirkey keeps its retiree-fallback `lignite`
and 57937 stays unresolved (both are coal only in `vintage_2020`, outside the solved span).

**THE SCREEN (rule 29 `[R-SCREEN]`) CLEARED EVERY GATE.** Screen year **2023**, named in the
PRECOMMIT by the mechanism's **own measured footprint** (1,025.9 MW reclassified vs 679.0 in 2024;
Harrington's measured coal 3.1775 vs 2.0590 TWh) and deliberately **not** the residual year, which
is 2024. G2 identity — the limb that killed SPP-61 — **bare `COAL` 4.3551 → 0.0000 TWh**. G3
magnitude ΔCOAL_PRB **+3.4118** (band +1.0…+5.0; Harrington measured 3.1775). G4 conservation
residual **0.0052 TWh**. G5 C3a **25.6527** (+2.08 %), C3b **0.1723**. **C1's residual is read
NOWHERE in the gate, by design.** The identity limb holds across the whole span: bare `COAL` =
**0.0000 TWh in 2023, 2024 AND 2025**.

Corroboration worth recording: the coal-family net move is **+2.8178 TWh** against SPP-61's
**+2.8251** on the same arm without R-ay — a 0.0073 TWh difference. R-ay moved the same energy
into a different class and changed essentially nothing else.

**THE SINGLE-DELTA A/B AGAINST KEEPER 6 IS AS CLEAN AS THESE GET.** In 2023, **4.3551 TWh moves
from `COAL` to `COAL_PRB` and NOTHING ELSE** — all fourteen other classes byte-identical to four
decimals (`ST_GAS` 7.0867, `CT_PEAKER` 16.2967, `CC_REGULAR` 42.4877, `COAL_LIGNITE` 7.2935, wind
113.7572, …). In 2024 the same re-label moves 2.0670 TWh. That doubles as a **stronger G-DRIFT
corroboration than a hunk audit**: the 21 files changed between keeper 6's basis and this run's
base are *measurably* inert for SPP.

**THE SCORED RESULT — a wash, with one row moving the wrong way, reported at full magnitude.**

| | keeper 6 | **keeper 7 (this run)** |
|---|---|---|
| determination | NOT-YET | **NOT-YET** (identical basis: `fuelmix`, `price_tail`) |
| grade | 6 of 8, 2 fails, 0 caveats | **6 of 8, 2 fails, 0 caveats** |
| free-class C1 | 14/16 all · 10/12 free | **14/16 all · 10/12 free** |
| C1 `COAL_PRB` 2023 | 62.522 (−2.76) | **66.877 (+1.60)** — abs error **down 1.16** |
| C1 `COAL_PRB` 2024 | 59.651 (−0.30) | **61.718 (+1.76)** — abs error **up 1.46** |
| C1 `ST_GAS` 2023 / 2024 | FAIL −8.38 / −9.71 | **FAIL −8.38 / −9.71, unchanged** |
| C2 / C3a / C3b / C3c / C4 / C6 / C8 | — | **unchanged, every row** |
| C5a CO2 (REPORTED-ONLY) | −5.6 / −3.1 / +2.9 % | **−1.7 / −1.2 / +2.9 %** |
| C8 `COAL` forced-share 2023/2024 | **SKIPPED** (no class to score) | **PASS at 0.0 % forced** |

**Keeper 6's near-perfect 2024 coal row was an ARTIFACT of the blind spot** — it read −0.30 only
because 2.067 TWh sat in an unscorable class. The apparent accuracy was luck, not fidelity. The
degradation is real all the same and is stated rather than explained away.

**WHAT THIS DOES NOT FIX.** SPP is **NOT calibrated** and the scoreboard does not move. Both
`ST_GAS` rows still fail and C3c still fails in all three years (model 0 / 5 / 0 h above $200
against 42 / 59 / 68 actual). **Two failing criteria, so rule 22 `[R-C3C]` cannot fire** — it
requires a LONE failure. The named successor is **unchanged**: the ST_GAS offer / commitment
defect (model ST_GAS already 6.95 / 8.13 TWh below actual *before* either repair).

**GOVERNANCE DEFECT FOUND AND FIXED IN-LANE.** `replay_keeper.py --out-dir` does not propagate
`calibration_attestation.json`, so the span bundle first scored **C6 UNATTESTED** (grade 5 of 7).
`scripts/gen_spp62_attestation.py` authors it — ledger inherited verbatim, the census switch
declared under `governance.measured_input_switches` with its rule-23 argument, and `attested_by`
re-pointed at THIS lane rather than the inherited SPP-52a string it arrived with.

**TWO HAZARDS ROUTED, NEITHER CAUSED BY THIS LANE, NEITHER TOUCHED.**
1. **Re-deriving PJM's or MISO's coal supply CSV at HEAD with NO code change at all already
   re-ranks 5 PJM plants** (594, 876, 879, 3149, 6166) **and 10 MISO plants** (1082, 1091, 1733,
   2107, 4041, 4078, 6034, 7343, 8023, 56068) — the raw `f923_*.zip` receipt corpus their committed
   CSVs were built from is gone from `data/raw` and the generation fallback disagrees. SPP is the
   clean case (every row `source=generation`). Recorded in `data/raw/_processed-legacy/README.md`.
2. **`coal_supply_*.csv` is a solve-affecting registry table** covered by neither the capx D79
   solve-surface fingerprint (seven config *modules*) nor a `resolved_inputs` sha256 stamp. Harmless
   here — inertness is proven by direct measurement — but a real hole, stated rather than relied on.

**MATRIX INTEGRITY REPAIR, explicitly not a verdict.** `nyiso_hub_gap_month_level` (nyiso-223) and
`spp_curtailment_ceiling` (SPP-58) were added with cells in the other six shards and SPP's own
omitted, turning the CI guard RED. Both cell lines restored — `.` and **`U`** respectively. **Lane
SPP-58 is live and owns `spp_curtailment_ceiling`'s verdict**; SPP-62 measured nothing about it.

**Next shorthand: spp-23.** Next lever: **SPP-51b R-2**, the thermal-commitment floor (the LP
absorbs 98.2 % of concentrated curtailment headroom; thermal annual minimum 254.3 MW across a
~40 GW fleet) — or the **ST_GAS offer / commitment defect**, which is the only object that reaches
either failing C1 row. Then R-3 the zonal spread (measured |N−S| 12.13 / 17.23 / 15.18 against a
model ~1), then SPP-55/56 scarcity / C3c.

## spp-23 — 2026-09-10

**Lane SPP-63. ZERO LP SPENT.** Base `24737d3c`. Object as chartered: **R-az, the ST_GAS offer /
commitment defect**, named by SPP-62 §7 as the successor that "reaches either failing C1 row."
**Refused at phase 0 under rule 29 `[R-SCREEN]` clause 0** — the arm has a computable pre-solve gate
and does not pass it, so no shard was launched. Record:
`docs/handoffs/FINDING-spp-63-2026-09-10.md`. **Keeper UNCHANGED**
(`2026-09-10-spp-62-vintage-census`); nothing registered, nothing promoted, **no matrix cell verdict
minted**.

**THE FINDING.** The two failing `ST_GAS` rows are not an ST_GAS defect. Re-derived from the
keeper's committed sidecars and the committed EIA-930 benchmark:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model wind − actual | **+10.708** | **+11.407** | **+11.586** |
| scored thermal (C1 total) model − actual | **−10.196** | **−11.605** | *(C1 skipped, prelim 923)* |
| solar + hydro + nuclear, combined \|Δ\| | 0.25 | 0.41 | 0.48 |

The wind excess and the thermal deficit are **the same energy**, agreeing to **4.8 %** and **1.7 %**.

**The wind POTENTIAL is right; the CURTAILMENT is missing.** Re-derived this session from
`wind_cf × wind_cap` (the arrays the LP bounds on), independent of any prior lane's prose — and
matching SPP-51c's recorded potentials and SPP-58's recomputed 2024 bound:

| year | potential | model disp | actual | implied real curtailment | **share taken by the LP** |
|---|---|---|---|---|---|
| 2023 | 114.0552 | 113.7572 | 103.0490 | 11.0062 | **2.71 %** |
| 2024 | 120.9925 | 120.7235 | 109.3170 | 11.6755 | **2.30 %** |
| 2025 | 122.2552 | 122.0430 | 110.4570 | 11.7982 | **1.80 %** |

**THE BOUND THAT REFUSES THE ARM.** Only three scored classes carry any surplus at all —
`CT_PEAKER` **+2.407 / +2.725**, `COAL_PRB` **+1.598 / +1.765**, `CC_CHP` **+0.116 / +0.019** —
totalling **4.121** and **4.509** TWh against `ST_GAS` gaps of **8.380** and **9.712**. So **at most
49.2 % (2023) and 46.4 % (2024)** of the gap exists anywhere in the thermal stack, and even that
ceiling assumes a mechanism driving all three surplus rows to exactly their actuals. Every other
class is already *under*. **The remaining 4.26 / 5.20 TWh has no source in the thermal stack** — it
is the wind.

**WHY EACH CHARTERED CHANNEL IS CLOSED.** (a) `spp_gas_commitment_bridge` and `gas_commitment_bridge`
are **already `R`** (SPP-44's gate kill; SPP-46's rule-13 refusal of the measured-state form), and
their stated re-test condition is not met, so rule 28(a) forbids re-testing them. Measured
independently here and agreeing: every SPP fossil unit carries `pmin_mw = min_run_hours =
min_down_hours = startup_cost_per_mw = 0`, but `ST_GAS` is **already ON in 7,556 / 8,021 of 8,760
hours** — the gap needs **959 / 1,107 MW more in *every* hour**, while filling all 1,204 / 739
fully-off hours to a full 1 GW recovers only **1.2 / 0.7 TWh**. It is a *level* deficit inside
running hours, the one shape a min-gen floor cannot repair. (b) The authorized `offer_curve_by_group`
multipliers are a **level** lever (SPP-52a measured −6.00/−5.91/−6.03 %, flat to 0.12 pp), and the
bound above is the general refusal: re-ordering the stack cannot create energy the stack does not
contain, and no finite multiplier beats a competitor at MC = 0. (c) `tranche_startup_amortization` is
already `R` at max $2.14/MWh.

**CORROBORATION THIS LANE DID NOT PRODUCE.** Live lane **SPP-58**'s committed solved 2024 arm
(`3a699f10`, control = keeper 5) arms `spp_curtailment_ceiling`: wind **120.723 → 109.229** — within
**0.09 TWh** of the actual — gas family **84.02 vs 83.21 actual**, its gates G-2/G-3/G-4 all PASS.
**Reported against this lane's own reading:** the ceiling alone does **not** close `ST_GAS` (+0.801 of
11.5 TWh; most goes to `CC_REGULAR` +4.580 and `COAL_PRB` +4.484), and **keeper 7 is a harder basis**
than SPP-58's keeper-5 control, because the vintage repair took `ST_GAS` from 11.970 to 10.386 TWh —
projecting +0.801 onto keeper 7 gives ≈ −8.9 TWh, still outside the ±8.00 band. That projection is
arithmetic, not a measurement, and is offered as a caution to whoever composes the two objects.

**WHAT IS REAL — successor R-ba, the merit-order inversion.** Level-invariant, so it survives the
wind correction: SPP gas steam runs at **0.47 / 0.52 ×** its measured capacity factor while peakers
run at **1.23 / 1.18 ×**, and the model offers `ST_GAS` **above** `CT_PEAKER` at every stack depth to
6 GW (by $4.99–$6.99 in 2023) despite a **better** capacity-weighted heat rate (**10.543** vs
**10.974**; only VOM is higher, $4.00 vs $3.50). **Sequencing is binding: R-ba is not measurable
until the wind ceiling lands** — scored on a wind-oversupplied stack it would close a wind residual
through a gas offer, which is the fitted mechanism rule 1 `[R-STRUCT]` forbids.

**Rule 19 `[R-ONE-MECH]` enumeration, done and recorded:** nothing else floors or prices SPP `ST_GAS`
— no commitment floor, no bridge, no must-run, no reliability floor; the only live pricing channel is
`offer_curve_by_group` at a uniform 0.93 on the ten fossil classes.

**Rule 28 `[R-MECH-MATRIX]`:** no verdict minted — this lane tested no mechanism.
`spp_gas_commitment_bridge` / `gas_commitment_bridge` / `tranche_startup_amortization` stay **`R`**,
`spp_curtailment_ceiling` stays **`U`** and **belongs to SPP-58**, `offer_curve_by_group` stays
**`K`**. The shard's `gates:` stamp and the §5.7 prose header — both of which named the ST_GAS
successor — were re-stamped with the predecessor text preserved verbatim.

**Rule 23 `[R-FROZEN-DERIVE]`:** re-running `derive_campd_gas_commitment_params.py --iso SPP`
reproduced the committed `campd_gas_commitment_params_SPP.csv` **byte-identically**. The new `--ct`
artifact (`campd_ct_commitment_params_SPP*.csv`) is additive and is read by no solve path. SPP's own
measured conduct, per rule 25 `[R-ISO-SCOPE]` — no number transferred from any other ISO: `ST_GAS`
min-load **0.265957** / run-hours p50 14 h (cap-wtd 49 h); `CC_REGULAR` **0.440000** / 16 h (20 h);
`CT_PEAKER` **0.316735** / 9 h (10 h).

**Rule 31 `[R-RETAIN]`:** nothing was solved, so nothing is promotable and **nothing was deleted**.

**Next shorthand: spp-24.** *(Superseded within the same session — see the continuation below.
Lane SPP-58 was killed by owner instruction and SPP-63 took the wind object itself.)* Next lever:
**land the wind ceiling first**, then **R-ba**, the ST_GAS/CT_PEAKER merit-order inversion, measured
on the corrected stack. Behind those, unchanged: **SPP-51b R-2** (thermal-commitment floor), **R-3**
(zonal spread, measured |N−S| 12.13 / 17.23 / 15.18 against a model ~1), **SPP-55/56** (scarcity /
C3c). **SPP remains NOT-YET and is not calibrated**; two criteria still fail, so rule 22 `[R-C3C]`
cannot fire.


### spp-23 CONTINUATION — same lane SPP-63, same session: the wind ceiling was screened and KILLED

**Owner instruction, 2026-09-10, verbatim: _"No spp 58 was killed just proceed with your solve"_** —
issued against this lane's recommendation to defer to SPP-58. SPP-58 is dead, so
`spp_curtailment_ceiling` was unowned and SPP-63 took it. **PRECOMMIT**
`docs/handoffs/PRECOMMIT-spp-63-curtailment-ceiling-2026-09-10.md` pushed at `efd60202` **before any
solve**. **RESULT** `docs/handoffs/RESULT-spp-63-screen-2026-09-10.md`. **LP spent: ONE year
(~150 s)**, shard pinned `92b59c73`, branch `claude/spp63-screen-2025`. **THE SPAN WAS NOT SPENT.**
**Keeper UNCHANGED** `2026-09-10-spp-62-vintage-census`; nothing registered, nothing promoted.

**THE ARM DOES EXACTLY WHAT ITS ARITHMETIC SAYS.** 2025 wind **122.0430 → 110.2248 TWh** — a fall of
**11.818**, inside the pre-registered 9.0–15.0 band, landing **within 0.232 TWh of the EIA-930 actual
110.457** where the control was **+11.586** out.

**GATE BOARD** (all five pre-registered before the solve; none reads C1):

| gate | measured | verdict |
|---|---|---|
| G-1 config identity & liveness | ceiling `true`, depth `0.288137` at its declared default, ten fossil classes 0.93 × 4 | **PASS** |
| G-2 reach | wind −11.818 TWh (band 9.0–15.0) | **PASS** |
| G-3 allocation identity | decile-0 carries **26.049 %** of the removal vs a 10.000 % flat reference = **2.6049 ×** (gate > 1.15) | **PASS** |
| **G-4** no new forcing | dump **0.000** ✓, slack **0.0000 → 211.208 MWh** against a pre-registered ≤ 100.0 | **FAIL** |
| **G-5** no load-bearing regression | **C3b NRMSE 0.167 → 0.253** (band ≤ 0.20) — load-bearing **PASS → FAIL**; C3a survives at **+9.9 %** vs ±10 % (from +2.2 %); negative-price hours **167 → 0** | **FAIL** |

**Neither gate was re-cut.** The PRECOMMIT named G-5 the gate with real bite and named C3b's headroom
as **0.033**; the arm missed by **0.053**. Re-reading a gate against the result it would decide is
the fitted-mechanism selection rule 1 `[R-STRUCT]` condition (c) forbids.

**THE RESULT THAT MATTERS FOR C1 — and it runs AGAINST the wind hypothesis reaching the failing
rows.** The recovered energy goes to **COAL**, not gas steam: `COAL_PRB` **+7.099**, `CC_REGULAR`
**+3.680**, `CT_PEAKER` +0.641, while **`ST_GAS` FALLS 0.693 TWh**. The coal family goes from a
nearly-exact **+0.72** to **+8.69 TWh** against actual; the gas family improves −12.75 → −8.95 but
`ST_GAS` itself gets worse. This is the **spp-23 merit-order inversion** (gas steam at 0.47 / 0.52 ×
its measured CF, offered *above* `CT_PEAKER` at every stack depth to 6 GW despite a better
capacity-weighted heat rate 10.543 vs 10.974) operating on a correctly-sized stack for the first
time. **The wind repair does not reach the ST_GAS rows — it re-routes the error into coal.**

**Rule 28 `[R-MECH-MATRIX]`:** `spp_curtailment_ceiling` **`U` → `O`**, exactly as the PRECOMMIT
pre-registered for this outcome — **not `R`**. Three of five gates pass exactly, the mechanism is a
rule-14 `[R-ACCURATE]`-owed repair, and `R` would trip rule 28(a)'s do-not-redo against something the
model owes. Prior cell text preserved verbatim inside.

**Instrument built and validated, and it is reusable:** `scripts/lib/spp63_g5.py` rebuilds the run
payload's per-zone `pMon`/`dMon` from a bundle's committed hourly sidecars and applies the scorer's
own `score_price_mean` / `score_price_shape`. **Validated on keeper 7 before use** — C3a
25.65 / 25.79 / 29.23 and C3b 0.172 / 0.172 / 0.167, reproduced exactly. This is what made G-5
evaluable on an unregistered screen bundle at all: `calibration_verdict.py` can only score a
REGISTERED run and rule 29(2) forbids registering a screen, which is why lane SPP-58 had to report
its own G-5 as *unavailable*. (Load-bearing detail documented in place: the payload bins months on a
FIXED 365-day calendar, so a leap-aware reimplementation is a different statistic — measured to move
2024's C3b 0.172 → 0.170.)

**Rule 31 `[R-RETAIN]`: nothing was deleted.** `results/calibration/spp63_*/` is gitignored, which is
what discharges rule 29(c); no `rm` was issued. `scripts/gen_spp63_attestation.py` is committed and
ready (DOF 3 entries / 2 residual → **4 / 2**, the added `spp_curtail_depth_wind` entry carrying a
**measured** identification source) if the span is ever spent.

**Next shorthand: spp-24.** Next levers, in order: **R-bb — root-cause SPP price formation without
the phantom wind.** The keeper reproduces SPP's monthly price shape *while dispatching 11.8 TWh the
market curtailed*, so the shape is right for the wrong reason; C3b's doubling and the loss of all 167
negative-price hours are that dependency surfacing. **Do NOT re-cut `spp_curtail_depth_wind` to make
G-5 pass** — it is measured, one config across all years, and re-cutting it against a gate is
forbidden. Then **R-ba**, the ST_GAS/CT_PEAKER merit-order inversion, which this screen shows is
needed independently of the wind level. Behind those, unchanged: **SPP-51b R-2**, **R-3** (zonal
spread), **SPP-55/56** (scarcity / C3c). **SPP remains NOT-YET and is not calibrated.**

---

## spp-24 — 2026-09-10

**Lane SPP-64. ZERO LP SPENT.** Base `2a267cc4`. Object as chartered: **R-bb, SPP price formation
without the phantom wind** — root-cause the C3b regression and the loss of all 167 negative-price
hours that killed SPP-63's ceiling screen. **Root-caused at phase 0**; every candidate arm was
refused on a computable pre-solve gate under rule 29 `[R-SCREEN]` clause 0, so no shard was launched.
Record: `docs/handoffs/FINDING-spp-64-2026-09-10.md`. **Keeper UNCHANGED**
(`2026-09-10-spp-62-vintage-census`); nothing registered, nothing promoted, **no matrix cell verdict
minted**.

**THE FINDING — SPP's model is a one-zone market, and that single absence produces every open gate.**
The LP carries ONE internal transmission constraint (the N↔S link) and its two zonal prices are
**IDENTICAL in 87.4 / 86.1 / 76.8 % of hours**; mean |N−S| is **0.595 / 1.227 / 1.573** against a
measured hub spread of **12.129 / 17.227 / 15.180**, i.e. the model reproduces 5–13 % of SPP's
congestion rent. SPP's own published RTBM binding-constraint archive says what is missing:
**735 / 723 distinct internal constraints binding in 96.4 % / 97.9 % of ALL hours**, median binding
shadow price **$94.50 / $91.47**, maximum **$1,103.97 / $1,500.00**.

**THE KEEPER'S C3b PASS IS A CANCELLATION, MEASURED.** Clipping the measured actual into the model's
own observed price window and re-scoring the same model months moves NRMSE **0.1669 → 0.2562** (2025)
and **0.1724 → 0.2249** (2023) — and the 2025 summer deficit VANISHES (Jul/Aug/Sep −4.00 / −3.50 /
−7.43 → −0.81 / −1.53 / **+0.40**), leaving a near-uniform **+5 to +10 $/MWh body over-pricing**. The
missing tail is worth **+3.64 / +2.71 $/MWh** annually, so the body must run high to carry the mean;
the phantom wind pushes it back down in exactly the shoulder months (Mar/Apr hold the negative
regime AND two of the three largest positive C3b errors). The two errors are so nearly equal that
keeper-vs-tail-corrected (**0.2562**) ≈ SPP-63's arm-vs-raw (**0.253**). **2024 is the control**: its
window is contaminated to $421 by two infeasibility hours, so its clip is nearly a no-op
(0.1724 → 0.1771).

**PRICE DISTRIBUTION COMPRESSED AT BOTH ENDS.** 2025 model p5/p10/p99/max **+13.13 / +20.11 / 51.51 /
73.77** against actual **−11.35 / −2.21 / 176.91 / 1093.22**; median and p75 nearly right. Negative
hours **229 / 214 / 167** vs **992 / 1,172 / 1,018**; hours >$100 **0 / 7 / 0** vs **152 / 260 / 213**.
**In all 24 measured month-years the actual monthly MAXIMUM is 4–20× the model's** — the tail is in
EVERY month (2025's three largest are Oct, Apr, Mar), which refutes any summer-scarcity account on
its own.

**WHAT SETS THE NEGATIVE PRICE, AND WHY THE CEILING DESTROYS IT.** The model's minimum is **exactly
−26.000** in every year and both zones: wind's flat `-ira_ptc_wind` offer, a clamp not a
distribution (measured floor −37.25 / −36.03 / −35.56). `spp_curtailment_ceiling` is a multiplier on
the **CF UPPER BOUND**, and a unit held at its bound is never marginal — so bounded-off wind cannot
set a price at all. In the real market curtailment **IS** the negative-price event; the ceiling
reproduces its quantity half and discards its price half, which is why 167 → 0. **No value of
`spp_curtail_depth_wind` changes this** — the defect is the channel, not the coefficient — so
re-cutting the depth would be ineffective as well as forbidden, and this lane did not do it.

**THE SLACK IS A REAL ADEQUACY SIGNAL.** The KEEPER's own 2024 carries **370.1017 MWh in 2 zone-hours
at exactly $2,000.00** (`ISOConfig.voll` for SPP) — **1.75× the 211.208 MWh SPP-63 reports for its
arm**, in a year that PASSES. Slack IS the model's entire scarcity mechanism: between the top of the
thermal stack (~$74) and VOLL there is **nothing**, which is why C3c reads 0 / 5 / 0 — an absent tail,
not a mis-calibrated one. Reported as a measurement; SPP-63's gate was pre-registered and spent and
is NOT re-read here.

**CORROBORATION.** Every thermal class clears within a **~$5 band** (2025 p50: COAL_PRB 33.67,
CC_REGULAR 33.90, CT_PEAKER 35.22, ST_GAS 32.51) — R-ba's inversion is confirmed (ST_GAS 12.9 % CF
below CT_PEAKER 19.0 %) but is a re-ranking *inside* a band that should be tens of dollars wide.

**CORRECTION OWED TO SPP-63.** `RESULT-spp-63` §6 states the 2025 arm's slim artifacts "are committed
under `results/shard-staging/spp63/2025/`". **They were never committed to any ref** — the RESULT
commit `8fb9f0eb` carries three files (log, matrix shard, doc) and no artifacts. The promised zero-LP
differencing basis does not exist, so **no SPP-63 arm number is quoted here as re-derived**; the
diagnosis rests only on the committed keeper and the committed measured actuals. Separately,
keeper 7's `basis_sha` `67feede7…` does **not** resolve at this base (the 2026-08-16 history rewrite);
nothing here depends on it.

**ROUTING — card P1 is now servable, with a warning.** `data/raw/spp-binding-constraints/README.md`
still reads "Status: UNSERVED"; **the data has since landed**. This lane deliberately does NOT compute
the SPP-54-vs-SPP-57 ranking (choosing flowgate membership while reading the shares is rule-1
forbidden — it needs its own PRECOMMIT). Membership-free fact it does report: 2024 congestion rent is
carried by **444 facilities, top-20 = 47.4 %, 23 for half, 115 for 90 %** — **not a 3-zone object**,
the same shape as MISO RO-3's NO-BUILD verdict.

**SUCCESSORS.** **R-bc — price-forming curtailment**: the ceiling family is rule-14-owed and its
allocation is right, but it must enter as an **LP constraint whose dual reaches the zonal price**, not
a CF bound, so curtailment and the negative-price hour are ONE event; success = wind volume down AND
negative hours UP toward 1,018 AND congestion rent up AND C3b down. It **replaces**
`spp_curtailment_ceiling`, never stacks (rule 19). **R-bd — the upper tail is CONGESTION RENT, not
reserve scarcity**: SPP-55 measured the reserve route dead (1/0/0 hours of C3c overlap;
`energy_reserve_coopt` = `I`) and the every-month tail confirms it independently; not separately
screenable — R-bc and R-bd are one object. **R-ba unchanged and now bounded.** **SPP remains NOT-YET
and is not calibrated** — two criteria fail, so rule 22 `[R-C3C]` still cannot fire.

**Next shorthand: spp-25.**

## spp-25 — 2026-09-10

**SPP-64 SPAN — `st_gas_mustrun_per_plant` armed on SPP's ST_GAS fleet, 2023–2025. SOLVED,
REGISTERED, NOT PROMOTED.** Run `2026-09-10-spp-64-stgas-selfcommit`, bundle
`results/calibration/spp64_span`. Records: `docs/RESULT-spp64-span.md`, charter
`docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`, screen
`docs/handoffs/RESULT-spp64-screen-2023.md` (six of six §6 STOP gates PASS), arithmetic correction
`docs/handoffs/ADDENDUM-spp-64-g2-arithmetic-2026-09-10.md`, root cause
`docs/handoffs/FINDING-spp-64-2026-09-10.md`.

**THE HEADLINE: the scorer returns `CALIBRATED` — SPP's first — grade 7 of 8, 0 fails, 1 ledgered
caveat.** ONE `--years 2023 2024 2025` invocation, years sequential (rules 12 / 16), 12 min 5 s.
Control = keeper 7's **committed** bundle, differenced and **never re-solved** (rule 29(b) form 4).
Config identity: **exactly ONE live field moves** (838 `scenario_config` keys compared; the other
three diffs are fields added since the keeper solved, materializing at declared defaults with their
gate OFF). `offer_curve_by_group` **byte-identical**, `st_gas_mustrun_p25_level` **False** in both.

**C1 FAIL → PASS, and BOTH failing rows close on volume AND share.** 2023 ST_GAS −8.380 → **−6.034**
TWh (share_pp −2.94 → −2.12); 2024 −9.712 → **−7.423** (−3.34 → −2.55), against a ±8.00 TWh / ±3 pp
band. Free-class C1 **14/16 all · 10/12 free → 16/16 · 12/12**. Two neighbours move *toward* their
actuals: COAL_PRB +1.598 → +0.526 (2023) and +1.765 → +0.762 (2024); CT_PEAKER +2.407 → +1.881 and
+2.725 → +2.091. C2 gas `C1 flags: ST_GAS` → **all classes in band**. Gross ST_GAS **+2.3314 /
+2.2886 / +2.5736 TWh**, paid by coal and the other two gas classes, **not** by curtailing wind
(−0.0150 / −0.0106 / −0.0071); energy conserved to ±0.0013 TWh; slack and dump **byte-identical** to
the keeper (dump 0; slack 0 / 370.102 / 0 MWh). **2025 C1 is SKIPPED for every class** (preliminary
EIA-923), so the C1 verdict rests on 2023–2024.

**THE DETERMINATION FLIP IS C1'S ALONE.** C3c is **unchanged at full magnitude** — 0 / 5 / 0 model
hours above $200 against 42 / 59 / 68 actual, system price max byte-identical (59.313 / 2000.000 /
73.773), so not one tail hour moved. It merely reclassified to a ledgered CAVEAT under rule 22
`[R-C3C]`'s standing rule once C1 closed and it became the **lone** failure. SPP's absent tail
(R-bd) is exactly as absent as before. Reported and NOT claimed as evidence (rule 1 forbids judging
a mechanism by the residual): C3a **+2.1 / +1.3 / +2.2 % → +1.0 / +0.1 / +0.7 %**, C3b 0.172 / 0.172
/ 0.167 → 0.173 / 0.171 / **0.163**, C4 improves in 5 of 6 rows, C5a within 0.2 pp.

**THE ADVERSE FINDING — D-4 PER-UNIT CONDUCT RIDER FAILS IN ALL THREE YEARS, and this lane will not
absorb it.** 4 / 5 / 3 FAILing rows where **the keeper carried zero**; `D4.passed` True → False.
Plants **1230, 1235, 1271 fail in EVERY year** (3008 in 2023–24, 6193 in 2024) with measured median
**0.000 MW** over the hours the floor binds for them and **59–83 %** of those hours metered at zero.
That is rule 17 `[R-FLOOR-WINDOW]`'s signature at the per-unit grain — *"a floor binding in hours its
own driver evidence says the class is offline is a bug by definition"* — and it is a **window-construction**
defect: the top-system-load placement is verified by the meter for **15/19, 15/20, 17/20** plants and
**falsified** for the rest. Magnitude 0.0595 / 0.0763 / 0.0216 TWh = **2.56 / 3.26 / 0.85 %** of the
mechanism's forced energy. The class-level D-4 window leg PASSES (`offwindow_share` 0.0000,
self-windowing h0-23).

**CRITICALLY, THE RIDER NEVER REACHED THE DETERMINATION.**
`calibration_verdict._score_forced_share` consults `_d4_provenance` **only** for a class ABOVE its
cap, and ST_GAS came in under — rule 20 `[R-FORCED-BUDGET]` forced share **0.1962 / 0.1849 /
0.1744** against `d2_merchant_max_share` 0.30 (ST_GAS is NOT in `d2_exempt_classes`, so this is a
real test) — so **C8 passed on the share alone and the `CALIBRATED` headline was produced by a code
path that never examined this defect.** Stated plainly so no one quotes the determination without
it. The PRECOMMIT's pre-declared ~0.33 forced-share risk **did not materialise**, so the rule's
conditional-pass limb was never reached and the "is a 100 %-regulated class a *merchant* class"
question is **left open** rather than answered by a lane that did not need to answer it. Every other
class stays 0.0 % forced, so rule 19 `[R-ONE-MECH]` holds on the solved artifact and not merely on
the pre-solve census.

**D-1 passes comfortably and IMPROVES**: `profile_r` **0.997 / 0.999 / 0.997** (bar 0.80) and
`cv_ratio` **2.117 / 1.844 / 1.717** moving *toward* 1.0 from the keeper's 2.161 / 2.060 / 2.244
(bar 0.50, one-sided — so the improvement earns the arm nothing, but it is evidence the floor
reproduces observed conduct rather than flattening it). The PRECOMMIT called D-1 "the genuinely
uncertain leg"; it was not close.

**RULE 21 `[R-DOF]`: ZERO free parameters added** — ledger inherited at n_entries 3 / n_residual 2
(`offer_curve_by_group`, `offer_curve_smoothing`, `wefor_multiplier`), verified from the written
attestation. The level used is `committed_pct` (the P5-of-online LSL), the **smallest** of the three
the artifact offers (9.090 TWh all-on vs `p25_cf` 14.427 and `median_cf` 23.319), fixed ex ante.
`st_gas_mustrun_p25_level` is **refused for SPP** on rule 25 `[R-ISO-SCOPE]`: its rationale is
MISO's own out-of-market VLR record (Entergy South) and SPP has no equivalent driver.

**RECOMMENDATION: PROMOTE, with the window defect opened as the immediate successor card and NOT
absorbed. NOT ACTED ON — promotion is the OWNER's call (rule 31 `[R-RETAIN]`);
`frontend/data/backcast/keepers/SPP.json` is UNTOUCHED and SPP's designated keeper remains
`2026-09-10-spp-62-vintage-census`.** The rule-1 `[R-STRUCT]` case: the incumbent gives a fleet
measured **100.0 % EIA-860 Sector 1** (9,515 of 9,515 MW) **no commitment structure at all** —
ST_GAS forced 0.0 % and absent from D-2 entirely — so the choice is *right on ~80 % of the fleet vs
right on none of it*, and reverting would trade a 2.3 TWh structural repair for a 0.02–0.08 TWh
defect while restoring a larger error. The case against is stated first in the RESULT: a recurring
rule-17 defect is a bug by rule 17's own words, and a defensible owner decision is to refuse, repair
the window and re-solve (**~12 min of LP**, costed). The successor is specific — re-derive the
placement rule for plants whose measured operation is not top-system-load correlated — and is
explicitly **NOT** a `mustrun_plant_exclusions` reach, per miso-170's own warning that excluding a
conduct-test failure "would bury that error inside a membership list".

**RETENTION (rule 31 `[R-RETAIN]`): nothing was deleted.** `results/calibration/spp64_*/` is
gitignored (`.gitignore:1914`), which is what discharges rule 29(c); the bundle lives on ephemeral
local disk and does not survive the container. The committed slim files + `hourly/` sidecars are
what a later lane differences against without re-solving. Registration used `--no-prune` (SPP has 2
runs against a cap of 15, so the sweep is a no-op, and which run is the keeper is the open question).

**`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated against:
every number here is model-**SELECTION** evidence, and **`CALIBRATED` is a rubric determination, NOT
a certified out-of-sample skill claim.**

**Next shorthand: spp-26.**

## spp-26 — 2026-09-10

**PROMOTION — `2026-09-10-spp-64-stgas-selfcommit` is SPP's EIGHTH KEEPER, and SPP's FIRST
`CALIBRATED` determination.** Promoted **by owner ruling in-session**, verbatim: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper."* Lane SPP-64 had recommended promotion in spp-25 and had **not** acted;
`frontend/data/backcast/keepers/SPP.json` stayed untouched until the ruling (rule 31 `[R-RETAIN]`).

**Promotion procedure executed in full, one PR** (`frontend/data/backcast/keepers/README.md`):
1. `keepers/SPP.json` → `2026-09-10-spp-64-stgas-selfcommit`, with the run's provenance, its gate
   table, and **the defect it carries** recorded in the note.
2. `scripts/build_status.py --iso SPP` → `status/SPP.js` + `status/shared.js`, reading
   **`[SPP:CALIBRATED]`** (rebuilt again after the prune so it names no pruned run).
3. **R-T gate-(a) re-key in the SAME PR**: `frontend/data/forecast/program-status.json`
   `isos.SPP.gate.a_keeper_marker` now names the new run. **Status `fail` → `fail`, unchanged** —
   R-T is a STAMP re-key that reads no determination, and SPP still has **no `complete` entry**, which
   this promotion deliberately does **not** create (that is a separate owner act and was not
   requested). `check_gate_a_provenance.py` OK, 7 rows.
4. Rule 28 `[R-MECH-MATRIX]`: `st_gas_mustrun_p25` cell **O → K** in **SPP's shard only**, plus the
   `keeper` and `gates` stamps.

**Rule 15 `[R-DASHBOARD]` keeper-only retention executed** — rule 31's trigger (i) is met now that
the owner has ruled. `prune_iso_runs.py --iso SPP` removed the superseded keeper 7 (registry sidecar,
run payload and `results/calibration/spp62_span`); **1 pruned, 1 kept**. Git history is the record and
keeper 7's FINDING docs are retained.

**A retention trap was hit and repaired before pruning, and it is worth recording because keeper 7's
own note predicted it.** The first prune attempt reported keeper 7 as **PROTECTED — cited by a
governance file**, because the new keeper note named it **by run id**. That is exactly the failure
keepers 3–7 each warned about: `prune_iso_runs.py`'s citation guard scans `keepers/<ISO>.json`, so a
run id written there is shielded from retention and later dangles. The note was rewritten to cite the
predecessor **by lane** (`keeper 7 (lane SPP-62)`), and the prune then behaved correctly. **Keep
citing predecessors by lane.** A stale "registered but NOT promoted" sentence left in the matrix
cell's own evidence was also repaired in the same pass; the remaining references to the pruned id in
SPP.js are historical evidence in *other* cells, which is normal.

**Post-promotion checks, all green**: `audit_keepers.py --iso SPP` PASS (0 failures, 0 warnings;
keeper / holdout / marker / status rows all clean) · `check_registry_payload_parity.py` OK (41 runs,
73 bundle dirs, 0 unsynced) · `check_gate_a_provenance.py` OK · `check_mechanism_matrix.py` exit 0 ·
the promoted run re-scores **CALIBRATED** by run id.

**WHAT THE KEEPER IS AND WHAT IT CARRIES** is spp-25 above and `docs/RESULT-spp64-span.md`; the
headline is unchanged by promotion — grade 7 of 8, 0 fails, 1 ledgered C3c caveat; C1 FAIL → PASS on
both failing ST_GAS rows (volume **and** share); free-class C1 16/16 · 12/12; and **the flip is C1's
alone** (C3c unchanged at full magnitude, 0/5/0 vs 42/59/68). **The keeper carries a known,
recorded rule-17 defect** — the D-4 per-unit conduct rider FAILS in all three years (4/5/3 rows;
keeper 7 carried zero; plants 1230/1235/1271 in every year) and **reached no scored criterion**
because C8 passed on the share alone (forced share 0.1962 / 0.1849 / 0.1744 vs cap 0.30), so
`_d4_provenance` was never consulted. That is written into the keeper note, the gate-(a) detail and
the matrix cell so it cannot be lost.

**OPEN CARDS carried forward, unchanged by this promotion**: **R-be (NEW)** — re-derive the floor's
placement rule for ST_GAS plants whose measured operation is not top-system-load correlated;
explicitly **not** a `mustrun_plant_exclusions` reach (miso-170: excluding a conduct-test failure
"would bury that error inside a membership list"). **R-bd** — the absent upper tail is congestion
rent, not reserve scarcity. **R-bc** — price-forming curtailment, which must enter as an **LP
constraint whose dual reaches the zonal price**, replacing `spp_curtailment_ceiling` and never
stacking. **R-ba** — the merit-order inversion. And `FINDING-spp-64`'s root cause stands: SPP's model
is effectively a **one-zone market**.

**`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated against:
**`CALIBRATED` is a rubric determination, NOT a certified out-of-sample skill claim.**

**Next shorthand: spp-27.**

## spp-27 — 2026-09-10

**CARD R-be — the keeper's named, unfixed rule-17 `[R-FLOOR-WINDOW]` defect — is ATTACKED AT THE
GRAIN, and the grain half LANDS. The card does NOT close, and this entry says so before it says
anything else.** New registered run `2026-09-10-spp-27-commitment-grain`
(`results/calibration/spp27_span`), **CALIBRATED**, grade 7 of 8, 0 fails, 1 ledgered C3c caveat —
**identical to keeper 8 on every scored criterion**, both re-scored live at HEAD rubric v3.7.
Records: `docs/RESULT-spp27-span.md`, `docs/RESULT-spp27-screen-2023.md`,
`docs/handoffs/PRECOMMIT-spp-27-commitment-grain-2026-09-10.md`,
`docs/handoffs/ADDENDUM-spp-27-registration-seam-2026-09-10.md`,
`docs/SHARDREPORT-spp27-screen-2023.md`, `docs/SHARDREPORT-spp27-span.md`.
**NOT PROMOTED — `frontend/data/backcast/keepers/SPP.json` is UNTOUCHED and SPP's designated keeper
remains keeper 8 (lane SPP-64). Promotion is the owner's call (rule 31 `[R-RETAIN]`).** SPP still
holds **no `complete` marker and no `frontier` declaration**, and this lane creates neither.

**THE OBJECT, re-diagnosed rather than inherited.** The keeper note and the handoff both read R-be as
*"their operating hours are simply not top-system-load correlated"*. Phase 0 (zero LP, from the
committed bench and three `run_year(fleet_only=True)` rebuilds) **falsifies half of that**: 1230's
floor window is **3.5×** enriched in its own online hours over the plant's base rate (1271 **4.2×**,
1235 **3.3×**), so those plants ARE load-correlated. What the census found instead is a **GRAIN**
defect. The floor asserts a COMMITMENT — a day-ahead, whole-operating-day decision by a
vertically-integrated utility — but the engine placed it by ranking **individual hours** by system
load, so it carried the diurnal shape of LOAD, not of COMMITMENT. **The driver measurement is SPP's
own and is unambiguous**: the peak-to-mean of each plant's ONLINE hour-of-day profile is
**1.007–1.146 on 21 of the 22 ST_GAS plants** (only Mooreland 3008 at **1.609** genuinely
two-shifts) and the night/afternoon share of online hours is **0.78–1.09 on 19 of 22** — when these
units are synchronized they run through the overnight trough. **The physics statement is the
decisive one (rule 18 `[R-PHYSICS]`): the incumbent window implies 2,843 STARTS in 2023 against the
meter's 647 — 4.39× — including 202 asserted starts on 989 MW Muskogee in 2024 against 27 measured,
307 on Plant X against 45, 179 on 883 MW Wilkes against 11. A gas-steam unit cannot start 200 times
in a year.**

**THE ARM: `mustrun_window_commitment_grain`, a NEW gated `ScenarioConfig` field, default off.** The
window becomes `round(k/24)` whole operating days ranked by that day's MEAN system load — the
mechanical lift of the incumbent's own hourly ranking to the commitment period, **same signal, same
ordering statistic, one grain coarser**. SIZE (`online_frac`), LEVEL (`committed_pct`) and MEMBERSHIP
untouched. Armed: window peak-to-mean **1.0000 in all three years by construction** and implied
starts **288 / 342 / 315**, i.e. FEWER than the meter records — a conservative commitment scaffold.
**Rule 21 `[R-DOF]`: ZERO free parameters** (no threshold, share, multiplier or length; the grain is
the operating day), ledger inherited at n_entries 3 / n_residual 2. **Rule 13 `[R-MEASURED]`: nothing
measured enters the PLACEMENT** — the ranking is the model's own load shape — so unlike
`mustrun_online_frac_per_year` the field is deliberately **NOT** registered backcast-only. **Rule 25
`[R-ISO-SCOPE]`:** default `False`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at that declared
default, so every pre-existing cache key of all seven ISOs is byte-stable and **no other ISO moves**.

**PROTOCOL.** PRECOMMIT pushed at `32dfd75e` **before any LP**. Screen year **2023**, named on the
mechanism's OWN largest measured footprint (**858,999.2 MWh of floor moved, 22.20 %**, against
19.61 % and 19.25 %) and demonstrably **not** the residual year (2024 carries the larger C1 miss and
the smaller footprint). **Six pre-registered STRUCTURAL STOP gates, NONE of which reads the target** —
the target is the D-4 rider, so no gate reads D-4 or any per-plant conduct statistic — and **six of
six PASS**. G-DRIFT returned **ZERO** solve-path files changed between the keeper's `basis_sha` and
this base, so form 4 held and **no control solve was spent**. Span: ONE `--years 2023 2024 2025`
invocation, **499 s**, **exactly ONE differing `scenario_config` key across the whole config**,
`offer_curve_by_group` byte-identical, dump 0 and slack byte-identical to the keeper
(0 / 370.1017 / 0 MWh), system price max byte-identical (59.3126 / 2000.0000 / 73.7731) — **so C3c
could not and did not move a single hour.** ST_GAS gross **+0.2801 / +0.2004 / +0.2403 TWh**, paid by
coal and CC_REGULAR and **not** by curtailing wind (−0.011 %). C8 ST_GAS forced share
0.1962/0.1849/0.1744 → **0.2112 / 0.1969 / 0.1825** against a 0.30 cap, still under in all three
years. D-1 passes with `cv_ratio` moving further toward 1.0 (2.117/1.844/1.717 → 1.672/1.515/1.338)
and `profile_r` 0.997/0.999/0.997 → 0.987/0.997/0.992, far above its 0.80 bar.

**THE ADVERSE FINDING, REPORTED NOT ABSORBED — R-be DOES NOT CLOSE.** `D4.passed` is still False and
the conduct-FAIL count is **4 / 4 / 4** against the keeper's **4 / 5 / 3 — the same total of 12
rows.** It removes 1230 in 2024 (`measured_zero_share` 0.5906 → 0.4408, PASS) and improves
1230/1235/1271 in **all nine** of their year-rows without crossing the bar elsewhere
(2023: 0.7018 → 0.6096, 0.6230 → 0.5606, 0.6976 → 0.5875), and it **ADDS Mooreland 3008 in 2025**
(0.4735 → 0.5262). Mooreland is the one measured two-shifter in the fleet, so a uniform whole-day
window is the wrong grain for it — **exactly what the charter predicted, in both directions, before
the solve.** **Mooreland is NOT special-cased**: a per-plant grain predicate needs a threshold, which
is a free parameter (rule 21), and choosing it against this statistic is the fitted-mechanism
selection rule 1 `[R-STRUCT]` (c) forbids; a plant exclusion is refused on miso-170's own warning
that it *"would bury that error inside a membership list"*. **What remains of R-be**: day SELECTION
(for 1230/1235/1271 the day-selection lift over chance is only ~2×, and **no forecast-admissible
signal available to this model reaches it**), plus a SIZE component that is **not a defect** (pooled
`online_frac` is the rule-13-admissible construction and necessarily mis-sizes an individual year;
`mustrun_online_frac_per_year` is **refused** here as backcast-only).

**VARIANTS MEASURED AT PHASE 0 AND DELIBERATELY NOT TAKEN**, declared so the choice cannot be read as
hidden: a day-**PEAK** ranking key and a **NET-load** signal each score marginally better on the
conduct-overlap statistic (net+peak **0.8368** against day-mean-gross **0.8238** over 65 plant-years).
Both refused — each bundles a second, independently-unmotivated change into the same arm, and
net-vs-gross is a **wash at the hour grain** (0.8168 vs 0.8168). **Nothing was swept against any
gate.**

**THE RECOMMENDATION IS PROMOTE, AND THE CASE AGAINST IS STATED FIRST** (`RESULT-spp27-span.md` §8):
the arm buys **no score at all**, does not close the card it was chartered against, and costs +3–5 %
forced energy. The case for is rule 1 `[R-STRUCT]`'s own test — a run is a keeper because it is the
most structurally faithful, and a structurally-correct mechanism is never rejected because the
residual didn't move. **The choice is the same numbers with a floor that asserts a possible
commitment, or the same numbers with a floor that asserts an impossible one.**

**ALSO RECORDED, ROUTED NOT FIXED — an instrument defect.**
`scripts/lib/bundle_fleet.reconstruct_bundle_fleet` is **order-dependent across years within a
process** for SPP: the control's 2025 mechanism-16 floored energy read **3.477892**, **3.758881**
(alone, reproduced exactly twice) and **4.263776** depending on which years were built before it in
the same process. **2023 is stable at 3.870051 in every history**, which is why the screen gates —
all set on 2023 — are unaffected, and every qualitative span conclusion holds under every history.
**Nothing scored is affected**: scored numbers come from the solved bundles, and the solve builds
years sequentially in one process identically for control and arm. Not this lane's object.

**Process notes kept rather than tidied:** the parent misread the wall clock and launched a duplicate
screen shard (cost: one ~5-minute LP); the first span shard went idle asking for clarification and
was re-launched with a plainer prompt. Neither destroyed any result (rule 31). Registration used
`--no-prune`. The bundle's `unit_hourly_*` / `network_*` parquets (~48 MB) were deliberately not
carried onto the lane branch — the committed set matches the keeper's (3.1 MB). Post-run checks all
green: `check_mechanism_matrix.py` exit 0 with the new field registered,
`check_registry_payload_parity.py` OK (42 runs, 74 bundle dirs, 0 unsynced),
`audit_keepers.py --iso SPP` PASS (0 failures, 0 warnings).

**`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated against:
**`CALIBRATED` is a rubric determination, NOT a certified out-of-sample skill claim.**

**Next shorthand: spp-28.**

## spp-28 — 2026-09-11

**PROMOTION — `2026-09-10-spp-27-commitment-grain` is SPP's NINTH KEEPER.** Promoted **by owner
ruling in-session**, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper."* Lane SPP-27 had
recommended promotion in spp-27 and had **not** acted; `frontend/data/backcast/keepers/SPP.json`
stayed untouched until the ruling (rule 31 `[R-RETAIN]`).

**PROMOTED ON STRUCTURE, NOT ON SCORE — and the record says so plainly.** The run buys **no score at
all**: every scored criterion, the grade (7 of 8), the 0 fails, the single ledgered C3c caveat and
the free-class C1 16/16 · 12/12 are **identical to keeper 8**, both re-scored live at HEAD. `dump`,
`slack` and the system price max are byte-identical, so C3c could not and did not move an hour. What
it buys is the floor's own shape (mechanism-16 window peak-to-mean **1.2349 / 1.2159 / 1.2159 →
1.0000**, against a measured commitment peak-to-mean of **1.007–1.146 on 21 of 22 plants**) and the
starts it asserts (**2,843 → 288** in 2023 against the meter's **647**; the incumbent asserted
**202 starts on 989 MW Muskogee in 2024 against 27 measured**). Rule 1 `[R-STRUCT]`'s own test.

**Promotion procedure executed in full, one PR** (`frontend/data/backcast/keepers/README.md`):
1. `keepers/SPP.json` → `2026-09-10-spp-27-commitment-grain`, with the run's provenance, its gate
   table, and **the defect it still carries** (card R-be) recorded in the note; predecessors cited
   **by lane**, never by run id, per the citation-guard trap keepers 3–8 each recorded.
2. `scripts/build_status.py --iso SPP` → `status/SPP.js` + `status/shared.js`, reading
   **`[SPP:CALIBRATED]`** (rebuilt again after the prune so it names no pruned run).
3. **R-T gate-(a) re-key in the SAME PR**: `frontend/data/forecast/program-status.json`
   `isos.SPP.gate.a_keeper_marker` now names the new run. **Status `fail` → `fail`, unchanged** —
   R-T is a STAMP re-key that reads no determination, and SPP still has **no `complete` entry**,
   which this promotion deliberately does **not** create. `check_gate_a_provenance.py` OK, 7 rows.
   **The SPP-64 encoding trap was hit and avoided**: the file is stored `ensure_ascii=True`, and a
   first re-serialization with `ensure_ascii=False` rewrote 313 lines across every ISO; it was
   reverted and redone, so the committed diff is **1 line, SPP only**.
4. Rule 28 `[R-MECH-MATRIX]`: `mustrun_window_commitment_grain` cell **O → K** in **SPP's shard
   only**, plus the `keeper` and `gates` stamps and the §5.7 prose header.

**Rule 15 `[R-DASHBOARD]` keeper-only retention executed** — rule 31's trigger (i) is met now that
the owner has ruled. `prune_iso_runs.py --iso SPP` removed the superseded keeper 8 (registry
sidecar, run payload and `results/calibration/spp64_span`); **1 pruned, 1 kept**. Git history is the
record and keeper 8's RESULT/PRECOMMIT docs are retained. The remaining reference to the pruned id
in `SPP.js` is historical evidence in the `st_gas_mustrun_p25` cell, which is normal.

**ALSO IN THIS PR — ~48 MB of out-of-convention bundle payload removed from the tip.** The span
shard committed `unit_hourly_*` and `network_*` parquets on its own branch, which merged to `main`
ahead of the lane branch. The keeper convention (rule 15) is `class_band_hourly` / `class_hourly` /
`storage` / `system`, which is what keeper 8 carried; those six files are untracked here so the
committed bundle is **3.1 MB**. They remain recoverable from history.

**Post-promotion checks, all green**: `audit_keepers.py --iso SPP` PASS (0 failures, 0 warnings) ·
`check_registry_payload_parity.py` OK (42 runs, 74 bundle dirs, 0 unsynced) ·
`check_gate_a_provenance.py` OK · `check_mechanism_matrix.py --base origin/main` exit 0 · the
promoted run re-scores **CALIBRATED** by run id.

**OPEN CARDS carried forward.** **R-be (STILL OPEN, and now carried on the keeper)** — the D-4
per-unit conduct rider is **4 / 4 / 4** against keeper 8's 4 / 5 / 3, **the same total of 12 rows**.
What remains is **day SELECTION** for plants whose commitment is not system-load driven, and this
lane found **no forecast-admissible signal that reaches it** and says so rather than inventing one;
Mooreland 3008 is deliberately **not** special-cased. **R-bd** — the absent upper tail is congestion
rent, not reserve scarcity. **R-bc** — price-forming curtailment, which must enter as an **LP
constraint whose dual reaches the zonal price**, replacing `spp_curtailment_ceiling` and never
stacking. **R-ba** — the merit-order inversion. And `FINDING-spp-64`'s root cause stands: SPP's model
is effectively a **one-zone market**. **NEW, routed not fixed** — `reconstruct_bundle_fleet` is
order-dependent across years within a process for SPP.

**`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated against:
**`CALIBRATED` is a rubric determination, NOT a certified out-of-sample skill claim.**

**Next shorthand: spp-29.** *(spent — see below.)*



---

## spp-29 — 2026-09-11

**Object: card R-bd, SPP's absent C3c price tail. VERDICT: R-bd's premise is FALSE and the card is
CLOSED as chartered. ZERO LP SPENT** (rule 29 `[R-SCREEN]` clause 0). **Keeper UNCHANGED**
(`2026-09-10-spp-27-commitment-grain`, read never written), **determination UNCHANGED**
(`CALIBRATED`, grade 7 of 8, 0 fails, 1 ledgered C3c caveat). Nothing solved, nothing registered,
no verdict minted, **no `rm` issued**, and no promotion question to put because nothing promotable
was produced. Record: `docs/handoffs/FINDING-spp-29-c3c-price-tail-2026-09-11.md`; instrument
`scripts/probes/_spp29_c3c_phase0.py` (`--report` reproduces every number).

**THE REFUSAL.** `FINDING-spp-64` §9 chartered R-bd as *"the upper tail is CONGESTION RENT, not
reserve scarcity."* Measured on SPP's own published archives, it is neither:

1. **The scored quantity is a HUB AVERAGE.** `derive_actual_tail.py` reads
   `actual_lmp_hourly_SPP.rt`, which equals the two-hub mean to **6.1 × 10⁻⁵ $/MWh**. **Both** hubs
   clear > $200 simultaneously in **32 / 31 / 50** of the 42 / 59 / 68 tail hours, median *lower*
   hub **$230.80 / $211.28 / $259.38** — a system-wide energy event, which N↔S congestion does not
   move. (The model side is scored as the **max** zonal dual, an asymmetry generous to the model,
   which still reads 0 / 5 / 0 — re-derived from the keeper's committed sidecars, matching the
   registered payload exactly.)
2. **Congestion does not select the tail.** From `RTBM-BC-YEARLY-2024`: tail hours sit at the
   **53.2nd** percentile of binding-constraint count and the **54.2nd** of distinct facilities; the
   top-59 hours by facility count overlap the tail **1 / 59**; and
   **spearman(hourly congestion rent, RT hub price) = +0.019** (max shadow price +0.079). SPP-64's
   97.6 % binding-hours census is reproduced — congestion is what happens in *every* hour, not what
   distinguishes a tail hour.
3. **DECISIVE — SPP's own day-ahead market, which HAS all ~730 constraints at full nodal
   resolution, produces no tail either.** DA cleared > $200 in **0 / 42**, 14 / 59 and **0 / 68** of
   the RT tail hours; **2025's DA annual maximum is $176.62** against 68 RT hours above $200. The
   median RT − DA wedge in tail hours is **+$227.48 / +$181.67 / +$244.04** against −$4.39 / −$4.07
   / −$5.60 in an ordinary hour, and **40 / 42, 32 / 59, 66 / 68** tail hours had DA clear below
   $100. A fully nodal *hourly* optimization of SPP does not produce the tail, so a reduced zonal
   split of SPP cannot.

**NOR IS IT A QUANTITY ERROR.** Against EIA-930 (alignment measured, r = 0.98369), the keeper's net
load in the tail hours is right to **−0.52 / −0.25 / −0.44 GW** — ≤ 1.4 % — and **the phantom wind
is not there** (+0.18 / **−1.20** / +0.31 GW in tail hours against +0.85 / +1.33 / +1.35 annually).
Reaching $200 needs **10,096 / 5,758 / 11,094 MW** removed — **43.6 % / 15.2 % / 39.6 %** of that
hour's net load. Nor is it the offer ceiling: the stack carries **1,788 / 2,319 / 1,809 MW above
$200** with a maximum unit MC of **$725.99 / $649.91 / $538.57**.

**THE POSITIVE IDENTIFICATION — a PERFECT-QUANTITY hourly LP still FAILS C3c in all three years.**
Price the keeper's own fleet against SPP's **metered** net load with perfect foresight (a
merit-order screen, **validated** against the keeper LP at spearman **0.981 / 0.984 / 0.951** and an
**exact** match on the scored tail count 0 / 5 / 0, and deliberately tighter than the LP since it
omits storage):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| perfect-net-load hours > $200 | 7 | 29 *(6 literal infeasibility)* | **0** |
| perfect-net-load annual max | $361.73 | $507.50 | **$166.50** |
| actual RT | 42 | 59 | 68 |
| C3c band `[0.5×, 2.0×]` | 0.1667× **FAIL** | 0.4915× **FAIL** | 0.0000× **FAIL** |
| median markup the market charged over the marginal unit's cost | **+$241.04** | +$207.82 | **+$254.20** |
| as a multiple of that cost | **9.5×** | 7.3× | **9.4×** |

Hand the model the market's own metered quantities and **2025 prices out with a maximum of
$166.50** — it cannot reach $200 once, in a year the market did 68 times. The residual is an
**offer markup of 7.3–9.5× marginal cost in real time**, which a marginal-cost LP does not contain
and which cannot be closed without the fitted adder rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`
forbid.

**RULE 22 `[R-C3C]`: the classification is EARNED, and this is SPP's first measurement of it.** The
lane recommends **no change to C3c's standing and proposes no rubric change**. One hazard is named
rather than left implicit: on the rubric's own **reported-only DA row** SPP would read
PASS / FAIL / PASS — **reported as a measurement of the limitation's size, explicitly NOT a
proposal**, because moving a criterion to the basis on which it passes is gate-shopping and is the
owner's call alone.

**RULE 28(a) DO-NOT-REDO honoured.** `energy_reserve_coopt` (**`I`**, SPP-55) was **not**
re-tested; it is corroborated from a new direction by the tail's RT−DA character. No arithmetic
bound is claimed from the offer caps — SPP's CRDC steps are $275 / $550 / $1,100 per MW (Protocols
v119 §4.1.5.2), far above $200 — so that kill rests on SPP-55's measured **non-overlap** (1 / 0 / 0
hours), not on the level. `spp_curtailment_ceiling` (`O`), `negative_renewable_offers` (`I`) and
`spp_gas_commitment_bridge` (`R`) likewise not re-tested. **No cell moved**;
`internal_congestion_split` and `ordc_scarcity_overlay` received **annotations without a cell move**
(the SPP-55 / SPP-64 precedent). `offer_curve_by_group` stays at the keeper's uniform 0.93 and was
not re-cut, swept or examined against C3c; DOF ledger unchanged (3 / 2).

**OPEN CARDS.**
- **R-bd — CLOSED as chartered.** Do not re-open it as a congestion object without evidence
  meeting rule 28(a)'s re-test condition. **A topology change is recommended AGAINST for C3c**:
  SPP-64 §8's census (115 facilities for 90 % of rent) already said the rent is not a 3-zone
  object, and §1c says the build would not reach the tail even if it were perfect.
  `internal_congestion_split` stays **`U`**.
- **R-bc — SURVIVES, with a SHARPENED boundary.** The model still owes the ~11.8 TWh of
  curtailment under rule 14, and a price-forming curtailment must **replace**
  `spp_curtailment_ceiling`. **But it must be chartered against the NEGATIVE tail and the wind
  volume ONLY** — the over-delivered wind is absent from the upper-tail hours and the upper tail
  survives perfect quantities, so **a lane that charters R-bc against C3c will fail for reasons
  unrelated to R-bc's merits.**
- **R-bf (NEW) — the 2024 hourly remnant, the only reachable tail work left.** 2024 alone misses
  the perfect-quantity band by **0.0085**, is the only year whose tail is an hourly net-load event
  (34 of 59 tail hours in the top actual-net-load decile; SPP's own DA reached $563.55), and the
  model's 5 hours there are **all `ISOConfig.voll` infeasibility cliffs**, not a scarcity curve.
  The card is a **rule-14 `[R-ACCURATE]` availability question** — in SPP's 35 DA-tail hours the
  model holds a median **8,233 MW** above its $74.80 marginal unit, and Winter Storm Heather is in
  the window. Answerable at **zero LP** against CAMPD. Not a price adder, and not a topology change.
- **R-be** (day SELECTION) and **R-ba** (merit-order inversion) unchanged.

**`[R-HOLDOUT]` was removed 2026-09-09**, so no year is protected from having been iterated
against: every number here is model-**SELECTION** evidence and **`CALIBRATED` is a rubric
determination, NOT a certified out-of-sample skill claim.** No `complete` marker and no `frontier`
declaration is added, requested or implied.

**Next shorthand: spp-30.**

---

## spp-31 — 2026-09-12

**Object: the DECISION MEMO for SPP `complete` / `frontier`, and the ordered work plan behind it.
ZERO LP SPENT** (rule 32 `[R-SHARD]` (a) — an orchestrator with nothing to orchestrate). **Keeper
UNCHANGED and UNTOUCHED** `2026-09-10-spp-27-commitment-grain`. **No marker file touched, nothing
registered, no verdict minted, no matrix cell moved, no `rm` issued.** Record:
`docs/handoffs/PLAN-spp-31-complete-frontier-2026-09-12.md`. Base `9e499b0e`.
*(Lane SPP-30 — SPP's out-of-training price coverage — runs independently and was neither waited on
nor duplicated.)*

**RECOMMENDATION: DECLARE `complete`; DO NOT DECLARE `frontier`.** Both are OWNER ACTS and this lane
performed neither.

**THE PEER BAR, RE-SCORED THIS SESSION** (`calibration_verdict.py --json`, rubric v3.7, committed
artifacts only, no solve). All seven ISOs read **CALIBRATED** today. SPP: **grade 7 of 8, 0 fails,
1 ledgered C3c caveat, 0 protective, free-class C1 16/16 · 12/12** — and the two declarations that are
still re-scorable at HEAD, both from 2026-09-06, are **identical in shape**:
`2026-09-06-nyiso-202-startup-aware` 7/8 · 0 · 1 C3c · 0 · 14/14 · 10/10, and
`2026-09-06-caiso-260-b1-demand` 7/8 · 0 · 1 C3c · 0 · 12/12 · 8/8. PJM alone grades 8/8 (C3c PASSes).
**ERCOT / PJM / NEISO's declaration-time keepers are NOT re-scorable** — bundles and payloads pruned
under rule 15, and this clone's history begins 2026-09-07 (`git rev-list --count HEAD` = 666); stated
as a limit of the record, not a finding against them. SPP also carries the program's **leanest DOF
ledger** (3 entries / 2 residual against 8–42 / 2–7) and is one of only three ISOs whose **D-1 and D-2
both pass** (SPP, ERCOT, NYISO; D-4 is `False` in all seven).

**REPORTED AGAINST THE RECOMMENDATION, at full magnitude.** (1) **SPP is the ONLY ISO whose keeper
declares `authorized_price_tuning`** — the rule-1 carve-out channel, uniform 0.93 — and the record is
explicit that **C3a and C3b PASS only after it** (spp-20: C3a FAIL 2025 +10.3 % → PASS +1.36/−0.61/
+3.61 %; C3b FAIL 0.204 → PASS 0.1647/0.1762/0.1755). Fully rule-legal (conditions (a)–(e) verified at
promotion, owner's own number, declared ex ante in the PRECOMMIT, never swept, C6 passes) and still a
difference in kind from how all five declared ISOs got there. (2) **Zero out-of-training coverage** —
SPP is alone: `tail/actual_tail.json` and `bench/SPP/` carry `{2023,2024,2025}` only. (3) **Keeper 9 is
one day old and the ninth in five days** (first SPP solve 2026-09-07), and **Q5's uniform rule** (*"a
`complete` marker cannot stand on a NOT-YET keeper"*) has taken NYISO's marker down three times — on a
lane whose stated promotion convention is structure-over-gates, the marker should be expected to fall
at some future structural repair. (4) The **one-zone root cause** stands (`FINDING-spp-64` §5).

**`frontier` IS REFUSED ON A MEASUREMENT.** Mechanism-matrix shard census, `cell:` verdicts, `.`
excluded: **SPP 16 of 173 applicable cells adjudicated (9 %), 155 UNTESTED**, against NYISO 131/182
(72 %), MISO 120/182, CAISO 107/176, ERCOT 103/178, PJM 85/165, NEISO 66/152 (43 %). `frontier` means
the lever queue is exhausted; SPP's is not within a factor of four of the lowest declared ISO.

**THE HANDOFF'S GATE-CODE PREMISE IS FALSE AT HEAD, AND IT CHANGES THE SEQUENCING.** The prompt asserted
four live holdout gates and an ACTIVE freeze. Checked limb by limb: `enforce_holdout_year_gate` **does
not exist** (no `def` anywhere; the name survives only in stale docstrings at `run_calibration.py:15`,
`knob_jacobian.py:10,230`, `derive_actual_tail.py:72`, `fetch_campd_unit_level.py:71`,
`invariant_ledger.py:20`); **`--holdout-authorized` is a flag in neither runner's `--help`** and is
registered nowhere; `dashboard_add_run.enforce_registration_marker_gate` is named at
`dashboard_add_run.py:31` and **does not exist**; `_year_emittable` is `return True` unconditionally
(`derive_actual_tail.py:103-111`, `derive_actual_amplitude.py:74-82`);
**`frontend/data/backcast/holdout-freeze.json` does not exist**; `HOLDOUT_CALIBRATION_YEARS` /
`HOLDOUT_MARKER_FILE` (`run_calibration_full.py:8690-8691`) are referenced nowhere; `audit_keepers`'s
H1 has no failure emitter (`"H1"` only at lines 992/996, both in the pass branch). **The CODE AGREES
WITH CLAUDE.md; the DOCSTRINGS are stale.** Consequence: **a `complete` declaration is NOT a
prerequisite for SPP to spend any year** — SPP-30 is not blocked on it and must not wait for it.
Nothing was edited, resolved or deleted; routed as card **R-bg**.

**WHAT THE MARKER STILL DOES, verified:** (1) `audit_keepers` M1 currency + determination
re-verification (`audit_keepers.py:159-199`), which declaring would put SPP under; (2)
`derive_plant_emissions_v2.py --holdout-intake SPP` — the intake-log ISO vocabulary at line 244 is
`{ERCOT,CAISO,PJM,MISO,NYISO,NEISO}` and **excludes SPP**, so the marker is SPP's **only** route to
2022/2026 emission rows; (3) forecast §2.1b **gate (a)**, which reads `fail` for exactly the two ISOs
with no `complete` entry — **MISO and SPP, both CALIBRATED**. Separately: `GOLDEN_ISOS`
(`ff_readiness_battery.py:102`) does not include SPP, so admitting it there is a separate capx-director
act, not an inference from the marker.

**C3c IS CLOSED AS A WORK ITEM and no card is chartered against it** (spp-29, re-verified here: model
0/5/0 hours >$200 against RT 42/59/68; ρ(congestion rent, RT price) = +0.019; SPP's own nodal DA market
0/14/0 with a 2025 DA max of $176.62; perfect-quantity re-pricing 7/29/0, FAIL in all three years).

**THE ORDERED PLAN** (each card with its ONE seam, rule-19 enumeration, forward story, DOF effect and a
STRUCTURAL screen gate that never reads the target residual). SPP's measured span cost is **499 s of LP
for 2023–2025** (`SHARDREPORT-spp27-span.md:24`), ≈166 s/year, so rule 32(b) gives **one year = one
shard**, ~20–35 min wall each on a cold container. **1. R-bf** — the 2024 hourly availability remnant, a
rule-14 question answerable at **ZERO LP** against committed CAMPD; do it first. **2. R-bc** —
price-forming curtailment as an LP constraint whose dual reaches the zonal price, **chartered against
the NEGATIVE tail and wind volume ONLY** (a C3c charter fails for reasons unrelated to its merits);
screen year named in the PRECOMMIT as the year of largest **measured** curtailment, never largest
residual. **3. R-be remnant** — day selection; expected to CLOSE at phase 0 with no LP, because no
forecast-admissible signal reaches it. **4. R-ba** — the merit inversion, bounded (every thermal class
clears within a ~$5 band) and sequenced behind R-bc.

**NO-BUILD, so a later lane does not re-open it:** a sub-zonal topology change (444 facilities, 115 for
90 % of 2024 rent — not a 3-zone object; and SPP's own fully-nodal DA market produces no tail either),
`energy_reserve_coopt` (`I`), `negative_renewable_offers` (`I`), `spp_gas_commitment_bridge` (`R`),
`spp_curtailment_ceiling` as a CF upper bound (channel refused; the object stays `O`), card R-bd
(closed), any C3c price adder, re-cutting or sweeping `offer_curve_by_group`, and moving C3c to the DA
basis (gate-shopping; owner's call alone and NOT proposed).

**Rule 28 `[R-MECH-MATRIX]`: NO VERDICT MINTED and NO CELL MOVED.** This lane tested no mechanism; the
matrix census is a read of the shards, not an edit. **Rule 21 `[R-DOF]`:** ledger unchanged
(3 / 2). **Rule 31 `[R-RETAIN]`:** nothing created, nothing deleted — **no bundle exists, so there is no
promotion question to put.** **`[R-HOLDOUT]` was removed 2026-09-09:** no year is protected from being
iterated against, so **no SPP number here is a certified out-of-sample skill claim** and `CALIBRATED`
is a rubric determination.

**THE QUESTION PUT TO THE OWNER:** *Declare SPP `complete` on keeper
`2026-09-10-spp-27-commitment-grain` — yes or no?* (`frontier`: this lane recommends no.)

**Next shorthand: spp-32.**

---

## spp-32 — 2026-09-12

**Object: the measured sub-5-day unit-availability family, screened on 2025 in two nested arms.
VERDICT: ARM B (COAL+GAS) IS KILLED on two pre-registered gates; ARM A (COAL) clears four of five and
is STOPPED by the fifth — a gate this lane wrote badly and says so rather than rewriting.** Parent LP
**ZERO** (rule 32 `[R-SHARD]` (a)); shard LP **340 s** across two containers. **Keeper UNCHANGED**
`2026-09-10-spp-27-commitment-grain`. Nothing registered, no marker touched, **no `rm` issued**.
Records: `docs/RESULT-spp-32-shortwindow-screen-2026-09-12.md`,
`docs/handoffs/PRECOMMIT-spp-32-shortwindow-availability-2026-09-12.md`,
`docs/handoffs/SHARDREPORT-spp32-A-2025.md`, `docs/handoffs/SHARDREPORT-spp32-B-2025.md`.

**WHY THIS LANE EXISTED.** SPP's LP ignored **every** sub-5-day unit outage in its own CAMPD record.
The coal extract (620 windows, 24 plants, 39 units, 620/620 `plant_group` COAL) had sat committed and
**unarmed** since it was derived; the gas companion did not exist. Both matrix cells were **`U`**, so
this is a first test, not a re-test (rule 28(a)). The basis is rule 14 `[R-ACCURATE]`, never the
residual — and PRECOMMIT §4 recorded **before either solve** that the family removes a mean 557.6 MW
per hour across 2024's 35 DA-tail hours against a model holding a median 8,233 MW of headroom
(**6.8 %**), so it **cannot** close C3c and no gate reads it. Card R-bf's availability route is
answered NEGATIVE at zero LP.

**THE GAS EXTRACT, derived here from SPP's own CAMPD record** —
`data/raw/campd-unit-outages-shortgas-SPP.csv`, **2,838 windows, 39 plants, 75 units** (CC_REGULAR
2,204 / ST_GAS 608 / CC_CHP 26). The recorded invocation is **byte-identical to PJM's committed
sidecar on every knob** (only `iso` and `years` differ), so **zero parameters were chosen by this
lane** (rules 21 / 24) and nothing crosses from PJM (rules 25 / 28(d)). Rule 23 `[R-FROZEN-DERIVE]` is
not engaged: a new artifact, not a re-derivation, and the coal extract is byte-unchanged.

**SCREEN YEAR 2025, named in the PRECOMMIT before either solve** on the mechanism's own largest
measured footprint — coal 7,050.714 GWh / 246 windows, gas 11,354.227 / 1,063, total 18,404.941 /
1,309, largest on **every** basis — never the largest residual (rule 29(1)). **Control = keeper 9's
COMMITTED bundle differenced, NO control solve** (rule 29(b) form 4): the G-DRIFT audit classified all
six changed solve-path files between `basis_sha` `09d9fc00` and the pinned base as INERT, with the one
code-reading case (the `model/lp/model.py` memory-hygiene hunk) named as such rather than buried.

**THE GATE TABLE.** The C3a/C3b instrument is validated first — replaying the parent's arithmetic on
the **control's** committed sidecar reproduces the scorer to 4 dp (LW mean **28.7893** vs 28.79;
monthly NRMSE **0.1638** vs 0.164).

| gate | arm A (coal, 94 tranches) | arm B (coal+gas, 218 tranches) |
|---|---|---|
| G1 direction | coal −2.5714 TWh · **PASS** | coal −1.4608, gas-scope −2.3567 TWh · **PASS** |
| G2 confinement | 23 COAL plant-groups · **PASS** | 55 = COAL 23 + CC_REGULAR 18 + ST_GAS 13 + CC_CHP 1 · **PASS** |
| G3 magnitude | 2.5714 < 3.857 TWh · **PASS** | 3.8175 < 9.43 TWh · **PASS** |
| G4 identity | **slack 240.5966 MWh · FAIL** | **slack 10,911.0219 MWh · FAIL** |
| G5 no non-target flip | C3a +5.15 %, C3b 0.1878 · **PASS** | C3a **+15.97 %**, C3b **0.2619** · **FAIL (both)** |

Every 2025 C1 row and all of C2 are SKIPPED by the scorer on the preliminary EIA-923 vintage, so on
the screen year G5 reduces to C3a/C3b — recorded so nobody reads it as broader clearance than it is.

**ARM B IS KILLED, AND THE FAILURE MODE WAS PRE-REGISTERED.** PRECOMMIT §7 named it in advance:
*"2,838 gas windows over three years is too many for a merit-order guard to have filtered — SPP's CC
fleet runs at ~49 % CF, and a 1–5 day dead span at that CF can be economics rather than an outage."*
G3 held; **G4 blew out** — 10,911.0219 MWh of unserved energy in 12 hours, all SPP-South, three
clusters (2025-09-15, 2025-10-06, 2025-12-21), every hour at VOLL $2,000 — and **G5 flipped BOTH
load-bearing price criteria**. The entire price move is scarcity, not merit order: all 18 hours above
$200 are exactly $2,000, the slack penalty. **The arm does not price SPP better; it makes SPP
infeasible.** Rule 28(d) demonstrated rather than asserted: PJM's and MISO's `K` on the coal parent do
not carry, and the reason is fleet conduct. **The extract stays committed — what is rejected is arming
it in SPP's LP, not the data.** The arm-B shard verified the gas scope genuinely entered with its own
zero-LP probe (23 plant-groups at `gas_scope=False` vs **55** at `True`, coal unchanged either way),
which the static `(< 5-day baseload-coal windows)` log string alone would not have proved.

**ARM A IS STOPPED ON A GATE THIS LANE WROTE BADLY, AND THE GATE STANDS ANYWAY.** G4 demanded
`slack` = 0.0000; arm A produced 240.5966 MWh in 2 hours in SPP-South at VOLL. But **keeper 9's own
committed span carries a LARGER slack event — 370.1017 MWh, 2 hours, SPP-South, VOLL, in 2024**
(2023 and 2025 are 0.0000). "Slack stays 0.0000" is therefore a standard **the designated keeper does
not meet**, and this lane generalised a one-year accident into a gate after looking only at 2025.
**The gate is not being rewritten**: re-reading a pre-registered gate after seeing its number is the
fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids. The arm is stopped and the defect is
reported to the owner as a fact about this lane's instrument. Reported at full magnitude and **not** a
reason to reject it (rule 1: a structurally-correct mechanism is never judged by the residual): C3a
degrades +0.66 % → +5.15 % and C3b 0.1638 → 0.1878, both still passing.

**Rule 28 `[R-MECH-MATRIX]` (b), SPP's shard only:** `unit_outage_short_windows` **`U` → `O`**
(screened, live, not adjudicated — promotion is the owner's act, the posture SPP-52a's producing lane
set); `unit_outage_short_windows_gas` **`U` → `R`**. No other cell moves.

**Rule 29(c) + rule 31 `[R-RETAIN]`:** `.gitignore` now carries `results/calibration/spp32_*/` — the
seam the arm-B shard correctly flagged and correctly declined to fix itself (it was permitted exactly
one committed file). The duty is discharged by `.gitignore`, **never by `rm`**. Both screen bundles
were written on ephemeral shard containers and are gone; **this RESULT and the two SHARDREPORTs carry
every number this lane will ever cite.**

**A PROCESS FAILURE OF MINE, recorded rather than tidied away.** The first pair of shard prompts said
"commit and push nothing" — correct under rule 29(c), but it stranded the numbers in cloud sessions
this parent cannot read (no `list_events`; they do not appear in `ListAgents`). Caught while both were
still `PENDING`, before any LP: interrupted, archived, relaunched with one change — each shard pushes a
single markdown report and nothing under `results/`. **Wasted LP: none.**

**THE PROMOTION QUESTION, put explicitly (rule 31):** *arm A is a rule-14 measured input on an
untested cell that cleared four of five gates and was stopped by a fifth shown to be mis-set against
the control's own span — should it go to the full 2023–2025 span?* Cost if yes: **3 shards, ~166 s of
LP each**, including a re-solve of 2025 because the screen bundle did not survive. No code changes;
the extract is committed and the flag exists. **This lane does not recommend arming arm B under any
conditions.**

**`[R-HOLDOUT]` was removed 2026-09-09** — no number here is a certified out-of-sample skill claim.
**No `complete` or `frontier` declaration is added, requested or implied.**

**Next shorthand: spp-33.**

---

## spp-36 — 2026-09-12

**PROMOTION — `2026-09-12-spp-36-shortwindow-span` is SPP's TENTH KEEPER**, promoted **by owner
ruling in-session**, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper."* `keepers/SPP.json` was
untouched until the ruling (rule 31 `[R-RETAIN]`). Records:
`docs/RESULT-spp-36-shortwindow-span-2026-09-12.md`,
`docs/handoffs/PRECOMMIT-spp-36-shortwindow-span-2026-09-12.md`,
`docs/handoffs/SHARDREPORT-spp36-span.md`, `docs/handoffs/FINDING-spp-36-runyear-kwarg-2026-09-12.md`.

**THE ARM.** Keeper 9's recipe plus EXACTLY ONE armed gate, `unit_outage_short_windows` — the
< 5-day baseload-coal CAMPD overlay SPP's LP had ignored **entirely**. The extract (620 windows /
24 plants / 39 units, 620 of 620 rows COAL) had been committed and unarmed since it was derived and
the matrix cell was **`U`**; rule 14 `[R-ACCURATE]` is the basis, never the residual. Not re-derived
(rule 23). Gas companion stays `False` (cell `R`, SPP-32). ONE `--years 2023 2024 2025` invocation,
**377 s**. Control = keeper 9's committed bundle differenced, no control solve (form 4; G-DRIFT: all
twelve changed solve-path files INERT, including SPP-30's out-of-training intake, whose 2023-2025
rows were read back from the keeper's own `basis_sha` blob and compared row-for-row as IDENTICAL).
`offer_curve_by_group` byte-identical, SHA-256 `090abd79…62f65` in both legs.

**MEASURED, span vs span.** Tranches 80 / 73 / 94. Coal 72.8124→70.7851, 67.1699→64.7963,
87.2130→84.0355 TWh (−2.0273 / −2.3736 / −3.1775) onto gas (+2.0283 / +2.3764 / +3.1807), energy
conserved to ≤ 0.0032 TWh. LW price 25.3716→25.7428, 25.4676→26.0214, 28.7893→29.5377.
**SLACK AND DUMP UNCHANGED IN EVERY YEAR** — 0.0000 / 370.1017 / 0.0000 MWh in *both* legs; the arm
adds no unserved energy and 2024's event is the keeper's own. Hours > $200 move only in 2024, 5 → 7
against 59 actual.

**THE GATES.** DETERMINATION **CALIBRATED**, grade 7 of 8, 0 FAILS, 1 ledgered C3c caveat, 0
protective, free-class C1 16/16 · 12/12 — the same shape as keeper 9, re-verified by the parent from
committed artifacts with no solve. C1/C2/C3a/C3b/C4/C6/C8 all PASS. **Reported as the cost:** C3a
+2.44 / +3.54 / +5.15 % (keeper 9 +0.96 / +0.07 / +0.66) and C3b 0.1760 / 0.1658 / 0.1878 (keeper 9
0.1728 / 0.1682 / 0.1638) — both degrade on two years, 2024's C3b improves, all six in band.
Diagnostics with ROW COUNTS checked: D-1 PASS (25) · D-2 PASS (15) · **D-4 FAIL (71 rows, 12
failures)** · D-5 PASS (8) · D-9 PASS (5) · D-10 PASS (6).

**RULE 21 `[R-DOF]` — AND A CORRECTION.** The arm adds ONE entry, `unit_outage_short_windows`,
**measured-physical**, not residual; ledger reads **5 / 3**. The like-for-like baseline is the
CONTROL'S OWN CONFIG REBUILT AT HEAD, which gives **4 / 3** — keeper 9's committed **3 / 2** is
**STALE** (the HEAD builder adds `st_gas_mustrun_per_plant` and reclassifies `offer_curve_smoothing`
as residual). **`n_residual` is unchanged by this arm.** The PRECOMMIT's "stays 3/2" was wrong about
the baseline, not about the arm's incremental cost.

**A PARENT ERROR THAT PRODUCED A FALSE FINDING, RECORDED RATHER THAN TIDIED.** The span was first
fanned into three per-year shards. They solved correctly but their slim outputs **cannot compose
into a registrable run** (`build_payload` needs bundle-root `system.parquet`; D-1/D-2/D-4 need
`dispatch/*.parquet`; `--reuse-solved` gates on both — all gitignored). The composite's D-1/D-2/D-4
returned **zero rows and passed VACUOUSLY**, with **D-4 flipping False → True** against the control's
71 rows — caught by checking row counts, not verdicts. Worse, differencing single-year arm solves
against a SPAN-solved control reported the arm **adding 1,295.6995 MWh (2024) and 240.5966 (2025) of
slack**, which was relayed to the owner and is **wrong**: the span-vs-span A/B shows slack unchanged.
Now banned — **rule 32 `[R-SHARD]` (b) amended by owner instruction the same day** (*"Ok ban slim
shards this is dumb I should only have to wait for one solve wtf"*), `rule-history.md` §19.

**OPEN AND ROUTED, NOT CLOSED.** 2023 (first year in both constructions) reproduces to 4 dp; 2024 and
2025 do not. **Process-order sensitivity in SPP's solve is unresolved** — SPP-27 already recorded
`reconstruct_bundle_fleet` as order-dependent across years within a process for SPP. The registered
A/B is unaffected (both legs are 3-year invocations), but a lane should settle it.

**ALSO THIS SESSION — a STOP-THE-LINE repair.** `solve_and_persist` passed
`unit_outage_window_hour_grain` unconditionally to `run_year()`, which never accepted it, so **every
ISO's solve path was dead** at HEAD (both runners). Found by an SPP-36 shard that stopped and
reported rather than patching. Repaired in `scripts/run_calibration.py` (default `None`, byte-inert)
plus a new AST guard `tests/unit/pipeline/test_run_year_kwarg_binding.py`, proven to fail on the
unrepaired tree. `docs/handoffs/FINDING-spp-36-runyear-kwarg-2026-09-12.md`.

**Rule 28(b):** `unit_outage_short_windows` **`O` → `K`** in SPP's shard, with the keeper and gates
stamps re-cut. **Rule 15:** keeper-only retention executed, keeper 9 pruned (1 pruned, 1 kept) —
after fixing a citation-guard trap of my own making (I had named keeper 9 by run id in the new note,
which would have protected it from retention and later dangled; predecessors are cited by LANE).
**R-T:** `program-status.json` gate (a) re-keyed, status `fail` → `fail` unchanged, 1-line SPP-only
diff (the `ensure_ascii` trap avoided), `check_gate_a_provenance.py` OK, 7 rows.

**SPP has NO `complete` entry and this promotion does NOT create one.** `[R-HOLDOUT]` was removed
2026-09-09: **CALIBRATED is a rubric determination, NOT a certified out-of-sample skill claim.**

**Next shorthand: spp-37.**

## spp-37 — 2026-09-12

**THE SPAN/SINGLE-YEAR DIVERGENCE IS AN EIA-860 VINTAGE CACHE LEAK. YEARS 2+ OF EVERY
SPP SPAN SOLVE ON A STALE FLEET SNAPSHOT.** Card A closed at **phase 0 — zero LP, zero
shards.** Base `9ae27cd7fca1e401c3a977eb0f86383242ad2090`.
`docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md`; probe
`scripts/probes/_spp37_vintage_cache_census.py`.

**The mechanism.** SPP keeper 10 carries `eia860_vintage_tracks_solve_year = True`, so
`run_year` re-points the process-global `_ACTIVE_EIA_860_DIR` on every year
(`vintage_2023` → `vintage_2024` → canonical; no `vintage_2025/` is committed). The LP's
own fleet follows correctly — `load_fleet_from_csv` is not cached — but eleven
`lru_cache`d loaders read that global **without it in their key**, so year 1 pins its
vintage for every later year. Numerator and denominator then sit on different vintages,
the exact defect `_iso_plant_capacity`'s own docstring forbids. **Year 1 is always
correct; years 2+ are not** — which is why 2023 reproduced to 4 dp and 2024/2025 did not.

**Two leaks reach keeper 10's own path**: `outages._iso_plant_capacity` (the denominator
of BOTH outage overlays) and `campd_bins.cc_duct_peaking_pct` (the CC peak offer band,
`cc_duct_peaking=True`; 3 SPP CC plants wrong per year). Nine more are the same class,
latent behind gates SPP has off.

**Measured.** Denominator wrong in **63 bins / +413.55 MW (2024)** and **92 bins /
−2,740.44 MW (2025)**. Worse, events whose bin is absent from the stale map are silently
skipped — **26 bins / 3,692.3 MW of 2025 fleet whose outages never reach the LP**, led by
plant 6193, which the 2023 vintage carries as `COAL` and the 2025 fleet as `ST_GAS`: **a
coal-to-gas conversion the span cannot see.** LP availability input for 2025:
**−5,817,173 MWh** removed on the ≥5-day overlay, **+142,296 MWh** on the <5-day.

**Direction verified on committed artifacts, no solve.** Differencing
`spp36_2025` (single-year arm) against `spp36_span` year 2025 (same config, same
`git_sha` 706aa547) reproduces SPP-36's table exactly and every sign follows: span
ST_GAS **+1.2737 TWh**, COAL_PRB −0.5654, CT_PEAKER −0.4815, slack **240.5966 → 0**,
hours>200 **2 → 0**, LW price **30.0737 → 29.5377**. Four observations, one mechanism.

**Which leg is right: the SINGLE-YEAR one.** So **keeper 10, keeper 9 and every prior SPP
span carry wrong outage derates and duct-peaking bands for 2024 and 2025** (2023 is sound
throughout). The SPP-36 **A/B survives** — both legs were 3-year invocations sharing the
identical stale state — but the **level** either leg reports for 2024/2025, which is what
C3a/C3b/C1 score, does not. Basis is rule 14 `[R-ACCURATE]`; no gate or residual was
consulted.

**The charter's proposed shard would have PASSED and misled.** The span path is
deterministic — it reproduces itself byte-for-byte — and is *also* wrong. The defect is
order-dependence, which byte-identity against a same-order bundle cannot detect. The
zero-LP enumeration found it; **no LP was spent and none was needed.**

**REPAIR PROPOSED, NOT LANDED (owner's call).** Key the cache on the active directory —
the `cod_ramp._load_cod_map(eia860_dir)` pattern already used four times here. Zero free
parameters, zero new fields, **no matrix row** (a cache-key defect is not a tuning
channel). Blast radius measured: with `tracks_solve_year` off the directory is constant,
so the repair is a **strict no-op**; of 93 committed bundles **only SPP's two arm it**, so
every other ISO, every SPP single-year run and SPP 2023 are byte-identical. Cost if
accepted: **one shard, one `--years 2023 2024 2025` invocation, ~500 s** (rule 32(b)). Not
landed unilaterally: it would leave keeper 10 non-reproducible at HEAD with no
replacement, and card A "cannot move a keeper and must not try".

**Queue HELD, deliberately.** R-be and R-ba both reason off per-plant ST_GAS and thermal
behaviour in 2024/2025 — the years the leak moves, in the class it moves most. Proceeding
would have built on contaminated evidence.

**Flagged, not acted on.** (a) `results/calibration/spp36_2025` is committed, unregistered
and turns the parity gate RED (Class-E point 4) — and is also the only committed artifact
showing the CORRECT 2025 construction and the evidence above, so rule 31 `[R-RETAIN]`
keeps it; recovery pin `git checkout 18ef91756ac84482a78ea719c2fc8d57ec7d5cf5 --
results/calibration/spp36_2025`. The gate is already red from four other lanes'
bundles, so removing SPP's would not turn it green. (b) SPP-27's `reconstruct_bundle_fleet`
order-dependence is the same defect class one layer over; its "nothing scored is affected"
is right for an A/B difference and wrong to infer the numbers are correct — that inference
is what let this sit.

**Rules.** 32(a) parent ran no LP, launched no shard · 33 nothing to archive · 29(b) no arm,
so no G-DRIFT owed, but `tests/unit/pipeline/test_run_year_kwarg_binding.py` **4 passed** at
HEAD · 1/13 `offer_curve_by_group` not read, re-cut or swept · 31 nothing deleted, no `rm` ·
28 no cell moves · 15 no run produced. `[R-HOLDOUT]` removed 2026-09-09: no SPP number is a
certified out-of-sample skill claim.

**Next shorthand: spp-38.**

## spp-38 — 2026-09-13

**THE REPAIR LANDED AND THE KEEPER WAS RE-SOLVED ON A CORRECT LP INPUT.** Run
`2026-09-13-spp-38-vintage-cache` (bundle `results/calibration/spp38_span`) is **`CALIBRATED`**
(rubric v3.7), grade **7 of 8**, **0 FAILS**, **1 ledgered C3c caveat**, 0 protective, free-class
C1 **16/16 all · 12/12 free** — the SAME SHAPE as keeper 10 on every scored criterion. Repair
commit `760012f7a12b5d6fae01c5a6a4c96c9dc8588ed9`, **merged to `main`**. Parent LP: **zero**;
one shard, **9m35s wall, 6.12 GiB peak**, archived.

**WHAT WAS FIXED.** SPP-37's defect, at **twelve** loaders rather than eleven: each public name is
now an UNCACHED shim over a cached core keyed on the active EIA-860 directory. The twelfth,
`eia860_selfcommit_scope_plants`, is vintage-blind by the same construction — a `maxsize=1` cache
over a union of two loaders that both move — and its census "stable" reading was an artifact of
the probe clearing the union but **not its two legs**, not a property of the data. Zero free
parameters, zero `ScenarioConfig` fields, zero gates, **no matrix row and no cell verdict moves**
(rule 28 does not reach a cache key). Basis rule 14 `[R-ACCURATE]`, never the residual.

**PROVEN, NOT ASSERTED.** Census §2b: all twelve now `rekeys` on a warm cache. Census §5: the
span-vs-single-year delta in the LP's own 2025 availability input goes **−5,817,173 MWh (18 bins)
and +142,296 MWh (5 bins) → +0 MWh / 0 bins on BOTH overlays**. New guard
`tests/unit/data/test_eia860_vintage_cache_keying.py`, 33 hermetic tests, pinning re-keying, the
strict no-op at a constant vintage, and the `eia860_dir` first-parameter shape. Fast lane **9,410
passed** vs the base's 9,377 with the **identical 16 pre-existing failures**, verified by
re-running the lane on a stashed clean tree.

**SPP-27's `reconstruct_bundle_fleet` ORDER-DEPENDENCE IS THE SAME DEFECT AND IS CLOSED BY THIS
REPAIR** — no separate treatment needed. SPP 2025's `fleet_arrays.availability` digest, built
alone vs after 2023→2024, **each leg in its own process**: pre-repair 7,580,565.41768 vs
7,625,968.40751 (order-dependent), post-repair identical. The span held MORE availability, the
same sign FINDING §4b measured from a different instrument. *Method note: the first attempt ran
both legs in ONE process and passed for the WRONG reason — the alone-build populates the
vintage-blind cache the chain then reads. Each leg must be isolated.*

**THE 2023 SELF-CHECK PASSES EXACTLY** — year 1 in both constructions, so the cache cannot reach
it: LW price **25.7428**, slack 0.0000, dump 0.0000, 0 hours > $200, max 61.4221, and **all
fifteen class TWh at +0.0000**.

**2024/2025 LAND ON THE CORRECT SINGLE-YEAR CONSTRUCTION, TO 4 dp** — every 2025 figure reproduces
FINDING-spp-37 §4c's single-year column: LW **29.5377 → 30.0737**, slack **0 → 240.5966 MWh**,
hours>200 **0 → 2**, COAL_PRB **77.4872 → 78.0526**, COAL_LIGNITE 6.5483 → 6.5890, CC_REGULAR
36.1986 → 36.3783, CT_PEAKER 15.5101 → 15.9916, **ST_GAS 12.6132 → 11.3395** TWh. 2024: LW
26.0214 → 26.3509, slack 370.1017 → **1295.6995** MWh, hours>200 7 → 8. Energy conserved to
≤ 0.0026 TWh; dump 0.0000 everywhere.

**THIS OVERTURNS A CONCLUSION IN KEEPER 10'S OWN PROMOTION NOTE.** That note dismissed three
single-year fan-out shards' slack readings — 1295.6995 MWh in 2024, 240.5966 in 2025 — as "a
CONSTRUCTION MISMATCH IN THE PARENT'S OWN DESIGN" and declared the span-vs-span A/B "the valid
one". **The repaired span reproduces those exact numbers.** The single-year legs were right; the
span carried the defect. The SPP-36 A/B itself survives (both legs shared the identical stale
state, so the DIFFERENCE is real) but the LEVEL either leg reported for 2024/2025 was not. The
note stands as the historical record; `docs/handoffs/RESULT-spp-38-vintage-repair-2026-09-13.md`
is the correction.

**GATES REPORTED AT FULL MAGNITUDE, GATED ON NOTHING.** C3a err % **+2.43/+2.24/+3.29 →
+2.43/+3.54/+5.17**; C3b NRMSE **0.176/0.175/0.175 → 0.176/0.169/0.188** (2024 improves, 2025
degrades); all six inside their bands, no C1 status flip, every 2025 C1 row SKIPPED on the
preliminary EIA-923 vintage. **Two of three C3a years get worse and the repair stays** — rule 14's
own instruction — and C3b 2024 improving is not evidence for it either. **No screen gate and no
residual gate existed for this arm, deliberately:** a known-wrong LP input is not a candidate
mechanism competing against a correct one (rule 29 `[R-SCREEN]` governs mechanisms). Diagnostics
carry **identical non-zero row counts** (D1 25, D2 15, D4 71, D5 8, D9 5, D10 6) — checked because
a composite passes vacuously at zero rows. **D-4 still FAILS: card R-be is untouched.** Rule 21:
**zero** free parameters; `build_dof_ledger.py` rebuilt at HEAD from the bundle's own config gives
the same **5 / 3**.

**G-DRIFT, AND ONE CORRECTION TO IT.** Recorded in the PRECOMMIT before the arm; form 4 valid, no
control solve. `_hydro_benchmark_is_923_only("SPP", y)` reads **False** all three years, and keeper
10's committed bundle **re-scored at this base to its exact committed determination**. *Corrected
after the fact:* `plant_taxonomy.py` was NOT fully covered by that argument — the re-score reads a
committed payload, not a rebuilt input store. The `eia923` shared-input hash moved
(`58267fd3f822 → 7da41467dba7`) while all seven others are byte-identical, because
`gov-hydro-seam-1` repaired `classify_plant` so prime mover `PS` returns `OTHER` not `hydro`.
`data/raw` is unchanged between the bases, so it is a code effect. **Measured and separated, not
folded in:** it moves the scored ACTUALS, not the LP — ≤ **+0.023 TWh** on any class, **hydro
unmoved**, **zero status flips**.

**REGISTRATION IS NOT PROMOTION.** `keepers/SPP.json`, `calibration-complete.json`,
`prune_iso_runs.py` and the matrix keeper stamp are **untouched** (rules 31 `[R-RETAIN]` / 35
`[R-PROMOTE]` (e): promote → verify → then delete). `audit_keepers` **E13 therefore reports the new
run as registered-but-unstamped** — the expected state of an undecided promotion. Rule 35(b) year
set enumerated first: SPP's registered union is exactly **{2023, 2024, 2025}**, which the new run
covers, so a promotion would shrink nothing. The bundle is **committed and pushed** (the identical
slim + `hourly/` set keeper 10 carries), so nothing is lost to this container; the full 125 MB
bundle and 23 MB input store are pinned at `0b58650a323d4b2da2529511ba45dfb137cccb12` and
`ea3458ff92280a41fb532bc5f23ea481c3b3e689`. Branch `claude/spp-38-span` is deliberately retained
(rule 33(f)(3)) because it holds the only copy of the per-plant `dispatch/` layer a promotion
registers. **SPP still has NO `complete` and NO `frontier`; this lane creates neither.**

**INHERITED, CORRECTED.** (a) `offer_curve_by_group` is **not** "uniform 0.93" — 18 distinct values
(0.5–15.0); the SHA-256 matched and is the binding check. (b) `results/calibration/spp36_2025` is
**no longer** a parity offender — pruned upstream by `654c561a`; **SPP now has ZERO offenders**, the
three remaining are CAISO's and NYISO's, raised not acted on; the §4c evidence stays recoverable at
`18ef91756ac84482a78ea719c2fc8d57ec7d5cf5` (verified). (c) Keeper 10's note records C3b
0.1760/**0.1658**/**0.1878**; the scorer reads 0.176/0.175/0.175 and an independent reconstruction
off the committed sidecars gives 0.1760/0.1722/0.1753 — C3a reproduces to 4 dp on all three
instruments, so it is the note's 2024/2025 C3b figures that are unreproducible. Nothing turns on it.

**TWO LAUNCH-DISCIPLINE FAILURES IN THIS LANE'S OWN SHARD PROMPT**, neither covered by rule 32(c):
(1) the shard **backgrounded its solve and ended its turn**, stranding the work — recovered by
waking it with a poke-only Routine bound to its session (there is no `send_message` for cloud
sessions and they do not appear in `ListAgents`); **≈30 min lost**. A shard prompt must say *run the
solve in the FOREGROUND; never `nohup`, never `&`, never end your turn while it is in flight.*
(2) `results/calibration/_shared/<ISO>/` — the content-addressed input store `meta.json` references —
is **separately gitignored and registration fails without it**; rule 34(a)'s negation recipe covers
only the out-dir. Also: `git checkout <sha> -- <path>` **stages** files even when gitignored, so a
parent must `git reset HEAD -- <path>` immediately.

**Next shorthand: spp-39.** The queue (R-be → R-ba → R-bc) was NOT entered: card A consumed the
lane, as the handoff ordered. Until a promotion, rule 29(b) form 4 for SPP 2024/2025 should
difference against **this run**, not keeper 10.

### spp-38 — PROMOTION EXECUTED (same session)

**OWNER RULING in-session, 2026-09-13, on the question "Keeper 10's committed 2024/2025 numbers
are computed on an LP input we have proven wrong. Promote?" — answered PROMOTE.**
`2026-09-13-spp-38-vintage-cache` is **SPP KEEPER 11**. The lane recommended and did not act until
the ruling (rule 31 `[R-RETAIN]`).

Rule 35 `[R-PROMOTE]` executed in order: **(b)** year set enumerated BEFORE any delete — union
{2023, 2024, 2025}, covered by the incoming keeper, so **(c)** no year set shrinks; **(a)**
`keepers/SPP.json` re-keyed, keeper 10's note preserved verbatim as `prior_keeper_note_spp36`
(it records a conclusion this run overturns, so it is kept rather than edited), predecessors cited
BY LANE not run id per the standing retention convention; **(e)** `audit_keepers --iso SPP` run
**between** the re-key and the prune, showing the incoming three stores resolving; only then
`prune_iso_runs.py --iso SPP` removed keeper 10's three stores together. **`--force-uncite` was NOT
needed and NOT used** — no governance file blocks it; the only citation is the matrix shard, which
is reported but non-blocking. Keeper 10's bundle recoverable at
`f6e3ed374682059291605b0d425b81c399baaa96`.

`calibration-complete.json` **deliberately untouched**: SPP has no entry, and creating one would
create a `complete` marker — a separate owner act this lane is forbidden to take. **SPP still holds
no `complete` and no `frontier`.**

Matrix: SPP.js keeper + gates re-stamped, and `mechanism-testing-matrix.md` §5.7 prose header
re-stamped — it was **two generations stale** because keeper 10's promotion never discharged that
rule-28 duty; the gap is stated in the new header rather than papered over, so the preserved
predecessor is keeper 9's. **STAMPS ONLY:** cell verdict counts byte-identical before and after
(K 9, R 6, I 3, G 0, O 2, U 155).

**VERIFIED AFTER (rule 35(f)): `audit_keepers --iso SPP` PASSES, 0 failures / 0 warnings** (keeper,
holdout, marker, status all clean). Parity gate carries 3 offenders, all CAISO's and NYISO's; **SPP
has zero.**

**THE SHARD BRANCH `claude/spp-38-span` COULD NOT BE DELETED AND REMAINS.** Rule 33(f) steps 1–3
were done (no unique record on it — every doc inherited from `main`; the registered layer is on
`main`), but `git push origin --delete` returns **HTTP 403**: this session's credential can create
and update refs but not delete them, and the GitHub MCP server exposes no branch-deletion tool —
exactly what rule 33(f)(5) documents, including the misleading `send-pack: unexpected disconnect` →
`Everything up-to-date` that hides the 403 until HTTP/1.1 is forced. **Reported, not claimed as
done.** The §5 recovery pins stay live as a result.

**Rule 29(b) form 4 for SPP now differences against KEEPER 11.** Against keeper 10 it is void for
2024/2025, and keeper 10 is no longer registered. **Next shorthand: spp-39**, queue unchanged
(R-be day selection → R-ba merit inversion → R-bc price-forming curtailment), none entered.

## spp-39 — 2026-09-13

**CARD R-be (DAY SELECTION) DOES NOT CLOSE, contrary to the prompt pack's expectation.** ZERO LP;
no shard. Evidence read off **keeper 11** (`2026-09-13-spp-38-vintage-cache`), as the SPP-38
handoff required, never keeper 10's superseded bundle.
Record: `docs/handoffs/FINDING-spp-39-day-selection-2026-09-13.md`.

**A CORRECTION TO SPP-38'S OWN RECORD.** The SPP-38 RESULT, its log entry and keeper 11's promotion
note all say D-4 is "identical to keeper 10, 71 rows". The **71 is the TOTAL** and is right; the
phrasing implied the FAILING set was unchanged, and it is not — **12 → 10 failing rows**. Recovered
keeper 10's diagnostics from its pin `f6e3ed374682059291605b0d425b81c399baaa96` and differenced:
**RESOLVED `(2024, 6193)` and `(2025, 1230)`; new-failure set EMPTY.** Plant **6193 is Harrington**,
the coal→gas conversion that was the single largest term in the stale vintage map — its D-4 failure
was an artifact of the leak, and the repair removed it. All four 2023 rows moved +0.0000 (the 2023
self-check on a third instrument); the seven survivors moved −0.0007 to +0.0023. **The card's object
is now 10 rows on 4 plants (1230 in 2023 only; 1235/1271/3008 all three years) — smaller than the
pack describes, and plant 6193 is out of it entirely.**

**THE SIZE HYPOTHESIS IS REFUTED — this is a genuine SELECTION defect.** ORACLE bound (rank each
plant's days by its OWN measured online hours — the best any selection rule could ever do):
**10 of 10 rows clear the 0.50 bar, margins 0.00–0.35** (oracle 0.0000–0.3526 against actual
0.5257–0.7487). Seven of ten rows have `D_online − W_days` positive by 23–121 days. So the window is
**not** size-bound and day selection is the right object. The bound is robust to the exact window
definition — the margins are 0.15–0.50 wide.

**THE ADMISSIBLE SET IS NOT EMPTY — the pack's premise is falsified.** Enumerated against rule 13's
forward test: day-mean gross load (incumbent), day-PEAK gross, **day-mean NET load**, day-peak net
are ALL admissible (each is the model's own array, regenerated forward by construction, responding
to changed conditions). Temperature/weather and any SPP commitment/outage instrument are
**unreachable** — no committed weather driver, LTLF blocked (audit item 17), audit items 15/16/19
blocked/partial. `mustrun_online_frac_per_year` and a per-plant grain threshold stay refused
(rule 28(a) DO-NOT-REDO). **PAIRED measurement (same instrument both arms, bias cancels):
`day-mean NET load` beats the incumbent on 7 of 10 rows, mean −0.0335**; day-PEAK gross is WORSE
(0.5873 vs 0.5652).

**THE INSTRUMENT DOES NOT REPRODUCE THE SCORER, AND THAT BOUNDS THE CLAIM.** Two reconstructions
tried, both REJECTED rather than reported as the scorer: (1) `W = round(bind_h/24)` over all days
runs 0.03–0.09 optimistic on every row; (2) mechanism-16 binding cells collapsed per plant off
`floors/<year>_P1.npz` reproduce **0 of 10** rows (`bind_h` systematically larger — 1440 vs 1287,
2448 vs 2047) because the scorer evaluates **per class-slice** (`sel[global_i]`), not per plant.
**What survives: the PAIRED sign. What does NOT: any absolute 0.50-crossing claim** — an earlier
pass's "5 of 10 clear 0.50 under net load" is **WITHDRAWN as unsupported**, an artifact of the
optimistic bias.

**NOT PROMOTABLE YET, and the gap is not more phase-0 arithmetic.** SPP-27 refused NET load once
(measured a WASH at the HOUR grain, 0.8168 vs 0.8168) for bundling a second unmotivated change.
This result is at the **DAY** grain, which SPP-27 never measured — genuinely new evidence under
rule 28(a) — **but a statistic is not a driver**, and adopting net load because it scores better on
the rider it is scored against is the fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids.
The driver argument (a vertically-integrated utility commits gas steam against the load its own
wind cannot serve) is plausible on SPP's ~120 TWh wind against ~300 TWh demand but **needs SPP's own
commitment record, not the D-4 rider**, and no such instrument is committed.

**RULES.** 32(a) zero LP, no shard · **28 NO cell verdict minted** (nothing was tested, only
measured; `st_gas_mustrun_per_plant` and `mustrun_window_commitment_grain` keep their `K`) ·
1/13 `offer_curve_by_group` not read, re-cut or swept · 21 the candidate adds zero free parameters
(necessary, not sufficient) · 31 nothing deleted · C3c untouched.

**CONSEQUENCE FOR `complete` / `frontier`: the queue got LONGER, not shorter.** R-be was the
cheapest card and the one expected to close for free; it stays OPEN. R-ba (merit inversion) and
R-bc (price-forming curtailment) are untouched. **Next shorthand: spp-40**, and its first step is
ZERO LP — make the D-4 rider reproducible per class-slice, then re-run the signal comparison on a
faithful instrument. Only if net load still wins AND a driver lands does this become a PRECOMMIT.

## spp-40 — 2026-09-13 — HELD-OUT YEARS 2019–2022 (SPP's first out-of-training price coverage)

**Run** `2026-09-13-spp-40-holdout-span` · bundle `results/calibration/spp40_holdout` ·
stamped to keeper 11 `2026-09-13-spp-38-vintage-cache` (rule 30 `[R-TOUCHPOINT-FOLD]` (a)).
Full write-up: `docs/handoffs/RESULT-spp-40-holdout-span-2026-09-13.md`.

Keeper 11's recipe, **no `--set` at all**, one `--years 2019 2020 2021 2022` invocation, one
shard, one bundle. **SPP's headline determination is UNCHANGED at `CALIBRATED`** — rule 30 (c),
a held-out year reports and cannot decertify. Per-year: 2019/2020/2021/2022 all NOT-YET
(forced_share; +price_shape from 2020; +fuelmix, price_mean, dispatch_corr from 2021).
C6 governance **PASSES** on all four; C2 sysvol passes on all four; C3c carries as the ledgered
caveat exactly as in-sample.

**THE FINDING — one defect, four symptoms, keyed to DELIVERED GAS PRICE, and visible in the
training window too.** Sorted by gas price rather than year, the model's CC share of (CC+PRB)
is monotone and **saturates**: 2020 $2.03 +3.6 pp · 2024 $2.19 −1.4 · 2023 $2.54 −1.2 ·
2019 $2.57 +2.4 · **2025 $3.52 −4.6** · 2021 $3.72 −16.3 · 2022 $6.45 −18.0. Above ~$3.5 the
model puts essentially the whole CC fleet behind PRB coal (CC_REGULAR 15.8 TWh in BOTH 2021 and
2022 vs 34.6/35.8 actual; COAL_PRB 98.8/101.3 vs 80.2/78.0). Gas rises 74 % between those two
years and the model's split barely moves — the plateau is the signature of a crossover that is
far too sharp. C1, C3a, C3b/C4 and C8 are all that one defect: C8's ST_GAS breach (50.4 %/55.6 %
vs a 30 % cap) is a collapsing denominator (14.7/15.9 → 10.8/9.9 TWh) on top of a genuinely
larger floor (4.8–5.5 TWh vs 2.2–2.5 in 2023–2025, more gas steam pre-retirement), and rule 19's
conditional-pass escalation does not rescue it because D-1 `cv_ratio` reads 0.429/0.391 — the
class runs flat because all that is left of it is the floor. In 2019/2020 D-1 **passes**
(0.765/0.809) and the breach is marginal, i.e. the larger floor alone.

**NOT ESTABLISHED, stated at the gate.** The crossover is **bracketed** ($2.57 passes, $3.72
fails), not located — 2025 at $3.52 would decide it but its fuelmix/sysvol are unscored. No
counterfactual gas price was solved, so the association is measured and the causation is a
hypothesis. The mechanism is unidentified (candidate levers: a coal supply/stockpile/take-or-pay
**maximum** — the model has the minimum only; PRB ramp/sustained-output limits; the
`coal_prb_passthrough_sigmoid` extrapolated far outside the $2.19–$3.52 range its anchors were
identified in). 2021 contains Uri (121 % of its full-year price gap) which drives its TAIL but
**not** its fuelmix miss — 2022 shows the same substitution with no Uri.

**RULES.** 32 `[R-SHARD]` one shard, parent solved nothing · 34 `[R-SHARD-PROMOTABLE]` full
bundle pushed, recoverable at `2fa060dafd0c2d23265949599816974d65f062d3` · 16 `[R-ALLYEARS]` one
bundle · 1/13 `offer_curve_by_group` byte-identical (SHA-256 `090abd79…62f65`), not read, re-cut
or swept · 21 `[R-DOF]` ledger inherited, **zero** additions · 23 frozen derives untouched ·
28 `[R-MECH-MATRIX]` **NO cell verdict minted** — nothing was tested, a frozen recipe was
measured · 31 `[R-RETAIN]` nothing deleted.

**Two shared-infrastructure defects REPORTED, not patched** (rule 25): `stamp_touchpoint_holdout.py`
hardcodes NEISO-specific `[R-HOLDOUT]`-era caveat text onto every ISO's touchpoint (now
zero-consumer prose after the rule 30 (a) amendment deleted its render path; SPP's sidecar carries
corrected text, and **a re-stamp resets it**); `gen_touchpoint_attestation.py` refuses a
multi-tier year span on a stale `tier_for_year` guard, so this lane used the established per-lane
generator (`scripts/gen_spp40_attestation.py`).

**Next shorthand: spp-41**, first step ZERO LP — score 2025 fuelmix/sysvol when the source data
lands, which narrows the bracket for free; then a rule-29 phase-0 offer-array delta for a 2022
gas-price counterfactual before any solve is spent.

## spp-41 — 2026-09-14 — THE COAL↔GAS CROSSOVER IS THE OFFER CONSTRUCTION, AND EVERY CHEAP LEVER IS DEAD (card R-bf)

**ZERO LP. NO SOLVE, NO SCREEN, NO BUNDLE, NO KEEPER CHANGE, NO REGISTRATION.**
Base `75f0e4561d13977477910077714c15a8dbc5132b`. Control = keeper 11's COMMITTED bundle
(rule 29(b) form 4); no control solve was spent and none was needed, because nothing was solved.
Full write-up: `docs/handoffs/RESULT-spp-41-coal-gas-crossover-2026-09-14.md`.

**STEP 0 — the bracket cannot be narrowed.** Re-ran `audit_eia923_completeness.py --year 2025`
against the raw at HEAD; it reproduces the committed part. Both SPP families read INCOMPLETE
(CC_REGULAR 17/22 plants, COAL_PRB 26/29, CT_PEAKER 16/62, ST_GAS 20/36), only COAL_LIGNITE and
CC_CHP gate. C1/C2 on 2025 stay unscored; the bracket stays **$2.57 passes / $3.72 fails**.

**STEP 1 — phase 0 says the offer construction IS the object.** Four `run_year(fleet_only=True)`
rebuilds of keeper 11's own recipe. Share of CC_REGULAR committed+econ MW priced above the
DEAREST PRB row: 6.0 % @ $2.19, **0.0 % @ $2.54**, **97.1 % @ $3.72**, 91.7 % @ $6.45. Sweeping
the 2022 fleet's own decomposition puts the **crossing at $2.33–$2.65/MMBtu with full saturation
by $3.50** (14.2 → 45.5 → 80.3 → 96.4 % at $2.00/$2.50/$3.00/$3.50, then FLAT to $6.50).
**Arrays and dispatch agree**, so the lane proceeded rather than redirecting.

**STEP 2a — the sigmoid is NOT being extrapolated; it is NEVER EVALUATED.** `COAL_SIGMOID_DEFAULTS`
has 10 entries over ERCOT/MISO/PJM and **no `("SPP", *)` key**; keeper 11 leaves all four
`coal_prb_passthrough_*` scalars `None`; so `coal_sigmoid_params` returns `None` for every supply
and `coal_passthrough_series` returns the FLAT 1.0. MEASURED, not read off the source: implied PRB
econ passthrough `(mc − vom)/(fuel × heat_rate)` reads **exactly 1.00000 at p05/p50/p95 over 46
plants in all four years**, gas-INVARIANT across $2.19–$6.45. Keeper 11's armed
`coal_prb_passthrough_sigmoid` + `_tiered` are **provably inert** — rule 24 `[R-REGISTRY]`: the
bundle's `run_config.json`/`meta.json` OVERSTATE what the solve read (xiso-3 shape). Cell
`coal_passthrough_sigmoids` moves **U → I** in `mechanism-matrix/SPP.js` (rule 28(b)).
ROOT CAUSE: SPP is absent from `data/raw/reference/coal_region_crosswalk.csv`, which
`derive_coal_sigmoid.py` iterates, so no SPP row exists downstream either.

**STEP 2b — THE OBVIOUS REPAIR IS DEAD, killed at zero LP.** `derive_coal_sigmoid.py` fixes
`ceil = 1.0` for every supply BY DESIGN (its header retires the ceil>1.0 opportunity-cost story),
and all 10 derived rows carry it. Applied to SPP at either existing PRB shape, the hour-by-hour
merit-order position moves **95.0 → 95.7 % (2021)** and **96.7 → 96.7 % (2022)** — exactly inert
in the two FAILING years, since passthrough → 1.000 at $6.45 is what the model already does —
while **2023 goes 39.5 → 97.3 %**. It would leave the defect untouched and destroy both
CALIBRATED years.

**STEP 2c — the capacity-ceiling hypothesis is dead on measurement.** CAMPD census of the model's
own 29-plant PRB set, every vintage on disk: fleet max hour 18.45–21.07 GW, best year 90.79 TWh
gross (2021). Model 2022 = **101.25 TWh at a 17.91 GW peak** — annual energy ~19 % above the best
measured year on a like-for-like net basis, but a peak **11 % BELOW** the measured 2022 maximum
hour and below max-24 h. **The excess is DURATION, not LEVEL**, and **0 of 29 plants exceed their
own CAMPD-demonstrated maximum** (ratios 0.32–0.96), so `derive_coal_max_cf.py`'s demonstrated-
capability ceiling — the repo's one admissible coal ceiling — would not bind on a single plant.
`coal_takeorpay_committed` / `coal_prb_committed_dispatchable` / `coal_prb_committed_split` /
`coal_min_load_floor` stay **U**: all four are commitment/floor objects and the defect is what
coal OFFERS, so stacking one on an unfixed offer is what rule 19 `[R-ONE-MECH]` forbids.

**STEP 2d — THE DRIVER IS FOUND AND IT IS PUBLISHED BY SPP'S OWN MARKET MONITOR.** The MMU's
annual coal offer-price markup (offer minus mitigated/reference offer, cleared-MW weighted —
ASOM 2024 fn. 135), against the model's zero: **$6.02 (2021) · $21.12 (2022) · $6.88 (2023) ·
$4.29 (2024) · $5.81 (2025)**, all $0.00 in the model. The MMU names the 2022 driver itself
(ASOM 2023 fn. 194): *"Several coal resources experienced coal deliverability issues as a result
of rail limitations, which resulted in many resources offering higher than typical mark-ups."*
The physical scarcity is REAL and DOCUMENTED — and the market expressed it as a PRICE, not an
energy cap, which is why the ceiling census finds nothing. Applied at own-year values it supplies
**~2/3 to 3/4** of the separation the failing years need (1.50× short in 2021, 1.32× in 2022) and
moves 2022 from 96.7 → 65.0 %, 2021 from 95.0 → 69.3 %.

**STEP 2e — AND NO ADMISSIBLE PARAMETERIZATION REACHES IT. This is the result.** (1) A same-year
MMU overlay is backcast-only — no MMU report exists for a forecast year, so it fails rule 13
`[R-MEASURED]`'s forward test. (2) The markup is **NOT gas-keyed** ($2.19→$4.29, $2.54→$6.88,
$3.52→$5.81, $3.72→$6.02, $6.45→$21.12; only 2022 elevated, and the monitor attributes it to
RAIL), so fitting a four-parameter gas logistic to five points to capture one of them would
attribute to gas what the monitor attributes to rail — the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, and the D-8 weak identification `COAL_SIGMOID_DEFAULTS`' own header flags.
(3) **The rule-1 authorized band-multiplier channel is PROVABLY INCAPABLE** of closing it:
condition (b) requires ONE config across every scored year and the real markup swings **5×**
year-on-year, so a year-invariant +$5.81 leaves 2022 at 95.5 % (from 96.7 %) while pushing 2023
from 39.5 → 19.3 % — it misses the failing year and breaks the passing ones. SPP's
`offer_curve_by_group` also already carries the **identical 0.93** on all four bands of BOTH
`COAL_PRB` and `CC_REGULAR`, so moving it scales the two stacks together and cannot reverse their
order. (4) The MMU's own named driver WOULD be forecast-admissible, but nothing on disk reaches
it — there is no EIA-923 Schedule-5 coal receipts/stocks intake, only the purchase-type share.

**NO SCREEN SPENT.** Named structural successor for SPP's queue, entering as `U`: a coal offer
markup keyed to **coal deliverability / stockpile days**, identified from the MMU's published
markup series against a Schedule-5 receipts-and-stocks intake. Cost is a DATA INTAKE, not a solve.

**CROSS-ISO, reported not transferred (rule 25 `[R-ISO-SCOPE]`).** Census over every designated
keeper's committed `run_config.json`: **SPP and CAISO are the only two keepers arming ZERO
offer-markup machinery of any kind** (every other arms at least `gas_offer_net_revenue_margin`);
**five of seven carry an armed-but-inert `coal_prb_passthrough_sigmoid`**, so the xiso-3 shape is
the majority state — harmless where PRB is trivial, load-bearing in coal-dominant SPP (18.5 GW PRB
against 10.1 GW CC); and **`COAL_SIGMOID_DEFAULTS` disagrees with `coal_sigmoid_params.csv`** —
the live registry keeps hand-tuned `ceil > 1.0` curves (ERCOT prb 1.50, PJM subbituminous 2.10)
that the data-grounded derivation was written to retire and re-derives at 1.0, and the derivation
was never adopted. So the only curve SHAPE in this repo that would address SPP's defect exists
ONLY as an un-derived hand-tuned number, which rule 25 refuses to transfer. **For the NYISO lane:**
its gas-monotone tilt is a DIFFERENT instance — NYISO arms `gas_offer_net_revenue_margin`, so its
gas markup mechanism is live where SPP's is absent entirely. No parameter offered, no cell filled.

**HOUSEKEEPING.** Parity gate still RED on exactly the two pre-existing non-SPP bundles,
`caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — rule 35 `[R-PROMOTE]` (a) is per-ISO, so
**not pruned by this lane** (`soco15_spp_arm` carries "spp" in its name but is a SOCO bundle).
SPP's determination is UNCHANGED: `CALIBRATED` on the 2023–2025 train-tier verdict. The two
shared-infra defects SPP-40 reported were not re-discovered and not touched; this lane
re-registers nothing, so no `stamp_touchpoint_holdout.py` re-apply is owed.

**Next shorthand: spp-42.** The cheap lever does not exist; the queue's top item is now an
owner decision on the Schedule-5 coal receipts/stocks intake, not a modelling session.

## spp-42 — 2026-09-16 — CARD R-be's OPEN HALF IS A CLIP DEFECT, NOT A SELECTION DEFECT; the screen CLEARS and the span is launched

**NO PROMOTION. `frontend/data/backcast/keepers/SPP.json` is UNTOUCHED** and SPP's designated
keeper remains 11, `2026-09-13-spp-38-vintage-cache` (rule 31 `[R-RETAIN]` — promotion is the
owner's act). SPP's determination is UNCHANGED: `CALIBRATED` on the 2023–2025 train-tier verdict.
Full write-up: `docs/handoffs/RESULT-spp-42-commitment-feasibility-2026-09-16.md`; charter
`docs/handoffs/PRECOMMIT-spp-42-commitment-feasibility-2026-09-14.md`.

**PHASE 0 ESTABLISHED THE SELECTION EXACTLY, THEN OVERTURNED THE CARD'S OWN READING OF IT.**
The floor's hours are the top `round(online_frac × 8760 / 24)` whole operating days ranked by
**day-mean SYSTEM LOAD — the identical ranking for every plant**; verified, the placed day set
is a subset of the top-N load days for all 21 floored plants, and the plant's own record enters
ONLY through the COUNT and the LEVEL. The confusion matrix splits the four D-4 failures in two:
1230/1235/1271 are a DAY-selection miss (day precision 0.483/0.500/0.500, within-day
0.855/0.907/0.847) and 3008 is a WITHIN-DAY miss (0.812 / 0.601, daytime-cycling) — the one
measured two-shifter SPP-27 named. **But the day-selection reading is largely WRONG**: about
half of each failing plant's floored hours carry a dated ≥5-day CAMPD full stop and the floor
SURVIVES it as a fraction of the plant's own minimum online level — single-unit **Cimarron River
(1230, 50 MW) floored at a MEDIAN 1.33 MW, 6.2 % of its own 21.6 MW level, across 845 hours its
meter reads zero** (1235 4.00/24.0, 1271 1.68/17.0, 3008 16.91/41.9; passing plants 73–92 %).
Because a committed tranche's `cc_mustrun_pmin_mw` IS its own `pmax`, the global clip reduces to
exactly `pmax × availability`: the asserted COMMITMENT inherits the derate LINEARLY, and
`np.minimum` substitutes a smaller, equally infeasible commitment instead of none.

**THE ARM.** New gated field `mustrun_commitment_feasibility_clip` (default off, registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at that default in the same commit): zero the floor where the
plant-group's own available capacity is below the committed level it asserts; every other hour
keeps the incumbent clip. **Rule 21 `[R-DOF]` ZERO free parameters, zero new artifacts, loaders
or CLI inputs.** Rule 18 `[R-PHYSICS]` eligibility is unit physics. Rule 13 `[R-MEASURED]`
nothing measured enters — both operands are arrays the LP already holds — so it is
FORWARD-NATIVE, deliberately NOT in `_BACKCAST_ONLY_OVERLAY_FIELDS`. Rule 19 `[R-ONE-MECH]`:
the ONE floor's clip is replaced, nothing stacked; the committed D-2 confirms
`st_gas_mustrun_per_plant` is the SOLE mechanism flooring SPP ST_GAS.

**TWO SIBLING ROUTES KILLED AT ZERO LP.** (a) `mustrun_layup_window_mask` alone is a rule-19
**double-subtraction** on SPP — `campd_outage_merit_order_guard` is off, no
`campd-unit-outages-perunitmerit-SPP.csv` exists, and **1089 of 1089** lay-up rows are already
present in the `campd-unit-outages-SPP.csv` the keeper reads, with availability inside those
windows already at 0.040/0.182/0.108/0.297 and ZERO lay-up hours left underated. (b) The blunt
"zero under ANY dated outage" variant removes 1.15 TWh fleet-wide and destroys CORRECT floors on
multi-unit plants (2964: 4,326 of its 4,560 zeroed hours are hours the meter says it WAS running).

**THE SCREEN (2023, named ex ante on the mechanism's own largest footprint, 0.1428 TWh against
0.1154 and 0.0465, and NOT the residual year).** G-DRIFT **VOIDED form 4** and the control solve
was EARNED: a LIVE hunk sits on the exact path under test (`arrays.py`'s COD-ramp seam moved to
`cod_ramp.generator_online_mask`, SOCO-15 card S12, whose comment records that `min_gen` is now
"scaled by the same mask" where it was "zeroed in offline months"), so both legs were solved in
ONE shard at the SAME base. **The control is faithful — three reproductions of keeper 11's
committed 2023**: D-4 rows identical, C3a +2.43 % (committed +2.43), C3b 0.1761 (committed
0.1760). **G1 FIRING PASS** (placed `min_gen` 22.2420 → 22.0992 TWh, −0.1428, hitting the
zero-LP prediction to 4 dp) · **G2a/G2b PASS** (one differing key; `offer_curve_by_group`
`090abd79…62f65` in both) · **G3 PASS** (ST_GAS −0.1312 TWh against a 0.4284 bound; CC_REGULAR
+0.0422, CT_PEAKER +0.0391, COAL_PRB +0.0363, COAL_LIGNITE +0.0101; total +0.0002 on 284.64 TWh;
wind +0.0026, no curtailment traded) · **G4 PASS** (slack 0.0000 and dump 0.0000 in BOTH legs,
price max 61.4221 byte-identical) · **G5 PASS** (C3a +2.43 → +2.52 %, C3b 0.1761 → 0.1768, C1
ST_GAS share_pp −0.046, no flip).

**G2c FAILS AS LITERALLY WRITTEN AND IS REPORTED RATHER THAN RE-READ (the SPP-32 discipline).**
The clause said "no class other than ST_GAS changes its D-2 forced energy"; CC_CHP 0.0533 →
0.0531 and CT_CHP 0.0474 → 0.0472 moved by 0.0002 TWh each. It names a DISPATCH measure to test
a MECHANISM property and was drafted loosely. The property is proven by a strictly stronger
check, pre-registered in the PRECOMMIT's prose and re-run on the SOLVED floor arrays: **6,720
moved cells, control-leg mechanism stamp id 16 on 100 % and arm-leg id 0 on 100 %, with the
`chp_steam` (104,016 cells) and `nuclear_mustrun` (17,520 cells) floor arrays BYTE-IDENTICAL.**

**THE TARGET, after the gates and never as one: D-4 FAIL rows 4 → 1.** 1230/1235/1271 all
RESOLVE; **3008 improves and STILL FAILS** (bind_h 2047 → 1836, zero share 0.6087 → 0.5839).
That is the pre-registered risk landing: phase 0 predicted 3008's PLACED median would move
0.0 → 13.8 MW and the rider scores BINDING hours, where it stays 0.0 — the placed-vs-binding
bound SPP-39 was caught by, biting on one plant of four. 3008 is the only multi-unit plant of
the four and the fleet's one two-shifter; its defect is the within-day grain (SPP-27), never
this clip. D-2 ST_GAS forced 2.4998 → 2.4057 TWh, share 0.1935 → 0.1881. **Expectations held
and were stated at the gate:** C1 ST_GAS worsens −6.362 → −6.494 TWh because the arm REMOVES
floor from a class already under-produced; load-weighted price 25.7440 → 25.7672.

**SPAN LAUNCHED on the cleared screen — SEVEN years in TWO registrable bundles** (rules 16 /
32(b) / 34(c); year union enumerated from `frontend/data/backcast/registry/*.json` BEFORE any
prune, rule 35(b)): `--years 2023 2024 2025` and `--years 2019 2020 2021 2022`, each one shard,
one bundle, pushing every `dispatch/<year>_P1.parquet`. Span B carries the number SPP-40 named
as this lane's object: the held-out C8 ST_GAS `forced_share` 0.504/0.556 in 2021/2022 against a
0.30 cap.

**HOUSEKEEPING.** Parity gate still RED on exactly the two pre-existing non-SPP bundles
`caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — rule 35(a) is per-ISO, **not pruned by
this lane**. `[R-HOLDOUT]` was removed 2026-09-09, so `CALIBRATED` is a RUBRIC DETERMINATION,
NOT a certified out-of-sample skill claim.

**Next shorthand: spp-43.**

### spp-42 PROMOTION (same session, 2026-09-16) — SPP KEEPER 12

**OWNER RULING, verbatim: "Promote it when they land."** The lane had not acted;
`keepers/SPP.json` was untouched until the ruling (rule 31 `[R-RETAIN]`).

**Keeper 12 = `2026-09-16-spp-42-commitment-feasibility`** (bundle `results/calibration/spp42_span_a`,
committed slim). **CALIBRATED**, 0 FAILS, 1 ledgered C3c caveat, free-class C1 16/16 / 12/12;
C1/C2/C3a/C3b/C4/C6/C8 all PASS — the same shape as keeper 11. **D-4 conduct FAIL rows 10 → 2**
(1230/1235/1271 resolve in every year they failed, 3008 resolves in 2025; 3008 remains in
2023-24, improved). C8 ST_GAS forced share 0.2001/0.1873/0.1535 → **0.1881/0.1769/0.1423**.
Cost declared at the gate and reported at full magnitude: C1 ST_GAS worsens (−6.362 → −6.494
TWh in 2023) because the arm removes floor from an under-produced class; **2025's price criteria
degrade the most** (C3a +5.18 → +6.05 %, C3b 0.1884 → 0.1964 against a 0.20 band) while its
volume error improves on net.

**SPAN B WAS SOLVED AND THE ARM IS PROVABLY INERT ON 2019–2022.** Dispatch, D-4 rows and D-2
forced energy are all **byte-identical** to `2026-09-13-spp-40-holdout-span`, because **SPP's
CAMPD unit-outage extracts cover 2023–2025 ONLY** (880/905/936 windows there, **zero** rows in
2019–2022) — availability is the flat EFOR baseline (`min availcap == p05 availcap` for all 21
floored ST_GAS plant-groups in 2019) and the clip's predicate can never fire ("21 floored
plant-groups tested, **0 infeasible plant-hours**"). The held-out run was therefore **re-stamped**
to keeper 12 (rules 30(a)/34(c)/35(c)) rather than replaced by a numerically identical twin;
SPP's registered year set stays at **seven**. Bundle kept and recoverable at
`be5123c29d82c74f464ebc0f3bc5061be94975d7`.

**CAUTION — a number that must not be read as this arm's.** Held-out C8 ST_GAS forced share
reads 0.3423/0.3014/0.5041/0.5556 in the SPP-40 control and 0.2497/0.2844/0.4559/0.4995 on this
base. That is **NOT this arm**: `forced_twh` is byte-identical and only the benchmark-side
**denominator** moved between bases. **SPP-40's held-out C8 breach stays OPEN**, root-caused to
the same missing 2019–2022 outage extract and routed as SPP's next **DATA-INTAKE** item.

**PROMOTION MECHANICS (rule 35 `[R-PROMOTE]`, in order).** Year union enumerated FIRST
(2019–2025, seven years) → both spans attested (`scripts/gen_spp42_attestation.py`; DOF ledger
machine-checked at **5 entries / 3 residual on both, byte-identical to keeper 11** — the gate
adds zero free parameters) → registered → holdout re-stamped with SPP's corrected caveat text
re-applied → `keepers/SPP.json` promoted → `calibration-complete.json` re-keyed (audit M1a) →
**`audit_keepers.py --iso SPP` PASS, 0 failures 0 warnings (E1/E13) BETWEEN promotion and prune**
→ `prune_iso_runs.py --iso SPP --force-uncite` removed keeper 11's three stores (the rule-35(d)
intended route; both surviving citations are historical prose and **stay**) → matrix cell **O → K**,
shard stamp and §5.7 prose header re-stamped (rule 28).

**ONE INCIDENT, RECORDED.** The first span-B registration collapsed to the same run id as span A
and **overwrote span A's sidecar** before dying on missing shared inputs, making the keeper
briefly re-score `NOT-YET` with `governance FAIL`. Caught by re-scoring rather than trusting the
earlier `CALIBRATED`, and repaired by re-registering span A.

**OPEN, carried at promotion and not absorbed:** (1) D-4 still FAILS on 2 rows, both plant 3008
in 2023-24 — card R-be's residue is now the **within-day grain alone** (SPP-27's object; a
per-plant grain predicate stays refused on rule 21, and `mustrun_plant_exclusions` on miso-170's
warning); (2) C3c remains the accepted model-class limitation; (3) 2025's price degradation.
Parity gate still RED on the two pre-existing non-SPP bundles — rule 35(a) is per-ISO, not
pruned here.

**Next shorthand: spp-43.** Top queue item is the **2019–2022 CAMPD unit-outage intake**, which
both unblocks this gate on the held-out years and root-causes SPP-40's C8 breach.

## spp-43 — 2026-09-16 — THE 2019–2022 UNIT-OUTAGE INTAKE: the data gap both open defects root-caused to is CLOSED, and so is the held-out C8 breach

**NO PROMOTION. `frontend/data/backcast/keepers/SPP.json` is UNTOUCHED** and SPP's designated
keeper remains 12, `2026-09-16-spp-42-commitment-feasibility` (rule 31 `[R-RETAIN]` — promotion
is the owner's act, and this lane asks the question rather than pre-empting it). SPP's
determination is UNCHANGED: `CALIBRATED` on the 2023–2025 train-tier verdict, and
`audit_keepers --iso SPP` passes clean. Full write-up:
`docs/handoffs/RESULT-spp-43-unit-outage-intake-2026-09-16.md`; charter
`docs/handoffs/PRECOMMIT-spp-43-unit-outage-intake-2026-09-16.md`.

**THE SOURCE SURVEY CAME FIRST AND IS WHAT LICENSED THE INTAKE** (rule 29 `[R-SCREEN]` step 0,
`scripts/probes/_spp43_source_survey.py`). 13 of SPP's 14 CAMPD detection states carry a complete
Jan 1 → Dec 31 unit-level parquet in **every** year 2019–2025; the 14th (**CO**) is absent in
every year **including 2023–2025**, so the committed block was itself derived on the same
13-state panel and **the gap is purely TEMPORAL, never spatial**. Fleet CEMS coverage in
2019–2022 equals or exceeds the in-sample years (112/109/107/107 model plants against
107/105/106; ST_GAS 19/18/17/17 against 17/17/17; COAL 26/25/24/24 against 24/23/23), and all
four plants carrying SPP-42's residual D-4 failures (1230 / 1235 / 1271 / 3008) file in all seven.

**RULE 23 `[R-FROZEN-DERIVE]` IN ITS OWN TERMS.** Extending an extract's YEAR RANGE on unchanged
source data is a FIRST derivation for those years, not a re-derivation against a residual. The
invocation differs from the committed one in `--years` and nothing else; no detector threshold,
constant or setting was touched, and the derived years were never compared against a residual
before being kept. Standard +943/932/982/946 windows, short +181/239/379/270 — the same order of
magnitude and class composition as 2023–2025. **ADDITIVITY PROVEN FOUR WAYS**: 3,803 / 1,069
additions and **0 removals**; the committed block's bytes unchanged **including line positions**;
no new row with `outage_end ≥ 2023-01-01`; and the decisive one — **the LP's own 2023–2025
availability multiplier arrays are BYTE-IDENTICAL before and after, all six**. The keeper's
scored years therefore cannot move and were deliberately NOT re-solved, a ~10-minute shard
killed at zero LP. Reach (`scripts/probes/_spp43_overlay_reach.py`): the 2019–2022 overlays go
from **0 bins to 77–81**, 363k–403k derated cells against 337k–370k in-sample — the flat-EFOR
condition is gone.

**THE RESULT** — `2026-09-16-spp-43-outage-intake`, bundle `results/calibration/spp43_holdout_span`,
keeper 12's recipe replayed UNREVISED (no `--set`, zero differing behavioural keys,
`offer_curve_by_group` byte-identical SHA-256 `090abd79…62f65`), stamped to keeper 12.
**SPP-40's held-out C8 breach is CLOSED: `forced_share` FAIL on all four years → PASS.**
**NUMERATOR AND DENOMINATOR SEPARATED**, because the ratio alone is the trap this lane was
warned about: the whole improvement is NUMERATOR (ST_GAS `forced_twh`
5.0294/4.7849/5.4248/5.4898 → **1.7035/1.7040/1.9543/2.3652** TWh) and the DENOMINATOR moved
**AGAINST** it in three of four years (`class_total_twh` 14.6909/15.8746/10.7616/9.8806 →
14.7341/**14.0692**/**7.9206**/**7.5281**). Shares 0.3423/0.3014/0.5041/0.5556 →
0.1156/0.1211/0.2467/0.3142; 2022 stays above the 0.30 cap and clears rule 20's
**grounded-above-budget** route (all binding mechanisms clear D-4; profile r 0.952, off-peak CV
ratio 1.438) — a clean PASS surfaced as a report note. **D-4 per-unit conduct FAIL rows 33 → 4**,
the survivors being plant 3008 in 2019–2021 and a marginal 1230 in 2019 (46 binding hours, down
from 1391) — 3008 being the fleet's one measured two-shifter whose defect SPP-27 identified as
the WITHIN-DAY grain, never this mechanism. That is the same residual the in-sample keeper
carries, so the held-out picture now matches the in-sample one.

**ATTRIBUTION IS JOINT AND SAYS SO.** The arm differs from the `2026-09-13-spp-40-holdout-span`
control by the intake AND keeper 12's `mustrun_commitment_feasibility_clip`, and the two are
**NOT separable by construction** — SPP-42 measured the clip PROVABLY INERT on these years
without the extract, so the data is the enabling condition and the clip the mechanism. A
decomposition leg settles the split — three legs one delta apart, `offer_curve_by_group`
byte-identical in all three. **A** = ctrl (old extract, no clip), **B** = NEW extract with the
clip OFF, **C** = the arm. ST_GAS `forced_twh` A/B/C: 5.0294/**1.8898**/1.7035,
4.7849/**1.8185**/1.7040, 5.4248/**2.0268**/1.9543, 5.4898/**2.4743**/2.3652; shares
.3423/.3014/.5041/.5556 → .1268/.1278/.2535/.3236 → .1156/.1211/.2467/.3142; D-4 FAIL rows
**33 → 14 → 4**. **THE INTAKE DOES 94.4 / 96.3 / 97.9 / 96.5 % OF THE FORCED-ENERGY REDUCTION**
and 19 of the 29 D-4 rows; the clip supplies the last ~4 % of energy and the other 10 rows.
**BUT NEITHER ALONE CLOSES C8, WHICH IS WHY THE LEG WAS WORTH SOLVING**: both B and C breach the
raw 0.30 cap in 2022 only (32.4 % and 31.4 %), and what differs is rule 20's grounded-above-budget
escalation, which needs every binding mechanism to clear D-4 — **B still fails D-4 in 2022 on
plants 1230/1235/3008 so it is NOT grounded and C8 FAILs; C has ZERO 2022 D-4 failures so it IS
grounded and C8 PASSes.** The intake and the clip are **complements, not substitutes**: the data
supplies almost all the energy, the clip supplies the 2022 D-4 clearance that flips the gate. The
leg is deliberately kept OFF `main` (rule 29(c)) on `claude/spp43-extract-only` at
`2addbeee3cfc7dc91d64739d606de35345909290`; every number cited from it is recorded here and in the
RESULT, and nothing scored depends on it.

**THE COSTS, DECLARED NOT DISCOVERED.** 2022 gains **563.6284 MWh of slack** against the
control's 0.0000 and its max system price goes **85.58 → 1102.55 $/MWh**; **2020 degrades across
the board** (C3a +24.0 % now FAILs, C3b 0.231 → 0.319, a new C1 COAL_PRB −10.85 TWh row,
reported-only CO2 −4.8 % → +17.5 %). Load-weighted price rises every year (19.8177 → 22.3866,
18.0677 → 20.4872, 29.4211 → 40.1673, 33.7319 → 43.6848); hours > $200 0→0 / 0→0 / 14→220 / 0→4;
energy conserved to ≤ 0.0159 TWh on 262–288 TWh; dump 0.0000 everywhere. **Determination stays
NOT-YET** on four unchanged FAIL criteria, with **grade 2 → 3** and **fails 5 → 4**: C1 FAIL rows
4 → 2, C3a 2 → 1, C3b 2021 0.640 → 0.213, C4 3 → 1, C3c 2021 CAVEAT → PASS, D-10 free-class C1
28/32 → 30/32 (free 20/24 → 22/24). **RULE 14 `[R-ACCURATE]` IS THE BASIS AND THE RESIDUAL IS
NOT** — that C8 and D-4 improved is a RESULT, and that 2020 and 2022 got worse is a discovered
root cause to route, never grounds to revert an accurate input. **RULE 29 `[R-SCREEN]`: no screen
gate and no residual gate**, on the precedent keepers 11 and 12 both record — the screen applies
to a candidate MECHANISM competing against a correct one, and a MISSING measured input is not a
candidate mechanism. Form 4 holds: G-DRIFT from the keeper-12 promotion commit `520d9fc0` to this
base finds **ZERO changed hunks** on the solve path, and the older gap from the control's own
`git_sha` `3117f06a` was already closed by SPP-42's actual re-solve.

**REPORTED, NOT FOLDED IN.** (1) **The frozen 2023–2025 block is NOT reproducible at HEAD**:
re-deriving it as a control emits **103 rows it does not carry — all plant 762 (Ponca) units 3–4,
ST_GAS, ZERO removals** — because Ponca reaches the deriver only through
`load_retired_within_window` and the frozen block predates that scope. Left untouched since
changing it would move the keeper's SCORED years; the 2019–2022 block IS at HEAD scope and DOES
carry Ponca, because rule 14 forbids degrading an accurate input to match a stale one. The short
extract reproduces byte-identically (coal-only scope). Routed as its own lane. (2) The four
companion extracts (`layup`, `layup-shortgas`, `shortgas`, `e923`) stay 2023–2025 and were
deliberately NOT extended — the keeper consumes none of them, and SPP-42's lay-up
double-subtraction finding is unaffected since there are still no 2019–2022 lay-up rows.
(3) `stamp_touchpoint_holdout.py`'s NEISO-specific `[R-HOLDOUT]`-era caveat defaults were
re-applied by the stamp and corrected in place on the new sidecar — they assert an
envelope-parity story that is the **exact opposite** of this run's object, and claim a touch-once
locked test is unspent when 2019 is one of this bundle's years. Zero consumers; REPORTED, not
patched (rule 25); **a re-stamp resets them**. (4) `replay_keeper --out-dir` still propagates
neither `calibration_attestation.json` (closed by `scripts/gen_spp43_attestation.py`) nor
`metrics.json` (the parent's scoring step writes it). (5) Parity gate: two pre-existing REDs,
neither pruned — `caiso279_ablate_dswcouple_span` (CAISO) and `soco15_spp_arm`, whose `meta.json`
reads **`iso = SPP`**, not SOCO: it is the SOCO-15 lane's *SPP arm* and so IS in this ISO's
rule-35(a) scope, but it is cited as live evidence by ten-plus docs across five lanes and rule 31
reserves that call for the owner.

**RETRIEVABILITY** (rule 34 `[R-SHARD-PROMOTABLE]` (e)): the bundle is **ON `main`**. PR #6223
(`claude/spp43-holdout-span`) was rebased onto main to clear a `.gitignore` conflict and merged at
`aea6158f0b12535890a8e8fed35b3b3207410875` — 45 committed files including all four
`dispatch/<year>_P1.parquet`, their `_fleet` companions and the 8 `_shared/SPP` inputs. **A
promotion costs zero re-solves and needs no recovery command.** The shard's `.gitignore` negation
was scoped to SPP before merge: a blanket `!results/calibration/_shared/` would have un-ignored
EVERY other ISO's shared inputs and let a later `git add` in any lane sweep them onto main
(rule 32(c)(6)), so the parent re-ignored `results/calibration/_shared/*` and re-opened only
`_shared/SPP/`.

**THE PROMOTION QUESTION, ASKED NOT PRE-EMPTED**: this run supersedes
`2026-09-13-spp-40-holdout-span` as SPP's 2019–2022 rung. Both are currently registered and both
are stamped to keeper 12; nothing was pruned. Promote and prune the predecessor (rule 35
`[R-PROMOTE]` (a), SPP only)? SPP's registered year set stays at SEVEN either way, and the keeper
itself is unaffected — its availability arrays are byte-identical, proven above.

**LINEAGE**: SPP-40 → SPP-42 → **SPP-43**.

## spp-44 — 2026-09-16

**ZERO LP. No screen, no shard, no bundle, no registration. Keeper 12
(`2026-09-16-spp-42-commitment-feasibility`) and the 2019–2022 rung
(`2026-09-16-spp-43-outage-intake`) are both UNCHANGED, and no `ScenarioConfig`
field, default or keeper file was touched.** Base
`d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c`. Record:
`docs/handoffs/RESULT-spp-44-coal-deliverability-2026-09-16.md`; probe
`scripts/probes/_spp44_coal_deliverability_phase0.py`.

*(Lane-name collision: the 2026-09-07 SPP-44 was the `spp_gas_commitment_bridge`
lane. Unrelated and untouched; cite both by date.)*

**THE OBJECT** was SPP's NAMED STRUCTURAL SUCCESSOR — "a coal offer markup keyed
to coal deliverability / stockpile days", entered as `U` by SPP-41 and recorded
there as blocked on an EIA-923 Schedule-5 coal receipts-and-stocks intake that
**did not exist on disk**.

**THE BLOCKER IS STALE AND IS NOW CORRECTED IN THE QUEUE.** Both datatypes
landed 2026-09-14 (`data/raw/coal-receipts`, `data/raw/coal-stocks`, EIA-923
Pages 5 and 2, 2018–2024, national) with schemas, curation scripts and the
rule-13-disciplined readers `prior_years_delivery_rate` / `opening_stock_tons`.
Coverage of SPP's own model coal fleet is complete: **30 of 32 plants in
receipts, 29–30 in stocks, every year**. The data question is closed.

**THE IDENTIFICATION FAILS ANYWAY, AND THE LEVER IS `R`.** Six legs, all zero-LP.
Across lagged (≤ Y-1) and same-year, fleet and per-plant, annual tonnage and
sub-annual timing, **no statistic puts 2022 outside the other years' range**,
while the MMU target has 2022 at **3.07× the max of every other year**
($21.12 against [4.29, 6.88]). The decisive pair: **2021 and 2022 are 0.02 %
apart on the best admissible statistic (prior-2yr receipts/burn 0.9990 vs
0.9988) and 3.51× apart in the target**, and **2023 is *tighter* than 2022
(0.9933) on a $6.88 markup** — so a monotone map would need a residual-fitted
steepness, which rule 1 `[R-STRUCT]` (c) refuses. `L:rec/burn` does rank-correlate
at ρ −0.900 (n=5) in the expected direction and that is reported honestly, but
the agreement is carried entirely by the two *loose* years; the statistic has no
3× feature to produce a 3× spike.

**2022 WAS THE SMOOTHEST DELIVERY YEAR IN THE 2018–2024 RECORD** — fewest
zero-delivery months (0.20 vs 0.37–1.62), lowest receipt CV (0.326 vs
0.354–0.589), one plant with a ≥2-month gap (vs 4–9), ρ **−0.800** on all three,
i.e. the wrong sign. Per-plant, 2022 had **2 of 28** plants under 90 % coverage
and **zero** under 75 %, against **2024's 10 and 3** (p10 0.651) — and 2024
carries the record's **lowest** markup. The reporting-frequency confound that
would have manufactured the timing leg is ruled out by measurement: the filer mix
is constant at 28 M / 2 A in every year. **The hypothesis is inverted by the data,
not merely unsupported by it.**

**A SECOND CELL FALLS OUT OF THE SAME MEASUREMENT: `coal_fuel_inventory` MOVES
`U` → `R` FOR SPP** (cell updated in `SPP.js` this session, rule 28(b)).
Re-opening SPP-41's "do NOT propose a coal ceiling" line was legitimate rather
than a re-test: the cell was `U`, the **field did not exist** when SPP-41 was
written (row added 2026-09-16 by miso-259), the intake it reads was believed
absent, and every number SPP-41 cited is about **LEVEL** (peak MW, max-24 h,
per-plant demonstrated maximum) while its own conclusion is that the excess is
**DURATION** — which is what an **energy** budget constrains. The flat `/12` row
**would** bind: 0 / 0 / **5** / **5** / 2 / 0 / 3 months in 2019–2025, worst month
−2.3 / −6.0 / **+45.6** / **+50.1** / +15.9 / −11.3 / +15.8 % over cap, annual
headroom +51.4 / +81.5 / **+10.9** / **+6.9** / +54.2 / +95.3 / +24.6 %. **But the
physically correct cumulative constraint binds in ZERO months in all seven years**,
bottoming at 16.9 days of burn (2022) and 31.6 (2021); the full path is
88.2 / 137.8 / 31.6 / 16.9 / 99.6 / 186.5 / 89.7 min-days. SPP's measured
stockpile supports exactly the seasonal drawdown-and-rebuild the `/12` row
forbids, so the binding is a **form artifact**, not a fuel shortage.

**THAT IT BINDS IN 2021/2022 — precisely SPP-41's two failing crossover years — IS
REPORTED AND IS EXPLICITLY NOT THE BASIS.** Rule 1 forbids selecting a mechanism
because the residual moves, and forbids reaching the right number through a
mechanism that is not real; arming this would do both. Reopening the verdict
needs a change to the row's **form** (a carryover/cumulative inventory
constraint), which is shared machinery and a different charter — not a re-run of
this cell. Rule 25 `[R-ISO-SCOPE]`: the verdict is SPP's own footprint and fills
no other ISO's cell; MISO's chartering measurement is untouched.

**MEASUREMENT CAVEAT, STATED.** The legs E/F tons are a **screen**: converted from
the model's class-hourly coal MWh at year Y-1's measured tons/TWh (2019 uses its
own year — there is no 2018 bench), where the builder would use per-unit heat
rates and the receipts' own `mmbtu_per_ton`. The conclusion is not close
(`cum_bind` 0 with 16.9–186.5 days of margin), so no plausible refinement of the
conversion reaches it.

**RULES.** 13 `[R-MEASURED]` — every candidate built from ≤ Y-1 only; the
same-year legs are computed and labelled as the forbidden comparator, never as
candidates. 21 `[R-DOF]` / 24 `[R-REGISTRY]` — zero free parameters proposed,
zero fields added, nothing armed. 29 `[R-SCREEN]` — zero-LP phase 0 only; **no
screen year was owed** because both objects died before an arm existed. 32(a) —
the parent never solved and no shard was launched. 15 `[R-DASHBOARD]` — no
completed run, so nothing to register. 31 `[R-RETAIN]` — nothing deleted;
nothing stranded on ephemeral disk.

**PARITY GATE: the same two pre-existing REDs, no new ones** —
`caiso279_ablate_dswcouple_span` (CAISO) and `soco15_spp_arm` (whose `meta.json`
reads `iso = SPP`, so it *is* in SPP's rule-35(a) scope, but it is cited as live
evidence by ten-plus docs across five lanes and rule 31 reserves that call for
the owner). This lane created no bundle and added none.

**WHAT REMAINS OPEN.** SPP's C1 / C3a / C3b / C4 held-out failures, with **no
identified forward-admissible instrument** after this lane — the object is now an
owner data-procurement decision, the same shape as ERCOT's daily-Waha block.
Untouched by this lane: card R-be's within-day grain on plant 3008, SPP-43's two
declared costs (2022's 563.6 MWh of new slack, 2020's across-the-board
degradation) and the Ponca reproducibility defect in the frozen 2023–2025
extract block.

## spp-45 — 2026-09-17 — THE PONCA EXTRACT DEFECT IS COSMETIC: zero LP reach, measured; and the "inert rows" premise it was routed on is FALSE

**Base** `d54cd9c5`. **Keeper 12 `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`)
— UNCHANGED.** 2019–2022 rung `2026-09-16-spp-43-outage-intake` — UNCHANGED. **ZERO LP; no
bundle, no run registered, no cell armed, no shard launched.** Record:
`docs/handoffs/RESULT-spp-45-ponca-reach-2026-09-17.md`; probe
`scripts/probes/_spp45_ponca_reach_phase0.py`.

**THE GATE CLOSES, BUT NOT WHERE IT WAS EXPECTED TO.** SPP-43 §7 item 1 routed the frozen
2023–2025 block of `data/raw/campd-unit-outages-SPP.csv` — which re-derives at HEAD with
**+103 rows, 0 removals, all plant 762 (Ponca) units 3/4 ST_GAS**, split 2023: 32 / 2024: 34
/ **2025: 37** — as its own lane, on the belief that repairing it "moves the keeper's SCORED
years". It does not, and the reason is **not** the predicted one. Plant 762 **IS** in the LP
fleet in **2025** (4 ST_GAS tranches, **34.000 MW**), and the added rows genuinely **reach the
overlay** there — a new `(762, 'ST_GAS')` key with derate < 1.0 in **7,176 of 8,760 hours**.
They still move **0.000 MWh**, because 762's availability is **identically zero across all
8,760 hours** (min = max = 0, live hours 0/8760): a retired plant entering via
`load_retired_within_window` and then masked fully offline by the COD/retirement ramp. A
derate applied to zero is zero. **This is a stronger null than the predicted one** — the pipe
demonstrably works and the answer is still zero. **All 15 `FleetArrays` LP inputs hash
BYTE-IDENTICAL in 2023, 2024 AND 2025** (`availability`, `min_gen`, `min_gen_mechanism`,
`pmax`, `pmin`, `heat_rate`, `vom`, `emission_rate`, `nox_rate`, `so2_rate`, `zone_idx`,
`fuel_type_idx`, `efficiency_bin`, `plant_code`, `unit_ids`); fleet available energy identical
to the sixth decimal (2023 335,652,747.693079 / 2024 327,408,849.067823 / 2025
339,256,583.891876 MWh). **Cosmetic reproducibility wart: no re-solve, no re-gate, no
promotion owed.**

**CORRECTION TO THE RECORD — the 105 committed Ponca rows are NOT inert.** The lane brief
asserted "plant 762 is ABSENT from the LP fleet in all four years 2019–2022", and inferred the
omitted rows were probably inert too. **False for 2019**, where 762 is present (34.000 MW) and
those rows remove **201,656.459 MWh** of available energy (242,143.920 → 40,487.461, **−83.28 %**;
live hours 8760 → **1368**) — a delta **exactly equal at plant and fleet level**, so confined to
762 and nothing else. Inert in 2020–2022 only. **This changes no committed number** —
`spp43_holdout_span` solved WITH those rows, which is correct behaviour — but the analogy the
2023–2025 conclusion was resting on is void, and that conclusion now rests on direct
measurement. The claim is in the **lane brief only**; `RESULT-spp-44-…-2026-09-16.md` makes no
fleet-membership claim and **no other lane's record is altered**.

**TWO MEASUREMENT TRAPS, BOTH HIT AND BOTH GENERAL — read these before the next zero-LP probe.**
(1) **The unit-id convention.** Most SPP units are `<CLASS>_<zone>_p<plant>_<tranche>`
(`ST_GAS_SPP-South_p762_peak`), a minority `<plant>_<unit>` (`210_1`). A `startswith("762_")`
test sees only the second and reports "absent" — it loses **~57 %** of the fleet's plant codes
(2019: 137 found vs **315** real). That is the entire origin of the false premise above.
(2) **`outages.unit_outage_derate_factors` is `@lru_cache`d on its ARGUMENTS, never on the
extract's CONTENTS.** An arm/control that swaps the extract by monkeypatching
`unit_outage_csv_for_iso` **in one process** gets a cache hit and silently re-reads the
**control's** factors, returning a delta of **exactly 0.000** — indistinguishable from a real
null, and exactly what a lane hoping to close a stop gate wants to see. This lane produced that
spurious zero and caught it only on a contradiction (the overlay reported a 7,392-hour derate
the "measured" delta said changed nothing). **Every leg now forks its own interpreter.**

**REPAIR INSTALLED (the one judgement call, flagged for the owner).** The extract is now a
**single 7-year derive** at the sidecar's frozen settings in canonical sort — a **verified pure
superset**: all 6,524 prior rows reproduce **every field byte-identical**, 0 removals, +103
Ponca rows (6,524 → 6,627). It fixes a genuine provenance defect (the recorded
`derive_invocation` did **not** reproduce the two-block concatenation) and an internal
inconsistency (the two blocks sat at different deriver scopes). **Rule 23 `[R-FROZEN-DERIVE]` is
satisfied, not bent** — a deriver-SCOPE repair with a measured zero effect; no residual moved
and none was consulted. Reverting is a one-file revert with no re-solve either way.

**RULES.** 15 — no completed run, nothing to register, dashboard unchanged and correct.
21/24 — zero free parameters, zero new tunables, `offer_curve_by_group` untouched.
25 — SPP's own extract only; the two shared-infra defects reported, not patched.
28 — **no cell moves and none is owed**: no mechanism was tested (a stale measured input is
not a candidate mechanism, per the SPP-38/42/43 precedent), and no SPP cell asserts anything
this lane contradicts. 29 — zero-LP phase 0 only, no screen owed; **G-DRIFT moot** (no control
differencing, no LP), and the branch changes **nothing** on the solve path. 31 — nothing
deleted, nothing stranded. 32/33/34 — no shard launched; the parent solved nothing.

**PARITY GATE: the same two pre-existing REDs, no new ones** — `caiso279_ablate_dswcouple_span`
(CAISO) and `soco15_spp_arm`. Neither pruned; `soco15_spp_arm` is in SPP's rule-35(a) scope but
is cited as live evidence by ten-plus docs across five lanes and rule 31 reserves that call for
the owner.

**STILL OPEN, cheapest first:** SPP-43's two declared costs on the 2019–2022 rung — 2022's
563.6284 MWh of new slack (max system price 85.58 → 1102.55 $/MWh) and 2020's across-the-board
degradation with its new C1 `COAL_PRB` −10.85 TWh row — **both differenceable at ZERO LP against
the committed `spp43_holdout_span` `hourly/` sidecars, and now SPP's cheapest open objects**;
card R-be's within-day grain on plant 3008, which needs a genuinely new idea rather than a new
solve; and the coal↔gas crossover, **fully data-blocked** pending a new dataset (rail-performance
or delivery-reliability) — an owner data-procurement decision, not a modelling lane.

## spp-47 — 2026-09-18

**SPP's four rubric failures on the 2019–2022 rung, adjudicated at ZERO LP.** Base
`8f0d41df`. Keeper `2026-09-16-spp-42-commitment-feasibility` and rung
`2026-09-16-spp-43-outage-intake` **both UNCHANGED**. No LP, no bundle, no shard, no
registration, no cell armed. Record: `docs/handoffs/RESULT-spp-47-four-failures-2026-09-18.md`.

**THE BRIEF'S CENTRAL HYPOTHESIS IS REFUTED.** "2020's COAL_PRB shortfall is the single thread
tying three of the four criteria together" is false. C3a/C3b-2020 is not a coal-volume defect:
the model is too expensive in **10 of 12 months** (mean overshoot +$5.05),
`corr(monthly price error, model monthly coal) = −0.292` (other years −0.491 / −0.237 / +0.063),
and the model's cheapest month is **$16.46 against the market's $9.65**. It captures **44 %** of
2020's real monthly price variation (sd 1.97 vs 4.52) and its **floor gap (+$6.81) exceeds its
mean error (+$3.83)**. The object is a **price FLOOR** — no price-setter below coal SRMC — and
it is the same object in all three failing years (2021 84 %, 2022 68 % of real dispersion).
This is the **floor half of SPP-64's ceiling finding**, and SPP-64 already supplies the
mechanism: `spp_curtailment_ceiling` holds wind at its CF **bound**, a bounded unit is never
marginal, the model's minimum price is exactly −26.000 in every year/zone, and nothing sits
between that and coal SRMC. **Wind long +8.2 to +10.9 TWh every year and the floor being too
high are the same defect from two sides**; successor **R-bc** addresses both. Corroboration
only — no cell moved, no new queue entry.

**STALE-BENCHMARK TRIAGE DISCHARGED (7/7 parts STALE, all `unresolvable: unknown builder
state`).** The flag is provenance; the numbers were measured. `--rebuild-benchmark` is zero-LP
and the shared inputs are content-addressed, so reproduction is exact rather than approximate.
**THE KEEPER (2023–2025) REPRODUCES BYTE-EXACTLY — 8 of 8 shared inputs to the same content
hash, `eia923-7da41467dba7` included. SPP's CALIBRATED headline was never at risk.** The rung
moves in **exactly three class-years**: 2020 `COAL_PRB` **−1.2092 TWh**, 2021/2022 `ST_GAS`
+0.2591 / +0.2527. Resolved to two plants, pointing **opposite ways** — plant **6193** is a
genuine repair (new COAL_PRB+ST_GAS = **5,140,010 MWh** against CAMPD's **5,140,010**, an exact
meter reconciliation; the committed value under-counted ST_GAS by 259,133 MWh), plant **127** is
a **regression**.

**ROOT CAUSE, and it is a confined zero-DOF INPUT defect (rule 14 `[R-ACCURATE]`).** Plant 127
is **Oklaunion**, `ba_code SWPP`, 720 MW sub-bituminous. It is in the LP fleet in **2019**
(`COAL_SPP-North_p127_*`, 650.0 MW) and **absent 2020–2022** — yet it ran **May–Sep 2020,
1,209.2 GWh metered** (92.5/222.6/288.9/334.9/270.2 GWh). EIA's own vintages pin it:
`vintage_2019` operable **OP** with *planned* retirement **9/2020**; `vintage_2020`
retired-and-canceled **RE**, retirement **9/2020**. Under `eia860_vintage_tracks_solve_year`,
`load_retired_within_window` returns empty for a native vintage on the stated assumption that
"the operable fleet already has them" — **true for a plant retiring after the vintage year,
FALSE for one retiring during it**, because that vintage's year-end operable snapshot has
already moved it to the retired sheet. The plant and its nine operating months vanish. The COD
ramp that would zero it correctly after September already exists; the **injection gate** is what
is wrong. **Footprint confinement, measured over every SPP mid-vintage-year retiree
2019–2022: 2019 0.0 GWh, 2020 1,209.2 GWh (Oklaunion alone), 2021 0.0 GWh, 2022 47.8 GWh
(Ponca, already SPP-45-inert).** Every other such retiree is either carried (GREC 165, 540 MW,
2,615.4 GWh — the machinery working) or has zero metered energy. **11.1 % of the failing
−10.85 TWh row, and it does not close C1** (best case −9.64, still FAIL).

**DO NOT REBUILD SPP'S BENCHMARK YET.** The rebuild is one-sided: it fixes 6193 **and deletes
Oklaunion's 1.209 TWh of real metered coal from the 2020 ACTUAL**, shrinking a failing criterion
by 11 % by removing data rather than dispatching it — "rescaling an input so the model's output
lands on the actuals" (rule 13 `[R-MEASURED]`) and "burying the error back inside an inaccurate
input" (rule 14). Governed order is **fleet repair first, benchmark second**; after the fleet
carries Oklaunion the benchmark question is moot, since the builder keys on the fleet map.

**C1 IS TWO OBJECTS, NEITHER 2020-SPECIFIC.** *Object A* — COAL_PRB and CC_REGULAR are an
antisymmetric pair (`r = −0.971`) whose split error is **monotonic in the gas price**
(`r = +0.885`, OLS **+4.081 TWh per $/MMBtu**, zero-crossing **$3.93/MMBtu**): SPP coal SRMC is
near-fixed (~$16/MWh, coal $1.46–1.82/MMBtu) while gas SRMC swings ~$14 → ~$45, and the model
follows the swing all the way. **A LEVEL miss, not duration** — hours-on ~8,760 in model and
actual every year; 2020's gap is 98 %+ mean-output-when-on (−1,863.6 MW) against −43 hours.
*Object B* — **ST_GAS short 4.6–4.9 TWh in EVERY year**, gas-price-independent: SPP-63's routed
successor **R-ba** (gas steam offered above CT_PEAKER despite a better heat rate, 10.543 vs
10.974), corroborated here on a second year set. **C4-2022 is their arithmetic consequence and
is 80.8 % BIAS** (bias/scale/shape 80.8/1.1/18.1; 2021 64.5/0.6/34.8; 2019–2020 shape-dominated
at 87.6 %/75.9 %) — 21.3 TWh of missing gas, a 32 % level shortfall with near-perfect timing,
and a clean regime change at 2021 where the gas price crosses Object A's $3.93 zero-crossing.

**TWO HYPOTHESES KILLED SO THEY ARE NOT RE-SPENT.** (i) Fuel-price data is **not** Object A's
cause. Gas is already rich — `gas_plant_monthly_fuel_pricing` **and**
`f923_gas_price_plausibility_screen` are both armed in `scenario_config` (**not** in
`calibration_flags`, which is why the flat annual `gas_prices` scalar misreads as the whole
story); SPP-46's routed **R-1 is built and armed**. And SPP's **coal** frame is clean: of
**1,100** SPP coal plant-months 2019–2022, **0** at ≤ $0.00, **0** at ≤ $0.30, **0** at ≥ $6.00,
24/26 plants covered, quantity-weighted 1.535/1.457/1.503/**1.822** $/MMBtu rising correctly
into 2022 — **the gas seam's garbage problem has no coal analogue in SPP**, so the missing coal
plausibility screen costs this ISO nothing. (ii) **2022's slack is immaterial**: 563.6284 MWh in
**4 zone-hours**, all SPP-South, two consecutive-hour pairs (h3350–3351, h6326–6327) at
19.4–22.5 GW demand — **0.0002 %** of load, against exactly 0.0000 MWh in 2019/2020/2021. Real
scarcity hours, touching only the auto-caveated C3c.

**METHOD NOTES (two of this lane's own probes were wrong and were discarded).** A hand-rolled
reconstruction of `_benchmark_eia923_frame` disagreed with the committed part on classes the
clean test says are stable (2019 CC_CHP +0.87 TWh) because it reproduced neither the bundle's
`btm_backfill_year`/`mustrun_chp_btm_holdout` settings nor `classFull`'s EIA-930-sourced
classes; and a census scoring "unmapped" plants off the shared `campd` frame returned **581 TWh**
for a ~250 TWh ISO because that frame is **state**-scoped, not ISO-scoped. Only
`--rebuild-benchmark` on the bundle itself carries the bundle's own settings. **SPP-45 trap (a)
mattered**: matching both unit-id conventions is what showed Oklaunion present in 2019 — a
`^127_` prefix test reports it absent there and destroys the central contrast. Trap (b) was
never reached (no in-process path swap).

**RULES.** 1 — nothing selected on a residual; Object A is reported as a **measurement with no
lever proposed**, and §9 records why the rule-1 carve-out cannot reach it (the required
correction **changes sign** between 2020 and 2022, against condition (b)'s one-config-every-year).
13/14 — the §2.2 ordering ruling. 15 — no completed run, dashboard unchanged and correct.
21/24 — zero free parameters, `offer_curve_by_group` untouched. 25 — the retiree-injection seam
is **cross-ISO** (`data/fleet/eia860.py`), so it is deliberately **not** built by this lane; it
needs its own charter. 28 — **no cell moves and none is owed**: no mechanism tested. 29 — zero-LP
phase 0 only; a measured-input repair takes no screen (SPP-38/42/43/45 precedent). 30(c) — a
held-out rung reports and cannot decertify; SPP stays **CALIBRATED**. 31 — nothing deleted,
nothing stranded, promotion question asked in RESULT §8. 32/33/34 — no shard launched.

**PARITY GATE: the same two pre-existing REDs, no new ones** — `caiso279_ablate_dswcouple_span`
and `soco15_spp_arm`. Neither pruned (rule 31 reserves `soco15_spp_arm` for the owner).

**STILL OPEN, ranked:** **S-1** mid-vintage-year retiree injection (new, owed; rule 14, zero
DOF, cross-ISO charter needed); **S-2** R-bc, curtailment as an LP constraint whose dual reaches
the zonal price — the **only** object addressing C3b's floor half; **S-3** R-ba, the
ST_GAS/CT_PEAKER merit-order inversion; **S-4** the coal↔CC elasticity (Object A) — largest
single C1 residual, **no structural successor found**, and explicitly **not** closeable by the
authorized offer-curve channel. Card R-be's within-day grain on plant 3008 is unchanged and
still needs a new idea rather than a new solve. The coal↔gas **supply** lane (deliverability
markup, stockpile inventory) remains data-blocked per SPP-44 and is untouched here — Object A is
a different object, about relative merit-order elasticity, not coal supply.
