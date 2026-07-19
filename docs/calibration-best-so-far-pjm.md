# PJM calibration — best config so far

> Status: SUPERSEDED-BY frontend/data/backcast/keepers.json + docs/codebase-site/calibration-status.html — historical keeper snapshot, not current keeper truth.

> **DETERMINATION (2026-06-22, scorer): NOT-YET** for the registered keeper
> `pjm-38-outage-regate` (`python scripts/calibration_verdict.py --run-id
> 2026-06-21-pjm-38-outage-regate`; bundle `results/calibration/pjm_38`). This is
> the keeper's **first real registration** — it was a stub (meta.json +
> run_config.json only, never rendered), so the scorer previously saw all years
> data-blocked. Re-solved its committed config from meta.json, writing
> `btm.parquet` + the full dashboard payload + bench; C6 governance now PASS
> (truthful attestation). Deciding fails are genuine **MODEL MISSes** (not
> ledgerable per rubric §3):
>
> - **C2 coal +17.3 / +13.9 / +22.8%** and C1 COAL_PRB +2.5–3.7 TWh / COAL_BIT
>   +13–22% — the documented **PJM structural coal over-run**, a SEPARATE known
>   issue (`docs/...pjm-lmp-residual`, `pjm-coal-mustrun-floor`) that the
>   net-load outage re-gate amplifies (freed cheap take-or-pay coal). **Not**
>   folded into the BTM re-gate; the offer-curve / coal-cost retune is the next
>   model-side frontier.
> - C1 CT_PEAKER −18/−33% under (2023/24) and ST_CHP −1.2 to −1.7 TWh under;
>   CC_CHP +1.0–2.0 TWh over (model runs some CC-CHP plants above their measured
>   EIA-923 grid output, now visible on the grid-delivered BTM basis).
> - C3a mean LMP −11.4 / −19.3% (2024/25) — the LMP cools below actual, tracking
>   the same coal-over / over-export wedge.
>
> C4 dispatch correlation PASSes. C3c/C5a/C5b are SKIPPED (series not in payload —
> the shared-render gap noted for every ISO). BTM did its job (CHP now
> grid-delivered); the determination is gated by the coal over-run, the
> acknowledged separate workstream.
