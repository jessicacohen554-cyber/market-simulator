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
