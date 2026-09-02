# PRECOMMIT — caiso-239: the caiso-238 object-2 ST_GAS committed band, MEASURED AT ITS TRUE LOCATION

**Registered 2026-09-02, session caiso-239. Branch
`claude/caiso-st-gas-committed-sce4lq`, cut from `origin/main` (`3a2239ba`).
PUSHED BEFORE ANY SOLVE. No LP has been built and no solver called in this
session.**

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`** (bundle
`results/calibration/caiso231_b1_ungrounded`), determination **NOT-YET**, **C3a
the SOLE load-bearing FAIL** (+4.1 % 2023 PASS / +12.5 / +15.6 %); C1 12/12 free
8/8; C3b PASS; C3c the single ledgered caveat (standing rule, non-downgrading);
C6 attested; C8 PASS. CAISO holds **no `complete` and no `final` marker**; the
holdout spend freeze is **ACTIVE**. Every read and every solve in this session
stays inside **2023–2025**.

---

## §0 — WHAT THIS SESSION IS, AND THE DISCLOSURE THAT CONDITIONS IT

**§0.1 — The object is caiso-238 object 2, the CAISO ST_GAS `committed` band.**
It is a rule-14 `[R-ACCURATE]` / rule-21 `[R-DOF]` **structural-integrity**
repair on the caiso-231 model, **NOT a C3a lever**. Per rule 1 `[R-STRUCT]` and
the caiso-238 charter §0.3, **no conclusion in this session is argued from the
price residual**, in either direction. The owner's standing standard applies:
*structural integrity improving while a gate regresses may still be a keeper*
(caiso-231's own promotion basis).

**§0.2 — FULL DISCLOSURE: THE MEASUREMENT WAS TAKEN BEFORE THIS FILE WAS
PUSHED, AND IT FALSIFIED THE CHARTER'S PREMISE.** This is the caiso-238 §0.6
pattern, and it is stated first because it changes what this precommit can
honestly pre-register. The handoff directed a choice between two values for
`offer_curve_by_group["ST_GAS"]["committed"]` and instructed that the measured
inputs *not* be re-derived, citing
`results/calibration/_caiso238_grounding_charter.json`. **That artifact does not
exist**: caiso-238 pushed only its PRECOMMIT (`6b7e6492`, PR #4625); its
`ASSESSMENT-…md`, its probe and its JSON were never committed. The §3 charter I
was told to read as my whole brief therefore had to be reconstructed from
primary sources, and reconstructing it established that **the charter's
premises about which units the scalar prices are false**. §1 records exactly
what was measured, how, and what it overturns; §2 registers the design decision
that follows; **§3's bound and §5's gates are pre-registered against the
un-solved arm and no solve has been run.**

**§0.3 — HARD STOPS.** Training window only (2023 / 2024 / 2025), all three in
one invocation and one bundle (rule 16 `[R-ALLYEARS]`), years sequential (rule
12 `[R-PARALLEL]`). No `calibration-complete.json`, `holdout-freeze.json`,
keeper shard or other ISO's file is touched except as §7 names. No P2. No
off-registry knob (rule 24 `[R-REGISTRY]`). Nothing armed outside CAISO (rule 25
`[R-ISO-SCOPE]`).

**§0.4 — DO-NOT-REDO acknowledged (rule 28(a)).** Not re-opened here: the
measured **BID** committed multipliers (CC 1.030 / CT 1.166) for any CAISO gas
class — the Lever-A refusal stands uniformly (rule 19 `[R-ONE-MECH]`), and the
object below is the **PHYSICAL** basis, a different object, deliberately not
merged with it; the `offer_curve_by_group` census; CAISO `pct_peaking` as a
grounding object; `band_windows_geometry.econ_low_share` and `CT_PEAKER`
`pct_peaking` as measurements; whether `offer_curve_smoothing_exp = 1.0` is an
identity; the whole caiso-229 / 230 / 233 / 234 / 235 / 224 / 221 closure list;
the W-1/W-2/W-3 sweep, which is **DATED** to the Order-881 AAR effective date
(≤ 2026-12-01) and is **not swept here**.

**§0.5 — PROCESS DEVIATION, DECLARED: NO CONTROL ARM.** The handoff asks for
"control + arm" and a G-CTRL that reproduces the keeper to the cent. That is
**superseded by the standing owner directive recorded at caiso-231**
(`docs/calibration-log/caiso.md`, 2026-09-01, verbatim: *"that's one in like
1000 runs that have been done so I don't care and I don't want to measure
drift"*; **binding going forward: a single-delta calibration arm is solved ONCE
and scored against the committed keeper**). This session therefore solves **one
arm** and scores it against `caiso231_b1_ungrounded`'s committed metrics.
G-CTRL is re-specified in §5 as a **source-diff** assurance — the route the
directive itself prescribes — not as a spent LP run.

---

## §1 — THE MEASUREMENT, AND WHAT IT FALSIFIES

Probe: `scripts/probes/_caiso239_st_gas_committed_footprint.py`, output
`results/calibration/_caiso239_st_gas_committed_footprint.json`. **Zero solves**:
the marginal-rung attribution and the §H bounding form are imported UNCHANGED
from `_caiso230_abovefloor_decomposition.py` and **re-pointed at the caiso-231
keeper**, as caiso-231's DO-NOT-REDO requires. The footprint is established by
REBUILDING the keeper's offer surface at three band values
(`run_year(fleet_only=True)` — assembles the fleet and the P0 objective, builds
no matrix, calls no solver) and diffing `mc_base` row by row.

**F-1 — THE SCALAR DOES NOT PRICE THE THREE OTC STEAMERS. It prices 2 of the
keeper's 25 ST_GAS LP tranches, and neither is one of them.** In all three years
the tranches of plants **315 (AES Alamitos), 335 (AES Huntington Beach) and 350
(Ormond Beach)** are **byte-identical** at `committed` ∈ {0.81, 1.00, 1.683}
(max |Δmc| = 0.0). The cause is in the code, not the data:
`offer_curves.py::_offer_curve_for_group` returns **`None`** for
`group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS`, and
`data/outages.py::ST_GAS_PEAKER_PLANTS` names **315, 335 and 350 explicitly**
("the last once-through-cooling steamers, kept on OTC compliance extensions as
RMR-style reliability units"). With `offer is None`, `assembly.py::bins_to_fleet`
never reaches `committed_hr = base_hr × offer["committed"]` and the three
steamers take the class defaults instead —
`campd_bins.py::_DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]` = **{mr 1.10, mc 1.15,
econ 1.00, peak 1.10}**. Verified arithmetically: p315 base HR 11.850 →
committed 13.63 = 11.850 × **1.15**, econ 11.85 = × **1.00**, peak 13.04 =
× **1.10**, all three exact.

**F-2 — the two tranches it DOES price are EIA-860 retired-window units, and by
2025 BOTH are at zero availability.**

| plant | identity | zone | committed pmax | avail 2023 / 2024 / 2025 |
|---|---|---|--:|---|
| 356 | **AES Redondo Beach LLC** (`eia860_generator_retired_within_window`) | LA_BASIN | 249.0 MW | 0.813 / **0.000** / **0.000** |
| 10446 | **SEGS IX** (Terra-Gen; EIA-860 status `RE`, "Natural Gas Steam Turbine" — the auxiliary boiler of a retired solar-trough plant) | ZP26 | 26.4 MW | 0.764 / 0.631 / **0.000** |

**In 2025 — the keeper's WORST C3a year — the object is completely dead**: both
responsive tranches carry zero available capacity in all 8,760 hours, so every
candidate value is provably byte-identical there.

**F-3 — the measured counterpart is measured on the DISJOINT population.**
`caiso_campd_marginal_hr_summary.csv` reports ST_GAS `n_units = 10`, and
`campd_gas_commitment_params_CAISO_units.csv` shows those ten units are
**entirely plants 315 / 335 / 350** (Alamitos 3, 4, 5, CT1, CT2; Huntington
Beach 2, CT1, CT2; Ormond Beach 1, 2). So `avg_committed_p50 = 1.683` is
measured on **exactly the three plants the band does not price**, and arming it
on the band would apply an OTC-steamer statistic to a retired Redondo Beach and
a retired SEGS auxiliary boiler **while leaving the units it was measured on
untouched**. That is rule 14 `[R-ACCURATE]`'s own stated exception — *"the data
is defined on a different boundary than our representation"* — in its exact
form.

**F-4 — AGAINST INTEREST: the handoff's inversion premise is also false for the
steamers at the RESOLVED offer level.** On the keeper as built (2024 mean mc,
$/MWh) p315 is committed **69.19** > peak **68.92** > econ **62.38**; p335
68.96 / 68.69 / 62.15; p350 82.84 / 82.57 / 76.03. The three steamers' min-load
band is already their **dearest** band, not their cheapest. The inversion is
real only for the two retired units the scalar actually reaches (2023 p356:
committed 151.40 vs econ 178.60).

**F-5 — the measured value's own quality, disclosed.** ST_GAS is the only CAISO
class whose `avg_committed` distribution is not tight: p25 **0.682** / p50
**1.683** / p75 **3.275**, ratio **4.80**, against 1.12–1.27 for CC_CHP,
CC_REGULAR, CT_CHP and CT_PEAKER. The spread is real physical bimodality, not
noise: the pooled ten units split into six steam units at LSL **7.6–10.0 %** of
HSL and four colocated CTs at **22.0–28.2 %**, and a lower LSL means a far
higher min-load block-average burn. **This cuts in the repair's favour and is
recorded as such:** the model's `_committed` tranche for these plants is sized
**6.3–9.3 %** of nameplate (`Pct_Committed`, `Committed_Source: campd`), i.e. it
is the **steam** min-load block, whose own statistic sits near p75, so the class
p50 of 1.683 is a **conservative** choice for the tranche it would price, not an
arbitrary one.

---

## §2 — THE DESIGN DECISION, FIXED HERE, BEFORE ANY SOLVE

**§2.1 — On the chartered scalar `offer_curve_by_group["ST_GAS"]["committed"] =
0.81`: NEITHER 1.00 NOR 1.683. REFUSED — on measurement, not on C3a.** Three
independent grounds, each sufficient: **scope** (F-1 — 2 of 25 tranches, no OTC
steamer among them); **liveness** (F-2 — both responsive plants are retired-window
units, both dead in 2025); **population mismatch** (F-3 — the measured value is
measured on the plants the scalar excludes). This is the **fifth outcome** the
caiso-238 charter pre-registered for its own objects — **MIS-CLASSIFIED at
caiso-236**, which recorded the row as "live and material". It is live in the
narrow sense (two tranches move) and it is **not material**, and neither candidate
value is admissible on it. **Arming either would be a rule-13 violation dressed
as a rule-14 repair.**

**§2.2 — The repair is RELOCATED to the scalar that actually prices CAISO's
ST_GAS committed band: `_DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"] = 1.15`.**
This is the same phenomenon — the CAISO ST_GAS `committed` band — at its true
location. The value is an **uncited ERCOT-lineage class literal in a `data/`
module**, invisible to `run_config.json`, to the DOF ledger's
`offer_curve_by_group` count, to caiso-230 §H, to caiso-231's re-grounding and
to the caiso-236 audit — a rule-24 `[R-REGISTRY]` off-registry channel and a
rule-25 `[R-ISO-SCOPE]` exposure on 2,858.8 MW of SP15 capacity. It is replaced
by **`avg_committed_p50 = 1.683`**, CAISO's own CAMPD measurement of **exactly
the ten units of exactly the three plants this band prices**. Population and
statistic coincide; zero free parameters are added; the substitution is
measured-for-estimate in rule 14's plain sense.

**Why not 1.00 here either.** 1.00 is not measured. It is a third unidentified
number, it retires nothing under rule 21 `[R-DOF]`, and — reported against
interest — it would not even achieve its own Lever-A rationale, since on the
caiso-231 keeper the relevant comparator is the **measured** econ band, not the
0.95 Lever A was set against. The only reason to prefer it is that it moves C3a
less, which §0.1 forbids as a criterion.

**Why 1.683 and not the measured BID 1.166.** They are different objects. 1.166
is the CT bucket's measured **offer** conduct and is withheld by the adjudicated
Lever-A / rule-19 refusal, uniformly, for every CAISO gas class. 1.683 is the
**physical min-load block-average burn** of these plants' own units. This session
does not touch the bid side.

**Registered against interest:** the relocation is a **judgement call the owner
can reverse**. The charter funded object 2 as posed; I am reading "the ST_GAS
committed band" as the phenomenon rather than as the specific dictionary key,
because acting on the key while leaving the scalar that does the work untouched
would repair nothing. If the owner reads the funding narrowly, the correct
outcome is §2.1 alone — a refusal with no arm and no run.

---

## §3 — THE ADVERSE DIRECTION, DECLARED BEFORE THE ARM SOLVES

**Direction is ADVERSE.** Raising the committed band raises the min-load offer of
these plants in the hours they are marginal, i.e. **UP** on a C3a that is already
over in 2024 and 2025. Per rule 1 `[R-STRUCT]` this is **not an argument against
the repair** — it is what goes on the record first.

First-order bound, caiso-230 §H form re-run on **this** keeper
(`|Δλ| ≤ Σ ω·p_z·|Δmult/mult|` over the zone-hours where the tranche is the
marginal rung, annualised on the scorer's own zone-hour load-weighted basis). It
is a strict **upper** bound: the multiplier scales only the fuel component, and
in an LP the margin moves to the next-cheapest rung (caiso-231 measured the same
bound over-predicting by 4–13×).

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **THE ARM** — relocated band 1.15 → 1.683 (**+46.3 %**) | **+0.0003** | **+0.0265** | **+0.0000** |
| *(refused)* chartered band 0.81 → 1.683 (+107.8 %) | +0.1812 | +0.2054 | +0.0000 |
| *(refused)* chartered band 0.81 → 1.00 (+23.5 %) | +0.0394 | +0.0447 | +0.0000 |
| C3a required move (scorer basis, caiso-230 §E) | 0.00 | −0.848 | −1.893 |

The arm's bound is **+0.0265 $/MWh at its largest**, 3.1 % of 2024's required
move and **zero** in 2025. Registered prediction: **measured C3a moves ≤ the
bound in every year, no year flips verdict, 2023 stays PASS.**

---

## §4 — WHAT IS BUILT

`ScenarioConfig.caiso_st_gas_committed_measured: bool = False` — gated,
**default off**, **CAISO-only** (armed on any other ISO is a hard `ValueError`,
never a silent no-op — rule 25). When armed, an ST_GAS bin whose
`_offer_curve_for_group` resolves to `None` (i.e. a `ST_GAS_PEAKER_PLANTS`
member) takes `committed_hr = base_hr × ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO[iso]`
instead of the `_DEFAULT_HR_MULT_BY_GROUP` class literal. The constant lives in
`constants.py` with its citation (`caiso_campd_marginal_hr_summary.csv`,
`avg_committed_p50`, n = 10 units = plants 315/335/350). **Exactly one band
moves**; `mr` / `econ` / `peak` are untouched; every other ISO and every other
class is byte-identical armed or not. Threaded onto `--replay-bundle` on the
established single-delta pattern (`caiso_offer_surface_measured_ungrounded`,
`unit_outage_mixed_gas_routing`, `campd_per_unit_attribution`), so the arm is
provably the recipe plus one flag. Rule 28(c): the matrix base row plus a cell
line in **every** ISO shard land in the same PR.

**DOF, stated honestly and NOT overclaimed.** The retired literal
(`_DEFAULT_HR_MULT_BY_GROUP`) is **not counted** by
`build_dof_ledger._count_scalars`, which reads `offer_curve_by_group` only, so
**`n_residual` stays 6 and the ledger will not move.** The handoff's "6 → 5" is
**not achievable by this repair, nor by the chartered one** — caiso-231 hit the
identical gate-specification defect and disclosed it rather than dropping it.
The structural claim is verified on the resolved fleet instead (G-STRUCT).

---

## §5 — GATES, EACH WITH ITS FALSIFIER

* **G-CTRL** *(re-specified per §0.5 — source diff, no control solve)*: the arm's
  `run_config.json` reproduces the keeper's recipe in every field except the one
  new flag. **Falsifier:** any second field differs.
* **G-STRUCT**: on the rebuilt fleet, **exactly** the three OTC steamers'
  `_committed` tranches change heat rate (11.850 × 1.15 → × 1.683; p350 11.845);
  **0** other ST_GAS tranches, **0** non-ST_GAS tranches, **0** other bands
  (`mr` / `econ` / `peak`) move. **Falsifier:** any other tranche or band moves.
* **G-INERT**: the arm is **not** byte-identical to the keeper — the mechanism
  must actually do something. **Falsifier:** identical annual metrics in all
  three years.
* **G-C3a**: measured |ΔC3a| ≤ the §3 bound in every year; **no year flips
  verdict; 2023 stays PASS**. **Falsifier:** any year flips, or a move exceeding
  the bound (a bound violation is a defect in the estimator or the mechanism,
  reported as such, never re-fitted).
* **G-C1**: 12/12, free 8/8, unchanged. **Falsifier:** any C1 criterion regresses.
* **G-C3b**: PASS, with the 2025 composition-watch tripwire (margin 0.019 at
  caiso-231) explicitly re-read. **Falsifier:** C3b fails, or 2025 crosses.
* **G-C8**: PASS — no material class over its forced-energy budget.
  **Falsifier:** any material class crosses.
* **G-CAVEAT**: the ledgered-caveat budget stays 1 of 1 (C3c alone).
  **Falsifier:** a second ledgered or any protective caveat appears.

**Promotion rule, fixed in advance:** the arm is proposed as keeper **only if**
G-STRUCT, G-INERT, G-C1, G-C3b, G-C8 and G-CAVEAT all pass and G-C3a shows no
verdict flip. A C3a regression **within** the bound does not block promotion
(caiso-231's governing precedent); a verdict flip does.

---

## §6 — DELIVERABLES

1. This PRECOMMIT, pushed to `origin` **before the solve**.
2. `scripts/probes/_caiso239_st_gas_committed_footprint.py` +
   `results/calibration/_caiso239_st_gas_committed_footprint.json` (already
   produced; zero solves).
3. The mechanism (§4) with unit tests, its `constants.py` citation, its
   `--replay-bundle` thread, and its mechanism-matrix base row + a cell line in
   every ISO shard (rule 28(c)).
4. ONE arm — `--replay-bundle results/calibration/caiso231_b1_ungrounded
   --caiso-st-gas-committed-measured --year 2023 2024 2025` — solved sequentially
   in one invocation, one bundle (rules 12 / 16), registered on the backcast
   dashboard in **this** session whether keeper or rejected probe (rule 15).
5. `FINDING-caiso239-st-gas-committed-relocation-2026-09-02.md` with the §3
   prediction and the §2 decision **scored against interest**.
6. The `docs/calibration-log/caiso.md` caiso-239 entry; the CAISO matrix cell
   updated whatever the outcome (rule 28(b)).
7. The carried repair to `tests/unit/results/test_cache_config_agreement.py`
   (`len(groups) == 15` → `assertGreaterEqual(..., 14)`; the two refused keys
   left exact), which this session's registration would otherwise turn red.
