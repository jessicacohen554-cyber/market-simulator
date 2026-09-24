# FINDING nwpp-50: no measured repair of the side-inflow gate exists, and coupling would be inert. Zero LP.

**Lane:** NWPP-50 · **Date:** 2026-09-24 · **Zero LP.** Nothing solved, nothing registered, no
`src/` change, no gate touched. No mechanism was tested, so no matrix cell moves (rule 28(b); the
NWPP-48 precedent).
**Control:** keeper `2026-09-24-nwpp-49-ror-split` (`results/calibration/nwpp49_ror_span`).
**Probe:** `scripts/probes/_nwpp50_sideinflow_phase0.py` → `results/calibration/_nwpp50_sideinflow_phase0.json`.
**Intake:** `data/raw/nwpp-hydro/usgs/` (7 USGS daily-discharge gauges, 2023–25, README + SHA256).

## 0. In one line

**Step 1 fails, so steps 2–3 have nothing to build.** The seven links do not fail on a spill-metering
artefact that a better basis would remove. Adjacent federal dams' outflow records disagree by
**2–6 % even in months with no spill**. No measured, citable correction exists in CROHMS or USGS.
Even if the links were coupled, the prediction is **INERT**: rows of the same construction are
already slack in every hour of the keeper, and no new row would reach Grand Coulee. **No solve is
proposed.**

## 1. Step 1: can the gate pass without loosening 2 %?

The gate is applied verbatim: floor > 2 % of arriving water in any plant-month → STOP. The threshold
is unchanged.

| test | result | verdict |
|---|---|---|
| NWPP-36 basis (`Flow-Out`), reproduced | STOP months RRH 6 · PRD 13 · MCN 6 · JDA 3 · TDA 15 · LGS 13 · LMN 1 | identical to FINDING-nwpp-36 §3.5 |
| **(a) turbine-flow basis** (`Flow-Gen + Flow-Spill`, NWPP-36 §7 item 1a) | RRH 2 · PRD 2 · MCN **17** · JDA 1 · TDA **26** · LGS 14 · LMN 2 | **all 7 still fail; 4 get worse** |
| **(b) independent mainstem gauge** (USGS 14105700 below The Dalles) | TDA / USGS monthly ratio 0.78–1.21; 27 of 36 months off by > 2 % | **unusable:** the gauge's error is ~10× the tolerance |
| (b) USGS 12472800 below Priest Rapids | ratio 0.945–1.036 | tracks the dam record; not an independent check |
| **(c) gauged-tributary closure** (below) | bias present with **zero spill** | **premise falsified** |

**Why (a) fails.** `Flow-Out` is not `Gen + Spill`. It also carries non-power outflow (fish passage,
locks): BON 6.3 %, TDA 3.6 %, MCN 3.2 % of outflow, but only 0.2–1.2 % at the upstream plants.
Dropping that water from both sides takes more from the downstream plant, so the residual grows.

**Why (c) matters.** The closure is downstream outflow minus upstream outflow minus the USGS-gauged
tributaries between them, as a % of upstream outflow:

| link | no-spill months: mean (range) | spill months: mean (range) |
|---|---|---|
| JDA → TDA (Deschutes gauged) | **−4.4 % (−5.7 to −2.1)**, n = 21 | −8.8 % (−11.1 to −6.2), n = 15 |
| MCN → JDA (John Day, Umatilla) | +0.3 % (−4.2 to +4.3), n = 17 | +0.7 % (−5.5 to +4.4), n = 19 |
| PRD + IHR → MCN (Yakima, Walla Walla) | −0.9 % (−4.9 to +1.6), n = 13 | −1.6 % (−5.3 to +8.4), n = 23 |

* At JDA → TDA, water goes missing **every month**, spill or not. So the turbine-flow ratings
  disagree too, and spill season roughly doubles the gap.
* NWPP-36's side-inflow term had hidden this. In winter the Deschutes happens to fill the gap, so
  the floor only tripped in summer. The "spill-metering artefact" reading is **half right**.
* Elsewhere the error is two-sided noise of ±4–8 %. A per-link scale factor would be fitted to the
  very residual the gate tests. Rules 1/13 forbid that, and no published correction exists.

**Answer:** no measured, pre-registrable repair exists. The 7 links stay uncoupled and the gate
stays frozen (rule 21). **Step 2 is not reached**: no artifact is rebuilt, no link changes.

## 2. Step 3: what coupling would do anyway (the lesson built in)

Even in the counterfactual where all 7 links coupled, the prediction is INERT, for three reasons.

**(i) Grand Coulee's within-day freedom is untouched.** WEL → RRH still fails celerity and RIS → WAN
still fails τ, whatever happens to the side-inflow gate. So no new row connects GCL / CHJ / WEL to
the lower river. That is exactly NWPP-49's re-absorption path, left open.

**(ii) Rows of this construction are already slack.** Keeper sidecar, every coupled plant-year:

| plant | pond (h of mean outflow) | hours with row dual > $1 (2023 / 24 / 25) | hours pond at 0 |
|---|---|---|---|
| RIS | **1.0** | 0 / 0 / 0 | ≥ 8,755 |
| CHJ | 3.8 | 0 / 0 / **5,808** | 8,197–8,710 |
| IHR | 5.9 | 0 / 0 / 0 | ≥ 8,686 |
| BON | 6.9 | 0 / 0 / 0 | 8,760 |
| WEL | 7.0 | 0 / 0 / 0 | ≥ 8,754 |

The ponds are never used, because the flat measured spill plus side inflow on the right-hand side
leaves spare water in every hour. So the downstream plant can turbine whatever shape its upstream
sends. The new plants' ponds (PRD 5.1, MCN 7.6, JDA 14.7, TDA 2.0, LGS 13.6, LMN 4.7 h) are no
smaller than Rock Island's 1.0 h, which never binds. The lower-river links are also τ = 0 (PRD → MCN
13 h aside), so the chain can swing in phase.

**(iii) The ceiling is below C4 anyway.** Per FINDING-nwpp-48 §2, perfect intra-day timing at the
model's amplitude gives coal r of only 0.693 / 0.653 / 0.701. The daily term carries 70–87 % of the
measured variance.

**Pre-registered prediction (if it were ever armed):** hydro intra-day sd ratio moves < 0.010 in
every year (INERT limb); coal r and r_intra move ≤ ±0.005; hydro annual energy moves 0.000 TWh.
No evaluator is committed, because no admissible arm exists to evaluate.

## 3. Step 4: to the owner

**Recommendation: no solve.** Nothing admissible can be armed, and the counterfactual is predicted
inert. LP cost avoided: 3 year-isolated shards, ~60–100 min each.

What would change this, routed rather than acted on:

1. **Required fish spill as a floor on `S_d`.** The rows are slack because measured spill enters as
   water the turbines may use. Real ROD / Fish Operations Plan spill is mandated. It is published per
   year, so it has a forward story. Stating it as `S_d ≥ published spill` would make spill-season rows
   bind at BON / IHR.
   * **Predicted small for C4:** it covers 1.7 GW, spill months only, and GCL is still untouched.
   * **It is a structural accuracy item** (rule 1), not a C4 lever. It needs a design PRECOMMIT.
2. **The C4 lever is not intra-day hydro.** (iii) caps it. FINDING-nwpp-48's daily-placement term,
   together with Jim Bridger's coal inputs, is where the r lives. The owner's open card D2
   (`eia860_vintage_tracks_solve_year`) is still the named item.
3. **An independent flow measurement of the lower river** is the only thing that could reopen the
   gate. Candidates are acoustic gauges at the dams or BPA's modified-flow study. Neither is in hand.

## 4. Reported, not absorbed (inherited, unchanged)

* C1 demand-basis gap −7.6 / −10.0 / −7.1 TWh (open owner decision, FINDING-nwpp-45 §8).
* C5a CO2 is reported-only FAIL.
* Jim Bridger has no COAL row in `thermal_tranches_NWPP.csv`.
* The NWPP-40/41/42 attestation corrections are still owed.
* D2 / D3 are deferred.
* The budget and envelope duals are written to no sidecar.
* The leftover `claude/nwpp-49-ror-{2023,2024,2025}` refs: `git ls-remote` returns **none** at this
  writing, so they are already gone.

## 5. Retrievability

Nothing was solved, so no bundle exists. The committed artifacts are the probe, its JSON record, the
USGS intake and this doc.
