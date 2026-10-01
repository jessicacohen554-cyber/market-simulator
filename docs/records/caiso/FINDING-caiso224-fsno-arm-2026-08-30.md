# FINDING — caiso-224: THE FSNO SUB-ZONAL ARM ROUND, ADJUDICATED — the partition WORKS as structure (north–south separation restored from 52/40/14 h to 1,556/1,359/1,186 h against reality's 1,310/1,691/1,347) AND the static DMM-cap arm is FALSIFIED exactly as pre-registered: F1 fires all three years on NP15↔FSNO (binding share 0.3054/0.3547/0.3380 vs the 0.27 DMM ceiling — the lower-bound element caps over-trap) and F2 fires (arm split vector strictly year-ordered vs reality's non-monotone — single-vintage statics insufficient at sub-zonal grain). Verdict **R for keeper purposes**; the partition REPRESENTATION remains; W-2/W-3 are the upgrade feeds; the transmission-outage derate channel is the recorded WATCH. Both bundles registered; keeper untouched (2026-08-30)

**Charter.** This is the completion of the caiso-224 round whose solve session
ran out of context after both solves committed but before registration,
adjudication and records landed — executed by the caiso-224 FINISHER session
(drafted by the capacity-expansion director at the owner's explicit request,
capx r#17 sitting Q14). ZERO SOLVES were run: every number below is read from
the artifacts the solve session committed
(`results/calibration/caiso224_a0_control/`, `caiso224_b1_fsno/`,
`_caiso224_ctrl_tolerance.json`, `_caiso224_split_witness.json`), scored with
`calibration_verdict.py` at HEAD. The governing document is
`PRECOMMIT-caiso224-fsno-arm-2026-08-30.md` — §5's pre-registered gates and
falsifiers are applied verbatim; nothing in this finding is a post-hoc
criterion.

## THE ONE-SCREEN OWNER SUMMARY

1. **G-CTRL is BIT-ZERO.** The A0 control (caiso-220 keeper recipe replayed at
   HEAD with the gated FSNO partition in tree and OFF) reproduces the keeper's
   committed hourly sidecars with max |Δ| = 0.0 on every zone-hour (prices
   included) and every class-hour of all three years
   (`_caiso224_ctrl_tolerance.json`, quoted before any arm value was read).
   Head drift since the caiso-220 solve AND the flag-off FSNO plumbing are
   measured inert; the arm was read licitly. At the scorer level the control's
   verdict rows are identical to the keeper's (C3a +4.0/+12.5/+15.5%).

2. **The split RESTORATION is real — the round's structural thesis is
   confirmed.** North–south separation hours (>$15): control 52/40/14 → arm
   **1,556/1,359/1,186** vs reality's 1,310/1,691/1,347. The negative-price
   mass migrates INTO the carved pocket exactly as the trapped-solar mechanism
   intends (NP15 negative hours 315/570/504 → 98/121/175; FSNO carries
   162/374/428). At hub grain the model had essentially NO north–south price
   structure; with the pocket carved it has reality-magnitude structure.

3. **AND both pre-registered falsifiers fire — both facts are the record.**
   - **F1 (over-trapping), fires all three years.** NP15↔FSNO binding share
     0.3054 / 0.3547 / 0.3380 vs the 0.27 ceiling (the DMM record's own
     highest observed element share — Moss Landing–Las Aguilas at 24–27% of
     all hours; Gates–Midway 9% in 2024). The FSNO↔ZP26 boundary does NOT
     fire (0.2515/0.2059/0.1621). The rule-14 lower-bound reconciliation
     (each cap counts only its DMM-rated elements, omitting unrated parallel
     feeds) over-traps on the NP15 cut, precisely the §2(b) documented risk.
   - **F2 (static vintage), fires.** The arm's split vector [1556, 1359,
     1186] is strictly year-ordered while reality's [1310, 1691, 1347] is
     non-monotone (2024 is reality's PEAK year). 2023-annual scalars carried
     into 2024/2025 cannot produce a non-monotone separation profile — the
     caiso-218 §C insufficiency signature at sub-zonal grain.

4. **Verdict: R for keeper purposes** — mechanical under §5's pre-registered
   rule (F1 firing ⇒ R; no full-guard K evaluation arises, so no owner
   decision card). The partition REPRESENTATION (P-A′ zones, membership,
   measured load split) remains standing evidence; the STATIC DMM-CAP LIMITS
   are what is falsified. W-2 (constraint-report limit/flow field) and W-3
   (DMM element limits beyond the 2023-annual scalars) remain the sanctioned
   upgrade feeds (caiso-222 §(i)); F2 additionally records the
   **backcast-admissible transmission-outage derate channel** (rule-13
   admissible: outage windows are physical availability events; today
   unpublished for these elements) as the WATCH — **not armed**.

5. **Guards: no collateral damage; the §5 pre-bound is measured at full
   magnitude.** C1 clean in both runs, zero row flips; C2/C4/C8 PASS both;
   C3a moved −$0.20 / **+$0.22** / −$0.16 lw (2024 the WRONG WAY) vs the
   direct-channel pre-bound −0.23/−0.32/−0.25 and nowhere near the −0.85
   (2024) / −1.90 (2025) band-pass requirement — the full-2025-close
   non-expectation was stated ex ante and is confirmed; the C3b tripwire
   fires in 2024 (+0.015) and is named to the falsified caps (§E.3).

6. **Both bundles are REGISTERED** (rule 15): `2026-08-30-caiso-224-a0-control`
   and `2026-08-30-caiso-224-b1-fsno`, with the honest slim-render disclosure
   in each sidecar (§F — per-plant panels intentionally empty; class/system/
   price surfaces exact, cross-proven against the committed split witness to
   <$0.002). The caiso-220 keeper, its shard, the markers and the freeze are
   untouched; the keeper's verdict re-scored byte-identical after every
   operation of this session.

## §A — G-CTRL, the licence to read the arm

`_caiso224_ctrl_tolerance.json` (computed by the solve session before any
treated delta was read): max |Δ| = 0.0 in every scored column of
`system_<year>` (price, slack, demand — every zone-hour) and
`class_hourly_<year>` (every class-hour), all three years; ΔC3a = 0.0 pp and
ΔC3b = 0.000 identically against the ratified tolerance |ΔC3a| ≤ 0.1 pp /
|ΔC3b| ≤ 0.005. This is simultaneously (i) the caiso-200-discipline control
tolerance met with a noise floor of exactly zero, (ii) the measured proof that
head drift since the caiso-220 solve is inert on the CAISO default path, and
(iii) the rule-28c inertness proof for the `caiso_fsno_subzonal_topology`
plumbing when the flag is off. The finisher session independently confirms the
scorer-level equivalence: the registered control's C1/C2/C3a/C3b/C4/C8 rows
match the keeper's registered rows exactly (§E).

## §B — The primary structural witness: separation restored, and where it lives

From `_caiso224_split_witness.json` (all six run-years, committed by the solve
session):

| measure | 2023 | 2024 | 2025 |
|---|---|---|---|
| reality north–south split h (>$15) | 1,310 | 1,691 | 1,347 |
| control split h | 52 | 40 | 14 |
| **arm split h** | **1,556** | **1,359** | **1,186** |
| arm FSNO↔NP15 separated h (>$15) | 126 | 366 | 512 |
| arm FSNO↔ZP26 separated h (>$15) | 1,109 | 853 | 558 |
| arm NP15↔FSNO boundary engaged h | 2,506 | 2,770 | 2,627 |
| arm FSNO↔ZP26 boundary engaged h | 6,898 | 6,828 | 6,017 |
| FSNO negative h (arm) | 162 | 374 | 428 |
| FSNO ≤ −$5 h (arm) | 157 | 369 | 376 |
| NP15 negative h (control → arm) | 315 → 98 | 570 → 121 | 504 → 175 |
| FSNO mean price (arm, $/MWh) | 56.65 | 38.73 | 38.46 |

The mechanism operates as designed: the San-Joaquin-Valley pocket traps the
solar-floor hours that hub grain smeared across NP15, and the north–south
separation count lands at reality's order of magnitude in every year — the
2023 arm count even brackets reality from above (1,556 vs 1,310). The
separation's internal composition shifts monotonically (NP15↔FSNO grows
126→512 while FSNO↔ZP26 shrinks 1,109→558) — a fingerprint of static caps
interacting with an evolving fleet/load mix rather than of measured
year-varying limits (§D).

*Unadjudicated leg, stated honestly:* §5's expectation that pocket-floor
engagement concentrates in the caiso-221 §E.1 Local-curtailment-active
windows (655/508 h, 2024/25) is NOT measurable from the committed witness —
the witness carries the engagement magnitudes (above) but no window-overlap
decomposition, and `_caiso221_surplus_design.json` commits window AGGREGATES,
not hour sets. The falsifier set (F1/F2) — not this diagnostic — was
pre-registered to decide the round, and it did. Any future arm round should
add the overlap count to its witness spec.

## §C — F1, over-trapping: FIRES (all three years, NP15↔FSNO)

Pre-registered ceiling: the DMM record's own highest observed element binding
share — Moss Landing–Las Aguilas 24–27% of ALL hours (the 0.27 ceiling);
Gates–Midway 9% of hours in 2024. Measured (witness `arm_boundaries`,
binding share of all 8,760 h):

| boundary | 2023 | 2024 | 2025 | fires |
|---|---|---|---|---|
| NP15↔FSNO (1,940 MW: Tesla–Los Banos #1 1,600 + Moss Landing–Las Aguilas 340) | **0.3054** | **0.3547** | **0.3380** | **YES, 3/3 years** |
| FSNO↔ZP26 (2,500 MW: Gates–Midway #1) | 0.2515 | 0.2059 | 0.1621 | no |

The NP15 cut binds 31–35% of all hours — beyond anything the DMM record
attributes to its own elements. This is the §2(b) misalignment realizing as
model behaviour: the 1,940 MW cap is a **lower-bound** reconciliation (it
counts only the two DMM-rated elements and omits the unrated parallel feeds
of the real boundary), so the model's single equivalent link is tighter than
the real corridor and manufactures excess separation/congestion. Consistent
corroboration in the guard set: 2024's lw price moved UP +$0.22 (§E.2) — the
north-side congestion-rent surplus of an over-tight cut outweighing the
pocket floor's own downward pull — and C3b-2024 worsened (§E.3). The
FSNO↔ZP26 side (a single rated element, Gates–Midway #1, with the smaller
omitted-parallel set) stays inside its ceiling all three years: the
over-trapping is specifically where the parallel-path omission is largest,
which is exactly what rule 14's parallel-path clause predicts.

## §D — F2, static vintage: FIRES

The arm's split-hour vector [1,556, 1,359, 1,186] is strictly decreasing;
reality's [1,310, 1,691, 1,347] peaks in 2024. Pre-registered reading
(precommit §2(a), §5): 2023-annual scalars carried into 2024/2025 are
insufficient at this grain — the caiso-218 §C signature. The model's
separation declines because the static caps meet a monotonically evolving
system (storage build-out, load growth, fleet turnover) while reality's
separation is driven by year-specific states the statics cannot carry —
element outages/derates being the named, rule-13-admissible missing channel
(a derate window is a physical availability event with a forward analogue,
same input class as the unit outage windows the keeper already carries).
Disposition, verbatim from §5: the **transmission-outage derate channel is
the WATCH, not armed** — today unpublished for these elements; it enters (if
ever) as a data intake first under the caiso-218 §F fences, never a solve.

## §E — The guards, at full magnitude (scorer at HEAD on the registered artifacts)

Both runs score `NOT-YET` with reason `governance gate UNATTESTED` — correct
and expected for a probe pair carrying no `calibration_attestation.json`
(pjm-158 precedent; C6 attestations are keeper artifacts, and §6 owes none
here). Guard-by-guard:

1. **C1 fuel-mix (the zonal-recut no-flip guard): PASS both, zero flips.**
   Every gated class row PASSes in both runs, all years. The recut moves gas
   volume toward actuals: CC_REGULAR 2023 −3.09 → −1.02 TWh, 2024 −0.13 →
   +1.05 TWh (control → arm) — trapped-pocket commitment lifting CC energy —
   with every move inside band. 2025 keeps the preliminary-vintage skips
   (identical skip set to the keeper).
2. **C3a mean LMP, full magnitude against the §5 pre-bound.** Load-weighted
   model $/MWh (witness, exact; actual RT lw 54.17/34.65/34.42):

   | year | control | arm | Δ realized | §5 direct-channel pre-bound | band-pass need |
   |---|---|---|---|---|---|
   | 2023 | 56.3126 (+4.0%) | 56.1084 (+3.6%) | **−0.2042** | ≈ −0.23 | (in band already) |
   | 2024 | 38.9625 (+12.5%) | 39.1841 (+13.1%) | **+0.2216** | ≈ −0.32 | −0.85 |
   | 2025 | 39.7551 (+15.5%) | 39.5967 (+15.0%) | **−0.1584** | ≈ −0.25 | −1.90 |

   2023 and 2025 realize ~90% and ~63% of the direct-channel prediction; 2024
   moves the WRONG WAY — the changed-system-dispatch channel (the program's
   C3a case, caiso-223 §D(b)) nets POSITIVE +$0.54 against the −$0.32 direct
   pull in reality's peak-separation year, the same over-trapping that fires
   F1's 2024 maximum (0.3547). The ex-ante statement that a full 2025 close
   was NOT expected (convertible mass +0.94 vs required −1.90) is confirmed;
   no promotion claim was available from C3a in any reading.
3. **C3b tripwire: FIRES in 2024, named to the falsified mechanism.** Monthly
   load-weighted price NRMSE (the rubric's C3b shape metric): 2023
   0.100 → 0.097 (−0.003), **2024 0.177 → 0.192 (+0.015 > 0.005)**, 2025
   0.180 → 0.173 (−0.007). The 2024 worsening is attributed to
   `caiso_fsno_subzonal_topology`'s static DMM-cap chain — the over-tight
   NP15↔FSNO cut (F1's 2024 peak) redistributing prices in months where
   reality's separation did not sit — the same object F1/F2 falsify; both
   improvements land in the years where the direct channel dominates. All six
   year-rows remain PASS against the C3b band; the tripwire is a movement
   guard, not a level gate.
4. **C2 system volume: PASS both** (gas family in band 2023/2024; 2025
   preliminary-vintage diagnostics identical to keeper; coal immaterial).
5. **C4 fleet dispatch correlation: PASS both.** Gas family (CEMS basis)
   r/NRMSE — control 0.881/0.283, 0.907/0.263, 0.872/0.291; arm 0.879/0.267,
   0.910/0.250, 0.877/0.278. The arm slightly IMPROVES the gas NRMSE in all
   three years (commitment redistributed toward the measured fleet shape).
   Coal immaterial (scored SKIP, <5 TWh).
6. **C8 forced-energy share: PASS both, and the arm REDUCES forcing.**
   CC_REGULAR forced share (D-2, committed `legitimacy_diagnostics.json`
   written by the solve session): control 6.5% / 7.3% / 9.2% → arm 5.3% /
   5.6% / 6.6% of class energy — the carved pocket lets the RA must-offer
   floor bind less because the topology itself now produces the commitment
   pattern the floor was buying. Structurally the right direction (rule 20's
   intent: floors as scaffolding, not the dispatch model). Hydro/CT_PEAKER
   0.0% forced throughout.
7. **C3c, reported for completeness (not a §5/§6 guard):** FAIL 2023/2024,
   PASS 2025 (small-count), both runs — model 0 h > $200 on the energy-only
   basis, the SAME basis and the same 0-hour counts as the keeper's rows
   (the caiso-144/145 owner record refused the scored-lane overlay; these
   bundles, like the keeper, carry no `scarcity.parquet`). On the keeper the
   identical rows read CAVEAT via its attested exceptions ledger; a probe
   pair carries no attestation, so the C3c standing rule's guard (b)
   correctly leaves the FAIL standing. No new information vs the keeper.

## §F — Registration mechanics: the slim render, disclosed in full

The solve container was reclaimed before registration, and dispatch/system
parquets are gitignored by design — so the standard payload render had no
solve outputs to read. The finisher reconstructed the render inputs FROM THE
COMMITTED BYTES, with zero solves:

* `system.parquet` / `storage.parquet`: exact concatenation of the committed
  per-year `hourly/` sidecars (the sidecars are the solve's own per-year
  copies of these frames — container-death insurance doing its job).
* `dispatch/<year>_P1.parquet`: the committed `class_hourly_<year>` sidecar
  at CLASS grain with `plant_code = 0` — **no per-plant model hourly survives
  the container, so none is rendered**: the per-plant panels of both run
  pages are intentionally EMPTY rather than fabricated. Every class-level,
  system-level and price surface in the payload is an exact aggregation of
  committed solve output.
* Benchmark parquets: rebuilt via the documented no-solve path
  (`run_calibration_full.py --rebuild-benchmark`), landing **hash-identical**
  to the solve session's frozen `meta.json` shared-input refs
  (`eia930-3697b311…`, `eia923-8ca120c6…`, `campd-48c0f1dd…`) — the
  strongest available proof the finisher scored against the solve's exact
  benchmark inputs.
* Two payload fields the empty plant map cannot produce were repaired from
  committed artifacts by `scripts/probes/_caiso224_payload_fuelrow_fix.py`
  (the committed instrument): the C4 gas `fuelRows` row recomputed on the
  native CEMS basis from the COMMITTED `bench/CAISO/<year>.json.gz` part's
  own `plants[].campd`/`btm`/`gas_cogen_grid` (the identical series
  `calibration_verdict._cems_gas_hourly_fit` decodes; quantization tolerance
  ≤~0.01 in r per its docstring), and the REPORTED-ONLY C5a `co2` block
  REMOVED (its full-plant basis needs the gitignored `btm.parquet`; a
  mislabelled grid-basis number would be wrong, so it reads SKIP — never a
  silent pass).
* The freshly-rendered bench parts (which an empty plant map would gut) were
  DISCARDED and the committed parts restored byte-identical; the caiso-220
  keeper's verdict was re-scored after every operation and is byte-identical
  to its pre-session baseline (`NOT-YET`, C3a FAIL only — the open problem
  this program chases).
* **Cross-proof:** the registered payloads' per-year load-weighted LMP equals
  the solve session's committed split-witness values to <$0.002 on all six
  run-years (rounding residual of the payload's 2-decimal zonal price / 4-
  decimal demand fields) — the slim render reproduces the solve's price
  surface.

`check_registry_payload_parity.py` PASSes (58 runs, both directions). Both
payloads travel over `git push` per CLAUDE.md Git & Pushing (§2 transport
rule); `push_files` cannot carry them.

## §G — Disposition, records, fences

* **Matrix (rule 28b):** the CAISO shard's `caiso_fsno_subzonal_topology`
  cell is stamped **R** with this finding as the citation, in this session.
  Base row and all-shard cell lines were minted when the gated field landed
  (rule 28c, the deliberately non-parallel edit) — only the CAISO verdict
  stamp was owed. No other ISO's shard is touched (rule 25).
* **The flag stays default-off.** No keeper change: the CAISO keeper remains
  `2026-08-26-caiso-220-c1-crosswalk`; keeper shard, `calibration-complete.json`,
  `holdout-freeze.json` untouched. Reads stayed inside 2023–2025 (rule 22).
* **What R means here, precisely** (per §5, verbatim intent): the STATIC
  DMM-CAP arm is rejected for keeper purposes. The partition representation —
  P-A′ zones, the caiso-223 measured membership
  (`data/raw/reference/caiso-fsno-subzone-membership.csv`) and 3-way ATL_LDF
  load split — is unrefuted and remains the standing sub-zonal
  representation for any future limit-side upgrade. Re-arming requires a
  year-varying and/or element-outage-aware limit object through W-2/W-3 (or
  the derate-channel WATCH maturing into publishable data), entering as a
  data intake with its own precommit — never a re-tune of these caps, and
  never anything backed out of binding hours or split counts (caiso-218 §F.2
  fence, untouched).
* **Records landed by this session:** both dashboard registrations (sidecars
  + payloads), this finding, the `docs/calibration-log/caiso.md` caiso-224
  entry, the CAISO matrix-shard stamp, and the payload-repair probe script.
  The solve session's own artifacts (bundles, tolerance, witness, precommit)
  were already committed and are byte-untouched.
