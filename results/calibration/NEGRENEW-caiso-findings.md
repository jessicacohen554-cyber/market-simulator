# CAISO Session B — negative curtailable-renewable offers (findings)

Branch: `claude/caiso-negative-renewable-offers`. Implements the "negative tail"
workstream from `NEXT-caiso-floor-prompts.md` (Session B). Read that and
`AUDIT-caiso-structural.md` (items 2/3/6) first.

## What was built

A default-off `negative_renewable_offers` flag (ScenarioConfig; CLI
`--negative-renewable-offers` on `run_calibration_full.py` and
`run_calibration.py`). When on, the curtailable wind/solar dispatch offer is
**floored at the negative keep-running value** `-renewable_keep_running_value`
(`policy/eac.apply_negative_renewable_offer_floor`, applied in `run_calibration`
right after the EAC/PTC adders). The floor is the *more-negative* of the
existing offer and the keep-running value, so:

- **solar** (dispatch offer `$0` — it earns the ITC, not the PTC) is carried to
  `-$20`, and
- **wind** (already `-PTC ≈ -$26`) is left untouched — no double-count.

`renewable_keep_running_value` defaults to **$20/MWh**, one defensible constant
(no per-hour shape) in the middle of the cited range: CA RPS Bucket-1 (PCC1) REC
prices have historically cleared ~$10–25/MWh and the federal §45 wind PTC is
~$28/MWh (2024). A renewable on a PPA/REC pays up to this to avoid curtailment,
so it bids `-keep_running_value`; in oversupply the marginal — curtailed —
renewable then sets a sub-$0 LMP.

`build_cost_vector`'s overgeneration-dump cost already auto-scales above the
most-negative renewable offer, so the LP **curtails** the surplus (no credit
paid on undelivered energy) rather than generating-and-dumping it — the price
goes negative via forgone REC value, not a paid dump. No new LP rows.

Byte-identical when off (verified: real 2024 run below).

## Mechanism / dependency

The negative offer only bites when the model is **LONG** (surplus that must be
curtailed). Per the audit, the CAISO backcast is a **net importer in ~100% of
hours** and never goes long midday — so its marginal is always a ≥$28
import/gas, and the existing `$0` export/curtailment sink floors any surplus at
`$0`. Negative prices therefore require Session A (the RA must-offer commitment
floor) to make the model long. Developed and proven independently here; full
3-yr payoff needs Session A merged.

## Results

### Real 2024 run — before/after (load-weighted system price, vs actual `da_pct`)

| metric | BEFORE (base) | AFTER (flag) | ACTUAL (da) |
|---|---|---|---|
| mean | 57.43 | 57.43 | — |
| p5   | 38.82 | 38.82 | -10.24 |
| p1   | 36.00 | 36.00 | -24.49 |
| min  | 28.00 | 28.00 | -40.65 |
| neg-hrs | 0 | 0 | — |

**Byte-identical** — the model is never long, so the offer is never marginal
(exactly the documented dependency). Pairing with `--interchange-shaping` does
NOT help: the model stays a net importer (-18 TWh, -2.1 GW avg; midday swing
1809 MW vs actual 4596 MW) and the price *rises* (avg $64.65) as capped imports
are replaced by gas — shaping alone never induces midday longness (audit item 3).

### Forced-long full-fleet probe — the proof

Real CAISO 2024 fleet/renewables, demand scaled ×0.30 so domestic must-take
(solar+nuclear+hydro+geo) exceeds load AND the 6.5 GW `$0` export sink, forcing
solar curtailment (a stand-in for Session A's RA floor; throwaway probe):

| | system min | system neg-hrs | SP15 min | SP15 neg-hrs |
|---|---|---|---|---|
| flag OFF | **0.00** | 0 | -0.00 | 0 |
| flag ON  | **-20.00** | 388 | -20.00 | 388 |

Flag-off floors at `$0` (the export sink); flag-on pushes **below** it to
exactly `-$20` (= the keep-running value) once the sink saturates and curtailed
solar is marginal — reproducing CAISO's negative midday prices. Unit tests
(`tests/test_negative_renewable_offers.py`) prove the same in a minimal harness,
including the layering below the `$0` export sink (price = `$0` while the sink
has headroom, `-$20` once it saturates).

## To realize the full 3-yr payoff

Merge Session A (RA must-offer commitment floor) so the model is long midday,
then re-run with both flags:

```
python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 \
  --commitment --priced-interchange --interchange-shaping \
  --negative-renewable-offers --out-dir results/calibration/caiso_negrenew_3yr
```

Expect spring-midday p5/min to move from `$28`/`$36` toward actual
(`p5 -$10`, `min -$41`), with negative-price hours appearing in the solar
glut. Keep gas scored vs **EIA-923** (not EIA-930) per the audit caveat.
