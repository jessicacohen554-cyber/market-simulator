# FINDING — ercot-240 (2026-08-30): the event-hour "demand gap" is the DC-TIE NET IMPORT IDENTITY, exactly and everywhere — the model's demand input is NOT understating real demand (it serves the measured net-generation boundary, correctly), the phase-0 §0.5/§4 framing is re-adjudicated, and all three chartered demand-source candidates (4CP/load response, 930-vs-MIS boundary, weather-hour alignment) are REFUTED as gap carriers under the precommitted rules

**Session ercot-240, 2026-08-30, designated branch
`claude/ercot-240-demand-gap-xbdwn5`. ZERO-SOLVE — every number below is
read from committed artifacts and raw measured inputs (the
`ercot236_k33_clip` keeper sidecar, the EIA-930 wide extract, the ERCOT MIS
native-load record NP3-565-CD, the committed actuals parquet, the committed
ercot-239 JSON); the model demand series is recomputed through the engine's
own loader and gated against the sidecar.** Precommit
`docs/PRECOMMIT-ercot240-eventhour-demandgap-2026-08-30.md` pushed +
blob-verified before any measurement; no amendments were needed (§1 notes
one within-convention join-mechanics detail). Probe:
`scripts/probes/ercot240_eventhour_demandgap.py` →
`results/calibration/ercot240_eventhour_demandgap.json` (committed).
Charter: FINDING-ercot239 §6 OBJECT 2 only (owner 2026-08-30 PM charter);
objects 1 and 3 untouched. The two-config keeper structure is UNTOUCHED; no
input changed; no lever armed or tested; no matrix cell changes (nothing
tested). Reads ⊂ {2023}.

## 0. Verdict in five lines

1. **The gap IS the netted DC-tie import — exactly, at every hour.** The
   ERCOT demand loader serves `EIA-930 Demand + Total interchange` (a net
   import lowers what the internal fleet must serve), so the phase-0 metric
   `930 Demand − model demand` is `−TI` by construction. Measured: identity
   residual **0.0 MW at p50/p95/p99/max over all finite 2023 hours**, 0
   hours above 1 MW, identity share **1.000** over the 14 event hours,
   year-mean gap 97.6 MW = year-mean net import 97.6 MW. (M-1; A-d CARRIES,
   P1 confirmed.)
2. **Nothing is missing from the model's energy balance.** The extract's own
   identity `Demand = Net generation − TI` holds to ≤ 1 MW (p95), so the
   model's served demand ≡ measured ERCOT **net generation** — what the
   real internal fleet actually produced in those hours. Reality met these
   hours with the ties importing near capability (SWPP at 807–815 MW
   import in 10 of 14; import level ≥ p85 of load-matched control hours in
   9 of 14); the model correctly serves the correspondingly reduced
   internal-fleet load. The two hours whose gap sat below the +651 MW
   family floor (h2971 +218, h7001 +111) are exactly the two hours the
   ties were NOT importing near max.
3. **(b) the EIA-930-vs-MIS settlement boundary is real but carries NONE of
   this.** 930 `Demand` runs **~+260 MW above** the MIS native-load total
   on a typical 2023 hour (p50 +267, p95 +504) — a level property of the
   boundary. At the event hours the wedge is SMALL (median +100 MW, |w|
   median 115) and the event excess over month/hod/load-matched controls
   is **negative** (median −143 MW; positive in only 2 of 14, max +120).
   The wedge *collapses* under scarcity — median +274 MW at RT < $50 vs
   **+30 MW at RT ≥ $500** — the storage/WSL-treatment signature, the
   OPPOSITE direction of a gap carrier. (M-2/M-4iii; A-b refuted, P2
   confirmed.)
4. **(c) weather-hour alignment is clean.** Best lag = 0 in every DST
   regime (CST-early/CDT/CST-late/full-year) for both level joins (model
   vs 930 corr 0.9997 at lag 0; native vs 930 0.9999), per-event-hour
   local best lag = 0 in **14 of 14**, and zero hours pass the
   ramp-support test. The one alignment fact found is the one code
   reading predicted: the zonal-shares parser's wall-clock grid rides
   **+1 h vs the positional clock during CDT** (5,710 hours) —
   system-total-neutral by construction (share columns sum to 1), reported
   for the owner queue in §5. (M-3; A-c refuted, P3 confirmed.)
5. **(a) 4CP / load-resource response does not separate the boundaries.**
   In 4CP-candidate windows (Jun–Sep top-8 native-peak days, HE 16–18) the
   wedge again SHRINKS (+108 vs +206 MW in same-month/same-hod
   non-window hours), and at the event hours the two series dip/peak
   TOGETHER (median |dip₉₃₀ − dip_native| = 56 MW against dips of up to
   ~950 MW). Real load response is present in BOTH measures — correct
   representation, not understatement. (M-4; A-a refuted, P4 confirmed.)

## 1. Gates and constructions

* **V-0 PASS:** the recomputed population {h : model < $200 ∧ actual ≥
  $500} is exactly the committed 14-hour family; price constructions
  byte-identical to ercot-239/237.
* **V-1 PASS at 0.0 MW:** `load_demand("ERCOT", 2023, td_loss_factor=0.0,
  include_interchange=True, ercot_tie_zonal_interchange=True)` summed over
  zones equals the keeper sidecar's per-hour system demand with max |Δ| =
  0.0 MW — the decomposition is of the keeper's own input.
* **Native join gates PASS:** the NP3-565-CD hour-ending labels tz-joined
  onto the extract's UTC axis land 8,760/8,760 exact matches, strictly
  monotone. Join-mechanics note (within the declared convention, no
  measurement had run): the interval ending exactly AT a DST transition
  has no resolvable hour-ending wall stamp, so the probe localizes the
  hour-BEGINNING stamps (fall-back duplicate disambiguated by the file's
  own `DST` marker) and adds 1 h — verified end-to-end by the two declared
  gates.
* Extract completeness: `Demand` has zero missing 2023 hours;
  `Total interchange` has 6 (none at event hours; the loader interpolates
  them; identity stats computed on finite hours).

## 2. The central table (full rows in the committed JSON)

| h | mo | gap (930−model) | −TI (net import) | identity resid | wedge w (930−native) | w excess vs controls | SWPP tie |
|---|----|-----------------|------------------|----------------|----------------------|----------------------|----------|
| 2058 | 3 | +786 | +786 | 0.0 | +62 | −183 | −596 |
| 2971 | 5 | +218 | +218 | 0.0 | +210 | −81 | −218 |
| 4578 | 7 | +724 | +724 | 0.0 | +155 | −89 | −814 |
| 4623 | 7 | +743 | +743 | 0.0 | −85 | −261 | −743 |
| 4626 | 7 | +651 | +651 | 0.0 | +224 | −12 | −812 |
| 5369 | 8 | +815 | +815 | 0.0 | +123 | −69 | −815 |
| 5484 | 8 | +815 | +815 | 0.0 | +52 | −104 | −815 |
| 5777 | 8 | +814 | +814 | 0.0 | +324 | +26 | −814 |
| 5943 | 9 | +815 | +815 | 0.0 | −181 | −227 | −814 |
| 5945 | 9 | +808 | +808 | 0.0 | −49 | −198 | −814 |
| 6399 | 9 | +815 | +815 | 0.0 | −31 | −211 | −814 |
| 7001 | 10 | +111 | +111 | 0.0 | +108 | −190 | 0 |
| 7145 | 10 | +776 | +776 | 0.0 | +414 | +120 | −814 |
| 7480 | 11 | +873 | +873 | 0.0 | +91 | −226 | −807 |

Reading: the gap column and the net-import column are the same number in
every row — the +651…+873 MW "12 of 14" family is the hours the DC ties
imported 651–873 MW, and the +98 MW year mean is ERCOT's 2023 mean net
import. Control-set caveat: the September/November rows have thin matched
control sets (2–7 hours; high-load non-event RT < $100 peers are scarce in
those months) — the A-b refutation does not lean on them (the event wedge
itself is already an order of magnitude below the gap).

## 3. Prior grading (declared ex ante, graded as declared)

* **P1 CONFIRMED / A-d CARRIES:** 14/14 event hours within the 25 MW
  identity tolerance (all at 0.0), 0 refuting hours, identity share 1.000
  (declared ≥ 12, ≥ 0.95).
* **P2 CONFIRMED / A-b REFUTED:** median event wedge +99.5 MW (declared
  carrier needs ≥ 300) with negative median event excess (−143 MW;
  declared carrier needs ≥ +300).
* **P3 CONFIRMED / A-c REFUTED:** lag 0 wins in every regime on both
  joins; 0 of 14 event hours show nonzero local lag (declared carrier
  needs ≥ 7 with ramp support); the shares-parser CDT offset is present
  exactly as predicted (CST: offset 0 for 3,048 h; CDT: offset +1 for
  5,710 h; the two stray rows are the transition hours themselves) and is
  system-neutral.
* **P4 CONFIRMED / A-a REFUTED:** 4CP-window excess −98 MW and
  price-conditioned excess −244 MW — both below the 300 MW materiality
  line AND of the wrong sign to carry a positive gap.
* **P5 CONFIRMED (disposition):** no input change is warranted; see §4.

## 4. Re-adjudication of the phase-0 framing

FINDING-ercot239 §0.5/§4 read the gap as "an event-hour demand
understatement — ~0.7–0.9 GW of the tightness reality priced is absent
from the model's energy balance before conduct even enters." That framing
is **withdrawn by measurement**: the 0.7–0.9 GW was served by the DC ties
in reality, so it was absent from the REAL internal fleet's energy balance
too. The model nets the measured tie schedule into served demand (a
rule-13-admissible measured market input with a forward analogue — the
priced import node), and its served demand equals measured net generation
to ≤ 1 MW. There is no demand-side contribution to the 14-hour miss
family: the misses stand fully on the ercot-239 conduct/renewables
adjudication (its objects 1 and 3, not chartered here). The +98 MW year
mean the phase-0 quoted as a base rate is the year-mean net import, not a
bias. The event-hour signal that IS real: the ties sat at/near maximum
import in exactly these hours (§0.2) — scarcity-consistent measured
behavior the backcast already carries by construction.

## 5. Named observations for the owner queue (named, NOT armed — nothing tested)

1. **Metric hygiene (docs/diagnostics only):** any future demand-gap
   diagnostic should compare like boundaries — model served demand vs
   `930 Demand + TI` (≡ net generation), or `930 Demand` vs model demand
   with TI added back. The ercot-239 probe's `gap_base_rates_mw.demand_*`
   and per-row `gap_components_mw.demand` are cross-boundary numbers and
   read as bias where none exists. No engine surface is involved.
2. **Forecast-lane representation question (the one substantive item):**
   the backcast nets the MEASURED tie schedule, which reality set to
   near-max import under scarcity (SWPP 807–815 MW in 10/14 event hours;
   ≥ p85 of load-matched controls in 9/14). Forecast mode has no measured
   schedule — the priced-interchange/import-node lane should be checked
   for whether it reproduces scarcity-coupled max-import behavior at the
   ERCOT DC ties. This is a forecast-default matrix question for the
   owner's queue, not a backcast defect ([R-MECH-MATRIX] duty (a) applies
   to whoever picks it up; this session tested nothing).
3. **Zonal-shares CDT wall-clock offset (small, zonal-only):**
   `parse_ercot_shares` builds its share grid on the wall-clock
   month/day/hour formula, which rides +1 h against the positional clock
   the demand series uses for the 5,710 CDT hours (measured: offset +1 in
   5,710/5,711 CDT rows, 0 in 3,048/3,049 CST rows). System totals are
   unchanged by construction (columns sum to 1); the effect is a one-hour
   lag in the slow-moving ZONAL weight shapes for ~65 % of the year. A
   repair is a data-handling fix under [R-ACCURATE] scope for a separate
   owner-visible round (it perturbs every ERCOT/PJM-style zonal solve
   input by a small amount and so needs its own before/after gate run,
   and the same formula is shared by other ISOs' parsers — check each).
4. **The ~+260 MW 930-vs-native level wedge (document-only):** EIA-930
   ERCO `Demand` runs +260 MW (p50) above the MIS native-load total,
   seasonal (Jun–Nov ~+300–372, Dec–Jan ~+130–142), largely
   load-level-flat, collapsing to ~+30 MW at RT ≥ $500 — consistent with
   a consumption category the native TAC boundary excludes and 930
   includes that switches off under scarcity (wholesale storage charging
   is the natural candidate; not further attributed here). Matters only
   if a future round proposes swapping the ERCOT demand basis; the
   current basis is internally consistent and correct for the fleet
   boundary.

## 6. Disposition

Characterization complete: zero solves, zero input changes, nothing
armed, keeper structure untouched, kills K-1..K-3 honoured (no amendment
needed; the residual-mass clause never fired — there is no residual
mass). Deliverables: the pushed precommit + probe + JSON + this FINDING +
the calibration-log entry. The chartered question — WHICH root cause
carries the gap — is answered: **none of the three chartered demand-source
candidates; the gap is the comparison-frame identity on the model's
(correct) interchange-netting demand construction**, with (a)/(b)/(c)
each refuted by its own precommitted discriminator. The owner queue above
inherits the two follow-ups worth anything (forecast-lane tie behavior;
the zonal-shares clock repair).
