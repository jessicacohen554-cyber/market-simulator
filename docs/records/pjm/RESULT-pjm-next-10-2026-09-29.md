# RESULT — PJM-NEXT-10: COAL_BIT loading and cards 2–3 — no admissible lever found yet, OPEN (zero LP), 2026-09-29

> **RELABELLED 2026-09-29 (owner instruction, same session): OPEN, not a model-class limit.** This session found no admissible lever; it did NOT show the LP is structurally unable to reproduce the loading. The over-run is year-dependent (2023/24 fit) and tracks the coal/gas ratio, which points to a fixable merit-order or offer input. Next test queued for PJM-NEXT-11: PJM's own offered EcoMax for the LONG_RUN segment by year (FINDING §5).

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`). **No LP solved, no shard launched, nothing registered or promoted.**
The parent session PJM-NEXT-9 (`session_01ER7chbHCBdnMTh7v26hrtp`) was archived after confirming `main` carries merge `6c2c132f` (PR #6854).

## Card 1 — COAL_BIT level offset

Detail: `docs/records/pjm/FINDING-pjm-next-10-coal-loading-2026-09-29.md`. Probe `scripts/probes/_pjmnext10_coal_phase0.py` → `results/phase0/pjm/_pjmnext10_coal_phase0.json`.

- **Online hours match CAMPD.** The over-run is **loading within synced capacity**: +10.47 / +7.70 / +10.07 / +1.87 / −0.58 / −2.11 / +11.43 TWh (2019–25). It is flat in time (the same at night and in the day, on weekdays and weekends).
- **It tracks coal's depth in merit.** Delivered coal ÷ gas of 0.55 (2021) gives +17.1 TWh; 1.21–1.38 (2023/24) gives ≈0. 2022 is the coal-supply-constrained exception.
- **Ruled out, measured:**
  - outage windows (cover 90–99 % of dark capacity);
  - Pmax (−5.2 to +5.5 %);
  - AEP–Western congestion (−0.3 to −0.6 $/MWh in 2019–21);
  - PJM's own offers (h9c, wrong sign);
  - incremental-HR econ pricing (wrong sign);
  - min-load committed repricing (wrong year sign).
- **The rule-1 offer-band channel is refused:** no ex-ante value exists that isn't read off this residual.
- **Owner card:** *"Record as limit"*, superseded the same day: **relabelled OPEN**.

## Cards 2–3 — CT_PEAKER 2021, C3a 2020/2022, C3b 2022, net interchange

- **CT_PEAKER 2021 (−9.59):** 6.2 of 8.4 TWh of the bench shortfall falls outside the actual top-10 % price hours. It is the same coal-displaces-gas swap.
- **Balance:** demand matches EIA-930 (2023: 784.8 vs 783.0 TWh). The model exports 10–14 TWh *less* than actual in 2019–24, so correcting exports would add fossil. Interchange is not the cause.
- **C3a 2020 / 2022 and C3b 2022:** price-distribution compression (2020 low-price hours missing; 2022 p99 $105 vs $210), the object pjm-h12 named.
- **Owner card:** *"Record, no successor"*, superseded the same day: **OPEN**, successor PJM-NEXT-11 launched.

## State after this session

- **Training span 2023–25:** NOT-YET on one row, CC_REGULAR 2023 +8.48. It is a recorded model-class limit (`internal_congestion_split` G, PJM-NEXT-9).
- **Run-level 2019–25:** NOT-YET, 14 rows, all out-of-span. They are reported, non-gating (rule 30(c)). The CC_REGULAR rows trace to the recorded east–south limit; the COAL_BIT, CT_PEAKER, C3a and C3b rows are OPEN.
- **Lever queue §5.3:** (1) LONG_RUN offered EcoMax by year; (2) the 2022 coal-supply check; (3) verify C3a/C3b compression. See FINDING §5.
- **Successor PJM-NEXT-11 launched** to fetch the offers corpus and run test (1).

## Retrievability (rule 34(e))

Nothing was solved. The probe and its JSON are on `main` via this lane's PR. The PJM DA binding-constraint corpus and the curated LMPs used here are gitignored; re-fetch with `scripts/data/fetch_pjm_binding_constraints.py --years 2019 … 2025` and `scripts/regenerate_clean.py lmp`.

## Leftover refs for the owner to delete (sessions cannot delete refs, rule 33(f))

`claude/pjm-next-9` is the only one still on the remote. `claude/pjm-next-8` and `claude/pjmnext8-xf-{2019,2022,2023,2024,2025}` are already gone. All are transport only, with nothing to salvage. This lane's own branch `claude/pjm-next-10` is auto-deleted on merge.
