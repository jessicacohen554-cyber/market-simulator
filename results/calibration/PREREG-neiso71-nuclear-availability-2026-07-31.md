# PRE-REGISTRATION — neiso-71: `nuclear_unit_availability` (NEISO)

**Committed and pushed BEFORE either bundle solves.** Every gate, threshold and
prediction below is fixed here; none may be revised after a number is seen.

| | |
|---|---|
| Session | neiso-71 |
| Branch | `claude/neiso-71-chp-floor-nuclear-twsx5m` |
| Incumbent keeper | `2026-07-31-neiso-70-ctheatrate` (bundle `neiso70_ctheatrate_B`) — CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat (C3c) |
| Lane | rule 14 `[R-ACCURATE]` measured-input swap — **not** C3c scarcity work |
| Arm tested | `nuclear_unit_availability = True` (matrix §5.6 item 7, NEISO cell `U`) |
| Bundles | `neiso71_control_A`, `neiso71_nucavail_B` |
| Runs | `2026-07-31-neiso-71-control`, `2026-07-31-neiso-71-nucavail` |
| Years | 2023 2024 2025, one invocation each, sequential within (rules 12/16) |

---

## §0 — why this arm and not Lever A (pre-registered, decided BEFORE any solve)

The session's PRIMARY lever was §5.6 item 6 — derive a measured NEISO CC_CHP
host-steam floor and land it together with `measured_chp_heat_rates`. **It is
MEASUREMENT-BLOCKED and no LP was spent on it.** Screened by
`scripts/probes/_neiso71_lever_screen.py` (no solve), reproduced above this
pre-registration:

* NEISO's `thermal_tranches_NEISO.csv` is a **pre-WP-3 vintage** — it carries
  neither `steam_level_cf` nor `p25_allhr_cf`, so `chp_steam_floor_p25` is
  **inert for NEISO today** and the class's committed `chp_pmin_cf` is
  `0.0 / 0.0 / 0.0` for all three CAMPD-visible CC_CHP plants (the
  p2-of-all-hours statistic FINDING-caiso95 §5 showed mixes offline zeros in).
* Re-running the committed WP-3 statistic on **NEISO's own CAMPD** returns
  **146.1 % of nameplate** for Kendall Square (EIA 1595, 206 of 494 MW = 42 %
  of the class). It is **saturated, not measured**: CAMPD unit "4"
  (unitType "Combined cycle") meters **278-299 MW median** against an EIA-860
  CHP nameplate of **213.4 MW (206.0 summer)**, so the derivation's 1.5
  available-CF clip guard binds in **59.0 %** of online hours.
* Armed, that level floors Kendall at **195.7 MW against a 206.0 MW pmax —
  95.0 % of capacity, forced flat year-round (~1.71 TWh/yr)**, which would MORE
  than close neiso-70's 0.34-0.68 TWh CC_CHP shortfall. A floor sized like that
  is a **fitted parameter** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`) and the
  session prompt forbids it explicitly.
* The other two CAMPD-visible CC_CHP plants measure **2.2 %** and **3.6 %** —
  the statistic correctly self-targeting genuine cyclers (5.5 % / 7.0 %
  on-frequency). Non-Kendall CC_CHP floor total: **15.0 MW**. NEISO's merchant
  cogens really do carry no host-steam obligation; this is a different fleet
  from CAISO's flat 43-47 % steam hosts, not a missing mechanism.
* Every capacity-factor floor inherits the same denominator (the EIA-923 lens
  divides by the same nameplate), so **no admissible NEISO measurement of the
  obligation exists** until Kendall's capacity basis is fixed — its own lane,
  and it sits in the miso-95 provenance-orphaned `nameplate_mw` column.

Per the session's own instruction ("if no admissible NEISO measurement of the
obligation exists, say so and stop"), Lever A stops at `O` (unchanged, still
open) and this pre-registration covers the FALLBACK lever only.

## §1 — the artifact (STEP 1, pre-solve)

`data/raw/nuclear-availability-NEISO.csv` — 3,288 rows = 3 reactors x 1,096
days, derived at HEAD by the committed
`scripts/data/derive_nuclear_availability.py` with **zero fitted scalars**
(`EVENT_RAW_MAX` 0.90 / `SCALE_CLIP` 1.25 / `WEDGE_TOL` 0.01 inherited frozen
from the ERCOT deriver, rule 23 `[R-FROZEN-DERIVE]`).

The **only** code change is an identifier crosswalk — three `NRC_TO_EIA["NEISO"]`
rows, not a tunable:

| NRC unit | EIA (plant, unit) | model pmax | zone |
|---|---|---|---|
| `Millstone 2` | (566, 2) | 863.43 MW | Connecticut |
| `Millstone 3` | (566, 3) | 1,244.97 MW | Connecticut |
| `Seabrook 1` | (6115, 1) | 1,247.00 MW | North |

3,355.4 MW total. Pilgrim (retired 2019), Vermont Yankee (2014), Maine Yankee
and Connecticut Yankee carry neither NRC rows nor a model fleet unit, so the
crosswalk is complete. All three reactors report **365 / 366 / 365** days in
2023 / 2024 / 2025.

**Reconciliation:** all 36 months reconcile to the committed
`NUCLEAR_MONTHLY_CF_BY_YEAR["NEISO"]` EIA-923 anchor within `WEDGE_TOL`
(worst −0.70 %, 2025-02); **no month is dropped**, so the overlay covers 100 %
of dates. `--check` reports `nuclear-availability-NEISO.csv reproduces
byte-for-byte`.

**Rule 13 `[R-MEASURED]` admissibility:** a reactor power state / refuel window
is a physical availability event — the same class as the CAMPD fossil outage
windows and the already-keeper ERCOT/PJM/NYISO/CAISO nuclear overlays. It
regenerates for a forward year from the static `NUCLEAR_MONTHLY_CF` /
refuel-block schedule and responds to changed conditions. **The anchor owns the
LEVEL, NRC owns the TIMING** — no measured outcome is fed back.

## §2 — construction gates (each is PASS/FAIL, fixed here)

* **G-1 flag fidelity (the ERCOT-146 hazard).** ERCOT-146 stamped a flag `I`
  with no solve spent because it never reached the fleet. Discharged here
  **before any solve** by `_neiso71_lever_screen.py`: all **3 reactors match by
  `(plant_code, unit_no)` with 1.000 date coverage in every year**, 3,355.4 MW.
  Post-solve confirmation: the arm's `run_config.json` records
  `nuclear_unit_availability: true`, the control `false`.
* **G-2 control integrity.** The control is a `--replay-bundle` of
  `neiso70_ctheatrate_B/meta.json` **verbatim**; the arm replays the same meta
  with exactly one key flipped. The control's ScenarioConfig must equal the
  keeper's except recorded provenance. **Byte identity against the COMMITTED
  keeper is NOT a gate** — neiso-70 measured code+environment drift of
  913-1,029 MW on CC_REGULAR that cannot be decomposed; the same DRIFT is
  reported here, not gated.
* **G-3 LIVENESS — `max |Δ class MW| > 50` in at least one year.** Failing this
  makes the verdict **`I` (inert), not `R`**. Pre-solve availability-side
  prediction, recorded now: max |Δ| **1,050.5 / 1,841.7 / 1,026.3 MW**
  (2023/24/25), mean |Δ| 226.2 / 210.9 / 169.3 MW.
* **G-4 single delta.** Proven by construction and re-checked from the two
  `run_config.json`s: `replay_keeper.build_kwargs` differs in **exactly one
  kwarg**, `nuclear_unit_availability: False -> True`.
* **G-5 year span.** Every bundle carries exactly `[2023, 2024, 2025]`
  (rules 16 `[R-ALLYEARS]` / 22 `[R-HOLDOUT]` D-6). The holdout spend freeze is
  ACTIVE and NEISO's locked test is already SPENT (2026-07-07), never
  re-grantable — **no year outside 2023-2025 is touched**.

## §3 — predictions (directional, recorded in advance)

* **P1.** Fleet nuclear ENERGY moves ≈ 0 (|Δ| ≤ 0.05 TWh/yr): the monthly
  anchor is preserved by construction. A larger move means the reconciliation
  leaked and is a **bug to root-cause**, not a result.
* **P2.** The delta is **timing and location**, not level: within a refuel
  month the model stops derating all three reactors uniformly and instead takes
  one reactor to ~0 while the others sit near 100 %. Expect thermal
  (CC_REGULAR / oil) to move counter-cyclically hour-to-hour with ≈ 0 annual
  net, and Connecticut-vs-North zonal prices to separate more than the fleet
  mean suggests.
* **P3.** Mean λ moves are small (< $1/MWh annual). C3c tail hours are
  **not** expected to change materially — this is not scarcity work.

## §4 — what can KILL the arm vs what is only REPORTED

**KILL (blocks promotion):**
1. Any criterion status regression PASS → FAIL against the control.
2. C1 coverage falling below the keeper's 12/12 · free 8/8.
3. G-4 failing (more than one config delta) — the arm is void, not rejected.
4. P1 violated (fleet nuclear energy moves > 0.05 TWh/yr) — reconciliation bug.
5. The determination degrading below CALIBRATED-WITH-CAVEATS on a
   **non-artifact** basis.

**REPORTED, never a kill (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`):**
class TWh moves, mean λ, C3c tail hours, D-1/D-2 rows, zonal price splits, and
the control-vs-committed-keeper DRIFT. **A worse backcast on a measured-input
swap is a discovered bug to root-cause, not a kill condition, and reverting to
the smear because it fits better is forbidden.** Structural integrity improving
while gates hold is a keeper.

**Known scoring artifacts — carried from neiso-70, not to be rediscovered:**
* A probe bundle with no `calibration_attestation.json` scores NOT-YET /
  governance UNATTESTED, and **C3c degrades CAVEAT → FAIL** because a caveat can
  only be LEDGERED by an attestation. That is an **artifact**, not drift.
* **C1 2025 rows are SKIPPED** (preliminary EIA-923, 57 % plant reporting).
  C1 scores 2023+2024 only — a 2025 C1 ratio is never evidence.
* C7 `shape` is SKIPPED for NEISO; CC_CHP / CT_CHP are exempt from BOTH C7 and
  C8 by explicit class list. Their D-1/D-2 numbers are diagnostics, never a
  passed gate in either direction.

## §5 — DOF ledger (rule 21 `[R-DOF]`)

**Zero free parameters added.** The arm swaps a measured fleet-month smear for
a measured per-reactor daily series on the **same EIA-923 level anchor**. The
crosswalk is an identifier map (NRC name → EIA plant/unit), not a tunable; the
three reconciliation constants are inherited frozen from the ERCOT deriver and
were **not** swept. Per rule 23 the extract re-derives only when a new NRC
annual file lands, and any such commit must cite the data change.

## §6 — governance

Rules 1, 5, 12, 14, 15, 16, 21, 22, 23, 24, 25, 27, 28. Years 2023-2025 only.
Both bundles registered on the dashboard whatever the outcome (rule 15
`[R-DASHBOARD]`), and the matrix cell updated in this session including a
rejection or an inert verdict (rule 28b).
