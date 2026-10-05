# RESULT — closeout-MISO-w3f: steam-host CHP commitment (`chp_startup_covered`) on the w3e arm, with (B) and without (A) the w3c holdout

**Headline: arm B fails one record on the reconciled basis** (#7210 head). It clears every desk bar fixed ex ante:
- **C1:** 1 failing record, ST_GAS 2019 −9.63 (bar ≤ 4; w3e arm 5, seam control 8, keeper 10).
- **C3a 2020:** +9.5 % (bar ≤ +10.5 %).
- **C8:** PASS.
- **D-4:** no CHP row.
- **Kill:** clear under reading (i).

Two qualifications go with the headline:
- **The pass depends on the bench.** On the original bench basis, B fails five records: CC_CHP 2019/20/23/24 over-deliver against the default-share bench. B is coupled to #7210 and owner decision #20.
- **The kill wording was ambiguous.** It was clarified mid-run, before any arm-B gated score was known. Both readings are shown below. Under the literal reading (ii) it fires on six CHP rows; every one is lower than in the control.

Status: structure vs gates, not a slot request. This lane does not promote.

```
LANE      : closeout-MISO-w3f (desk GO on arms A+B, 2026-10-05)
PRECOMMIT : PRECOMMIT-closeout-miso-w3f-chp-commitment-2026-10-05.md (+ Addendum: desk bars, + Addendum 2: kill reading (i)); pushed before any solve
PIN       : 3d095d07b2de6b8a07ce34960c52bd71510b2d10 (code drift vs the w3e pin: benchmark_semantics.py only, bench-side)
CONTROL   : the w3e arm 2026-10-05-closeout-miso-w3e-arm (claude/closeout-miso-w3e-probe), reconciled basis
ARM A     : control + chp_startup_covered=true
ARM B     : control + chp_startup_covered=true + mustrun_chp_btm_holdout=true
BUNDLES   : results/calibration/closeout_miso_w3f_{a,b}_span (7 legs each, composed with diagnostics, all shared-input refs rebuilt)
```

## Legs

There were 14 shards, one year each, all solved at 3d095d07. Each `run_config.json` was read after fetch:
- every A leg shows `chp_startup_covered=true` and `mustrun_chp_btm_holdout=false`;
- every B leg shows all four flags true.

Every shard was fetched, verified (17 files in `ls-tree`) and archived.

| year | A commit | A dispatch | B commit | B dispatch |
|---|---|---:|---|---:|
| 2019 | 5b8f0953 | 68 MB | d49d1123 | 76 MB |
| 2020 | 8681d0ff | 72 MB | 80f0c621 | 71 MB |
| 2021 | d4fa67be | 65 MB | d26ce18f | 66 MB |
| 2022 | 4ab92038 | 65 MB | 82f0e33c | 66 MB (zstd-9) |
| 2023 | 175e0bba | 99 MB | 16253b3c | 64 MB |
| 2024 | 2f4cd4be | 93 MB | 920d3e08 | 99 MB |
| 2025 | 4cb937b8 | 97 MB | ed830bc9 | 96 MB |

- **Unserved energy:** zero in every year except 2024: A 4.09 GWh, B 8.57 GWh. For comparison, the w3e arm had 4.1 and the seam control 8.4.
- **B2022 solve time:** P0 2,292 s and P1 2,799 s, about 91 min of wall clock, inside the 150-min budget.

## Desk bars (arm B, reconciled basis)

| bar (fixed ex ante) | arm B | |
|---|---|---|
| ≤ 4 failing records | **1** (C1 ST_GAS 2019 −9.63 TWh) | PASS |
| C8 holds | PASS. Gated ST_GAS: 2019 27.4 %, 2020 21.3 %, 2023 16.5 %, 2024 16.4 %, 2025 21.9 % | PASS |
| D-4 clean for any new CHP commitment | No CHP row in D-4. B adds no floor: the lever removes a markup and the holdout removes injection. The 5 remaining D-4 failures are the pre-existing ST_GAS `reliability_floor` on plants 990 and 1122, ≤ 0.005 TWh each (6 on the control). | PASS |
| C3a 2020 ≤ +10.5 % | **+9.5 %** | PASS |
| Kill, reading (i) | No CHP class's forced share rises against the control in any of the 21 class-years (table below). | not fired |

Counting scope is the same as w3e:
- price_tail (C3c) and governance (C6) are left out, because a probe carries no attestation.
- sysvol, price_shape, dispatch_corr and C8 PASS.

## Kill bar: both readings

The kill was written as "any CHP class whose forced share exceeds 30 %". Its wording was ambiguous between two readings:
- **(i)** B *raises* a CHP class's forced share against the control *and* it ends above 30 %;
- **(ii)** literally, any CHP class above 30 % in B.

The desk ruled (i) mid-run (Addendum 2, 05:45Z). At that point only the B2020 and B2023 D-2 diagnostics had been reported, and no arm-B gated score was known.

The forcing in every row is the existing D-2-exempt `chp_steam` floor (`chp_steam_following`, cell K).

| class-year | control (w3e) | A | B | (i) | (ii) |
|---|---:|---:|---:|---|---|
| CC_CHP 2019 | 0.507 | 0.416 | 0.374 | — | fires |
| CC_CHP 2020 | 0.432 | 0.359 | 0.321 | — | fires |
| CC_CHP 2021 | 0.649 | 0.566 | 0.514 | — | fires |
| CC_CHP 2022 | 0.583 | 0.531 | 0.472 | — | fires |
| CC_CHP 2023 | 0.327 | 0.281 | 0.254 | — | — |
| CC_CHP 2024 | 0.276 | 0.239 | 0.220 | — | — |
| CC_CHP 2025 | 0.377 | 0.334 | 0.309 | — | fires |
| CT_CHP 2019–2025 | 0.242–0.328 | 0.228–0.328 | 0.204–0.306 | — | fires 2023 (0.306) |
| ST_CHP 2019–2025 | ≤ 0.048 | ≤ 0.045 | ≤ 0.040 | — | — |

**Reading:**
- Under (ii), all six firing rows are inherited from the control, which fires on seven.
- B lowers every one of the 21 shares. The extra grid energy comes from economic dispatch over the same floor.

## Records: control → A → B against the PRECOMMIT predictions (reconciled basis, TWh)

| record | control | A (pred) | B (pred) |
|---|---:|---:|---:|
| CC_CHP 2019 | −9.70 F | −6.00 P (−0.2) | −4.62 P (≈ +0.2…+5.9) |
| CC_CHP 2020 | −7.08 | −3.46 | −1.98 |
| CC_CHP 2021 | −7.88 | −5.67 | −4.43 |
| CC_CHP 2022 | −9.03 F | −7.55 P (−0.8) | −6.12 P |
| CC_CHP 2023 | −5.08 | −1.66 | −0.31 |
| CC_CHP 2024 | −2.01 | +1.12 | +2.25 |
| CC_REGULAR 2019 | −5.21 | −6.03 (−8.5 F) | −1.77 (in band) |
| CC_REGULAR 2020 | −5.48 | −6.55 (−8.8 F) | −2.34 |
| CC_REGULAR 2021 | −9.52 F | −10.52 F (−14.8) | **−5.00 P** (−9.6 F) |
| CC_REGULAR 2022 | −5.63 | −6.52 (−10.4 F) | −0.19 |
| ST_GAS 2019 | −9.83 F | −10.14 F (−10.6) | −9.63 F (−9.9) |
| ST_GAS 2020 | −8.01 F | −8.52 F (−9.1) | **−7.70 P** (−8.0, on the line) |
| COAL_PRB 2019 / 2022 | −1.53 / +5.44 | −2.81 / +5.42 | −0.32 / +5.57 (in band) |
| ST_CHP 2019–2024 | −2.5…−3.6 | −2.5…−3.5 | −2.4…−3.4 |
| C3a 2019 / 20 / 21 / 22 / 23 / 24 / 25 (%) | +4.7 / +8.0 / −6.8 / −5.5 / +2.8 / +0.2 / −6.4 | +3.7 / +6.6 / −7.8 / −6.2 / +1.9 / −0.7 / −7.2 | +6.1 / **+9.5** / −4.7 / −3.0 / +4.3 / +1.7 / −4.9 (2020 pred +10.5) |
| C3b NRMSE max | 0.183 (2021) | 0.186 (2021) | 0.172 (2021) |
| **failing records** | **5** | **3** (pred ≈ 6) | **1** (pred 3–4) |

### Prediction errors (reading rule: a miss of more than 2× is a model-of-the-model failure)

**Arm A misses by more than 2× on its central row.**
- CC_CHP gains 1.5–3.7 TWh/yr against a static gain of 7–10 TWh, about 40 %.
- So CC_CHP 2019 lands at −6.00, not −0.2, and the declared CC_REGULAR displacement (−3 to −5 TWh) does not happen: CC_REGULAR moves only −0.8 to −1.1.
- **Root cause:** the static walk assumed an exempted committed tranche runs whenever it is in merit. In the LP it still cycles hourly on price (census below).
- A's record count (3) beats its prediction (≈ 6) for the same reason: the trade never materialised.

**Arm B over-delivers on its record count in the favourable direction** (1 vs 3–4). The difference is CC_REGULAR:
- The PRECOMMIT expected the holdout to leave CC_REGULAR 2021 failing at −9.6.
- Instead, B raises CC_REGULAR by 2.0–5.4 TWh in every year against the control. The holdout's removal of chp=Y biomass/OTHER injection is taken up by merchant gas as well as by CHP.
- **CC_CHP itself also falls short of prediction** in B (2019 −4.62 vs +0.2…+5.9), for the same cycling reason.

## Attribution (rule 19: A isolates the lever, B stacks the holdout on it)

| TWh/yr vs control | CC_CHP | CC_REGULAR | ST_GAS | C3a |
|---|---|---|---|---|
| A − control (commitment lever alone) | +1.5…+3.7 | −0.8…−1.1 | −0.1…−0.6 | −0.7…−1.4 pt |
| B − A (holdout on top) | +1.1…+1.5 | +2.9…+6.3 | +0.3…+1.1 | +2.3…+3.2 pt |

The lever is the CHP fix. The holdout is what moves CC_REGULAR, ST_GAS 2020 and the price level back up. Neither reaches CC_CHP's measured volume on its own.

## Commitment census (CEMS vs model, CHP plants, CEMS-energy-weighted; phase-0 method)

| year | CEMS online | control online / starts | A online / starts | B online / starts | CEMS starts (median) |
|---|---:|---|---|---|---:|
| 2019 | 0.926 | 0.181 / 65 | 0.358 / 196 | 0.404 / 201 | 8 |
| 2020 | 0.917 | 0.235 / 116 | 0.419 / 243 | 0.468 / 236 | 8 |
| 2021 | 0.862 | 0.143 / 76 | 0.244 / 156 | 0.288 / 187 | 10 |
| 2022 | 0.906 | 0.180 / 66 | 0.249 / 124 | 0.300 / 133 | 6.5 |
| 2023 | 0.920 | 0.308 / 120 | 0.475 / 243 | 0.515 / 229 | 8 |
| 2024 | 0.933 | 0.400 / 205 | 0.569 / 252 | 0.603 / 244 | 7 |
| 2025 | 0.907 | 0.297 / 150 | 0.429 / 212 | 0.462 / 211 | 8.5 |

**What the census shows:**
- Removing the inverted markup roughly doubles the committed tranche's online share.
- It also roughly doubles the starts: the tranche now cycles with the daily price, 200+ starts a year against 7–10 measured.
- **The remaining gap is commitment physics, not price.** A pure LP has no state that keeps a steam host's unit online through a low-price night. Measured, these units run continuously (Midland, Taft and Carville: 1–3 starts a year, CF 0.69–0.81).
- **Open root cause (not a parameter, rule 21):** steam-host CHP has no host obligation in commitment. The structural candidates are:
  - CHP clusters inside the UC MILP stage (MECH 28, ISO-armed), or
  - a host min-run leg on the existing `chp_steam_following` mechanism (rule 19: reconcile with that K floor; never stack a second one).

## Bench-basis sensitivity (arm B)

| basis | B failing records |
|---|---|
| **reconciled** (#7210: artifact + gas fold refuted) | **1**: ST_GAS 2019 |
| original (default share + fold applied) | 5: CC_CHP 2019 +8.02, 2020 +9.03, 2023 +11.10, 2024 +13.51 (over-delivery against the default-share bench), ST_GAS 2019 −9.03 |

On the original basis, B over-delivers against a bench that still subtracts the sector-default BTM share. That is the mismatched pair the w3e FINDING excludes. **B is meaningful only together with #7210.**

## Where the bundles are and what a promotion would cost

**Bundles:**
- Both composed spans and their local registrations are on `claude/closeout-miso-w3f-probe` (off `main`, E13):
  - `2026-10-05-closeout-miso-w3f-arm` is arm A;
  - `2026-10-05-closeout-miso-w3f-b` is arm B on the reconciled basis.
- The per-year legs are on the shard branches above (transport only).

**Steps a promotion of B would take** (an owner decision; this lane does not promote):
1. Owner decision #20 lands #7210 (the artifact plus the gas-fold refutation).
2. Arm `miso_chp_btm_measured`, `chp_startup_covered` and `mustrun_chp_btm_holdout` (the last pending its own cross-ISO ruling, w3c), plus `miso_seam_neighbour_hourly_full_span`, in MISO's `default_scenario_overrides`.
3. Attest. The C3c ledger carries forward. C3c and C6 are not scored here.
4. Run `promote_keeper.py` over the 7-year span. The year set is unchanged.
