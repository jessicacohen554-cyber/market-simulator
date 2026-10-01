# PRECHECK / PREREG — caiso-162: CAISO per-year LCT pocket import caps

**Session** caiso-162 · **Date** 2026-08-03 · **Branch**
`claude/caiso-per-year-import-caps-1gq4j0` · **Base** `de504ad` (main, with
caiso-161 PR #3368 merged at `b3c8f91`)

**Mechanism** `ScenarioConfig.caiso_per_year_import_caps` · matrix row
`lcr_tsl_published`, CAISO cell `U` (minted by the caiso-161 census, never
adjudicated) · **Incumbent keeper** `2026-08-03-caiso156-meter-screen-b`
(`results/calibration/caiso156_meter_screen_B`), determination
CALIBRATED-WITH-CAVEATS, 2 of 3 non-protective ledger slots spent.

This document is written and pushed **before any LP is solved**. Every number in
§2–§4 is measured from committed artifacts only (no solve).

---

## 1. The arm

Single delta on the caiso156 keeper recipe, applied through
`scripts/replay_keeper.py --set caiso_per_year_import_caps=true`. Nothing else
moves; the replay driver reproduces the keeper's `meta.json` kwargs exactly, so
the config delta is **structurally** one field rather than an asserted one.

`iso_configs.py:355-356` bakes the two internal SP15-pocket import links at
CAISO's **2023 tightest-year** published LCT import capability and uses it in
every solve year:

```
_LA_BASIN_IMPORT_CAP_MW = 12008.0   # link 4: SP15_rest -> LA_BASIN (one-way)
_SDGE_IMPORT_CAP_MW     =  1436.0   # link 5: SP15_rest -> SDGE     (one-way)
```

The published per-year LCT rows, re-read this session from
`data/raw/capacity-deliverability/caiso/caiso.csv` via
`data.local_capacity.load_lcr_parameters` (`import_cap = peak_load −
requirement`):

| pocket | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| LA Basin (19,537−7,529 / 19,637−4,413 / 19,297−4,123) | **12,008** | **15,224** | **15,174** |
| San Diego/IV (4,768−3,332 / 4,908−2,834 / 4,780−2,709) | **1,436** | **2,074** | **2,071** |

So the static bake under-states 2025 pocket import capability by **3,801 MW**
(LA_BASIN 3,166 + SDGE 635). Under-stating pocket import capability forces
dearer in-pocket generation and **lifts** the pocket price — the same sign as
the open C3a-2025 defect. `scenarios.py:8955` and the SP15-split scope doc
(`docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md`,
"Import-cap values") both name per-year as **the deferred end state** of the
2026-07-09 split; this arm is that deferral being closed.

### 1a. NO-TUNING CLAUSE

**Zero free parameters.** Every value is the published LCT row read through
`load_lcr_parameters`, on the literal `peak_load − requirement` convention —
**never** the reserve-margin gross-up. No value may be swept, blended,
interpolated, rounded or adjusted; there is no knob in this arm to sweep. A year
with no published row keeps its static default (already the code's behaviour,
`apply_caiso_local_import_limits` returns `iso_config` unchanged). The DOF
ledger gains **no** entry (rule 21).

### 1b. RULE 19 `[R-ONE-MECH]` CHECK — no double-count with the deliverability seam

The keeper runs `capacity_deliverability_limits=True` and
`local_capacity_constraints=False` (verified in the keeper's
`run_config.json/scenario_config`). Those two mechanisms and this arm write
**disjoint objects**:

- `apply_deliverability_seam_limit` (`import_nodes.py:696`) rewrites
  `iso_config.interface_limits` — specifically the one `InterfaceLimit` *whose
  every link originates at the import node* `WECC_import`. That is the
  **external WECC seam** (CAISO branch-group MIC).
- `apply_caiso_local_import_limits` (`interchange/caiso.py:1782`) rewrites
  `links[].ttc_mw` for `SP15_rest→LA_BASIN` and `SP15_rest→SDGE` — **internal**
  pocket links, neither of which originates at `WECC_import`, and which carry no
  `InterfaceLimit`.

Different field (`interface_limits` vs `links[].ttc_mw`), different boundary
(external seam vs internal pocket), disjoint link sets. **No double-count; rule
19 clean.** The seam cap is untouched by this arm, so total WECC import
capability into CAISO is unchanged — only its *distribution* past the SP15
pocket boundary moves.

Cache safety: `ScenarioConfig.cache_key` hashes config fields, and the delta
**is** a config field, so the arm cannot collide with the keeper's persisted
tree (the caiso-158 §4a trap needs an input-bytes-only delta; this is not one).

---

## 2. PRE-CHECK — do links 4/5 actually bind? (no LP spent)

Run on the keeper's committed hourly sidecars
(`results/calibration/caiso156_meter_screen_B/hourly/system_<year>.parquet`,
P1). The sidecars carry zonal `price` and `demand` but **no per-link flow
column**, so binding is identified from price separation, which for a **one-way**
import-limited link is exact:

- `price[POCKET] > price[SP15_rest]` ⟺ the **TTC upper bound binds** (imports
  into the pocket are rationed). These are the only hours loosening the cap can
  touch.
- `price[POCKET] < price[SP15_rest]` ⟺ the **flow ≥ 0 lower bound** binds
  (pocket surplus that the one-way link cannot export). Raising the TTC cannot
  help these hours.
- equal ⟺ interior, link slack.

| year | pocket | TTC-binding h | equal | one-way floor | mean premium when binding |
|---|---|---:|---:|---:|---:|
| 2023 | LA_BASIN | **0** (0.0%) | 8760 | 0 | — |
| 2023 | SDGE | 805 (9.2%) | 7938 | 17 | $8.34 |
| 2024 | LA_BASIN | **37** (0.4%) | 8723 | 0 | $3.89 |
| 2024 | SDGE | 972 (11.1%) | 7229 | 559 | $8.69 |
| 2025 | LA_BASIN | **64** (0.7%) | 8696 | 0 | $4.86 |
| 2025 | SDGE | 1011 (11.5%) | 6994 | 755 | $5.63 |

**The arm survives the kill-before-solve screen** (caiso-74 / caiso-129
precedent): the caps do bind, so it is not inert by construction and it will
produce a non-zero change. But the screen relocates where the binding is, and
that is the load-bearing finding:

> The **LA_BASIN** cap — which carries **83% of the MW loosening** (3,166 of
> 3,801 MW in 2025) — binds in **64 of 8,760 hours (0.7%)**. The 3.2 GW of
> extra import capability the published row grants is capability the keeper's
> dispatch was **already not using** in 99.3% of hours. Almost all of the
> binding that exists is **SDGE**, the pocket with the *small* (635 MW)
> loosening.

## 3. CEILING ON THE C3a MOVE (measured, ex ante)

C3a is the **system load-weighted** mean LMP (`score_crossover.py:507`). A
strict upper bound on what this arm can deliver is obtained by removing the
pocket congestion premium **entirely** — i.e. pretending both caps became
infinitely loose, which is strictly more than the published rows grant:

| year | model load-wtd mean LMP | max removable pocket premium | as % of mean |
|---|---:|---:|---:|
| 2023 | $55.95 | $0.067/MWh | 0.12% |
| 2024 | $37.83 | $0.100/MWh | 0.26% |
| 2025 | **$38.57** | **$0.084/MWh** | **0.22%** |

Baseline C3a-2025 = **+12.2%** (re-measured this session with
`scripts/calibration_verdict.py --run-id 2026-08-03-caiso156-meter-screen-b`,
committed artifacts only). Veto band ±10%. Implied actual ≈ $34.38/MWh; to
reach +10.0% the model mean must fall by **$0.76/MWh**.

> **The arm's absolute ceiling is $0.084/MWh — about 11% of the $0.76 needed,
> and the realised move will be smaller still.** This arm **cannot** clear
> C3a-2025 on its own. That is stated here, before the solve, so the outcome
> cannot be re-framed afterwards as either a success or a surprise.

### 3a. Pass bars, pre-committed

- **PASS (C3a-2025 clears the gate):** C3a-2025 lands inside ±10%. Per §3 this
  is **not attainable** by this arm; recorded for completeness.
- **PARTIAL CREDIT (the arm's real target):** C3a-2025 moves **down** by
  ≥0.05 pp of level with no guard breach. This would confirm the mechanism has
  the predicted sign and is worth carrying on rule-14 grounds.
- **INERT:** |ΔC3a-2025| < 0.01 pp. Still adopted — see §5.
- **ADVERSE:** C3a-2025 moves **up**. Also still adopted — see §5.

### 3b. Governance note the owner asked for (attribution, not re-litigation)

C3a-2025's ledger slot rests on the caiso-141 **A2 pumped-storage data wall**
(no public hourly PS telemetry; Helms + Eastwood = 60.3% of the PS fleet).
**That wall is real and is not challenged here.** The question this session was
asked to settle is narrower: the ledger entry was adopted at caiso-145 when this
import-cap lever was invisible to the matrix, so *could* this arm own part of
the residual the A2 wall is charged with?

**Measured answer: at most 0.22 pp of a 12.2 pp residual — under 2% of it —
and that is a ceiling, not an estimate.** The A2 attribution is **not**
materially undermined by this lever. Recorded so the owner has the number
before any `complete` marker is considered, per the handoff's standing note.

---

## 4. GUARDS (any breach ⇒ report, never tune)

No gate may flip PASS → FAIL. Scored with `scripts/calibration_verdict.py` on
the new bundle:

| gate | incumbent | requirement |
|---|---|---|
| C1 fuel-mix (load-bearing) | PASS (all 12/12, free 8/8) | no flip |
| C2 system volume (load-bearing) | PASS | no flip |
| C3a mean LMP (load-bearing) | CAVEAT (ledgered) | no new ledger slot |
| C3b price duration/shape (load-bearing) | PASS | no flip |
| C3c price tail (supporting) | CAVEAT (ledgered) | no flip; §8 caiso-131 interaction — this arm must not spend C3a-2025's negative headroom |
| C4 dispatch correlation (supporting) | PASS | no flip |
| C6 governance (protective) | PASS | no flip |
| C7 diurnal shape D-1 (protective) | PASS | no flip |
| C8 forced share D-2 (protective) | PASS | no flip |

Additional watch, specific to loosening an import cap: **import volume.** Track
CAISO net imports (TWh) against EIA-930 net interchange. Loosening a pocket
boundary redistributes flow *inside* SP15 and does not raise the WECC seam cap
(§1b), so net ISO imports should be near-unchanged; a material rise would mean
the arm is pulling extra energy across the seam and is a reportable breach.

Ledger budget: 2 of 3 non-protective slots spent. This arm has **zero free
parameters** and introduces **no new caveat**, so it spends **no** slot.

---

## 5. RULE 14 `[R-ACCURATE]` DISPOSITION — stated BEFORE the result

The published per-year LCT import capability is **measured data on the same
convention** as the frozen estimate it replaces, produced by CAISO's own LCT
study, resolvable for any delivery year, and responsive to changed conditions —
so it is admissible under rule 13 `[R-MEASURED]` and preferred under rule 14.

**Therefore, pre-committed:**

- If the published caps make the backcast **worse**, the accurate input
  **STAYS**. The worse fit is a **discovered bug** — the frozen 2023 estimate
  was silently compensating for something else — and this session opens the
  root-cause investigation rather than reverting. There will be **no** revert to
  the static estimate, and **no** burying of the error back inside the input.
- If the arm is **inert**, the accurate input still stays: rule 1 `[R-STRUCT]`
  is explicit that a structurally-correct mechanism is not judged by whether it
  moves the residual. An inert result is registered as `I` on the matrix with
  the §2/§3 measurement as its evidence, and the mechanism remains armed.
- The **only** outcome that would keep the static bake is a guard breach that
  the published data itself cannot explain — and per rule 14 that too would be
  logged as a root-cause investigation, not a silent revert.

## 6. LOYO (rule 22)

A structural mechanism change is scored **leave-one-year-out within 2023–2025**
before any promotion. The zero-delta control below makes 2023 a free LOYO fold.
If C3a moves by ≥1.0 pp of level in any year, a full explicit LOYO is owed
before promotion is even proposed.

## 7. BUILT-IN ZERO-DELTA CONTROL — 2023

2023's published LCT row **equals** the static default (12,008 / 1,436 MW), so
`apply_caiso_local_import_limits` finds `cap == link.ttc_mw` for both links,
sets `changed = False`, and returns `iso_config` **unchanged**
(`interchange/caiso.py:1831-1837`).

> **2023 MUST come back byte-identical to the keeper.** This is the same-head
> zero-delta control (lesson (c) from caiso-161 / nyiso-113); no separate A0 run
> is built or needed. **If 2023 moves at all, the wiring is wrong — stop and fix
> before reading 2024 or 2025.**

## 8. HOLDOUT / SCOPE DISCIPLINE

- Years **2023 2024 2025**, ONE invocation, ONE bundle (rule 16). Years run
  **sequentially** (rule 12); CAISO is a plant-level multi-zone LP.
- The **holdout spend freeze** (`frontend/data/backcast/holdout-freeze.json`) is
  ACTIVE and outranks every marker. No year outside 2023–2025 is solved, scored
  or registered, for any reason.
- Solved **in-session**. No GitHub Actions runner (private repo, billed
  minutes).
- Registered on the dashboard whether keeper or rejected probe (rule 15); matrix
  cell `lcr_tsl_published` × CAISO updated `U` → verdict in **this** session
  (rule 28b).
- **Out of scope, explicitly:** `caiso_asymmetric_path_ratings` (its own later
  arm), the caiso-141 A2 wall, the `caiso_gas_floor_frac` rule-26 deletion
  (owner decision), and every cell marked R/I/G in the matrix.
