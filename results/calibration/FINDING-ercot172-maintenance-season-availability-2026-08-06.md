# FINDING — ercot-172: the 2024 maintenance-season defect is **real capability the overlays removed**, not phantom capability the model carries. The event-cap ceiling is measurably BELOW the physical CEMS record at 8 of 9 named plants, and the instrument it overrides — the 60-Day DAM COP — is the one that tracks reality.

**Session ercot-172, 2026-08-06. PHASE 0 — no LP, no solve, no
`ScenarioConfig` field written, no mechanism armed, no cell verdict flipped,
keeper UNCHANGED at `2026-08-05-run168b-year-curves`.** Decision rule
pre-registered, committed and pushed **before** any capture ran
(`docs/PRECOMMIT-ercot172-maintenance-season-availability-2026-08-06.md`); no
bar, band, floor or window moved after measurement.

## 0. Verdict

**ACTIONABLE** (precommit §4 branch 3) — every pre-registered gate passes, and
the object is attributed to **nine named plants at MW grain**.

| gate | bar | h2827 (Apr 28) | h3067 (May 8) | |
|---|---|---|---|---|
| G-FOOT | ≥0.99 within 1e-3 | **1.0000** (35,128 class-hours, max Δ 5.03e-5) | — | PASS |
| G-EXACT | 0 violating rows | **0** | **0** | PASS |
| G-SEAM | max abs Δ = 0 | **0.0** over 600 out-of-scope rows | — | PASS |
| L1 COP-resolvable | ≥ 0.90 | **1.0000** | **1.0000** | PASS |
| L2 ambiguous | ≤ 0.10 | **0.0000** | **0.0000** | PASS |
| `E ≥ shed` | ≥ 1.00× | **8.58×** (4,847.9 vs 565.1 MW) | **3.15×** (1,731.8 vs 550.3 MW) | PASS |
| `E_named / E` | ≥ 0.60 | **1.0000** (9 plants) | **1.0000** (6 plants) | PASS |
| P-ERR | ≥ 0.60 | **1.0000** | | PASS (weak — see §5) |

**No mechanism is built or armed.** Per the precommit, branch 3 authorises this
session to *specify* the correction and its kill gates only; building it needs an
explicit owner adjudication that was not taken. §4 specifies it; §6 records what
is **not** claimed.

## 1. Calendar correction — the object's days were mislabelled repo-wide

The true dates are **2024-04-28** and **2024-05-08**, not the "Apr 27 / May 7"
carried by `FINDING-ercot166` §5 and the `ercot_dam_availability_gas_event_cap`
matrix note. Verified against the primary source
(`data/raw/lmp-data/RTMLZHBSPP_2024.zip`, `HB_HUBAVG`): April's top day is
**2024-04-28**, day-mean **$126.86**, peak hour **$1,259.83**; May's is
**2024-05-08**, **$345.99** / **$3,048.98** — the same $1,260 / $3,049 the
ercot-149 note itself quotes. The one-day-early labels are a **naive-leap-index
artifact**: an 8760-long index built on a 2024 calendar without dropping Feb 29
relabels every hour after Feb 28 one day early. **The hours and prices in those
records are correct; only the printed date labels are off by one.** Peak
prevailing **HE21 = 19:00–20:00 CST**, so the model's error hour and ERCOT's
event hour are the same hour. This matters because every instrument lookup in
this session is keyed on the calendar date.

## 2. The object — two hours, both at VOLL, both load-shed

The keeper's **only two 2024 shed hours** are the object, exactly:

| model hour | timestamp (CST) | shed MW | model $/MWh | actual RT $/MWh |
|---|---|---|---|---|
| 2827 | 2024-04-28 19:00 | **565.1** | 5,015.9 | 1,259.83 |
| 3067 | 2024-05-08 19:00 | **550.3** | 5,000.0 | 3,048.98 |

Shed census: 2023 → 4 (Jun/Aug, scarcity season), **2024 → 2**, 2025 → 0.
Day-mean price error **+375.0** and **+227.3** $/MWh on a year MAE of 13.04.
Both days are **real ERCOT tight evenings the model over-amplifies into a
shortage** — the model prices at the cap and sheds firm load where the measured
settlement record peaks at $1,260 / $3,049. *(That ERCOT itself did not shed is
inferred from the settlement record — no sustained cap-priced interval — not read
from an EEA log; the verified statement is the model-vs-measured price gap.)*

## 3. The attribution — MW grain, and which instrument disagrees with which

`E = A_pin − A_final` is the capability the event cap removed, exact by
construction (the cap is a pure `np.minimum`; G-EXACT and G-SEAM confirm the
toggle isolates it). `f_ceiling = f_window × f_partial` is the ceiling it
imposes; `f_COP` is the 60-Day DAM COP declaration it overrides; `f_CEMS` is the
plant's own fuel-matched gross output **in that hour**, a hard physical floor on
what it was able to produce.

**h2827 — 2024-04-28 19:00 CST, shed 565.1 MW**

| plant | name | class | E MW | f_window | f_partial | **f_ceiling** | f_COP | **f_CEMS** | ceiling < physical |
|---|---|---|---|---|---|---|---|---|---|
| 3470 | W A Parish | COAL | 1,177.5 | 0.6995 | 0.3630 | **0.2539** | 0.7359 | **0.7843** | **YES** |
| 3612 | V H Braunig | ST_GAS | 1,108.0 | 0.0264 | 1.0000 | **0.0264** | 1.0000 | **0.5343** | **YES** |
| 6146 | Martin Lake | COAL | 778.8 | 0.6667 | 0.5020 | **0.3347** | 0.6619 | **0.6547** | **YES** |
| 55153 | Guadalupe | CC_REGULAR | 744.4 | 0.4999 | 0.4820 | **0.2410** | 0.9250 | **0.4650** | **YES** |
| 55230 | Jack County | CC_REGULAR | 491.7 | 0.5000 | 1.0000 | **0.5000** | 0.8841 | **0.9344** | **YES** |
| 55168 | Bastrop | CC_REGULAR | 256.2 | 0.4909 | 1.0000 | **0.4909** | 0.9049 | **0.9067** | **YES** |
| 7097 | J K Spruce | COAL | 192.8 | 0.3802 | 0.2080 | **0.0791** | 0.2086 | **0.1968** | **YES** |
| 7900 | Sand Hill | CC_REGULAR | 51.4 | 0.9262 | 1.0000 | 0.9262 | 1.0000 | 0.7352 | no |
| 56611 | Sandy Creek | COAL | 47.2 | 1.0000 | 0.4850 | **0.4850** | 0.5354 | **0.5684** | **YES** |
| | **TOTAL** | | **4,847.9** | | | | | | **8 / 9** |

**h3067 — 2024-05-08 19:00 CST, shed 550.3 MW**

| plant | name | class | E MW | f_window | f_partial | **f_ceiling** | f_COP | **f_CEMS** | ceiling < physical |
|---|---|---|---|---|---|---|---|---|---|
| 3612 | V H Braunig | ST_GAS | 883.0 | 0.2241 | 1.0000 | **0.2241** | 1.0000 | **0.6406** | **YES** |
| 6146 | Martin Lake | COAL | 353.3 | 0.3333 | 0.5020 | **0.1673** | 0.3158 | **0.3576** | **YES** |
| 3601 | Sim Gideon | ST_GAS | 256.7 | 0.5634 | 1.0000 | 0.5634 | 0.9754 | 0.5377 | no |
| 7900 | Sand Hill | CC_REGULAR | 102.8 | 0.8524 | 1.0000 | 0.8524 | 1.0000 | 0.6720 | no |
| 3470 | W A Parish | COAL | 88.9 | 0.6995 | 1.0000 | **0.6995** | 0.7359 | **0.7941** | **YES** |
| 56611 | Sandy Creek | COAL | 47.2 | 1.0000 | 0.4850 | **0.4850** | 0.5354 | **0.5491** | **YES** |
| | **TOTAL** | | **1,731.8** | | | | | | **4 / 6** |

**The direct answer to the chartered question.** The model is **not** carrying
phantom capability out; it is **removing real capability, and the removal is
refuted by the very instrument whose authority it claims**:

* **Impossible MW** — fuel-matched CEMS gross **above the model's entire
  available envelope** — is **3,945.7 MW (6.98× the shed)** at h2827 and
  **1,218.0 MW (2.21× the shed)** at h3067. These plants were *generating* while
  the model held them unavailable.
* **Both certificates are TRUE for every named plant** — K-COP **9/9** and
  **6/6** (the QSE filed live HSL), K-CEMS **9/9** and **6/6** (the plant
  demonstrably operated the same fortnight). Not one plant in the object is a
  case of the model correctly holding capacity out.
* **The overridden instrument is the accurate one.** At 6 of the 9 plants
  `f_COP` tracks `f_CEMS` to within a few points — W A Parish 0.7359 vs 0.7843,
  Martin Lake 0.6619 vs 0.6547, J K Spruce 0.2086 vs 0.1968, Bastrop 0.9049 vs
  0.9067, Jack County 0.8841 vs 0.9344, Sandy Creek 0.5354 vs 0.5684 — while
  `f_ceiling` misses by up to 0.53 (W A Parish 0.2539 vs 0.7843).

**The rating-basis term `R` is not the object** (precommit §2, measured and
reported): total **+563.5 MW** at h2827 and **+161.1 MW** at h3067, large but
offsetting per class (CT_PEAKER +2,869 / +3,048; CC_REGULAR −1,406 / −1,641;
ST_GAS −850 / −1,057). A material per-class `R` re-points to the fleet-scope /
crosswalk lane (item 11); it is not acted on here.

## 4. The mechanism of the defect, and the correction it specifies

The ceiling the event cap enforces is the **product of two measured layers**
(`fleet/arrays.py` `_evcap_scope` block):

* **`f_window`** — `unit_outage_derate_factors`, at **(plant_code, plant_group)**
  grain: `1 − Σ(unit_capacity / plant_capacity)` over ≥5-day full-stop windows.
* **`f_partial`** — `partial_outage_derate_factors`, at **plant grain only**, a
  **multi-week FLAT plateau** (W A Parish carries a single `derate_factor 0.363`
  spanning 2024-03-04 → 2024-05-04; Martin Lake 0.502 over 04-10 → 06-06; J K
  Spruce 0.208 over 04-24 → 05-04; Guadalupe 0.482; Sandy Creek 0.485).

Three faults compound, and all three are visible in the tables above:

1. **Double-count (rule 19 `[R-ONE-MECH]`).** Both layers are derived from the
   same CEMS record and both remove the same units' downtime; multiplying them
   removes it twice. W A Parish: 0.6995 × 0.3630 = 0.2539, against a plant that
   ran at 0.7843 of its coal `pmax` that hour.
2. **Grain mismatch.** `partial_outage_derate_factors` returns a dict keyed by
   `oris_code` **only** — the extract's own `plant_group` column is read and
   discarded — so one facility-wide plateau is applied to every class bin of that
   plant. `_unit_outage_target` deliberately splits W A Parish's units into
   `(3470, COAL)` and `(34702, ST_GAS)` for the *window* layer; the *partial*
   layer has no such split, so the facility-wide plateau lands on the coal bin.
   *(The window extract's own `plant_group=COAL` labels on the gas units WAP1–4
   are a CSV-label defect that does **not** reach the LP — `_unit_outage_target`
   routes facility 3470 by unit, not by label. Recorded so it is not re-found and
   mis-attributed.)*
3. **A period-average used as an hourly ceiling.** A multi-week flat plateau caps
   the one evening inside its window when the plant ran hard. This is why the
   defect is *seasonal*: fleet-wide, the mean MW of CEMS-above-model-available
   peaks in **April (2,713 MW)** and **March (2,302 MW)** and bottoms in
   **February (866 MW)** and **September (1,062 MW)** — the maintenance season,
   exactly where both fabricated spike days sit. *(Own construction,
   non-gating: 118,753 plant-class-hours / 15.293 TWh in 2024; **not** the
   committed `impossible plant-hours` metric of the
   `ercot_thermal_dam_availability` cell, and not comparable to it.)*

**The correction this specifies** — named, not built, each needing its own
charter and an owner adjudication:

* **C1 — grain repair (zero DOF, pure wiring).** Give
  `partial_outage_derate_factors` the class grain its own extract already
  carries. Strictly the smallest change and the one with no judgement in it.
* **C2 — rule-19 reconciliation.** Replace `f_window × f_partial` with
  `min(f_window, f_partial)`: two resolutions of one phenomenon reconciled, the
  same way the event cap itself composes with the COP layer. **Measured
  counterfactual, reported honestly: C2 helps but does not close the object
  alone** — W A Parish 0.2539 → 0.3630 (still below `f_CEMS` 0.7843), Martin Lake
  0.3347 → 0.5020, Guadalupe 0.2410 → 0.4820, J K Spruce 0.0791 → 0.2080. It
  removes the double-count, not the period-average-as-ceiling fault.
* **C3 — ceiling floor at the plant's contemporaneous output.** Flagged as the
  **least admissible** and recommended against: it injects a measured *outcome*
  into the availability envelope with no forward analogue (rule 13
  `[R-MEASURED]`).

**Recommendation, for the owner and not acted on here: C1 + C2 together**, as a
single rule-19 reconciliation of the ceiling's own two layers — never a repeal of
the ERCOT-148/149 precedence, which removed a real 4.36/4.98/5.01 TWh coal (and
4.27/5.93/4.14 TWh gas) phantom and is not disturbed by either.

Kill gates for any such arm are fixed in the precommit §5 and are not restated
here: G-BIT/G-SPAN (conditional pair — a G-NEUT-admissible rule is year-agnostic,
so G-SPAN applies), G-SHED, G-SPUR, G-C3c, **G-COAL148** (the incumbent coal
adjudication must survive within 0.5 TWh), G-DOF (zero new fitted scalars), G-D2,
LOYO. **G-NEUT** (precommit §3c) is not reached: neither C1 nor C2 restricts the
event-window population — both are year-agnostic, class-agnostic reconciliations
of how existing layers compose, so no population is selected and the ercot-171
gate has nothing to bite on. Any *future* proposal that does restrict the window
population must clear G-NEUT before it may be built.

## 5. What is NOT claimed

* **The ERCOT-148/149 precedence is not refuted.** Its object — a QSE filing
  OFF-at-full-HSL through a certified weeks-long dead stop of baseload coal — is
  real and its removal stands. What this session finds is that the **ceiling**
  that precedence enforces is defective at *partially*-available multi-unit
  plants, where CEMS is **not** zero. At the two shed hours the ceiling
  contradicts the physical record it claims to represent; that is a
  reconciliation question inside the mechanism, not a case against it.
* **No cell verdict is flipped.** `ercot_dam_availability_coal_event_cap` and
  `ercot_dam_availability_gas_event_cap` both stay **`K`**; their cells are
  re-cited with this defect recorded as an open root cause.
* **P-ERR passed but is a weak discriminator, and this is a pre-registration
  lesson, not a post-hoc softening.** It reads 1.0000 because `E(h) > 0` in
  8,578 of 8,760 hours — the cap binds somewhere almost always — so the gate
  could not have failed as written. It is reported at its measured value and the
  weakness is recorded; the load-bearing gates are `E ≥ shed`, `E_named/E`, L1
  and L2, all of which could have failed and did not.
* **No claim about 2023 or 2025.** They were read only as the shed-hour census
  (4 / 0) and are otherwise untouched. Whether the same defect drives the 2023
  shed hours is **item 11's chartered extreme-hour face**, not this session's.
* **No solve, no DOF, no keeper movement.** Nothing in this session changes a
  dispatch.

## 6. Governance

Rule 15 `[R-DASHBOARD]`: **no solve was run, so no bundle and no dashboard
registration** — the deliverable is the committed record
`results/calibration/ercot172_maintenance_availability.json`, the probe
`scripts/probes/ercot172_maintenance_availability_phase0.py` (which reproduces
every number here from committed inputs plus two cached no-LP captures), and this
write-up. Rule 16 `[R-ALLYEARS]`: not engaged — no bundle. Rule 22
`[R-HOLDOUT]`: 2024 object, 2023/2025 read only as the shed census; ERCOT holds
no `complete` marker, so 2022 and every locked-test year stayed quarantined and
unread. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run, no constant re-identified.
Rule 25 `[R-ISO-SCOPE]`: ERCOT-scoped; no other ISO's cell or artifact read or
written. Rule 27 `[R-PUSH]`: no existing ≥300-line source file was rewritten;
pushes blob-verified. Rule 28(b)/(c) `[R-MECH-MATRIX]`: matrix §5.1 item 15
stamped and both event-cap cells re-cited in this session;
`check_mechanism_matrix.py` exit 0.

**Instruments reused verbatim, never re-implemented:**
`scripts/probes/ercot148_availability_capture.py` (unmodified, as a subprocess),
`market_sim.data.outages.{unit_outage_derate_factors, partial_outage_derate_factors,
ercot_thermal_dam_availability_plant_series}`.

**Carried forward, surfaced NOT decided.** (1) **The ercot-167 SOC-reserve
re-gate stays blocked** — its reopen condition is this defect *landing*, and
nothing landed: the object is now attributed and a correction specified, but no
fix is built. The re-gate becomes available only after a correction is armed and
solved. (2) ercot-171's named limb-C successor (an instrument for
`COAL_PEAK_OFFER_LEVEL` that does not select on the tail) is unchartered.
(3) ercot-165's daytime curtailment mode needs an owner decision on a per-family
weight. (4) Item 11 stays FILED-UNLICENSED on its crosswalk half and chartered on
its extreme-hour half; the R-term per-class split above is new input to it.

**DO-NOT-REDO honoured in full** — the ~8 GW cheap CC offline block, the CC
headroom crosswalk, both ercot-171 COAL limb verdicts,
`energy_online_capability_cap`, `ercot_storage_rt_offer_surface`, per-year CT
re-identification, lignite offer SLOPE, `coal_min_load_floor`, lignite daily unit
commitment, coal seasonal LEVEL split, `coal_offer_level_rebasis`,
`tranche_startup_amortization`, ercot-168 OPTION B, the West/Panhandle topology
split.

**Next shorthand: ercot-173.**
