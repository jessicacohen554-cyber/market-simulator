# PRECHECK — caiso-194 (lane 4): `hydro_ror_split` A/B, pre-measurement anchors

**Written and committed BEFORE the curator runs on the full population.** This
artifact discharges GATESPEC-caiso194-hydro-ror-split-2026-08-11 §7 bullet 1 and
the ordering clause inside G-SHARE ("the labeled-subset share is computed and
COMMITTED IN THE PRECHECK **before** the completion rules run on the unlabeled
remainder").

Nothing in this file is a gate band. The GATESPEC's bands are fixed and are not
restated, relaxed, or reinterpreted here — this file only fixes the two
*measured anchors* those bands are evaluated against, so neither can be chosen
after the answer is visible.

## 0. Why this file exists at all (reported contradiction, not resolved here)

The lane-4 handoff states "PRECHECK is already discharged by the GATESPEC (say
so)." The GATESPEC does not support that reading: §7 lists
`PRECHECK-caiso194-hydro-ror-split-<date>.md` as a required artifact "committed
before the curator runs on the full population; carries the G-SHARE
labeled-subset share", and the GATESPEC nowhere contains that share. The share
is a *measurement* that did not exist at authorship.

Resolution taken: honour the GATESPEC, which the handoff itself designates
binding and non-reinterpretable, and write the PRECHECK. This is the
conservative direction — it adds a pre-registration the GATESPEC asked for and
removes no gate. The contradiction is **reported, not silently resolved**, and
is restated in the FINDING's SESSION-REPORT block for the owner.

## 1. G-SHARE anchor — EHA `Mode`-LABELED subset (curator rule 1 ONLY)

Computed by `scripts/probes/_caiso194_precheck_labeled_share.py`, which applies
**only** curator rule 1 (the published EHA `Mode` label) and deliberately does
not classify the Mode-NaN remainder. Grain matches the curator's output (EIA
plant-id, `shapeable` = ANY constituent EHA plant, capacities summed), so the
anchor and the full-population figure it gates are the same statistic.

| quantity | value |
|---|---|
| source | `data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx` |
| CISO conventional-hydro EHA rows (`CH_MW` > 0, `EIA_PtID` present) | 196 |
| — with a `Mode` label (rule 1 applies) | 97 |
| — `Mode` NaN (completion rules 2–5 will govern) | 99 |
| labeled plants at EIA plant-id grain | 97 |
| labeled total `CH_MW` | 2,046.125 MW |
| labeled NON-shapeable `CH_MW` | 500.525 MW |
| **labeled non-shapeable capacity-weighted share** | **24.4621 %** |

`Mode` value counts over the 196 CISO conventional rows: Run-of-river 35,
Peaking 31, Canal/Conduit 29, Intermediate Peaking 2, NaN 99.

**G-SHARE admissible band for the full population** (the GATESPEC's own ±10 pp,
applied to this anchor — band unchanged, only instantiated):
**14.4621 % … 34.4621 %**.

**Materiality note, recorded pre-measurement.** The labeled subset is 2,046 MW
of a ~6.7 GW fleet, so the completion rules govern the clear majority of
capacity. That is precisely the exposure G-SHARE was written to bound, and it
means the gate is load-bearing here rather than decorative. Recording it now so
the observation cannot be read as post-hoc framing of whatever the full
population turns out to be.

## 2. G-COVER denominator — the model's own EIA-860 hydro fleet basis

Taken from the same loader the dispatch path uses,
`market_sim.data.hydro._load_hydro_nameplate("CAISO")` (EIA-860 generator
parquet, prime mover `HY`, BA `CISO`, pumped storage excluded), so coverage is
measured against the fleet the mechanism actually acts on.

| quantity | value |
|---|---|
| CAISO conventional-hydro plants | 192 |
| **nameplate (G-COVER denominator)** | **6,740.300 MW** |
| GATESPEC 90 % bar | 6,066.270 MW |

## 3. What is NOT pre-registered here

* No classification of the 99 Mode-NaN rows has been computed or inspected.
* No solve has been run; no C3a, C3b, or any other scored metric has been read.
* The caiso-141 wall stands: no gate, probe, or diagnostic in this session
  scores hydro or pumped-storage OUTPUT against actuals. The two anchors above
  are a published source attribute and a nameplate census — neither is an
  output series.

## 4. Reproduction

```
PYTHONPATH=.:src uv run python scripts/probes/_caiso194_precheck_labeled_share.py
```

Emits both anchors as JSON plus the instantiated G-SHARE band.
