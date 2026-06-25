# CAISO caiso-29 — HSL endogenous curtailment wiring (2023–2025)

caiso stgas-hrfix keeper config + uncurtailed-VRE wiring for the no-HSL years
(`renewables.py` `_UNCURTAILED_FALLBACK_ISOS`). See
`docs/forecast-methodology-gaps-2026-06.md` G7.

## What changed

- CAISO **2023/2024** already consume a built HSL parquet (EIA-930 delivered +
  CAISO reported curtailment) — unchanged.
- CAISO **2025**'s Production-and-Curtailments workbook is **partial** (only
  reaches May), so `build_caiso_hsl.py` correctly refuses to fabricate a
  full-year HSL. 2025 now gets the **gross-up uncurtailed potential** (delivered
  grossed up by the most-recent-HSL-year reference rate — 2024: wind 1.13%,
  solar 6.63%) instead of the net-of-curtailment delivered series.

## Modeled vs measured curtailment (diagnostic — rule #11)

| year | fuel | potential TWh | model gen TWh | model curt % | measured curt % | source |
|------|------|--------------:|--------------:|-------------:|----------------:|--------|
| 2023 | wind | 16.55 | 16.55 | 0.00 | 0.91 | ISO-reported HSL−GEN |
| 2023 | solar| 39.79 | 39.79 | 0.00 | 6.31 | ISO-reported HSL−GEN |
| 2024 | wind | 20.29 | 20.29 | 0.00 | 1.13 | ISO-reported HSL−GEN |
| 2024 | solar| 47.91 | 47.91 | 0.00 | 6.62 | ISO-reported HSL−GEN |
| 2025 | wind | 20.04 | 20.04 | 0.00 | 1.13 | ref rate (2024 HSL) |
| 2025 | solar| 53.35 | 53.35 | 0.00 | 6.63 | ref rate (2024 HSL) |

## Key finding — CAISO does not curtail endogenously (pre-existing)

The LP dispatches **100% of the renewable potential** every year — including the
**unchanged HSL years 2023/24** (model solar curtailment 0.0 vs CAISO-reported
~2.5–3.2 TWh). The surplus solar is **absorbed via negative renewable offers and
exported through the priced WECC intertie** rather than curtailed (net
interchange −39/−32 TWh import, with an export sink that soaks up oversupply).

So the uncurtailed potential is wired correctly, but the dispatch's economics
never bind to force curtailment. This is a **pre-existing CAISO characteristic,
not introduced by this change** (the HSL years it doesn't touch show the same
0%). Making CAISO curtailment endogenous — tightening the export/ATC envelope so
midday oversupply binds, or removing the negative-offer absorption — is a
separate investigation (forecast-gaps G8 territory).

## Caveat — intervening main-code

NOT-YET, but the score is confounded by the **freshly-merged caiso-intertie /
transmission code** in current main (priced interchange, per-hub intertie,
corridor ATC), independent of this HSL wiring.
