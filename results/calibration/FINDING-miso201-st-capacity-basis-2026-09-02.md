# FINDING miso-201 — the ST-side capacity BASIS gap is REAL, the charter's "inert" caution was CONFIRMED AND THEN SUPERSEDED BY THE SAME MEASUREMENT, and the arm is PROMOTED with its one fired kill disclosed (2026-09-02)

**Session:** miso-201 (2026-09-02). **Keeper at open:** `2026-09-02-miso-200-unitroute`.
**KEEPER AT CLOSE: `2026-09-02-miso-201-stbasis`** (bundle
`results/calibration/miso201_stbasis_B`), promoted under the owner's standing re-scoped
bar, restated verbatim in-session: *"If structural integrity improves but gates regress
that may still be a keeper."* `audit_keepers --iso MISO` **PASS 0/0**.

**Charter:** FINDING-miso200 §8 item 1 — the ST_GAS/ST_CHP analogue of
`unit_outage_lp_capacity_basis`, which is CC-only (`_CC_NAMEPLATE_BASIS_GROUPS`) and so
can never reach a steam bin.

---

## 1. The answer, in one paragraph

The charter's caution was right about the overflow and wrong about the object, and the
same measurement establishes both. At Ninemile Point 1403 and Moselle 2070 the pre-clip
**overflow** is genuinely inert — the units carrying the windows are exactly the units in
the bin, so a concurrent full stop means the bin really is 100 % out and availability
0.0000 is correct. **But the overflow was never the object.** The basis gap over-removes
in **every hour a steam unit is out**, and the clip hides only the extreme: at 1403
itself, unit 5 alone out removes `895.1 / 1465.4 = 0.611` of the bin against a correct
`742.6 / 1465.4 = 0.507` — real over-removal, in exactly the hours that do *not* overflow.
**The lever is live at the very facility the charter named inert**, and it was the
charter's own instruction — find where the overflow is "not already landing on the correct
answer" — that surfaced it. Root cause pinned at primary source: EIA-860 generator `5` at
1403 is **nameplate 895.1 MW against net summer 742.6 MW**, while the extract's numerator
is that nameplate and the fleet denominator is net summer. The repair puts each row's
removed MW on **the LP's own basis** (the fleet unit's `pmax_mw`), all-or-nothing per bin,
so a bin all of whose units are out lands on **exactly 1.0**. Zero fitted scalars, 32 of
55 steam bins eligible (8,553 of 12,291 MW, 69.6 %), +1,576 / +1,968 / +1,403 GWh of
wrongly-removed capability returned. The A/B is **K-1 silent with no band exit anywhere**,
ST_GAS moves toward actual in all three years, and **one frozen kill (K-3) fired** on a
single cell — reported at full magnitude, not renegotiated.

## 2. A design correction the charter's own vocabulary would have got backwards

The charter (inheriting the CC flag's name) framed this as a **denominator** alignment.
Measured, that direction is **wrong for a steam bin**, and the reason is worth recording
because a successor will meet it again.

`unit_outage_lp_capacity_basis` raises the denominator because `fleet_to_bins` had
*already* raised the CC bin's LP capacity to nameplate: the map was chasing a change the
LP had made. **Nothing raises a steam bin's LP capacity.** So raising the steam denominator
to nameplate would put the share on a basis the LP never applies it to — at 1403 a
nameplate denominator makes a full concurrent stop read
`(895.1 + 786.0) / (895.1 + 895.1) = 0.939`, i.e. **89 MW of phantom availability at a
plant that is entirely out**. The correct move is the mirror image: put the **numerator**
on the LP's basis. The mechanism is therefore named for the family it belongs to and built
in the opposite direction, with that reasoning recorded at the field, the CLI flag and the
matrix row.

## 3. What phase 0 measured, before the mechanism existed

`_miso201_st_basis_phase0.json`, committed at `d331c1cb` **before** the PREREG and before
a line of mechanism code.

* **N-1 reproduction PASS on 988 bins.** The pre-clip share is reconstructed from the
  production code path and every bin asserted to reproduce `clip(1 − v, 0, 1)` exactly,
  for **both** overlays that reach steam bins. The maxgen layer does **not** share the std
  accumulator (its rows carry a measured `derate_mw` over an hour-granular half-open
  window, class-agnostic, no status filter), so it got its own faithful reconstruction
  rather than being run through the wrong one.
* **N-3, the census the charter asked for.** 65 steam overflow cells, of which the
  count-based liveness test flags 13. **That test false-positives**, and the finding says
  so: the `eia923_netzero` family carries ONE synthetic row whose `unit_capacity_mw` is the
  **whole plant's** nameplate standing for a whole-plant lay-up, so counting it as "one
  unit out of two" flags a bin live when zeroing it may well be correct.
* **N-5/N-7, the honest magnitude.** The buildable design's capability is
  **+1,576.0 / +1,968.3 / +1,403.2 GWh** for 2023/2024/2025, and the **built mechanism
  reproduces it exactly** (+1576.02 / +1968.34 / +1403.23) — the strongest available check
  that the committed probe and production are the same object.

### Two families separated rather than absorbed

Both are real, both are reported, **neither is repaired here**:

1. **The `eia923_netzero` whole-plant lay-up rows.** One synthetic `NET0-923` row per
   plant carrying the plant's TOTAL nameplate against a single group's bin (54518: 100.8 MW
   against a 16.0 MW ST_CHP bin — exactly the plant's `38 + 38.8 + 12 + 12`). **58 of 61
   rows are full-year 2025**, which is itself a signal worth a successor's attention. A
   by-product: the row routes to one group only, so at 54518/50846 the **CT_CHP bin is not
   zeroed** even though the plant is declared net-zero — an under-removal on the other side.
2. **An extract/fleet UNIT-SET mismatch.** In 23 of 55 steam bins the two sides do not
   agree on which units are in the bin: the extract carries units the fleet does not model
   (1702 has 4 extract units against 2 fleet units; 6190, 8056, 4042, 992 likewise),
   boiler-vs-generator grain (55096 `BLR1`/`BLR2` against fleet `ST`), and naming
   conventions (990 CAMPD `50`/`60`/`70` against EIA `5`/`6`/`7`). This is why the
   all-or-nothing rule refuses 30 % of steam capacity, and it is the largest un-adjudicated
   object this session leaves behind.

## 4. The mechanism

`ScenarioConfig.unit_outage_st_capacity_basis` — GATED, default off, byte-inert off,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` **in the same commit as the field** (the
nyiso-119 / caiso-186 discipline, so it cannot repeat the caiso-184 / nyiso-128 failure of
moving the pinned default key; `tests/unit/config` 652 passed, 0 failed).

**All-or-nothing per bin.** Aligned only when every extract unit resolves 1-1 onto a
distinct fleet unit, by exact normalised id, an unambiguous trailing-digit hit, or a unique
1-1 **residual** pairing that is *forced, not chosen* (which is what resolves 1403, whose
CAMPD unit `4` cannot match EIA generator `6(4)` on digits). Any unresolved unit, any
collision, or any synthetic row leaves the **whole bin** on the production basis: a
half-aligned bin is less coherent than either basis alone, so partial application is
refused rather than counted.

**Scope, measured rather than assumed.** Shared by the std ≥5-day, short and partial
layers **and by the lay-up loader**, whose contract is that a lay-up share and an outage
share for the same plant "sit on the same basis and are additive" — aligning one and not
the other would break exactly that invariant (rule 19 `[R-ONE-MECH]`). **The maxgen layer
is out of scope BY CONSTRUCTION and this is not the same question as miso-200's**: the
routing repair had to move both layers because a unit routed to *different bins* is
incoherent, but a numerator **basis** is per-layer, and maxgen's rows carry a measured
`derate_mw` — a partial MW reduction, not a unit capacity — so a `pmax` substitution there
would swap a capacity for a derate. That exclusion is documented at the call site.

24 unit tests on a **synthetic** fleet and extract, so a change to the committed MISO
extract can never quietly turn one green.

## 5. The A/B

Control `2026-09-02-miso-201-control` vs arm `2026-09-02-miso-201-stbasis`, both MISO
2023+2024+2025 in one invocation, years sequential, in-session (rules 12/16), both from the
same committed keeper recipe via `--replay-bundle`. Scorer `_miso201_ab_gates.py`
**committed blind with the PREREG before the mechanism existed**.

| gate | result |
|---|---|
| S-0 control integrity | **PASS — BIT-IDENTICAL**, 9 sidecars, `max_abs_diff` 0.0 |
| S-1 single delta | PASS — exactly `unit_outage_st_capacity_basis` |
| S-2 liveness | PASS |
| **K-1 C1 band** | **SILENT — no band exit anywhere** |
| K-2 C3b | silent |
| **K-3 D-4 conduct** | **KILL FIRED** — one cell |
| K-4 D-1 shape | silent (cv_ratio marginally better) |
| K-5 status flips | silent |
| K-6 DOF | **PASS, and REAL** — not vacuous |

**K-1, the pre-registered risk, in full.** Every named cell moved as predicted:

| class-year | keeper | arm | reading |
|---|---:|---:|---|
| ST_GAS-2023 | −3.834 | **−3.512** | toward actual |
| ST_GAS-2024 | −7.854 | **−7.488** | toward actual; the tightest cell on the board moves **away** from the −8.00 edge |
| ST_GAS-2025 | −6.862 | **−6.681** | toward actual |
| CC_REGULAR-2024 | +7.075 | **+6.931** | toward zero |
| CC_REGULAR-2023 | −3.319 | −3.434 | **named adverse risk** — moved adversely, 4.57 TWh of headroom left |
| COAL_PRB-2025 | −4.865 | −4.904 | **named adverse risk** — 3.10 TWh left |

The capability bound was rigorous and the LP converted **36 / 40 / 26 %** of it
(+0.561 / +0.782 / +0.363 TWh of ST_GAS energy).

**Determination UNCHANGED** at NOT-YET on `price_mean` alone, with C3c the single ledgered
caveat and C6 attested (ledger **40 / 2**, `n_residual` unchanged).

## 6. Reported against the promotion, at full magnitude

**(a) THE FROZEN K-3 KILL FIRED AND IS NOT RENEGOTIATED.** One cell:
`(2023, unit-conduct, reliability_floor × ST_GAS, plant 1122)`, pass → **FAIL**. Both
halves of the D-4 row are stated because they cut in opposite directions:

| | control | arm |
|---|---:|---:|
| binding hours | 10 | **2** |
| floored TWh | 0.0001 | **0.0000** |
| off-window share | 0.0362 | **0.0041** |
| measured zero share | 0.20 | **1.00** |
| verdict | pass | **FAIL** |

The arm **reduced** that floor's binding by 80 % and its forced energy to zero, and the
off-window share fell by an order of magnitude. It FAILs because the 2 surviving binding
hours are hours the plant's own meter reads zero, so the conduct ratio trips on a two-hour
denominator. **That is a real miss on a check this session's own PREREG made a kill**, and
the scorer does not promote on that branch — the promotion is the owner's standing bar,
not the scorer's.

**(b) C8 MOVES THE WRONG WAY, SLIGHTLY — the opposite of miso-200's gain.** ST_GAS forced
share **0.1496 / 0.1520 / 0.2651 → 0.1551 / 0.1529 / 0.2713** (+0.5 / +0.1 / +0.6 pp), all
still well inside the 0.30 merchant budget. The mechanism is honest about why: restoring
availability gives the must-run floor more capacity to assert on, so a basis repair that is
right on its own terms can raise forced share. It is reported, not explained away.

**(c) C3a GETS SLIGHTLY WORSE**, and is reported and **never** the justification (rule 1
`[R-STRUCT]`): 2023 +0.2740 → +0.1218, 2024 −4.3653 → −4.5820, 2025 −12.2745 → −12.3845.
The keeper's sole failing criterion moves against us, so nothing here can be read as
C3a-driven.

**(d) THE ARM'S FIRST SOLVE CRASHED ON THIS SESSION'S OWN PLUMBING**, after completing all
three years: the new field's override was written into `_recorded_config` in the
solve-path style, so `run_config.json` was never written. The bug was fixed and the arm
re-solved, and the re-solve is **BIT-IDENTICAL to the crashed run across all 18 hourly
sidecars** (`max_abs_diff` 0.0) — which is what establishes that the fix is confined to
config recording and that **both legs remain one code state**. Disclosed rather than
quietly re-run.

**(e) THE SCORER'S OWN K-6 READ WAS WRONG ON THE FIRST TWO PASSES.** It looked for a
top-level `entries` key while the attestation nests its ledger under `free_parameters`, so
K-6 reported UNSCORED on bundles that carried a full ledger. Fixed — and the fix corrects
what the gate can **see**, it does not move the gate: K-6 still counts UNSCORED as
never-a-pass.

**(f) The phase-0 L-3a soundness line did NOT fire**, and the way it did not is a result.
Every residual aligned-overflow cell (170, 1104, 2070, 6639) is **100 % explained by
same-unit window overlap** — the adjacent-window boundary-day double-count FINDING-miso200
§8 item 2 already names. The alignment therefore **isolates that defect as the only
remaining steam overflow**, which is exactly what makes it the named successor.

## 7. Handed on

1. **THE ADJACENT-WINDOW BOUNDARY-DAY DOUBLE-COUNT — now isolated and the clear successor.**
   With the numerator aligned it is the *only* mechanism still producing steam overflow, at
   four measured bins (170, 1104, 2070, 6639). A deriver/overlay defect under the
   `[start, end + 1 day)` reconstruction; small (24–72 h/yr per bin) but no longer masked.
2. **THE EXTRACT/FLEET UNIT-SET MISMATCH** — the largest un-adjudicated object here, and
   what caps this repair at 69.6 % of steam capacity. 23 of 55 steam bins. Three distinct
   sub-causes (over-scoped extract, boiler-vs-generator grain, naming conventions) which
   probably need three different answers.
3. **THE `eia923_netzero` WHOLE-PLANT LAY-UP FAMILY** — a plant-level numerator against a
   per-group denominator, 58 of 61 rows full-year 2025 (a vintage-completeness signal), and
   a one-sided routing that leaves the CT_CHP half of a declared-net-zero plant un-zeroed.
4. **THE MAXGEN LAYER'S OWN BASIS QUESTION** — its `derate_mw` is CEMS-gross against a
   net-summer denominator. Named, deliberately not inherited, and NOT the same repair.
5. **The K-3 cell itself**: a conduct ratio on a 2-hour denominator is a fragile test.
   Whether D-4 should carry a minimum-binding-hours floor is a rubric question, not a
   calibration one, and it is raised rather than assumed.
6. Unchanged from miso-199/200: floor fragmentation; the `D4_WINDOWS` "self-windowing by
   construction" wording (self-**sizing**, not self-**placing**); the lay-up census
   cycler/mothball boundary; `CT_CHP` as the visible half of the steam-host family;
   `ST_CHP`'s CEMS invisibility; the standing wind +5 TWh/yr over EIA-930; the 2023 import
   +2.0 TWh face; the committed extract's provenance drift (`outage_artifact_provenance`);
   and **the bid-side self-schedule form, still open, still unadjudicated, cell not minted**.

## 8. Governance

Attestation by `scripts/gen_miso201_attestation.py` on the gen_miso186/187/188/198/200
pattern — one appended MEASURED entry, **n_entries 40, n_residual UNCHANGED at 2**;
`build_dof_ledger.py` deliberately NOT run on it. Diagnostics **and** attestations were
generated for **both** legs *before* the pair was scored, and the scorer **refuses** to
score K-3/K-4/K-6 on empty inputs — the miso-200 vacuous-pass trap closed in advance rather
than discovered after the fact. Keeper shard, `status/MISO.js`, the matrix shard keeper
stamp, the `unit_outage_st_capacity_basis` cell (O → K) and the §5.4 prose header all
re-stamped this session (rule 28b); the base matrix row plus a cell in all six shards
landed with the field (rule 28c). Rule 25: only MISO's files were touched. MISO holds no
`complete` marker, so the rule-22 D-5(b) re-key does not apply. Rule 22: 2023–2025 only.

Next shorthand: **miso-202**.
