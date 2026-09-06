# FINDING nyiso-202 — the bridge run screen ALONE clears its 2025 screen on every pre-registered gate, and the span it earns is **promoted**: forcing at dark-meter plants falls **0.5963 → 0.2336 TWh** across 2023–2025 with **zero criterion flips** and the determination unchanged at **CALIBRATED, grade 7/8, fails 0**

**Session:** nyiso-202 (`claude/nyiso-202-backcast-calibration-3xdzby`), 2026-09-06.
**Keeper at open:** `2026-09-06-nyiso-196-extract-basis`.
**KEEPER AT CLOSE: `2026-09-06-nyiso-202-startup-aware`** — CALIBRATED, grade 7 of 8, fails 0,
C3c the lone ledgered caveat.
**Control:** the keeper's committed bundle (rule 29(b) form 4; G-DRIFT §2.2, empirical at this HEAD).
**Pre-registration:** `results/calibration/PREREG-nyiso202-bridge-startup-aware-2025-screen.md`,
pushed with **ZERO solves**; its Addendum A records the screen **before the span was launched**.
**Machine records:** `results/calibration/_nyiso202_screen_gates_a1_2025.json` (every screen number)
and the span bundle's computed `calibration_attestation.json` (every governance number).
**TWO LPs spent:** one rule-29 screen (2025, ~7 min, **deleted before merge** per 29(c)) and one
span (`--year 2023 2024 2025`, one invocation, one bundle, registered).

---

## 1. The result in one paragraph

nyiso-201 handed forward one live candidate — `nyiso_gas_bridge_startup_aware` **alone**, whose 2025
screen had never been spent — and it clears. **Every pre-registered gate passes** (§3), including
both of the constructions nyiso-201 corrected, and the arm is the one of the three fields with no
price-lowering signature: C3a-2025 moves **−6.9 % → −6.3 %**. The span it earns reads
**CALIBRATED, grade 7 of 8, fails 0, C3c the lone ledgered caveat — identical to the superseded
keeper's headline, with zero criterion flips in either direction** (§4). The promotion therefore
rests entirely on the structural half, and that half is measured and large (§5): **dark-meter forced
energy 0.5963 → 0.2336 TWh** over the span, with Astoria 8906's 0.3436 TWh 2024 conviction —
forcing at a plant whose measured median over its own binding hours is 0.0 MW — **eliminated**; C8
forced share falls on **every** class-year; and `CC_REGULAR` moves toward its actual in both scored
years. The regressions are reported at full magnitude and none is a flip (§6): `CC_CHP` is the away
class **and was named in the PREREG before the span was solved**, and **C3b-2024 at 0.185 against
≤0.20 is the tightest remaining margin in the model**. One thing is reported rather than buried
(§7): the D-4 failure-**row count** rises 5 → 6 while the forcing it purports to measure falls 61 %
— exactly the attribution artifact nyiso-201 §7(4) established, and the new row is itself the
object §8 hands forward.

## 2. What was fixed before the LP, and what was not re-derived

**2.1 Phase 0 was inherited, not re-run** (rule 29's DO-NOT-REDO discipline). A1's 2023 screen is
nyiso-200's and was not re-solved; the three-way pairing is refuted on both of its pre-registered
years and was not re-screened; the measured-conduct eligibility gate stays REFUSED (rule 13,
nyiso-144's 7314 ruling) and was not built; the NYC persistent-base **membership** question stays
closed negative (nyiso-201 §5) and no per-plant list was typed. The one number this session needed
before the solve — the arm's own 2025 reachability bound, **0.5701 TWh** — is read from
`_nyiso200_bridge_phase0.json`.

**2.2 G-DRIFT, empirical, not hunk-reading.** The committed keeper-sha probe record
`_nyiso198_rebuild_checks_2024.json` (per-plant / per-band LP `pmax`, 42 leaves) re-run at this HEAD
reproduces **0 of 42 differing leaves, max |Δ| 0.0**, its own `VERDICT` field included — the
regenerated file is **byte-identical** to the committed one (`git status` clean after the re-run).
Form 4 is valid; **no control solve was spent**. The attestation's G-CONTROL adds the independent
check that the keeper's committed bundle on disk equals `origin/main`: **0 of 52,560 hourly zonal
prices differ in each of the three years**.

**2.3 The ONE gate that had to change, and it is a narrowing.** nyiso-201's S-1 reads *"`CT_PEAKER`
must RISE, inside the CT band's newly-in-the-money bound"* — the **CT arm's** arithmetic, which has
no subject in an arm that does not arm the CT band. S-1 was re-pointed to this arm's own arithmetic
(the run screen can only *remove* anchors): **the bridge's D-2 forced volume must NOT RISE, and its
fall must sit inside the keeper's own 0.5701 TWh**. That is nyiso-200's own A1 gate
(`S1_direction_bound`), reused verbatim, together with its A1 companions `S2_census_identity` and
`S3_confinement`. `diff` over `nyiso202_screen_gates.py` against `nyiso201_screen_gates.py` shows
**only** that block plus the session/output labels: gate (a), gate (b), the load-bearing companions
and G-ENGAGE run byte-identical. **No solve-path code was changed by this session at all** — the
per-plant census that makes gate (b) falsifiable landed at HEAD in nyiso-201.

## 3. The screen — every gate, as pre-registered, on 2025

Arm: `nyiso_gas_bridge_startup_aware` alone over the keeper recipe, 2025, one LP. **G-DOF +0.**
2025's scoring was declared ex ante (PREREG §0.6): every C1 class cell and the C2 gas family are
SKIPPED on the preliminary EIA-923 vintage, so **no volume criterion is gateable there** and gate
(d) is vacuous on volume; C3a and C3b are what bind.

| gate | reading | verdict |
|---|---|---|
| **S-1** direction / bound *(re-pointed, §2.3)* | bridge D-2 volume **0.5701 → 0.1434 TWh**, a fall of 0.4267 inside the 0.5701 bound; does not rise | **pass** |
| **S-2** census identity | 19-plant per-plant census present; keeper bundle slim, so reported not gated | pass |
| **S-3** confinement | gas family **−0.026 TWh**, import **+0.023**; **no** non-gas non-import class moves > 0.005 TWh at all | **pass** |
| **(a)** dark-meter forced energy *(nyiso-201's correction)* | keeper **0.0010** → screen **0.0010 TWh**, **Δ 0.0000**; the one dark plant (8006) unmoved; D-2 adds no failure; the screen's only D-4 failure is the keeper's own 2025 8006 row | **pass** |
| **(b)** named plants 7314 / 50978 *(nyiso-201's correction)* | 7314 **977 unit-h / 19.617 GWh**, census 347 detected / **134 kept** / 213 dropped; 50978 **228 unit-h / 9.011 GWh**, census 66 / **40 kept** / 26 — reported at full magnitude; no floor with zero kept runs; no D-4 conviction at either (both `ct_only`-restored by the span guard) | **pass** |
| **(c)** C3a / C3b do-no-harm | C3a **−6.9 % → −6.3 %** PASS → PASS; C3b 0.154 → 0.154 PASS → PASS. System mean 58.86 → 59.293, p95 125.52 → 126.18, hours > $300 unchanged at 4 | **pass** |
| **(d)** no load-bearing flip | zero C1 flips, zero C2 flips — **vacuous on volume in 2025**, as declared | pass (vacuous) |
| **G-ENGAGE** | `gas_cc` **939 of 1,554** P0 runs dropped (4,561 h, 13 units), `gas_cc_state` **95 of 164** (365 h, 3 units), `gas_st` **386 of 508** (17,984 h, 7 units) | **pass** |

**VERDICT: CLEAR.** The span was then solved under PREREG §6.

**A determinism check worth recording:** the span's own 2023 census reproduces nyiso-200's A1-2023
numbers **exactly** (1,173 of 1,576 CC runs dropped), and its 2025 bridge totals reproduce this
session's screen exactly (29,019 unit-hours, 4.93 TWh floor volume). The arm is deterministic at
this HEAD.

## 4. The span's determination — identical headline, zero flips

**`2026-09-06-nyiso-202-startup-aware`: CALIBRATED, grade 7 of 8, fails 0, 1 ledgered caveat**
(C3c price tail, 3 / 1 / 4 h vs 10 / 13 / 42 h > $300 — the owner's standing accepted model-class
limitation, rubric v3.3 non-downgrading). C1 all 14/14, free 10/10; C2 / C3a / C3b / C4 / C6 / C8
PASS. **Not one criterion changes status in either direction** against the superseded keeper. The
governance gate C6 passes on a computed attestation whose every premise is derived from the bundles
and the repo: **G-DELTA exactly `{nyiso_gas_bridge_startup_aware: False → True}`** (with
`cc_duct_peaking_row_scoped` and `nyiso_ct_peaker_bands_measured` both recorded **False** — the two
refuted partners are not armed), **G-DOF +0** (13 entries / n_residual 6, verbatim from the keeper's
ledger), G-INPUTS pinning `COMMITMENT_PARAMS_BY_FUEL` to show the screen's bar is an **existing**
registered constant, G-CONTROL form 4, G-ENGAGE on two independent witnesses (the census lines and
the per-year bridge-volume fall inside each year's own bound).

## 5. Why it is promoted: the structural half, measured

The mechanism repairs what rule 17 `[R-FLOOR-WINDOW]` calls a bug by definition — a floor binding in
hours its own driver evidence says the unit is off. A detected P0 run now anchors a bridge leg only
when that run's own P0 margin per MW repays the unit's published startup cost, `_ra_bridge_unit_params`,
**the same constant the economic leg already prices**. Nothing is selected, swept or tuned; the
field is a bool; no `offer_curve_by_group` multiplier and no `phys_*` value moves, so rule 1's
price-tuning carve-out is not invoked.

**Dark-meter forced energy** — nyiso-200 §7(a)'s like-for-like measure, never a failure-row count:

| year | keeper | arm | |
|---|---|---|---|
| 2023 | 0.2515 (2480 0.0014 · **8906 0.2501**) | 0.2296 (2480 0.0014 · 8906 0.2282) | fall |
| 2024 | 0.3438 (2480 0.0002 · **8906 0.3436**) | **0.0030** (2480 0.0002 · 54574 0.0028) | **8906 leaves the dark set entirely** |
| 2025 | 0.0010 (8006) | 0.0010 (8006) | unchanged |
| **span** | **0.5963** | **0.2336** | **−61 %** |

**C8 forced share falls on every class-year**: `CC_REGULAR` 2.8 / 0.8 / 1.2 → **1.1 / 0.3 / 0.4 %**;
`ST_GAS` 16.6 / 22.4 / 18.2 → **15.5 / 19.9 / 17.2 %**. **C1 `CC_REGULAR`** moves toward its actual
in both scored years: +0.83 → **+0.37** TWh (2023), +3.01 → **+2.39** (2024). C4 improves slightly
(2024 r 0.896 → 0.898; 2025 0.839 → 0.840).

## 6. The regressions, at full magnitude — none a flip, all inside band

| criterion | 2023 | 2024 | 2025 | band |
|---|---|---|---|---|
| C1 **`CC_CHP`** *(the away class, named ex ante)* | +0.95 → **+1.18** | +2.31 → **+2.65** (share +1.9 → +2.1 pp) | skipped | ±3 pp |
| C1 `ST_CHP` | +0.17 → +0.21 | +0.21 → +0.29 | skipped | ±3 pp |
| C1 `ST_GAS` | +1.81 → +1.92 | −1.17 → **−1.12** (toward) | skipped | ±3 pp |
| C3a mean LMP | +4.6 → **+5.7 %** | +4.7 → **+6.5 %** | −6.9 → **−6.3 %** (toward) | ±10 % |
| C3b price shape | 0.119 → 0.124 | **0.175 → 0.185** | 0.154 → **0.152** (toward) | ≤0.20 |

**`CC_CHP` was named in the PREREG §6 before the span was solved**, from A1-2023's own committed
numbers, precisely so no post-hoc reading could present it as a discovered detail; it is the away
class in both scored years, exactly as predicted. **C3b-2024 at 0.185 is the tightest remaining
margin in the model** — 0.015 of room where the superseded keeper had 0.025 — and it is the first
thing a successor lane should watch. Rule 1 governs the reading in both directions: the arm is not
promoted *because* C3a-2025 improved, and it is not refused *because* C3a-2023/2024 moved outward
inside a band they never leave.

## 7. Reported and not hidden: the failure-row count rises while the forcing falls

The D-4 failure-**row** count goes **5 → 6** across the span while dark-meter forcing falls 61 %.
That is not a contradiction; it is the artifact nyiso-201 §7(4) established, seen a second time.
Concretely at Astoria 8906 in 2023: the bridge row shrinks **0.0463 → 0.0011 TWh** and the
`reliability_floor` row beneath it — previously below the rider's threshold because the bridge row
carried the conviction — **now convicts at 0.2271 TWh**. The plant's **total** forced energy is
0.2501 → **0.2282**, a *fall*. Removing the higher of two composed floors at a plant the lower one
also floors re-attributes the conviction downward; a count measures attribution, forcing does not.
**D-2 (the production C8 path) adds no failure and C8 PASSES.** The other row that appears, 2024
`nyiso_gas_commitment_bridge` × 54574 at 0.0028 TWh, replaces 8906's 0.3436 TWh — a 99.2 % reduction
that the count records as "no change".

## 8. Handed forward

1. **The NYC persistent-base reliability limb's BASIS is now the top object, and this session made
   it sharper.** With the bridge floor gone at 8906 that limb is the plant's **sole remaining
   forcer**, and it is what draws the new 2023 D-4 row at 0.2271 TWh. nyiso-201 §5.3 already named
   the object and closed its **membership** question negative (8906 is 0 of 18 zero-cells, pooled
   median 166 MW, online 66.7 %; never type a per-plant list): the open question is nyiso-140's
   Long_Island analysis repeated for NYC — whether a **fleet-aggregate** when-available cool-day CF
   p25, applied **per unit** `pro_rata` in all 8,760 hours at `floor_pct` 0.175, is the right basis
   for a fleet spanning 0.667–0.956 online. Source data only (rule 23), never a residual, zero LP up
   to the A/B.
2. **Watch C3b-2024.** 0.185 against ≤0.20 is the model's tightest margin. Any future arm that
   touches price shape in 2024 should measure it on a screen before a span is spent.
3. **`CC_CHP` is the standing away class** (+2.65 TWh / +2.1 pp in 2024). nyiso-197 already
   re-specified a large part of it as an **offer-position** object at Linden 50006 (+20.6 % / +21.0 %
   over the Gold Book Table III-2a net energy), filed to the owner court; that remains where the
   class's over-run should be worked, not in the bridge.
4. **The two refuted partners stay `R` and are not armed on this keeper.** Both of the three-way
   pairing's pre-registered screen years are spent; re-arming either alone still needs an owner
   ruling.
5. **Method, for every lane (rule 25 respected — this is method, not a verdict transfer):** where
   two mechanisms floor one plant and compose by maximum, a D-4 **failure-row count** is not a
   forcing measure. `nyiso202_screen_gates.dark_plant_forced` (inherited verbatim from nyiso-201,
   which verified it reproduces nyiso-200 §5.1's published 0.2515 TWh exactly) is the like-for-like
   one, and the attestation's `B1_DARK_FORCING` block now carries both side by side per year so the
   difference is visible in the committed record.

## 9. Disposition

**KEEPER: `2026-09-06-nyiso-202-startup-aware`** (bundle `results/calibration/nyiso202_startup_aware`),
promoted under the owner's standing formula carried verbatim into this lane's PREREG (*"Is this a
recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper.."*) on rules 17 `[R-FLOOR-WINDOW]` + 19 `[R-ONE-MECH]` + 1 `[R-STRUCT]`.
Registered on the dashboard, keeper shard and status page rebuilt, NYISO matrix shard and prose
header re-stamped, `audit_keepers --iso NYISO` PASS, registry/payload parity OK, the superseded
`nyiso-198` run pruned under rule 15's keeper-only retention. **`complete` is NOT re-declared:**
NYISO sits in `calibration-complete.json`'s `withdrawn` block and re-entry is a NEW owner
declaration, so no D-5(b) re-key is owed and no holdout year was touched — 2023–2025 only, as rule
22 requires. **The screen bundle is deleted before merge (29(c));** every number it produced lives
in `_nyiso202_screen_gates_a1_2025.json` and in this document, and git history is the record for the
bytes.

---

*(nyiso-202, 2026-09-06. Two solves: one rule-29 screen (deleted) and one registered span. Keeper
promoted: `2026-09-06-nyiso-196-extract-basis` → `2026-09-06-nyiso-202-startup-aware`.)*
