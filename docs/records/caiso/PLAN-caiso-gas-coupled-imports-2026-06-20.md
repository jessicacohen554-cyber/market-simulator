# CAISO no-OASIS import lever — methodology + plan (2026-06-20)

Branch: `claude/caiso-lmp-lever-ab-m56edy`. Supersedes the OASIS-dependent lever A
in `DIAGNOSIS-caiso-import-ladder-2026-06-19.md`. The CAISO OASIS intertie-LMP
fetch is abandoned (the runner hangs/throttles on `oasis.caiso.com`; every
`PRC_LMP` window returns no data — see the failed `fetch-caiso-intertie-lmp` runs
2026-06-19). It was also never *forecast-consistent*: a forecast has no measured
intertie LMP. This note records the best-practice replacement.

## Methodology: how energy models price CAISO imports

- **Full-WECC production-cost models** (PLEXOS-WECC, Aurora, GridView, EnCompass —
  the CAISO/IOU/consultant standard for IRP/RA/price studies) model *every* WECC
  BA as a zone with its own fleet + load, joined to CAISO by interfaces (COI, NOB,
  Path 46) with hurdle rates/TTCs. Imports/exports emerge endogenously; the
  "import price" is the intertie shadow price = the neighbor's marginal cost.
- **Reduced-form / CAISO-only models** (this one) collapse that into a
  price-quantity **import supply curve** at the interties, indexed to the
  neighbors' fundamentals: the **desert-SW (Palo Verde/Mead) leg is gas-set**
  (its price tracks SW gas + solar); the **PNW (Mid-C/Malin) leg is hydro-set**
  (tracks runoff).

The current `IMPORT_TRANCHES["CAISO"]` ladder *intends* this ("DSW gas blocks
priced at CA-gas-equivalent + wheeling") but the levels are **fitted to the
model's own solved price** and set high to throttle volume. That fit is what the
user's no-curve-fitting rule (claude.md #1/#11) targets, and it is why lever B
breaks: lever B lowers CA gas ~$8/MWh but the fitted import blocks don't move, so
domestic gas undercuts the desert-SW gas imports and steals their share — gas
over-runs (70.9 → 76.1 TWh, EIA-923 67.7).

## What the 2024 runs showed (this session, all in-repo data, no OASIS)

| run | mean | p50 | neg hrs | gas TWh | net imp TWh |
|---|---|---|---|---|---|
| baseline keeper | 55.5 | 56.2 | 14 | 70.4 | 32.6 |
| B + full `--interchange-shaping` | 53.5 | 54.9 | 37 | **87.8** | 15.2 |
| B + `--interchange-shaping-export-only` | 47.4 | 48.0 | 37 | 75.7 | 27.8 |
| target (actual RT / EIA-923) | 32.9 | 34.0 | 868 | 67.7 | 30.8 |

- **`--interchange-shaping` is a dead end.** Full shaping caps *gross* imports to
  the *net* envelope → imports starve (15 TWh), gas balloons (87.8). Export-only ≈
  lever-B-alone (gas still 75.7) because the envelope only *allows* midday export,
  it does not *force* it (model exports 0.2 TWh). Neither disciplines gas nor
  restores the negative tail.
- **Baseline net imports (32.6) already ≈ measured (30.8).** The gas over-run is
  purely lever B cheapening gas and stealing import share — a *price-coupling*
  defect, not a volume defect.

## Plan — gas-couple the desert-SW import blocks to the measured commodity gas

Forecast-consistent + grounded (claude.md #11): the desert-SW gas import blocks
are gas-set, so they must move with the **same measured commodity-spot gas** that
lever B applies to in-state gas (Henry Hub monthly + measured CA citygate basis,
`fuel.iso_hub_monthly_gas_prices`). Apply lever B's gas-level delta to the
gas-EF import tranches, preserving the ladder's relative supply-curve *slope*
(the reduced-form neighbor merit order that controls volume):

    newprice_tranche[m] = ladder_price + (commodity_spot_gas[m] − F923_delivered[m]) × HR_tranche
    HR_tranche = IMPORT_TRANCHE_EF["CAISO"][tranche] / 0.0531   (CCGT ≈ 6.97, CT ≈ 10.36)

- Applies to the gas-EF tranches only: `DSW_CCGT`, `DSW_CT`, `WECC_scarcity`.
- Zero-EF tranches (`PNW_hydro_base`, `PNW_midC`, `DSW_solar_PV`) are *not* gas-set
  → untouched (hydro/solar, no gas coupling).
- Reuses the `transmission.inject_caiso_import_hub_prices` seam (per-tranche mc
  overwrite + border carbon), fed by a new fundamentals price source instead of
  the OASIS parquet. Default-off, byte-identical off, flag-gated; pairs with
  `--gas-hub-basis-overlay`.

Mechanism: when lever B cheapens CA gas, the desert-SW gas imports cheapen by the
same token → they hold their share → gas stops over-running, while the body still
drops with gas. At baseline gas the delta is ~0, so the validated import-volume
behavior is preserved; only the gas-sensitivity is added — no new fit.

### Limits / honest scope

- Targets the **gas-volume + price** half (the user's primary success criterion).
- The **negative tail** (model 14–37 hrs vs actual 868) is a *separate* structural
  item: it needs the desert-SW solar diurnal (Palo Verde midday glut), for which
  there is no in-repo SW per-fuel series (EIA-930 BALANCE has neighbor BAs but no
  fuel split; eia-930-hourly has CISO only). Reported honestly, not fit.
- The structural floor (~$34 median, below CA gas marginal cost) is unreachable by
  a merit-order LP, as the diagnosis established. Mean will not reach $33.

### Validation gate

Keeper only if A+B-equivalent **lowers price AND holds gas near 67.7 AND net
imports near 30.8**, on 2024 then 2023/2025. No `_calibration_config` default flip
until validated on 3 years.
