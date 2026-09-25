#!/usr/bin/env python3
"""Re-base the ``neiso-t3`` FC-5 disposition table onto the capx D96 ``base`` leg.

capx D96 measurement record (not standing tooling). The MECHANICAL half reuses
capx D92's validated instruments unchanged: ``docs/handoffs/d92/
corridor_model_values.py`` (54/54 against the table's own declared bundle)
through ``rebase_disposition.classify``. Divergences are taken from the
4-dp-rounded model value, which is the table's own convention (54/54 at HEAD;
the raw value moves one row, ``generation:oil@2040``, by 0.4 pt).

The AUTHORED half is the smallest edit that keeps every explanation true of
the new bundle: a quoted CURRENT figure is replaced by the new bundle's figure
(each replacement below is an exact old->new string pair that must match once,
so a stale quote cannot survive silently), historical transitions (the D92
re-base's "A -> B" statements) are left as the history they are, and every
touched row gets one appended D96 sentence. No verdict is changed by hand;
a row whose class changes is emitted ``NEEDS AUTHORING`` and the script
refuses to write (PRECOMMIT-capx-d96-2026-09-25.md §4.3 / §5).

Usage::

    python3 docs/handoffs/d96/rebase_fc5_d96.py <bundle dir> <out json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "d92"))
from rebase_disposition import DIVERGENCE_PCT_THRESHOLD, classify  # noqa: E402

TABLE = Path("results/ff-corridor/dispositions/neiso-t3.json")


def _quotes(summary: dict) -> dict:
    """Bundle figures the explanations quote, keyed by year."""
    t = {r["year"]: r for r in summary["trajectory"]}
    out = {}
    for y in (2030, 2035, 2040):
        c, g = t[y]["capacity_by_fuel_mw"], t[y]["generation_by_fuel_mwh"]
        out[y] = {
            "ccs_mw": c.get("gas_cc_ccs", 0.0),
            "cc_mw": c.get("gas_cc", 0.0),
            "ccs_twh": g.get("gas_cc_ccs", 0.0) / 1e6,
            "gas_twh": sum(v for k, v in g.items() if k.startswith("gas")) / 1e6,
            "cc_twh": (g.get("gas_cc", 0.0) + g.get("gas_cc_ccs", 0.0)) / 1e6,
            "import_twh": g.get("import", 0.0) / 1e6,
            "co2": t[y]["co2_mt"],
        }
    return out


def _mw(x: float) -> str:
    return f"{x:,.1f}"


def _replace_once(text: str, old: str, new: str, row: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{row}: expected exactly one {old!r}, found {n}")
    return text.replace(old, new)


def author(rows: list[dict], recs: dict, q: dict) -> None:
    """Apply the D96 quote refresh + one appended sentence to each touched row."""
    div = {k: v["new_divergence_pct"] for k, v in recs.items()}
    old = {k: v["old_divergence_pct"] for k, v in recs.items()}
    stamp = "capx D96 (2026-09-25, owner ruling Q69) re-based this row onto the post-F1 bundle (eGRID-2024 heat rates)"
    q30, q35, q40 = q[2030], q[2035], q[2040]
    cc40 = q40["ccs_mw"] + q40["cc_mw"]
    pairs = {
        ("co2", 2030): [
            ("6,648.3 MW gas_cc_ccs beside 4,678.6 MW", f"{_mw(q30['ccs_mw'])} MW gas_cc_ccs beside {_mw(q30['cc_mw'])} MW"),
            ("now LOWER (-25.0 %)", f"now LOWER ({div[('co2', 2030)]:+.1f} %)".replace("+-", "-")),
            ("20.454 TWh of the 34.044 TWh", f"{q30['ccs_twh']:.3f} TWh of the {q30['gas_twh']:.3f} TWh"),
            ("(generation:renewables row, -41.0 %)", f"(generation:renewables row, {div[('generation:renewables', 2030)]:.1f} %)"),
        ],
        ("generation:gas", 2030): [
            ("(20.454 TWh of the 34.044 TWh", f"({q30['ccs_twh']:.3f} TWh of the {q30['gas_twh']:.3f} TWh"),
        ],
        ("co2", 2035): [
            ("21.338 TWh of the model's 28.432 TWh", f"{q35['ccs_twh']:.3f} TWh of the model's {q35['gas_twh']:.3f} TWh"),
            ("the model sits 57.0 % below", f"the model sits {abs(div[('co2', 2035)]):.1f} % below"),
        ],
        ("co2", 2040): [
            ("4,522.0 MW gas_cc_ccs beside 5,678.6 MW unabated gas_cc -- 44 % abated",
             f"{_mw(q40['ccs_mw'])} MW gas_cc_ccs beside {_mw(q40['cc_mw'])} MW unabated gas_cc -- {round(100 * q40['ccs_mw'] / cc40):d} % abated"),
            ("lands at 4.21 Mt", f"lands at {q40['co2']:.2f} Mt"),
            ("(20.691 of the 26.731 TWh CC total)", f"({q40['ccs_twh']:.3f} of the {q40['cc_twh']:.3f} TWh CC total)"),
        ],
        ("capacity:gas_cc", 2040): [
            ("10,200.6 MW -- 5,678.6 unabated + 4,522.0 abated",
             f"{_mw(cc40)} MW -- {_mw(q40['cc_mw'])} unabated + {_mw(q40['ccs_mw'])} abated"),
        ],
        ("generation:total", 2040): [
            ("imports 30.525 TWh", f"imports {q40['import_twh']:.3f} TWh"),
            ("its CC fleet 20.2 % short", f"its CC fleet {abs(div[('capacity:gas_cc', 2040)]):.1f} % short"),
            ("at -15.3 %, by 0.3 points", f"at {div[('generation:total', 2040)]:.1f} %, by {abs(div[('generation:total', 2040)]) - DIVERGENCE_PCT_THRESHOLD:.1f} points"),
        ],
    }
    for r in rows:
        key = (r["quantity"], r["target_year"])
        if key not in pairs:
            continue
        name = f"{key[0]}@{key[1]}"
        text = r["explanation"]
        for a, b in pairs[key]:
            text = _replace_once(text, a, b, name)
        text += (
            f" {stamp}: divergence {old[key]:+.1f} % -> {div[key]:+.1f} %, quoted figures refreshed;"
            " the mechanism is unchanged."
        )
        r["explanation"] = text


def main(argv: list[str]) -> int:
    bundle, out = Path(argv[1]), Path(argv[2])
    summary = json.loads((bundle / "full_horizon_summary.json").read_text())
    run_config = json.loads((bundle / "run_config.json").read_text())
    table = json.loads(TABLE.read_text())
    ps = float(table["model_source"].get("storage_ps_residual_gw") or 0.0)
    recs_list = classify(table["rows"], summary, ps)
    need = [r for r in recs_list if r["action"] != "carry"]
    if need:
        for r in need:
            print(f"NEEDS AUTHORING: {r['quantity']}@{r['target_year']} {r['action']}")
        return 2
    recs = {}
    for r, rec in zip(table["rows"], recs_list):
        mv = rec["new_model_value"]
        a = r["anchor_value"]
        rec["new_divergence_pct"] = None if a in (None, 0) else round((mv - float(a)) / float(a) * 100.0, 1)
        recs[(r["quantity"], r["target_year"])] = rec
    author(table["rows"], recs, _quotes(summary))
    for r in table["rows"]:
        rec = recs[(r["quantity"], r["target_year"])]
        r["model_value"] = rec["new_model_value"]
        r["divergence_pct"] = rec["new_divergence_pct"]
    rel = bundle.as_posix()
    table["model_source"].update(
        {
            "summary": f"{rel}/full_horizon_summary.json",
            "run_config": f"{rel}/run_config.json",
            "cache_key": run_config["cache_key"],
            "note": (
                "capx D96 leg `base` -- the golden recipe the neiso-t3 verdict names "
                "(ccs_retrofit_vom_adder=8.0, ccs_retrofit_fixed_cost_co2_scaling=false, --golden-posture), "
                f"re-solved at {run_config['git']['sha']} on post-F1 data (eGRID-2024 heat rates), so the "
                "primary bundle, the FC-6 paired arms, this table and the FC-6 driver battery (capx D94) "
                "sit on one data vintage. Evidence: docs/handoffs/FINDING-capx-d96-2026-09-25.md."
            ),
        }
    )
    n_div = sum(r["verdict"] == "EXPLAINED DIVERGENCE" for r in table["rows"])
    table["counts"] = {
        "in_corridor": len(table["rows"]) - n_div,
        "explained": n_div,
        "unexplained": 0,
        "total": len(table["rows"]),
    }
    table["authored_by"] = (
        "capx D96, 2026-09-25 (owner ruling Q69) -- RE-BASED onto the post-F1 capx D96 `base` leg, "
        "so the whole neiso-t3 verdict sits on one data vintage. The prior table (capx D92, keyed to "
        "results/ff-t3-neiso-golden/d92/base, cache_key dd8203a8bf1546b9, pre-F1) is preserved byte-equal "
        "at dispositions/neiso-t3-pre-d96.json. Every model_value / divergence_pct is recomputed "
        "MECHANICALLY by capx D92's validated instruments (docs/handoffs/d92/corridor_model_values.py, "
        "54/54 at HEAD); anchors are UNTOUCHED (rule 13 [R-MEASURED]). No row changed class. Explanations "
        "are touched only where they quote a figure of the bundle: co2@2030, co2@2035, co2@2040, "
        "generation:gas@2030, capacity:gas_cc@2040, generation:total@2040 -- each quoted current figure "
        "refreshed, D92's historical transitions left as history, one D96 sentence appended. Prior "
        "authorship: capx D92 (2026-09-10, owner ruling Q65), preserved in the -pre-d96 file. Script: "
        "docs/handoffs/d96/rebase_fc5_d96.py. Evidence: docs/handoffs/FINDING-capx-d96-2026-09-25.md."
    )
    out.write_text(json.dumps(table, indent=1) + "\n")
    print(f"wrote {out}: {table['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
