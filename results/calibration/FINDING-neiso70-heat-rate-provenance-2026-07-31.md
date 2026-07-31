# FINDING — neiso-70: two measured heat-rate arms off one same-HEAD control

**Pre-registration:** `results/calibration/PREREG-neiso70-heat-rate-provenance-2026-07-31.md`,
committed at `20ce479` and pushed **before either arm solved**. Every gate,
threshold and prediction below was fixed in advance; none was revised after a
number was seen.

| | |
|---|---|
| Session | neiso-70 |
| Lane | rule 14 `[R-ACCURATE]` input accuracy — **not** C3c scarcity work |
| Outgoing keeper | `2026-07-23-neiso-61-netrev-margin` (CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat) |
| **Outcome** | **`measured_ct_heat_rates` PROMOTED** → new keeper `2026-07-31-neiso-70-ctheatrate` (`K`). **`measured_chp_heat_rates` NOT promoted, cell `O` (open)** — live and accurate, but it overshoots because NEISO's CC_CHP has no host-steam floor (§6). |
| Bundles (one frozen sha `22cf8fb`) | `neiso70_control_A`, `neiso70_ctheatrate_B`, `neiso70_chpheatrate_B` |
| Runs | `2026-07-31-neiso-70-control`, `-ctheatrate`, `-chpheatrate` |
| Years | 2023 2024 2025, one invocation each (rule 16 `[R-ALLYEARS]`) |

Only my session's probe/doc files changed between the three solves — `src/`
was never touched — so all three bundles carry the same solve code.

---

## §1 — the artifacts (STEP 1, pre-solve)

Both derived at HEAD, `--iso NEISO`, **zero fitted parameters**, per rule 25
`[R-ISO-SCOPE]` on NEISO's own data: no verdict and no parameter was imported
from CAISO, PJM, NYISO or MISO.

### Lever 1 — `campd_ct_heat_rates_NEISO.csv` (CT_PEAKER)

* **8 plant rows, 8 applied (`flag == "ok"`), ZERO excluded by the physical
  band**; 17 per-unit detail rows.
* **Coverage 910 / 1,204 MW = 75.6 % of class capacity, but 100.0 % of the
  class's own metered CAMPD CT energy** (1.458 / 1.458 TWh).
* Exclusions all carry **zero** metered CT energy: 28 plants / 115.2 MW below
  the Part-75 boundary (mostly fuel cells, median 2.5 MW) and one 178.0 MW
  plant (Bucksport Generation) with a CAMPD account but no combustion-turbine
  unit.
* **Adverse selection PRESENT and stated, not waved away:** covered cap-wt
  incumbent HR **10.208** vs uncovered **11.830** (+1.621 MMBtu/MWh) — the
  uncovered set is dearer on paper, driven by Bucksport (178 MW at 13.24) and
  the fuel-cell rows carrying the 9.000 default. This **differs from CAISO**
  (10.819 vs 11.004, effectively neutral). Mitigated but not erased by the
  energy basis: nothing metered is left unswapped.
* **Direction — NEISO's own: TWO-SIDED with a net-cheaper tilt.** 6 plants /
  817 MW cheaper, **2 plants / 94 MW dearer**; cap-wt **−0.579 MMBtu/MWh
  (−5.7 %)**, gen-wt −0.889; ratio min 0.826 / median 1.038 / max 1.170.
  Two-directional like NYISO/PJM, net-cheaper like CAISO but about **half**
  CAISO's size, and the opposite sign to PJM's net +0.229. **No precedent ISO's
  pattern was assumed or reused.**
* Thin rows disclosed in advance: A L Pierce 154 loaded hours (one of the two
  dearer rows, +1.203); MMWEC 51 hours, at the committed ≥ 50 floor (−0.179).
  The screen is the committed one and was not re-tuned (rule 23).

### Lever 2 — `chp_power_only_heat_rates_NEISO.csv` (CC_CHP / CT_CHP)

* **40 (plant, class) rows, 12 applied**; excluded: `not_unfired_topping` 22,
  `no_egrid_row` 5, `basis_mismatch` 1.
* **CC_CHP 3/7 rows, 378 / 494 MW (76.6 %) and 99.5 % of the class's own
  metered CAMPD energy** (6.965 / 7.001 TWh) — strong reach.
* **CT_CHP 9/33 rows, 52 / 267 MW (19.3 %) and 0.0 % of metered energy**
  (0.000 / 0.328 TWh): every covered CT_CHP plant sits below the Part-75
  boundary, so none of them meters. **Thin AND zero metered reach — stated as a
  limitation, never claimed as identification.**
* **CEMS validation 4/4 covered plants within 1 %, median ratio 1.00000.**
* Selection is the EPA-envelope gate working as designed, and it *is* selection:
  CC_CHP covered credited 6.964 (thermal_share 0.266) vs excluded 2.632 (0.527);
  CT_CHP covered 8.699 (0.227) vs excluded 5.338 (0.629). The 22
  `not_unfired_topping` rows (247 MW, thermal_share median 0.633 vs the 0.50 EPA
  ceiling) would otherwise have taken a median 14.56 / max 23.6 MMBtu/MWh rate.
* **Direction — NEISO's own: ONE-SIDED DEARER in BOTH classes.** CC_CHP cap-wt
  **6.964 → 9.521 (+36.7 %)**, CT_CHP **8.701 → 11.515 (+32.3 %)**, **12 dearer
  / 0 cheaper**. This is the MISO "uniformly under" picture and **the opposite
  of CAISO**, whose two classes moved in opposite directions.

---

## §2 — flag fidelity: the ERCOT-146 hazard, discharged BEFORE any solve

ERCOT-146 stamped `measured_ct_heat_rates` **`I`** with **no solve spent**: its
consumer is `eia860._rows_to_generators`, but under `use_campd_bins` ERCOT's
thermal fleet comes from the curated `load_campd_bins` sheet, which never
receives the kwarg — so an A/B would have been bit-identical.

**The NEISO keeper runs the same `use_campd_bins=True` /
`plant_level_fleet=True` configuration**, so the question had to be asked here.
It takes the *other* branch: in `assembly.load_or_synthesize_bins` only
`iso == "ERCOT"` reads the curated sheet, and every other ISO **synthesizes**
its bins from `load_fleet_from_csv(..., measured_ct_heat_rates=…,
measured_chp_heat_rates=…)`; `build_base_fleet` passes both flags again on the
non-thermal leg. Verified empirically at the keeper's own ScenarioConfig
(`scripts/probes/_neiso70_flag_fidelity.py`, no LP):

| arm | generators moved | MW moved | class cap-wt HR at the LP seam |
|---|---|---|---|
| `measured_ct_heat_rates` | 31 / 1,166 | 910.4 | CT_PEAKER 13.7959 → 13.2196 (**−4.18 %**) |
| `measured_chp_heat_rates` | 20 / 1,166 | 271.0 | CC_CHP 8.1437 → 10.4210 (**+27.96 %**), CT_CHP 6.2962 → 6.7784 (**+7.66 %**) |

**Both LIVE.** NEISO is not ERCOT-146, and both solves were justified.

---

## §3 — the named risk for lever 2, resolved from the keeper's own diagnostics

NEISO's C1 scorecard lists `CC_CHP`/`CT_CHP`/`ST_CHP` in `pinned_classes` and
`CC_CHP`/`ST_CHP` in `excluded_from_free`. Had those classes been **pinned in
the LP**, a re-price would move nothing — a variable held at a floor is a
constant in the objective, and (the ERCOT-64 result) **a pinned variable cannot
price**.

**"Pinned" here is the scorer-side D-10 label, not an LP pin.**
`free_class_score` excludes classes whose dispatch is pinned to a measured
realization so their C1 pass is not counted as skill. The keeper's own D-2:

| class | forced mechanism | share of class energy 2023 / 2024 / 2025 |
|---|---|---|
| **CC_CHP** | **none — no D-2 row in any year** | **0 % / 0 % / 0 %** |
| CT_CHP | `chp_steam` | 2.84 % / 5.24 % / 5.55 % |

**CC_CHP is 100 % free in the LP** and CT_CHP is 94–97 % free, so the re-price
acts directly on dispatch. (NEISO differs sharply from CAISO, where CC_CHP's
`chp_steam` forced share was 0.435–0.470.)

What the label *does* cost — pre-registered, and it is a scoring limit, not a
dispatch one: `CC_CHP` is `excluded_from_free` and `CT_CHP` is not a scored C1
row at all, so **lever 2 cannot improve the free-class score by construction**.
Its C1 evidence is the all-class row plus the D-1 shape diagnostics, and it is
reported that way rather than dressed up as a free-class gain.

---

## §4 — the control, and why it was mandatory

The keeper's `meta.json` records `git_sha` `eede1c4`, and **that commit is not
in the repo** (squash-merged away), so keeper-relative deltas charge
unattributable code drift to the mechanism. neiso-69 caught exactly this: its
true 2024/2025 mechanism delta was *exactly* 0.0 for every class while the
keeper-relative comparison showed CT_PEAKER −189.7 GWh and CC_REGULAR
+145.8 GWh — 100 % drift.

**G-2 control integrity — PASSES on the scorecard basis.** Placing a
ledger-carrying attestation on the control makes it score
**CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat (C3c), C1 all 12/12 ·
free 8/8** — *exactly* the keeper's determination structure. (Without an
attestation every probe bundle reads `NOT-YET / governance UNATTESTED` and C3c
degrades from CAVEAT to a raw FAIL, because a caveat can only be *ledgered* by
an attestation. That is a scoring artifact of probe bundles, not drift, and it
applies identically to control and both arms.)

**DRIFT vs the committed keeper — reported as its own finding, not a failed
gate.** Class-hour maxima:

| year | max abs Δ | largest classes |
|---|---|---|
| 2023 | 912.9 MW | CC_REGULAR 912.9, hydro 553.0, oil 528.1, CT_PEAKER 338.0 |
| 2024 | 963.9 MW | CC_REGULAR 963.9, hydro 707.4, oil 589.6, CT_PEAKER 345.8 |
| 2025 | 1,029.0 MW | CC_REGULAR 1,029.0, hydro 907.0, oil 746.7, CT_PEAKER 315.0 |

Annual class TWh drift includes CC_CHP **+0.077 / +0.076 / +0.051** and
CT_PEAKER **−0.048 / −0.090 / −0.190**. The numerics stack also differs from the
keeper's recorded environment (highspy 1.14.0 vs 1.15.1, pandas 3.0.3 vs 3.0.5,
pyarrow 24.0.0 vs 25.0.0 — the repo's committed `requirements.txt` pin is older
than the stack the keeper was solved with), so the drift is **code + environment
and cannot be decomposed further with `eede1c4` gone**. This is precisely why a
same-HEAD control was solved rather than differencing against the keeper.

---

## §5 — LEVER 1 result: `measured_ct_heat_rates`

All figures **arm − control**, never arm − committed keeper.

### Pre-registered gates

| gate | result |
|---|---|
| G-1 flag fidelity | **PASS** — arm records the flag `true`, control records both `false` |
| G-2 control integrity | **PASS** (scorecard basis, §4) |
| G-3 liveness (> 50 MW) | **PASS** — max \|Δ CT_PEAKER MW\| **257.9 / 269.5 / 288.0** |
| G-4 single delta | **PASS** — exactly one differing ScenarioConfig field |
| G-5 year span | **PASS** — `[2023, 2024, 2025]` in every bundle |

### Dispatch (P1, TWh)

| year | CT_PEAKER | CC_REGULAR | total gen |
|---|---|---|---|
| 2023 | 0.183 → **0.309** (+0.126) | 51.877 → 51.756 (−0.121) | −0.004 |
| 2024 | 0.362 → **0.832** (+0.470) | 56.264 → 55.803 (−0.461) | −0.005 |
| 2025 | 1.098 → **1.706** (+0.608) | 58.337 → 57.718 (−0.619) | −0.006 |

A pure reallocation: total generation moves ≈ 0.005 % — **prediction P3
confirmed**. Mean λ −0.078 / −0.177 / −0.297 $/MWh (cheaper CTs displace dearer
CC at the margin).

### Criterion verdicts — every one IDENTICAL to the control

`fuelmix` PASS · `sysvol` PASS · `price_mean` PASS · `price_shape` PASS ·
`price_tail` (see §4) · `dispatch_corr` PASS · `shape` SKIPPED ·
`forced_share` PASS. **No flips in either direction**, and C1 stays
**all 12/12 · free 8/8**. **C3c is BIT-IDENTICAL** — model 0 tail hours in both
arms, all three years (RT actual 15 / 8 / 20 h). The frontier-declared C3c
family is untouched, exactly as scoped.

### C1 accuracy — improves in **both scored years**

2025's C1 rows are `SKIPPED` (preliminary EIA-923, 57 % plant reporting,
2.382 TWh vintage gap), so C1 scores 2023 + 2024 only.

| year | actual | control | arm | \|error\| control → arm |
|---|---|---|---|---|
| 2023 | 0.466 | 0.184 (0.39×) | 0.310 (0.67×) | 0.282 → **0.156** |
| 2024 | 0.655 | 0.363 (0.55×) | 0.832 (1.27×) | 0.292 → **0.177** |
| 2025 *(unscored)* | 0.619 | 1.099 (1.78×) | 1.706 (2.76×) | 0.480 → 1.087 |

**Prediction P1 confirmed** (CT_PEAKER rises) and beneficial where it is scored.
2024 crosses from under to over, but its absolute error still shrinks. **2025
moves further over — disclosed in the prereg in advance, against interest**, and
its C1 row is unscored against an incomplete actual.

### The structural result — this is the real deliverable

**D-2 CT_PEAKER `reliability_floor` forced share collapses:**

| year | control | arm |
|---|---|---|
| 2023 | 0.3958 | **0.2013** |
| 2024 | 0.2735 | **0.0736** |
| 2025 | 0.0680 | **0.0272** |

Correctly priced, the class **clears economically instead of leaning on its
commitment floor** — the floor stops being load-bearing. This is the MISO-107
result *in reverse* (there, arming the same mechanism made MISO's CT floor more
load-bearing because CTs had been carrying combined-cycle heat rates). It is a
rule-1 `[R-STRUCT]` improvement in mechanism faithfulness, independent of fit.

### Reported, not gated

**2025 CT_PEAKER D-1 `cv_ratio` 0.521 → 0.288**, below the 0.50 D-1 threshold.
This is **not** a broken protective gate: **C7 `shape` is `SKIPPED` for NEISO**
in keeper, control and arm alike, so the prereg's kill condition ("a protective
gate breaks *where the control passed*") is not met. `profile_r` moves
0.930 → 0.965 (2023), 0.982 → 0.976 (2024), 0.976 → 0.976 (2025), all far above
the 0.80 floor. C8 `forced_share` PASSES in both arms; CT_PEAKER is 0.19–1.0 %
of ISO load, under rule 20's 2 % materiality line, so its D-2 share is a
reported diagnostic rather than a gate. The `cv_ratio` move is disclosed here
because it is the one number that moved adversely on the repriced class.

CC_REGULAR gives up 0.121 / 0.461 / 0.619 TWh to fund the CT rise; its own C1
absolute error worsens slightly in the two scored years (0.471 → 0.596 in 2023,
0.340 → 0.801 in 2024) while improving in 2025 (2.527 → 1.908). Every row stays
comfortably inside the ±1.94 / ±2.08 TWh tolerance and PASSES.

---

## §6 — LEVER 2 result: `measured_chp_heat_rates` — verdict `O` (open)

### Pre-registered gates — all PASS

| gate | result |
|---|---|
| G-1 flag fidelity | **PASS** |
| G-2 control integrity | **PASS** (shared control, §4) |
| G-3 liveness (> 50 MW) | **PASS** — max \|Δ CC_CHP/CT_CHP MW\| **204.6** |
| G-4 single delta | **PASS** |
| G-5 year span | **PASS** |

**Nothing in the prereg's KILL list is triggered:** zero criterion regressions
across all 70 scored records, C1 stays all 12/12 · free 8/8, C3c
**bit-identical** (model 0 tail hours), C7 `shape` SKIPPED and C8
`forced_share` PASS in both arms, no protective caveat opened.

### Dispatch (P1, TWh)

| year | CC_CHP | CC_REGULAR | CT_CHP | total gen |
|---|---|---|---|---|
| 2023 | 1.334 → **0.741** (−0.593) | 51.877 → 52.503 (+0.626) | 0.493 → 0.460 (−0.032) | +0.003 |
| 2024 | 1.292 → **0.948** (−0.344) | 56.264 → 56.633 (+0.369) | 0.513 → 0.481 (−0.032) | +0.001 |
| 2025 | 1.216 → **0.539** (−0.677) | 58.337 → 59.041 (+0.704) | 0.482 → 0.451 (−0.031) | +0.002 |

**Prediction P2 is directionally CONFIRMED** — dearer CHP ⇒ CC_CHP falls, energy
lands on CC_REGULAR, total generation ≈ 0. Mean λ rises +0.157 / +0.111 / +0.309
$/MWh.

### But it OVERSHOOTS the class it reprices — this is why it is not promoted

| year | actual | control | arm | \|error\| control → arm |
|---|---|---|---|---|
| 2023 | 1.072 | 1.296 (1.21×) | 0.703 (0.66×) | 0.224 → **0.369** |
| 2024 | 1.124 | 1.254 (1.12×) | 0.910 (0.81×) | 0.130 → **0.214** |
| 2025 *(unscored)* | 1.194 | 1.216 (1.02×) | 0.539 (0.45×) | 0.022 → **0.655** |

CC_CHP crosses from *over*-generating to *under*-generating in every year. Note
the counterweight, reported in full: **CC_REGULAR improves markedly** —
0.471 → 0.156 (2023) and 0.340 → 0.030 (2024) — so the *combined* CC_CHP +
CC_REGULAR absolute error actually falls in both scored years (0.695 → 0.525 and
0.470 → 0.244). The displaced energy lands almost exactly on actual.

### Root cause, located: NEISO's CC_CHP carries NO host-steam floor

This is the deliverable of lever 2, and it is a structural finding rather than a
tuning one:

* **CC_CHP has no `chp_steam` D-2 row at all** in NEISO — in the control *and*
  the arm, all three years. CT_CHP has one (2.9 % → 3.3 %, 5.3 % → 5.9 %,
  5.8 % → 6.3 %); CC_CHP has **zero**. CAISO's CC_CHP `chp_steam` forced share,
  by contrast, runs **43–47 %**.
* So when the CC_CHP offer becomes **+27.96 %** dearer at the LP seam, **nothing
  holds those cogens to their host-steam obligation** and they drop out far
  past what a real cogen — which must run to serve its host's steam — would.
* The dispatch signature confirms it: CC_CHP's D-1 **`cv_ratio` explodes**
  2.814 → 6.99, 6.499 → 10.231, 2.156 → 11.248, while **`profile_r` barely
  moves** (0.919 → 0.908, 0.815 → 0.831, 0.852 → 0.860). The *timing* stays
  right; the *amplitude* blows out. That is exactly an unconstrained unit
  cycling on price instead of running to an obligation.

**The mechanism is structurally INCOMPLETE as armed**, in the ERCOT-141 sense:
it implements the accurate offer without the companion obligation floor. The
input is not refuted — eGRID's own published CHP allocation is more accurate
than the steam-credited rate, CEMS validates it 4/4 within 1 %, and **rule 14
`[R-ACCURATE]` forbids reverting to the estimate because it fits better**. What
is missing is NEISO's `chp_steam` floor.

### Verdict and disposition

Matrix cell **`O` (open)** — deliberately not `K`, `R` or `I`:

* not **`K`**: the fit on the repriced class degrades, which per prereg §6
  blocks *promotion* (never the *input*);
* not **`R`**: nothing was refuted on the merits — the artifact is accurate and
  CEMS-validated;
* not **`I`**: it is demonstrably live (204.6 MW, −0.34 to −0.68 TWh).

The flag stays **default-off**. The named successor is **neiso-71**: derive a
measured NEISO CC_CHP host-steam floor (the `chp_steam` mechanism the ISO
currently lacks for this class) and **land the two together** — an accurate
offer and its obligation floor are one mechanism, and arming either alone is
half of it (rule 19 `[R-ONE-MECH]`).

**Reported, not gated:** CT_CHP's D-1 `profile_r` is 0.0 / −0.264 / 0.0 in
control and arm alike — a pre-existing degenerate shape on a class that is
0.4–0.5 % of load and ungated, untouched by this arm. Also carried forward from
§1: the CT_CHP artifact leg covers 19.3 % of capacity and **0.0 % of metered
energy**, so lever 2's CT_CHP half is not identified at all and must not be
cited as evidence in either direction.

---

## §7 — DOF ledger (rule 21 `[R-DOF]`)

**Zero free parameters added by either arm.** Both are measured swaps of a
published estimate for a measured value on the same basis:

* Lever 1 — CAMPD unit-level hourly `grossLoad`/`heatInput` over the loaded
  window, converted to a NET basis by the **committed** parasitic-factor map
  (the same map the benchmark's net actual uses), so the derived rate and the
  actual it is scored against share one gross-to-net convention. Screen
  constants (0.8 × p95, ≥ 50 loaded hours, band [6.0, 25.0]) are the committed
  shipped values, unchanged.
* Lever 2 — eGRID's own published `(PLHTIAN + CHPCHTI) / PLNGENAN` on the same
  net denominator, so no gross-to-net factor is involved; the 0.50 thermal-share
  ceiling is the EPA CHP Partnership unfired gas-turbine envelope.

Neither was swept against a residual. Per rule 23 `[R-FROZEN-DERIVE]` both
re-derive **only** when their source data updates, and any such commit must cite
the data change.

---

## §8 — governance

* Rule 22 `[R-HOLDOUT]`: years 2023–2025 only. The holdout spend freeze is
  **ACTIVE** and outranks every marker; NEISO's locked test is already **SPENT**
  (2026-07-07) and never re-grantable. No out-of-training year was solved,
  scored or touched.
* Rule 15 `[R-DASHBOARD]`: all three bundles registered, arms and control alike.
* Rule 28 `[R-MECH-MATRIX]`: both cells updated in this session with their
  evidence citations.
* Scope held: §5.6 items 1, 2 (charter required), 4 (NG:PS time split) and 5
  (owner decision pending) were not opened, and C3c was not targeted.
