# FINDING miso-184 — the DA-vs-RT ladder question ADJUDICATED: **V-DEFECT-COUPLING — the derivation's scarce-tail failure is REAL and ESTABLISHED (it reproduces 7% of its own target flow in the 2025 scarce set), but the defect is NOT the price basis: every admissible zero-parameter rebasis LOWERS every export band and the charter's named RT-hub candidate carries exactly 0.000 GW.** No basis swap is licensed; NO ARM, NO RE-DERIVE, NO LP

**Session miso-184 (2026-08-24).** Executes
`PREREG-miso184-south-export-ladder-tail-2026-08-24.md` (committed and pushed
at `06bd675` **BEFORE any adjudicating quantity was computed**; the frozen
instrument at `1cc85a4` before it ran). The owner engagement of miso-183 §8
item (5) is recorded in the PREREG preamble — the rule-23 adjudication was
owner-chartered, with a conditional repair + A/B license. **The frozen verdict
mapping REFUSES the license: no `ScenarioConfig` field created, nothing armed,
the ladder NOT re-derived, no LP spent, no run registered** (rule 15 not
engaged). Keeper `2026-08-22-miso-177-rho-measured` (`miso177_rho_B`)
UNCHANGED; determination unchanged: **NOT-YET on C3a-2025 alone**, C3c the
single ledgered caveat. **Matrix cell minted: `miso_south_export_ladder_rt_tail`
= `R` in MISO's shard** (a mechanism-in-kind WAS tested here — at its own
identification, per the PREREG's §0 declaration — unlike miso-182/183's
no-cell sessions), with its new mechanism row added per rule 26.

Instrument: `scripts/probes/_miso184_ladder_tail_methodology.py` →
`results/calibration/_miso184_ladder_tail_methodology.json`. No new data
intaken; every input was already in-repo.

## 0. The verdict

**V-DEFECT-COUPLING, by the pre-registered mapping** (PREREG §4): the Leg A
defect line fires decisively AND no Leg C candidate clears the repair line.

1. **The defect is established on the derivation's own construction** (not the
   residual). The registered 2025 South export ladder, driven by the measured
   DA it was derived against (the derive script's own offline-P9 convention),
   produces a scarce-set mean export of **+0.096 GW against a measured +1.368
   GW** — 7.0 %, GAP **+1.272 GW** (the defect line needed 0.5). The same
   construction reproduces the **annual** flow nearly perfectly (+1.081 sim vs
   +1.031 GW measured; P9 volume −8.88 vs −9.03 TWh) — the failure is purely
   the tail the model is scored on. 2023 concurs (GAP +0.765 GW, 23.8 %
   reproduced); 2024 (reported-only year) concurs (+0.674 GW, 21.8 %).
2. **The defect is NOT the DA basis.** The charter's suspected repair —
   re-derive the export tail on RT quantiles — was tested as-armable along
   with both South-zone bases, under the frozen Q-Q machinery. **All three
   candidates LOWER every export band in every year** (2025 top band: RT-hub
   $47.08, South-DA $42.08, South-RT $37.23, vs the registered DA $53.00),
   because at the measured export-depth durations (d₁ = 0.79–0.90) every
   admissible price distribution's quantile sits BELOW the hub DA's. The
   RT-hub candidate carries **0.000 GW** of scarce-tail export in all three
   years — an anti-repair, strictly worse than the ladder it would replace —
   and the best candidate (South-zone DA) carries 0.152 GW = 11 % of the
   measured tail against the 50 % repair line. The no-wash clamp never fired;
   nothing was even close.
3. **The mechanism, measured:** the South seam's export is
   **price-INELASTIC** — Spearman rank correlation of flow vs every basis is
   |r| ≤ 0.19 (hub DA +0.07/+0.06/−0.08 by year; hub RT +0.06/+0.02/−0.13;
   South-zone DA +0.19/+0.18/+0.00; South-zone RT +0.18/+0.12/−0.04), and the
   derive's own P9 hourly correlation was already ~0 (+0.02/+0.04/−0.12) —
   the Q-Q ladder matches durations, never coincidence. And in 2025 the
   export **DEEPENS under scarcity at every band**: conditional depth c_k >
   unconditional d_k for all 8 bands (c₁ 0.851 > d₁ 0.793; at mid-ladder
   roughly double — c₄ 0.511 vs d₄ 0.368, c₈ 0.106 vs d₈ 0.045). A monotone
   willingness-to-pay sink curve driven by ANY single price series cannot
   represent an export that persists — deepens — at the top of every price
   distribution. The PREREG §1 representability frame, declared before
   measurement, is confirmed arithmetically: to follow the scarce set
   (ranks ≳ 0.995 of every basis) a Q-Q band needs measured duration
   d_k ≳ 0.995; the deepest measured d₁ is 0.90.

**Consequence: the rule-23 gate holds.** The DA-quantile ladder stands — not
because it is right in the tail (it demonstrably is not) but because it is
the *most tail-permissive admissible member of its own mechanism class*, and
every reachable "repair" inside the license (same machinery, corrected basis,
zero new parameters) moves the ladder away from the tail. The repair the tail
actually needs is a **different mechanism class**, named in §5 and handed to
the owner, not built.

## 1. Footing (hard gates; one instrument artifact disclosed)

* Scarce sets reproduce **11/14/47** exactly (F-1).
* The frozen machinery re-derives the registered
  `MISO_SEAM_LADDER_BY_YEAR` to the cent on **189 of 192** band values, 2025
  exact on all 32; three bands deviate by **exactly one cent** (2023
  PJM/import b5 $27.87 vs $27.86; 2023 South/export b4 $27.70 vs $27.69;
  2024 South/export b5 $23.76 vs $23.77) — `np.quantile` float jitter at the
  cents-rounding boundary vs the hand-rounded registration. Within the
  PREREG's strict "> $0.01 → STOP" line; Legs A/C score the REGISTERED
  (armed) values throughout, so nothing downstream moves.
* **Disclosed instrument correction:** the probe's first run STOPped on these
  cent flips because the code compared rounded floats with a bare `>`
  (0.01000…1 > 0.01). The comparison was made faithful to the declared line
  (epsilon on the float compare, commit `c584d08`) and the probe re-run;
  every other number is identical between the two runs. This is an
  implementation-fidelity fix, not a threshold move, and is reported as such.
* P9 unconditional context (the construction's design guarantee, all years):
  South volume within 1.7 % of measured, duration RMSE 129–155 MW.

## 2. Leg A — the tail reproduction failure (GW, scarce-set means, export-positive)

| year | measured E | ladder sim X_DA | GAP | X/E | annual E / X (context) |
|---|---:|---:|---:|---:|---|
| 2023 | +1.004 | +0.239 | **+0.765** | 23.8 % | +1.071 / +1.098 |
| 2024 (rep-only) | +0.861 | +0.188 | **+0.674** | 21.8 % | +1.350 / +1.366 |
| **2025** | **+1.368** | **+0.096** | **+1.272** | **7.0 %** | +1.031 / +1.081 |

Defect line (2025): GAP ≥ 0.5 GW ✓ and X_DA ≤ 0.5 × E ✓ — **ESTABLISHED**.
Row coverage 8,760/8,760 (zero rows dropped for `rt`), scarce coverage
11/14/47 of 11/14/47.

## 3. Leg C — the candidates, as-armable (2025; full tuples in the JSON)

| candidate | top band σ₁ (reg. DA: $53.00) | X_B scarce | X/E | repair ≥ 50 %? | non-inversion 2023? |
|---|---:|---:|---:|---|---|
| B1 RT hub (the charter's) | $47.08 | **0.000** | 0 % | NO | NO (0.000 < 0.139) |
| B2 South-zone DA | $42.08 | 0.152 | 11.1 % | NO | yes |
| B3 South-zone RT | $37.23 | 0.032 | 2.3 % | NO | NO |

No clamp fired in any candidate-year (all σ far below the no-wash limits
$50.98/$57.85/$68.45). B1 and B3 additionally fail 2023 non-inversion — they
would REDUCE tail export relative to the ladder they replace, in the LP too:
every band's sink is strictly lower, so at any internal price the armed
export set is a subset of the control's. Annual durations are preserved by
construction under every candidate (quantile matching; X_B annual ≈ 1.08–1.37
GW ≈ measured) — which is exactly the trap: **a rebasis moves WHICH hours the
ladder shuts off in, and every admissible basis puts the shut-off in the
scarce set**, because the scarce set sits in the top ranks of every basis
(hub by construction; the South-zone series empirically — the real South's
own hubs were elevated in the hub-scarce hours too, which is why B2/B3 carry
almost nothing).

## 4. The import side, reported not built (the same defect mirrored)

The registered DA **import** ladder, driven by DA over the 2025 scarce set,
simulates **+0.957 GW of import** — so the seam pair's net offline clearing
is **+0.862 GW INTO MISO against a measured −1.368 GW OUT: a ~2.2 GW total
tail miss on the derivation's own diagnostic**. Driven by RT (what an
internal price tracking actual scarcity would do), the import side reaches
+2.202 GW — the offline mirror of the keeper's known +2.1 GW tail
over-import (miso-178 §"tail generation guard"). The import side's scarce
behaviour is therefore the SAME duration-coupling defect, mirrored, and is
NAMED here for the record — not built, not gated, and not reachable by this
session's export-bands-only license.

## 5. What the object now is (handed to the owner, not built)

The C3a-2025 South residual's export-price half now has a complete
adjudication chain: the ladder's tail failure is real (§2), and **no
zero-parameter rebasis inside the ladder's own mechanism class can repair
it** (§3). What the measured record shows the tail needs is a
**scarcity-coincident, price-inelastic export** — the South's surplus moving
out (S→N at the RDT limit + the TVA leg) regardless of price. Every road
from here leads OUTSIDE this session's license:

* **The firm/scheduled-block form** is exactly
  `miso_south_firm_export_block` — already `G` (miso-182), re-openable ONLY
  on the §6b data (an EQR firm-sale series clearing the crosswalk +
  rule-13 forward-regenerability + cost, or a published by-counterparty
  contract-path series). This finding strengthens the case for that data
  hunt but does not change the refusal's grounds.
* **The upstream internal-direction object** (the too-cheap Midwest stack
  manufacturing southward pressure, miso-178 §2 / miso-183 §5) — a repair
  there would raise the Midwest-South spread the RIGHT way; the standing
  falsifiable prediction (it must flip the scarce-hour RDT direction toward
  the measured S→N-binding record, 32/47) is unchanged, and this session's
  S-2/S-3 gate constructions (PREREG §6) are ready-made for whichever
  session next arms a candidate there.
* **A non-monotone / state-conditioned coupling** (an export that clears on
  the SOUTH's own surplus state rather than a price threshold) would be a
  NEW mechanism-in-kind with its own driver identification — an owner
  charter, not a derive fix.
* Failing all three, the residual remains an honest model-class limitation
  of the seam representation, priced at ~1.3 GW of scarce-set export
  (≈ the GAP), sitting inside the C3a-2025 miss.

## 6. Reported against interest

* **The A/B never ran**, so the charter's structural predictions (N→S binding
  count falling from 9/47; outflow toward −2.441 GW) were NOT measured on an
  LP. The refusal rests on the offline construction — which is the
  derivation's OWN identification test, failed by 89–100 %. For B1/B3 the LP
  direction is additionally bounded without solving (every sink strictly
  lower ⇒ export weaker at any internal price); for B2 an LP arm remains
  conceivable but would arm an 11 %-of-object level tweak — the "level adder
  wearing a repair's name" the charter kills by name.
* **The orientation line fires only in 2025**: in 2023/2024 c₁ < d₁ (0.818
  vs 0.858; 0.857 vs 0.903) — the scarce-set DEEPENING is a 2025 signature;
  in the small 2023/24 scarce sets the export thins slightly instead. The
  defect line does not depend on the orientation line (Leg A fires in all
  three years); reported as found.
* **A composite basis (e.g. max(DA, RT)) was not in the candidate set.** By
  the frame's arithmetic its quantile at d₁ ≈ 0.79 sits only marginally
  above the hub DA's (the RT-only exceedance is ~1 % of hours) — nowhere
  near the ≥ $200 the tail needs — but it was excluded by declaration, not
  measurement, and is reported as such.
* **B2's 2025 row set is 8,759** (one South-zone hour missing); scarce
  coverage still 47/47. The three one-cent F-2 flips and the probe's
  float-compare fix are §1's disclosure.
* The measured South-zone actuals here are the C3a benchmark's own hub set
  (ARKANSAS/LOUISIANA/MS/TEXAS mean). That the real South's own price was
  mostly ABOVE ~$42 in the hub-scarce hours (implied by X_B2 = 0.152)
  bounds how much price separation the real S→N binding produced — the
  South was cheaper than the Midwest in those hours (miso-178: actual South
  = the cheapest zone), but not cheap in absolute terms. Any future
  South-price-conditioned mechanism must respect that.
* The pool-basis object size (+1.19 GW) stays retired (miso-183); this
  session's E_meas quantities are SEAM-pool measures used to score the
  derivation against its own target series — they are not re-quoted as the
  object's size, which remains the basis-free ≥ 0.93 GW.

## 7. Governance

Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only; MISO holds neither marker
(fail-closed); the spend freeze untouched; no re-key owed. Rule 23
`[R-FROZEN-DERIVE]`: **the ladder is NOT re-derived** — the frozen mapping
refused the license; the three one-cent registration flips are disclosed,
not "fixed" (the registered values remain the armed truth). Rule 15: not
engaged (no solve). Rule 26(b): the `miso_south_export_ladder_rt_tail` row +
MISO cell `R` + §5.4 queue stamp + calibration-log entry, all in-session.
Rule 27 `[R-PUSH]`: exact on-disk bytes; every pushed blob ≥ 300 lines
verified. No new `.github/workflows`. **DO-NOT-REDO honoured throughout**
(the PREREG §7 list; nothing re-opened, the miso-183 basis adjudication not
re-litigated, `ba_code="SOCO"` untouched as a forecast-lane item). Owner
decision points, restated not decided: (1) the D-4 determination posture —
the ladder-tail queue head is now ADJUDICATED, so the C3a-2025 South
residual's remaining roads are §5's (new data per miso-182 §6b / the
Midwest-stack object / a new-mechanism charter / the model-class
concession); (2) the C8 provenance-materiality floor, committed-diagnostics
exposure, and `RHO_CLIP` items carried unchanged from miso-183 §8.

## 8. Reproduction

```
cd <repo root>
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,pyyaml \
  --python 3.12 python scripts/probes/_miso184_ladder_tail_methodology.py
```

Reads `data/raw/eia-930-interchange/MISO interchange hourly.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`,
`data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet` (via the
derive's `load_joined`), and imports the frozen machinery from
`scripts/data/derive_miso_seam_ladders.py` byte-for-byte. Record:
`_miso184_ladder_tail_methodology.json`. PREREG: `06bd675`; instrument:
`1cc85a4`; execution + fidelity fix: `c584d08`.
