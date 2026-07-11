# NYISO 61 — downstate import discipline: measured NYC (Zone J) LCR/TSL import cap — KEEPER

The `2026-07-10-nyiso-60-ldc-transport` keeper recipe VERBATIM with exactly one
change, a **measured-data transmission-limit swap** (rules 12/13/14/17, zero new
free parameters): `nyiso_nyc_lcr_tsl=True`. In the summer-peak design-condition
window (HB14-21, `NYISO_SELFSUPPLY_FLOOR_HOURS`) the **Lower_Hudson→NYC
(Dunwoodie-South)** link's import limit is capped at the **published NYISO
NYC-locality Bulk-Power Transmission Capability import limit — 2,875 MW** every
capability year 2023/24–2025/26 (`data/raw/capacity-deliverability/nyiso/
nyiso.csv`, "NYC" `import_limit`), **replacing the link's 3,900 MW Gold-Book
energy-TTC estimate**. Every other hour keeps the physical rating.

This is the **Zone-J analog of the already-active Zone-K `nyiso_li_lcr_tsl`
cap** (issue #1345), applied identically. **Rule-14 boundary (clean, parallel
to the LI cap):** the 2,875 MW is the AC transmission-security import limit; the
controllable HVDC ties into Zone J (Neptune / HTP / Linden-VFT) are the
**separate** priced import-node link (`IMPORT_NODE_LINKS["NYISO"]`
`("NYC", 1000.0)`) and stay at their physical rating, so the cap limits **only**
the Dunwoodie-South AC link, not total NYC import. It is a transmission limit,
**not a min_gen floor** — it forces no energy (D-2 budget unchanged), so it is
not on the zero-forcing ablation off-list and stays ON in the twin.

## Result (vs the nyiso-60 keeper, v2.4 lw price basis)

A **near-null price effect**: the measured NYC AC-import limit (2,875 MW) vs the
3,900 MW estimate does **not** move the level materially and does **not** close
the deep (>$300) tail.

| metric | keeper nyiso-60 | nyiso-61 | actual |
|---|---|---|---|
| C3a 2023 / 2024 / 2025 | −4.8% / −13.2% / −13.7% | **−3.7% / −12.8% / −13.7%** | ±10% band |
| C3b NRMSE 2023 / 2024 / 2025 | 0.163 / 0.223 / 0.199 | **0.156 / 0.222 / 0.198** | ≤0.20 band |
| C3c >$300 h 2023 / 2024 / 2025 | 23 / 1 / 25 | **28 / 3 / 25** | DA 1 / 0 / 12 (RT 10 / 12 / 42) |
| C5a CO2 2023 / 2024 / 2025 | +3.3 / +2.5 / +8.1% | **+3.3 / +2.5 / +8.1%** (identical) | ±7% / ±10% commercial |

C3a marginally better (or equal) every year; C3b marginally better every year;
C3c 2023 slightly more over-count (23→28 h) on the already-ledgered G-20a
DA-basis artifact; **the 2025 deep tail is UNCHANGED (25 h)**. C1 fuel-mix
**14/14 PASS** all years (free 10/10), C2 PASS, C4 PASS, C7 PASS, **C8 clean
PASS** (ST_GAS grounded-above-budget, D-4 off-window 0.0%) — all **identical to
the keeper**. C5a identical.

**Determination: CALIBRATED-WITH-CAVEATS** (same as the nyiso-60 keeper; the
same 5 ledgered price criteria — C3a 2024/2025, C3b 2024, C3c 2023/2025 — plus
the C5a-2025 commercial-band auto-caveat). **Rule 1: promoted on its measured
structural-faithfulness basis** (a published NYISO transmission-security limit >
a Gold-Book estimate — the exact promotion logic of nyiso-56 measured load
shares, nyiso-59 measured hourly requirements, nyiso-60 measured delivered gas),
**not on residual movement**, and never chased with a tuned adder (rules 11/26).

**FINDING (ledgered):** downstate import discipline is **NOT** the binding lever
for the NYISO deep price tail in these years — applying the measured NYC locality
import limit is a near-null price change and leaves the 2025 deep tail unchanged
(25 h vs 42 h RT). The remaining open levers are the two data-blocked residual
items: **(a) #1344 B1 condition-varying reserve-requirement increments** (formal
NYISO Market Operations request only; the derived series is a documented lower
bound in non-TSA hours), and **(b) the Iroquois Z2 winter hub** (Ask-C,
licensed-data ask). Neither is chased with a tuned proxy.

Zero-forcing ablation twin registered alongside
(`2026-07-11-nyiso-61-downstate-import-ablation`): floors-off prices sit HIGHER —
simple means keeper 29.14 / 32.00 / 54.08 vs twin 32.29 / 35.10 / 60.09
(2023/2024/2025) — the floors force cheap steam-base energy; they do not
manufacture the level or the tail (the tail is the measured requirement's reserve
duals plus the measured daily delivered gas). Identical twin deltas to nyiso-60,
confirming the NYC cap's near-null level effect.

## Reproduce

CI replay of this recipe OOMs GitHub-hosted runners in `regenerate_clean`
(nyiso-59 lineage); solve locally with ≥15 GB + swap:

```
python scripts/regenerate_clean.py
python scripts/replay_keeper.py results/calibration/nyiso60_ldc_transport \
  --set nyiso_nyc_lcr_tsl=true \
  --out-dir results/calibration/nyiso61_downstate_import
# ablation twin:
python scripts/run_calibration_full.py --replay-bundle \
  results/calibration/nyiso61_downstate_import --iso NYISO \
  --zero-forcing-ablation \
  --out-dir results/calibration/nyiso61_downstate_import-ablation
```
