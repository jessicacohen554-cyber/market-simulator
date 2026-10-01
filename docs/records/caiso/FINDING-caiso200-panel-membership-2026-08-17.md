# FINDING — caiso-200: the §3b FLEET-MEMBER PANEL SCOPE lands byte-identically to the pre-flip run-Y measurement and is PROMOTED KEEPER on the owner's structural-integrity instruction — the C1-2023 return watch answers NO (+3 GWh), which is itself the structural finding

**Pre-registration:** `PRECHECK-caiso200-panel-membership-2026-08-17.md`,
committed and pushed at `45254f1` **BEFORE any derive or solve of this session
ran**. All shas (committed pair AND the caiso-198 run-Y target pair) were fixed
in that document ex ante; none was edited afterwards. Gates applied as written.

**Adjudication executed:** the caiso-200 handoff delegated the caiso-199 §4
owner decision (A: promote g1 / B: decline / C: fund §3b first). The session
adjudicated **(C)** at start (PRECHECK preamble, grounds 1–3), ran the closure,
and re-decided under the §6 pre-registered decision tree — whose branch 1
fired and was **ratified by the owner in-session** ("Is this a recommended
keeper candidate? If so plz promote. If structural integrity improves but
gates regress that may still be a keeper").

**Registered runs:** `2026-08-17-caiso-200-h0-control` (bundle
`caiso200_h0_control`) and `2026-08-17-caiso-200-h1-memberpanel` (bundle
`caiso200_h1_memberpanel`). 2023–2025 only, one bundle per arm, years
sequential, arms sequential (rules 12/16). **KEEPER →
`2026-08-17-caiso-200-h1-memberpanel`** (promotion duties executed in-session:
attestation generated at promotion, lane pruned to the keeper alone per the
standing 2026-08-15 directive, shard + matrix + §5.2 + status re-stamped,
`audit_keepers` PASS).

**The extract LANDED and SUPERSEDES**: main `da33e509…` → **`cf156483…`**
(4,710 rows), layup `1475a577…` → **`4ccae12e…`** (819 rows) — byte-identical
to the caiso-198 run-Y product, i.e. to a measurement taken **before the C1
flip existed**.

## 0. Head repair, disclosed first

`main` at `a4ef2a9` was **UNSOLVABLE**: `scripts/run_calibration.py` carried a
duplicate `reliability_floor_plant_exclusions` parameter in `run_year` — the
8839960 (nyiso-140 registration) / 7246272 (ercot-213 repair) **semantic merge
collision** via #4036: two branches repaired the same 3febd5c signature gap
independently and the merge stacked both copies with no textual conflict.
Deduped at `5148f2e` (keep the documented 7246272 copy; drop the bare copy and
the second identical override block), blob-verified after push. Every
calibration solve of every ISO was blocked at that head; a parallel lane
(miso-162, `a84baa2`) independently deduped the same collision on main.
G-CTRL below measures the repaired head.

## 1. Direction-hazard regime — REVERSED sign, honoured

PRECHECK §0, binding: the expected sign of this delta was **C3a- and
C1-2023-FAVORABLE** (it can only REMOVE measured outage removal), so C3a was
doubly inadmissible and acceptance rested solely on the ex-ante byte-identity
gates and the structural membership argument. The anti-tuning defense is that
the object's entire content was fixed by the caiso-198 run-Y measurement
before the flip fired, with **zero free parameters**. Outcome: the movement
was immaterial anyway — C3a is unchanged at 2 dp in every year and C1-2023
moved +0.003 TWh. Nothing favorable was bought, and nothing was consulted.

## 2. Gate tally — all PASS

| gate | measured | verdict |
|---|---|---|
| **G-CTRL** | **BIT-ZERO** vs the committed `caiso199_g1_meritpin` sidecars (the committed baseline for the landed-extract configuration): max \|Δ\| = 0.0 over every zone-hour of `hourly/system_*.parquet` (prices included) and every class-hour of `hourly/class_hourly_*.parquet`, all three years (`_caiso200_ctrl_tolerance.json`). Noise floor exactly 0.0, quoted before any treated delta. Also the measured proof that the head drift since caiso-199 (#4036/#4032/#4031 merges + the `5148f2e` dedup) and the member-scope code are inert on the CAISO solve path. | **PASS** |
| **G-MEMBER** | The derived member map resolves to **exactly `{NV: (55077,)}`** — Desert Star, the sole CAISO-fleet facility among the 15 NV facilities seen 2018–2026. Derivation: out-of-panel detection states' facilities whose plant code (via the CEMS→EIA remap where one applies) resolves into the ISO's own fleet registry — the same `group_by_code` the detection path filters on. | **PASS** |
| **G-DELTA (a)** | Member scope DISABLED ⇒ the committed pair reproduces **byte-identically** (`da33e509…`/`1475a577…`, 4,719/810 rows): the implementation is inert unarmed — the narrowing's own baseline byte-identity proof. | **PASS** |
| **G-DELTA (b)** | Member scope ARMED ⇒ the caiso-198 run-Y product reproduces **byte-identically** (`cf156483…`/`4ccae12e…`, 4,710/819 rows) — a cross-construction (directory-scope → membership-scope), cross-head reproduction of the pre-flip measurement. | **PASS** |
| **G-DELTA (c)** | Movement EXACTLY the §0a pre-registration: **all 158 facility-55077 rows retained in main**; exactly **9** pre-existing CA-facility windows leave main and the same 9 enter layup; zero additions; zero other window movement; headers identical; every kept main row byte-identical and in order. Shared layup rows differ **only** in the re-measured `out_of_merit_share` column (111 rows, deltas 0 to +0.052, mean +0.001 — the RCC dip of the member CC joining the panel). Mover census: Glenarm ×4 (GT3 2023, GT4 2019 + 2023, GT5 2018 — CC_REGULAR, 60.5 MW units), Yuba City 2 / Bear Mountain GT1 / Live Oak GT1 (CT_CHP, 2020/2019/2020), Algonquin Sanger 8 (CC_REGULAR, 2019), Lodi CT1 (CC_REGULAR, 288.9 MW, 2023); oom shares **0.900–0.932** — borderline windows tipped over the 0.90 threshold. Three movers fall in solve years: **all 2023, all CC_REGULAR** (Glenarm GT3 9.7 d, Glenarm GT4 6.8 d, Lodi CT1 13.3 d — spring). | **PASS** |
| **G-DELTA (d)** | h0-vs-h1 `scenario_config` diff **EMPTY** over 717 keys. | **PASS** |
| **G-ENGAGE** | Exactly the census: loader derate factors rise in 2023 at the two mover plants (Glenarm 0.3008→0.3066, Lodi 0.6369→0.6733; all 16 other key-years unchanged); the LP differs in **2023 only** (4,331 price zone-hours by bitwise count, 2,686 above 1e-9; max \|Δprice\| $68.09; 263 class-hours) and is **bit-identical in 2024/2025** — no solve-year mover exists there. Not inert. | **PASS** |
| **G-SIXISO** | Only CAISO's extract moved; every other registered ISO admits no member facilities (asserted by test over the registry); the membership derivation can admit only the ISO's own fleet by construction. | **PASS** |
| **G-DOF** | Ledger **10/7 carried byte-identically** onto both bundles (`_caiso200_carry_dof_ledger.py`; import-tranche census row n_scalars 6 intact). Zero new parameters — fleet membership is a market fact and the delta content was fixed pre-flip. | **PASS** |
| **G-C8** | Both bundles ship and score `legitimacy_diagnostics.json`; C8 PASS both. | **PASS** |
| **G-COV** | Unchanged by construction and by measurement: detection content untouched, all 158 DS rows retained in main ⇒ CC_REGULAR extract population stays **1.000000**; no facility lost its last main-extract row (each mover facility retains its other windows). | **PASS** |

**Single-mechanism statement (PRECHECK §3, verbatim):** "The A/B delta is the
fleet-member panel-scope extract re-derive and the 9 CA-facility windows it
reclassifies mechanical→layup; no ScenarioConfig field differs."

## 3. The §0a record correction, now measured

FINDING-caiso199 §3 item 3, the matrix cell, and the caiso-200 handoff all
read caiso-198's run Y as reclassifying "9 of the 158" Desert Star windows
(bounding the fail-safe's error at ~5.7 %). **The committed record and this
session's re-derive both show otherwise**: the 9 movers are **pre-existing
CA-facility windows**, and **ALL 158 Desert Star windows are retained as
mechanical by the guard that can finally see them**. The correction
STRENGTHENS the caiso-199 §3 conclusion: the fail-safe's default was what the
guard itself concludes for **100 %** of the Desert Star windows, not ~94 % —
the plant's mid-winter cycling signature windows are real mechanical
unavailability by the instrument's own test. The collateral is the small RCC
dip of an efficient member CC joining the panel, which tips 9 borderline CA
windows (all with oom ≥ 0.90 already) into economic layup.

## 4. The watches

**Watch 1 — C1-2023 return: NO.** The row moves −4.246 → **−4.243 TWh**
against the ±4.15 band: the closure returns **+0.003 TWh** (3 GWh). Upper
bound on the restorable energy was ~0.116 TWh (the three windows at
nameplate); the LP, offered the restored spring capacity, dispatched almost
none of it. **This is the structural finding:** the guard classified those
windows as *economic* non-operation, and the dispatch model — the independent
instrument — agrees: the market did not want that energy in those hours. The
C1-2023 CC_REGULAR deficit is therefore a **real residual of the class** (the
standing CC-side under-dispatch / over-import lane: caiso-121 surplus-belly,
caiso-135 ride-through, caiso-140 §B belly wedge), not an artifact of the
outage instrument. The volume face of that lane, which caiso-197 closed to
−4.13 and the caiso-199 measured landing re-opened to −4.25, is now measured
to be ~97 % structural.

**Watch 2 — criteria flips: NONE.** h1 vs the caiso-199 g1 arm: no
criteria-panel movement at all (C1 FAIL on the same single row, marginally
smaller; C2/C3b/C4/C8 PASS; C3a FAIL 2024/2025 unchanged at 2 dp; C3c per the
ledger below). No new load-bearing FAIL ⇒ §6 branch 1.

## 5. The promotion

**Keeper → `2026-08-17-caiso-200-h1-memberpanel`** (§6 branch 1: gates pass,
arm engaged, load-bearing FAIL set {C1, C3a} ⊆ {C1, C3a}), ratified by the
owner in-session. Determination **NOT-YET**: C1 (single row, 2023 CC_REGULAR
−4.243 TWh, 11/12 · free 7/8) + C3a (+4.1 PASS / +12.8 / +15.7 %). **C3c is
the single ledgered caveat**, magnitudes re-measured on this bundle at the
promotion per caiso-189 §8.3: 2023 model 0 h vs RT actual 47 h; 2024 **1 h**
vs 35 h (the 1 h entered at the caiso-199 landing); 2025 PASSES.
Classification and reason carried byte-identical through the caiso-184 → 188
→ 196 → 197 lineage; no new slot spent. **C6 PASSES** — attestation generated
AT promotion by `scripts/gen_caiso200_attestation.py` (G-DELTA / G-RECIPE /
G-EXTRACT `da33e509`→`cf156483` A/B provenance == live tree / G-ENGAGE /
G-MACHINE / G-DOF / G-EXC, every premise computed). C8 PASSES. LOYO
discharged by construction (zero fitted values anywhere in the delta).

**Vs the alternatives.** caiso-197 (option B) would keep a keeper whose
classifier was coverage-incomplete AND which is no longer byte-reproducible at
HEAD (its extract no longer exists in the tree). caiso-199-g1 (option A as
written) embodies the landing but leaves the §3 item-3 asymmetry open — 158
windows retained by fail-safe, never tested. h1 embodies the identical
landing, closes the asymmetry, and costs nothing further: its criteria panel
is identical to g1's (C1 marginally better). The instrument arc
25360e90 → 5f3e35c5 → da33e509 → cf156483 is complete: **CC_REGULAR is 100 %
population-observed and every window of every fleet plant is now testable
against a panel it belongs to.**

## 6. Probe defects, disclosed

1. The arm-stage row-accounting first cut byte-compared shared layup rows and
   FAILED its own sub-checks — it wrongly assumed the layup companion's
   `out_of_merit_share` column frozen across a panel change. The column is
   the panel's own measurement and legitimately re-measures (111 rows,
   ≤ +0.052); the corrected accounting is window-key grained, and the
   pre-registered sha pins (the primary instrument) had already matched
   before the defect was hit. Fixed in place, both versions in git history.
2. The same first cut naively comma-split CSV lines and crashed on quoted
   facility names containing commas; fixed with csv-module parsing.

## 7. Queue posture and the frontier

**The in-model queue is EXHAUSTED — now confirmed by measurement rather than
inventory.** The §3b option was the last named in-model object (caiso-199 §4);
it is now landed, promoted, and its C1 hypothesis measured (3 GWh). The only
named C3a routes remain the two standing owner objects: the walled hourly PS
water-state intake (caiso-141 / ruling 4 — purchase DECLINED) and the
8,800 MW declared residual (caiso-191 §4 — desk-adjudicated NO, no citable
axis). Owner ruling 5 stands: **C3a must genuinely pass; NOT-YET is the
honest fallback.** The frontier/complete-readiness assessment is
`ASSESSMENT-caiso200-frontier-2026-08-17.md` (the neiso-87 pattern): a
`complete` declaration is **NOT supportable on the merits**, and the decision
in front of the owner is whether to fund either standing object or hold the
lane at its honest NOT-YET.

## 8. Holdout posture

**2023–2025 solves ONLY.** CAISO holds NO `complete` and NO `final` marker;
the spend freeze is ACTIVE; no out-of-training year was solved, scored or
registered. The 2018–2026 derive span is data preparation (rule 22,
spend-only enforcement — the caiso-196/198/199 precedent).

## 9. Artifacts

Runs `2026-08-17-caiso-200-h0-control`, `2026-08-17-caiso-200-h1-memberpanel`
(slim files + hourly sidecars + `legitimacy_diagnostics.json` +
`free_parameters` 10/7; h1 + the promotion attestation). Records:
`_caiso200_ctrl_tolerance.json` (G-CTRL bit-zero),
`_caiso200_member_panel_gates.json` (G-MEMBER + G-DELTA legs a–d + movement
census + factors pre/post + G-ENGAGE). Probes:
`scripts/probes/_caiso200_ctrl_tolerance.py`, `_caiso200_member_panel_gates.py`,
`_caiso200_carry_dof_ledger.py`; generator `scripts/gen_caiso200_attestation.py`.
Code: `campd.MERIT_PANEL_FLEET_MEMBER_ISOS` + `merit_panel_admits_fleet_members`,
the deriver's `_merit_member_facilities` + wiring + `[scope CA +members
NV:55077]` log line, `build_merit_order_panel(member_facilities=…)`, and
`tests/curation/test_campd.py::TestMeritPanelFleetMembership` (6 tests incl.
the remap-resolution and wiring guards). PRECHECK @ `45254f1`; head repair @
`5148f2e`. Site retention: lane pruned to the keeper alone (5 runs off the
site — the superseded caiso-197 keeper, the caiso-198 control, the caiso-199
A/B pair, and h0 — durable evidence retained in the FINDINGs, gate records and
git history; dangling citations deliberate per the standing directive). Matrix
duty (b): `campd_outage_windows` CAISO cell updated, the extract sha
superseding to `cf156483…`, the §0a correction recorded; §5.2 heading + shard
keeper/gates stamps rewritten. Calibration-log entry in
`docs/calibration-log/caiso.md`. Also disclosed: two pre-existing MISO
sidecars (`2026-08-16-miso-160-*`) have no matching run payloads (the parity
check flags them) — another lane's stranded registration, not touched here
(rule 25).
