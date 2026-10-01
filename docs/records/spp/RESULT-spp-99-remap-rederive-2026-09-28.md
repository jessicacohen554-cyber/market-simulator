# RESULT — SPP-99: SPP's CEMS-derived inputs under the SPP-98 remap, through miso-280's split-remap companions

**Lane** SPP-99 · control = keeper `2026-09-28-spp-98-cems-remap` (`spp98_remap_span`, rule 29(b) form 4) · PRECOMMIT
`docs/records/spp/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md`, merged at `289d4baf7b0819e7d0b5279cb6ac71930e12ec09`
before any shard launched · owner decision card **"Extend miso-280 (Rec.)"** · registered run
**`2026-09-28-spp-99-remap-rederive`**, bundle `results/calibration/spp99_remap_span` (2019–2025).

## 1. What changed (one field, zero free parameters)

`campd_split_remap_companions = true`: miso-280's mechanism, extended to SPP's plain tranche family (rule 19; no new
field). It selects four `-splitremap-` companions:

- the net-load-masked std outage extract;
- the base outage extract (the tranches' denominator);
- the measured CC heat rates;
- the plain tranches.

Each companion is the incumbent with only the SPP-98 remap plants' lines swapped. The splice control passed on all four.

**What moves in the fleet:**
- **Stall 56565** gets its own measured CT outage windows (availability 0.913 → 0.69–0.83).
- **Arsenal Hill 1416** loses Stall's windows and its 150 %-CF tranche row.
- **Ponca City 7546 CC** gets unit 3's windows and a measured heat rate.

## 2. Legs (rule 36, one per year; the parent solved nothing)

| year | leg SHA (provenance only, rule 33(d)) | shard check | ΔCC_REGULAR TWh | ΔCOAL_PRB | ΔCT_PEAKER | Δprice $/MWh | slack MWh leg / keeper |
|---|---|---|---|---|---|---|---|
| 2019 | `b18f5f79d536c9a24c3674b40a460c5e657796c0` | PASS | −0.553 | +0.266 | +0.166 | +0.078 | 0 / 0 |
| 2020 | `46fd4ee940fc1e60d5ebaec5ff0bf64dbbdb6d27` | PASS | −0.386 | +0.189 | +0.134 | +0.038 | 0 / 0 |
| 2021 | `d5253ce6c0b679882e03a8ed22208cb6ef627fdf` | PASS | −0.249 | +0.048 | +0.195 | +0.247 | 0 / 0 |
| 2022 | `0a0c37667b7e6c06b27c474470fd8bfb0efbd804` | PASS | −0.146 | +0.034 | +0.137 | +0.139 | 0 / 0 |
| 2023 | `e2f131424fda7a2f2b35fd3e594b28bfb482e82e` | PASS | −0.366 | +0.187 | +0.195 | +0.068 | 0 / 0 |
| 2024 | `d006fec4396d30de30e3397ac81c7e8b75691672` | PASS | −0.435 | +0.169 | +0.205 | +0.420 | **862 / 56** |
| 2025 | `23141bf58d7bfa9b8b2752c93792fdd93bf49dee` | PASS | −0.309 | +0.123 | +0.153 | +0.087 | 136 / 77 |

**Parent checks.** Every shard check was re-run in the parent before the shards were archived. The composite carries
the same 9 legitimacy FAIL rows as the keeper; 2022 ST_GAS forced share improves 0.3215 → 0.3072.

**2024 scarcity.** The lost Stall / Ponca City availability tips a few tight hours into scarcity: +806 MWh of unserved
energy, and a max hourly Δprice of $1,955.

## 3. Expectations (PRECOMMIT §6)

| # | result | holds? |
|---|---|---|
| E1 | shard check PASS on all 7 legs (recipe = keeper + exactly the one field; resolved `41ee31e0…` / `92ed67de…`) | yes |
| E2 | \|ΔCC_REGULAR\| ≤ 1.1 TWh (max 0.553); \|ΔST_GAS\| ≤ 0.15 (max 0.068) | yes |
| E3 | \|Δprice\| < $1/MWh (max +0.420) | yes |
| E4 | no C1 / C3a / C3b / C4 status flip in either tier | yes |

**Rule §7 → RECOMMEND PROMOTE.**

## 4. Scored effect at full magnitude (not a criterion, rule 1)

**Train 2023–25: CALIBRATED**, lone ledgered C3c, unchanged. C3c's tail count rises slightly toward actual (hours
above $200):

| year | model (keeper → arm) | actual |
|---|---|---|
| 2023 | 0 → 0 | 42 |
| 2024 | 3 → 7 | 59 |
| 2025 | 1 → 2 | 68 |

**Validation 2019–22: NOT-YET**, the same failing rows, each moving slightly the wrong way:

| row | keeper | arm |
|---|---|---|
| C1 CC_REGULAR 2021 | −9.16 TWh | −9.26 |
| C1 CC_REGULAR 2022 | −10.31 | −10.46 |
| C1 COAL_PRB 2021 | +13.52 | +13.57 |
| C1 COAL_PRB 2022 | +13.49 | +13.53 |
| C3a 2019 | +11.5 % | +11.9 % |
| C3a 2020 | +27.8 % | +28.0 % |
| C3b 2020 | 0.348 | 0.349 |

This is the expected sign: the repair removes available CC energy and coal backfills it. The 9–13.5 TWh CC/coal miss
is not an input-attribution problem, so this lever could not close it. It is correctness at the plant level, not a
residual lever.

## 5. Findings routed (unchanged from the PRECOMMIT §5)

1. `derive_thermal_tranches.py`'s plain path drops every COAL row at HEAD (all ISOs; coal-subclass regression).
2. WFEC 55655 is not a nameplate defect: the fleet holds its 90 MW inside Anadarko 3006. The WFEC and Tinker remap
   rows are misaligned with the fleet, but their solve reach is nil; they are benchmark-domain.
3. Stall's tranche row is derived from CT-only CEMS: min-load 42.7 % against ~55 % true. This is a disclosed limit of
   the tranche deriver, which has no boundary guard.

## 6. Retrievability (rule 34(e)) and year set (rule 35(b))

- **On `main`:** the composite `results/calibration/spp99_remap_span` (committable set), its sidecar and its run payload
  land on `main` with this lane's PR. **Promotion costs zero re-solves.**
- **Not on `main`:** the per-year legs are gitignored in the parent. Their SHAs above are provenance only; they are not
  a recovery route (rule 33(d)).
- **Year set:** SPP's registered years are 2019–2025 on `spp-98` only. `spp-99` covers all seven.
