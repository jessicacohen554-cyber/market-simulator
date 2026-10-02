# FINDING — SPP W0 ST_GAS availability: the commission-year fallback arms age-escalated WEFOR on top of the measured outage layer (zero LP), 2026-10-02

Lane: closeout-B W0 phase 3. Chartered by the desk's relay of the owner card "Hold, fix derate first" (2026-10-02). Zero LP: every number below comes from a `run_year(fleet_only=True)` rebuild.

## Question

Why does the SPP-107 W0 re-solve's train tier fall? C1 ST_GAS crosses its volume band in 2024 (−7.85 → −8.16 TWh) and 2025 (−7.61 → −8.26 TWh).

## Method

- Rebuild the 2024 SPP fleet three ways:
  - the W0 recipe (`w0_spp_span`);
  - the incumbent's own recorded pre-W0 values (`spp107EXR_span`);
  - the W0 recipe with each W0 field switched off one at a time.
- Compare ST_GAS installed MW and mean available MW (availability × pmax) per row and per plant.

## Result (2024, ST_GAS, MW)

W0 vs pre-W0: pmax goes 9,515 → 10,122 and annual mean available goes 3,836 → 3,703. Jun–Sep goes 6,017 → 5,974 and Dec–Feb 2,553 → 2,469.

Each row is the W0 fleet with one field switched off:

| W0 field switched off | Δ pmax | Δ available, Jun–Sep | Δ available, Dec–Feb | Δ available, annual |
|---|---:|---:|---:|---:|
| `commission_year_cod_fallback` | 0 | **+80** | **+128** | **+166** |
| `retiree_vintage_status_scope` | +221 | +61 | +54 | +54 |
| `admit_standby_units` | −39 | −35 | −29 | −29 |
| `partial_plant_exit_carry` | **−560** | −1 | −12 | −3 |
| `seasonal_capacity_basis` | −8 | −1 | +1 | +2 |
| the other four fields | 0 | 0 | 0 | 0 |

## Findings

1. **Correction to the phase-3 note to the desk.** The note said W0 adds zero-availability ST_GAS rows. That is wrong. W0 adds one new ST_GAS plant (2244, 39 MW, available). The +568 MW of pmax comes from `partial_plant_exit_carry`, which carries exited units' MW inside existing tranches. That MW is almost entirely unavailable, but it moves annual availability by only −3 MW. It is a census/pmax effect, not the dispatch driver.
2. **The driver is `commission_year_cod_fallback`, at −166 MW annual mean (−80 Jun–Sep, −128 Dec–Feb).**
   - With the fallback off, SPP's per-plant rows fall through to `online_year = 2010` (the master registry is ERCOT-only, miso-159). The age-escalation limb of `THERMAL_AVAILABILITY` is then inert.
   - With it on (W0), each plant takes its real EIA-860 commission year (1962–1989 for these steam plants). For ST_GAS that is WEFOR 0.21 + 0.003 per year past age 30, so roughly 0.21 → 0.30 at age ~62, or 0.147 → 0.214 after `wefor_multiplier = 0.7`.
   - The largest plant moves are 3484 −25, 3478 −19, 2956 −16, 2965 −11, 2952 −11 and 6193 −11 MW.
   - The fallback is a correctness repair (true vintages). What it exposes is the issue in finding 3.
3. **Rule 19 [R-ONE-MECH] question.**
   - SPP backcasts take outages from the measured layer (`outage_source = historic`: CAMPD overlay, unit, partial and short derates). They also keep the statistical age-based WEFOR on the same rows, with no residual relief: `wefor_residual_cap` is unset and `wefor_residual_groups` is None.
   - Pre-W0 the stack was hidden at a flat 2010 age. W0 makes the statistical limb grow with true age, on top of measured outages that already carry those units' history.
   - The relief mechanism that reconciles exactly this stack exists: the WEFOR residual cap, "historic-backcast double-count relief". MISO arms it on measured evidence. It is not armed for SPP.
4. `retiree_vintage_status_scope` (−221 MW pmax, −54 MW available) is a roster correction (rule 14) and stays.

## Recommendation (for the desk and owner)

- Do not revert the commission-year fallback. It is measured data (rule 14).
- Reconcile the stack instead (rule 19). For SPP, decide on measured evidence whether the statistical ST_GAS WEFOR should yield to the measured outage layer: the existing residual-cap relief, scoped by class, as MISO's is. That is the second fix the SPP re-solve would carry, alongside #7081.
- Zero-LP pre-check before any solve: compare the measured CAMPD forced-outage share for SPP ST_GAS against the statistical WEFOR, by age band.

Artifacts (scratchpad, not committed): `sppstgas/rows_{w0,pre,off_<field>}_2024.parquet`.
