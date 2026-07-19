"""WP-3: column-merge ``steam_level_cf`` into the committed CAISO tranche artifact.

Owner-ruled 2026-07-19 at scope (a)+(b)
(`docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md`): the CT_CHP
steam-floor LEVEL statistic re-derives per rule 23 — the loading-when-on
construction for CAMPD-visible cogens (a) and the EIA-923 delivery-implied
level for CEMS-invisible cogens (b), both emitted as ``steam_level_cf`` by the
revised `scripts/data/derive_thermal_tranches.py`.

This merge follows the caiso-89 precedent (commit 75578e4): a FULL regen of
the committed `thermal_tranches_CAISO.csv` drifts on layers outside this
ruling's scope (nameplate reconciliation, `_ONLINE_FRAC_GROUPS` expansion,
shares-window provenance — loader-code drift, not source-data change, so
committed columns stay per rule 23). Instead the fresh pooled 2023-2025
derivation is written to a scratch path and ONLY the new ``steam_level_cf``
column is merged into the committed artifact, keyed on
``(plant_code, plant_group)``, for rows whose status is ``ok`` or
``eia923_cf`` in BOTH files. Row membership and every other committed column
are preserved byte-for-byte (the superseded ``p25_allhr_cf`` column is
dropped — rule 26, a superseded statistic does not stay parseable alongside
its replacement).

Usage:
    python scripts/probes/_caiso101_wp3_merge_steam_level.py <fresh_scratch_csv>
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
COMMITTED = REPO / "data" / "raw" / "_processed-legacy" / "thermal_tranches_CAISO.csv"
_CHP_GROUPS = {"CC_CHP", "CT_CHP", "ST_CHP"}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: _caiso101_wp3_merge_steam_level.py <fresh_scratch_csv>")
    fresh = pd.read_csv(sys.argv[1])
    committed = pd.read_csv(COMMITTED)

    levels: dict[tuple[int, str], float] = {}
    for r in fresh.itertuples(index=False):
        if str(getattr(r, "status", "")) not in ("ok", "eia923_cf"):
            continue
        if str(r.plant_group) not in _CHP_GROUPS:
            continue
        lvl = getattr(r, "steam_level_cf", float("nan"))
        try:
            lvl = float(lvl)
        except (TypeError, ValueError):
            continue
        if lvl == lvl:  # not NaN
            levels[(int(r.plant_code), str(r.plant_group))] = lvl

    def _lookup(row: pd.Series) -> float:
        if str(row.get("status", "")) not in ("ok", "eia923_cf"):
            return float("nan")
        if str(row["plant_group"]) not in _CHP_GROUPS:
            return float("nan")
        return levels.get(
            (int(row["plant_code"]), str(row["plant_group"])), float("nan")
        )

    committed["steam_level_cf"] = committed.apply(_lookup, axis=1)
    if "p25_allhr_cf" in committed.columns:
        committed = committed.drop(columns=["p25_allhr_cf"])
    committed.to_csv(COMMITTED, index=False)
    n = committed["steam_level_cf"].notna().sum()
    pos = (committed["steam_level_cf"].fillna(0) > 0).sum()
    print(
        f"merged steam_level_cf into {COMMITTED}: {n} rows with level, {pos} positive"
    )


if __name__ == "__main__":
    main()
