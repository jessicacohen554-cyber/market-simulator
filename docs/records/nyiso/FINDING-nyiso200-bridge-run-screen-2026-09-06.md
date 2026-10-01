# FINDING nyiso-200 — the bridge's P0-pattern dependence is REAL and it is the detector's, the nyiso-199 §8.3 STOP was fired by a one-year scorer artifact the span guard already handles, and the repair is the detector's own commitment-real run screen (G-61 path (b)) — zero DOF, wired for NYISO for the first time

**Session:** nyiso-200 (`claude/nyiso-gas-bridge-min-run-awz5xt`), 2026-09-06.
**Keeper at open: `2026-09-06-nyiso-196-extract-basis`** (CALIBRATED, grade 7 of 8, fails 0,
C3c the lone ledgered caveat).
**Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §3).
**Pre-registration:** `results/calibration/PREREG-nyiso200-bridge-run-screen.md`, pushed before
any solve. **Owner ruling recorded there before the first solve** (2026-09-06, verbatim): *"Is
this a recommended keeper candidate? If so plz promote. If structural integrity improves but
gates regress that may still be a keeper.."*
**Machine records:** `_nyiso200_bridge_phase0.json`, `_nyiso200_screen_gates_<arm>_<year>.json`;
probes `scripts/probes/nyiso200_*.py`.

---

## 1. The result in one paragraph

Three things are established, and both screened arms are STOPPED at their pre-registered gates
on 2023 with no further year spent (rule 29). **(i) The nyiso-199 §8.3 stop was a scorer
artifact of one-year screening**: the two convicted plants (7314, 50978) are `ct_only` reporters
the span scorer skips by construction, un-flagged only by the preliminary 2025 vintage; a one-year
bundle had no sibling vintage to union from. The guard now unions over the training span
(scorer-only, protective direction, keeper byte-identical). **(ii) The bridge's P0-pattern
dependence is real and it is the detector's**, and its repair is the detector's own
commitment-real run screen (G-61 path (b)), wired for NYISO as `nyiso_gas_bridge_startup_aware`
with zero free parameters. On the keeper's OWN 2023 P0 pattern it drops **1,173 of 1,576 CC runs
and 351 of 422 steam runs** as unable to repay a start, and the bridge's forced volume falls
**1.00 → 0.34 TWh** with zero C1 flips and C3a still PASS — the keeper's bridge is mostly anchored
on fragments a real unit commitment would not start. **(iii) The three-way pairing, screened on
2023, is the strongest single-year picture this lane has produced**: `ST_GAS` +1.81 → +0.46 TWh,
`CT_PEAKER` −1.69 → −0.99, C3a **+4.6 → +0.9 %**, C3b unchanged, zero C1 flips, **no new D-4 row
at the span guard** — with `CC_REGULAR` the one class moving away (+0.83 → +1.43 TWh, PASS). What
stopped each arm is a gate this session wrote, not the mechanism: A1 on a D-4 failure-row COUNT
that rose while the plant's forced energy fell (Astoria 8906's conviction migrated from the
bridge's row to the reliability floor's beneath it — the floor under the floor, rule 19), and A3
on a demand for ZERO bridge floor at the two named plants, where 542 h / 153 h remain, every one
anchored on a run that DID repay its start. **Nothing is registered, nothing is promoted, the
keeper is unchanged**, and the 2025 exposure of the pairing is unmeasured because the letter of
the gates says it may not be. §6 states the recommendation; §7 states the two gate constructions
the next PREREG must correct and the reliability-floor object the screen uncovered.

## 2. Phase 0 (zero LP) — what the nyiso-199 stop actually was

**2.1 The two convictions were on series the benchmark itself declines to trust — and the span
scorer skips them by construction.** The nyiso-199 2025 screen stopped on two new D-4
unit-conduct rows: 7314 (Flynn, Long Island, 170 MW `CC_REGULAR`; 3,210 binding hours, measured
median 0.0 MW) and 50978 (Upstate West, 123 MW; 352 h). Both plants carry the benchmark's
`ct_only` flag — EIA-923 net > 1.1× CAMPD gross, so the hourly CAMPD series is structurally
incomplete and the rider must not convict on it — in the complete 2023 and 2024 vintages, and lose
it only in the preliminary 2025 vintage, where `e_ann` falls back to `c_ann` and the ratio computes
exactly 1.00. That is the nyiso-145 §3 artifact, and nyiso-150 guarded it by **union-ing the flag
across the scored span**. The keeper's own committed diagnostics say so in words: *"2025: ct_only
vintage guard extended the flag from sibling-year vintages for 9 plant(s): … 50978 … 7314"*. A
rule-29 screen bundle scores ONE year, so its union was {2025} alone — the guard had no sibling
vintage to restore from — and the rider convicted exactly the plants the span scorer skips.

| plant | 2023 `ct_only` / CF / zero-share | 2024 | 2025 (preliminary) |
|---|---|---|---|
| 7314 | **True** / 0.184 / 0.571 | **True** / 0.214 / 0.534 | **False** / 0.160 / 0.636 |
| 50978 | **True** / 0.127 / 0.739 | **True** / 0.125 / 0.686 | **False** / 0.171 / 0.539 |

Union over {2025}: {2493, 54914}. Union over the training span: 12 plants, restoring 7314 and 50978
among ten. **2 of 2** of the nyiso-199 2025 failures are on restored plants; **0** survive the span
guard; the like-for-like count (0 ≤ the keeper's own 1) would not have fired the gate.

**Scorer-only repair, landed in this session:** `legitimacy_diagnostics.ct_only_guard_years` now
unions the flag over the ISO's training span whatever the bundle's own years (protective direction
only — it can only ever skip a conviction; a span keeper re-scores byte-identically; guarded by
`tests/scoring/test_ct_only_bench_flag.py::test_one_year_bundle_unions_over_the_training_span`).

Two things this does NOT say, stated so the finding is not over-read: (a) the production verdict
never consults D-4 for `CC_REGULAR` at all — `calibration_verdict._d4_provenance` escalates only
above the 30 % forced-share cap and the class reads 2.8 / 0.8 / 1.2 % — so the nyiso-199 stop was
the PREREG's own stricter "no new D-4 row" gate, not a C8 FAIL the span would have carried; (b) a
series the benchmark declines to trust is **unscorable, not exonerating** — the meter cannot say
whether 7314 was on in those 3,210 hours. The P0-pattern dependence is therefore judged on the
model's own economics, not on that meter.

**2.2 The object is real, and it is the detector's.** Every bridge leg — the min-run extension,
the online-hours state floor, the gap bridges — anchors on the model's OWN P0 run pattern. P0 is a
base-cost LP that pays no startup on a continuous ramp, so it manufactures runs a real unit
commitment would never start: the G-61 diagnosis the CAISO lane already carries. A merit change
moves P0's shape; nyiso-199 measured exactly that — cheaper `CT_PEAKER` offers displaced two
cycling CCs in P0, left them short P0 runs, and `nyiso_gas_bridge_min_run` extended those into
21 h min-load holds. Under rule 17 `[R-FLOOR-WINDOW]` the min-run leg's driver is *"a started unit
stays online for its minimum run"* and its evidence for "started" is a P0 run; a run whose whole
margin cannot repay one start is a run the driver's own economics say the unit would not have
started, so an extension floored on it binds in hours its own driver says the unit is off. That
is the defect, and it exists independently of any meter.

**2.3 The keeper's own bridge footprint (committed D-2 / D-4 rows)** — the repair can only REMOVE
floor, so this is its pre-solve reachability bound per year:

| year | `CC_REGULAR` forced TWh (share) | `ST_GAS` forced TWh (share) | **bound TWh** |
|---|---|---|---|
| **2023** | 0.8815 (2.76 %) | 0.1219 (1.02 %) | **1.0034** |
| 2024 | 0.2802 (0.79 %) | 0.2926 (2.70 %) | 0.5728 |
| 2025 | 0.4080 (1.21 %) | 0.1621 (1.34 %) | 0.5701 |

Neither 7314 nor 50978 is floored by the keeper in any year. The screen year by footprint is 2023.

**2.4 The eligible population and the screen's bar** (on-recipe `fleet_only` rebuild, no LP):
net of the keeper's two armed membership exclusions (13 plant codes), **21 / 22 / 22
`CC_REGULAR` base tranches (3,859–3,864 MW) at a $50/MW startup and 7 `ST_GAS` (1,298 MW) at
$35/MW**; 7314 (22.94 MW base tranche) and 50978 (45.52 MW) in the population every year at
min-down 4 h / $50/MW. The bar is `_ra_bridge_unit_params`' own registered constant — the
CAMPD-bin NREL/SR-5500-55433 value the economic leg already prices — so the repair selects no
number.

## 3. The repair — and why it is this one and not the one the handoff named

**`nyiso_gas_bridge_startup_aware`** (gated, default off, registered in every registry its sibling
legs are in, on the `gas_commitment_bridge` base row per rule 28(c), CLI
`--nyiso-gas-bridge-startup-aware`). It wires the shared detector's `startup_aware` run screen —
G-61 path (b), registered for CAISO as `caiso_ra_bridge_startup_aware` and never wired for NYISO —
into `_nyiso_gas_bridge_floor`: a detected P0 run anchors any leg only when its P0 energy margin
per MW, `Σ_t∈run (LMP_P0 − MC) × dispatch / pmax`, covers the unit's own published startup cost.
Runs failing it are removed before the min-run extension, the online-hours floor and the gap scan.
The detector now also fills an optional census (`screen_stats`: runs detected / dropped, P0 hours
de-anchored, units affected — diagnostics only, byte-identical when absent) which the NYISO wiring
logs per leg, so a screen reads what the mechanism DID.

* **Rule 19 `[R-ONE-MECH]`** — what already floors `CC_REGULAR`: this bridge (2.8 / 0.8 / 1.2 %)
  and nothing else. The repair adds no floor; it narrows the run set every existing leg reads.
* **Rule 18 `[R-PHYSICS]`** — gates on the unit's own start cost, never a class name.
* **Rule 13 `[R-MEASURED]` — why NOT "condition eligibility on the unit's own measured conduct in
  the window", the nyiso-199 handoff's construction.** An hourly meter test inside the solve is a
  one-sided pin to observed CEMS generation with no forward analogue — it fails rule 13's own
  admissibility test — and on 7314 it would read a series the benchmark declines to trust. The
  plant-level form, a conduct-based membership exclusion, was refused ex ante by nyiso-144
  (*"7314 … is a cycler the model's own P0 over-runs, so its forcing is an offer/economics defect
  and excluding it would bury that error in a membership list"*) and again at miso-170. The
  admissible measured membership channels (lay-up, reserve duty) already exist and stay armed. The
  run screen is the economics-side repair those rulings pointed to.
* **Rule 21 `[R-DOF]`** — zero free parameters, no ledger entry: the bar is the bridge's own
  registered startup constant; the prices and MC are the model's P0 duals and objective.
* **Forward-native** — regenerates from a forecast year's own P0.

Tests: `tests/iso/nyiso/test_nyiso_gas_commitment_bridge.py::TestCommitmentRealRunScreen` (a 2 h
P0 fragment at $10/MW margin is extended without the screen and not with it; at $60/MW it is still
extended; the flag absent and explicitly `False` are byte-identical through the wiring; the screen
gets its prices even with the economic leg off). 135 tests pass across the bridge, detector and
scoring files; `tests/unit/config` 715 pass; `check_mechanism_matrix.py --base origin/main` exit 0.

## 4. G-DRIFT (rule 29(b)) — the keeper's committed bundle is the control

`git diff f7bb76a5..HEAD` on the solve path touches 53 files / 7,569 insertions. Validated
empirically, the nyiso-199 §6 way: the committed keeper-sha probe record
`_nyiso198_rebuild_checks_2024.json` (the keeper recipe's per-plant / per-band LP `pmax`, 42
leaves) re-run at HEAD on a fresh cache reproduces **0 differing leaves, max |Δ| 0.0**. The one
changed `_validation-source` input (`actual_lmp.json`) adds PJM load-weighted rows only. Scorer
changes since the keeper sha are a ruff-format pass and the Y-17 bench-staleness fingerprint.
**Form 4 is valid; no control solve was spent.**

## 5. The screens

Four one-year rule-29 throwaway solves were pre-registered (A1 = the repair alone; A3 = the
three-way pairing with `nyiso_ct_peaker_bands_measured` + `cc_duct_peaking_row_scoped`), on
2023 (the footprint year) and 2025 (the exposed year), ONE LP at a time, gated by
`scripts/probes/nyiso200_screen_gates.py` exactly as PREREG §5 is written. Records
`_nyiso200_screen_gates_<arm>_<year>.json`; bundles deleted before merge (rule 29(c)). Each
solve took ~4 minutes.

### 5.1 A1-2023 — the repair alone on the keeper recipe: the mechanism does exactly what it says, and the pre-registered companion gate STOPS it on a row that is an attribution shift at one plant

**The census (the log's own line, the mechanism's arithmetic):** on the keeper's OWN 2023 P0
pattern the screen drops **1,173 of 1,576 `CC_REGULAR` P0 runs (7,186 P0 online hours at 13
units), 122 of 228 state-cohort runs (1,122 h, 3 units) and 351 of 422 `ST_GAS` runs
(10,194 h, 6 units)** as unable to repay one start. That is not inert: the keeper's bridge is
mostly anchored on fragments a real unit commitment would not start — the same finding CAISO's
own lane made of the same detector (G-61(b): ~40 % of its RA-bridge forced energy was
phantom-anchored, `caiso-ct-drag-d8-closure-2026-07.md` §8–§9; stated as context, no verdict
transfers, rule 25).

| gate | reading | verdict |
|---|---|---|
| **S-1 direction / bound** | bridge D-2 forced volume **1.0034 → 0.3439 TWh** (`CC_REGULAR` 0.8815 → 0.3373, `ST_GAS` 0.1219 → 0.0066); fall 0.66 inside the 1.0034 bound; no rise | pass |
| **S-2 census identity** | floors move at 16 plants; the census names 22 units with dropped runs; no floor moved where no run dropped | pass |
| **S-3 confinement** | gas family total −0.007 TWh; import +0.006; no non-gas class moves | pass |
| **S-4 companions — C1 / C3a / C3b** | zero C1 flips (`CC_REGULAR` +0.83 → **+0.37 TWh**, +1.2 → +0.8 pp; `CC_CHP` +0.95 → +1.18; `ST_GAS` +1.81 → +1.92; `CT_PEAKER` −1.69 → −1.67); C3a **+4.6 → +5.7 %** PASS (the de-anchored floors were price-suppressing, the CAISO signature); C3b 0.119 unchanged | pass |
| **S-4 companions — C8 / D-4** | D-2 clean both sides; **one NEW D-4 unit-conduct row: `reliability_floor × ST_GAS` plant 8906 (Astoria), 0.2271 TWh over 5,400 binding hours, measured median 0.0 MW** | **STOP** |

Class energy: `CC_REGULAR` **−0.462 TWh**, `CC_CHP` +0.230, `ST_GAS` +0.109, `CT_CHP` +0.055,
`ST_CHP` +0.042, `CT_PEAKER` +0.019, import +0.006.

**What the row that fired actually is.** Astoria 8906 is the keeper's own pre-existing D-4
conviction: its BRIDGE row fails in the keeper (0.0463 TWh, 1,400 h, median 0.0 MW, 74 % dark)
and its RELIABILITY-FLOOR row passes (0.2038 TWh, 4,140 h, median 81.4 MW, 44 % dark). Both
mechanisms floor the same plant, and the floors compose by maximum, so a binding hour is
attributed to whichever floor is higher. The run screen removes the bridge floor at 8906
(1,400 → 34 h — the repair working), and the 1,260 dark hours it had been holding at the higher
bridge level now sit at the reliability floor beneath: the reliability row grows 4,140 → 5,400 h,
its median over binding hours goes 81.4 → 0.0 MW, and the SAME conviction migrates from one
mechanism's row to the other's. At plant grain nothing regressed: **8906's total forced energy
0.2501 → 0.2282 TWh (5,540 → 5,434 binding hours), its annual dispatch 976 → 981 GWh, and the
fleet's forced energy at dark-median plants 0.2515 → 0.2296 TWh**; 2480, the other dark plant,
is byte-identical. What stood under the bridge at Astoria is the reliability floor's own
membership question at a plant whose 2023 meter is dark 74 % of the time — the nyiso-140/144
pattern one mechanism later (*"repaired one MECHANISM, not the plant"*, rule 19).

**Disposition under rule 29: A1 is STOPPED at its pre-registered gate.** The gate as written
counts this year's D-4 failure rows, and it fired; a screen gate may kill an arm and this one
did. It is reported as such, with the attribution analysis above at full magnitude, and
**A1-2025 was not spent**. What is handed forward is the gate's own lesson (§7): a
failure-row COUNT can rise while the plant's forced energy falls, whenever two mechanisms floor
the same plant and the higher one is removed; the like-for-like measure is forced energy per
dark-meter plant, which this arm improves.


### 5.2 A3-2023 — the three-way pairing: every companion gate clears, including C8/D-4, and the pre-registered named-plant gate STOPS it on 542 + 153 commitment-real floored hours

**Census** (the P0 pattern is now the pairing's own, not the keeper's): 966 of 1,317 CC runs
dropped (6,308 h, 12 units), 157 of 254 state-cohort runs (2,017 h, 3 units), 255 of 309 steam
runs (15,010 h, 6 units).

| gate | reading | verdict |
|---|---|---|
| **S-1 direction** | `CT_PEAKER` **+0.702 TWh**, inside the CT arm's own 2.627 TWh bound | pass |
| **S-2 confinement** | gas family −0.005 TWh; import −0.020; no other non-gas move | pass |
| **S-3 companions — C1 / C3a / C3b** | **zero C1 flips**: `ST_GAS` +1.81 → **+0.46 TWh** (+1.6 → +0.5 pp), `CT_PEAKER` −1.69 → **−0.99** (−1.3 → −0.8 pp), `CC_REGULAR` +0.83 → **+1.43** (+1.2 → +1.6 pp, PASS), `CC_CHP` +0.95 → +1.28; C3a **+4.6 → +0.9 %** (mean price 32.97 → 31.77 $/MWh, p95 48.4 → 44.5); C3b 0.119 unchanged | pass |
| **C8 / D-4 at the span guard** | D-2 clean; **no new D-4 row** (the only 2023 failure is the keeper's own 2480 reliability-floor row); Astoria 8906's reliability row reads 0.2631 TWh / 6,025 h / median **13.6 MW**, pass — the pairing re-shapes NYC steam so the row does not tip; the union guard extended `ct_only` for 2503 and 54131, i.e. the nyiso-200 scorer repair is live in a one-year bundle | pass |
| **S-4 the defect read directly** | bridge floors at **7314: 542 unit-hours / 10.0 GWh** (65 segments, median 8 h, 18.2 MW) and **50978: 153 h / 5.1 GWh** (32 segments, median 5 h, 30.6 MW), against the keeper's 0 / 0 | **STOP** |

Class energy: `ST_GAS` **−1.354 TWh**, `CT_PEAKER` **+0.702**, `CC_REGULAR` **+0.597**, `CC_CHP`
+0.329, `CT_CHP` −0.213, `ST_CHP` −0.066, import −0.020. Bridge forced volume 1.0034 →
**0.3066 TWh**. Plant grain: 7314 273 → **124 GWh**, 50978 253 → **143 GWh** (the CT arm
displaces both cyclers, which is the nyiso-199 mechanism, now with the phantom anchors gone),
Bethlehem 2539 4,857 → 4,399 GWh, Astoria 8906 976 → 830 GWh.

**What the row that fired actually is.** The 542 and 153 hours are bridge floors anchored on P0
runs that **passed** the screen — runs whose P0 margin repaid the $50/MW start, i.e. runs the
mechanism's own driver evidence says the unit started. They are gap bridges and min-run
extensions on commitment-real runs, 5–8 h median segments, at 18–31 MW. Whether the meter agrees
cannot be read: both plants are `ct_only` reporters and the rider skips them (§2.1). The
pre-registered gate demanded ZERO floor at the named plants — written on the assumption that the
pairing would remove every anchor there — and it fired on floors the repair's own logic admits.
That is a gate-construction fact about this PREREG, stated at full magnitude; it is not a
finding that the pairing manufactures commitment where the driver says the unit is off, which is
what nyiso-199's 3,210 h at 76 % dark was.

**Disposition under rule 29: A3 is STOPPED at its pre-registered gate, and A3-2025 — the exposed
year — was not spent.** The 2025 price exposure of the pairing is therefore UNMEASURED: the CT
arm alone read −9.1 % there (nyiso-199), the duct arm alone −10.3 % on the span (nyiso-198), and
the run screen alone raises prices (+1.1 pp in 2023), so the sign of their sum on 2025 is not
knowable from this session's records.

### 5.3 What A1 and A3 agree on

* **The screen is live and large on the keeper.** 74 % of the keeper's own CC runs and 83 % of
  its steam runs are fragments that cannot repay a start; the bridge's forced volume falls by
  two-thirds under either arm, with zero C1 flips and C8 clean. The mechanism does exactly what
  §3 says; its own arithmetic is not in question anywhere in either screen.
* **The 7314 / 50978 floors are bounded by the repair.** Under the pairing they are 542 / 153 h
  on commitment-real anchors, against the 3,210 / 352 h phantom-anchored extensions nyiso-199
  measured under the CT arm without the screen.
* **Prices move the way the CAISO lane measured for the same leg** — de-anchored floors were
  price-suppressing (+1.1 pp C3a in A1) — and the pairing's CT-band effect dominates it (−3.7 pp
  net in A3).

## 6. Disposition and recommendation

**Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`. Nothing registered. No span solved.**
Both arms were killed at their 2023 screens by pre-registered gates; rule 29 says a screen may
kill an arm and the remaining years are never spent, and this session does not re-read its own
gates after they fired — selecting the gate an arm passes is the hazard the rule exists for.
The owner's standing formula (*"if structural integrity improves but gates regress that may
still be a keeper"*) has nothing to act on here: no span run exists to promote, and this session
does not recommend spending one on the strength of a single-year screen that its own gates
stopped.

**The recommendation is the next session's PREREG, not a keeper.** The structural half is not in
doubt in either arm — zero DOF, the detector's own registered constant, every census line the
mechanism's own arithmetic, A3-2023 moving `ST_GAS`, `CT_PEAKER`, prices and every D-4 row
toward or onto their actuals with no flip anywhere. What is unresolved is (a) a 2025 price
exposure the pairing has never been screened on, and (b) two gate constructions that fired on
readings that are not the defects they were written to catch. Both are fixable ex ante, and §7
writes them down so the re-screen is pre-registered, not re-litigated.

## 7. Handed forward

1. **Re-screen A3 on 2025 under corrected gates, pre-registered before the solve** (the only
   solve the next session needs first; ~4 min): **(a)** the C8/D-4 companion compares forced
   energy per dark-median plant like-for-like (this session's §5.1 table), not the failure-row
   count — a count rises whenever the higher of two composed floors is removed at a plant the
   lower one also floors; **(b)** the named-plant gate is "no bridge floor at 7314 / 50978
   anchored on a DROPPED run" (zero by construction of the screen) plus "no new D-4 conviction at
   the span guard", not "zero floor" — a floor on a run that repaid its start is the mechanism
   working; **(c)** C3a-2025 stays the named risk and a FAIL there is still a STOP. If it clears,
   the span, registered, with the determination reported at full magnitude and the promotion
   question put under the owner's formula with `CC_REGULAR` (+0.6 TWh in 2023) named as the
   class that moves away.
2. **The floor under the floor: Astoria 8906 and the reliability floor's membership.** The run
   screen removed the bridge at 8906 (1,400 → 34 h) and the reliability floor beneath it now
   binds 5,400 h at a plant whose 2023 meter is dark 74 % of the time; the plant's total forcing
   FELL, but the reliability floor's persistent-base limb is asserting ~0.23 TWh at a plant the
   lay-up census does not exclude (it is not 18/18 dark). That is the nyiso-140 question at one
   more plant, on the reliability floor's own row, and it is answerable from source data only
   (rule 23): either 8906's conduct qualifies it for `reliability_floor_plant_exclusions` under
   the existing criterion or the criterion is the thing to look at — never a residual.
3. **`nyiso_gas_bridge_startup_aware` on the keeper alone is a keeper-change candidate in its own
   right** once (1)(a) is the gate: A1-2023 has zero flips, C8 clean, the bridge two-thirds
   smaller and `CC_REGULAR` closer to its actual. Its 2025 screen was never spent.
4. **Rule 26: the two R cells stay R** with their re-test condition now sharpened — the partner
   is `nyiso_gas_bridge_startup_aware`, the three-way arm has cleared 2023 on every companion
   gate, and 2025 is the open question.
5. **Repo-wide, outside this lane (rule 25):** every ISO's one-year rule-29 screen scored D-4
   with a one-year `ct_only` union until this session; the training-span union now applies to all
   six, protective direction only. Any prior one-year screen stopped on a D-4 unit-conduct row at
   a plant that is `ct_only` in a sibling year should be re-read before being cited as a stop.

*(nyiso-200, 2026-09-06. TWO solves, both one-year rule-29 screens, both deleted before merge
(29(c)). Nothing registered, nothing promoted, no span spent. Keeper unchanged:
`2026-09-06-nyiso-196-extract-basis`.)*
