# FINDING — neiso-71: CHP host-steam floor BLOCKED; nuclear per-reactor availability A/B

**Pre-registration:** `results/calibration/PREREG-neiso71-nuclear-availability-2026-07-31.md`,
committed at `464817e` and pushed **before either arm solved**. Every gate,
threshold and prediction below was fixed in advance.

| | |
|---|---|
| Session | neiso-71 |
| Outgoing keeper | `2026-07-31-neiso-70-ctheatrate` (CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat) |
| Frozen HEAD | `464817e` (both bundles; working tree clean at solve time) |
| Bundles | `neiso71_control_A`, `neiso71_nucavail_B` |
| Years | 2023 2024 2025, one invocation each (rule 16) |

---

## §1 — LEVER A: `measured_chp_heat_rates` companion host-steam floor — **BLOCKED, no LP spent**

The session's primary lever (matrix §5.6 item 6) asked whether NEISO's CC_CHP
should carry a host-steam floor like CAISO's and MISO's do, derived from
NEISO's OWN measured obligation. **It should not, and the measurement that
would size one is not admissible today.** Screened entirely without a solve by
`scripts/probes/_neiso71_lever_screen.py`.

### The mechanism already exists and is inert for NEISO

The committed WP-3 statistic `steam_level_cf` (`derive_thermal_tranches.py`,
consumed by `chp_steam_floor_p25`) is exactly the "measured host-steam
operating level" the lever wanted. NEISO's `thermal_tranches_NEISO.csv` is a
**pre-WP-3 vintage** carrying neither `steam_level_cf` nor `p25_allhr_cf`, so
`thermal_tranche_chp_steam_level("NEISO")` returns `{}` and the flag is inert.
The committed `chp_pmin_cf` is **0.0 for all three CAMPD-visible CC_CHP
plants** — the p2-of-all-hours statistic FINDING-caiso95 §5 already showed
mixes offline zeros into the level. That is the mechanical reason NEISO's
CC_CHP carries no `chp_steam` D-2 row.

### Re-deriving it on NEISO's own CAMPD returns a saturated, unusable number

| plant | nameplate | on_freq | `steam_level_cf` | clip_frac | implied floor |
|---|---|---|---|---|---|
| 1595 Kendall Square | 206.0 MW | 0.974 | **146.1 %** | **0.590** | 195.7 MW (**95.0 % of pmax**) |
| 10567 Algonquin Windsor Locks | 64.0 MW | 0.055 | 2.2 % | 0.000 | 0.9 MW (1.4 %) |
| 50002 Pittsfield Generating | 157.7 MW | 0.070 | 3.6 % | 0.000 | 3.7 MW (2.4 %) |

Kendall's 146.1 % is **not a measurement**. CAMPD facility 1595 ("Kendall Green
Energy LLC") reports unit **"4"**, `unitType` **"Combined cycle"**, at
**278 / 299 / 283 MW median** gross (2023/24/25, max 321 MW) against an
EIA-860 CHP nameplate of **213.4 MW (206.0 summer** = the model's pmax, the
`apply_cc_summer_guard` sum 22.9 + 183.1). The available-CF therefore rides at
1.35–1.45 and **saturates the derivation's 1.5 clip guard in 59.0 % of online
hours**.

### Why that is a stop, not a tuning opportunity

Armed, the floor pins Kendall — 42 % of the CC_CHP class — at **95 % of pmax
flat, year-round, ≈1.71 TWh/yr**. neiso-70's CC_CHP shortfall was
0.34–0.68 TWh. The floor would have **over-closed it**, i.e. produced a
visibly "better" backcast from a parameter whose size is set by a capacity
defect. That is a fitted parameter (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`) and
the lever's own charter forbids it.

Every capacity-factor lens inherits the same broken denominator (the EIA-923
delivery-implied level divides by the same nameplate), so **no admissible
NEISO measurement of the obligation exists** until Kendall's capacity basis is
fixed. That fix is its own lane: `nameplate_mw` is one of the five
provenance-orphaned columns miso-95 blocked, and correcting it moves far more
than CHP.

### The structural answer to the question that was asked

**NEISO's merchant CC_CHP genuinely carries no host-steam obligation**, and
that is a real difference from CAISO, not a missing mechanism. Windsor Locks
and Pittsfield are online **5.5 % and 7.0 %** of hours — the WP-3 statistic
self-targeting genuine cyclers to ~0, exactly as designed. CAISO's CC_CHP
`chp_steam` forced share runs 43–47 % because CAISO's cogens are flat baseload
steam hosts; NEISO's two merchant cogens are not. Non-Kendall CC_CHP floor
total across all seven plants: **15.0 MW**.

**Matrix cell unchanged: `measured_chp_heat_rates` NEISO stays `O` (open).**
Nothing was refuted and nothing was promoted; what changed is that the named
successor path is now closed with evidence, and the successor is a capacity
lane, not a floor lane.

---

## §2 — LEVER B: `nuclear_unit_availability` — **`K`, PROMOTED to keeper**

New keeper **`2026-07-31-neiso-71-nucavail`** (bundle `neiso71_nucavail_B`),
replacing `2026-07-31-neiso-70-ctheatrate`.

### The artifact

`data/raw/nuclear-availability-NEISO.csv` — 3,288 rows = 3 reactors x 1,096
days. The **entire** NEISO nuclear fleet, on NEISO's own crosswalk (rule 25):

| NRC unit | EIA (plant, unit) | model pmax | zone |
|---|---|---|---|
| `Millstone 2` | (566, 2) | 863.43 MW | Connecticut |
| `Millstone 3` | (566, 3) | 1,244.97 MW | Connecticut |
| `Seabrook 1` | (6115, 1) | 1,247.00 MW | North |

3,355.4 MW ≈ **22 % of NEISO energy**. Pilgrim (2019), Vermont Yankee (2014),
Maine and Connecticut Yankee carry neither NRC rows nor fleet units, so the
crosswalk is complete. Coverage **365 / 366 / 365** days; **all 36 months
reconcile inside `WEDGE_TOL`** (worst −0.70 %), so — like NYISO, unlike
PJM/CAISO — **no month is dropped**. `--check` reproduces byte-for-byte.

**The entire code delta is a three-row identifier crosswalk.** No `src/` change
was needed: the `arrays.py` seam and the `outages.py` loader were already
ISO-generic. The three reconciliation constants (`EVENT_RAW_MAX` 0.90,
`SCALE_CLIP` 1.25, `WEDGE_TOL` 0.01) are inherited **frozen** from the ERCOT
deriver and were not swept (rule 23).

### What it actually fixes

The smear derates every reactor by one fleet-month factor. In **2025 Millstone 2
never fell below 94 % and Seabrook below 47 % while Millstone 3 took a full
refuel** — yet the Apr/May anchor (0.75 / 0.77) derates all three alike. Since
NEISO nuclear is `nuclear_mustrun`-pinned at 0.999+ D-2 share, the overlay
moves the **must-run floor itself** hour-by-hour (`min_gen` clipped to
`pmax × availability`) — the documented application order.

### Every pre-registered gate PASSES

| gate | result |
|---|---|
| G-1 flag fidelity | **PASS** — arm `true`, control `false`; 3 reactors matched, 1.000 date coverage |
| G-2 control integrity | **PASS** — recipe diff `{}`, 1 new-default field, flag off |
| G-3 liveness (> 50 MW) | **PASS** — max \|Δ class MW\| **1,129 / 1,842 / 1,265**, 20-37× the floor |
| G-4 single delta | **PASS** — `['nuclear_unit_availability']`, proven by construction |
| G-5 year span | **PASS** — both `[2023, 2024, 2025]` |
| P-1 energy neutrality (KILL) | **PASS** — −0.0079 / −0.0006 / −0.0313 TWh vs 0.05 tol |

Both bundles solved at the **identical frozen HEAD `464817e`**, `dirty: False`.

### Result

**ZERO criterion status changes** across all nine criteria vs the same-HEAD
control. Determination **CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered C3c
caveat**, **C1 all 12/12 · free 8/8**, DOF **12 entries, `n_residual`
UNCHANGED at 5**. C3c **bit-identical** (model 0 h vs RT 15 / 8 / 20 h — an
energy-neutral re-arrangement cannot create a tail), so the `price_tail` ledger
entries carry verbatim and **no new ledger slot is spent**.

**The fit improves slightly:** scored C1 total absolute error **2.602 → 2.521
TWh** across the 12 scored rows (2023+2024; the six 2025 rows are SKIPPED on a
preliminary EIA-923 vintage, 57 % plant reporting). Mean λ −0.025 / −0.024 /
−0.019 $/MWh. D-2 and D-4 PASS in both arms with every forced share moving
≤ 0.005.

### Reported against interest

* **Pre-registered prediction P2's ZONAL half did NOT materialize.** Millstone
  and Seabrook sit in different zones, so I predicted Connecticut-vs-North
  separation. **All four NEISO zones clear at an identical mean λ** in control
  and arm alike — no binding internal congestion at annual-mean grain. Only
  P2's **timing** half is confirmed.
* **D-1 fails in BOTH arms on the SAME class/year set** (COAL_BIT 2023-2025,
  ST_GAS 2023) — pre-existing, not a regression, and C7 `shape` is SKIPPED for
  NEISO. Within it 2024 COAL_BIT `profile_r` improves 0.617 → 0.753 while 2023
  slips 0.600 → 0.588.
* **The C1 gain is a net, not a uniform improvement**: 7 rows improve, 6
  worsen, 5 unchanged; all moves are small.

### Why this is a keeper

A measured physical input (rule 13 `[R-MEASURED]`) replaces a fleet-month smear
on 22 % of the ISO's energy, with **zero fitted parameters**, every gate
holding, no criterion regressing, and the fit slightly better. Rule 1
`[R-STRUCT]` / rule 14 `[R-ACCURATE]`: structural fidelity improves and the
level is untouched — the EIA-923 anchor owns it.

---

## §3 — process note (recorded because it cost compute)

The arm was killed mid-solve and relaunched on a **misread of a duplicate log
line**. `bins_to_fleet` builds its own `FleetArrays` from the thermal-tranche
list alone and logs `nuclear unit-availability overlay: 0 reactor(s)` **before**
the runner's dispatch-fleet build logs the real `3 reactor(s)`. Reading only the
first occurrence looks exactly like the ERCOT-146 inert-flag signature. **Read
the LAST occurrence.** Cost ~5 minutes of compute; no effect on correctness.
Worth a follow-up: the `bins_to_fleet` call site should not emit that line at
all, since its fleet can never contain a reactor.

## §4 — DOF ledger (rule 21 `[R-DOF]`)

**Zero free parameters added.** One `measured` entry
(`nuclear_unit_availability[NEISO]`); `n_entries` 11 → 12, **`n_residual`
unchanged at 5**. The crosswalk is an identifier map, not a tunable; the three
reconciliation constants are inherited frozen. Per rule 23 the extract
re-derives only when a new NRC annual file lands.

## §5 — governance

Years 2023-2025 only; the holdout spend freeze is ACTIVE and NEISO's locked test
is already SPENT (2026-07-07), never re-grantable. Both bundles registered
(rule 15) — control and keeper alike. Matrix cells updated with evidence
citations (rule 28b) and the NEISO header re-stamped. `audit_keepers --iso
NEISO`: **0 failures, 0 warnings**.

**Open / next.** (1) **NEISO CC_CHP capacity basis** — Kendall Square (EIA 1595)
meters 278-299 MW against a 206.0 MW model pmax; a fleet/nameplate lane inside
the miso-95 provenance-orphaned column, and the prerequisite for any future
CC_CHP host-steam floor. (2) §5.6 items 1/2 (C3c DA-bid depth, import-side
scarcity) still require their own owner charter. (3) Item 4 (NG:PS hydro time
split) and item 5 (STEP 3 seam) unchanged.

