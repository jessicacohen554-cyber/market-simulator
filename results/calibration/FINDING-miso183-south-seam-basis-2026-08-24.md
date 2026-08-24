# FINDING miso-183 — the South-seam measurement-basis question ADJUDICATED: **V-TRADE — the "+1.19 GW" is a REAL defect, not bookkeeping.** Measured MISO-South generated ABOVE its own load and pushed ~2.4 GW OUT across its boundaries in the 2025 scarce set; the real RDT bound N→S in ZERO of the 72 scarce hours of 2023–25 and bound **SOUTH→NORTH in 32 of 2025's 47** — the keeper's internal posture runs BACKWARD. The object survives on a NEW, basis-free measure (≥0.93 GW conservative), and the residual is named: the export ladder's scarce tail. NO LP

**Session miso-183 (2026-08-24).** Executes
`PREREG-miso183-south-basis-decomposition-2026-08-24.md` (committed and pushed
at `bdfda0c` **BEFORE the source hunt and before any adjudicating quantity was
computed**; the intake landed at `604e599`, the probe + record + this finding
after, in the prereg's own order). **NO LP SPENT. Keeper
`2026-08-22-miso-177-rho-measured` (`miso177_rho_B`) UNCHANGED; nothing armed,
no `ScenarioConfig` field created, no run registered** (rule 15 not engaged;
the miso-142…182 no-LP precedent). Determination unchanged: **NOT-YET on
C3a-2025 alone**, C3c the single ledgered caveat. **No matrix cell minted** —
this session tested no mechanism-in-kind (PREREG §0/§4; rule 26(b) engages via
the §5.4 queue stamp + calibration-log entry).

Instrument: `scripts/probes/_miso183_south_basis_decomposition.py` →
`results/calibration/_miso183_south_basis_decomposition.json`. New substrate:
`data/raw/miso-regional-balance/` (README there;
`scripts/data/fetch_miso_regional_balance.py`).

## 0. The verdict

**V-TRADE, by the pre-registered mapping** (PREREG §4, reduced form — Leg 3
unavailable per §5's declared reduction): Leg 2 fires `south_surplus`
(s2_mid −2.52, both interval ends ≤ −0.78, every declared sensitivity
concurring) and Leg 4 fires `wheel_clean` (D4 = −2.77 GW ≤ +0.3). 2023 concurs
(s2_mid −3.19; its most conservative interval end, −0.233, sits just short of
the −0.25 line and is reported as such); 2024 reported-only (the disclosed
EIA-930 substrate year) points the same way (s2_mid −6.09).

In words, and stronger than the mechanical rule:

1. **The real MISO-South is a net SOURCE, not a sink.** Measured
   `N_S = L_S − G_S` (the South's total intake across ALL its boundary
   meters — a construction on which internal-vs-external booking cancels) is
   **negative in all three years and widens under stress**: 2025 annual
   −1.166 GW → scarce **−2.441 GW**. The South generated above its own load
   and pushed the surplus out, hardest in exactly the hours the model is
   scored on.
2. **The model's posture is inverted.** In its own 2025 scarce hours the
   keeper binds the RDT **N→S** (into the South) in 9/47 and never S→N, while
   the **measured** RDT record shows **N→S binding in 0/47** (not one 5-minute
   row — 0/72 across all three years) and **S→N binding in 32/47** (≥1 row;
   9/47 at the ≥6/12 majority; 2024: 6/14 and 4/14; 2023: 5/11 and 0/11).
   Reality ran the wheel at its South→North limit toward the stressed
   Midwest; the model pushes energy the other way.
3. **The miso-182 "wheel at its limit" corroboration dissolves.** The
   measured scarce-hour MISO→TVA export of 2,720 MW sitting 1.4 % below the
   derated N→S limit was a numerical coincidence: the N→S constraint never
   bound in those hours, and the flow is the South's own surplus (plus S→N
   transit) going out — not a Midwest→South wheel booked at the TVA boundary.

**The object therefore survives — as a real defect, on a better basis** (§4),
and the residual is named precisely and handed forward, not built (§5).

## 1. Footing (hard gates, passed exactly)

Pool aggregate reproduces the committed miso-174 values to the millimeter
(annual net import −1.071 / −1.354 / −1.031 GW; scarce sets 11/14/47). The two
structural premises the PREREG's Leg 1 frame stands on both VERIFIED:
**(a) pair-level DIBA booking** — zero duplicate (hour, diba) rows in any year,
so one MISO↔TVA series covers every MISO–TVA tie, Midwest-side and South-side
alike; **(b) the Midwest copper plate** — max intra-Midwest zonal spread in the
keeper sidecars is 0.0000 in all 8,760 hours of all three years, so the
South−Midwest price spread is a clean RDT/RPE binding indicator.

## 2. The hunt record (H-1 NEGATIVE; H-2/H-3 POSITIVE)

Per the PREREG §5 ladder, every source probed, with verdicts:

* **MISO Data Exchange** — key-gated (standing adjudication miso-77 §2c /
  miso-174 K-PRE-4 re-confirmed; no key requested).
* **RT Data Broker RDT endpoint** — re-verified DEAD 2026-08-24: returns
  `{"error": "no data"}` pointing at the rtdataapis page.
* **`docs.misoenergy.org/marketreports/`** — the namespace has NO directory
  listing (Azure blob; the www index page 403s through this proxy), so the
  negative is name-probe-bounded: `rt_rdt.{csv,xls,xlsx}`, `rdt.csv`,
  `sr_rdt.{csv,xlsx}`, `rdt_flow.csv`, `YYYY_rdt_HIST.csv` all 404.
  `sr_nd_is.xls` (Next Day Interchange) is a per-interface FORECAST —
  probed, does not carry RDT flow; `sr_la_rg.csv` is the look-ahead report;
  `mom.xlsx` is the operating-margin forecast — neither carries it.
* **IMM/Potomac SOM + quarterlies** — RDT binding/derate figures are
  chart-only (standing adjudication; unchanged).
* **FERC** — dockets EL14-21 / ER14-1174 hold the Settlement Agreement
  framework, not a flow series; no published usage series surfaced.
  **eLibrary informational filings were NOT exhausted** — recorded as a
  coverage gap, not a negative finding; monthly grain at best (level
  corroboration only, per the PREREG).
* **gridstatus** — no RDT dataset in the public library docs; the hosted
  archive is key-gated. Corroboration-only class regardless.

**Conclusion: no retrievable aggregate RDT flow series exists for 2023–2025 at
any usable grain.** Leg 3 falls away; V-BASIS was thereby unreachable and the
adjudication rests on Legs 2 + 4 — which is exactly what the PREREG's reduced
mapping provided for. *(The binding-RECORD half of the RDT story — when, not
how much — is public and is what Leg 4 uses.)*

**What DID land (H-2/H-3):** MISO's regional **Forecasted and Actual Load**
(`rf_al`: hourly North/Central/South/MISO actual load) and **RT State
Estimator Generation Fuel Mix** (`sr_gfm`: hourly regional generation by
fuel) — full 365/366/365-day coverage, intaken to
`data/raw/miso-regional-balance/` (quarantined 2023–2025). These resolve
MISO's non-contiguous footprints at hourly grain for the first time in this
repo, and they are what makes the basis-free Leg 2 possible.

## 3. Leg 2 — the basis-free South-intake comparison

`N_S` = measured South intake (`L_S − G_S`, + into the South);
`N_S^m` = model interval (`RDT^m` from the keeper sidecar spread classifier +
the committed miso-174 seam net, vintage drift disclosed there):

| 2025 | measured `N_S` (±1h) | model `N_S^m` [lo, hi] | identity wedge |
|---|---:|---:|---:|
| annual | **−1.166** (−1.166/−1.166) | [−0.357, +2.132] | +0.315 |
| summer | **−1.837** (−1.838/−1.837) | [−1.628, +1.969] | −0.278 |
| **scarce (47 h)** | **−2.441** (−2.232/−2.454) | **[−1.508, +2.629]** | +0.486 |

2023: annual −0.936, scarce −1.438 vs model [−1.291, +2.455] (wedge +0.940);
2024: annual −1.390, scarce −2.222 vs model [−2.450, +2.266] (wedge +0.353).
Coverage 8,759/8,760 (the declared Dec-31-h8759 edge) and 47/47 in the gate
set. The whole-MISO wedge — the identity's accuracy, calibrated against
EIA-930 TI — is **±0.3 GW annually** (on a ~70 GW system) and at most
+0.94 GW in any scarce set; the PREREG's wedge sensitivity moves s2 (2025)
only within [−2.93, −2.11].

**`s2` (2025, load-bearing):** ΔN = −3.00 GW against O = +1.19 → mid
**−2.52**, interval ends [−4.26, **−0.78**]. Every reading — both interval
ends, both ±1h shifts, both wedge adjustments — is far below the −0.25
`south_surplus` line and nowhere near the +0.5 V-TRANSFER line.

**Model composition behind the interval** (the per-set classifier the PREREG
called for): of 2025's 47 scarce hours the keeper is RDT-unconstrained
(zero spread) in 38 and N→S-binding in 9; S→N never, RPE-only never, in any
year. Two semantics notes reported as declared: the binding-hour spreads
cluster at **$2–$9** — never the TCDC $40/$500 steps or the RPE $200 — so the
model's binding flow sits AT the derated limit with small duals (the interval's
[2,760, 3,000] hi end is conservative) and the armed `miso_rpe_pricing` never
fires alone; and this classifier's nonzero-spread counts (1,845/2,173/4,671)
differ slightly from miso-174 §5's separation counts (2,432/2,705/5,086) —
the ±$1 dead band; both reported.

**Reading.** Even granting the model its most-outward-flowing state in every
unconstrained hour (S→N at the full derated 2,300 MW — the interval's low
end), reality still moved **≥0.93 GW more OUT of the South boundary complex**
than the model in the 2025 scarce set. At the interval mid the shortfall is
~3.0 GW. The under-export object is real on a measure that no wheel
bookkeeping can touch — `L_S − G_S` is subregional arithmetic, not interchange
accounting.

## 4. The basis-artifact hypothesis: refuted as chartered — with one honest residue

**Refuted, three independent ways:**

1. **The sign of `N_S`.** A Midwest→South wheel booked externally requires the
   South to be RECEIVING ~2.7 GW through its boundary meters. Measured, the
   South was SENDING 2.4 GW. For the N→S-wheel reading to survive, the South
   would have to be genuinely exporting ~5.2 GW externally at the same time —
   arithmetically excluded by the pool totals (scarce E_pool +1.37) plus the
   measured whole-SWPP pair (+0.95 GW *import*, miso-174).
2. **The binding record.** The N→S constraint (`RDT_MW_SO`) has **zero** rows
   in all 72 scarce hours of three years. A wheel "running at its limit" that
   never binds its limit in the very hours it is supposed to explain is not
   running.
3. **The D4 contrast runs the wrong way for the hypothesis.** In the hours the
   real RDT DID bind N→S (summer), the pool seam swings toward **import**
   (D4 = −0.51/−0.60/−2.77 GW; 2025 majority-sample n=2, but the any-variant
   D4 −2.46 on 43 h and both other years agree): real N→S binding marks
   **South-emergency** hours (TVA leg 2025: +1.91 → −0.89 GW), disjoint from
   the Midwest-stress scarce set. The wheel-carrying signature (pool export
   elevated when the wheel runs) never appears.

**The residue, stated against the verdict's own convenience:** the measured
S→N binding (32/47 scarce hours) means an **S→N wheel** was running at its
limit in most scarce hours, and an S→N wheel with asymmetric boundary
composition (out of the South via Joint-Party ties, back into the Midwest
partly via SWPP) **can leak apparent export into the pool-basis number** — a
mirrored, smaller cousin of the chartered concern. Nothing published splits
that composition (same refusal as miso-182 §6), so the **pool-basis magnitude
(+1.19 GW) should no longer be quoted as the object's size**. The defect and
its floor are established basis-free: **≥0.93 GW (conservative interval end)
to ~3.0 GW (mid) in the 2025 scarce set, on the South boundary-complex
measure**, which no leakage can inflate. The consistency arithmetic
(`N_S ≈ S→N wheel at −2.3 + genuine external ≈ −0.14`) suggests the South's
genuine third-party trade is small and the pool number is substantially
transit — one more reason the basis-free measure replaces it.

## 5. What the object now is, and the residual handed forward (NOT built)

The C3a-2025-relevant defect at the southern boundary, restated on the new
basis: **in scarce hours the real system moves ~2.4 GW out of the South —
S→N over the RDT toward the stressed Midwest AND out east at TVA — while the
keeper moves ≈ +0.35 GW INTO the South** (interval mid; ≥0.93 GW short at the
most conservative end). Two coupled halves, both named with their mechanism
location, neither touched here:

* **The export-price half.** The armed South export ladder
  (`MISO_SEAM_LADDER_BY_YEAR[2025]["South"]["export"]`, top band **$53.00**)
  is a willingness-to-pay curve that shuts off once MISO's own price clears
  ~$53 — against a scarce set averaging $479 — so the model's South export
  collapses by construction (miso-182 §4). The precise defect location is the
  **ladder derivation's scarce tail**: `scripts/data/derive_miso_seam_ladders.py`
  Q-Q couples the measured flow-duration curve to **DA hub LMP quantiles**,
  while the scarce set is an **RT** phenomenon (RT > $200; DA foresaw a
  fraction) — a deep-export band priced at a DA quantile can never follow the
  seam into RT scarcity. **Rule 23 guard, stated now:** re-deriving the ladder
  because this residual points at it would be a frozen-derive violation UNLESS
  adjudicated as a methodology defect (the DA-vs-RT basis of the Q-Q
  coupling), and any such change is a mechanism test with leave-one-year-out
  scoring — a successor charter and an owner call, not this session's.
* **The internal-direction half.** The keeper's RDT runs N→S in scarce hours
  where reality ran S→N at the limit. This is the miso-178 §2 Midwest-slope
  reading measured directly on the constraint record: the too-cheap Midwest
  stack manufactures southward pressure. It is NOT a new lever — it is the
  same upstream object the offer family already adjudicated (miso-179/180) —
  but any future Midwest-stack candidate now has a sharp falsifiable
  prediction: **it must flip the scarce-hour RDT direction.**

## 6. Leg 5 — `ba_code="SOCO"` liveness (the miso-182 named item, resolved)

**PARTIAL: superseded in the keeper's backcast years; live in the forecast
fallback.** Trace at HEAD: the armed `miso_seam_measured_ladder` applies
`inject_miso_seam_ladder_prices` (`model/interchange/miso.py:280`, called from
the shared mc-construction at `scripts/run_calibration.py:4287`, which
`run_calibration_full.py` imports), whose `_inject_seam_ladder` core
(`model/interchange/import_nodes.py:598–628`) overwrites `mc[row, :]` for
**every** South band row, both directions, with the flat per-band ladder
prices. The `ba_code`-driven path — `seam_tranche_prices` /
`neighbor_load_shape` shaping band prices by the EIA-930 **SOCO** Demand
series (`data/neighbor_price.py:254–294`, consumed at
`model/interchange/import_nodes.py:381–424`) — is computed and then fully
displaced: **zero live pricing role in the keeper's 2023–2025**. In forecast
years the ladder registry has no entry, `_inject_seam_ladder` no-ops, and the
gas-elastic reference formula with the SOCO load shape IS live — so the
rule-14 item (the seam's reference BA is the one counterparty MISO essentially
never trades toward, and this session adds: the seam's real scarce-hour
behaviour is the South's own surplus export, which no neighbor-load shape
represents) is a **forecast-lane** representation item. Named for the forecast
program; no forecast solve here, nothing stamped.

## 7. Reported against interest

* **The 2025 majority-sample D4 is n=2.** The `wheel_clean` gate was written
  for "no elevation" and is satisfied here by a large negative on a tiny
  sample. The verdict does not rest on it: the any-variant (n=43) and both
  other years agree in direction, and Leg 2 alone establishes
  `south_surplus` on every declared sensitivity.
* **The Leg-2 model interval is wide** (the model is RDT-unconstrained in
  38/47 scarce hours, and the unconstrained band spans [−2,300, +2,760]).
  The verdict is quoted at the **conservative end** (−0.78×O) for exactly
  this reason; the mid (−2.52×O) is the narrative number, labeled as such.
* **The identity wedge is largest in the scarce sets** (+0.49 to +0.94 GW —
  SE-vs-settlement noise concentrates in extreme hours). The wedge-adjusted
  s2 range [−2.93, −2.11] (2025) never approaches the lines.
* **2023's most conservative reading (−0.233) does not clear the −0.25 line**;
  2023 concurs on the mid and on every other sensitivity, and is reported so.
* **The S→N leakage residue (§4) cuts against quoting the pool-basis +1.19**,
  the very number the charter is built around — conceded, and the finding
  re-bases the object rather than defending the number.
* **The model-side seam net is a cited pruned vintage** (`miso169_gated_A`,
  drift disclosed at miso-174); it contributes at most 0.21 GW to an interval
  whose width is ~4 GW, and the footing does not depend on it.
* **The market-reports negative is name-probe-bounded** (no listing exists);
  FERC eLibrary was not exhausted. Neither gap can hide an HOURLY series
  usable for Leg 3's β, but a monthly usage series may yet exist.
* **`rf_al` actuals and `sr_gfm` SE generation are different measurement
  bases** — that is what the wedge is for, and why no per-region wedge
  apportionment was attempted (PREREG: reported, never apportioned).
* **The 5,086-hour figure quoted since miso-174 is a model separation count**,
  not a measured RDT statistic; the measured RT RDT-proper record is sparse
  (29/66/43 any-hours per year). This finding is the first to put the two on
  the same page, and they disagree by an order of magnitude — a fact that
  itself feeds the §5 direction question.

## 8. Standing OWNER items, restated not decided

Carried forward unchanged, plus this session's sharpenings: (1) the C8
provenance-materiality floor (unrepaired); (2) committed-vs-regenerated
diagnostics exposure (unchanged); (3) `RHO_CLIP` 0.5 vs measured 0.1764
(nyiso-144); (4) **D-4, the determination posture — sharpened in BOTH
directions**: the basis question is now closed (the C3a-2025 South object is a
REAL defect of established floor ≥0.93 GW, so NOT-YET is not resting on an
artifact), **and** the queue is no longer empty: §5 names a concrete,
falsifiable successor object (the ladder derivation's DA-vs-RT scarce tail,
rule-23-gated) where miso-182 had left "every named lever adjudicated with no
mechanism surviving". Whether to charter that successor or adjudicate the
posture stays the owner's call; (5) NEW: the rule-23 adjudication named in §5
(is the Q-Q DA-basis a methodology defect?) is itself an owner decision point.

## 9. Governance

Rule 22 `[R-HOLDOUT]`: 2023–2025 only (the intake fetch refuses out-of-train
market dates; publish-edge files carry none in); MISO holds neither marker
(fail-closed); the spend freeze untouched; no re-key owed. Rule 15 not
engaged — no solve, no run registered. Rule 26(b): §5.4 queue stamp +
calibration-log entry in this session; **no cell minted** (no mechanism-in-kind
tested — the PREREG bound this in advance). Rules 5/13: the new corpus is
diagnostic/validation only, enters no solve, and its README says so. Rule 27
`[R-PUSH]`: exact on-disk bytes; every pushed blob ≥300 lines verified. No new
`.github/workflows`.

**DO-NOT-REDO honoured throughout.** Nothing re-opened
`miso_south_firm_export_block` `G` (the K-1-cleared form stays refused on the
driver; §5's named successor is the LADDER TAIL, a different mechanism-in-kind,
and it is *named*, not proposed), `miso_seam_coincident_envelope` `R` (Leg 4 is
a binding-indicator contrast on the pbc record, not a flow-envelope statistic),
`measured_interface_limits` `R`, `m2m_seam_entitlement_cap` `G`,
`import_shape_lever` `G`, `internal_congestion_split` `G`, `zonal_loss_surface`
`R`, the within-unit `measured_offer_surface` `R`, `gas_hub_basis_overlay` `R`,
`ramp_envelopes` `I`, `dam_availability_rebasis` `R`, the ordc/reserve and
dispersion families, or the **`miso_offer_spread_anchored` unspent re-open
clause** (untouched; this session may not be cited as graft evidence).

## 10. Reproduction

```
cd <repo root>
uv run --no-project --with pandas,xlrd,openpyxl --python 3.12 \
  python scripts/data/fetch_miso_regional_balance.py        # intake (cached)
uv run --no-project --with pyarrow,pandas,numpy,pydantic --python 3.12 \
  python scripts/probes/_miso183_south_basis_decomposition.py
```

Reads `data/raw/miso-regional-balance/miso_regional_{load,genmix}_<year>.csv.gz`,
`data/raw/eia-930-interchange/MISO interchange hourly.parquet`,
`data/raw/MISO_region.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
`data/raw/transfer-constraint-binding/MISO/miso_pbc_rt_<year>.csv.gz`,
`results/calibration/miso177_rho_B/hourly/system_<year>.parquet`, and the
committed `_miso174_seam_overimport_decomposition.json`. Record:
`_miso183_south_basis_decomposition.json`. PREREG: commit `bdfda0c`; intake:
`604e599`.
