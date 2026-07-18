# ERCOT Session 2 prompt — offer-curve merit order (CC_REGULAR↔ST_GAS↔CT_PEAKER) + grounded 2023 market-design adder

**Branch off `main`** (PR #726 is merged — the measured RTOLCAP/RTORPA series,
the run143_redo / ordc_pub2 re-baselines, and
`docs/ercot-reserve-supply-scarcity-handoff-2026-06.md` are all on `main`).
**Keeper:** run143 (`results/calibration/ercot_dam_2023as_netload`). **Re-baseline
to compare against:** run143_redo (`results/calibration/run143_redo`, the keeper on
the current local-30 outages). **Read first:**
`docs/ercot-reserve-supply-scarcity-handoff-2026-06.md` (the Task-A/B handoff, the
2023 decomposition, the 2024 CC diagnosis) and
`docs/ercot-run131-lmp-decomposition-2026-06.md`.

ENV: `uv sync --extra dev`; co-opt LP ~3–4 min/yr, run **SEQUENTIALLY** (OOM at 4
cores/16 GB if parallel); 3-yr ~13 min. Push to a fresh branch.

---

## TRACK 1 (primary) — fix the within-gas merit order via offer curves

**The miss (run143_redo, model vs grid-delivered EIA-923−BTM TWh):**

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | 145.4 / 143.7 **(+2.9%)** | 157.8 / 145.4 **(+9.9%)** | 153.3 / 142.1 **(+9.2%)** |
| ST_GAS | 12.3 / 16.7 **(−26%)** | 11.4 / 18.1 **(−37%)** | 10.0 / 14.8 **(−33%)** |
| CT_PEAKER | 4.3 / 7.6 **(−33%)** | 4.2 / 8.2 **(−39%)** | 5.1 / 7.1 **(−28%)** |

The model **over-runs CC_REGULAR and under-runs ST_GAS + CT_PEAKER in all 3
years** (CC fine in 2023, over by ~+10% in 2024/25 as the CC fleet grows / gas
cheapens). The CC over-run ≈ the ST_GAS+CT_PEAKER under-run — a **within-gas
merit-order swap**: combined-cycle clears where ERCOT actually ran steam-gas +
peakers. Worst in the **shoulder** (Apr/May/Oct: CC +19–24pp, ST_GAS/CT −40–67%).
It FAILs C1 fuel-mix (HARD) every year and is **pre-existing** in run143 (not a
reserve-curve artefact — unchanged by the price-only published-ORDC curve).

**The lever — the keeper's `offer_curve_deltas` (measured-DAM-curve multipliers).**
The keeper carries (`meta.json`):
- `CC_REGULAR`: committed −0.05, econ_low −0.24, econ_high −0.20, peak +0.32
- `ST_GAS`: committed 0.0, econ_low −0.13, econ_high −0.35, peak −1.0
- `CT_PEAKER`: committed −0.34, econ_high +0.20

CC_REGULAR's econ bands sit **too low** relative to ST_GAS/CT_PEAKER, so CC clears
first. Re-order the merit stack by **raising CC_REGULAR's econ_low/econ_high**
toward the measured DAM offer and/or **relaxing the ST_GAS/CT_PEAKER cuts** so
they clear ahead of CC in the shoulder.

**Non-negotiable gates (this is where it gets hard — read before tuning):**
1. **No fitting to the volume residual, no markup.** Re-derive the relative offer
   heights from the **measured ERCOT DAM energy offers** — the in-repo
   `_validation-source` offer-curve JSONs / `scripts/data/parse_ercot_dam_offers.py` /
   the `60_DAY_DAM_DISCLOSURE_*EnergyOnlyOffers*` + `*EnergyBidAwards*` parquets
   under `data/raw/ercot/` — **not** by dialing deltas until CC = 145 TWh. The
   delta must trace to a measured offer-height relationship (rule #12).
2. **The run131 honesty gate stands:** pushing CT/ST *below* the measured DAM
   curve to force them on is a markup — barred. If the measured offers say CT/ST
   are genuinely more expensive than CC on energy, then the residual is **not an
   offer-curve miss** but the **energy-only-LP structural limitation** (real
   ST_GAS/CT_PEAKER run for **local-reliability / AS commitment** at part-load,
   which an energy-only dispatch can't see). In that case the honest move is to
   **ledger CT_PEAKER/ST_GAS as an accepted measured-input limitation**
   (`calibration_attestation.json`, per the rubric's documented CT_PEAKER case) —
   *not* to tune it away. Decide which it is **from the measured offers first**,
   before spending an LP solve.
3. **Gate on C1/C2 across all 3 years AND the price.** Re-solve 3-yr; CC_REGULAR
   must come into ±5% without ST_GAS/CT_PEAKER over-correcting, and the LMP /
   duration curve must not regress (the offer change moves dispatch, hence price).
   Don't trade the volume gate for a price regression or vice-versa.

**Suggested first step (cheap, no solve):** dump the measured DAM offer curves for
CC_REGULAR vs ST_GAS vs CT_PEAKER (committed/econ_low/econ_high bands, 2024 gas
$2.19) and check whether the measured stack actually orders ST_GAS/CT_PEAKER below
CC in the shoulder. That single check decides Track-1's whole shape (real
offer-curve fix vs ledgered structural limitation).

---

## TRACK 2 (also requested) — the grounded 2023 reliability-deployment adder

Put the **2023 market-design change into the model**, built so it is
**backcast-able on 2022** (the mechanism must generalize — *do not run the 2022
LP this session*, just keep it able to).

**What it is.** 2023's undershoot is 87% in the 181 h>$200 tail; that tail is
~$85/h of measured **out-of-market reliability-deployment adder** (ECRS launched
2023-06-10; ERCOT's conservative H2-2023 real-time reliability deployments — IMM
~$12B). The ORDC/LOLP co-opt structurally cannot produce it. The measured source
is now in-repo: the **`rtordpa`** column (Real-Time ORDC + Reliability-Deployment
Price Adder) of `data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`.

**Design (grounded, not a fit):**
- Add a regime-gated overlay that **adds the measured `rtordpa` series** to the
  model system price, **gated to the pre-RTC+B regime** (≤ 2025-12-04). Read it
  **per-year from the parquet** (never a 2023 hardcode) — that is exactly what
  makes it backcast-able on any year incl. 2022.
- **Overlay `rtordpa` only, NOT `rtorpa`.** The co-opt already produces an ORDC
  adder (≈ RTORPA); `rtordpa` is the *reliability-deployment* component the model
  has **no** mechanism for, so adding it is additive, not double-counting. Verify
  no double-count against the model's existing co-opt adder before/after.
- It closes only ~$85 of the ~$223/h 2023 tail gap; the other ~$138 is the
  **energy-scarcity base** (the separate reserve-supply lever — re-scope
  `ercot_reserve_eligible` to online RTOLCAP, deferred). State this split; don't
  let the overlay paper over the energy base.

**Backcast-able-on-2022 requirement (do NOT run 2022):**
- Run `python scripts/data/fetch_ercot_ordc_reserves.py --years 2022` so
  `data/raw/ercot/ercot_2022_ordc_reserves_hourly.parquet` exists (archive DocID
  was visible at `reportTypeId=13231`, `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_2022`).
  Validate it (ranges/coverage) **as data only** — proof the lever has a 2022
  input — but **do not add 2022 to the solve set**. The deliverable is that the
  overlay *would* apply to 2022 unchanged, not a 2022 backcast.
- Gate on 2023/2024/2025: the overlay must **lift 2023's tail toward actual**
  (h>$200 toward 181, avg toward 48.4) **without inflating 2024/2025** (their
  measured `rtordpa` is small — demand-wtd ~$0.2/yr — so the regime-gated overlay
  should be near-inert there; confirm it).

---

## Out of scope / parallel (don't conflate)
- The **reserve-supply lever** (online RTOLCAP re-scope) is the *price-shape* track
  (lifts the hollow P90–P99 band in all years + 2023's energy base). Independent
  of Track 1 (volumes) and Track 2 (out-of-market adder). Deferred unless Track 2
  needs it to size the 2023 residual.
- 2024-Jan winter-storm tail and the global storage-AS credit stay as documented
  (un-modelable / rejected).

## Reproduce / score
```bash
# re-baseline keeper on current outages (Track-1 baseline):
python scripts/probes/_keeper_2023as_run.py run143_redo 2025 2023 '{"ST_GAS":{"committed":0.0}}'
python scripts/probes/_ercot_lmp_shape_score.py results/calibration/run143_redo
python scripts/calibration_verdict.py results/calibration/run143_redo   # C1/C2 fuel-mix FAILs
# register every run (PROBE/keeper) per the calibration-report skill (top-15 ERCOT).
```
