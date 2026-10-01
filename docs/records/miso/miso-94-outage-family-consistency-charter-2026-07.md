# miso-94 charter — LANE A: the guard-corrected std extract stales its own downstream outage family

**Status:** PRE-REGISTERED. Written and committed BEFORE any solve was launched and
before any post-change price number was read. Every input-side number below was
measured from committed artifacts with **no LP solve** (extract A/B re-derives only).

**Lane:** A of the miso-93 handoff — "the MISO re-tune", scoped by its own first
question: *which offer-curve parameters were fitted against the inflated envelope,
and do they re-derive?*

**Parent:** `docs/handoffs/miso-93-keeper-reaudit-charter-2026-07.md`;
`results/calibration/FINDING-miso93-keeper-reaudit-meritguard-2026-07.md`.

---

## 1. The question this charter answers first (cheap, no solve)

miso-93 measured that adopting the merit-order-guard-corrected CAMPD extract
(`6a8f285`) lowers MISO prices by −$0.445 (−1.38 pp) on 2024 and pushes C3a-2024
from −8.7 % to −10.1 %, 0.1 pp past the ±10 % veto. The ledger is 3/3, so the miss
must close by **structure** or not at all.

The handoff named one legitimate door: rule 23 `[R-FROZEN-DERIVE]` permits a
frozen-derive parameter to be re-derived when its **source data** changes, and the
guard-corrected extract IS a source-data change. So: **which of MISO's derived
parameters actually consume that extract?**

Answered by reading each derivation, before solving:

| candidate | consumes the std extract? | verdict |
|---|---|---|
| `gas_offer_margin_anchor` (3.0492) | **No** — derived from the delivered-gas series only (`derive_gas_offer_margin_anchor.py`; rule-23 trigger is `data/raw/gas-prices/` or EIA-923 receipts) | does NOT re-derive |
| `phys_committed` / `phys_econ_low` / `phys_econ_high` (the miso-88 eGRID-HR bands) | **No** — `derive_campd_marginal_hr.py` reads CEMS unit-hours with `grossLoad > 0`; outage hours self-exclude and the extract never enters | does NOT re-derive |
| `SUMMER_WEFOR_SHARE` / `SUMMER_CLASS_DERATE` | **No** — no derivation of any kind exists (`fuel_trajectories.py`: "no derivation, sweep or calibration lineage exists"); nothing to cite | does NOT re-derive (and is forbidden anyway) |
| `reliability_floor_coeffs_MISO.csv` | **No** — `commit_frac_window` is an online-count from CAMPD gross load; the extract never enters | does NOT re-derive |
| `campd_ct_run_lengths/bands_MISO.csv`, `MISO_SEAM_LADDER_BY_YEAR`, `miso_measured_reserve_requirements` | **No** — CAMPD run blocks / LMP+flows / ASM respectively | does NOT re-derive |
| `offer_curve_by_group` (72 scalars) | n/a — **residual**-identified, not a derive | cannot be "re-derived"; see §5 |
| **`campd-unit-outages-short-MISO.csv`** | **YES** — `_load_standard_windows` → `_when_operable_cf`, the CF basis of the `SHORT_BASELOAD_CF ≥ 0.55` guard | **re-derives** |
| **`campd-unit-outages-maxgen-MISO.csv`** | **YES** — `_load_covered_windows` → guard 4 (disjointness) | **re-derives** |
| **`thermal_tranches_MISO.csv`** | **YES** — `unit_outage_derate_factors` is the availability denominator of `committed_pct` / `mustrun_pct` | re-derives, but **provenance-blocked** — see §4 |

**So the door opens onto the outage family, not onto the offer-curve level.** The
three artifacts that consume the changed extract are all availability inputs; none
of MISO's price-level parameters re-derive. That is the finding, and it is what
this charter acts on.

## 2. The mechanism being changed (rule 12 `[R-FLOOR-WINDOW]` triple)

Not a new mechanism — a **consistency re-derivation of two existing measured
inputs** the MISO keeper already loads (`unit_outage_short_windows=True`,
`unit_outage_maxgen_events=True`), both of which take the std extract as a
derivation **input** and neither of which was re-run when `6a8f285` changed it.

* **Driver:** each unit's own CAMPD trace, scoped by the ISO's declared
  capacity-emergency instruments (maxgen registry) and by the coal baseload
  identification guards (short). Unchanged — only the std-extract input changes.
* **Window:** unchanged. Maxgen binds only inside declared registry windows;
  short binds only inside detected < 5-day coal full stops.
* **Forward story:** unchanged — both regenerate from each new CAMPD/declaration
  vintage; a forecast year carries the class outage-rate machinery instead.
* **Rule 23 citation:** the source-data change is
  `data/raw/campd-unit-outages-MISO.csv` at `6a8f285` (blob
  `f2b3ec8` → `c298c68`, 2,424 windows reclassified to the layup companion).
  **Not a residual.**

### 2a. A second, pre-existing defect the re-derive also fixes

The committed maxgen extract **violates the deriver's own asserted guard 4**. Three
unit-blocks are covered by short-extract full-stop windows *and* carry a maxgen
derate row, so the keeper multiplies two derates onto the same unit-hours
(`arrays.py` applies short and maxgen as successive `availability *= f`):

| unit | block | maxgen derate | short window covering it |
|---|---|---|---|
| Weston 4078/3 | 2024-08-26 13:00–20:00 | 369 MW | 2024-08-23 → 2024-08-27 (3.7 d) |
| Sherburne County 6090/1 | 2024-08-26 13:00–20:00 | 729 MW | 2024-08-24 → 2024-08-28 (4.4 d) |
| F B Culley 1012/3 | 2025-07-28 12:00–2025-07-30 | 287 MW | 2025-07-27 → 2025-07-28 (1.8 d) |

~1,385 MW double-derated during declared emergencies, 1,098 MW of it in the only
2024 block. This is a rule 19 `[R-ONE-MECH]` violation. Diagnosis: the committed
extract predates the short-extract leg of guard 4 (it also *excludes* Prairie
State 55856/01 on 2025-07-24, which only a then-present std window explains).
It is **not** reproducible at HEAD, which is how it was found.

## 3. Measured input deltas (no solve) and the pre-registered magnitude

Controls run first, HEAD code, single delta = the std extract:

* **short:** committed file is **byte-identical** to a HEAD re-derive on the
  pre-guard std blob → provenance clean, delta cleanly attributable.
  Guard delta: **−1 row** (F B Culley 1012/2, 2023-03-10→12, 2.2 d, 103.7 MW).
* **maxgen:** control does **not** reproduce (§2a is why). Guard delta on a
  like-for-like HEAD re-derive: **+18 rows / +1,338 MW / 23.1 GWh**, ST_GAS
  1,002 MW + CC_CHP 251 + CC_REGULAR 85 — exactly the classes the guard returned
  to merit (ST_GAS was 73.5 % of the guard's removals).

Net change, **committed on-disk → adopted**, by declared block:

| block | Δ derate MW | direction on price |
|---|---|---|
| 2023-08-24 12:00 (12 h) | **+41** | tighter |
| **2024-08-26 13:00 (7 h)** | **−362** | **looser** |
| 2025-06-23 00:00 (48 h) | +74 | tighter |
| 2025-07-24 00:00 (24 h) | +316 | tighter |
| 2025-07-28 12:00 (36 h) | +13 | tighter |

### PRE-REGISTERED PREDICTION (direction **and** magnitude — miso-93's charter got
### magnitude wrong, so it is stated explicitly here)

* **2024 moves the WRONG WAY and this arm does NOT close C3a-2024.** The only 2024
  block loses 362 MW of derate for 7 h. Bounding the price effect between MISO's
  measured local stack slope (~2 $/GW, FINDING-miso89 §6) and a scarcity-steep
  stack: 7 h × 0.362 GW × [2 … 100] $/GW ⇒ **−$0.0004 … −$0.03/MWh** on the annual
  load-weighted mean. Predicted C3a-2024: **−10.06 % → −10.06 % to −10.2 %**,
  i.e. **still FAIL**. Point estimate: −10.07 %.
* **2023:** +41 MW × 12 h ⇒ ≤ +$0.002/MWh; C3a-2023 unchanged to 2 dp. The short
  delta (−103.7 MW × 2.2 d, March 2023, off-peak) is worth ≤ −$0.01/MWh.
* **2025:** net +403 MW across three blocks (108 h) ⇒ **+$0.001 … +$0.05/MWh**;
  C3a-2025 −17.5 % → −17.5 % to −17.4 %, still ledgered.
* **C3b/C3c/C1/C2/C4/C5a/C7/C8:** predicted unchanged in verdict. C8 ST_GAS forced
  share may move ≤ 1 pp (18 added rows are mostly ST_GAS) and is predicted to stay
  **grounded above budget** (D-4 clean), i.e. C8 still PASS.

### Pass/fail bar — pre-registered

This arm is adopted **on correctness, not on the residual** (rules 1 / 11 / 19 / 23):
it removes a measured double-count and applies an already-adopted guard consistently
to the artifacts derived from it. Therefore:

* **ADOPT** iff the two extracts re-derive cleanly at HEAD from the guard-corrected
  std extract (already verified) **and** no gate that currently PASSes flips to FAIL.
* **The arm is NOT judged by whether C3a-2024 closes.** If C3a-2024 stays FAIL — the
  predicted outcome — the determination stays **NOT-YET** and the honest LANE A
  result is: *there is no structural door of the required sign and size; C3a-2024 is
  an open root-cause issue under rule 24 `[R-DOF]`, reported and not tuned.*
* **KILL** only if a currently-passing gate fails, in which case the arm is reported
  as a rejected probe (rule 15 — registered either way).

## 4. What this charter deliberately does NOT do

* **`thermal_tranches_MISO.csv` is NOT re-derived this session — provenance-blocked.**
  It consumes the std extract (so it IS stale), but the committed file does **not**
  reproduce at HEAD on its own pre-guard input: a 3-year (`--years 2023 2024 2025`)
  re-derive differs on `committed_pct` (71 plants, max 53.3 pp), `mustrun_pct` (31,
  max 60.0 pp), `p25_cf` (77) and even `nameplate_mw` (6 plants, max 1,028.6 MW) —
  changes that are **not** attributable to the guard. Adopting it would be a
  confounded arm, the exact caiso-123 defect miso-93 was careful to avoid. It is
  reported as an open item with its own measurement, not buried. **This is the
  highest-value next lane** — it is the only stale artifact that touches offer-curve
  *shape* (must-run / committed tranche sizes) rather than availability, so it is the
  only remaining candidate with plausible magnitude on C3a.
* **No offer-curve re-tune.** `offer_curve_by_group` is residual-identified
  (72 scalars, ≥39 solves) and is not a derive — there is nothing to "re-derive" and
  no source-data change to cite. Re-fitting it to recover 0.06 pp would be an answer
  key (rule 24), and the handoff forbids an adder, a level multiplier, and a summer
  band explicitly.
* **No ledger widening.** Budget is 3/3 and this lane consumes none of it.
* **Rule 22:** 2023–2025 only. No marker, freeze active.

## 5. Verification protocol

1. Both extracts re-derived at HEAD with the guard-corrected std extract **in place**
   (verified by blob hash before and after each run — one contamination was caught
   and corrected this session: a control run left the pre-guard blob on disk).
2. Clean partitions (`capacity-deliverability`, `ramp-capability`,
   `transfer-interface-limits`, `winter-fuel-inventory`) regenerated **before** the
   solve, and the solve log audited for missing-input warnings — miso-93 correction 1:
   `_miso_cil_cel_groups` silently falls back to static PY2025-26 summer caps
   independently of the `capacity_deliverability_limits` flag.
3. All three years 2023/2024/2025 in ONE bundle (rule 16), staged
   `--reuse-solved` recipe.
4. Registered on the dashboard whatever the verdict (rule 15).
