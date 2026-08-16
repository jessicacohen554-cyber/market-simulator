# PRECHECK — caiso-197 (lane 3): the CAISO-derived, publicly cited ST_GAS WEFOR base — `gas_st_wefor_base_override = 0.1591` — FROZEN before any lane-3 solve

**Committed and pushed before the lane-3 arm solves.** Gate spec applied as
written: `GATESPEC-caiso193-stgas-wefor-2026-08-11.md` (authored by caiso-191
BEFORE any lane-3 measurement) — no band edited. The lane discharges
FINDING-caiso187 §3d / known-open item 3: CAISO's 2,858.8 MW of ST_GAS carries
a statistical WEFOR base of 0.21 the matrix's own note records as *"fitted to
ERCOT's once-through 1950s-60s steamers and more than 2× every other thermal
class"* — an ERCOT-fitted parameter governing a different ISO's fleet, with
zero CAMPD overlay coverage so the statistical term is the ONLY outage
mechanism on the class. Executed on the re-anchored caiso-196 campaign base
(FINDING-caiso196 §7), sharing the lane-2 control `caiso197_l2_control`
(GATESPEC §6's own sharing clause — disclosed here and in both FINDINGs).

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

The derived value (0.1591) is below the incumbent 0.21, adds ST_GAS capability
and lowers price — the flattering sign; every ambiguity below is therefore
resolved per the GATESPEC §4 conservative default and each resolution is
stated. No price series was read anywhere in the derivation (the census probe
reads EIA-860, the GADS corpus CSVs, and the CAMPD extract facility-id column
— a count, not a fit).

## 1. THE FROZEN VALUE

```
gas_st_wefor_base_override = 0.1591        (CAISO only; one value, no sweep)
```

Committed record: `results/calibration/_caiso197_stgas_census.json`
(probe `scripts/probes/_caiso197_stgas_census.py` — NO LP, no price series).
Any post-PRECHECK change to this value voids the session (G-FROZEN).
`wefor_multiplier` stays at its control value in this arm; the lane-2 fields
are lane 2's object and are NOT bundled here (rule 19).

## 2. The citation chain (G-CITE), reproducible from the citations alone

**Link 1 — EIA-860 fleet census** (`data/raw/eia-860/
eia860_generator_operable.parquet`, the model's own fleet basis), restricted
to the LP's ST_GAS bins through the SHIPPED fleet path (caiso-187/193 probe
construction — `load_or_synthesize_bins` + `bins_to_fleet` on the caiso-196
keeper config), so the census population is exactly the fleet the override
governs. Three plants, six gas-fired ST units, 2,858.8 MW (equal to the
GATESPEC's own figure):

| plant | unit | summer MW | online | GADS size class |
|---|---|---|---|---|
| 315 AES Alamitos | 3 | 327.0 | 1961 | 300-399 |
| 315 AES Alamitos | 4 | 335.0 | 1962 | 300-399 |
| 315 AES Alamitos | 5 | 480.0 | 1964 | 400-599 |
| 335 AES Huntington Beach | 2 | 225.8 | 1958 | 200-299 |
| 350 Ormond Beach | 1 | 741.0 | 1971 | 600-799 |
| 350 Ormond Beach | 2 | 750.0 | 1973 | 600-799 |

All six are 1958–1973-vintage coastal once-through steam units — the same
technology generation the ERCOT 0.21 was fitted to, which is exactly why the
class must be re-derived from a PUBLISHED class statistic rather than carried
from another ISO's residual fit (rule 25).

**Link 2 — the published class table**: NERC GADS **"Generating Unit
Statistical Brochure 3 — 2020-2024 — Unit Reporting Events"** (NERC RAPA/GADS;
public, no login/paywall), on-disk corpus
`data/raw/reference/nerc-gads-eford-2020-2024/` with the recorded source URL
(`nerc.com/globalassets/programs/rapa/gads/reports/generating-unit-statistical-
brochure-3-2020-2024---unit-reporting-events.xlsx`), retrieval record
(2026-07-08, HTTP 200, 44,295 bytes) and extraction rule in its README. Rows
used — FOSSIL **Gas Primary** (gas-fired fossil steam), EFORd column, by unit
size class:

| GADS row (2020-2024) | # units | unit-years | EFORd (%) |
|---|---|---|---|
| FOSSIL Gas Primary 200-299 | 36 | 144.83 | 10.35 |
| FOSSIL Gas Primary 300-399 | 34 | 133.75 | 10.67 |
| FOSSIL Gas Primary 400-599 | 50 | 208.33 | 15.22 |
| FOSSIL Gas Primary 600-799 | 12 | 49.67 | 19.31 |

**Link 3 — the mapping arithmetic** (unit summer capacity = the GADS NMC
analog; capacity-weighted mean over the six units' size-class rows):

```
(327.0·10.67 + 335.0·10.67 + 480.0·15.22 + 225.8·10.35 + 741.0·19.31
 + 750.0·19.31) / 2,858.8  =  15.9149 %   →   0.1591
```

No vintage adjustment is applied because the source publishes none (the
brochure conditions on size class only); the model's own age escalation
remains in force on top of the base, which is the registered field's shipped
semantics (`data/fleet/arrays.py` keeps `+ max(0, age − onset) · rate` — the
same application MISO's armed value uses).

## 3. Derivation rules and every ambiguity's resolution (stated, with anchors)

* **Metric = EFORd, not EFOR.** This is a semantic mapping, not a
  higher/lower coin flip: the model applies the value as an hourly
  availability derate — the probability the unit is forced-unavailable when
  the market demands it — which is EFORd's definition; EFOR overweights
  forced hours for cycling/intermediate duty (service hours shrink while
  forced hours persist), which is why GADS publishes the demand-adjusted
  variant. The repo's OWN reading of this same document family is 1 − EFORd
  (`gas_availability_factor = 0.866` = 1 − 0.1344, the 2019-2023 brochure's
  Gas Primary All Sizes EFORd — `docs/parameter-citations.md`), and the
  corpus README's availability table quotes EFORd. Citing EFOR (24.27 % All
  Sizes) into an hourly availability slot would be a class mis-mapping — the
  decimal-slip family G-BAND exists to catch, in the other direction.
* **Window = 2020-2024** (brochure 3): the newest published pool, the maximal
  overlap with the 2023–2025 solve span, AND the highest pooled Gas Primary
  EFORd of the three published rolling windows (12.60 → 13.44 → 14.26 across
  2018-2022 → 2019-2023 → 2020-2024) — recency and the GATESPEC's
  higher-defensible-value rule agree, so no ambiguity is spent on the window.
* **Category = FOSSIL Gas Primary**: the exact class semantics of ST_GAS
  (gas-fired fossil steam). The Oil/Gas Primary superset was the pre-declared
  fallback for suppressed size rows only; no fallback fired (all four needed
  size rows are published in Gas Primary).
* **Size classes from EIA-860 summer capacity** (the net-MW NMC analog; the
  same basis the fleet's pmax carries).

## 4. Numeric gates (GATESPEC §4), status at PRECHECK time

| gate | bar | status |
|---|---|---|
| **G-FROZEN** | one value, committed before any solve; no sweep, no second candidate | **0.1591 frozen above**; census probe ran no LP and read no price |
| **G-CITE** | full public chain: census → published table rows → arithmetic | §2 — every link public, quoted, and reproducible from the citations alone |
| **G-BAND** | value ∈ [0.03, 0.21] | **0.1591 IN BAND** (no ceiling exception needed) |
| **G-POSITION** | position vs MISO's 0.10 explained by the census, never targeted | §5 below, written before any solve |
| **G-DOF** | ledger does not increase; field enters identified `measured` (cited); ERCOT 0.21 / MISO 0.10 byte-untouched | verified on the built bundles at FINDING time; the ERCOT-fitted 0.21 stops governing CAISO |

## 5. G-POSITION — why 0.1591 sits ABOVE MISO's 0.10, from the census alone

CAISO's six-unit fleet is size-concentrated at the TOP of the gas-steam size
distribution: Ormond Beach's two 600-799 MW units are 52.2 % of fleet
capacity, and that size class carries the near-highest published Gas Primary
EFORd (19.31 %); another 16.8 % (Alamitos 5) sits in 400-599 at 15.22 %. The
published table's small/mid classes (where a mid-continent fleet like MISO's
predominantly sits, 100-399 MW) print 10.35–11.26 % — i.e., MISO's 0.10 is
mid-size-class territory, and CAISO lands higher purely because its capacity
is weighted onto the largest, worst-performing published size classes. The
value was computed blind from the size mapping; no cross-ISO number entered
the arithmetic (MISO's 0.10 and ERCOT's 0.21 appear in this file only as the
fence and the explanation obligation the GATESPEC assigns them).

## 6. CAMPD zero-coverage premise, re-verified (a count, not a fit)

`data/raw/campd-unit-outages-CAISO.csv` (the committed extract, caiso-196
re-derived sha) contains **0 of the 3** census plants (315, 335, 350 — none
present in any year), so the statistical term remains the ONLY outage
mechanism on the class and the override is the only channel through which its
availability can be made CAISO's own. Recorded in the census JSON.

## 7. A/B protocol (GATESPEC §6; control shared with lane 2, disclosed)

* **CONTROL** — `results/calibration/caiso197_l2_control` (the caiso-196
  keeper recipe replayed on the re-anchored base; capacity-deliverability
  partition materialized, seam-cap log lines verified; `hydro_ror_split`
  explicitly False, disclosed; ratified tolerance |ΔC3a| ≤ 0.1 pp/yr,
  |ΔC3b| ≤ 0.005 against the keeper's committed values, noise floor quoted
  first). ONE control for lanes 2 and 3, per the GATESPEC's own sharing
  clause.
* **ARM** (`results/calibration/caiso197_l3_stgas`) — control + ONE field:
  `python scripts/replay_keeper.py results/calibration/caiso196_e1_elsegundo
  --out-dir results/calibration/caiso197_l3_stgas --set hydro_ror_split=false
  --set gas_st_wefor_base_override=0.1591`
  The lane-2 fields stay at their CONTROL values in this arm (one mechanism,
  rule 19); composition of surviving lanes is Wave 2's job under the
  integration protocol.
* Rule 16: 2023+2024+2025 in one bundle; years sequential, arms sequential
  (rule 12); registered (rule 15) with `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B
  delta is `gas_st_wefor_base_override` = 0.1591 at CAISO; no other input
  differs."

## 8. Kill criteria (GATESPEC §5, inherited whole)

* Value outside G-BAND without the census-grounded exception ⇒ refused, no
  solve. (In band; clause moot.)
* Any link in the chain non-public or non-quotable ⇒ no arm (null-FINDING).
* Any post-PRECHECK value change ⇒ void.
* Any use of MISO/ERCOT values as evidence ⇒ void (rule 25) — they appear
  only as fence and explanation obligation.

## 9. Required artifacts

* This PRECHECK (committed before the lane-3 solve) +
  `_caiso197_stgas_census.json` + the census probe.
* Bundle `caiso197_l3_stgas` (control shared: `caiso197_l2_control`).
* `results/calibration/FINDING-caiso197-stgas-wefor-2026-08-16.md` — gate
  tally, §0 quoted verbatim, single-mechanism statement verbatim, matrix duty
  (b) on the `wefor_statistical_stack` CAISO cell (the row that registers
  `gas_st_wefor_base_override`), calibration-log entry in-session.
