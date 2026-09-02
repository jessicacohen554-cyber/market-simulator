# FINDING — caiso-239: the chartered ST_GAS committed scalar is MIS-LOCATED; the repair lands at the scalar that actually prices the band

**Session caiso-239, 2026-09-02. Branch `claude/caiso-st-gas-committed-sce4lq`.
Keeper UNCHANGED at `2026-09-01-caiso-231-b1-ungrounded`; determination
**NOT-YET**, C3a the sole load-bearing FAIL. Run registered:
`2026-09-02-caiso-239-b1-stgas`. CAISO holds no `complete` and no `final`
marker; the holdout freeze is ACTIVE; every read and the whole solve stayed
inside 2023–2025.**

Pre-registration:
`PRECOMMIT-caiso239-st-gas-committed-relocation-2026-09-02.md`, pushed to
`origin` (`84803e81`) **before the solve**.

---

## §1 — HEADLINE

The caiso-238 object-2 charter funded a choice between two values for
`offer_curve_by_group["ST_GAS"]["committed"] = 0.81`, on the premise that the
scalar prices CAISO's three coastal OTC steamers. **The premise is false.**
Both chartered candidates are refused on that scalar — on measurement, never on
C3a — and the repair is relocated to
`campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"] = 1.15`, the uncited
ERCOT-lineage literal that actually prices CAISO's 2,858.8 MW once-through-
cooling steam fleet. The relocated repair is built, gated default-off, solved
and registered; it costs **+0.0001 / +0.0060 / +0.0001 $/MWh** of C3a, inside
its pre-registered adverse bound, and changes no verdict.

---

## §2 — THE FALSIFICATION, IN FOUR MEASUREMENTS

Instrument: `scripts/probes/_caiso239_st_gas_committed_footprint.py` →
`results/calibration/_caiso239_st_gas_committed_footprint.json`. **Zero solves.**
The marginal-rung attribution and the §H bounding form are imported UNCHANGED
from `_caiso230_abovefloor_decomposition.py` and re-pointed at the caiso-231
keeper, as caiso-231's DO-NOT-REDO requires. The footprint is established by
REBUILDING the keeper's offer surface at three band values
(`run_year(fleet_only=True)` — no matrix, no solver) and diffing `mc_base`
row by row.

**F-1 — SCOPE. The scalar moves 2 of the keeper's 25 ST_GAS LP tranches, and no
OTC steamer is among them.** In all three years the tranches of plants **315
(AES Alamitos), 335 (AES Huntington Beach) and 350 (Ormond Beach)** are
byte-identical at `committed` ∈ {0.81, 1.00, 1.683} — max |Δmc| = 0.0.
`offer_curves.py::_offer_curve_for_group` returns **`None`** for
`group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS`, and
`data/outages.py::ST_GAS_PEAKER_PLANTS` names 315, 335 and 350 explicitly
("the last once-through-cooling steamers, kept on OTC compliance extensions as
RMR-style reliability units"). With `offer is None`,
`fleet/assembly.py::bins_to_fleet` never reaches
`committed_hr = base_hr × offer["committed"]`, so the three steamers take
`campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]` = {mr 1.10, **mc 1.15**,
econ 1.00, peak 1.10}. Verified arithmetically on the rebuilt fleet: p315 base
HR 11.850 → committed **13.628** = × 1.15, econ **11.850** = × 1.00, peak
**13.035** = × 1.10, all three exact.

**F-2 — LIVENESS. Both responsive tranches are EIA-860 retired-window units,
and by 2025 both are at zero availability.**

| plant | identity | zone | committed pmax | availability 2023 / 2024 / 2025 |
|---|---|---|--:|---|
| 356 | **AES Redondo Beach LLC** (`eia860_generator_retired_within_window`) | LA_BASIN | 249.0 MW | 0.813 / **0.000** / **0.000** |
| 10446 | **SEGS IX** (Terra-Gen, EIA-860 status `RE`, "Natural Gas Steam Turbine" — the auxiliary boiler of a retired solar-trough plant) | ZP26 | 26.4 MW | 0.764 / 0.631 / **0.000** |

The solve's own log corroborates it independently: *"loaded 26 within-window
retiree units for CAISO (1066 MW, plants [356, …, 10446, …])"*. **In 2025 — the
keeper's worst C3a year — the chartered object is provably dead**: both
responsive tranches carry zero available capacity in all 8,760 hours, so every
candidate value is byte-identical there.

**F-3 — POPULATION MISMATCH.** `caiso_campd_marginal_hr_summary.csv` reports
ST_GAS `n_units = 10`, and `campd_gas_commitment_params_CAISO_units.csv` shows
those ten units are **entirely plants 315 / 335 / 350** (Alamitos 3, 4, 5, CT1,
CT2; Huntington Beach 2, CT1, CT2; Ormond Beach 1, 2). So
`avg_committed_p50 = 1.683` is measured on **exactly the three plants the band
excludes**. Arming it there would apply an OTC-steamer statistic to a retired
Redondo Beach and a retired SEGS auxiliary boiler **while leaving the units it
was measured on untouched** — rule 14 `[R-ACCURATE]`'s own stated exception,
*"the data is defined on a different boundary than our representation"*, in its
exact form.

**F-4 — AGAINST INTEREST: the charter's inversion premise is ALSO false at the
resolved offer level.** On the keeper as built (2024 mean mc, $/MWh) p315 is
committed **69.19** > peak **68.92** > econ **62.38**; p335 68.96 / 68.69 /
62.15; p350 82.84 / 82.57 / 76.03. The three steamers' min-load band is already
their **dearest**, not their cheapest. The inversion is real only for the two
retired units the scalar actually reaches (2023 p356: committed 151.40 vs econ
178.60).

**F-5 — MEASUREMENT QUALITY, disclosed; it cuts in the repair's favour.**
ST_GAS is the only CAISO class whose `avg_committed` spread is wide — p25
**0.682** / p50 **1.683** / p75 **3.275**, ratio **4.80**, against 1.12–1.27 for
CC_CHP, CC_REGULAR, CT_CHP and CT_PEAKER. The spread is real physical
bimodality, not noise: six steam units at LSL **7.6–10.0 %** of HSL pooled with
four colocated CTs at **22.0–28.2 %**, and a lower LSL means a far higher
min-load block-average burn. The model's `_committed` tranche for these plants
is sized **6.3–9.3 %** of nameplate (`Pct_Committed`, `Committed_Source: campd`)
— i.e. it is the **steam** min-load block, whose own statistic sits near p75.
The class p50 is therefore a **conservative** choice for the tranche it prices,
not a midpoint of convenience.

---

## §3 — THE DECISION

**§3.1 — On `offer_curve_by_group["ST_GAS"]["committed"] = 0.81`: NEITHER 1.00
NOR 1.683. REFUSED**, on F-1 (scope), F-2 (liveness) and F-3 (population), each
sufficient alone. This is the **fifth outcome** the caiso-238 charter itself
pre-registered — **MIS-CLASSIFIED at caiso-236**, which recorded the row as
"live and material". It is live in the narrow sense and **not material**, and
neither candidate is admissible on it. Arming either would have been a rule-13
violation dressed as a rule-14 repair.

**Why not 1.00 even as a compromise.** It is not measured; it retires nothing
under rule 21 `[R-DOF]`; and — reported against interest — it would not achieve
its own Lever-A rationale here, because on the caiso-231 keeper the comparator
is the **measured** econ band (1.145), not the 0.95 Lever A was set against. The
only argument for it is that it moves C3a least, which the precommit §0.1
forbids as a criterion.

**§3.2 — The repair is RELOCATED** to `_DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"]
= 1.15` and grounded on `avg_committed_p50 = 1.683`, the measurement taken on
exactly those plants. Statistic and band populations coincide; zero free
parameters; exactly one band moves.

**Registered against interest:** the relocation is a **judgement call the owner
can reverse**. The charter funded object 2 as posed; this session reads "the
ST_GAS committed band" as the phenomenon rather than the dictionary key, because
acting on the key while leaving the scalar that does the work untouched would
repair nothing. On a narrow reading of the funding the correct outcome is §3.1
alone — the refusal, with no arm and no run.

---

## §4 — WHAT WAS BUILT

`ScenarioConfig.caiso_st_gas_committed_measured` — gated, **default off**,
per-ISO registry `constants.ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO`
(CAISO 1.683, cited to the CAMPD artifact and its ten-unit population).
Consumer: one gated limb in `fleet/assembly.py`'s `offer is None` branch, so it
is unreachable for any plant that resolves an offer curve. An ISO with no
registry entry is a **hard error** at both the config gate and the consumer —
never a silent fallback (rule 25 `[R-ISO-SCOPE]`). Registered at all three sites
in one commit per the nyiso-119 discipline; both pinned cache-key literals
verified unmoved. Threaded onto `--replay-bundle` on the established
single-delta pattern. Seven unit tests; matrix base row plus a cell line in
every ISO shard, same PR (rule 28(c)) — **ERCOT's cell is `U`, not n/a**: six
ERCOT plants take the same 1.15 default through the same bypass, and an ERCOT
lane must derive its own `avg_committed_p50` rather than transfer CAISO's.

**Deliberately NOT in `_BACKCAST_ONLY_OVERLAY_FIELDS`**, unlike the two OASIS-bid
siblings. Those arm measured **bid conduct**, which has no forward analogue.
This is a measured **physical heat-rate ratio** — the part-load burn of a boiler,
a unit characteristic that does not depend on the year — i.e. the family's own
documented exclusion (*"measured PHYSICAL parameters with a forward story —
measured heat rates … which rule 14 tells us to PREFER"*). Rule 13 satisfied.

---

## §5 — GATES, SCORED

| gate | verdict | measurement |
|---|---|---|
| **G-STRUCT** | **PASS** | exactly **3 of 1,795** fleet rows move, all three the OTC steamers' `_committed` tranches, ratio **1.4635 = 1.683/1.15** exact; 0 other bands, 0 other classes. Verified pre-solve AND on the solved fleet. |
| **G-INERT** | **PASS** | not byte-identical: 2024 ST_GAS sheds **14.7 GWh (−2.3 %)** to CT_PEAKER (+8.2), CC_REGULAR (+4.6) and imports (+1.8). 2023 and 2025 identical to the keeper to 0.001 TWh in every class. |
| **G-C3a** | **PASS** on its substantive legs | no year flips; 2023 stays PASS at +4.1 %; 2024 +12.5 → **+12.6 %**; 2025 **+15.6 %** unchanged. Exact load-weighted move **+0.0001 / +0.0060 / +0.0001 $/MWh**. |
| **G-C1** | **PASS** | 12/12, free 8/8, unchanged. |
| **G-C3b** | **PASS** | unchanged. |
| **G-C8** | **PASS** | no material class over budget (ST_GAS is 0.6 % of ISO load, inside the 2 % materiality floor). |
| **G-CAVEAT** | **PASS** | budget 1 of 1 — C3c alone, ledgered. |
| **G-CTRL** | **DISCLOSED, NOT SATISFIED AS WRITTEN** | see §6. |

**The pre-registered adverse bound held.** §3 of the precommit predicted
**+0.0003 / +0.0265 / +0.0000 $/MWh**; measured **+0.0001 / +0.0060 / +0.0001**
— inside the bound with 3× and 4× margin in the two years the bound was
non-zero, the same over-prediction behaviour caiso-231 measured (a first-order
bound assumes λ follows the repriced rung 1:1; in an LP the margin moves to the
next-cheapest rung).

---

## §6 — TWO PRE-REGISTERED GATES DISCLOSED AS NOT SATISFIED AS WRITTEN

Neither is dropped, and neither is re-specified after the fact to pass.

**§6.1 — G-CTRL.** It required the arm's `run_config.json` to differ from the
keeper's in the one new flag alone; **22 fields differ**. Every one is HEAD
drift, not a solve input:

- **1** — `caiso_st_gas_committed_measured`, the intended delta.
- **9** — provenance recording added since the keeper solved: `git_sha`; the
  `hydro_plant_modes` presence probe (3 fields — `hydro_ror_split` is **False**
  on both arms, so the partition is recorded and not consumed); the nyiso-176
  `thermal_tranches` identity block (5 fields).
- **8** — new `ScenarioConfig` fields at their defaults
  (`campd_per_unit_attribution`, `carbon_price_delta`,
  `entry_dispersion_expectation_signal`, `entry_vre_zone_selection`,
  `fossil_announced_exits_enabled`, `neiso_net_icr_requirement`,
  `st_gas_mustrun_oom_level`, `unit_outage_mixed_gas_routing`).
- **1** — `caiso_bidir_intertie`, deleted at HEAD by caiso-236 under rule 26.
- **3** — `renewable_buildout_pace` (removed) and the capx-D41 forecast-only CCS
  cost re-identification (`ccs_retrofit_capex_kw` 900.0 → 1521.4,
  `fixed_om_gas_cc_ccs` 25.0 → 65.0), both consumed **only** in
  `model/capacity_evolution/`, which a backcast never runs.

**The substantive claim is established from the DISPATCH instead, and that is
stronger evidence than the field diff:** 2023 and 2025 class energy is identical
to the keeper **to 0.001 TWh in every class**, which no fleet-representation or
measured-input change could survive. This also settles a question the field diff
raised — the `thermal_tranches_CAISO.csv` artifact was first *committed to git*
on 2026-09-01 18:06 UTC, after the keeper solved at 03:05, but the identical
2023/2025 dispatch proves it was already **on disk** for the keeper's solve and
that PR #4536 captured provenance rather than changing an input.

**This is worth the owner's attention on its own.** The caiso-231 standing
directive *"NO CONTROL ARMS"* rests on the empirical warrant that a control
reproduced the keeper to the cent across 25+ merges. That warrant survives here
— but it was checkable only because the mechanism happens to be inert in two of
three years. A future single-delta arm whose mechanism is live in every year
will have no comparable independent check, and the run_config field diff will
not supply one.

**§6.2 — G-C3a's 2025 leg.** Its bound was degenerate: **exactly +0.0000**,
because no responsive tranche is ever the nearest-matched marginal rung in 2025.
The measured move is **+0.0001 $/MWh** — a 1-part-in-400,000 excess on a
$39.79 price level. The §H form counts only zone-hours where the repriced rung
is itself the matched marginal rung within the estimator's $0.75 tolerance, and
cannot represent indirect re-dispatch elsewhere in the stack. Reported at full
magnitude as a **bound-form limitation**; nothing was re-fitted, and the bound
was not widened after the fact.

---

## §7 — THE DOF LEDGER DOES NOT MOVE, EXACTLY AS PREDICTED

Precommit §4 stated the handoff's "n_residual 6 → 5" is **not achievable by this
repair, nor by the chartered one**, because the retired literal lives in
`campd_bins.py` and `build_dof_ledger._count_scalars` reads
`offer_curve_by_group` only. Measured on the rebuilt ledger: `n_entries` 9,
`n_residual` **6**, unchanged. The chartered
`offer_curve_committed_below_floor[CAISO] {"ST_GAS": 0.81}` row **stays** — and
that is correct: this session refused that scalar rather than arming it, and it
still prices the two retired plants. This is the same gate-specification defect
caiso-231 disclosed on its own G-STRUCT DOF leg (the counter is
provenance-blind: it measures the surface's SIZE, not its fitted content).

---

## §8 — DO-NOT-REDO ADDS

1. **Never re-propose `offer_curve_by_group["ST_GAS"]["committed"]` as a repair
   target for CAISO's OTC steamers.** It does not price them; the bypass in
   `_offer_curve_for_group` is the reason, and it is measured (F-1).
2. **Never arm `avg_committed_p50` on that scalar.** The measurement's
   population is disjoint from the scalar's (F-3).
3. **Never quote the chartered scalar as live-and-material on a CAISO keeper.**
   It reaches two retired-window plants and is dead in 2025 (F-2).
4. **Never re-propose this mechanism as a C3a lever.** It COSTS C3a; the
   measured cost is +0.0001/+0.0060/+0.0001 $/MWh.
5. **Never transfer CAISO's 1.683 to ERCOT's six bypassed ST_GAS plants**
   (rule 25). ERCOT's cell is `U`: an ERCOT lane derives its own.
6. **CORRECTED after the fact, against interest.** This session's §2 was
   measured while only caiso-238's PRECOMMIT (`6b7e6492`, PR #4625) was on
   `origin`; its `ASSESSMENT-caiso238-grounding-charter-2026-09-02.md` and
   `_caiso238_grounding_charter.json` **landed on main mid-session** and are
   now committed. They must be cited — and read with their object-2 grade
   withdrawn. The charter graded the scalar **F1, groundable now** on two
   numbers this session reproduces exactly (0.81 / 1.683 = 48.1 %; the
   band-dict inversion), but its `object2_st_gas_committed` block is
   **entirely config-level** — armed multiplier, measured basis, ratio,
   markup-clips-to-zero, class energy share — and contains **no footprint
   measurement of any kind**. It never asked which LP units the scalar
   reaches. That is the gap §2 closes, and it is why the correct grade is the
   charter's own fifth outcome (MIS-CLASSIFIED at caiso-236) rather than F1.
   Object 2's supporting measurements stand; its class and its ask do not.
   A correction banner is appended to the caiso-238 calibration-log entry.

---

## §9 — WHAT IS STILL OPEN (proposed, NOT started)

1. **`_DEFAULT_HR_MULT_BY_GROUP` is an off-registry channel for every ISO and
   every class, not just CAISO ST_GAS.** Twenty-eight uncited literals across
   seven groups price any plant that does not resolve an offer curve, none of
   them recorded in any `run_config.json`. This session repaired exactly one.
   A rule-24 census is the natural successor and is owner-fundable.
2. **The `ST_GAS_PEAKER_PLANTS` double duty (rule 19 `[R-ONE-MECH]`).** One
   frozenset means both "no outage overlay and no reliability floor" (its
   documented purpose) and "no offer curve" (a second phenomenon). The coupling
   is stale — its stated warrant is the `gas_st_*_hr_override` scope, and those
   overrides are `None` on this keeper.
3. Carried unchanged and unfunded: caiso-238 object 4
   (`battery_dispatch_adder` → measured AS reservation + ATB degradation), object
   3 (own-curve shape derive), the SoCalGas OFO arm
   (`PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`), and the `IMPORT_TRANCHES[CAISO]`
   LEVEL object.
