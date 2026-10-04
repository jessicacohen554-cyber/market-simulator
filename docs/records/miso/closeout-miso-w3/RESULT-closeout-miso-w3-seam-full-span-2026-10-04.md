# RESULT — closeout-MISO-w3: the hourly neighbour seam ladder over 2019–2022 beats the keeper on structure. Two failing records flip to PASS (C1 CC_REGULAR 2021, C3b 2021), every kill is clear, and price_shape now passes. MISO stays NOT-YET on C1 ST_GAS 2019 and C3a 2020.

```
LANE      : closeout-MISO-w3 (desk session_01ERkBTm23ZAP4CTZnJVD9Ss)
PRECOMMIT : PRECOMMIT-closeout-miso-w3-seam-full-span-2026-10-04.md (pushed 72ed3d85, before any solve)
PIN       : 381ee26c7fe6cefb15b79334e14e0bd57e095eec (G-DRIFT f98c4564 -> 90cea720: every hunk INERT for MISO)
ARM       : keeper recipe + miso_seam_neighbour_hourly_full_span=true (one field)
PROBE     : run 2026-10-04-closeout-miso-w3-seam, bundle results/calibration/closeout_miso_w3_span
            (7 year-isolated legs, composed by _miso260_compose_span.py; all 11 shared-input refs equal the keeper's)
CONTROL   : keeper 2026-10-03-closeout-miso-nuc-r (committed bundle; no control solve, rule 29b)
RUBRIC    : v3.20 (unchanged)
```

## Legs (one shard each, archived after fetch + verify)

| year | shard branch @ commit | files | dispatch P1 | unserved |
|---|---|---:|---:|---:|
| 2019 | claude/closeout-miso-w3-2019 @ d874bdab | 17 | 73.2 MB | 0 |
| 2020 | claude/closeout-miso-w3-2020 @ 92861870 | 17 | 68.5 MB | 0 |
| 2021 | claude/closeout-miso-w3-2021 @ c296a58a | 17 | 80.1 MB | 0 |
| 2022 | claude/closeout-miso-w3-2022 @ 286b1201 | 17 | 71.3 MB (zstd-9) | 0 |
| 2023 | claude/closeout-miso-w3-2023 @ 8637c66b | 17 | 65.6 MB | 0 |
| 2024 | claude/closeout-miso-w3-2024 @ 0e17876b | 18 | 74.2 MB | 8,357 MWh (same as the keeper) |
| 2025 | claude/closeout-miso-w3-2025 @ 9494792a | 17 | 57.6 MB (zstd-9) | 0 |

Each leg's `run_config.json` records `miso_seam_neighbour_hourly_full_span: true` at pin 381ee26c and carries `unit_marginal_<y>`.

**Composite benchmark basis.** The composed meta first inherited the 2019 leg's single-year shared-input refs. `run_calibration_full.py --rebuild-benchmark` (zero LP) re-pointed them at the seven-year frames. All 11 refs now equal the keeper's (`campd fe5d500c…`, `eia923 cece4730…`, `eia930 105bfdb6…`, …), so the scoring basis is identical.

## Scored records that move (keeper → probe, rubric v3.20)

| record | keeper | probe | |
|---|---:|---:|---|
| **C1 CC_REGULAR 2021** | −8.15 TWh **FAIL** | −6.41 TWh **PASS** | T1 hit (+1.74) |
| **C3b 2021** | 0.219 **FAIL** | 0.177 **PASS** | T2 hit (−0.042) |
| C1 ST_GAS 2019 | −8.71 FAIL | −8.42 FAIL | toward |
| C3a 2020 | +10.2 % FAIL | +10.3 % FAIL | declared wrong sign; +0.1 pt (K5 limit +2.0) |
| C3a 2021 | −8.4 % | −4.9 % | toward |
| C3a 2022 | −6.9 % | −3.7 % | toward |
| C3a 2019 | +6.2 % | +6.4 % | away, in band |
| C3b 2019 / 2020 / 2022 | 0.091 / 0.147 / 0.127 | 0.089 / 0.142 / 0.088 | all toward |
| C1 CC_REGULAR 2019 / 2020 / 2022 | +3.17 / −1.24 / −5.48 | +0.67 / −3.10 / −2.70 | in band |
| C1 COAL_PRB 2019 / 2020 / 2021 / 2022 | +4.56 / +3.87 / +5.03 / +5.72 | +6.01 / +4.70 / +4.99 / +5.43 | in band; no declared coal crossing happened |
| C1 COAL_BIT 2019 / 2020 / 2021 / 2022 | −2.79 / −4.66 / −1.26 / +5.21 | −1.47 / −4.14 / −0.68 / +5.12 | toward |
| C1 CT_PEAKER / ST_GAS / CC_CHP 2020–2022 | — | all toward measured | in band |
| 2023 / 2024 / 2025 | — | identical in every record | inert, as constructed (K6) |

**Determination.**

| | criteria FAIL | failing records | price_shape | determination |
|---|---|---|---|---|
| keeper | fuelmix, price_mean, price_shape | 4 | FAIL | NOT-YET |
| probe, as registered (no attestation) | fuelmix, price_mean | 2 | PASS | NOT-YET |
| probe, with the keeper's attestation carried forward (local, uncommitted) | fuelmix, price_mean | 2 | PASS | NOT-YET |

The registered probe also reads C3c FAIL and C6 UNATTESTED. That is only because a probe has no attestation; the keeper's C3c ledger is what a promotion carries forward. With the attestation carried forward, the grade summary is 8 scored / 5 target / 1 ledgered / **2 fails**, against the keeper's 8 / 4 / 1 / **3**. C2, C4 and C8 PASS.

## Bars (PRECOMMIT)

| bar | reading | verdict |
|---|---|---|
| T1 CC_REGULAR 2021 ≥ +0.5 TWh | +1.74 TWh, FAIL → PASS | **hit** |
| T2 C3b 2021 ≤ −0.010 | −0.042, FAIL → PASS | **hit** |
| K1 both targets fail | — | clear |
| K2 wrong-way target | — | clear |
| K3 any gas C1 2019–2022 PASS→FAIL | none (every gas row moves toward measured, except CC_REGULAR 2019/2020, in band) | clear |
| K4 C3a other years leave ±10 % / C3b crosses 0.20 | max C3a +6.4 % (2019); every C3b improves | clear |
| K5 C3a 2020 worse by > +2.0 pt | +0.1 pt | clear |
| K6 2023–2025 differ beyond G-DRIFT | identical in every record | clear |
| K7 net import away from EIA-930 by > 2 TWh in ≥ 3 of 4 years | 2 of 4 (see below) | clear |

**Beats the keeper:** yes. Failing records fall 4 → 2, no kill fires, and price_shape becomes PASS.

## Reported against interest

1. **Seam volume moves away in 2021–2022.** Model vs EIA-930 net import (TWh, import negative):

   | | 2019 | 2020 | 2021 | 2022 |
   |---|---:|---:|---:|---:|
   | measured | −50.07 | −56.37 | −35.51 | −30.97 |
   | keeper | −48.43 | −56.30 | −30.90 | −17.93 |
   | probe | −48.16 | −56.55 | −27.13 | −13.44 |

   The price records move toward measured while the volume moves away. Once neighbour prices are hourly, the measured spread no longer clears the 2021–2022 bands as deeply against the model's own price. The record is below the K7 threshold but is real, and 2022's volume error was already −13 TWh on the keeper.
2. **The C3a 2020 overshoot is untouched.** +10.3 % is the same low-load level shift (MISO-F3), and the static census predicted this. Spring 2020 moved the right way, but that move is too small for the annual mean.
3. **The D-4 per-unit rider on plant 990** (`reliability_floor`/`st_gas_mustrun_per_plant` × ST_GAS) appears in the 2022 leg's diagnostics. The keeper already carries the same rider in 2019. C8 PASSES on the composite.

## Promotion cost (if the desk takes the slot)

- **Code:** the field lands default-off with this lane's PR. Promotion arms it in the MISO recipe (`_miso_config` `default_scenario_overrides`, or `--set` in the replay recipe), with zero DOF added.
- **Solves:** none. The seven legs and the composed span are promotable as they stand. The bundle is on branch `claude/closeout-miso-w3-probe` (composite + registration). The legs are also on their shard branches until the lane PR merges.
- **Ledger:** the keeper's attestation carries forward (C3c entries re-measured, unchanged hour counts). MISO-F2's "fall-2021 coal conservation" row becomes inert for C1 (C1 CC_REGULAR 2021 now PASSES) and for C3b 2021 (now PASSES); MISO-F1 (ST_GAS 2019) and MISO-F3 (C3a 2020) remain.
- **Promotion lessons from earlier lanes:**
  - move the gitignored leg dirs to the scratchpad before the parity gate;
  - re-key the `config_partition` run_ids if the strict audit stops on E12/S1;
  - update `keepers/MISO.json` `superseded`.

## Matrix

`seam_neighbour_hourly_ladder` (MISO): the cell stays **K**, with the year extension recorded as tested and beating the keeper. The probe is registered on `claude/closeout-miso-w3-probe` only (E13).
