# NYISO 40 — true-date gas control probe

Control for nyiso-41: the nyiso-39 keeper config re-solved on the corrected
measured gas data only — **no new mechanism**. Isolates the effect of
(1) true-date placement of the Transco Z6 NY daily quotes and (2) the NYISO
monthly hub levels recomputed from the completed daily print series
(Dec-2024 basis +0.16 → +1.00 $/MMBtu; see the nyiso-41 SUMMARY for both).

## Effect vs keeper 39 (data fixes alone)

- C3a mean LMP: −15.6/−19.2/−13.2% → −15.3/−16.3/−13.6% (2024 +2.9pp, all
  from the corrected Dec-2024 hub level).
- C3b shape NRMSE: 0.211/0.304/0.203 → 0.210/0.248/0.215.
- C3c tail: unchanged 0h (no import repricing → no tail channel).
- C5a CO2 2024: −7.2% (band ±7) — the marginal breach appears here too, i.e.
  it comes from the corrected gas data, not from the import mechanism
  (root cause = the ledgered steam under-run; see the attestation).

Attribution: of nyiso-41's C3a-2024 gain (−19.2 → −13.4), ~half is the
measured gas data (this probe) and ~half the measured-neighbor seam pricing.
Registered as a probe; the keeper is nyiso-41.

## Reproduce

The nyiso-39 keeper flags (no new flags) on the branch's corrected data:

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --out-dir results/calibration/nyiso40_truedate
```
