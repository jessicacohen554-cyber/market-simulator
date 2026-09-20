"""Derive per-plant coal take-or-pay (contract vs spot) share for an ISO from
EIA-923 Schedule 5.

The dispatch model treats a coal plant's must-run tranche as fully **sunk**
(``campd_tranche_fuel_frac`` returns ``0.0`` for ``_mustrun`` coal → it bids
VOM + carbon + NOx only, no fuel). That is the take-or-pay assumption: contracted
tonnage is must-burn, so its fuel cost is unavoidable on a dispatch-hour basis and
should not price the unit out of merit when gas is cheap. But "100% of the floor
is sunk" is an *assumption*, not a measurement — it is the physically-honest input
the calibrated 0.76 gas-keyed discount stands in for (see
``docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md``, Thread B/D).

EIA-923 Schedule 5 (Page 5, Fuel Receipts and Costs) records a **Purchase Type**
for every fuel receipt, so the contracted vs spot split is *observable* and
forward-reproducible (CLAUDE.md #11). Per the EIA-923 instructions the codes are:

    C   contract  — term ≥ 1 year (the take-or-pay / must-burn tonnage)
    NC  new contract — term ≥ 1 year, began in the reporting year
    S   spot      — spot-market purchase (avoidable)
    T   tolling   — fuel supplied under a tolling agreement (firm; rare for coal)

This reads the ``f923_*.zip`` releases, sums each coal plant's **coal** receipts
by Purchase Type (by delivered tons), and writes the contracted (sunk) share
``contract_share = (C + NC + T) / total`` to
``data/raw/_processed-legacy/coal_takeorpay_<ISO>.csv`` (one row per coal plant).
:func:`market_sim.data.fleet.coal_takeorpay_share` loads it; when
``ScenarioConfig.coal_takeorpay_from_data`` is set, the coal must-run tranche's
sunk fraction becomes this measured share (``fuel_frac = 1 - contract_share``)
instead of the hardcoded ``0.0`` — so the spot remainder bids full delivered
fuel and the contracted base stays sunk, both grounded in the receipt data.

Usage:
    python scripts/data/derive_coal_takeorpay.py --iso PJM
    python scripts/data/derive_coal_takeorpay.py --iso PJM --year 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.data.process_f923_fuel_costs import (  # noqa: E402
    _RENAME,
    _find_zips,
    _load_receipts,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_coal_takeorpay")

# EIA-923 Schedule-5 Purchase Type codes grouped into the model's sunk
# (take-or-pay / firm commitment) vs avoidable (spot) buckets. Contract (C),
# new contract (NC) and tolling (T) are firm obligations whose fuel is
# must-burn; spot (S) is the avoidable, price-responsive remainder.
_CONTRACT_CODES: frozenset[str] = frozenset({"C", "NC", "T"})
_SPOT_CODES: frozenset[str] = frozenset({"S"})


#: The committed EIA-923 Page-5 receipts corpus (``fetch_eia923_coal_receipts.py``),
#: one ``coal_receipts_<year>.csv`` per release year. It carries the SAME Page-5
#: columns the ``f923_*.zip`` releases do, ``Purchase Type`` included, and it is
#: TRACKED — the zips are not committed to the repo (see ``_takeorpay_table``).
#: That is the whole reason this source exists: an ISO whose table has never been
#: derived can be derived from what is already in the tree, with no re-fetch.
#: Discovered by lane NWPP-43 (2026-09-20), which found ``coal_takeorpay_NWPP.csv``
#: absent while the file exists for all seven other ISOs — so
#: ``coal_takeorpay_from_data`` and ``coal_committed_takeorpay_regulated`` were
#: silently INERT for NWPP (``campd_tranche_fuel_frac`` needs the plant in
#: ``takeorpay_by_plant``). The NWPP-41 defect class: an underived artifact making
#: a real mechanism do nothing.
_RECEIPTS_CORPUS = "coal-receipts"


def _load_receipts_corpus(raw_dir: Path, years: list[int] | None) -> list[pd.DataFrame]:
    """Return Page-5 receipt frames from the committed coal-receipts corpus.

    Column-for-column equivalent to :func:`_load_receipts` over a ``f923_*.zip``:
    the same ``_RENAME`` map is applied, so every downstream column name
    (``plant_id`` / ``quantity`` / ``fuel_group`` / ``purchase_type``) is
    identical and :func:`_takeorpay_table` cannot tell the two sources apart.
    The corpus is coal-only by construction (the fetch filters
    ``FUEL_GROUP == "Coal"``), which is a subset of what this deriver keeps
    anyway.

    Args:
        raw_dir: The ``data/raw`` root holding ``coal-receipts/``.
        years: Restrict to these release years; ``None`` takes every year present.

    Returns:
        One frame per matching release year, renamed to the canonical columns.
    """
    corpus = raw_dir / _RECEIPTS_CORPUS
    paths = sorted(corpus.glob("coal_receipts_*.csv"))
    if not paths:
        raise SystemExit(
            f"No coal_receipts_*.csv found in {corpus} — fetch the corpus with "
            "scripts/data/fetch_eia923_coal_receipts.py, or drop "
            "--from-receipts-corpus to read the f923_*.zip releases instead."
        )
    frames = []
    for path in paths:
        m = re.search(r"(\d{4})", path.stem)
        yr = int(m.group(1)) if m else 0
        if years is not None and yr not in years:
            continue
        raw = pd.read_csv(path)
        keep = [c for c in _RENAME if c in raw.columns]
        frames.append(raw[keep].rename(columns=_RENAME))
    if not frames:
        raise SystemExit(
            f"coal-receipts corpus holds no release year in {years} (found "
            f"{[p.stem for p in paths]})."
        )
    return frames


def _takeorpay_table(
    iso: str,
    years: list[int] | None,
    raw_dir: Path | None = None,
    from_receipts_corpus: bool = False,
) -> pd.DataFrame:
    """Return ``[plant_code, contract_share, spot_share, total_tons, n_receipts,
    source, breakdown]`` — one row per coal plant in ``iso`` with coal receipts.

    ``contract_share`` is the take-or-pay (sunk) fraction of delivered tonnage:
    ``(C + NC + T) / total``. Plants that report no Purchase Type on any coal
    receipt are omitted (the loader's ``None`` → the model keeps its default
    100%-sunk must-run behaviour for those plants).
    """
    iso_config = get_iso_config(iso)
    coal_codes = {
        int(g.plant_code)
        for g in load_fleet_from_csv(iso, iso_config)
        if g.fuel_type == "coal" and int(g.plant_code) > 0
    }
    logger.info("%s EIA-860 fleet has %d coal plants", iso, len(coal_codes))

    rframes = []
    # Raw f923_*.zip releases: data/raw since the W1 layout collapse (the
    # pre-W1 inputs/raw-data root no longer exists). The zips are immutable
    # EIA downloads (https://www.eia.gov/electricity/data/eia923/), not
    # committed to the repo — re-download the cited vintages to re-derive.
    _root = raw_dir if raw_dir is not None else RAW_DATA_DIR
    if from_receipts_corpus:
        # Same Page 5, same columns, same construction — a committed source
        # instead of an uncommitted one (see _load_receipts_corpus).
        rframes.extend(_load_receipts_corpus(_root, years))
    else:
        for zip_path in _find_zips(_root):
            m = re.search(r"f923[_-]?(\d{4})", zip_path.stem)
            yr = int(m.group(1)) if m else 0
            if years is not None and yr not in years:
                continue
            rframes.append(_load_receipts(zip_path))

    receipts = pd.concat(rframes, ignore_index=True)
    if "purchase_type" not in receipts.columns:
        raise SystemExit(
            "EIA-923 receipts carry no Purchase Type column — re-run after "
            "extending process_f923_fuel_costs._RENAME, or the workbook layout "
            "changed (check Page 5 header names)."
        )
    receipts["plant_id"] = pd.to_numeric(receipts["plant_id"], errors="coerce")
    receipts["quantity"] = pd.to_numeric(receipts["quantity"], errors="coerce").fillna(
        0.0
    )
    receipts = receipts.dropna(subset=["plant_id"])
    receipts["plant_id"] = receipts["plant_id"].astype(int)
    coal = receipts[
        (receipts["fuel_group"] == "Coal")
        & (receipts["plant_id"].isin(coal_codes))
        & (receipts["quantity"] > 0)
    ].copy()
    coal["pt"] = coal["purchase_type"].astype(str).str.strip().str.upper()

    rows = []
    for code, grp in coal.groupby("plant_id"):
        by_pt = grp.groupby("pt")["quantity"].sum()
        total = float(by_pt.sum())
        if total <= 0:
            continue
        contract = float(by_pt.reindex(list(_CONTRACT_CODES)).fillna(0.0).sum())
        spot = float(by_pt.reindex(list(_SPOT_CODES)).fillna(0.0).sum())
        # Receipts with an unrecognised / blank Purchase Type are excluded from
        # both buckets but kept in the denominator only if they are codes we
        # know; renormalise the share over the classified tonnage so a plant
        # that filed a few blank rows is not spuriously diluted.
        classified = contract + spot
        if classified <= 0:
            continue
        rows.append(
            {
                "plant_code": int(code),
                "contract_share": round(contract / classified, 4),
                "spot_share": round(spot / classified, 4),
                "total_tons": round(total, 1),
                "n_receipts": int(len(grp)),
                "source": "receipts",
                "breakdown": ";".join(
                    f"{k}:{v / total:.0%}"
                    for k, v in by_pt.sort_values(ascending=False).items()
                ),
            }
        )

    cols = [
        "plant_code",
        "contract_share",
        "spot_share",
        "total_tons",
        "n_receipts",
        "source",
        "breakdown",
    ]
    if not rows:
        logger.info("%s: no coal plants with classifiable Purchase Type", iso)
        return pd.DataFrame(columns=cols)
    out = pd.DataFrame(rows).sort_values("plant_code").reset_index(drop=True)
    missing = sorted(coal_codes - set(out["plant_code"]))
    if missing:
        logger.info(
            "%d %s coal plants had no classifiable coal Purchase Type "
            "(kept default 100%%-sunk must-run): %s",
            len(missing),
            iso,
            missing,
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive per-plant coal take-or-pay (contract) share from EIA-923."
    )
    parser.add_argument("--iso", required=True, help="ISO (e.g. PJM).")
    parser.add_argument(
        "--year",
        type=int,
        nargs="*",
        default=None,
        help="Restrict to these EIA-923 release years (default: all).",
    )
    parser.add_argument("--out-dir", default="data/raw/_processed-legacy")
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Directory holding the f923_*.zip releases (default: data/raw).",
    )
    parser.add_argument(
        "--from-receipts-corpus",
        action="store_true",
        help=(
            "Read the COMMITTED data/raw/coal-receipts/ corpus instead of the "
            "uncommitted f923_*.zip releases. Same Page 5, same columns, same "
            "construction — use it when the zips are not on disk."
        ),
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    table = _takeorpay_table(
        args.iso.upper(),
        args.year,
        raw_dir=raw_dir,
        from_receipts_corpus=args.from_receipts_corpus,
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"coal_takeorpay_{args.iso.upper()}.csv"
    table.to_csv(out_path, index=False)

    if not table.empty:
        logger.info(
            "wrote %s: %d plants — contract share mean %.0f%%, range %.0f-%.0f%%",
            out_path,
            len(table),
            100 * table["contract_share"].mean(),
            100 * table["contract_share"].min(),
            100 * table["contract_share"].max(),
        )
    else:
        logger.warning("wrote %s: no plants classified", out_path)


if __name__ == "__main__":
    main()
