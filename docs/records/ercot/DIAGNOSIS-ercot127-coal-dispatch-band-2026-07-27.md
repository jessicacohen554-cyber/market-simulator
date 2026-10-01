# DIAGNOSIS — ERCOT-127: the coal dispatch band is a UNIT-COMMITMENT representation gap. The min-load parameter is measured, full-span and forward-admissible — and it is not expressible on the model's plant-grain, commitment-free LP, which is why applying it there breaks 13 of the 19 price bands the keeper already passes

**Date** 2026-07-27 · **ISO** ERCOT · **Lane** ercot127-coal-band ·
**Keeper under audit** `2026-07-26-ercot115-coal-marginal-hr` (bundle
`results/calibration/ercot115_coal_floor_only`) — **unchanged by this session** ·
**Chartered by** `DIAGNOSIS-ercot126` §5.3, which closed the coal AVAILABILITY
layer and routed the residual to the dispatch band ·
**Scope fork resolved by the owner, ex ante, before any build work:**
**(a) ERCOT-127 SUBSUMES ERCOT-117 §5.3** — the band is ONE phenomenon and one
mechanism owns it (rule 19 `[R-ONE-MECH]`), so both halves are in scope here ·
**Method** Phase 1 only — the keeper's committed payload/bench plus raw sources,
through `scripts/probes/ercot127_coal_dispatch_band.py` (sections A–H), one run
of the frozen `scripts/data/derive_campd_ramp_envelopes.py`, and code traces of
the ramp, floor and mechanism-attribution paths.
**No LP was built. No year was solved. No arm was registered. No `ScenarioConfig`
field, cache-key surface or solve path was touched. No keeper file was touched.**

**Outcome: Phase 1 does NOT license a mechanism, and Phase 2 was not run** — but
for a different and sharper reason than ERCOT-122/123/124/125/126. In those five
lanes the instrument was missing, empty, mis-shaped or already live. **Here the
instrument EXISTS**: the coal committed min-load fraction is measured full span
on the same corpus, by the same derive, in the same convention as an
already-registered accepted parameter (§2). What fails is **grain**. The real
fleet's low-loading plant-hours are *units switched off*, not units at min load
(§4); the model's LP carries per-plant continuous tranches with no commitment
integrality, so it cannot tell those apart, and a plant-grain floor at the
measured value forces reality's *offline* units back on. §3 proves the
consequence ex ante with no solve: the floor fixes the keeper's two failing G1
bands and **breaks thirteen of the nineteen it already passes**. §1 refutes the
one remaining registered top-side candidate. §5 is the recommendation.

---

## 0. What is inherited, re-verified rather than assumed

| claim | source, verified this session |
|---|---|
| keeper coal 59.35 / 57.40 / 60.33 TWh; actual 60.42 / 57.62 / 62.21 | ERCOT-126 §1.1, reproduced through the same loaders |
| the keeper forces ZERO coal energy | keeper `legitimacy_diagnostics.json` — D-2 has **no COAL row in any year**; the four live floors are `chp_steam`, `reliability_floor` (CC_REGULAR + CT_PEAKER), `gas_commitment_bridge` (CC_REGULAR), `st_netload_drag` (ST_GAS) |
| the pin: 43.1 / 40.6 / 50.3 % vs actual 3.6 / 3.7 / 6.9 % | ERCOT-126 §1.4 |
| price-conditional loading, fleet-aggregate basis | §3's table reproduces ERCOT-126 §1.5 **exactly** (2024 `<$15` act 0.542 / keeper 0.494; `≥$50` 0.720 / 0.767) — a cross-validation of this lane's entire pipeline against the previous one's |
| coal is CLLIG only; ten ERCOT coal plants | ERCOT-126 §0, filters reused verbatim |

**One correction to the charter's framing, with receipts.** The charter states
the model "works the ENDS … 0.494 at <\$15, 0.767 at ≥\$50" against a real fleet
in a narrow band. On the **fleet-aggregate basis the G1 gate is written on**, the
keeper already tracks the real fleet to within 0.05 in **19 of 21** price-bands
(§3) — it fails only `<$15` in 2023 (−0.064) and 2025 (−0.069). The band defect
is real but it is **almost entirely the bottom**, and the top is already matched.
That matters, because it is the level budget the bottom-half fix has to come out
of (§3.2).

## 1. The top half — the last registered candidate, refuted ex ante

ERCOT-126 §3 exhausted the *availability* instruments. This session adds the one
**dispatch-trajectory** instrument that is already registered and was never
derived for ERCOT: `ScenarioConfig.ramp_limits` — CAMPD-measured per-plant hourly
ramp envelopes (`model/lp/rows.py::_build_ramp_rows`), default-off, in the cache
key, wired into both orchestrators and `run_calibration_full.py`, with an
artifact for **CAISO only**. Exactly the ERCOT-126 §3.2 pattern.

**Derived this session** (frozen script, default guards, `--iso ERCOT --years
2023 2024 2025`): 115 rows, 92 well-observed plants; nine of the ten coal plants
carry a measured `basis == "plant"` row, up-envelope **0.28–0.52 of pmax** — well
under capacity, so the loader's pruning rule would NOT drop them and the rows
would be built.

**It cannot touch the defect, and this is provable without a solve.** Applying
the measured envelope to the keeper's own per-plant coal series:

| year | keeper moves the envelope forbids | excess | actual's | **pin: sustain share** | **pin entered by a forbidden move** |
|---|---|---|---|---|---|
| 2023 | 111 up / 31 dn | 9.0 GWh | 0 up / 5 dn | **92.1 %** | **0.02 %** |
| 2024 | 151 up / 60 dn | 23.0 GWh | 1 up / 10 dn | **91.0 %** | **0.09 %** |
| 2025 | 165 up / 100 dn | 37.1 GWh | 0 up / 6 dn | **92.7 %** | **0.13 %** |

The pin is **91–93 % SUSTAIN**: the model is already at the ceiling and stays
there. A trajectory bound can only shave the hour a series *arrives*, and
arrivals via a forbidden move are **0.02–0.13 %** of pinned energy. Against a
23–30 TWh pin the envelope's total excess is 0.04–0.12 %. The mechanism is
**inert on this defect by construction**, and its own derive says why: the
envelope is a *max observed* move, so it "must never make the backcast fleet
unable to do something it actually did" — which is confirmed on the other side of
the table, where the real fleet violates it 0–10 times a year.

**Recorded as a clean measured negative so the lane is not reopened on it.** The
artifact is committed at a **probe path**
(`data/raw/_validation-source/ercot127_campd_ramp_envelopes_ERCOT.csv`), *not*
the loader path `data/raw/_processed-legacy/campd_ramp_envelopes_ERCOT.csv`, so
`ramp_limits` cannot arm on ERCOT by accident; promoting it is the owner's call
and would be its own lane.

**A defect found on the way, routed not fixed:** the envelope is derived on
CAMPD **gross** load and the loader applies its MW figure directly to the model's
**net** columns, so every ISO's ramp rows are ~10 % looser than the measured
capability. It is inert on this lane (the rows do not bind) but it is a real
cross-ISO basis error in a registered mechanism; the probe reports the bite on
both bases.

## 2. The bottom half — the instrument EXISTS, measured, full span, forward-admissible

`ScenarioConfig.ercot_gas_bridge_min_load_frac = 0.574` is an accepted registered
parameter identified by the ERCOT-62 derive as the **committed `LSL/HSL`
capacity-weighted p50** of the 60-Day DAM Gen Resource corpus. That derive
published CC 0.574, CT 0.744 and ST_GAS 0.205 — and **no coal row**, because coal
was not a bridge candidate then. Reproducing it verbatim for `Resource Type ==
CLLIG`:

| year | resource-hours | **cap-weighted p50 LSL/HSL** | fleet aggregate ΣLSL/ΣHSL |
|---|---|---|---|
| 2023 | 208,989 | **0.3500** | 0.3742 |
| 2024 | 228,358 | **0.3729** | 0.3926 |
| 2025 | 190,294 | **0.3705** | 0.3856 |
| **pooled** | **627,641** | **0.3636** | 0.3844 |

The aggregate column reproduces ERCOT-126 §3.1(b)'s 0.374 / 0.393 / 0.386
exactly. **This clears every admissibility test the charter puts up front
(task c):** it is a unit *registration* parameter, not an outcome — forward-
derivable for any vintage and condition-responsive (a retired unit contributes
nothing); it is FULL SPAN with all three years independently identified, so
G6's 2023 LOYO leg is not the ERCOT-124/125 killer here; and it is the same
instrument, corpus, convention and derive as a parameter the model already
carries. **Rule 19 is clean**: D-2 shows coal forcing exactly zero and none of
the four live floors touches coal, so a coal floor would stack on nothing — the
explicit reason ST_GAS was excluded from the gas bridge does not apply.

Everything about the parameter is admissible. The problem is what happens when
it is applied.

## 3. Applying it at plant grain — the ex-ante gates (charter tasks b and c)

### 3.1 G1, evaluated ex ante

The floored series is the keeper's own dispatch lifted to `0.364 ×` each plant's
monthly maximum wherever it runs below — a **hard lower bound** on the LP's
answer, since the floor is a bound the LP cannot undercut and coal above it is
in-merit. Loading vs price, fleet-aggregate basis, gate `|model − actual| ≤ 0.05`:

| | 2023 act / keeper / floor | 2024 act / keeper / floor | 2025 act / keeper / floor |
|---|---|---|---|
| `<$15` | 0.552 / 0.488 **FAIL** / 0.588 **PASS** | 0.542 / 0.494 PASS / 0.578 PASS | 0.689 / 0.620 **FAIL** / 0.693 **PASS** |
| `$15–20` | 0.615 / 0.618 PASS / 0.685 **FAIL** | 0.609 / 0.618 PASS / 0.673 **FAIL** | 0.730 / 0.737 PASS / 0.780 **FAIL** |
| `$20–25` | 0.644 / 0.646 PASS / 0.714 **FAIL** | 0.652 / 0.676 PASS / 0.724 **FAIL** | 0.754 / 0.750 PASS / 0.790 PASS |
| `$25–30` | 0.682 / 0.698 PASS / 0.753 **FAIL** | 0.696 / 0.722 PASS / 0.763 **FAIL** | 0.777 / 0.761 PASS / 0.799 PASS |
| `$30–35` | 0.689 / 0.707 PASS / 0.762 **FAIL** | 0.683 / 0.706 PASS / 0.752 **FAIL** | 0.774 / 0.760 PASS / 0.797 PASS |
| `$35–50` | 0.703 / 0.729 PASS / 0.781 **FAIL** | 0.689 / 0.720 PASS / 0.762 **FAIL** | 0.789 / 0.787 PASS / 0.819 PASS |
| `≥$50` | 0.693 / 0.710 PASS / 0.764 **FAIL** | 0.720 / 0.767 PASS / 0.801 **FAIL** | 0.801 / 0.806 PASS / 0.833 PASS |

**Keeper 19/21 pass. Floor 8/21.** The floor repairs exactly the two bands the
keeper fails — and breaks **thirteen** it already passes. G1 is the gate the
charter set precisely because ERCOT-116 fails it at 9–15 pp; the measured floor
fails it in the same direction, for the same reason.

### 3.2 C1 level and C8 forced share, declared ex ante

| floor | 2023 added TWh → vs actual | 2024 | 2025 | **C8 coal forced share** |
|---|---|---|---|---|
| keeper (none) | — → **−1.07** | — → **−0.22** | — → **−1.88** | **0.0 %** |
| 0.364–0.374 (measured) | +7.26 → **+6.19** | +5.84 → **+5.62** | +4.11 → **+2.23** | **18.3 / 16.7 / 12.6 %** |
| 0.400 (WWSIS-2 physical) | +8.13 → +7.06 | +6.60 → +6.38 | +4.70 → +2.82 | 20.3 / 18.7 / 14.2 % |

C8 would pass (12–19 % against the 30 % material-class budget). **C1 would not**:
the floor takes coal from 0.3–3 % of actual to **+4 to +10 % over**, because the
model's coal energy budget is already fully spent — §0's finding that the top is
already matched is exactly why there is no room at the bottom. This is the
ERCOT-116 arithmetic (ERCOT-126 §1.4's ceiling-rider) reproduced on the opposite
end of the band.

> **The ERCOT-123 §4 adverse-direction warning does not apply as written, and is
> superseded here.** It cautioned that raising the base of a class the model
> "already **over**-runs" adds forced energy at the bottom. ERCOT-126 §1.1
> corrected the level frame — the keeper is **under**, not over — so the floor's
> direction on *level* is toward actual for the first ~1–2 TWh. The refutation
> above is not the §4 one: it is that the floor overshoots straight past actual
> and lands 2.2–6.2 TWh **over**, while breaking the price-conditional shape.

## 4. WHY it overshoots — the finding that settles the lane (charter task a)

The charter asks whether the band is a **conduct** property or a
**representation** artifact. Both hypotheses as posed are refuted, and the true
answer is a third thing.

**The representation hypothesis as posed — "the 5-tranche per-plant curve has no
shape between floor and ceiling" — is refuted.** The keeper's coal occupies
**102 / 110 / 108** distinct loading levels at 1 % grain against the real fleet's
**135 / 134 / 128**, and its interior share (online hours strictly between 0.05
and 0.95 of declared) is **0.776 / 0.785 / 0.747** against **0.817 / 0.801 /
0.678** — in 2025 the model is *more* interior than reality. The curve has
plenty of shape. Cross-plant dispersion is right too: at `≥$50` the model's
within-hour spread across plants is 0.238–0.250 against actual's 0.232–0.275, so
the model is **not** moving its plants together.

**What is actually wrong is the tails of the per-plant distribution.** Per-plant
loading against the COP declaration, keeper vs actual:

* **p05**: keeper **0.013–0.767**, actual **0.106–0.585** — the model drives coal
  far below anything the real fleet does, on nearly every plant, every year
  (2023 W A Parish 0.026 vs 0.171; J K Spruce 0.013 vs 0.106; Martin Lake 0.058
  vs 0.233).
* **p95**: keeper exceeds **1.0** on five of nine plants (Oak Grove 1.350,
  J K Spruce 1.261, Limestone 1.196) where actual sits at 0.95–1.0 — the model
  runs plants *above* their declared HSL in the tail, which is the ERCOT-116
  envelope defect.

So the model has roughly the right total coal energy and the right central
tendency, distributed **too far into both tails**. That is one phenomenon, which
is what makes the owner's scope choice (a) the right one.

**And here is why the bottom tail cannot be fixed with a floor.** CAMPD carries
the UNIT grain the model does not. Decomposing the real fleet's *low* plant-hours
(plant at 2–35 % of its own capability — the region a 0.364 plant-grain floor
lifts), with a unit counted synchronised at a deliberately permissive `>0.10 ×`
its own maximum:

| year | low plant-hours | share of online | **units online** (fleet) | **loading OF the online units** (fleet) |
|---|---|---|---|---|
| 2023 | 14,986 | 19.2 % | **0.653** (0.885) | **0.386** (0.671) |
| 2024 | 15,600 | 20.3 % | **0.667** (0.878) | **0.425** (0.663) |
| 2025 | 8,011 | 10.8 % | **0.641** (0.836) | **0.438** (0.758) |

A real coal plant at 20 % of its capability is **not** all its units at 20 %. It
is about **two-thirds of its units online, holding 0.39–0.44** — which is §2's
measured min-load fraction, confirmed independently by conduct — **and the
remaining third shut down.**

The model's LP has per-plant continuous tranches and **no commitment
integrality** (pure LP, no MIP). "Three units at 60 %" and "one unit at 20 % plus
two off" are the same number to it. A floor applied at that grain therefore
cannot distinguish the units reality held at min load from the units reality
switched **off** — it forces both to the floor. That is precisely the 13 broken
bands in §3.1, and it is why the overshoot is largest in 2023–2024 (19–20 % of
plant-hours in the low region) and smallest in 2025 (10.8 %).

**Conduct or representation? The band is CONDUCT — real coal genuinely decommits
units rather than deep-cycling them, and the min-load it holds when online is
measured and stable at 0.39–0.44. The model's failure to reproduce it is a
REPRESENTATION gap, and specifically a unit-commitment one, not an offer,
availability, ramp or min-load-parameter gap.** The measured parameter is right;
the LP has nowhere to put it.

## 5. Recommendation — recommend-and-STOP (keeper untouched; owner decides)

1. **Phase 2 is NOT run, and no mechanism is licensed.** The single-delta
   plant-grain coal min-load floor is refuted **ex ante** on the charter's own
   G1 gate (8/21 bands against the keeper's 19/21, §3.1) and on C1 level
   (+2.2 to +6.2 TWh over actual, §3.2), with the mechanism-level reason
   established at unit grain (§4). Rule 21 `[R-DOF]`: closing the residual from
   here would require *choosing* a floor below the measured value to limit the
   damage — a residual-identified parameter, which makes it an open root-cause
   issue, not a parameter. Solving it would spend ~50 minutes to measure a
   number §3 already bounds.
2. **The ERCOT-116 envelope's standing recommendation is UNCHANGED and this
   session adds one argument for it.** It remains MEASURED-CORRECT AND PREMATURE
   (ERCOT-126 §5.2). New here: §4 shows the keeper runs five of nine coal plants
   *above* their declared HSL at p95, which is a defect only the measured
   envelope fixes. It still must not be armed until something holds coal below
   its ceiling, and **the joint arm the charter pre-authorised is NOT
   recommended**: this lane's mechanism failed its own gates, and both legs push
   coal energy the same way (envelope +5.7/+8.9/+11.0, floor +7.3/+5.8/+4.1), so
   the joint arm is predicted to fail C1 and G1 harder than either alone. No
   joint bundle was built.
3. **The successor is a UNIT-GRAIN COMMITMENT question, and it is an
   architectural decision, not a calibration lane.** §4 localises the defect
   precisely: multi-unit coal plants need per-unit commitment STATE for the
   measured min-load parameter to have anywhere to land. The model is pure LP by
   standing rule (no MIP), and the three existing P1-native bridges detect
   commitment from the P0 run pattern — which cannot help here, because the
   keeper's coal never goes to zero in P0 either, so a detector would mark it
   committed in every hour and reproduce the same blanket floor. Whether to
   represent multi-unit coal plants at unit grain (tranches as units, each with
   its own P0-detected commitment state and the §2 min-load floor) is a change
   to the fleet representation itself and needs its own charter and owner
   sign-off. **ERCOT-117 §5.3 is subsumed into this finding** per the owner's
   scope decision and should not be re-opened as a standalone base-share lift:
   §3.1 is the measurement of what a base-share lift does at the available grain.
4. **The coal band lane as a whole should CLOSE.** With ERCOT-122 (offer level),
   -123 (reach), -124 (upper tail), -125 (owner split), -126 (availability) and
   this session (dispatch band: ramp refuted, min-load measured-but-inexpressible),
   every instrument on the coal residual is now either closed or blocked on the
   unit-grain question in item 3. The residual stays **attributed**, not tuned
   (rule 1 `[R-STRUCT]`).
5. **The derived artifacts stand as the committed measured record.**
   `data/raw/_validation-source/ercot127_coal_dispatch_band.json` (sections A–H)
   and `ercot127_campd_ramp_envelopes_ERCOT.csv` (115 rows, deliberately off the
   loader path).
6. **Owner decisions surfaced, NOT decided.** All four inherited from ERCOT-126
   stand, with this session's additions:
   (a) `BIN_FORCED_DERATE_BY_YEAR` (ERCOT-126 §4.1) — unchanged, still its own
   default-changing lane; this session touched neither entry.
   (b) The **ERCOT-122 offer-LEVEL controlled refutation** — one `replay_keeper`
   away, separate bundle, `DIAGNOSIS-ercot122` §5.1 as its pre-commit. This
   session adds no new argument either way.
   (c) The committed-band data gap and the Dec-2025 SCED schema re-fetch —
   inherited unchanged; §2 further reduces the stake, since the coal min-load
   parameter is now measured full span on the DAM instrument.
   (d) **NEW — the ramp-envelope gross/net basis error** (§1): a registered
   mechanism applies gross-derived MW bounds to net columns for *every* ISO,
   including the CAISO artifact already on the loader path. Inert on this lane;
   a real correctness issue elsewhere, and default-affecting for any ISO that
   arms `ramp_limits`.

## 6. Scope, closed items honoured, environment

No year solved, no run registered, no arm built;
`frontend/data/backcast/keepers/ERCOT.json` untouched. The session's diff against
`origin/main` is **one probe script, two derived artifacts, this diagnosis and
the calibration-log entry**. No `ScenarioConfig` field, cache-key surface, solve
path or existing artifact was touched, so no config pin moved and no existing run
can change. `scripts/data/derive_campd_ramp_envelopes.py` was **run, never
modified** (rule 23 `[R-FROZEN-DERIVE]`: default guards, output relocated to a
non-loader path after the run; no parameter was chosen against a residual).

Rule 22 `[R-HOLDOUT]`: every window is {2023, 2024, 2025}. The 60-Day DAM
`*_Jan-Mar` files carry trailing Nov/Dec-2022 delivery rows; §2 drops them
explicitly inside the probe before any aggregate, and no 2022-or-earlier quantity
appears anywhere in this document. No LP ran. No GitHub Actions workflow was
added.

Closed lists honoured: the whole coal availability layer (ERCOT-126 §§2–3); all
four coal offer-surface lanes; age/temp coal derates (ERCOT-121 §1a); the
EP-rebasis lane as a C3c fix and the peak-p50/quantile-ladder legs (ERCOT-119);
the pooled HH-0.50 artifacts; `ercot_zonal_gas_basis` ablations; the
West/Panhandle topology split. ERCOT-120 remains a separate un-renumbered lane,
neither folded in nor blocked on.

**Sampling bounds, carried on every number.** Sections A–H are **FULL SPAN**
(8760 h × 3 years); §2 is 627,641 resource-hours across all three years. Nothing
in this document rests on the 82-probe-day SCED corpus — the bound that killed
ERCOT-124 and -125 — and where an earlier lane's probe-day figure is quoted
(ERCOT-123 §4's 0.42–0.46) it is labelled as such and not extended.

**Environment parity.** Fresh container: the `gtc-limits` clean partition is
absent, so the "static TTC kept" fallback applies as it did for every
ercot115–126 baseline; the `hydro-plant-modes` clean-partition WARNING is
expected. Neither affects this session, which builds no LP.
