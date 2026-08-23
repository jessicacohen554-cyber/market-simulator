# PREREG nyiso-153 — `nyiso_incity_commitment_obligation` A/B on the measured rho (the online-rho pair, unlocked by the RHO_CLIP ruling)

Session nyiso-153, 2026-08-22. Committed and pushed BEFORE the arm solves.
Phase-0 record: `_nyiso153_phase0.json` (probe
`scripts/probes/_nyiso153_phase0.py`, measured on the committed keeper bundle
`nyiso152_armSE` ≡ `2026-08-22-nyiso-152-duty-complete`). Holdout freeze
ACTIVE; every year solved, scored or read is 2023–2025 (rule 22); all three
years in one invocation (rule 16).

## 1. Object and unlock

`nyiso_incity_commitment_obligation` (NYISO cell **U** — never solved):
re-classes the published downstate 10-minute families
(`nyc_10min_total` 500 MW, `li_10min_total` 120 MW) onto the online-gated
class 2, whose row `R[2,z] ≤ ρ·ΣP` counts ONLY online in-pocket output (no
idle credit, no storage — `reserve_rows.py` gated branch). The premise
(spec.py `NYISO_INCITY_OBLIGATION_FAMILIES` block): a load-pocket 10-minute
product is supplied synchronised — steam necessarily online; fast-start GTs
"the other in-pocket provider". ρ is the MEASURED
`campd_online_reserve_rho_NYISO.csv::incity_obligation` aggregate **0.3014**
(126 units / 29 plants, 9.53 GW HSL, CAMPD coverage 95.5 %, buckets quick
0.2157 / steam 0.3283). UNLOCK: the arm was inadmissible while
`RHO_CLIP = (0.5, 4.0)` floored the identified 0.3014 up to 0.5 (an uncited
floor deciding the mechanism, rule 21); the owner's 2026-08-22 ruling (card
nyiso-145 option A) deleted the floor, so the row now solves at its own
measurement. Mutually exclusive with `nyiso_synchronised_reserve` (code-
enforced, rule 19); disposition of that sibling in §6.

## 2. Phase-0 measurement and the pre-registered prediction

On the keeper's own dispatch the gated row would start in DEFICIT
(`ρ·ΣP < req`) in **7,391 / 7,920 / 7,653 h (NYC)** and
**7,524 / 6,806 / 5,768 h (LI)** — the keeper's median in-pocket online
output is 645/443/676 MW (NYC) against the `req/ρ ≈ 1,660 MW` the family
needs online. The gated mechanism's ONLY commitment channel is the
effective-offer subsidy `ρ·μ`, and μ is capped by the published NYC flat $25
RCPF (`nyiso_nyc_rcpf_step_curve`, armed) → max inducement
**$7.53/MWh**. Revealed-offer cross (p05 of zone LMP over each unit's own
on-hours): the offline capacity within the subsidy of merit covers the
needed MW in only **3 % / 3 % / 12 %** of NYC deficit hours (LI
17 / 18 / 37 %).

**PREDICTION (committed before the solve):** the LP prefers the $25
shortfall to uneconomic commitment — `nyc_10min_total` ends with
`shortfall_mw > 0` in **≥ 5,000 h** in each of 2023/2024 (and ≥ 4,000 h in
2025), i.e. the arm manufactures a persistent locational reserve-shortfall
regime. The real market MEETS this requirement; RCPF shortfall pricing is an
exception state (tens of hours a year at most), not a standing condition.

## 3. Arms (ONE new solve)

* **Control = the committed keeper bundle** `nyiso152_armSE`
  (`2026-08-22-nyiso-152-duty-complete`). NO control re-solve: zero solve-
  affecting commits have landed since that bundle solved at this HEAD
  (verified: `git log 12b90ca..HEAD -- src/ scripts/run_calibration*.py` is
  empty; the working-tree delta is docs/probes only). K1 runs on
  `run_config.json` scenario diffs as always.
* **ARM O** `nyiso153_armO` — keeper recipe +
  `nyiso_incity_commitment_obligation: true`
  (`nyiso153_armO_recipe` = `nyiso152_armSE_recipe` + the one key).

## 4. Gates (probe `scripts/probes/_nyiso153_ab_gates.py`)

* **O-K1 exactness** — scenario diff vs the keeper =
  {`nyiso_incity_commitment_obligation`} exactly.
* **O-K2 liveness** — the solve log carries the measured-rho line
  (`MEASURED online_rho=0.3014` for family_set `incity_obligation`) every
  year, and the arm's `reserve_family` sidecar shows `nyc_10min_total` and
  `li_10min_total` at `reserve_class = 2` (control: 1).
* **O-K3 adjudication, two pre-registered branches:**
  * **REJECT branch** — if `nyc_10min_total` shortfall hours ≥ **2,000** in
    any year: REJECTED-AS-ARMED on structural falsity — the mechanism
    manufactures a standing shortfall regime the real market never shows
    (the bar sits an order of magnitude above any real RCPF activation
    regime and far below the predicted ≥ 5,000, so the branch assignment is
    unambiguous). Matrix cell U → **R** with this record; the premise's
    GT-half (idle 10-minute-start capacity excluded from a TOTAL-product
    family) is recorded as the diagnosed defect for any successor.
  * **STRUCTURAL-PASS branch** — if shortfall hours < 2,000 every year AND
    the in-pocket online ΣP rises materially toward `req/ρ` (the commitment
    channel worked against the phase-0 arithmetic): adjudicate on O-K4/O-K5
    plus the downstate faces (C3c model counts vs 1/0/0; NYC/LI C3a zonal
    legs), registration per rule 15, promotion only via the standing
    convention (determination not worse + legitimacy strictly better) — and
    a rule-19 reconciliation session with the downstate ST_GAS always-on
    reliability-floor limbs is chartered before any further downstate
    commitment lever (the obligation and the floors would then both hold
    downstate steam online; never silently stacked).
* **O-K4** — zero new D-4 FAILs, zero new D-1 misses; no material class's
  forced share rises (the mechanism adds no floors — its commitment is
  priced, not forced, so D-2 carries no new attribution).
* **O-K5** — no CRITERIA PASS→FAIL vs the keeper in any year. Watched
  adverse case: C3a-2023 sits at +5.3 % (4.7 pp of headroom); the subsidy
  can only DEPRESS in-pocket effective offers (≤ $7.53/MWh), so downstate
  under-pricing may worsen — NYC/LI zonal C3a legs are REPORTED per year.
  C3c reported at whatever it lands (the family dual is not a zonal energy
  price; no mechanical C3c claim is made).

## 5. Registration disposition

The arm registers per rule 15 whatever the branch (keeper or rejected
probe). The control is the already-registered keeper — nothing new to
register on that side.

## 6. The `nyiso_synchronised_reserve` sibling (cell U)

NOT solved in this session. The code itself states the obligation
"GENERALIZES the path-A NYC-spinning family to the published J/K ladders"
and enforces mutual exclusion (rule 19). Path A's family is HAND-SCOPED
(`nyc_spin_online`, 250 MW at a $500 penalty that appears in no published
NYC RCPF cell) with a quick-only eligible set, where the published
instrument the obligation uses is the $25 NYC RCPF on the full
in-pocket fleet. Disposition rule, pre-registered: if the obligation
REJECTS on the shortfall branch, the sibling is adjudicated **G**
(governance-refused, no solve) — its only differences from the tested form
are a NON-published penalty (rule 5 [R-NO-MAGIC]) and a narrower eligible
set that contradicts the measured steam-carried spin supply (its own
artifact row: steam bucket ρ 0.3283 on 6.4 GW), so it could only "succeed"
by manufacturing scarcity from an uncited $500 scalar — the exact
reach-the-number-through-an-unreal-mechanism move rule 1 forbids. If the
obligation lands STRUCTURAL-PASS, the sibling stays U-superseded (noted on
its cell), never separately armed.

## 7. Reproduction

```
python3 scripts/probes/_nyiso153_phase0.py
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso153_armO_recipe --out-dir results/calibration/nyiso153_armO
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso153_armO --iso NYISO --json-out results/calibration/nyiso153_armO/legitimacy_diagnostics.json
python3 scripts/probes/_nyiso153_ab_gates.py --arm-log <solve log>
```
