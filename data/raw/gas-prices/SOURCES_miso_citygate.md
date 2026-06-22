# MISO gas-basis citygate proxies

`eia_citygate_IL_MI_monthly_2023-2025.csv` — EIA monthly Natural Gas Citygate
Price ($/Mcf), 2023-01 .. 2025-12.
  - Illinois citygate (series N3050IL3)  -> Chicago Citygate proxy
  - Michigan citygate (series N3050MI3)  -> MichCon proxy

Source: EIA API v2 `natural-gas/pri/sum` (monthly). Pulled 2026-06-22.

Caveat: these are EIA utility-citygate state averages, NOT the ICE
Chicago-Citygate / MichCon daily trading-hub spot indices (paywalled / not
on the allowlist). They are the accessible reproducible monthly proxy for the
MISO gas-basis track; the daily hub indices remain a manual-download item
(see docs/multi-iso/miso-data-audit.md). $/Mcf ~= $/MMBtu within ~3% for
pipeline-quality gas (HHV ~1.037 MMBtu/Mcf).
