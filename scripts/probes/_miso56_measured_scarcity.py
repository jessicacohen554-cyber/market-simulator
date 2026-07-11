"""miso-56: Lane-2 RDC/ELMP scarcity — measured requirement shape + evening timing.

Executes the miso-55 handoff's sanctioned Lane 2 (RDC/ELMP scarcity depth +
evening timing) on what the measured data actually supports. Replays the
RECOMMENDED CANDIDATE's exhaustive ``miso55_ct_faststart/meta.json`` through
the RENAME + signature-check machinery (never
``run_config.json:calibration_flags`` — the miso-50..53 islanding trap), with
exactly two deliberate changes on top of the HEAD code state:

1. **Measured hourly OR requirements** (``miso_measured_reserve_requirements``,
   ``data.miso_reserve_requirements`` ← ``asm_rt_cleared_mw_<year>.parquet``):
   the market-wide RBDC family drops the flat fleet-MSSC + 400 MW estimate
   (~3.44 GW) for the measured hourly cleared reg+spin+supp series
   (mean 2.45/2.56/2.64 GW, max 3.07/3.12/3.30 GW for 2023/24/25 — the
   event-evening requirement increases MISO actually posts, e.g. Aug 12 2023
   HE17-20 2410→2830 MW, are now in the LP at the right hours), and the South
   zonal family drops the within-zone-MSSC static (~2.2 GW) for the measured
   South reservation (mean 321/366/477 MW) — the static basis fabricated
   ~1.8 GW of South withholding the real market never held. Rule-13 (a
   measured AS power reservation) + rule-14 (measured beats the overstated
   estimates, whatever the residual does).

2. **Condition-keyed fast-start amortization horizons**
   (``tranche_startup_conditional_runs``, v4 of the Order-825/ELMP lever):
   CAMPD measures MISO CT runs STARTED in p97.5+ net-load hours at a 6 h
   median vs 10 h pooled (ratios 0.9/1.1/1.1/0.8/0.6 across the
   [0-.5/.5-.75/.75-.9/.9-.975/.975+] bands, stable each of 2023/24/25;
   ``derive_campd_ct_run_lengths.py --condition-bands`` →
   ``campd_ct_run_bands_MISO.csv``, 61,322 runs). The v3 measured ceiling now
   scales per hour by the band ratio of the hour's within-year net-load
   percentile — a tight evening engagement is a shorter commitment block, so
   its start recovery amortizes over fewer hours in exactly the HE15-20 tight
   hours (the ELMP evening-timing element the monthly grain could not carry).

**Measured adjudication recorded ex-ante (rule 1 — score movement is a
by-product):** the DA reserve MCPs (asm_damcp) hit the RDC steps in ZERO
hours of 2023-24 (max $27) and once in 2025 ($132) — real DA reserve
scarcity is ~nonexistent, so the model's 0 binding RDC hours is
structurally CORRECT on the DA basis; the RT tail (supp/spin MCP ≥ $190 in
3-4/8-11/17-19 h) is where reserve scarcity lives, outside the DA-expressible
scoring frame. The 2025 residual's IMM-measured drivers (Summer-2025
quarterly): RDT S→N congestion ($9.31/MWh regional separation — the
transmission lane), June-23/24 ELMP *ex-post* emergency repricing (2.5× ex
ante — an RT construct), and the hour-18 net-load-ramp OR shortage intervals
(26, RT forecast-error events). Expected direction here: correctly-timed
evening markup lift (+$1-2/MWh band-4 hours), South withholding release,
requirement shape honesty; July-2025's −18 $/MWh monthly gap is NOT expected
to close (its drivers are measured to live elsewhere).

Also solves the rule-20 zero-forcing ablation twin (``mode=ablation``).

Usage: python scripts/probes/_miso56_measured_scarcity.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso55_ct_faststart"
OUT_NAME = "miso56_measured_scarcity"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below. The three ercot_* recorder keys are inert (false/null) in
# the MISO meta and have no kwarg; the signature check below still errors on
# any NEW unmapped key so nothing can drop silently.
SKIP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "timestamp",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "highspy_version",
    "shared_inputs",
    "commitment",
    "commitment_screen_coal",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}


def main(mode: str) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    ablate = mode == "ablation"
    out = ROOT / (OUT_NAME + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    sig = inspect.signature(solve_and_persist).parameters
    kwargs = {}
    unmapped = []
    for k, v in meta.items():
        if k in SKIP:
            continue
        mapped = RENAME.get(k, k)
        if mapped in sig:
            kwargs[mapped] = v
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(
            f"meta.json keys not bound to solve_and_persist: {unmapped} — "
            "extend RENAME/SKIP deliberately, never drop silently"
        )
    # Guard the skipped inert keys: if a future meta ever arms one, fail loud.
    for k in ("ercot_zonal_gas_basis", "ercot_west_netload_gas_shape"):
        if meta.get(k):
            raise SystemExit(f"meta.json arms skipped key {k} — replay invalid")
    if meta.get("ercot_west_gas_delivered_floor") is not None:
        raise SystemExit("meta.json arms ercot_west_gas_delivered_floor")

    # The two deliberate changes vs the miso-55 recipe (docstring §1-§2).
    kwargs["miso_measured_reserve_requirements"] = True  # measured OR series
    kwargs["tranche_startup_conditional_runs"] = True  # v4 evening timing

    solve_and_persist(
        meta["years"],  # all three train years in one bundle (rule 16)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(OUT_NAME if ablate else None),
        note=(
            f"miso-56 Lane-2 measured scarcity ({mode}) -- miso-55 meta.json "
            "replay (full candidate structure: reserve co-opt pergen + zonal "
            "South + priced seam + intermediate splits + SOM coal offers + "
            "CT 1.025 measured committed + Order-825 fast-start v3) + "
            "measured hourly OR requirements (asm_rt_cleared_mw reg+spin+supp "
            "market-wide & South, miso_measured_reserve_requirements) + "
            "condition-keyed fast-start amortization horizons "
            "(tranche_startup_conditional_runs, campd_ct_run_bands_MISO.csv "
            "net-load-percentile band ratios 0.9/1.1/1.1/0.8/0.6), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
