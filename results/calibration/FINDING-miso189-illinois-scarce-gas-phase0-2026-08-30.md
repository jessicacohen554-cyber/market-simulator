# FINDING miso-189 — the MISO-Illinois $8.22/MMBtu scarce delivered-gas observation, phase-0'd zero-solve: the candidate is REFUTED on its own pre-declared rule, the "artifact" is measured F923 across-plant dispersion the model carries faithfully, and the C3a-2025 lane stands at its adjudicated frontier

**Session miso-189 (2026-08-30).** Charter: the miso-189 handoff — ask A
(zero-solve validation of the miso-188 keeper), ask B (standing owner item 6:
the MISO-Illinois $8.22/MMBtu scarce delivered-gas observation, phase-0
zero-solve, PREREG+solve only if the measured record exceeds the model's
input), ask C (partial-plant mid-window exit charter — owner-grant only, not
granted, not built). Probe: `scripts/probes/_miso189_illinois_gas_phase0.py`;
record: `results/calibration/_miso189_illinois_gas_phase0.json`. **NO LP was
built or solved; the keeper is unchanged: `2026-08-30-miso-188-rvsscope`.**

## 1. Ask A — zero-solve validation

`calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope` reproduces the
registered determination exactly from committed artifacts: **NOT-YET on
{C3a-2025 −12.3%} ALONE**; C1 16/16 all classes / 12/12 free; C3a-2023 −0.7%
RT-diagnostic +3.50% scored / C3a-2024 −4.30% in-band; C3c the single
ledgered caveat; C6 attested; C8 PASS all years (2025 ST_GAS
grounded-above-budget note carried, 34.2% forced, all mechanisms clear D-4).

## 2. The object and the pre-declared rule

FINDING-miso186 §1 Leg R/S recorded, for the 2025 scarce set (the 47 Jun–Sep
hours with measured Indiana-Hub RT > $200): the model's availcap-weighted
delivered-gas input for the MISO-Illinois gas fleet reads **$8.22/MMBtu**
against $2.7–3.8 in every other zone, flagged as "an F923 plant-level
delivered-price artifact worth a look in the Midwest lane" — standing owner
item (6) ever since. The miso-189 charter phase-0s it: **if the MEASURED
scarce-set delivered price exceeds the model's input materially, that is a
rule-13/14 measured-input candidate with the right sign for the C3a-2025
under-priced tail** (PREREG + solve next); otherwise refute and stamp.

The probe docstring froze the rule BEFORE any adjudicating quantity was
computed: CANDIDATE iff measured − model ≥ +$0.50/MMBtu on the 2025 scarce
set, on either the zone-book grain (best measured comparator vs the
capacity-weighted book) or the matched-plant grain (reporting plants' own
F923 prints vs the model restricted to the same units, availcap-weighted);
REFUTED otherwise.

## 3. Footing (all gates PASS)

Machinery: `_miso134.build_year` repointed to `miso188_rvs_B` (the
_miso156/_miso186 pattern) with the `weather_year=year` pin (the miso-188
§6.4 instrument lesson); scarce clock = `_miso183.hour_sets` verbatim.

* **F-1 PASS** — scarce-set sizes reproduce the committed 11/14/47 exactly.
* **F-2 PASS** — the rebuilt 2025 Illinois book reads **8.218** vs the
  committed miso-186 value 8.2179 (tolerance ±0.40 for the miso-186→188
  fleet delta; the reproduction is exact to 4 significant figures — the
  retiree-scope drops touched no Illinois gas availcap in the scarce set).
* 2023/2024 books also reproduce the committed miso-186 rows to 3 decimals
  (9.290/5.655 Illinois; every other zone likewise).

## 4. The measurement (2025 scarce set, adjudicating)

**Model Illinois book: $8.218/MMBtu** (availcap-weighted, 47 scarce hours).
Every measured comparator, weighted by scarce-hour counts over Jun–Sep:

| comparator | $/MMBtu |
|---|---|
| C-A F923 IL-state delivered, burn-weighted | 4.050 |
| C-B F923 Illinois-ZONE plants (the model's own members), burn-weighted | 3.955 |
| C-C Henry Hub month + MISO ISO-month basis (the miso-156 PRIMARY) | 3.423 |
| C-D Henry Hub month + Illinois zone annual basis (`miso_zonal_gas_hub.csv`) | 3.071 |
| C-E Chicago Citygate daily, the exact scarce days | 2.861 |
| C-F EIA IL citygate monthly (N3050IL3, /1.037) | 3.419 |

* **Zone-book grain: gap = best measured − model = 4.050 − 8.218 =
  −4.17 $/MMBtu.** The model input sits $4.2 ABOVE the highest measured
  comparator.
* **Matched-plant grain: model 10.931 vs measured own-prints 10.599, gap
  −0.33** — the model reproduces the reporting plants' own F923 monthly
  prints; the residual −0.33 is the mean-preserving Henry-Hub daily-shape
  factor evaluated on the specific scarce days, not a level wedge.

**VERDICT (the frozen rule): REFUTED.** No grain fires; both gaps are
negative. There is no under-priced scarce gas input to raise.

## 5. What the $8.22 actually is (the provenance decomposition)

The Illinois scarce-hour gas book splits 57.9% own-F923-print capacity
(capw fp $10.93) / 42.1% class-aware nearby-fallback capacity (capw fp
$4.59) / 0% trajectory-default. The high side is **the plants' own measured
prints**, led by (2025 scarce months, F923 rows):

| plant | class | scarce availcap | own F923 print | monthly burn |
|---|---|---|---|---|
| 913 Venice | CT_PEAKER | 339 MW | $11.2–12.4 | 20–25k MMBtu |
| 55496 Goose Creek | CT_PEAKER | 267 MW | $13.9–15.4 | 6–7k MMBtu |
| 55417 Raccoon Creek | CT_PEAKER | 179 MW | $20.5–22.7 | 2.3–2.8k MMBtu |
| 55204 Kinmundy | CT_PEAKER | 133 MW | $5.3–5.9 | 6–7k MMBtu |
| 55334 Holland Energy | CC_REGULAR | 77 MW avail | $2.8–3.1 | up to 1.85M MMBtu |
| 976 Marion | CT_PEAKER | 59 MW | $2.9–3.1 | 67–354k MMBtu |

The capacity-weighted vs burn-weighted contrast is the whole story: the
zone's scarce-hour gas **capacity** is dominated by rarely-run CTs whose
delivered $/MMBtu genuinely prints high (fixed LDC/transport/minimum-take
charges amortized over tiny monthly takes), while the zone's gas **burn**
concentrates at the cheap CCs (~$3.0). The same structure holds in 2023
(Raccoon Creek printed $45.28; book $9.29) and 2024 ($16.62; book $5.65).
It is measured across-plant dispersion, faithfully carried per plant — NOT a
wiring artifact, NOT a fallback-pool inflation (the fallback side of the
book is the CHEAP side, $4.59).

## 6. Reconciliation with the standing miso-156 adjudication (explicit, per charter)

`gas_hub_basis_overlay` MISO `R` (miso-156, FINDING-miso156 §7.1) rests on
two grounds: (1) at the ANNUAL grain the model's capacity-weighted delivered
gas is ABOVE both measured comparators in all three years, so the D2
fuel-cost channel (−6.156 $/MWh of the 2025 C3a gap) runs BACKWARDS —
correcting fuel toward measured makes C3a WORSE; (2) rule 14 — the per-plant
F923 measurement is faithful (across-plant dispersion 5.321→3.593→3.413 vs
source 5.657→3.748→3.679) and an ISO-flat hub series would trade a faithful
measurement for a flat one. This phase-0 is the SCARCE-SET-scoped version of
the same comparison, and it **corroborates both grounds rather than
producing the new evidence that could re-open the cell**: (1) scarce-set
model gas is above every measured comparator by $4.2 — the fuel channel
points the same (backwards) way in the scarce set as at the annual grain;
(2) the matched-plant gap of −0.33 measures the per-plant fidelity directly
at the scarce grain. The `R` stands, now with scarce-set corroboration; the
DO-NOT-REDO discipline gains a second citation, not an exception.

## 7. Reported against interest

1. **The 2023/2024 matched-plant gaps are positive** (+0.271 / +0.046
   $/MMBtu, measured above model) — the candidate's direction, but both
   below the +0.50 materiality line, in in-band years, and both are the
   daily-shape factor evaluated on few scarce days (11/14 hours), not a
   level wedge. Reported at full magnitude; they do not fire the rule.
2. **The 2025 F923 vintage is preliminary** (8 IL reporting gas plants; the
   C1-2025 skip is the same currency issue). Missing reporters would bias
   the burn-weighted comparators C-A/C-B UPWARD if the absentees are cheap
   high-burn CCs (the likelier case) — i.e. the true measured level is, if
   anything, LOWER, which strengthens the refutation. Not assumed either
   way; disclosed.
3. **A real methodological question is exposed, with ADVERSE sign, and left
   in owner court:** the F923 delivered $/MMBtu of a near-idle CT amortizes
   fixed charges over tiny takes, so it overstates the *marginal commodity
   cost* of an incremental scarce-hour MMBtu (Chicago spot + variable
   transport ≈ $3–4). Pricing IL peakers at marginal commodity cost instead
   of average delivered cost would CUT their offers by up to ~$150/MWh-scale
   at Raccoon Creek's heat rate and LOWER scarce prices — the wrong
   direction for C3a-2025, squarely inside miso-156's "fuel channel runs
   backwards" finding, and a cross-ISO methodology change (every ISO prices
   F923 average delivered cost) needing its own charter. NOT repaired here;
   NOT a lane lever.
4. **No dashboard registration is owed**: no solve was run (rule 15 binds
   runs; the miso-156 no-solve precedent). The committed record is the probe
   + JSON + this finding + the matrix stamp.

## 8. The lane state after this session (the escalation)

The queue after miso-188 carried **no named, un-adjudicated mechanism** for
C3a-2025; item (6) was the single named never-adjudicated candidate touching
2025 scarce price formation, and this phase-0 adjudicates it REFUTED at the
measurement stage. The lane is therefore at its **adjudicated frontier on
C3a-2025 (−12.30%)**: the direction object (N→S 7/47, +0.385 GW vs measured
32/47 S→N / −2.441 GW out) remains the ~3.3 GW mc-idled/flat-stack
MODEL-CLASS residual (offer family EXHAUSTED, miso-179 `R` / miso-180 `I`;
ORDC family `G` by owner ruling, miso-163), folding into the standing **D-4
posture question with the ~1.3 GW scarce-export concession — the ruling is
the owner's**. Standing OWNER items after this session: (1) the C8
provenance-materiality floor; (2) committed-vs-regenerated diagnostics
exposure; (3) `RHO_CLIP` cross-ISO band; (4) **D-4 posture — the C3a-2025
direction object** (unchanged, now the lane's ONLY open road); (5) ~~the
MISO-Illinois $8.22 observation~~ **CLOSED by this phase-0** (refuted as a
lane lever; the marginal-vs-average delivered-cost question of §7.3 is its
residue, adverse-signed, owner-court); (6) the partial-plant mid-window exit
charter (FINDING-miso188 §6.6 — named, sized, NOT granted, NOT built).

## 9. Governance

Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only; MISO holds neither marker; the
spend freeze untouched; no new data fetch (every comparator series was
in-repo). Rules 1/13/14: the candidate was tested against the measured
record and refuted on a pre-declared rule — no input was changed, no
parameter fitted, nothing tuned to a residual. Rule 19: the gas LEVEL
remains owned by the F923/EIA-923 series alone, unchanged. Rule 28(a): the
lever came from the standing owner-item queue (item 6, the one named
un-adjudicated candidate); 28(b): the evidence is stamped in §5.4 and the
MISO shard (`gas_hub_basis_overlay` ev gains the scarce-set corroboration;
verdict untouched); no new ScenarioConfig field was minted (28(c) n/a).
Rule 25: only MISO's shard/docs touched. Rule 27: exact on-disk bytes;
every pushed blob ≥300 lines verified. No `.github/workflows` change. THE
OWNER MERGES; no PR opened.

## 10. Reproduction

```
cd <repo root>
python3 scripts/calibration_verdict.py --run-id 2026-08-30-miso-188-rvsscope
python3 scripts/probes/_miso189_illinois_gas_phase0.py
```

Reads the committed `miso188_rvs_B` bundle (run_config + hourly sidecars),
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`,
`data/raw/gas-prices/{henry_hub_monthly,miso_citygate_daily,eia_citygate_IL_MI_monthly_2023-2025}.csv`,
`data/raw/gas_basis_by_iso_month.csv`, `data/raw/miso_zonal_gas_hub.csv`.
