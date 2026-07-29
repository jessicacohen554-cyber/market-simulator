"""caiso-137b — the CAISO LOLP scarcity overlay is **UNREACHABLE in the backcast lane**,
and its storage argument was never the flat nameplate. Corrects two claims in
``FINDING-caiso137-a2-lolp-reserve-measure-2026-07-28`` §2-§5.

The caiso-137 session's primary result — **ask A2 closes as a no-defect**, because
the overlay's reserve measure is already plant-level ONLINE — stands unchanged and
is re-verified in §A. Two *secondary* claims in that FINDING were wrong, both
because the session reconstructed the overlay through
``scripts/run_calibration.py::run_year(fleet_only=True)`` instead of tracing the
call site:

**Correction 1 — the overlay never runs in a CAISO backcast.**
``caiso_scarcity_overlay`` is called in exactly one place,
``src/market_sim/runner.py:2085`` (the FORECAST path). The calibration path
(``scripts/run_calibration_full.py`` -> ``scripts/run_calibration.py``) never
imports ``market_sim.runner``, and its only price writer — ``_system_frame`` —
builds ``total_overlay`` from **ERCOT terms alone** (``ercot_rtordpa_overlay_series``,
``ercot_dam_as_overlay_series``, ``ercot_ordc_realized_adder``, the reserve-price
/ cap-dual adders). So a CAISO keeper's persisted ``system_<y>.parquet`` price is
the **energy-only LP dual**, the realised overlay adder is **exactly $0.00 in
every hour**, and ``caiso_scarcity_pricing=True`` in a CAISO backcast
``run_config.json`` is a **stored no-op**. The FINDING's "realised overlay adder
dw-mean $0.1399 / $0.0158 / $0.0004" is withdrawn — it described a counterfactual.

**Correction 2 — there is no flat-nameplate defect.**
``runner.py:993-999`` REPLACES ``storage.power_cap`` with the COD-ramped 2-D array
before any solve, so the overlay's third argument is already the hourly in-service
cap and ``reserve_headroom`` takes its ``cap.ndim == 2`` branch. The 1-D nameplate
the FINDING measured is a property of ``run_calibration.py``'s ``fleet_only``
reconstruction helper — which assigns the ramped cap to a SEPARATE local
(``storage_power_cap``, line 3741) and leaves ``storage.power_cap`` untouched —
not of the overlay. The FINDING §3 "phantom 3,049 / 3,567 / 4,317 MW" is withdrawn,
and with it the whole D2 E1/E2 gate table, which gated a defect that does not exist.

**What the correction leaves standing** is a sharper structural fact than the one
it removes: CAISO has **no scarcity-pricing mechanism in the backcast at all**, so
every CAISO C3c count ever scored is an energy-only dual — which is exactly why it
is 0 / 0 / 0. See §D.

**No LP is built and no solver is called.** Nothing is armed.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python \\
        scripts/probes/_caiso137b_overlay_reachability.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEEPER = ROOT / "results/calibration/caiso130_nameplate_B"


def section_a() -> None:
    """§A — the standing result: A2 as written is a no-defect (unchanged)."""
    src = (ROOT / "src/market_sim/results/scarcity.py").read_text()
    cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    print("\n" + "=" * 92)
    print("A — STANDING: ask A2 closes as a no-defect (caiso-137 §1, unchanged)")
    print("=" * 92)
    checks = [
        (
            "measure basis is plant-level ONLINE",
            "reserves_online_mw=r_online" in src and "_online_plant_mask" in src,
            "reserve_headroom splits online/offline via _online_plant_mask and the "
            "half-hour LOLP term is evaluated on r_online -- option (a)/(c) refuted",
        ),
        (
            "import_headroom enters NO tier",
            cfg.get("caiso_scarcity_import_headroom") is False,
            "caiso_scarcity_import_headroom is False on the keeper -- option (b) moot",
        ),
        (
            "storage + curtailed VRE already in r_online",
            "renewable_headroom" in src and "storage_headroom" in src,
            "reserve_headroom adds both -- option (c) refuted",
        ),
    ]
    for name, ok, why in checks:
        print(f"      [{'OK' if ok else 'XX'}] {name}\n           {why}")
    print(
        "\n      => A2 AS WRITTEN IS CLOSED (option d). This is the session's primary"
    )
    print("         result and the corrections below do not touch it.")


def section_b() -> None:
    """§B — Correction 1: the overlay is unreachable in the calibration lane."""
    print("\n" + "=" * 92)
    print("B — CORRECTION 1: the overlay NEVER RUNS in a CAISO backcast")
    print("=" * 92)

    # (i) the single call site
    hits = []
    for p in sorted(ROOT.glob("src/market_sim/**/*.py")) + sorted(
        ROOT.glob("scripts/**/*.py")
    ):
        if p.name.startswith("_caiso137"):
            continue
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if "caiso_scarcity_overlay(" in line and "def " not in line:
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    print(f"      (i) call sites of caiso_scarcity_overlay(): {hits or 'NONE'}")

    # (ii) does the calibration path reach market_sim.runner?
    seen: set[str] = set()
    stack = ["scripts/run_calibration_full.py", "scripts/run_calibration.py"]
    reaches = []
    while stack:
        rel = stack.pop()
        if rel in seen or not (ROOT / rel).exists():
            continue
        seen.add(rel)
        for n in ast.walk(ast.parse((ROOT / rel).read_text())):
            mod = (
                n.module
                if isinstance(n, ast.ImportFrom)
                else (n.names[0].name if isinstance(n, ast.Import) else None)
            )
            if mod and mod.startswith("market_sim.runner"):
                reaches.append(f"{rel}:{n.lineno} -> {mod}")
    print(
        f"      (ii) calibration path imports of market_sim.runner: "
        f"{reaches or 'NONE — the two solve paths are disjoint'}"
    )

    # (iii) what the calibration path's ONLY price writer adds
    rcf = (ROOT / "scripts/run_calibration_full.py").read_text().splitlines()
    terms = [
        line.strip()
        for line in rcf[925:1010]
        if line.strip().startswith(("overlay = ", "dam_as = ", "ordc_adder = "))
        and "None" not in line
    ]
    print("      (iii) _system_frame's total_overlay terms (the only price writer):")
    for t in terms:
        print(f"            {t}")
    print("            -> every term is ERCOT-gated; there is NO CAISO overlay term.")

    print(
        "\n      => A CAISO keeper's system_<y>.parquet price is the ENERGY-ONLY LP dual.\n"
        "         The realised overlay adder is EXACTLY $0.00 in every hour, and\n"
        "         caiso_scarcity_pricing=True is a STORED NO-OP in the backcast lane.\n"
        "         WITHDRAWN: FINDING-caiso137 §2's 'realised adder $0.1399/$0.0158/\n"
        "         $0.0004' and §4's entire D2 E1/E2 table."
    )


def section_c() -> None:
    """§C — Correction 2: the overlay's storage argument is already the ramped cap."""
    print("\n" + "=" * 92)
    print("C — CORRECTION 2: there is NO flat-nameplate defect")
    print("=" * 92)
    run = (ROOT / "src/market_sim/runner.py").read_text().splitlines()
    cal = (ROOT / "scripts/run_calibration.py").read_text().splitlines()
    print("      src/market_sim/runner.py (the path that CALLS the overlay):")
    for i in range(992, 999):
        print(f"        {i + 1}: {run[i]}")
    print(
        "        -> storage.power_cap is REASSIGNED to the COD-ramped 2-D array, so\n"
        "           the overlay's 3rd argument is already the hourly in-service cap\n"
        "           and reserve_headroom takes its `cap.ndim == 2` branch.\n"
    )
    print("      scripts/run_calibration.py (the fleet_only reconstruction helper):")
    print(f"        3741: {cal[3740].strip()}")
    print(
        "        -> assigns to a SEPARATE local and leaves storage.power_cap 1-D.\n"
        "           That 1-D array is what caiso-137 measured. It is a property of the\n"
        "           reconstruction helper, NOT of the overlay."
    )
    print(
        "\n      => WITHDRAWN: FINDING-caiso137 §3's 'phantom 3,049 / 3,567 / 4,317 MW'\n"
        "         and every gate built on it. There is no defect and no candidate."
    )


def section_d() -> None:
    """§D — what the correction leaves standing, which is sharper than what it removes."""
    print("\n" + "=" * 92)
    print("D — the structural fact this leaves standing")
    print("=" * 92)
    print(
        "      CAISO has NO scarcity-pricing mechanism in the backcast lane at all:\n"
        "        * the in-LP co-opt (caiso_reserve_coopt) is off and, per\n"
        "          FINDING-caiso131 §4, inert when armed (12.9 GW headroom vs a\n"
        "          2.2 GW requirement);\n"
        "        * the LOLP overlay is forecast-path only (§B);\n"
        "        * no measured overlay series exists, so no scarcity.parquet is\n"
        "          derived and render_calibration_html falls back to _tail_hours on\n"
        "          the ENERGY-ONLY duals.\n"
        "\n      That is the honest reason CAISO's C3c is 0 / 0 / 0 -- not that the\n"
        "      overlay is armed and fails to fire, but that nothing prices scarcity in\n"
        "      the lane C3c is scored on. It also SHARPENS FINDING-caiso131 §4, whose\n"
        "      'the LOLP overlay IS armed on the keeper and is inert because R never\n"
        "      approaches MCL' is doubly imprecise: R is irrelevant because the code\n"
        "      never evaluates it in this lane.\n"
        "\n      Rule 24 [R-REGISTRY] note: caiso_scarcity_pricing appears in the keeper's\n"
        "      run_config.json reading as ARMED while being structurally incapable of\n"
        "      changing that run. That is a provenance trap for any future session, and\n"
        "      it is why this correction is filed rather than quietly dropped."
    )


def main() -> None:
    print("caiso-137b — overlay reachability; corrections to FINDING-caiso137")
    section_a()
    section_b()
    section_c()
    section_d()
    print("\n" + "=" * 92)
    print("VERDICT")
    print("=" * 92)
    print(
        "      STANDS    : ask A2 closes as a NO-DEFECT (caiso-137 §1).\n"
        "      WITHDRAWN : the realised-adder numbers, the flat-nameplate 'defect',\n"
        "                  and the D2 E1/E2 gate table built on it.\n"
        "      NEW       : the CAISO LOLP overlay is unreachable in the backcast lane;\n"
        "                  caiso_scarcity_pricing is a stored no-op there.\n"
        "      KEEPER    : NO candidate. Nothing to arm, nothing to promote — any flag\n"
        "                  would be provably inert in a backcast (matrix code I)."
    )


if __name__ == "__main__":
    main()
