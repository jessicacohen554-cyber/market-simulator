# FINDING — nyiso-114: the per-family reserve dual is now persisted, and it corrects the prior session's attribution

**Date:** 2026-08-03 · **Scope:** NYISO 2023–2025 (plus a six-ISO census) ·
**Keeper:** `2026-08-02-nyiso-113-li-locational` — **UNCHANGED by this session**
· **Pre-registration:** `PREREG-nyiso114-reserve-family-sidecar-2026-08-03.md`
(committed and pushed before either solve).

---

## §1 — the instrument: `hourly/reserve_family_<year>.parquet`

nyiso-113 §8 recorded a standing gap in **all six ISOs**: no committed bundle
anywhere persisted a per-family reserve dual.
`DispatchResult.reserve_price_by_family` is `(T, n_fam)` in memory (it is what
`results/scarcity.py` consumes) and was discarded at persist time, while
`system_<year>.parquet`'s `reserve_price` is the per-hour **sum across
families**, written **identically into every zone's rows**. It has no zone index
and no family index. A gate specified on that column reads inert **by
construction** — which is exactly how nyiso-113's own K3/K4 gates came to be
invalid.

Now persisted, long form, one row per (family, hour):

| column | meaning |
|---|---|
| `family`, `reserve_class` | the family's name and eligibility class |
| `dual` | that family's own balance-row shadow price |
| `requirement_mw` | its hourly requirement (from the `ReserveDesign` — the LP reports duals *positionally*; only the design knows which column is `li_30min_total`) |
| `held_mw` | the reserve MW the family actually held |
| `shortfall_mw` | its cleared ORDC shortfall MW |

Two of these are new LP outputs. `shortfall_mw` partitions the family-major ORDC
block by an `(n_steps, n_fam)` membership matmul (preferred over `reduceat`,
whose boundaries collide for a family carrying zero ORDC steps). `held_mw` is
taken from the **balance row's own activity** minus that shortfall, rather than
by re-summing R columns per family — the row's coefficient structure is
layout-dependent (per-class blocks, storage RS columns, per-generator product
masks, ERCOT's all-class family), and each of those five layouts is a chance to
attribute one family's MW to another's name. Row activity is `Σ_{z∈f} R + Σ_{k∈f}
ORDC` by construction, so it is exact and layout-independent.

Together they make the LP row itself **checkable from the bundle**: `held +
shortfall ≥ requirement`, tight exactly where the family prices, with the slack
saying how far a non-binding family was from binding. Without `held_mw` the
pre-registered G3 gate would itself have been unmeasurable from committed
artifacts — the same class of error as the K3/K4 instrument, caught before it
shipped.

**It is an instrument, not a lever.** No `ScenarioConfig` field, no CLI flag, no
LP row, column or cost; every value is read off the already-solved primal.
Rule 24 `[R-REGISTRY]` is not engaged (there is no tunable) and rule 21
`[R-DOF]` adds nothing (no free parameter). The writer **refuses to emit a
frame** when the design's family count disagrees with the solved dual's column
count — no sidecar beats a mislabelled one. **12 KB per ISO-year** (NYISO,
9 families × 8,760 h), so a keeper bundle carries it freely. **Not backfilled**
— written going forward; see §2 for why a backfill by re-solve would not be
faithful anyway.

## §2 — the confirmation run, and the gate that failed

Arm `results/calibration/nyiso114_lilocational_confirm` — a **zero-delta** replay
of the nyiso-113 keeper across 2023–2025, run only to emit the sidecar.

| gate | result |
|---|---|
| **G1** replay fidelity | **FAIL** — see below. Pre-registered as a gate that changes how everything else is *labelled*, not whether it is reported. |
| **G2** instrument well-formed | **PASS** — 9 families × 8,760 rows per year, no NaN, all three years |
| **G3** LP row identity | **PASS** — `held + shortfall ≥ requirement` everywhere, tight in exactly the binding hours |
| **G4** sum identity | **PASS** — `Σ_f dual == system reserve_price` to ≤ 6.1e-06 in all three years |
| **G5** write-invariance | **PASS** — see the attribution below |
| **G6** span | **PASS** — 2023–2025 in one bundle; no year outside 2023–2025 touched |

**G1 fails, and this is exactly the risk §2 of the pre-registration named.** The
replay does not reproduce the committed keeper: max |Δprice| ≈ $9.0–10.6/MWh,
27–46 % of zone-hours differing, mean LMP `+0.012 % / +0.012 % / +0.055 %`, and
class energy moving 0.018–0.072 TWh as a CT_PEAKER ↔ ST_GAS swap with the total
conserved. That is a marginal-tie reshuffle, not a mechanism change — the
caiso-155 P0-pattern-bridge vertex dependence, on a keeper that arms
`nyiso_gas_commitment_bridge`.

**The pre-registered kill K-A required attribution, not assertion, so it was
measured.** A second re-solve of 2024 was run in a worktree at this session's
**base commit** — the same code the replay ran, minus this session's entire diff
— against the same data root:

| comparison (2024) | max abs Δprice | differing zone-hours | mean LMP Δ |
|---|--:|--:|--:|
| replay **with** the sidecar diff vs keeper | 10.5637 | 18,630 / 52,560 | +0.0122 % |
| **base code, no sidecar diff** vs keeper | **10.5637** | **18,630 / 52,560** | **+0.0122 %** |

The divergence is **identical with and without this session's code**. It is
attributable entirely to the 58 commits that landed on main between the keeper's
solve basis (`0d49cc4a`) and this session's base (`5885248`); the environment is
byte-identical (same Python, HiGHS 1.14.0, numpy, scipy, pandas, pyarrow).
**K-A does not fire.** Every §3 result is therefore reported as measured on a
**re-solve of the keeper recipe, not on the keeper bundle** — and the keeper's
own committed artifacts are untouched.

**Consequence for backfill, and a standing caveat for every ISO.** A keeper that
arms a P0-run-pattern mechanism cannot be re-solved into byte-identity once main
has moved. Backfilling the sidecar onto existing keepers would therefore mint
numbers that are *near* the keeper but not the keeper. The sidecar is written
going forward only, and each ISO's next solve mints it automatically.

## §3 — what the instrument shows (measured on the re-solve)

**Hours in which each reserve family's own dual is positive:**

| family | class | requirement | 2023 | 2024 | 2025 |
|---|--:|---|--:|--:|--:|
| `nyc_10min_total` | 1 | 0 → 500 MW | **17** | **6** | **29** |
| `nyc_30min_total` | 0 | 0 → 1,000 MW | **8** | **6** | **10** |
| `seny_30min_total` | 0 | 0 → 1,800 MW | **2** | 0 | **8** |
| `li_30min_total` | 0 | 270 / 540 MW | 0 | 0 | **5** |
| `li_10min_total` | 1 | 120 MW | 0 | 0 | 0 |
| `nyca_10min_spin` | 1 | 655 MW | 0 | 0 | 0 |
| `nyca_10min_total` | 1 | 1,310 MW | 0 | 0 | 0 |
| `nyca_30min_total` | 0 | 2,620 MW | 0 | 0 | 0 |
| `east_10min_total` | 1 | 1,200 MW | 0 | 0 | 0 |

Two facts here were previously unobservable from any committed bundle in any
ISO. First, **NYISO's binding reserve constraint is overwhelmingly the NYC
locational pair** — not a system requirement. Second, **every NYCA-wide family
is slack in every hour of all three years**, which independently corroborates
nyiso-110's "the aggregate rows never bind" conclusion on a direct measurement
rather than an inference from the summed series.

### Predictions, scored as pre-registered

| id | prediction | verdict |
|---|---|---|
| **P1** | `li_30min_total` binds in ≥ 2025 h4193–4195, h4217–4218 | **CONFIRMED, EXACTLY** — it binds in those five hours and in no other hour of any year |
| **P2** | every hour with a positive system reserve dual is attributable to a named family | **CONFIRMED** — no unattributed hours |
| **P3** | `li_10min_total` never binds | **CONFIRMED** — 0 hours, all three years |
| **P4** | no LI family binds in 2024 | **CONFIRMED** |
| **P5** | the LI families bind in exactly 2 hours of 2023 | **REFUTED** |

**P1 is the strongest result.** nyiso-113 predicted those five hours *ex ante*
from Zone-K thermal headroom against the on/off-peak-stepped requirement, before
any per-family dual existed. The family's own dual binds in exactly that set —
`{4193, 4194, 4195, 4217, 4218}`, no more and no fewer — with shortfalls of
18.9–129.7 MW and duals of $3.13–6.25. The headroom screen was right, and it is
now confirmed directly rather than inferred.

**P5 is refuted, and the refutation is the point of the instrument.** nyiso-113
§7 reported that "the solved system reserve dual moves in 2 hours of 2023" and
attributed those hours to the LI mechanism. The per-family dual says the LI
families bind in **zero** hours of 2023; the two hours were **`seny_30min_total`**
(dual $62.50, shortfall 61.3 MW). That is an attribution error in the prior
session's *reading of a summed series* — not a defect in the keeper, whose
promotion rested on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` and not on those
two hours. It is exactly the error class the sidecar exists to make impossible,
and it appeared in the first bundle that carried the sidecar.

## §4 — the rule-28(c) census, all six lanes, and a ratchet

`scripts/probes/_nyiso113_matrix_gap_sweep.py` is promoted to a standing tool,
`scripts/mechanism_matrix_gap_sweep.py`, parameterised by `--iso` (all six by
default) and selecting bundles by their config's own `iso` field rather than by
name prefix. Measured, ISO-scoped fields:

| ISO | family fields | **absent from matrix** | prose-only | **armed on keeper, no cell** |
|---|--:|--:|--:|--:|
| ERCOT | 84 | **64** | 7 | **35** |
| CAISO | 61 | **39** | 3 | **23** |
| PJM | 35 | **21** | 2 | **8** |
| NEISO | 20 | **15** | 0 | **10** |
| MISO | 25 | **12** | 5 | **10** |
| NYISO | 39 | **10** | 1 | **9** |

**161 absent, 95 armed-but-cell-less.** CI could see none of them: the
`check_mechanism_matrix.py` diff gate fires only on fields **added in the same
PR**, so everything predating the gate is structurally invisible. This is a
standing blind spot in every ISO column, and the nyiso-112/113 finding was a
symptom of it, not a NYISO accident.

**NYISO's column is CLOSED this session — 0 absent, 0 prose-only, 0
armed-no-cell.** Its nine were all `nyiso_gas_bridge_*` sub-scalars (the measured
CC/ST/CT min-load fractions and min-run hours, plus the boolean legs), registered
by naming them **literally** in the `gas_commitment_bridge` row's `def` — the
checker's own documented escape hatch, since a sub-scalar belongs on its family's
row and not on one of its own. `nyiso_iroquois_winter_spread`, which appeared
only in the matrix file's **header comment** and in no row at all, now rides
`gas_hub_basis_overlay`.

**The other five columns are their own lanes' work.** Rule 25 / 28(d) forbid one
lane minting verdict-bearing rows for markets it did not measure, and a census
can mint a `U` and nothing more. What stops the backlog **growing** is a
**ratchet**: `docs/codebase-site/data/mechanism-matrix-gaps.json` enumerates the
146 known-absent fields per ISO, and `check_mechanism_matrix.py` now **fails**
any PR whose ISO-scoped field is in neither the matrix nor that baseline. The
list can only shrink; `--write-baseline` refuses a partial-ISO write, which would
silently drop the un-swept ISOs' entries. The gate is stdlib-only, matching the
checker's existing contract, and its stem matching is **substring, not `\b`** —
a stem sits mid-identifier in the row that owns it (`gas_bridge_startup` inside
`nyiso_gas_bridge_startup`), where `\b` never matches; with `\b` the ratchet and
the sweep disagreed on seven fields and the baseline could never be satisfied.

## §5 — the two hygiene items, traced and closed

**(a) `ct_committed_hr_override` / `ct_econ_hr_override` / `ct_peak_hr_override`
= 1.1 / 1.2 / 1.4 — DELETED (rule 26 `[R-DELETE]`).** nyiso-113 §6 filed these as
an open trace item, deliberately asserting nothing. Traced:

1. The triple has exactly **two** readers (`offer_curves.py`,
   `fleet/assembly.py`). Both sit inside the `else:` of `if offer is not None:`
   and both are additionally gated on `group == "CT_CHP"`.
2. For `CT_CHP`, `_offer_curve_for_group` takes **no plant-code branch** — the
   CT_PEAKER / ST_GAS / CC_REGULAR special cases cannot match — so it resolves to
   `curves.get("CT_CHP") or None`, plant-code-independently.
3. **All 119 committed bundles across all six ISOs** arm the triple at
   1.1/1.2/1.4, and **all 119** carry a truthy `offer_curve_by_group["CT_CHP"]`.

So the `else` branch never executes and the triple is **reachable on zero
bundles in zero ISOs**. `backcast_config`'s own comment already said "these are
INERT" — and a knob documented dead that still parses is precisely the re-armable
answer key rule 26 forbids: the CT_CHP curve is all-1.0, so any future arm
dropping CT_CHP from the offer map would have **silently re-armed** 1.1/1.2/1.4.
Deleted at every site, including the `CT_ECON/PEAK_HR_OVERRIDE_DEFAULT` constants
and the D-9 row in `legitimacy_diagnostics.py`.

**Rule 26 was made affordable rather than expensive.** Deleting a
`ScenarioConfig` field moves the default cache key, orphans every cached run, and
reddens six pinned-literal tests — whose only remedy is re-pinning the literal,
the fix `check_cache_key_registration.py`'s own docstring names as **wrong**. So
deletion now routes through `_CACHE_KEY_RETIRED_FIELDS`: a deleted field is
re-inserted at its historical default **inside `cache_key()` only**. Hash-only,
unassignable, unreadable by any solve path — it cannot be re-armed, which is the
failure mode rule 26 targets. All six pinned-key tests stay green with no literal
touched, and no cache is orphaned. This is the mirror of the existing
`_CACHE_KEY_OPTIONAL_FIELDS`, which keeps the key stable when a field is *added*.

**(b) `caiso_ra_min_load_frac = 0.26` — now CAISO-SCOPED (rule 25
`[R-ISO-SCOPE]`).** Confirmed inert outside CAISO: every reader
(`pipeline/commitment.py:207` and `:1582`) sits behind `caiso_ra_mustoffer and
iso == "CAISO"`, and that flag is `False` on every non-CAISO bundle. But it was
assigned unconditionally in `backcast_config`, so a **CAISO-fitted** value rode
the recorded recipe of **all 119 bundles in all six ISOs** — the exact channel
rule 25 exists to close, re-arming the moment any other lane tries the RA bridge
and carrying CAISO's measured CC turn-down into a fleet it was never measured on.
Non-CAISO now records the neutral shipped 0.40; CAISO is unchanged at 0.26.

## §6 — C3c: what sets the 2024 Long Island pin

nyiso-113 named the 2024 `$297.538777` pin a knife-edge and asked what sets it.
Measured on a 2024 re-solve carrying the unit-hourly and network sidecars:

* **The binding limit is BOTH Long Island import paths at once.**
  `NYC>Long_Island` sits at **275.0 / 275.0 MW** and
  `NYISO_external>Long_Island` at **1200.0 / 1200.0 MW** in all three pinned
  hours (h4528–4530). Zone K is fully import-saturated; the mainland clears at
  **$72.11–74.57** in the same hours.
* **The pin is energy-side, not reserve-side.** `reserve_price` is **0.0** in all
  three hours, and §3 confirms no LI reserve family binds anywhere in 2024.
* **The marginal unit is `7146_1`, an OIL tranche** — 68.93 of 73.80 MW, the
  **only** part-loaded generator on Long Island out of 132 tranches and 106
  running. $297.538777 is that tranche's offer rung. The neighbouring
  `$279.966487` rung (h4527, h4531) is a *different* unit,
  `CT_PEAKER_Long_Island_p2511_peak`.
* **The model is not out of Long Island supply at the pin.** **596.9 MW sits
  idle** at the annual peak-price hour — 561.6 MW of oil across 12 tranches plus
  35.3 MW of demand response — all offered above the marginal rung.

**Therefore 2024 is not a missing-mechanism year.** The same fleet and the same
offer curves reach **$503.74 in 2023 and $489.62 in 2025**, so the Long Island
ladder demonstrably extends far above $300; 2024's tightness simply never calls
the next oil rung. Closing 2024's C3c would require either Long Island genuinely
tighter than the model has it (a load / import / availability question), or a
**different oil offer level** — and the second is a residual tune that rule 1
forbids unless it arrives from measured oil-offer data. **No lever is proposed
here**; the brief asked what sets the pin, and this is the answer.

## §7 — governance

* **Keeper UNCHANGED** at `2026-08-02-nyiso-113-li-locational`. This session
  promotes nothing, demotes nothing and re-keys nothing. The confirmation arm is
  registered as a **diagnostic**, explicitly not as a keeper candidate: G1 shows
  it is a re-solve of the recipe, not the keeper bundle.
* **Rule 16** — 2023, 2024, 2025 in one bundle for the confirmation arm. The
  2024-only base-attribution run is a throwaway kill-gate control and is **not
  registered as a keeper** (rule 16's explicit allowance for a single-year
  diagnostic probe).
* **Rule 22** — the holdout spend freeze is ACTIVE and untouched. No year outside
  2023–2025 was solved, scored, or read; no marker spent or requested.
* **Rule 28(b)/(c)** — two rows added (`reserve_family_dual_sidecar`,
  `matrix_gap_census`), the `gas_commitment_bridge` and `gas_hub_basis_overlay`
  `def`s extended; no existing cell verdict touched.
* **Rule 27** — every push blob-verified against local (line count + hash) for
  every file ≥ 300 lines.
* **Unrelated pre-existing breakage repaired, and reported as such:**
  `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` was added to `config/fuel_trajectories.py`
  without the paired `constants.py` facade re-export, leaving
  `test_constants_facade`'s frozen inventory **red on main**. Restored to
  contract (inventory entry + re-export), no value touched. Five further
  failures in `tests/scoring/test_ff_readiness_battery.py` and
  `tests/unit/data/test_outages.py` were verified pre-existing on this session's
  base and are **left alone** — they belong to their own lanes.
* **Also found and NOT introduced here:** unresolved merge-conflict markers were
  committed inside three NYISO bundles' JSON (including the keeper's
  `metrics.json` and `legitimacy_diagnostics.json`) by a rename-conflict in
  caiso-158. Already repaired upstream by **caiso-159** (`9dacf6a`), which landed
  after this branch's base; picked up by rebasing.
