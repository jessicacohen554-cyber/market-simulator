# PREREG pjm-147 — measured power-only CHP heat rates at PJM (`measured_chp_heat_rates` cell)

**Committed BEFORE any arm solves** (the pjm-144/146 protocol). Charter:
`docs/handoffs/pjm-matrix-column-triage-2026-08.md` §2.2 (the triage's rank-2
live candidate; rank 1 `state_carbon_pricing` was spent at pjm-146 and left
`O`, PENDING OWNER). Keeper under test: `2026-07-31-pjm-143b-hy-level`
(CALIBRATED 9/9, C1 16/16 free 12/12, zero FAILs). One lever, zero fitted
parameters, single-delta A/B.

Rule 25 `[R-ISO-SCOPE]`: MISO/CAISO/NYISO `K` and NEISO `O` transfer nothing.
PJM enters as `U` and is judged on PJM's own artifact, derived this session
from PJM's own eGRID + CAMPD record.

## 1. The claim

eGRID publishes a **steam-credited** heat rate for a cogeneration plant: it
removes the fuel it attributes to useful thermal output before dividing by net
generation, so `PLHTRT` is not the rate at which the machine turns fuel into
power. Fed to the LP as a marginal cost it makes CHP the cheapest thermal on
the system. The measured replacement is eGRID's own published allocation added
back on the same net denominator, `(PLHTIAN + CHPCHTI) / PLNGENAN` — no
gross-to-net factor, the basis/source/vintage/denominator all held fixed.

**Standing defect this addresses (keeper note 13, carried from pjm-135):**
"PJM CC_CHP runs +42 %". Restated on the current keeper's own C1 rows, on the
grid-delivered basis the rubric scores:

| year | model TWh | actual TWh | miss | C1 status |
|---|---|---|---|---|
| 2023 | 9.047 | 6.115 | **+2.93 TWh (+47.9 %)** | PASS |
| 2024 | 8.696 | 7.283 | **+1.41 TWh (+19.4 %)** | PASS |
| 2025 | 7.785 | 6.445 | **+1.34 TWh (+20.8 %)** | SKIPPED (preliminary EIA-923, 71 % reporting) |

This is a class-level structural misstatement, not a price-fit complaint. It
is also **not** a failing gate: C1's band is ±min(2 % ISO load, 8 TWh) and
±3 pp share, so CC_CHP passes with wide headroom in both gated years. The
lever is chartered under rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`, not
to close a residual.

**PJM is the other hand-factor ISO.** `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS =
{CAISO, PJM}` — PJM's incumbent is not eGRID's credited rate but that rate
times an off-registry hand number (×1.8 for sub-8.0 CT_CHP; ×1.15 floored at
6.3 for sub-6.0 CC_CHP). Arming therefore also **retires a hand number**
(rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`), exactly as caiso-147 did.

## 2. Mechanism spec (the whole delta)

**There is no code delta.** Unlike pjm-146 this lever adds no
`ScenarioConfig` field, no constants registry and no wiring: the gate
`ScenarioConfig.measured_chp_heat_rates: bool = False` already exists, is
already registered in `_CACHE_KEY_OPTIONAL_FIELDS` (default key stays
`603c2498bf71d21d`, verified in-session; an armed run gets a distinct key),
and its matrix row already exists. The delta is exactly two things:

1. **The artifact**, derived this session with the ISO-generic deriver,
   unmodified (rule 23 `[R-FROZEN-DERIVE]`; committed at `a3efa19` before this
   pre-registration):
   `data/raw/_processed-legacy/chp_power_only_heat_rates_PJM.csv`.
2. **`--set measured_chp_heat_rates=true`** on arm B.

`apply_measured_chp_heat_rates` runs FIRST and hands the legacy hand factor a
`skip_ids` set, so a plant on its own measured rate never also takes the ×1.8
(rule 19 `[R-ONE-MECH]`). Scope is `(plant_code, plant_group)`-keyed and
restricted to `TARGET_CLASSES = (CC_CHP, CT_CHP)`, so a mixed facility's
out-of-scope trains are not repriced.

### 2.1 The artifact, audited (`scripts/probes/_pjm147_artifact_audit.py`)

65 `(plant, class)` rows, **21 applied**. Flag census: `not_unfired_topping`
27, `ok` 21, `no_chp_credit` 8, `no_egrid_row` 5, `basis_mismatch` 2,
`above_physical_band` 1, `below_physical_band` 1.

| class | plants | capacity | metered CAMPD energy | cap-wt shipped → measured |
|---|---|---|---|---|
| CC_CHP | 5/14 | 1,766/2,385 MW (74.0 %) | 24.95/30.26 TWh (**82.5 %**) | 7.422 → 7.943 (**+7.0 %**) |
| CT_CHP | 16/51 | 268/823 MW (32.6 %) | 1.17/4.64 TWh (**25.1 %**) | 10.701 → 11.282 (+5.4 %) |

CEMS validation: `PLHTIAN + CHPCHTI` reproduces independently metered CAMPD
annual heat input within 1 % on **11/12** covered plants, median ratio
**1.00000**. The one miss (50463 Procter & Gamble, 0.429) is a plant with
combustion units below the Part-75 boundary, where CEMS undercounts and eGRID
is the complete source — the check fails toward CEMS, never toward eGRID.

**Direction is PJM's own.** CC_CHP is **ONE-SIDED DEARER** — 5 of 5 rows,
100 % of covered MW — which is the MISO/NEISO shape and the opposite of
CAISO's two-sided result. CT_CHP is **two-sided with a dearer tilt** (13
dearer / 191 MW, 2 cheaper / 68 MW). The two cheaper CT_CHP rows are
hand-factored ones the ×1.8 **over**-corrected (Energy Center Dover CT 12.577
→ measured 9.929), which is caiso-128's "wrong in both directions at once"
measured on PJM.

**The caiso-147 seam defect in PJM is real and MEASURED SMALL.** 29 rows carry
the hand factor, but 25 are excluded by other gates regardless, so gating at
the replacement seam rather than the shipped rate buys PJM **4 applied rows /
182.2 MW** — against CAISO's 59 rows / 3,089 MW. PJM's CC_CHP credited rates
all sit above 6.0, so the CC limb of the hand factor never fires on the
applied population. Recorded because the triage predicted a CAISO-sized
defect; it is not.

**Adverse selection, stated:** CC_CHP covered plants are cap-wt 7.422 shipped
vs 8.194 uncovered (covered are the more efficient); CT_CHP covered 10.701 vs
uncovered 10.044 (the opposite tilt). Both mild, neither erased.

### 2.2 Two limitations declared NOW, not discovered later

- **The CT_CHP half is NOT identified and is NOT scored.** Coverage is 32.6 %
  of capacity and 25.1 % of the class's own metered energy — thin on **both**
  bases, unlike CC_CHP. And `CT_CHP ∈ FUELMIX_EXCLUDED`, so C1 never gates it
  in any ISO. It will be reported as a dispatch consequence and **must not be
  cited in either direction as evidence** (the neiso-73 discipline).
- **CC_CHP and CT_CHP are exempt from BOTH C7 and C8 by explicit class list**
  (`D1_GATED_CLASSES` / `D2_EXEMPT_CLASSES`) for host-steam-pinned duty — NOT
  by the 2 % materiality floor. Their D-1/D-2 numbers are **diagnostics, never
  a passed gate** (the caiso-147 protective-framing correction).

## 3. Pre-declared expectations (E1)

Cost arithmetic (deterministic): at PJM's keeper gas the CC_CHP cap-weighted
+0.521 MMBtu/MWh is roughly **+$1.5–1.9/MWh** on a ~$22–26/MWh marginal cost.
The class move is **dominated by three plants**, and that shape is declared
because it bounds the expected volume response: Marcus Hook (877 MW) moves
only 6.8314 → 7.0118 (+2.6 %) and Brandywine (427 MW) 8.4689 → 8.4945
(+0.3 %) — together 1,304 of the 1,766 covered MW barely move — while Hopewell
(378 MW) moves +17.2 %, Dover CC (59 MW) +42.1 % and Kenilworth (24.5 MW)
+44.3 %.

- **E1a (direction, all years):** CC_CHP model volume **FALLS**. CT_CHP
  reported, not predicted. The displaced energy lands predominantly on
  CC_REGULAR.
- **E1b (CC_CHP magnitude band):** **−0.3 to −2.0 TWh** per year. Declared
  from the plant-shape above (the two largest units barely move) net of the
  `chp_steam` floor, which already holds 11.0/7.9/10.4 % of the class's energy
  and puts a floor under the fall. A band miss is **recorded, never re-fit**
  (pjm-143 precedent).
- **E1c (C1 CC_CHP fit):** |error| **IMPROVES in all three years**. 2023 has
  +2.93 TWh of headroom, so any fall inside E1b improves it outright; 2024
  (+1.41) and 2025 (+1.34) improve for a fall up to 2.82/2.68 TWh, which is
  outside E1b's upper edge.
- **E1d — THE C1 MAGNITUDE EXPECTATION** *(pjm-146's declared gap: it licensed
  a C3a move ex ante but registered no C1 gate, and that is exactly why its
  verdict could not be adjudicated on its pre-registration alone)*:
  **no C1-gated class moves more than 1.5 TWh in any year, and CC_REGULAR —
  the class carrying ~40 % of ISO load — moves no more than 1.5 TWh.** The
  basis: CC_CHP's entire annual volume is 9.0/8.7/7.8 TWh (1.1 % of ISO
  generation), so even a complete class collapse could not move CC_REGULAR
  more than ~9 TWh, and E1b bounds the realistic transfer at 2.0 TWh. A move
  beyond 1.5 TWh on any C1-gated class is **out of band and is an elasticity
  finding**, escalated to the owner with numbers and blocking promotion —
  not a silent keep and not a revert.
- **E1e (C3a/C3c, reported not predicted):** C3a is reported in both arms. A
  1.1 %-of-generation class repricing should barely touch the annual
  load-weighted level; no direction is predicted. C3c tail-hour counts are
  reported explicitly against the keeper's thinnest margins (~1 h in 2024,
  ~2.5 h in 2025 — keeper note 7). No prediction beyond "reported".

## 4. Gates and kill rules

Construction gates **kill**; fit outcomes are **reported** and go to the owner
with numbers (rule 1: never revert a structurally-correct mechanism because
the residual moved the wrong way).

- **K0 — wiring liveness, PRE-SOLVE (the ERCOT-146 hazard).** ERCOT's cell is
  `I` because under `use_campd_bins` its thermal fleet comes from the curated
  per-plant sheet, which never receives the kwarg, so flag-on and flag-off
  build a byte-identical fleet. `assembly.load_or_synthesize_bins` reads that
  sheet only for `iso == "ERCOT"`; PJM synthesises its bins through
  `load_fleet_from_csv(..., measured_chp_heat_rates=...)`. **Measured on PJM's
  own fleet before any solve is spent** (`_pjm147_flag_fidelity.py`, rule 25 —
  neiso-70's clearance is NEISO's): the flag must move ≥ 1 generator and the
  CC_CHP cap-weighted heat rate at the LP seam, and must move **no class
  outside `(CC_CHP, CT_CHP)`**. No movement ⇒ stamp `I`, spend no solve.
- **K1 — mechanism live at its own grain (post-solve).** Max |Δ class-hour MW|
  on CC_CHP + CT_CHP > 1.0 MW in at least one year. Below that ⇒ `I`.
- **K2 — control integrity (strict byte).** The control arm reproduces the
  committed keeper to **0.0 MW** on every class-hour and to the third decimal
  on load-weighted prices (the pjm-144/146 standard, from
  `class_hourly_<year>.parquet` + `system_<year>.parquet`). Any drift ⇒
  stop-the-line, diagnose before the candidate is scored.
- **K3 — scope integrity.** In the solved arms, **no class outside
  `(CC_CHP, CT_CHP)` may change by more than round-off from a direct
  repricing** — every other class's move must be a dispatch consequence, not a
  repriced offer. Verified from the built fleet: exactly the 21 applied
  `(plant, class)` pairs carry a changed heat rate, and no other generator
  does. Any breach ⇒ kill (construction).
- **K4 — sign.** CC_CHP is one-sided dearer at the seam, so CC_CHP energy
  **rising** in any year is a defect signal ⇒ stop and diagnose.
- **K5 — OVERSHOOT (the neiso-70 kill, pre-registered as the triage §2.2
  requires).** If CC_CHP crosses from over- to under-generating such that its
  **|C1 error| WORSENS in any year**, the mechanism over-releases the class it
  reprices. That is a **pre-declared promotion blocker → cell `O`, not `K`**.
  It is explicitly **not** a reason to revert the artifact: rule 14
  `[R-ACCURATE]` forbids returning to the eGRID estimate because it fits
  better, so the input stays committed and the flag stays default-off while
  the root cause is named. PJM's mitigating fact, declared now: unlike NEISO
  (which carries **no** `chp_steam` D-2 row at all — the mechanical reason its
  CC_CHP fell straight through), PJM's CC_CHP **does** carry one at
  11.0/7.9/10.4 % of class energy — but far below CAISO's 43–47 %, so the
  overshoot risk is mitigated, not removed.
- **Honesty:** every criterion of the standard scorecard on both arms from
  `metrics.json` **only**, never re-derived; `legitimacy_diagnostics` on both
  arms **scored on the committed slim file set** (FINDING-pjm146 §8 — a fresh
  full bundle resolves mechanisms the committed tree cannot reproduce, so
  comparing a full-basis arm against a slim-basis control compares coverage,
  not dispatch). Order: register → diagnostics → attestation →
  `calibration_verdict --write-metrics` → A/B scorer. LOYO (rule 22): zero
  fitted parameters ⇒ nothing is identified on any training year; the
  per-year results **are** the leave-one-year-out evidence and are reported
  per-year.

## 5. Protocol

- Chain: `scripts/probes/_pjm147_chain.sh` (the committed `_pjm146_chain.sh`
  passthrough pattern; keeper `pjm143_hy_level_B`; swap re-asserted first —
  keeper note 14, peak RSS 15.55 GB with `ramp_limits=True`).
  - control: `_pjm147_chain.sh pjm147_control_A "<note>"`
  - candidate: `_pjm147_chain.sh pjm147_chp_B "<note>" --set measured_chp_heat_rates=true`
- Years **2023 2024 2025** in ONE invocation per arm, sequential, one fresh
  process per year, `--reuse-solved` links (rule 12 `[R-PARALLEL]`; rule 16
  `[R-ALLYEARS]` — never a one-year keeper). "reusing years" is confirmed on
  links 2–3; a dirty tree makes `--reuse-solved` refuse and silently re-solve
  (miso-113), so the chain script is committed before launch.
- Arms sequential. **Both arms registered on the backcast dashboard (rule 15
  `[R-DASHBOARD]`) in this session whatever the verdict**, top-15 retention,
  `pjm N <keyword>` labels.
- Scorer: `scripts/probes/_pjm147_chp_ab.py`, modeled on
  `_pjm146_rggi_ab.py` — all criteria from the two bundles' `metrics.json`
  plus the K-gates above from the built fleet and the hourly sidecars;
  attestation from the committed A/B JSON
  (`results/calibration/_pjm147_chp_ab.json`).
- **Verdict mapping.** K0/K1 ⇒ `I`. K2/K3/K4 breach ⇒ no verdict,
  fix-or-stop. K5 breach ⇒ `O` (built, live, gates intact, but it overshoots
  the class it reprices — the neiso-70 outcome). Live + gates intact + no
  overshoot + no out-of-band C1 move ⇒ surfaced to the owner as a promotion
  candidate: **`U → K` only on owner promotion, `U → O` if left pending**. A
  rejection on the merits stamps `R` with this pre-registration cited.

## 6. What this session does NOT do (scope fence)

No re-derivation of the artifact against any residual (rule 23 — it
re-derives only when eGRID/CAMPD source data updates, and the derive commit
cites the source reason). No hour-grain screen on the shared deriver (the
caiso-147 side finding: sub-6.0 MMBtu/MWh loaded meter hours drag the derive
low in every ISO, PJM 1.55 % of loaded hours / +0.081 energy-weighted — that
would move three committed keepers' inputs and needs its own charter). No
retirement of `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` for the plants the
artifact does **not** cover. No `chp_steam` floor work, no `chp_btm_pct` /
`chp_grid_pmin_mw` change (nyiso-105's named successor lane, and PJM's own
if K5 fires). No touch of any other ISO's CHP path. No promotion — `U → K` is
the owner's call. No solve on GitHub Actions. No year outside 2023–2025:
`frontend/data/backcast/holdout-freeze.json` is ACTIVE and outranks PJM's
`complete` marker.
