"""FFR-7A: the complete per-row delta between the old and corrected actuals targets.

Emits ``docs/handoffs/ffr-7a/target-delta.csv`` — every retirement row the
physical-exit dating rule (owner decision D-21(b),
``scripts/data/build_capacity_actuals.py``) added, dropped or re-dated, per
ISO, each carrying the EIA-860 evidence that produced the change: the unit's
``Status`` series across the committed release series and the reported
``Retirement Year`` the old builder used.

The "before" side is read out of git (``<base>:data/raw/_validation-source/
capacity_actuals_<iso>.csv``) so the artifact regenerates from the repo alone,
with no snapshot to keep by hand.

Read-only; never solves. Usage::

    uv run python scripts/probes/ffr7a_target_delta.py [--base origin/main]
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (_ROOT / "src", _ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.data.fleet import BA_CODE_TO_ISO  # noqa: E402
from scripts.data import build_capacity_actuals as bca  # noqa: E402

ISOS = ("ERCOT", "PJM", "MISO", "NYISO", "NEISO")
OUT = _ROOT / "docs" / "handoffs" / "ffr-7a" / "target-delta.csv"
TARGET = "data/raw/_validation-source/capacity_actuals_{iso}.csv"


def old_target(iso: str, base: str) -> pd.DataFrame:
    """The committed pre-FFR-7A target for ``iso``, read out of git at ``base``."""
    blob = subprocess.run(
        ["git", "show", f"{base}:{TARGET.format(iso=iso.lower())}"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return pd.read_csv(io.StringIO(blob), comment="#")


def evidence(iso: str) -> dict[str, dict[str, object]]:
    """Per-unit ``{status history, reported retirement year}`` from EIA-860."""
    bas = {ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}
    hist = bca.load_release_history(bas)
    out: dict[str, dict[str, object]] = {}
    for (plant_id, generator_id), grp in hist.groupby(
        ["plant_id", "generator_id"], sort=False
    ):
        grp = grp.sort_values("release_year")
        reported = grp["retirement_year"].dropna()
        out[bca._uid(int(plant_id), generator_id)] = {
            "eia860_status_series": ";".join(
                f"{r.release_year}:{r.status}" for r in grp.itertuples()
            ),
            "eia860_reported_retirement_year": (
                int(reported.iloc[-1]) if len(reported) else ""
            ),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/main", help="git ref for the old CSVs")
    args = parser.parse_args(argv)

    rows: list[dict] = []
    for iso in ISOS:
        old = old_target(iso, args.base)
        new = pd.read_csv(_ROOT / TARGET.format(iso=iso.lower()), comment="#")
        o = old[old["kind"] == "retirement"].set_index("unit_id")
        n = new[new["kind"] == "retirement"].set_index("unit_id")
        ev = evidence(iso)
        for uid in sorted(set(o.index) | set(n.index)):
            in_old, in_new = uid in o.index, uid in n.index
            old_year = int(o.loc[uid, "year"]) if in_old else None
            new_year = int(n.loc[uid, "year"]) if in_new else None
            if in_old and in_new and old_year == new_year:
                continue
            src = n.loc[uid] if in_new else o.loc[uid]
            rows.append(
                {
                    "iso": iso,
                    "change": "added"
                    if not in_old
                    else ("dropped" if not in_new else "re-dated"),
                    "unit_id": uid,
                    "plant_id": int(src["plant_id"]),
                    "fuel": src["fuel"],
                    "mw": float(src["mw"]),
                    "old_year": "" if old_year is None else old_year,
                    "new_year": "" if new_year is None else new_year,
                    **ev.get(
                        uid,
                        {
                            "eia860_status_series": "(gap-fix override row)",
                            "eia860_reported_retirement_year": "",
                        },
                    ),
                }
            )

    df = pd.DataFrame(rows).sort_values(
        ["iso", "change", "mw"], ascending=[True, True, False]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT} — {len(df)} changed rows")
    print(
        df.groupby(["iso", "change"])
        .agg(rows=("unit_id", "size"), mw=("mw", "sum"))
        .round(1)
        .to_string()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
