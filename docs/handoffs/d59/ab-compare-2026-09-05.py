"""capx D59 A/B instrument (ZERO solves): the locality half measured on the record.

    uv run python docs/handoffs/d59/ab-compare-2026-09-05.py

Reads three committed bundles — the D52 curve-ON probe (``nyiso-2021-2025-realized-t1h-
d52-curveon``, key 589f031432b6dc7d, solved at the D52 HEAD), the D59 CONTROL replay of the
same recipe at the D59 HEAD (``…-d59-control``, key ab3bc307278251ae, the field OFF) and
the D59 ARM (``…-d59-locality``, key 3ea2a186cdeddfa6, the field ON) — and prints, per
scored year: (1) the arm's ``locality_capacity`` ledger block (census / requirement /
position / locality price / NYCA price / settled price) beside the pre-declared values
(DESIGN §8.2) and the published margins / spot prices (§2.5); (2) the retirement rows by
zone × fuel × reason for the three legs; (3) the FC-3 score rows (retire total / per-fuel /
false-retire / recall / additions / LOYO / T-R10) for the three legs; (4) the control-vs-D52
byte-identity check (every score row and every ledger field outside the D59 block — a
difference there is upstream drift, never this lane's); (5) the P9 (a)/(b)/(c) grade on
the arm. Rows + stdout are committed beside this file. Nothing here is a fit target.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNS = {
    "d52": REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d52-curveon",
    "control": REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d59-control",
    "arm": REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d59-locality",
}
PREDECL = json.loads((Path(__file__).parent / "locality-predecl-2026-09-05.json").read_text())
PUB = {
    (2023, "NYC"): (1.026, 191.6), (2023, "LI"): (1.131, 49.3),
    (2024, "NYC"): (1.057, 141.1), (2024, "LI"): (1.117, 43.2),
    (2025, "NYC"): (1.078, 131.8), (2025, "LI"): (1.122, 51.4),
}
PUB_NYCA_POS = {2023: 1.043, 2024: 1.058, 2025: 1.035}  # 2025 = the implied reading (DESIGN §6)
ZONE_RE = re.compile(r"_(Upstate_West|Capital_Hudson|Lower_Hudson|NYC|Long_Island)_")


def bundle(run: Path) -> Path:
    meta = json.loads((run / "meta.json").read_text())
    return REPO / meta["bundle"]


def load(run: Path):
    b = bundle(run)
    leds = {y: json.loads((b / f"evolution_{y}.json").read_text()) for y in (2021, 2022, 2023, 2024, 2025)}
    score = json.loads((b / "score.json").read_text())
    return b, leds, score


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def retire_rows(led):
    agg = defaultdict(float)
    for r in led.get("retirements") or []:
        m = ZONE_RE.search(r["unit_id"])
        agg[(m.group(1) if m else "?", r["fuel"], r["reason"])] += r["mw"]
    return {f"{z}/{f}/{why}": round(mw, 1) for (z, f, why), mw in sorted(agg.items())}


def fc3(score):
    f = flatten(score)
    keys = [k for k in f if k.startswith(("retirements.total_gw", "retirements.per_fuel", "retirements.false_retire", "retirements.unit_recall_gt300.recall", "additions.by_tech", "loyo.folds", "tr10.tr10", "tr10.first_mover", "blk10"))]
    return {k: f[k] for k in sorted(keys) if not isinstance(f[k], (list,))}


def main() -> None:
    data = {}
    for name, run in RUNS.items():
        if not (run / "meta.json").exists():
            print(f"{name}: MISSING ({run})")
            continue
        data[name] = load(run)
    out = {"runs": {k: str(bundle(RUNS[k]).relative_to(REPO)) for k in data}}

    # (1) the arm's locality block vs pre-declared vs published
    print("== (1) locality block (ARM) vs pre-declared (DESIGN §8.2) vs published (§2.5)")
    print("year loc | supply  req    | pos     predecl pub   | P_loc   P_NYCA  settled | pub spot | settled/spot")
    loc_rows = []
    for y in (2023, 2024, 2025):
        for row in data["arm"][1][y].get("locality_capacity") or []:
            loc = row["locality"]
            pre = next(r for r in PREDECL["rows"] if r["year"] == y and r["locality"] == ("NYC" if loc == "NYC" else "Long Island"))
            pub_pos, pub_spot = PUB[(y, loc)]
            ratio = row["settled_price_per_kw_yr"] / pub_spot
            loc_rows.append(dict(year=y, **row, predecl_position=pre["position"], published_position=pub_pos, published_spot_kw_yr=pub_spot, settled_over_spot=round(ratio, 3), gap_pts=round((row["position"] - pub_pos) * 100, 1)))
            print(f"{y} {loc:<4}| {row['supply_icap_mw']:7.0f} {row['requirement_icap_mw']:6.0f} | {row['position']:.4f} {pre['position']:.4f} {pub_pos:.3f} | {str(row['price_per_kw_yr']):>7} {row['nyca_price_per_kw_yr']:7.2f} {row['settled_price_per_kw_yr']:7.2f} | {pub_spot:8.1f} | {ratio:.2f}")
    out["locality_rows"] = loc_rows
    for y in (2023, 2024, 2025):
        print(f"  {y} NYCA seam position: control {data['control'][1][y].get('screen_reserve_position')} arm {data['arm'][1][y].get('screen_reserve_position')} d52 {data['d52'][1][y].get('screen_reserve_position')} published {PUB_NYCA_POS[y]}")

    # (2) retirement rows
    print("== (2) retirement rows by zone/fuel/reason")
    out["retirements"] = {}
    for y in (2022, 2023, 2024, 2025):
        out["retirements"][y] = {k: retire_rows(v[1][y]) for k, v in data.items()}
        print(y, json.dumps(out["retirements"][y]))
    print("thermal additions:", {k: {y: v[1][y].get("thermal_additions") for y in (2023, 2024, 2025)} for k, v in data.items()})
    print("entry decided:", {k: {y: v[1][y].get("entry_decided_mw_by_tech") for y in (2023, 2024, 2025)} for k, v in data.items()})

    # (3) FC-3 rows
    print("== (3) FC-3 rows")
    rows = {k: fc3(v[2]) for k, v in data.items()}
    keys = sorted(set().union(*[set(r) for r in rows.values()]))
    out["fc3"] = {k: {kk: rows[k].get(kk) for kk in keys} for k in rows}
    for kk in keys:
        vals = [rows[k].get(kk) for k in data]
        flag = "" if len({json.dumps(v) for v in vals}) == 1 else "  <-- differs"
        print(f"  {kk:60s} " + "  ".join(f"{k}={rows[k].get(kk)}" for k in data) + flag)

    # (4) control vs d52 byte-identity (score + ledger)
    print("== (4) control (D59 HEAD, field OFF) vs D52 curve-ON (D52 HEAD): differences")
    diffs = []
    if "control" in data and "d52" in data:
        fa, fb = flatten(data["control"][2]), flatten(data["d52"][2])
        for k in sorted(set(fa) | set(fb)):
            if k.startswith("flip_gate_extras.utc"):
                continue
            if fa.get(k) != fb.get(k):
                diffs.append(("score", k, fb.get(k), fa.get(k)))
        for y in (2021, 2022, 2023, 2024, 2025):
            la, lb = data["control"][1][y], data["d52"][1][y]
            for k in sorted(set(la) | set(lb)):
                if k in ("locality_capacity", "entry_screen_diagnostics"):
                    continue
                if json.dumps(la.get(k), sort_keys=True) != json.dumps(lb.get(k), sort_keys=True):
                    diffs.append((f"ledger_{y}", k, lb.get(k), la.get(k)))
        print(f"  {len(diffs)} difference(s)")
        for d in diffs[:60]:
            print("  ", d[0], d[1], "d52=", str(d[2])[:80], "control=", str(d[3])[:80])
    out["control_vs_d52_diffs"] = [list(map(str, d)) for d in diffs]

    # (4b) arm vs control: which score rows moved
    print("== (4b) arm vs control: score rows that moved")
    fa, fc = flatten(data["arm"][2]), flatten(data["control"][2])
    moved = [(k, fc.get(k), fa.get(k)) for k in sorted(set(fa) | set(fc)) if fa.get(k) != fc.get(k) and not k.startswith("flip_gate_extras.utc")]
    for m in moved:
        print("  ", m[0], "control=", str(m[1])[:60], "arm=", str(m[2])[:60])
    out["arm_vs_control_moved"] = [list(map(str, m)) for m in moved]

    # (5) P9 grade on the arm
    s = data["arm"][2]
    tot = s["retirements"]["total_gw"]
    fr = s["retirements"]["false_retire"]
    pos_ok = all(abs(data["arm"][1][y]["screen_reserve_position"] - PUB_NYCA_POS[y]) <= 0.03 for y in (2023, 2024, 2025))
    p9 = {"a_total_within_10pct": abs(tot["err_frac"]) <= 0.10, "a_err_frac": tot["err_frac"], "b_false_retire_in_band": fr["band"] == "PASS", "b_frac": fr["frac_of_model"], "c_positions_within_3pts": pos_ok}
    out["p9"] = p9
    print("== (5) P9:", json.dumps(p9))
    (Path(__file__).with_suffix(".json")).write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
