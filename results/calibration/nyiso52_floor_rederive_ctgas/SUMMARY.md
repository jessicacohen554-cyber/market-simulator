# nyiso 52 floor rederive ctgas — PROBE (keeper-candidate pending #1344; keeper stays nyiso-41 STALE-VS-HEAD)

The CT/ST reliability-floor re-derivation named as the remaining structural work
in PR #1427 (rule 23), combined with the PR #1427 delivered-fuel input
(`nyiso_downstate_ct_gas_basis`, kept default-off). Companion floors-alone probe:
`nyiso 51 floor rederive`. One-delta baseline: `nyiso 48 head regate`.

> Registered as a PROBE (rule #15). Full disposition also in the co2-keeper-regate
> handoff and `docs/calibration-log.md`.

## The re-derivation (rule 17/18/23 — source-grounded narrowings, NOT re-levels)

Audit of every enabled NYISO CT/ST floor vs rule 17, using the nyiso-48 baseline
`legitimacy_diagnostics.json` (D-1/D-2/D-4) + CAMPD downstate CT/ST diurnal CF:

1. **reliability_floor × CT_PEAKER — NYC standalone 24h step (tmax 31.7 / floor
   0.1833, enabled, NO window).** Bound all 24h on hot days incl. overnight where
   measured CAMPD NYC CT CF ~= 0.018 flat; stacked on the windowed `NYC_CT_ev`
   ramp (rule 18/19 — two mechanisms, one phenomenon). This was the D-4
   off-window binder (baseline 30.5/30.9/34.3% of floored CT MWh off-window).
   **FIX: `r1_disabled=True`** in `reliability_floor_coeffs_NYISO.csv` — the
   windowed ramp is the single mechanism. No overnight driver exists.

2. **nyiso_local_selfsupply × LI in-zone thermal (incl CT_PEAKER), frac 0.45 ×
   LI load, ALL 24h.** Its source (LI LCR requirement / firm import_limit
   325/275/275 MW, `data/raw/capacity-deliverability/nyiso/nyiso.csv`) is a
   PEAK-hour ICAP basis, not an all-hours energy driver; the 0.45 is
   residual-identified (constants.py DOF ledger S5, issue #1345). D-2: forced
   1.84/2.87/1.86 TWh of CT_PEAKER (43/65/42% of class), most of it overnight
   where measured LI CT CF ~= 0.06 flat and LI imports never bind off-peak
   (reserve-incidence handoff Finding 4). **FIX: narrowed to the HB14-21 peak
   window** (`NYISO_SELFSUPPLY_FLOOR_HOURS`), the summer design-cooling condition
   the LCR is defined at. The **0.45 level is unchanged** — only the hours it had
   no driver for are removed.

3. **ST floors — audited, LEFT UNCHANGED (legitimate).** NYC/LI ST_GAS persistent
   24h base (0.391/0.289 when-available) is applied on frac × AVAILABLE cap, so
   all-hours CF ~0.04-0.06 matches CEMS; passes C7 (D-1) and D-4. The rule-20
   ST_GAS forced-share exceedance is a small-denominator artifact of the steam
   under-run, not over-forcing.

## Gate (one-delta vs nyiso-48, all years 2023/2024/2025)

| metric | nyiso-48 base | nyiso-51 floors | **nyiso-52 floors+gas** | actual |
|---|---|---|---|---|
| CT_PEAKER TWh | 4.46/4.51/4.73 | 3.70/2.84/3.86 | **2.02/2.33/2.91** | 2.26/2.13/2.84 |
| ST_GAS TWh | 6.15/7.58/9.30 | 6.29/7.59/9.43 | 6.72/7.77/9.74 | 8.70/11.07/15.99 |
| C1 free-class | 9/10 | 9/10 | **9/10** | — |
| C7 (D-1) 2024 CT cv_ratio | FAIL 0.454 | PASS 2.393 | **PASS 3.47** (r 0.84) | — |
| C3a mean LMP | -17/-18/-15% | -16.2/-15.5/-13.6% | **-13.5/-14.7/-12.5%** | — |
| C3c >$300 h | 0/0/7 | 0/0/7 | 0/0/7 | 10/12/42 |
| D-2 CT forced-share (rule 20 ≤10%) | 22%+ss | 25.6/34.1/25.1%+ss | **45.8/54.5/39.3%+ss FAIL** | — |
| D-4 CT off-window | 30.5/30.9/34.3% (incl overnight) | h14 only, 0 overnight | h14 only, 0 overnight | — |

## Findings

- **C7 (the NYISO calibration-complete item-1 blocker) is FIXED** both configs.
  The overnight CT flatness is gone: reliability-floor CT overnight energy =
  **0.000** (was ~0.18 TWh from the NYC step), self-supply CT forcing HALVED.
- **CT_PEAKER volume lands near-exact** with the gas premium (config B):
  2.02/2.33/2.91 vs actual 2.26/2.13/2.84.
- **D-4 residual is a metric-boundary artifact, not a rule-17 violation.** The
  reliability floor binds EXACTLY h14-21 with 0.000 overnight; the ~34%
  "off-window" is entirely hour 14, flagged only because D-4's hardcoded
  canonical CT window is h15-21 (from the CAISO ct_netload_drag derivation) while
  the NYISO ramp is source-derived HB14-21 (start_hour=14). Left as-is (rule 23 —
  not tuned to the gate).
- **NOT YET A KEEPER.** Rule-20 D-2 CT_PEAKER forced-share still >10% and
  C3a/C3c still FAIL. Both are the SAME root cause: the missing **#1344**
  peaker-scarcity / reserve (RCPF) price structure. Without it CT peakers never
  clear economically (reserve-incidence handoff Finding 3: idle peakers = phantom
  reserve = no scarcity price), so the floors carry ALL the CT commitment (high
  forced share) and the downstate tail never prices (C3a/C3c). The floor
  re-derivation removes the *illegitimate overnight* forcing; the *remaining*
  in-window forced share and the price gap are cleanly #1344, not floor-forced.

## Disposition

Keeper stays `nyiso-41` **STALE-VS-HEAD**; `keepers.json` unchanged (recommendation
only). The re-derived floors are correct rule-17/18/23 structure and are the new
NYISO default (unconditional, backcast + forecast). `nyiso 52` (floors + the
default-off delivered-fuel basis) is the **recommended eventual NYISO keeper
config once #1344 lands** — it needs no further floor work, only the reserve-price
structure to lift C3a/C3c and drop the CT forced share below 10%. #1344 is out of
scope here (parallel LP-core refactor). Did NOT re-arm the de-leaked offer scalars
(rule #26).

## Reproduce

```
python scripts/solve_nyiso_floor_rederive.py --config floors_gas   # nyiso 52
python scripts/solve_nyiso_floor_rederive.py --config floors        # nyiso 51
```
Both replay the nyiso-41 keeper meta at HEAD (= nyiso-48 baseline offer curve)
under the re-derived floors now on disk; `floors_gas` adds
`nyiso_downstate_ct_gas_basis=True`.
