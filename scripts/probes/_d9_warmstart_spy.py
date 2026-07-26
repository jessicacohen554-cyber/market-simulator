#!/usr/bin/env python
"""D-9 multi-ISO: confirm the forecast warm start is LIVE, not silently inert.

A cold-vs-warm A/B that shows an identical trajectory proves nothing if the warm
arm never actually installed a basis. The ERCOT D-9 record closed that hole by
spying ``DispatchModel.apply_cross_year_basis`` on a short warm run
(``attempts=3 installed=3`` warm vs ``attempts=0`` cold); this script is that
check, parameterized by ISO so the five capacity-market ISOs can each be
confirmed before their guardrail verdict is quoted.

Usage::

    MARKET_SIM_HIGHS_THREADS=1 python scripts/probes/_d9_warmstart_spy.py \\
        --iso MISO --start-year 2026 --end-year 2029 --hours 168
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.model.dispatch import DispatchModel  # noqa: E402

from scripts.run_full_horizon import reference_config, solve_and_summarize  # noqa: E402


def spy(iso: str, start_year: int, end_year: int, hours: int, out_dir: Path) -> dict:
    """Run one warm and one cold arm, counting basis installs in each."""
    counts: dict[str, dict[str, int]] = {}
    original = DispatchModel.apply_cross_year_basis

    def make_counter(arm: str):
        def counted(self, prev):  # noqa: ANN001 - mirrors the wrapped signature
            counts[arm]["attempts"] += 1
            installed = original(self, prev)
            if installed:
                counts[arm]["installed"] += 1
            return installed

        return counted

    results: dict[str, dict] = {}
    for arm in ("cold", "warm"):
        counts[arm] = {"attempts": 0, "installed": 0}
        DispatchModel.apply_cross_year_basis = make_counter(arm)
        try:
            config = reference_config(
                iso, start_year, end_year, cmc=False, golden_posture=True
            ).with_overrides(
                forecast_xyear_warmstart=(arm == "warm"),
                **({} if hours == 8760 else {"hours": hours}),
            )
            solve_and_summarize(
                config, iso, out_dir / arm, redirect_cache=True,
                extra_summary={"d9_spy_arm": arm},
            )
        finally:
            DispatchModel.apply_cross_year_basis = original
        results[arm] = dict(counts[arm])
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--end-year", type=int, default=2029)
    ap.add_argument("--hours", type=int, default=168)
    ap.add_argument("--out-dir", type=Path, default=Path("results/d9-ab/spy"))
    args = ap.parse_args(argv)
    iso = args.iso.upper()
    out = spy(iso, args.start_year, args.end_year, args.hours, args.out_dir / iso.lower())
    payload = {"iso": iso, "years": [args.start_year, args.end_year], **out}
    print(json.dumps(payload, indent=2))
    ok = out["warm"]["installed"] > 0 and out["cold"]["attempts"] == 0
    print(f"===== warm start live: {ok} =====")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
