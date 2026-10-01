# FINDING — caiso-150: the firm must-flow floor's **shape basis measures the wrong object**. Its rule-17 window is justified by "the measured (month × hod) median self-schedule", but the series it actually uses is EIA-930 realised **net corridor interchange** — the sum of a broadly flat price-insensitive core and a large price-elastic economic layer. Measured against CAISO's own as-submitted DAM bids (OASIS `PUB_BID_DAM`, 374 trade days, seasonally balanced), the floor forces **more price-insensitive import than CAISO's ENTIRE measured price-insensitive intertie position — in both directions combined — in 47.2 % / 48.9 % of hours (2024/2025), 4.634 / 5.705 TWh/yr, 17.0 % / 20.4 % of the forced block**. The over-forcing is concentrated overnight (h22–h05, ratio 1.24–1.39) and **grows with the DMM RA level** (5.1 % → 17.0 % → 20.4 % as the level steps 2,323 → 3,371 MW). Elasticity is therefore **REAL and the defect is PROVED direction-free**; a buildable, zero-DOF, direction-free reconciliation is specified in §F. **No solve spent, no new field, keeper unchanged** (2026-07-31)

**Keeper `2026-07-31-caiso148-nuclear-availability` UNCHANGED. NO SOLVE, no arm,
no `ScenarioConfig` field, nothing registered.** Design-first,
kill-before-solve — the caiso-129/136/140/142/143/144/149 discipline. This
session's lever was mechanism-matrix §5.2 **item 2's only live prerequisite**,
`caiso-138 §C firm-block elasticity` (caiso-143 §H inverted the dependency and
made it prerequisite **(a)**). The gate **OPENS**: the defect is proved on an
independent source and a mechanism is specified — but the **build is NOT
attempted here** (§G), because its parameter series needs its own rule-23 frozen
derive with honesty gates, and a hastily-built floor is exactly what rules
1/17/19 exist to prevent.

Instrument (committed, no LP, no solver except one fleet reconstruction):
`scripts/probes/_caiso150_firm_import_elasticity.py` (§A–§C).

---

## §A — the mechanism AS BUILT (keeper fleet, `run_year(fleet_only=True)`)

`inject_caiso_firm_import_selfschedule` (caiso-77) floors both firm tranches'
hourly `min_gen` at their **full** shaped capability `pmax × availability`:

| year | `PNW_hydro_base` | `DSW_solar_PV` | TOTAL forced | mean | forced hours |
|---|---|---|---|---|---|
| 2023 | 8.117 TWh | 10.740 TWh | **18.856 TWh** | 2,152.5 MW | 7,693 / 8,760 |
| 2024 | 11.668 TWh | 15.564 TWh | **27.232 TWh** | 3,108.7 MW | 7,994 / 8,760 |
| 2025 | 12.493 TWh | 15.496 TWh | **27.989 TWh** | 3,195.1 MW | 8,151 / 8,760 |

Every forced hour is **must-flow** (`min_gen == pmax × availability` exactly:
7,693 / 7,994 / 8,151 of 7,693 / 7,994 / 8,151). 2024 reproduces caiso-143 §B's
11.668 + 15.564 TWh **exactly**, so the reconstruction is sound.

**Gate exposure — this floor has never been window-tested by anything.**
`MECH_FIRM_IMPORT` is in **`NON_THERMAL_MECHS`** (D-2 exempt) *and*
**`MECH_ABLATION_KEPT`**, and carries **no `D4_WINDOWS` entry**. So it is
invisible to the C8 forced-share budget *and* to the D-4 off-window-binding
check. A 19–28 TWh/yr must-flow floor sits outside every legitimacy gate the
repo runs.

---

## §B — the independent source, and the identification wall it carries

**Source.** CAISO OASIS **Public Bid Data** (`PUB_DAM_GRP`, tariff §6.5.2.2,
90-day lag): every DAM bid **as submitted**, including
`RESOURCE_TYPE == "INTERTIE"` rows with `SELFSCHEDMW` (the price-insensitive
quantity) and full piecewise economic curves. It is independent of **both**
inputs the floor consumes — the DMM RA capacity table (level) and EIA-930
interchange (shape). Corpus fetched this session: **374 trade days,
1,618,533 (resource × hour) records, 1,452 masked resource seqs** — the 2023
sequential run Jan–Dec plus one full week per month across 2023/2024/2025, so
every (month × hod) bucket the floor's own shape uses has bid coverage.

**A parse defect had to be fixed first (and it is NOT only mine — see §E).**
OASIS publishes bids **run-length encoded**: one row spans the whole interval
over which a resource's bid is unchanged (`TIMEINTERVALSTART_GMT` ..
`TIMEINTERVALEND_GMT`, spans of 1–24 h). On 2024-07-10 the 1,326 intertie
self-schedule rows expand to **3,493 hour slots**. Every row must be expanded
before any hourly statistic is taken; my first pass did not, and produced a
**flat ~2.3 GW** profile that was an artifact of range start-times clustering.

**THE WALL — direction is not identifiable.** A resource that self-schedules
submits **no economic curve** (that is what price-insensitive means), and the
masked feed carries **no direction field** (`PRODUCTBID_DESC` /
`MARKETPRODUCT_DESC` are entirely NaN on INTERTIE rows). Curve monotonicity
classifies only the economic population — 149 import / 162 export — leaving
**1,141 resources carrying 94.91 % of all self-scheduled MW unclassifiable**.
There is no public crosswalk: `RESOURCEBID_SEQ` masking is the point of the
disclosure, and `derive_caiso_dam_resource_crosswalk.py` keys the *named*
outage namespace and is thermal-only by construction.

**So the measurement is a one-sided CEILING, and every conclusion below is
built to survive the wall.** Define

```
ceiling[t] = (ALL intertie self-schedule MW, both directions, unsigned)
           + (import-classified economic MW bid at or below $0/MWh)
```

The second limb is the other half of the floor's *own* definition of
price-taking conduct ("self-scheduled **or bid at/below $0/MWh**", CPUC
D.20-06-028) — an economic bid, and so invisible in `SELFSCHEDMW`. By
construction `ceiling[t] ≥` the true price-insensitive **import** position in
every hour, whatever the unresolvable split turns out to be.

Measured `ss_all`: mean **3,449 MW**, p50 3,013, hod range **2,944 (h03) –
4,387 (h19)** — a **1.49×** diurnal swing.

**Seasonal balance changed this materially and is not a detail.** On the
winter-only corpus (Jan–Feb 2023) `ss_all` read **2,291 MW and nearly flat
(1.32×)**; the balanced corpus reads **3,449 MW peaking in the evening**. A
winter-only read would have overstated the headline by ~50 % and mislocated the
peak. Any successor re-running this must keep the seasonal balance.

---

## §C — the confrontation (model's own (month × hod) grid)

| year | hours `F` > ceiling | share | forced energy above ceiling | share of forced |
|---|---|---|---|---|
| 2023 | 2,094 | 23.9 % | **0.969 TWh** | 5.1 % |
| 2024 | 4,132 | **47.2 %** | **4.634 TWh** | **17.0 %** |
| 2025 | 4,284 | **48.9 %** | **5.705 TWh** | **20.4 %** |

Diurnal detail (2024, MW):

| hod | 0 | 4 | 6 | 10 | 12 | 14 | 18 | 20 | 22 |
|---|---|---|---|---|---|---|---|---|---|
| model `F` | 4,601 | 4,384 | 3,618 | 1,229 | 962 | 1,119 | 3,754 | 4,217 | 4,543 |
| ceiling | 3,443 | 3,381 | 4,105 | 3,622 | 3,752 | 4,091 | 5,215 | 4,990 | 3,652 |
| ratio | **1.34** | **1.30** | 0.88 | 0.34 | **0.26** | 0.27 | 0.72 | 0.85 | **1.24** |

**What is rigorous (direction-free).** In 2024/2025 the floor forces more
price-insensitive import, in **47–49 % of hours**, than CAISO's entire measured
price-insensitive intertie position **in both directions combined plus every
≤ $0 import bid**. Concentrated **overnight, h22–h05, ratio 1.24–1.39**. The
masking cannot overturn this: the ceiling is an upper bound on the import limb.

**What is NOT rigorous, and must not be quoted as a result.** The midday
`ratio ≈ 0.26–0.34` reads as *under*-forcing, but midday is exactly when CAISO
**export** self-schedules are largest (oversupply), so the ceiling is at its
**most** generous there and the true import-only ceiling is unknown and probably
far lower. **The model may not under-force midday at all.** Recorded as
observed-and-unresolved.

**The defect scales with the level, which is the caiso-138 §C signature
re-measured on conduct instead of flow.** 5.1 % → 17.0 % → 20.4 % tracks the DMM
RA "Imports" level stepping **2,323 → 3,371 → 3,371 MW** while the measured
price-insensitive position stays ~flat across the three years. caiso-138 §C saw
this against EIA-930 corridor energy; this sees it against CAISO's own bid
record, which the level's own justification appeals to and had never been
checked against.

**Why the shape basis is wrong in kind, not just in calibration.**
`measured_firm_import_shape` builds `w` from realised **net corridor
interchange**. Realised net interchange = (price-insensitive core) + (economic
layer that clears differently every hour). The measured economic intertie offer
stack is **~11.7–12.9 GW and broadly flat in availability**; what swings is how
much of it *clears*. The floor attributes that entire swing to the
price-insensitive core — which is precisely the elasticity the lever asks about.
The mechanism's rule-17 declaration ("the shape **is** the window — midday the
measured base itself collapses to 0.2–1.3 GW") describes the **net flow**, not
the self-scheduled base; CAISO's bid record shows the price-insensitive position
does **not** collapse midday.

---

## §D — is this struck by caiso-138 §G? No — but the boundary matters

caiso-138 §G strikes *"re-deriving the PNW firm level/shape basis (charter ask
(a)) **as a quick fix**"*, on the ground that the basis "is real, E1-adverse, and
belongs to the upstream CA-supply lane."

This finding does **not** re-derive that basis and does not propose a level
change. It reports **new evidence, from a source never used in this lane**, that
the shape basis measures a *different physical quantity* than the mechanism
claims. Rule 28a permits re-entry on new evidence; §G's own reasoning (the basis
"is real") is what the new source contradicts. **Everything §G struck stays
struck:** no level re-derive, no naive sink re-arming, no β-dump work.

**E1-adversity is unchanged and is stated up front, not discovered later.**
Any reconciliation removes forced *cheap overnight* import, so overnight λ
**rises** — the same direction caiso-138 §C flagged. Rule 1 `[R-STRUCT]` governs:
that is not a reason to reject a structurally-correct mechanism, and equally not
a reason to adopt one before it is properly derived and pre-registered.

---

## §E — two defects found in passing, FILED not absorbed

1. **`scripts/lib/dam_public_bids/caiso.py` never expands the RLE ranges** —
   it keys every row by `TIMEINTERVALSTART_GMT` alone and does not even read the
   STOP columns. Measured on GENERATOR EN curves: **5,514 curve rows vs 12,878
   true curve-hours (2023-01-15), 6,628 vs 14,036 (2023-02-10), 9,195 vs 18,414
   (2024-07-10)** — the canonical clean datatype carries **43–50 %** of the real
   resource-hours, and the missing 50–57 % are exactly the **stable-bid** hours
   (spans ≥ 2 h). `derive_caiso_offer_surface.py` groups on
   `["resource_seq", "interval_start_utc"]` with no hour weighting, so the CAISO
   keeper input `caiso_offer_surface_measured` is derived from a population
   biased toward frequently-rebidding resource-hours. **The directional effect on
   the fitted band prices is NOT measured here** and must not be assumed —
   quantifying it is the offer-surface lane's job. Cross-ISO by construction
   (the seam is ISO-generic; CAISO is the only registered ISO today).

2. **A silent keeper-reconstruction trap.** CAISO's three firm-import flags
   (`caiso_firm_import_shape` / `_selfschedule` / `_envelope_clip`) have **no CLI
   flag and no top-level `meta.json` key**. They reach the solve *only* through
   the generic `ScenarioConfig` override channel, whose `meta.json` name is
   **`coal_prb_sigmoid_overrides`** (→ `run_year(prb_overrides=)`). A probe that
   omits that rename rebuilds the fleet with **the entire 27 TWh must-flow block
   absent** while every other CAISO mechanism still arms — the corridor split,
   the ATC cap and the RA bridge all log normally, so the fleet looks correct.
   This session hit it and lost time to it. `run_config.json` is **truthful** and
   `replay_keeper.py` is **correct**; the hazard is for probe authors only. The
   committed probe documents the rename at `_META_RENAME`.

---

## §F — the mechanism this identifies (SPECIFIED, deliberately NOT built)

**`caiso_firm_import_selfsched_clip`** — clip the firm must-flow floor, hour by
hour, at the measured DAM intertie self-schedule ceiling:

```
min_gen[t] = min( pmax × availability[t] , ceiling_(month × hod)[t] )
```

Why this form and no other:

- **Direction-free.** It uses only `ceiling ≥ true import position`, so the §B
  wall cannot invalidate it. It can only ever *remove* forcing the measured
  record cannot support, never add any.
- **Zero new DOF.** Pointwise min of two measured series — structurally the
  **same pattern as the accepted caiso-138 `caiso_firm_import_envelope_clip`**,
  which reconciled the same floor against the corridor envelope.
- **Rule 19 `[R-ONE-MECH]`.** It *reconciles* the caiso-73 shape rather than
  stacking on it, and composes with the caiso-138 clip as a second pointwise min.
- **Rule 13 forward-reproducible.** OASIS publishes continuously at a 90-day lag;
  a forecast year uses the pooled climatological ceiling exactly as the current
  shape pools its climatology.
- **Rule 17.** Driver = measured price-insensitive bid conduct; window = the
  hours the measured ceiling binds (overnight, h22–h05); forward story = the
  pooled ceiling regenerates.

**Prerequisites before any arm — why this session stops here (§G).** The ceiling
needs its own **rule-23 frozen derive** with the estimation-stage honesty gates
every comparable CAISO series carries (CV, LOYO), plus a `D4_WINDOWS` entry so
the floor finally becomes D-4 visible, a cache-key registration, and a matrix
row (rule 28c). Expected direction, stated ex ante so it cannot be spun later:
it removes **4.6–5.7 TWh/yr** of forced cheap overnight import, so **overnight λ
rises and C5a moves against the gas gap** — E1-adverse, per §D.

---

## §G — disposition

- **Lever verdict: the design gate OPENS.** Elasticity is REAL, the defect is
  PROVED direction-free on an independent source, and a zero-DOF reconciliation
  is specified. Matrix cell `caiso_firm_import_selfschedule` CAISO → **`O`**
  (chartered / in play, verdict not yet reached), not `K`/`R`/`I`/`G`.
- **Item 2 (corridor/export-path congestion) stays OPEN**, and its only live
  prerequisite is now *answered* rather than outstanding: the forced injection
  `F` is measurably too large in 47–49 % of hours, so caiso-143 §H's
  "then re-examine whether any sink is wanted, with `F` reduced" becomes
  reachable — **after** the §F derive lands.
- **No solve was spent, no field added, keeper unchanged.**

## §H — DO-NOT-REDO (new, binding)

* **Re-measuring the OASIS intertie self-schedule ceiling, its RLE expansion, or
  the direction-classification wall.** §B: 94.91 % of self-scheduled MW is on
  resources that never bid an economic curve, and the feed carries no direction
  field. The committed probe reproduces all of it.
* **Attempting to split intertie self-schedules import vs export from the public
  bid data** — by curve monotonicity (the self-scheduling population has no
  curve), by any masked-id crosswalk (masking is the disclosure's purpose), or by
  correlating against EIA-930 (that contaminates the independence this finding
  rests on).
* **Quoting the midday `ratio ≈ 0.26–0.34` as under-forcing.** §C: midday is
  where the ceiling is most generous (CAISO export self-schedules peak in
  oversupply). It is observed-and-unresolved, not a result.
* **Re-running this on a season-biased corpus.** §B: winter-only overstates the
  headline ~50 % and mislocates the diurnal peak.
* **Re-deriving the PNW firm LEVEL, or the caiso-138 §G list generally.** Nothing
  there is reopened; this finding is about the shape basis's *object*, not the
  level.
* **Building `caiso_firm_import_selfsched_clip` without its rule-23 frozen derive
  and honesty gates**, or arming it on the same flag as the caiso-138 envelope
  clip (rule 19 — two measured caps, two reconciliations, one composed min).
* **Absorbing §E's two defects into a CAISO lever session.** The RLE parse defect
  is the offer-surface lane's (and is cross-ISO by construction); the
  `coal_prb_sigmoid_overrides` trap is documentation, not a mechanism.

Carried forward unchanged: `FINDING-caiso149` §G, `FINDING-caiso148` §G,
`FINDING-caiso147` §G, `FINDING-caiso146` §G, `FINDING-caiso144` §G,
caiso-143 §I, caiso-142 §H, caiso-141, caiso-138 §G, caiso-137b §6,
caiso-131 §10.

Next number: caiso-151.
