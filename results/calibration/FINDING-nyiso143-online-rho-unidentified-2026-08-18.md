# FINDING nyiso-143 — the NYISO online-gated reserve family cannot be adjudicated: its single decisive coefficient `online_rho` is an unidentified hard-coded fallback, and the matrix's "inert by construction" ground for closing it is FALSIFIED

**Session nyiso-143, 2026-08-18. NO SOLVE SPENT on this object, no mechanism
written, no `ScenarioConfig` field added, keeper unchanged.** Measured entirely
from the committed keeper `2026-08-17-nyiso-142-stackdup` (its run payload and
its `meta.json`-replayed fleet, `run_year(fleet_only=True)` — no LP) and from
the committed source.

Probes: `scripts/probes/_nyiso143_nyc_spin_liveness.py`,
`scripts/probes/_nyiso143_online_rho.py`. Records:
`results/calibration/_nyiso143_nyc_spin_liveness.json`,
`results/calibration/_nyiso143_online_rho.json`.

---

## 0. WHAT THE SESSION WAS ASKED TO DO, AND WHAT IT FOUND INSTEAD

The nyiso-143 handoff expected `nyiso_synchronised_reserve` to be closable
without a solve — *"the matrix already argues it is inert by construction …
That is probably enough to move it `U → I` or `G` WITH A CITATION."*

**It is not, and the argument is wrong.** Reported against the session's own
convenience: the cell **stays `U`**, and the NYISO lever queue **gains** a
blocking object rather than losing one.

## 1. THE MATRIX'S STANDING CLAIM

`docs/codebase-site/data/mechanism-matrix.js`, row
`nyiso_synchronised_reserve`:

> it is a construction of exactly the class-2 online-gate family nyiso-110
> measured EXHAUSTED at NYISO: the class-2 row is an **AGGREGATE** rho\*output
> row that reserve-eligible hydro's own 2-5 GW of output keeps slack in every
> hour, which is why the nyiso-110 spin-online arm solved INERT.

## 2. THE CLASS-2 HEADROOM ROW IS PER-ZONE, NOT AGGREGATE

`src/market_sim/model/lp/reserve_rows.py`, the
`headroom_products is None and gated[h]` branch, writes **one row per zone**:

```
R[c,z] - rho * sum_{eligible g in z} P[g] <= 0
```

The two flags differ in **which families consume it**:

* `nyiso_spin_reserve_online` (cell `I`, solved inert at nyiso-110) gates the
  **published** families `nyca_10min_spin` / `east_10min_spin`, whose zone
  masks span NYCA / East. Their balance rows sum `R[2,z]` over those zones, so
  upstate hydro's output **does** enter — the aggregate reading is correct
  **for that arm**.
* `nyiso_synchronised_reserve` adds `nyc_spin_online`, whose zone mask is
  **NYC alone** (`reserves/spec.py`: `nyc_idx = (i for z, i in zone_index if
  z == "NYC")`). Its requirement can be backed **only** by NYC-zone online
  quick-start output. NYISO has **no NYC hydro** — the fleet carries 154 / 147
  / 3 hydro rows, none of them in NYC.

**So the inertness that nyiso-110 measured does not transfer to this family.**
The verdict was read across two structurally different zone masks.

## 3. THE FAMILY IS LIVE — measured on the keeper's own dispatch

Requirement: `NYISO_SPIN_FRACTION (0.5) × nyc_10min_total (500 MW)` = **250 MW
static** (`results/scarcity.py::nyiso_spin_requirement_mw`).

NYC online quick-start output, summed from the keeper's committed per-plant
payload over the 11-13 NYC `CT_PEAKER` / oil slices:

| year | min | p50 | max | `rho*` = 250 / min | binding h at `rho = 1.0` | worst deficit |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 79.1 MW | 212.2 | 1,593.4 | **3.1588** | **7,911 (90.3 %)** | 170.9 MW |
| 2024 | 86.3 MW | 140.2 | 1,716.8 | **2.8981** | **7,159 (81.7 %)** | 163.7 MW |
| 2025 | 82.9 MW | 248.7 | 1,754.7 | **3.0152** | **4,669 (53.3 %)** | 167.1 MW |

The family is slack in every hour **iff `rho >= rho*`**, i.e. iff `rho` sits in
the top quarter of its own admissible `[0.5, 4.0]` clip band. At the clip
ceiling 4.0 it binds in **0** hours; at 1.0 it binds in a **majority** of them.
The whole verdict is one coefficient.

## 4. THAT COEFFICIENT IS NEVER IDENTIFIED — it is the hard-coded fallback

`reserves/spec.py` derives it as *"the fleet's own `(pmax-pmin)/pmin` at min
load — a fleet property read off the same arrays the LP dispatches, not a tuned
coefficient (rule 5 `[R-NO-MAGIC]`)"*, guarded by
`valid = (pmin > 0) & (pmax > pmin)` with `else: online_rho = 1.0`.

Rebuilt on the keeper's own fleet:

| year | LP rows | rows with `pmin > 0` | quick-start rows | of those, valid for rho | `rho` |
|---|---:|---:|---:|---:|---:|
| 2023 | 851 | **4** | 363 | **0** | **1.0 (fallback)** |
| 2024 | 849 | **4** | 355 | **0** | **1.0 (fallback)** |
| 2025 | 705 | **4** | 211 | **0** | **1.0 (fallback)** |

**Only 4 of 851 LP rows carry `pmin > 0` at all** (2,393 MW, the nuclear
block), and **not one of them is quick-start eligible**. Under the keeper's
`plant_level_fleet` + `use_campd_bins` representation, must-run behaviour rides
`min_gen`, not `pmin` — so `pmin` is identically zero across the merchant
fleet and the declared identification path is **dead code for this ISO**. The
value that decides the mechanism is the literal `1.0` in the `else`.

**The same is true of the rule-19 sibling.** The obligation branch
(`nyiso_incity_commitment_obligation`) computes `rho` the same way over
`quick_elig | ST_GAS`: 451 / 443 / 299 rows, **0 valid**, `rho = 1.0`
fallback, every year.

## 5. WHY THIS BLOCKS BOTH MECHANISMS — rule 21, not a fit judgement

A mechanism whose behaviour swings from **provably inert** to **binding in
90 % of hours** across the admissible band of a coefficient that is *never
measured* is a mechanism with a **free parameter in disguise**. Arming either
flag today would put an unidentified scalar on the critical path of a
downstate commitment driver — which rule 21 `[R-DOF]` forbids
(*"a residual that can only be closed by a tuned value is an open root-cause
issue, not a parameter"*) and rule 5 `[R-NO-MAGIC]` forbids independently.

**This is a root-cause finding, not a rejection.** The family is not refuted:
NYISO's downstate 10-minute requirement genuinely is an online-gated
obligation, and the mechanism is a fair representation of it. What is missing
is `rho`'s identification on a fleet whose `pmin` is structurally zero — which
needs a measured 10-minute-headroom-per-MW-online statistic from CAMPD ramp
conduct or NYISO's own published capability data, derived under rule 23
`[R-FROZEN-DERIVE]` from source data, not from a residual.

## 6. DISPOSITION

* `nyiso_synchronised_reserve` — **stays `U`.** The matrix note's inertness
  ground is corrected in the NYISO shard. It is NOT closable "without a
  solve", and it is NOT closable *with* one either until §5 is answered.
* `nyiso_incity_commitment_obligation` — **stays `U`**, blocked on the SAME
  coefficient, in addition to needing its own solve. Note the two are mutually
  exclusive by a hard `ValueError` (rule 19), so **one identification unblocks
  the pair and only one of them may ever be armed.**
* `nyiso_spin_reserve_online` — **`I` STANDS, untouched.** nyiso-110 solved it
  and measured it inert; §2 explains why that verdict is sound for the
  published NYCA/East families and does not extend to the NYC-scoped one.
* **Nothing here re-opens `diurnal_price_amplitude`** (NYISO `G`), and nothing
  here is a price-amplitude claim.

## 7. A NOTE FOR EVERY OTHER ISO'S LANE — flagged, NOT actioned (rule 25)

`online_rho`'s `pmin`-based identification is **not NYISO-specific code**. Any
ISO whose keeper runs a tranche/binned fleet with `pmin = 0` will hit the same
`else: online_rho = 1.0` fallback if it ever arms an online-gated reserve
class. This session measured **only NYISO** and asserts nothing about the
other five; each lane must measure its own fleet. No other ISO's shard is
touched.
