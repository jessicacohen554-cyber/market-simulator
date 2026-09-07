# FINDING miso-234 — the South seam is a REPORTER of the North–South separation deficit, not an object of its own. Zero LP, no arm, no cell verdict moves.

**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`).
Determination **re-verified from committed artifacts only** (`scripts/calibration_verdict.py
--run-id`, never a solve): **CALIBRATED**, C3c the single ledgered caveat, C1 16/16 all-class /
12/12 free-class, C2 / C3a / C3b / C4 / C6 / C8 PASS. DOF ledger 41/2. Rule 22: 2023–2025 only;
MISO holds no `complete` marker and **no holdout year was solved, scored or registered**.
Nothing was registered, pruned, armed or promoted.

**PROVENANCE CARRIED FORWARD (rule 1 `[R-STRUCT]`), stated first and unsoftened.** miso-233's
screen PASSED all four of its pre-registered structural gates. The keeper it was promoted FROM
(miso-232) did not: the **miso-231 screen was KILLED on its pre-registered G-1 bar by 0.0183**,
the bar was not moved, and miso-232's span existed only by **OWNER RE-CHARTER**. Neither is
written up as the other here.

---

## 0. What this session is, and the limit that follows from it

Four zero-LP measurements on the keeper's **committed** sidecars, payload, bench parts and
measured input series. No LP was solved, no bundle produced, no `ScenarioConfig` field created
or armed.

**A PREREG was NOT pushed ahead of these measurements**, so — unlike miso-182 / 184 / 185 / 206,
each of which committed a decision rule before any adjudicating quantity — **this session is not
entitled to close, refuse or re-open anything on these numbers, and it does not.** No cell
verdict moves in the MISO shard; evidence is appended and the lane is re-routed. Where a number
here agrees with a standing adjudication, the adjudication is the finding and this is
corroboration on an independent instrument.

Part C exists because the owner asked, mid-session, why MISO wind is overproducing and whether
MISO HSL data is needed. It is answered in §3.

---

## 1. Part A — the measured South seam IS price-responsive; it responds to the price of the
zone it terminates on, and the residual is scored on the wrong one

`scripts/probes/_miso234_south_seam_character_phase0.py` →
`_miso234_south_seam_character_phase0.json`. Sign convention **export-positive** (MISO → the
southern DIBA pool). Deciles are of the stated basis; slope = cheapest-decile mean − dearest.

The lever queue's item 1 asks whether the seam is "even a price-arbitrage seam", proposing that
near price-independence is the Entergy–MISO RDT firm-contract signature. **The measured record
says the premise is basis-dependent, and the answer changes with the basis:**

| year | basis | pearson | spearman | export decile slope |
|---|---|---:|---:|---:|
| 2023 | MISO Indiana hub DA (**the scored basis**) | +0.029 | −0.067 | −125.4 MW |
| | **MISO-South zonal DA** (the bus the seam terminates on) | −0.107 | **−0.193** | **+323.3 MW** |
| 2024 | Indiana hub DA | −0.059 | −0.064 | −10.2 MW |
| | **MISO-South zonal DA** | −0.133 | **−0.176** | **+426.8 MW** |
| 2025 | Indiana hub DA | +0.141 | +0.082 | −636.4 MW |
| | MISO-South zonal DA | +0.064 | −0.001 | −235.6 MW |

On the **local** price the seam carries the correct arbitrage sign in 2023 and 2024 — export
falls as the South price rises — and a decile slope of +323 / +427 MW. On the **Indiana hub**
basis, which is the basis the residual decile slope is scored against, the same flow reads flat.
So "the South seam is price-independent" is a statement about the *comparator*, not about the
seam.

Firmness, against the firm-block reading: lag-1 autocorrelation **+0.95 / +0.95 / +0.96**, but
mean absolute hour-to-hour change **203 / 206 / 213 MW (15–21 % of the mean)** and
between-month variance share only **0.11 / 0.13 / 0.34**. It is persistent and smooth, **not** a
monthly-stepped contract block. The p10 "always-exported base" is 34 / 212 / **−200** MW — in
2025 the seam is a net importer in more than a tenth of hours, which no flat block represents.

Per counterparty (2025 shares of gross export; miso-182's premise correction reproduced):
**TVA 85.8 %**, LGEE 12.6 %, AECI 1.4 %, **SOCO 0.2 %**, SIKE 0.0 %. MISO is a **net importer**
from SOCO in all three years (−598 / −617 / −665 MW) and from AECI in 2024–25 — and SOCO is the
BA the model's South interface names as its `ba_code`.

## 2. Part B — the South seam's wrong-signed slope is INHERITED. 56–68 % of it is the model's
missing North–South price separation, measured at zero LP

`scripts/probes/_miso234_ns_separation_phase0.py` → `_miso234_ns_separation_phase0.json`.

**The model's South price carries no independent South information at all.** From Part A:
`corr(model MISO_external_South bus, measured South DA)` = +0.712 / +0.569 / +0.665 against
`corr(same bus, measured Indiana hub DA)` = +0.711 / +0.597 / +0.725 — identical to within 0.06
in every year. Whatever the South seam clears on, it inherits the Midwest price's decile
structure.

Separation Indiana − South, $/MWh:

| year | mean\|·\| measured | mean\|·\| model | p90\|·\| measured | p90\|·\| model | corr(I,S) measured | corr(I,S) model | **compression** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 6.19 | 0.91 | 13.56 | 3.53 | +0.771 | +0.947 | **0.148** |
| 2024 | 6.95 | 1.49 | 14.20 | 4.02 | +0.854 | +0.891 | **0.215** |
| 2025 | 10.15 | 2.86 | 24.29 | 9.18 | +0.771 | +0.913 | **0.281** |

**The decisive counterfactual, zero LP.** Same ladder, same envelope, same band grid — the ONLY
change is that the South bus price carries the measured separation
(`p_cf(t) = model Indiana price − measured (Indiana − South)`), holding the model's own Midwest
level fixed:

| year | export slope, model | → counterfactual | measured | mean export model → cf (measured) | **gap closed** |
|---|---:|---:|---:|---|---:|
| 2023 | +1,025.7 | **+386.1** | −125.4 | 754 → 1,164 MW (1,071) | **55.6 %** |
| 2024 | +1,274.7 | **+396.8** | −10.2 | 1,020 → 1,502 MW (1,350) | **68.3 %** |
| 2025 | +966.5 | **−45.8** | −636.4 | 667 → 1,208 MW (1,031) | **63.2 %** |

**THIS COUNTERFACTUAL IS INADMISSIBLE AS A MECHANISM AND IS NOT PROPOSED AS ONE.** Feeding a
measured price separation back into the bus the LP clears on is precisely the rule-13
`[R-MEASURED]` outcome pin. It is used here only to *size which object owns the residual*, and
what it says is that the majority of the South seam's wrong-signed slope is not in the seam.

**Consequence for the lever queue.** Item 1's two candidate remedies are already adjudicated and
this session does not re-test either (rule 28(a) DO-NOT-REDO):

* a **firm/scheduled South export block** — `miso_south_firm_export_block` **G** (miso-182,
  refused on the wheel-vs-external-sale decomposition criterion; the re-open executed and
  **closed negative** at miso-185, verdict V-NEG-ABSENT, the FERC EQR data does not exist);
* an **hourly neighbour anchor or any price rebasis of the export ladder** —
  `miso_south_export_ladder_rt_tail` **R** (miso-184: the measured South export is
  price-inelastic against *every* basis and **no monotone willingness-to-pay sink ladder driven
  by any single price series** can carry an export that persists at the top of the price
  distribution), and no published SOCO/TVA hourly price exists to anchor on in any case.

Both refusals are **corroborated, not weakened**, by Part A: the seam's real response is to a
*local* price the seam ladder does not see, so a better neighbour anchor was never the fix.
The residual routes upstream, to an already-open lane: miso-211 measured the model's
Indiana−South separation at **−$0.16 against a measured $58** in the 177 real RDT-binding 2025
shoulder hours and attributed it entirely generation-side (South gas priced out, 3.5 GW idle
within $20 of the model's South price), and miso-212 decomposed that into the gas cost
convention (~2.1 GW, owner-court, `gas_marginal_commodity_pricing` **O** / `gas_variable_transport`
**O**), the basis layering (closed at miso-213) and offer conduct. The zonal-grain half is
`internal_congestion_split` **G**, whose miso-79 NO-BUILD stands fundamental.

**Item 1 is therefore CLOSED AS A SEAM OBJECT and re-routed. No lever is licensed by this
session.**

## 3. Part C — MISO wind overproduces because the LP re-curtails ZERO of the gross-up.
MISO HSL data would not fix it

`scripts/probes/_miso234_wind_curtailment_phase0.py` → `_miso234_wind_curtailment_phase0.json`.
Asked by the owner mid-session.

MISO publishes no hourly HSL/curtailment series, so MISO wind takes the `forecast_uncurtailed`
reference-rate gross-up: the delivered EIA-930 profile grossed up by the Potomac Economics (MISO
IMM) measured annual curtailment rate — **4.895 %**, ×1.05147 — and the LP is expected to
re-curtail endogenously.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| wind actual, EIA-930 delivered (TWh) | 91.715 | 98.251 | 98.938 |
| uncurtailed potential = actual × 1.05147 | 96.435 | 103.308 | 104.030 |
| wind MODEL | 96.435 | 103.308 | 104.034 |
| **model re-curtailment, % of potential** | **0.001** | **0.000** | **−0.003** |
| reported curtailment | 4.895 | 4.895 | 4.895 |
| wind residual (TWh) | +4.720 | +5.057 | +5.096 |
| **share of the residual that IS the gross-up** | **100.0 %** | **100.0 %** | **99.9 %** |

Solar is the control at −0.0003 / −0.0003 / −0.0032 TWh (delivered-pinned). The reconstruction
closes to ≤0.004 TWh.

This **reproduces `vre_reference_rate_curtailment_grossup` (cell K, miso-206, 2026-09-04) to the
digit** on an independent instrument — its N-2 reads "bound = delivered/(1−0.048947) at
0.0000 MW and P1 wind ON the bound in 8,760/8,760 h every year". No verdict moves.

Why nothing is curtailed — internal congestion is nearly absent:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| mean max−min zonal price spread, MODEL ($/MWh) | 0.91 | 1.49 | 2.86 |
| mean max−min zonal price spread, MEASURED | 11.02 | 11.84 | 17.40 |
| **compression** | **0.083** | **0.126** | **0.164** |
| hours with every zone within $1 — model | 77.9 % | 78.7 % | 62.8 % |
| hours with every zone within $1 — measured | 1.0 % | 0.6 % | 0.1 % |

With slack and dump both 0.0000 TWh there is no channel to spill wind at all.

**Do we need MISO HSL data? Not for this, and it is blocked anyway.** An hourly series would
upgrade the bound's provenance from `forecast_uncurtailed` to `measured_potential` and give a
real hourly modelled-vs-reported curtailment benchmark — both worth having. It would **not**
close the +5 TWh: the LP already holds the +4.9 % headroom and delivers 100 % of it, and a
measured potential is *higher* in exactly the congested hours, so the residual could grow. The
binding object is `internal_congestion_split` **G**, where miso-79's NO-BUILD is recorded as
fundamental (**88–99.7 % of MISO's internal congestion mass is intra-LBA**, below the six-zone
grain; an optimal simultaneous split of all six zones captures 1.9–3.8 %) — a representation
limit, not a data gap. Access is separately shut: misoenergy.org's 5-minute curtailment
workbooks are allowlist-blocked (HTTP 403, `docs/multi-iso/miso-data-audit.md`).

**Note the coupling:** §2 and §3 are the same root object seen twice. The model's internal price
field is too flat, which simultaneously stops wind being curtailed and makes the South seam
inherit the Midwest price's decile structure.

## 4. Part D — the 2024/2025 correlation overshoot is the PJM seam, and NOT the SPP arm miso-233
just promoted

`scripts/probes/_miso234_corr_overshoot_phase0.py` → `_miso234_corr_overshoot_phase0.json`.
Correlation is exactly additive in its numerator, so
`corr(Σ_s x_s, P) = Σ_s cov(x_s,P)/(σ_total·σ_P)` is an identity and each seam carries a signed
contribution that sums to the total. Reconstruction harness `corr(recon, committed imports)` =
**+0.922 / +0.943 / +0.967**; the attribution is on the reconstruction and the committed total is
quoted beside it.

| year | | PJM | SPP | South | Manitoba | SUM |
|---|---|---:|---:|---:|---:|---:|
| 2023 | **model contribution** | **−0.3291** | +0.0186 | +0.1036 | n/a (firm block) | −0.2069 |
| | measured contribution | −0.0778 | −0.0291 | −0.0048 | +0.0568 | −0.0549 |
| 2024 | **model** | **−0.2922** | +0.0132 | +0.1126 | n/a | −0.1664 |
| | measured | −0.0573 | −0.0372 | +0.0050 | +0.0527 | −0.0368 |
| 2025 | **model** | **−0.2907** | +0.0312 | +0.0803 | n/a | −0.1793 |
| | measured | −0.0326 | +0.0188 | −0.0405 | +0.0340 | −0.0203 |

* **The PJM seam over-responds by 4.2× / 5.1× / 8.9×** on this instrument. It is the whole
  overshoot. This is the correlation-side counterpart of miso-233's own phase-0 slope reading
  (model PJM +2,377 / +2,611 / +2,704 MW against a measured +1,319 / +1,052 / +815).
* **The SPP arm promoted at miso-233 is exonerated**: its model contribution is small and
  **positive** (+0.019 / +0.013 / +0.031) in every year — it cancels part of PJM's excess rather
  than adding to it.
* **South contributes positively (wrong-signed) in the model** (+0.104 / +0.113 / +0.080) against
  a measured −0.005 / +0.005 / −0.041 — the same defect §2 attributes upstream.
* **Manitoba is inert in the model by construction** (a firm block under `miso_firm_imports`, so
  zero covariance) while contributing **+0.057 / +0.053 / +0.034** in the measured record.
* **The model's interchange under-varies overall**: total σ **1,378 / 1,558 / 1,482 MW** against
  a measured **2,105 / 2,019 / 2,437 MW**. So the model's seam moves *less* than the real one
  while being *far more* price-driven — the signature of missing non-price variation (outages,
  schedules, neighbour state), not of a price response that is merely too strong.

**No lever is proposed.** The PJM `delta_k` ladder is derived, frozen and pinned to its derive by
test; re-deriving or damping it against this residual is exactly the rule-23 `[R-FROZEN-DERIVE]`
and rule-1 `[R-STRUCT]` violation the handoff names. This is filed as an open item on the K cell.

## 5. Part E — the CC_REGULAR-2023 object is a LEVEL deficit, not a shape one

`scripts/probes/_miso234_cc_giveback_phase0.py` → `_miso234_cc_giveback_phase0.json`. Committed
bench `plants[*].campd` against the committed payload's `plants[*].m`, the same encoding the C1
scorer reads.

**The hour-level DIFF against miso-232 is NOT computable at HEAD** — that bundle was pruned under
rule 15 `[R-DASHBOARD]`'s keeper-only retention at the miso-233 promotion, and git history is the
record. The −0.132 TWh give-back is therefore reported from the miso-233 assessment and not
re-derived. The **level residual** is attributed instead, which is the larger object.

**Level warning, stated before the numbers:** the matched-plant CAMPD-gross subset (40 / 40 / 39
plants) is **not** the C1 grid-delivered basis on either side — the raw residual reads
−14.351 / −7.657 / −6.995 TWh against a C1 cell of −6.445 TWh for 2023. Only the **shape**
columns (model rescaled to the measured annual total, so every level and coverage term cancels)
are quoted as findings.

| price decile | 2023 shape deficit | 2024 | 2025 |
|---|---:|---:|---:|
| d1 (cheapest) | −97 | −44 | −813 |
| d5 | −126 | −19 | −10 |
| d10 (dearest) | **+136** | **+336** | **+464** |
| raw deficit as % of measured, d1→d10 | 9.3 → 10.6 | 4.9 → 6.9 | −1.0 → 7.6 |

* **2023 is essentially pure level.** The deficit is 9.2–10.7 % of measured in *every* price
  decile and the shape-normalised deficit spans only −126…+147 MW on a ~16 GW class (±0.9 %). A
  seam change moves the price distribution; in 2023 CC's deficit has almost no price structure
  for it to move. The give-back is a level nudge, not a newly-created shape defect.
* **A monotone shape emerges in 2024 and grows through 2025** (−44 → +336; −813 → +464 MW): the
  model runs CC too hard in cheap hours and too little in dear hours, increasingly so.
* Hour-of-day, all three years: minimum deficit at **h0**, maximum at **h18–h19**.

## 6. What moved, and what did not

**Nothing was armed, registered, pruned or promoted.** The keeper, its bundle, its sidecars and
its determination are untouched; MISO still carries exactly one registered run (rule 15).

**No cell verdict moves in `docs/codebase-site/data/mechanism-matrix/MISO.js`** — nothing was
tested, so rule 28(b) does not attach in its verdict-moving form. Evidence is appended to five
cells (`miso_south_firm_export_block` G, `miso_south_export_ladder_rt_tail` R,
`internal_congestion_split` G, `vre_reference_rate_curtailment_grossup` K,
`seam_neighbour_hourly_ladder` K), following the miso-206 / neiso-100 / caiso-206 no-solve
precedent.

**Handed forward, NAMED and NOT CHARTERED:**

1. **The PJM seam's 4–9× correlation over-response** (§4) — an open item on a K cell. Its
   admissible form is *not* a re-derive or a damping factor (rule 23, and the handoff's explicit
   freeze). The measured fact a successor would have to start from is that the model's total
   interchange σ is only 65–74 % of measured while its price coupling is 4–9× too strong.
2. **Manitoba's missing price response** (§4) — the measured MHEB seam contributes
   +0.057 / +0.053 / +0.034 to the correlation; the model's firm block contributes zero by
   construction. Sized here, not proposed.
3. **The CC_REGULAR 2024→2025 shape emergence** (§5) — distinct from the 2023 level object and
   growing.
4. **The South seam residual is upstream work**, in the already-open South-gas price-out lane
   (`gas_marginal_commodity_pricing` O / `gas_variable_transport` O, owner-court), not seam work.
5. **C3c** is untouched and stays the designated frontier (2026-07-20).

## 7. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; the one counterfactual computed is
labelled inadmissible in place and proposed as nothing. Rule 12: no LP was solved; nothing ran on
CI. Rule 13 `[R-MEASURED]`: §2's separation injection is named as the outcome pin it would be if
armed, and is not armed. Rule 14 `[R-ACCURATE]`: Part A prefers the measured local price as the
*comparator* and changes no input. Rule 15 `[R-DASHBOARD]`: no run was produced, so nothing is
registered and nothing is pruned; the pruned miso-232 bundle is treated as unrecoverable-by-design
and its numbers are cited from the miso-233 assessment, not re-derived. Rule 19 `[R-ONE-MECH]`: no
mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO
holds no `complete` marker and no out-of-training year was solved, scored or registered. Rule 23
`[R-FROZEN-DERIVE]`: no derive was re-run. Rule 24 `[R-REGISTRY]`: no field created. Rule 25
`[R-ISO-SCOPE]`: MISO's own shard, section and lane only. Rule 27 `[R-PUSH]`: every pushed blob
verified against local. Rule 28(a): the four standing adjudications this touches
(`miso_south_firm_export_block` G, `miso_south_export_ladder_rt_tail` R,
`internal_congestion_split` G, `vre_reference_rate_curtailment_grossup` K) are corroborated, never
re-tested. Rule 28(b): no verdict moves; evidence appended in-session. Rule 29 `[R-SCREEN]`:
clause 0 executed in full — phase 0 first, and it killed the arm before any solve was spent, which
is the outcome the clause exists to produce.
