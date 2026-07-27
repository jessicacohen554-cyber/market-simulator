# DIAGNOSIS — ERCOT-126: the coal availability envelope is ACCURATE and REALIZABLE; the residual is not in the availability layer at all — the model's coal converts any headroom it is given into energy, and every measured availability instrument is either empty, mis-shaped or already live

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot126-coal-avail-envelope ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** the ERCOT-122/123/124/125 closure of the entire coal offer
surface, which left the ERCOT-116/121 availability envelope as the only
structurally-open coal candidate ·
**Method** Phase 1 only — the keeper's committed payload/bench/sidecars plus raw
sources, through `scripts/probes/ercot126_coal_availability_envelope.py`
(sections A–G), two runs of the frozen `scripts/data/derive_campd_unit_outages.py`,
and one code trace of the availability and reserve paths.
**No LP was built. No year was solved. No arm was registered. No `ScenarioConfig`
field, cache-key surface or solve path was touched. No keeper file was touched.**

**Outcome: Phase 1 does NOT license a mechanism, and Phase 2 was not run.** The
decomposition (§1) is unambiguous and reverses the charter's framing: the
keeper's coal is **1.06 / 0.21 / 1.88 TWh UNDER** actual, not over — the
`+6.8/+9.2/+12.9 TWh` figure the charter carries forward is the ERCOT-116 arm's
*bite* against the keeper, and it lands the arm **+5.69 / +8.90 / +10.96 TWh
OVER** actual. What is wrong with the keeper is **shape, not level**: it delivers
**43 / 41 / 50 %** of its coal energy on a binding flat monthly top where the real
fleet delivers **3.6 / 3.7 / 6.9 %**. The measured envelope is accurate and
realizable (§2) and halves that pin — and converts the freed headroom into energy
essentially 1:1, in every price band. §3 enumerates every measured availability
instrument that could hold coal below its ceiling and finds all of them refuted:
the AS reservation is already an unconditional LP constraint and measures
1.15/0.95/**0.13** TWh full span, the sub-5-day outage layer is the wrong *shape*
for the defect (a proven-ex-ante 0.003 move on the gate it targets), the
partial-derate deriver returns **zero** windows, and time resolution accounts for
0.26–0.38 pp. §4 names two concrete defects found on the way. §5 is the
recommendation.

---

## 0. What is inherited, re-verified rather than assumed

| claim | source, verified this session |
|---|---|
| keeper coal 59.34 / 57.32 / 60.29 TWh | keeper `hourly/class_hourly_<y>.parquet`, P1, COAL_* classes |
| the keeper forces ZERO coal energy | keeper `legitimacy_diagnostics.json` — D-2 has no COAL row in any year (ERCOT-124 §3 #8, reproduced) |
| LIVE C7 failure = COAL_LIGNITE **2023** only | keeper D-1 rows: 2023 r **0.745** / cv_ratio **0.294**; 2024 0.862/1.117 and 2025 0.913/1.612 both clear. COAL_PRB passes all three years (r 0.975–0.995) |
| the ERCOT-116 arm's bite | `2026-07-26-ercot116-coal-avail-probe` payload — coal +6.76 / +9.11 / +12.84 TWh vs the keeper |
| coal is CLLIG only | `Resource Type` filter reproduced on the DAM disclosure |
| the ten ERCOT coal plants | `master-plant-registry.csv` (ba_code ERCO, plant_group COAL) + Sandy Creek 56611 from `custom-bin-assignments.csv` |

**The charter's residual statement is corrected here, with receipts.** "+6.8 /
+9.2 / +12.9 TWh of modelled coal over actual" is the ERCOT-116 arm's coal
*increase* (ERCOT-121 §3's BITE line, quoted onward by ERCOT-124 §4). Against
actual, the **keeper is under and the arm is over** — §1.1. Both directions
matter for what a mechanism must do, so the frame is fixed before anything is
proposed.

## 1. The decomposition (charter task a)

### 1.1 Level — the keeper is UNDER, the arm is OVER

Net TWh. `declared` is the accepted COP `live_mw` of the CLLIG registrations of
each model plant — the exact series `ercot_thermal_dam_availability_plant`
reads. `actual` is CAMPD **coal-fuelled units only** (which keeps W A Parish's
gas steamers out of the plant grain — the ERCOT-121 §1a contamination), gross
converted to net by the per-year factor measured against the committed EIA-923
bench: 0.8972 / 0.9051 / 0.9069.

| year | declared | actual | keeper | arm116 | act/decl | keep/decl | arm/decl | keeper−act | arm−act |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 96.00 | 60.42 | 59.35 | 66.11 | 0.629 | 0.618 | 0.689 | **−1.06** | **+5.69** |
| 2024 | 92.96 | 57.62 | 57.40 | 66.51 | 0.620 | 0.617 | 0.715 | **−0.21** | **+8.90** |
| 2025 | 83.32 | 62.21 | 60.33 | 73.17 | 0.747 | 0.724 | 0.878 | **−1.88** | **+10.96** |

The keeper's annual coal level is right to 0.3–3 % and its *fraction of the
declared envelope* matches the real fleet's to within 0.011–0.023. The arm
over-runs by 9–18 % and over-uses the envelope by 6–13 pp.

### 1.2 Hours-online or per-hour level? — **90–93 % LOADING**

Splitting `declared − actual` into hours the plant was declared live and
produced nothing (COMMITMENT) against hours it ran below its declaration
(LOADING):

| year | commitment share of the gap | loading share |
|---|---|---|
| 2023 | 0.071 | **0.929** |
| 2024 | 0.083 | **0.917** |
| 2025 | 0.045 | **0.955** |

Real coal is almost never declared-live-and-dark. It is online, continuously,
at 0.55–0.97 of its own declaration — per plant, 2023: W A Parish 0.600, Sandy
Creek 0.551, Fayette 0.656, Martin Lake 0.689, Limestone 0.708, J K Spruce 0.752
against Oak Grove 0.942 and Major Oak 1.028. **This kills the commitment
hypothesis and, with it, any full-stop-event mechanism as the primary lever** —
whatever holds coal down is a per-hour level effect, not an on/off effect.

### 1.3 Seasonal — the residual is almost entirely seasonal

Net GW monthly means. The annual totals of §1.1 are near zero *because* a
summer over-run and a winter/shoulder deficit cancel.

| | 2023 keeper−act | 2024 keeper−act | 2025 keeper−act | 2023 arm−act | 2024 arm−act | 2025 arm−act |
|---|---|---|---|---|---|---|
| Jun–Sep mean | **+1.48** | **+1.73** | **+1.06** | +1.86 | +2.56 | +2.26 |
| Feb–Apr mean | **−1.44** | **−1.72** | **−1.26** | −0.19 | −0.38 | +0.32 |
| spread | 2.92 | 3.45 | 2.32 | 2.05 | 2.94 | 1.94 |

Two different causes, as ERCOT-114 predicted a uniform lever would expose:

* **Summer (model over).** The model sits at 0.78–0.92 of the declared envelope
  and is availability-bound — §1.4's pin. The arm makes the *absolute* summer
  over-run worse (+1.9 to +3.0 GW).
* **Feb–Apr (model under).** The model runs at **0.24–0.41** of declared while
  the real fleet ran at **0.40–0.80**; the declared envelope in those months is
  6.9–9.3 GW against a model dispatch of 2.4–4.8 GW. **The model is nowhere near
  its ceiling there** — the shoulder deficit is a merit-order outcome and
  *availability is not its binding constraint*. No availability mechanism, right
  or wrong, can address it.

The arm narrows the seasonal *spread* (which is what the ERCOT-116 pre-commit's
matched-band G1/G2 measured, and why those gates passed) by lifting **every**
month, which is why it simultaneously blows the level.

### 1.4 The PIN — the finding that reframes the lane

Share of each fleet's annual coal **energy** delivered within 0.5 % of that
plant-month's own maximum. On a unit whose binding constraint is its ceiling
this is large; on a dispatching unit it is small. Monthly grain, online hours
only, so maintenance moving the ceiling cannot be mistaken for dispatch and an
outage month cannot manufacture a hit.

| year | **keeper** | arm116 | **actual** |
|---|---|---|---|
| 2023 | **43.1 %** | 19.7 % | **3.6 %** |
| 2024 | **40.6 %** | 15.9 % | **3.7 %** |
| 2025 | **50.3 %** | 17.4 % | **6.9 %** |

Per plant (2023 keeper / actual): Oak Grove 83 / 7, Major Oak 73 / 11, Limestone
36 / 3, Coleto Creek 34 / 2, J K Spruce 33 / 5, Sandy Creek 32 / 2, Fayette
30 / 1, W A Parish 26 / 2, Martin Lake 25 / 3, San Miguel 26 / 1. **The pin is
fleet-wide, not an Oak Grove idiosyncrasy** — ERCOT-121 §1a named Oak Grove
because it is the extreme case, but every coal plant in the model delivers
25–45 % of its energy at a binding ceiling against a real fleet at 1–5 %.

That is the mechanism-level explanation of ERCOT-116's bite: **the model's coal
is a ceiling-rider, so raising the ceiling raises the energy nearly one-for-one.**
The statistical availability estimate is not primarily an availability model in
this configuration — it is the *de facto* limiter on modelled coal energy.

### 1.5 Price-conditional loading — the keeper matches, the arm does not

Loading against the declared envelope, both fleets on the **same hours** and the
**same denominator**, binned by the measured ERCOT RT price:

| 2024 band | hours | actual | keeper | arm |
|---|---|---|---|---|
| <\$15 | 3353 | 0.542 | 0.494 | 0.582 |
| \$20–25 | 1270 | 0.652 | 0.676 | 0.777 |
| \$25–30 | 883 | 0.696 | 0.722 | 0.832 |
| \$35–50 | 602 | 0.689 | 0.720 | 0.830 |
| ≥\$50 | 760 | 0.720 | 0.767 | 0.871 |

(2023 and 2025 are the same picture; full table in the artifact.) The keeper
tracks the real fleet's price response to within ±0.05 everywhere above \$15 and
is 5 pp *low* below it. The arm is **9–15 pp high in every band, including the
sub-\$15 band** — the tell that the added energy is not economics: at a \$12
clearing price nothing about coal's merit position changed, only its ceiling.

**The real fleet's price response is remarkably shallow** — 0.54 → 0.72 (2024)
across the entire price range, never approaching its declaration even at \$50+.
That shallow band, not the level, is what the model does not reproduce.

## 2. Is the declared envelope right? — YES, and rule 14 `[R-ACCURATE]` therefore bites

The rule-14 exception is for accurate data *misaligned to our representation*.
Tested directly: the highest net output each real unit reached, against what the
COP declared.

| plant | actual max / declared max, 2023 / 2024 / 2025 |
|---|---|
| Limestone | 0.925 / 0.958 / 0.957 |
| W A Parish | 0.952 / 0.962 / 0.962 |
| Martin Lake | 0.934 / 0.951 / 0.967 |
| Coleto Creek | 0.925 / 0.938 / 0.950 |
| Fayette | 0.934 / 0.955 / 0.955 |
| Oak Grove | 0.960 / 0.966 / 0.975 |
| San Miguel | 1.015 / 1.021 / 1.023 |
| Major Oak | 1.010 / 1.019 / 1.021 |
| J K Spruce | 0.965 / 0.974 / 0.974 |
| Sandy Creek | 0.961 / 0.958 / 0.960 |

Every plant reaches 0.93–1.02 of its declaration. **The COP envelope is a
realizable physical ceiling, not an entitlement number**, so there is no
misalignment exception and rule 14 applies in full: the measured envelope is the
accurate input, the statistical availability is the estimate, and the estimate
was silently compensating. **The bug the accurate data discovers is real — and
§1.4 locates it outside the availability layer.**

## 3. Rule 19 `[R-ONE-MECH]` enumeration — every measured instrument that could hold coal below its ceiling (charter task c)

ERCOT-124 §3's table is inherited unchanged (bands, deltas, `coal_econ_marginal_hr_bound`,
`Pct_Peaking` 5.0 %, take-or-pay + passthrough sigmoids, the ERCOT-116 envelope,
per-plant must-run, and #8 — coal forces zero energy). What follows is this
lane's addition: the **availability-side** instruments, each measured this
session and each refuted.

### 3.1 The AS power reservation — already an unconditional LP constraint, and measured near-zero

Rule 13 `[R-MEASURED]` names "a measured ancillary-service power reservation" as
admissible, so this was the strongest candidate. Two independent refutations.

**(a) It is already in the LP, and not through the flag ERCOT-123 named.**
`model/lp/reserve_rows.py:185` builds `cap = fleet.pmax[:, None] * fleet.availability` —
literally the availability ceiling of §1 — and `reserve_rows.py:277-306` imposes
`Σ P[g,t] + Σ R[p,z,t] ≤ Σ pmax·avail` over the zone's eligible class. Coal is in
`RESERVE_FUEL_TYPES` (`model/reserves/spec.py:26-28`) and, under the keeper's
`ercot_multiproduct_as_coopt=True`, in **both** headroom tiers
(`spec.py:1445-1458`). Energy and reserve already share coal's headroom,
unconditionally.

> **Correction to ERCOT-123 §1, bucket (c).** That section attributed the
> modelling to `ercot_thermal_as_endogenous`. That flag is **forecast-only** —
> `config/scenarios.py:4475-4494`, used only in `model/ancillary.py:217-283` and
> the capacity screens (`evolve.py:280-286`, `retirements.py:1424/1447/1667`,
> `new_entry.py:683/909`, `runner.py:2194/2267`), never in `model/lp/` or
> `model/reserves/`. Setting it True changes **nothing** in any backcast LP.
> ERCOT-123's *conclusion* (rule 19 forbids a second AS reservation on coal) is
> unaffected and in fact strengthened: the constraint is on in every keeper,
> with the flag off.

**(b) Measured full span, it is far too small and its sign is wrong.** ERCOT-123
§2 could only measure the award block on 82 SCED probe days. The 60-Day **DAM**
disclosure carries `RegUp / RRSPFR / RRSFFR / RRSUFR / NonSpin / ECRSSD Awarded`
per resource for every hour of 2023–2025, so the same quantity is measurable
where a keeper needs it (rule 16 `[R-ALLYEARS]`):

| year | hours covered | fleet HSL mean | up-AS mean | up-AS / HSL | TWh equivalent |
|---|---|---|---|---|---|
| 2023 | 8,038 | 12.75 GW | 0.143 GW | **1.12 %** | 1.15 |
| 2024 | 8,782 | 12.81 GW | 0.108 GW | **0.84 %** | 0.95 |
| 2025 | 7,319 | 12.86 GW | 0.018 GW | **0.14 %** | **0.13** |

(The on-disk DAM disclosure files leave 0.7–1.4 k hours per year uncovered; the
shares are coverage-weighted means over the hours that exist and the TWh column
is the covered-hour total, so both understate a full-year figure by at most the
coverage ratio — which changes nothing about the conclusion below.)

Against a 5.7 / 8.9 / **11.0** TWh over-run, the reservation is 20 / 11 / **1 %**
of what is needed — and it **collapses to near zero in 2025, the year the gap is
largest**. A mechanism whose measured magnitude moves opposite to the residual it
is meant to explain is refuted by its own data, before rule 19 is even reached.
(Fleet `LSL/HSL` measures 0.374 / 0.393 / 0.386 on the same instrument, against
ERCOT-123 §4's 0.42–0.46 probe-day figure — recorded for ERCOT-117 §5.3, whose
lane that is.)

### 3.2 The sub-5-day forced-outage layer — the right kind of input, the wrong SHAPE, proven ex ante

ERCOT-121 §1a named the gap precisely: the CAMPD overlay carries **≥5-day**
events (`UNIT_OUTAGE_MIN_DAYS = 5`, `data/outages.py:238`), "so sub-5-day forced
outages and partial derates are represented only as a flat haircut, never as
events". The machinery for exactly that already exists and is unbuilt for ERCOT:
`ScenarioConfig.unit_outage_short_windows` (`scenarios.py:7712`, default off, in
the cache key at `scenarios.py:9144`), consumed by
`outages.unit_outage_short_derate_factors` (`outages.py:513-540`), fed by
`scripts/data/derive_campd_unit_outages.py --short-windows` with pre-declared
frozen guards (coal-only detector, unit annual CF ≥ 0.55 baseload screen,
revealed-availability in-merit filter), disjoint from the ≥5-day overlay by
construction. Only MISO and PJM have the file; ERCOT's
`campd-unit-outages-short.csv` has never been derived.

**Derived this session** (frozen script, default guards, `--iso ERCOT --years
2023 2024 2025`): **82 windows** over 8 coal plants — 15 / 27 / 40 events and
43.9 / 79.8 / 130.6 unit-days.

**It cannot clear G4, and this is provable without a solve.** D-1 takes the
**hour-of-day mean profile** and then the CV over h0–h14 *of that profile*
(`scripts/legitimacy_diagnostics.py:592-604`). A day-scale full stop lowers all
24 hours of the affected days together: it moves the profile's **level**, not
its **intraday shape**. Applying every derived 2023 lignite window to the
keeper's own COAL_LIGNITE series — the whole outage taken out of lignite, no LP
redistribution, so an upper bound:

| | profile_r (gate 0.80) | cv_ratio (gate 0.50) | lignite TWh |
|---|---|---|---|
| keeper, reconstructed | 0.744 | 0.300 | 16.739 |
| committed artifact | 0.745 | 0.294 | 16.738 |
| **+ short windows** | **0.742** | **0.303** | 16.512 (−0.227) |

The live C7 failure does not move. And the direction on level is adverse: the
layer removes coal in **every** year on a keeper that is already 1.06 / 0.21 /
1.88 TWh **under**, with the largest removal (130.6 unit-days) in 2025, the year
it is most under. Armed *with* the measured envelope it does nothing at all —
the DAM overlay is a bidirectional class-hour water-fill applied **after** the
outage overlays (`data/fleet/arrays.py:1163-1365` vs `arrays.py:896-939`) that
**sets** the cap-weighted class-hour mean to the measured fraction, so any layer
beneath it survives only as within-class shape.

### 3.3 The partial-derate plateau layer — measured EMPTY

`ScenarioConfig.unit_partial_outage_windows` (`scenarios.py:7737`) is the
companion for "a unit that keeps running but at a depressed ceiling" — on its
face the exact signature of §1.4. Run for ERCOT with the frozen detector
(`--partial-windows`, constants verbatim: 5-day plateau, 7-day median,
ceiling < 0.65× normal, 0.06 run-floor, CF ≥ 0.55 when-operable guard, in-merit
filter): **zero windows, all three years.**

That is a clean measured negative and it is decisive for the lane: the real
fleet's 0.55–0.97 loading is **not** a sustained availability plateau. It is
hour-to-hour dispatch inside a fully-declared envelope.

### 3.4 Time resolution — 0.26–0.38 pp, two orders of magnitude short

A saturating supply curve delivers less under a volatile 15-minute price than
its hourly mean implies, and the model is scored at 8760. Measured with no model
and no fitted value: the committed ERCOT-124 measured coal supply curve S(p)
evaluated on ERCOT 15-minute settlement prices (HB_BUSAVG, full year), as
`mean_i S(p_i)` against `S(mean_i p_i)`:

| year | intervals | 15-min market | hourly merit order | **resolution gap** |
|---|---|---|---|---|
| 2024 | 35,132 | 0.7468 | 0.7506 | **+0.38 pp of HASL** |
| 2025 | 35,036 | 0.8379 | 0.8406 | **+0.26 pp** |

Step-function sensitivities at \$20/\$22/\$25 give +0.18 to +0.67 pp. Against a
9–15 pp per-band over-delivery this is negligible. **Hourly resolution is not the
explanation** — recorded as a clean negative so the lane is not reopened on it.

### 3.5 What is left, and whose it is

| candidate | status |
|---|---|
| coal offer LEVEL / REACH / upper TAIL / owner split | **CLOSED** — ERCOT-122/123/124/125 |
| RT derate below the COP declaration (4.9–6.4 %, ERCOT-123 §3) | right size, but **82 probe days, 2024–2025 only**; no 2023 instrument exists, so the G6 LOYO 2023 leg would be unidentified before an hour was solved — the exact ERCOT-124 §4 killer |
| coal must-run base (model 0.28 vs measured 0.42–0.52) | **ERCOT-117 §5.3's lane**, un-renumbered and ring-fenced by this charter |
| age/temp coal derates | CLOSED — ERCOT-121 §1a |
| everything in §3.1–§3.4 | refuted this session |

**No un-used, full-span, measured availability input remains.** The mechanism
space of the availability layer is exhausted.

## 4. Two concrete defects found on the way (routed, not fixed here)

### 4.1 `BIN_FORCED_DERATE_BY_YEAR` — a live rule 26 `[R-REGISTRY]` breach inside the coal availability chain, and one of its two entries is wrong

`src/market_sim/data/fleet/eia860.py:2392-2404` holds a hardcoded per-plant
availability dict applied at `data/fleet/arrays.py:619-624` as a flat whole-year
multiplier. Rule 26 forbids exactly this ("no hardcoded per-plant dicts in
`data/` modules"), and the file's own comment records the V H Braunig entry being
removed on 2026-07-06 "per rule 24 (no off-registry tuning)" — the precedent is
in the file. Two entries remain:

* **`"N_COAL4": {2025: 0.67}` (Martin Lake) is factually right and load-bearing.**
  CEMS 2025: unit 1 **0.000 TWh**, units 2 and 3 4.263 / 5.097 TWh — a whole-year
  unit loss, and 835/2475 = 0.663 ≈ 0.67. The measured COP corroborates
  independently (Martin Lake's declared max collapses to 0.689 × nameplate in
  2025 from 1.03–1.04 in 2023–24). It is load-bearing because the CAMPD extract
  **misses it**: `campd-unit-outages.csv` carries 2025 windows for Martin Lake
  units 2 and 3 but **none for unit 1** — a unit that never runs has no baseline
  for the detector's CF ≥ 0.55 guard. Right value, wrong channel.
* **`"SC_COAL3": {2025: 0.0}` (Sandy Creek) is redundant AND wrong.** It zeroes
  all 8760 hours. Measured CEMS 2025: **364.5 GWh in January, 396.4 in February**,
  a 7.6 GWh April trace, zero thereafter — **768.5 GWh gross ≈ 0.70 TWh net**,
  and the last real output is 2025-04-24. The accurate, correctly-dated
  replacement **is already committed**: `campd-unit-outages.csv:6262-6263` carries
  `56611 S01 … 2025-01-22 → 2025-01-29` and `2025-02-28 → 2025-12-31` at 100 % of
  plant. The hardcode pre-empts it (`arrays.py:622-624` runs long before the
  outage overlay) and costs the model ~0.70 TWh of real 2025 coal — **~37 % of
  the year's 1.88 TWh coal deficit**, in the year the keeper is furthest under.
  This is a rule 14 `[R-ACCURATE]` breach as well as a rule 26 one: an estimate
  preferred over accurate data that is already on disk.

**Not fixed in this lane, and the reason is the charter's own gate.** Removing a
hardcode changes the ERCOT **default**, so it cannot be "a single declared delta,
default-off … byte-identical for every existing config, default cache key
unmoved". It needs its own pre-committed lane with a full-span re-solve. It is
also already on the repo's ledger — `docs/fable-repo-audit-2026-07.md:221` flags
`BIN_FORCED_DERATE_BY_YEAR` as an off-registry hardcode belonging in the outages
datatype. This session adds the measurement that makes it actionable and sizes it.

### 4.2 The ERCOT-123 §1 AS attribution

Corrected inline in §3.1(a). Recorded here because a future lane reading
ERCOT-123 would otherwise arm `ercot_thermal_as_endogenous` expecting an LP
effect and get a byte-identical backcast.

## 5. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run.** Three independent grounds, any one sufficient:
   **(a)** the residual is a *dispatch* property, not an availability property —
   the envelope is accurate and realizable (§2), the model's coal delivers
   43–50 % of its energy at a binding ceiling against reality's 3.6–6.9 % (§1.4),
   and every availability instrument therefore moves the level rather than the
   shape; **(b)** every measured availability input is refuted on its own data —
   AS already constrained and 0.13 TWh in the worst year, short windows a proven
   0.003 move on the gate they target *and* adverse on level, partial plateaus
   measured empty, resolution 0.26–0.38 pp (§3); **(c)** the one candidate with
   the right magnitude, the RT derate below the COP, has no 2023 instrument and
   would fail G6's 2023 LOYO leg before an hour was solved — the ERCOT-124
   precedent, applied to this lane's own charter.
   Rule 21 `[R-DOF]`: what is left can only be closed by choosing a value, which
   makes it an open root-cause issue, not a parameter.
2. **The ERCOT-116 envelope should be recorded as MEASURED-CORRECT AND
   PREMATURE, not as a defect.** §2 establishes the declaration is a realizable
   physical ceiling every plant reaches, so under rule 14 it is the right input
   and the statistical availability is the estimate that was compensating. It
   halves the pin (43/41/50 % → 20/16/17 %) — a real structural gain, rule 1
   `[R-STRUCT]`. It must not be promoted **until something holds coal below its
   ceiling**, because until then it converts headroom into energy 1:1 in every
   price band including sub-\$15 (§1.5). Arming it in isolation remains
   recommended against, as ERCOT-121 §3 concluded — this session supplies the
   mechanism-level reason that session could only infer.
3. **The successor lane is the coal DISPATCH band, not coal availability, and
   its most likely home is ERCOT-117 §5.3.** The real fleet operates in a narrow
   0.54–0.72 band that touches neither its min-load nor its ceiling; the model
   operates at the ends (0.49 at <\$15, 0.77 at ≥\$50, 43–50 % of energy pinned).
   The measured base share (0.37–0.46 full span here, 0.42–0.52 on the two
   earlier instruments) against the model's 0.28 is the bottom half of exactly
   that band and is already chartered. **This session does not fold into it** —
   it records that the availability lane's evidence now points there, and that
   the top half (nothing caps coal below its ceiling) has no measured owner yet.
4. **Fix `BIN_FORCED_DERATE_BY_YEAR` in its own lane** (§4.1) — the Sandy Creek
   entry is a rule 26 + rule 14 breach worth ~0.70 TWh of real 2025 coal with the
   correct measured replacement already committed; the Martin Lake entry needs
   the CAMPD detector's whole-year-zero blind spot addressed before its hardcode
   can be retired. Both are default-changing, so neither belongs in this lane.
5. **The derived artifacts stand as the committed measured record.**
   `data/raw/_validation-source/ercot126_coal_availability_envelope.json`
   (sections A–G) and the two frozen-script derivations,
   `ercot126_campd-unit-outages-short-ERCOT.csv` (82 windows) and
   `ercot126_campd-partial-outages-ERCOT.csv` (empty, header only — the measured
   negative). They are deliberately **not** placed at the paths the loaders read
   (`data/raw/campd-unit-outages-short.csv`,
   `data/raw/campd-partial-outages-ERCOT.csv`), so nothing can arm them by
   accident; promoting them is the owner's call and would be its own lane.
6. **Three inherited owner decisions, surfaced once and NOT decided here.**
   (a) The **ERCOT-122 offer-LEVEL controlled refutation** — this session adds no
   new argument either way; it remains one `replay_keeper` away, a separate
   bundle, with DIAGNOSIS-ercot122 §5.1 as its pre-commit.
   (b) The **committed-band data gap** (SCED `Min Gen Cost` is the RT instrument
   on 82 probe days, not the DAM committed band) — flagged as existing; **not**
   fetched, transformed or approximated here.
   (c) Whether the **December-2025 SCED schema revision** warrants a re-fetch
   intake lane. This session inherits the drop unchanged; note that §3.1(b)
   removes one reason to care — the AS award block that revision drops is now
   measured full span on the DAM instrument instead.

## 6. Scope, closed items honoured, environment

No year solved, no run registered, no arm built;
`frontend/data/backcast/keepers/ERCOT.json` untouched. The session's diff against
`origin/main` is **one probe script, three derived artifacts, this diagnosis and
the calibration-log entry**. No `ScenarioConfig` field, cache-key surface, solve
path or existing artifact was touched, so no config pin moved and no existing run
can change. `scripts/data/derive_campd_unit_outages.py` was **run, never
modified** (rule 23 `[R-FROZEN-DERIVE]`: default guards, `--out` redirected to a
non-loader path; no parameter was chosen against a residual, and the two
derivations were run before their results were compared with anything).

Rule 22 `[R-HOLDOUT]`: every window is {2023, 2024, 2025}. The 60-Day DAM
`*_Jan-Mar` files carry trailing Nov/Dec-2022 delivery rows; §3.1(b) drops them
explicitly inside the probe rather than letting them into an aggregate, and no
2022-or-earlier quantity appears anywhere in this document. No LP ran. No GitHub
Actions workflow was added.

Closed lists honoured: the four coal offer-surface lanes (level, reach, upper
tail, owner split); age/temp coal derates (ERCOT-121 §1a); the EP-rebasis lane as
a C3c fix and the peak-p50/quantile-ladder legs (ERCOT-119); the pooled HH-0.50
artifacts; `ercot_zonal_gas_basis` ablations; the West/Panhandle topology split.
ERCOT-120 and ERCOT-117 §5.3 remain separate un-renumbered lanes; §5.3 routes
evidence to the latter without folding into or blocking on it.

**Environment parity.** Fresh container: the `gtc-limits` clean partition is
absent, so the "static TTC kept" fallback applies as it did for every ercot115–125
baseline; the `hydro-plant-modes` clean-partition WARNING is expected. Neither
affects this session, which builds no LP.

**Sampling bounds, carried on every number.** §§1–2 and §3.1/§3.2/§3.3 are FULL
SPAN (8760 h × 3 years). §3.4's supply curve is the committed ERCOT-124 artifact
and carries its 82-probe-day, 2024–2025 bound; the prices it is evaluated on are
full-span. §3.5's RT-derate row is ERCOT-123 §3's probe-day figure, quoted as
such and not extended.

**Test state (reported, not chased, pins untouched):** recorded in the
calibration-log entry. This session touches no `src/` code, config surface or
cache key — its diff is one new script, three new artifacts and two documents —
so no test outcome is attributable to it.
