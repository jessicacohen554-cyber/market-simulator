#!/usr/bin/env python
"""Score a capacity hindcast against actuals (W2-P5, plan §1.4).

Consumes a bundle produced by ``scripts/run_capacity_hindcast.py`` (evolution
ledgers + dispatch parquets under ``results/hindcast/<run>/<iso>/<key>/``) and
the scoring target ``data/raw/_validation-source/capacity_actuals_<iso>.csv``
(built by ``scripts/data/build_capacity_actuals.py``). Emits:

* ``<bundle>/score.json`` — every metric, its band, and pass/fail;
* ``docs/hindcast-reports/<iso>-<start>-<end>-<variant>-<date>.md`` — the report,
  including the CO2 decomposition table and the two skill baselines.

Metrics and bands adapt ``forecast-validation-plan.md`` Phase 2c to the 5-year
window (plan §1.4). Scored years are 2023-2025 (2021 seeds, 2022 is the bridge —
never scored, rule 22). A missed band is a **root-cause investigation** (rules
1/11/14), never a band widening, and NOTHING here tunes a parameter.

Reported-only rows (no band, no verdict, no consumer reads a status off them):
``unit_recall_gt300.plant_recall_frac`` (plant-exact recall, G-31) and
``retirements.plant_release_precision`` (plant-grain release precision —
released MW at real-exit plants ÷ released MW, per window / year / channel;
capx D55, D32 §7 R4). They annotate the FC-3 verdict and never gate it.

Usage::

    python scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-...-realized
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
# Invoking this file directly puts scripts/ on sys.path[0], not the repo root,
# so ``scripts.lib.run_record`` would not resolve. Same bootstrap as
# run_capacity_hindcast.py.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.data.fleet import BA_CODE_TO_ISO  # noqa: E402
from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from scripts.lib.run_record import FromArgs, FromConfig, RecordSpec  # noqa: E402

SCORED_YEARS = (2023, 2024, 2025)  # 2021 seeds; 2022 bridged (rule 22).
CO2_HEADLINE_YEAR = 2025
LARGE_UNIT_MW = 300.0
SHORT_TON_TO_METRIC = 0.90718474  # CAMPD co2Mass is short tons.

# ISO → CAMPD state files used to derive the actual CO2 reference. ERCOT ≈ the
# Texas grid; the CAMPD TX total slightly overcounts (El Paso / SPP-side TX
# plants are outside ERCOT) — flagged in the report, never used to tune.
ISO_CAMPD_STATES = {
    "ERCOT": ["TX"],
    "PJM": ["PA", "NJ", "MD", "OH", "VA", "WV", "DE", "KY", "IN", "IL", "NC", "DC"],
}

# ISOs whose footprint crosses many states and overlaps another ISO get a
# *facility-exact* CO2 reference instead of a state sum: CAMPD unit-level rows
# filtered to the ORISPL/plant codes EIA-860 maps to that ISO's balancing
# authority, summed over the states the ISO spans. A plain state sum would be
# badly boundary-misaligned here (rule 11) — MISO shares IN/IL/KY/MI with PJM,
# so a TX..WI state sum would double-count PJM and overstate MISO CO2 by a large
# margin; NYISO ≈ NY but carries a few NJ/PJM-border plants. CAISO joined
# 2026-08-22 (first CAISO T1-H leg): a CA state sum would overcount CAISO by
# the non-CAISO CA balancing authorities' fossil fleets (LADWP, BANC, IID —
# several GW of in-state gas outside the CISO BA), so the same BA crosswalk
# applies. The crosswalk keeps the reference on the model's own BA boundary.
# ERCOT/PJM stay on the state-sum path above (unchanged, already registered).
ISO_CAMPD_FACILITY = frozenset({"MISO", "NYISO", "CAISO"})

THERMAL_FUELS = frozenset(
    {"coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear", "biomass"}
)
ADDITION_TECHS = ("wind", "solar", "gas_cc", "gas_ct", "storage")

# --------------------------------------------------------------------------- #
# Additions attribution basis (owner decision D-9(ii), signed 2026-08-04 —
# ffr-owner-sitting-2026-08-02.md sitting Addendum K.2)
# --------------------------------------------------------------------------- #
# An addition is scored against the year the model DECIDED to build it, not the
# year it commissions. See ``model_additions`` for the mechanism and FFR-3Q
# §3.2 for why the COD basis censors the last two decision cohorts of every
# admissible hindcast window. The COD basis stays computable and is reported
# alongside, so the two are comparable WITHIN one score.json.
ADDITIONS_BASIS_DECISION = "decision"
ADDITIONS_BASIS_COD = "cod"
ADDITIONS_BASES = (ADDITIONS_BASIS_DECISION, ADDITIONS_BASIS_COD)
ADDITIONS_BASIS_DEFAULT = ADDITIONS_BASIS_DECISION

# The record contract for the basis block (FFR-3R, scripts/lib/run_record.py).
# The basis is the SCORER's instrument and the lag gate is the SOLVE's — mixing
# the two sources by hand is the record-provenance defect class FFR-3R closed,
# so both are declared and the finished block is asserted against the solved
# config before it is written.
ADDITIONS_BASIS_RECORD_SPEC = RecordSpec(
    {
        "additions_basis": FromArgs(
            "the SCORER's attribution instrument, not a property of the solved "
            "config: one solve is scorable on either basis, so no ScenarioConfig "
            "field can answer which basis produced this verdict"
        ),
        "entry_commissioning_lag": FromConfig(
            cast=bool,
            why=(
                "the solved-config gate that separates decision from COD; when "
                "False the two bases coincide by construction and the basis "
                "choice is inert"
            ),
        ),
    },
    name="capacity-hindcast additions basis",
)

# Per plan §1.4 band table.
BANDS = {
    "thermal_gw_retired_total_frac": 0.10,
    "thermal_gw_retired_perfuel_frac": 0.20,
    "retire_recall_min": 0.70,
    "false_retire_frac_max": 0.15,
    "retire_timing_years_max": 1.5,
    "add_gw_frac_default": 0.15,  # wind/solar/gas
    "add_gw_frac_storage": 0.25,
    "techmix_share_pp_max": 0.05,
    "co2_2025_frac": 0.10,
}

# --------------------------------------------------------------------------- #
# IS-2020 information-set scoring (RC-0B §c.5, T-R8)
# --------------------------------------------------------------------------- #
# The vintage cutoff V: what was knowable at forecast start (EIA-860 2020
# vintage). Anything whose instrument/announcement post-dates V is unknowable at
# forecast start (RC-0B §c.5-5). Raw scoring grades realized usefulness against
# latest truth; IS-2020 grades forecast skill against the 2020 information set.
# Both are reported side by side — quoting only the flattering one is scoring
# abuse (RC-0B §c.5).
IS2020_CUTOFF = date(2020, 12, 31)

# Retirement-channel vocabulary (RC-0B §c.5-4). Ledger `reason` values map here;
# a bundle produced before the RC-1B recorder split records the pre-split
# "known" reason (steps 0-1 conflated) → announced (rule: legacy "known" maps to
# announced for pre-split bundles).
CHANNEL_ORDER = ("confirmed", "announced", "economic")
_LEGACY_REASON = {"known": "announced"}


# --------------------------------------------------------------------------- #
# Actuals + model aggregation
# --------------------------------------------------------------------------- #
def load_actuals(iso: str) -> pd.DataFrame:
    """Load the committed capacity-actuals CSV for an ISO."""
    path = Path("data/raw/_validation-source") / f"capacity_actuals_{iso.lower()}.csv"
    if not path.exists():
        raise SystemExit(
            f"actuals not found: {path} — run scripts/data/build_capacity_actuals.py --iso {iso}"
        )
    return pd.read_csv(path, comment="#")


def model_retirements(ledgers: dict) -> pd.DataFrame:
    """All modelled retirements across the window (from the ledgers).

    Carries the ledger ``reason`` verbatim so per-channel scoring (§c.5-4) can
    partition on the ``{confirmed, announced, economic}`` vocabulary. Bundles
    produced before the RC-1B recorder split record the pre-split ``"known"``
    reason (steps 0-1 conflated); ``channel_of`` maps that to ``announced``.
    """
    rows = []
    for year, led in ledgers.items():
        for r in led.get("retirements", []):
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["mw"]),
                    "year": year,
                    "reason": r.get("reason", "economic"),
                }
            )
        # NEISO-RC-R R3(iii) (2026-08-31): a confirmed exit on a PLANT-BINNED
        # fleet derates a surviving unit_id in place rather than dropping it —
        # the ledger records that MW under ``confirmed_derates`` (evolve.py's
        # step-0 recorder seam), and reading only ``retirements`` silently
        # swallowed exactly those exits (harmless while every NEISO exit was
        # economic; wrong the moment the R1 registry rows land on binned
        # plants). A derate row and a retirement row never cover the same MW
        # (partial-in-place vs whole-unit drop), so no double count; an absent
        # key (pre-FFR-1A bundles) is backward-compatible.
        for r in led.get("confirmed_derates", []) or []:
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["derate_mw"]),
                    "year": year,
                    "reason": "confirmed",
                }
            )
        # capx D42: the fossil announced-date step-1 channel derates
        # plant-binned tranches through the same machinery, recorded under
        # ``announced_derates`` (evolve.py's step-1 recorder seam) — the
        # announced-channel twin of the row above. Absent on every bundle
        # that never armed ``fossil_announced_exits_enabled``.
        for r in led.get("announced_derates", []) or []:
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["derate_mw"]),
                    "year": year,
                    "reason": "announced",
                }
            )
    return pd.DataFrame(rows, columns=["unit_id", "fuel", "mw", "year", "reason"])


def _entry_pipeline_rows(ledgers: dict) -> list[dict]:
    """Every ``entry_pipeline`` event row across the window, ledger-year tagged.

    The ledger writes this key only when ``entry_commissioning_lag`` is armed
    (``evolve_fleet``'s step-4.5/step-5 recorder seam); a bundle solved with the
    lag off — or any bundle predating FF-2A item 3 — carries no key at all, and
    an absent key is backward-compatible, never malformed. Each row carries both
    ``decision_year`` and ``cod_year`` plus an ``event`` of ``decided``
    (booked into the pipeline this year) or ``commissioned`` (left the pipeline
    into the fleet / VRE pools this year).
    """
    rows: list[dict] = []
    for year, led in ledgers.items():
        for r in led.get("entry_pipeline", []) or []:
            rows.append({**r, "ledger_year": int(year)})
    return rows


def model_additions(
    ledgers: dict, basis: str = ADDITIONS_BASIS_DEFAULT
) -> pd.DataFrame:
    """All modelled additions (thermal + renewable + storage), attributed by year.

    **Owner decision D-9(ii), signed 2026-08-04** (sitting Addendum K.2): the
    default attribution year is the year the model *decided* to build, not the
    year the unit commissions.

    Why the COD basis censors. With ``entry_commissioning_lag`` armed, the
    economic screen books a decision at year *Y* into ``entry_pipeline`` with
    ``cod_year = Y + ENTRY_COD_LAG_YEARS[tech]`` (2 years for
    wind/solar/gas_cc/gas_ct). A ledger's ``thermal_additions`` /
    ``renewable_additions`` rows record the *commissioning*, so in the
    2021→2025 T1-H window the 2024 and 2025 decision cohorts commission in
    2026/2027 and are **never scored** — half the solved decision years are
    invisible. The censoring is permanent and no window length removes it:
    forward needs 2026 (a locked-test year — ``final`` is empty and the holdout
    freeze is active) and 2027 (no actuals), and ``_validate_window`` hard-caps
    a non-crossover window at ``end <= 2025``; backward hits the 2021 demand
    floor and 2020's validation tier. The argument is FFR-3Q §3.2 — not
    re-derived here, and no window is widened to dodge it.

    The two bases:

    ``"decision"``
        Pipeline-mediated builds count in ``decision_year``. Implemented as an
        exact net-out against the COD-basis rows rather than a lag-constant
        reconstruction: every ``commissioned`` row is *reversed* out of its
        ``cod_year`` (where step 4.5 folded it into the ledger's additions) and
        every ``decided`` row is *added* at its ``decision_year``. The ledger
        records ``decision_year`` per row, so nothing is inferred by
        subtracting ``ENTRY_COD_LAG_YEARS``.
    ``"cod"``
        The pre-D-9(ii) instrument: the ledger year the capacity commissions.
        Kept computable so both bases are reported side by side in one
        ``score.json`` (they are comparable to each other; a *new* score.json's
        additions verdict is NOT comparable to any previously committed one —
        see :func:`additions_basis_record`).

    Storage never enters ``entry_pipeline`` (its build channel is the runner's
    ``storage_additions`` value stack, outside the economic-entry screen), so
    storage is COD-attributed under both bases — which is also its decision
    year, the two coinciding by construction.

    Args:
        ledgers: ``{year: ledger_dict}`` from ``load_ledgers_for_run``.
        basis: ``"decision"`` (default, D-9(ii)) or ``"cod"``.

    Returns:
        Columns ``fuel``, ``mw``, ``year``, ``channel``. Under the decision
        basis ``mw`` may be negative on ``pipeline_commissioned_reversal`` rows;
        every consumer aggregates by sum, so the net-out is exact.

    Raises:
        ValueError: ``basis`` is not one of the two declared values.
    """
    if basis not in ADDITIONS_BASES:
        raise ValueError(
            f"unknown additions basis {basis!r} — expected one of {ADDITIONS_BASES}"
        )
    rows = []
    for year, led in ledgers.items():
        for a in led.get("thermal_additions", []):
            rows.append(
                {
                    "fuel": a["fuel"],
                    "mw": float(a["mw"]),
                    "year": year,
                    "channel": "ledger",
                }
            )
        for a in led.get("renewable_additions", []):
            rows.append(
                {
                    "fuel": a["tech"],
                    "mw": float(a["mw"]),
                    "year": year,
                    "channel": "ledger",
                }
            )
        for a in led.get("storage_additions", []):
            rows.append(
                {
                    "fuel": "storage",
                    "mw": float(a["mw"]),
                    "year": year,
                    "channel": "ledger",
                }
            )
    if basis == ADDITIONS_BASIS_DECISION:
        for r in _entry_pipeline_rows(ledgers):
            event = r.get("event")
            if event == "commissioned":
                rows.append(
                    {
                        "fuel": r["tech"],
                        "mw": -float(r["mw"]),
                        "year": int(r["cod_year"]),
                        "channel": "pipeline_commissioned_reversal",
                    }
                )
            elif event == "decided":
                rows.append(
                    {
                        "fuel": r["tech"],
                        "mw": float(r["mw"]),
                        "year": int(r["decision_year"]),
                        "channel": "pipeline_decided",
                    }
                )
    return pd.DataFrame(rows, columns=["fuel", "mw", "year", "channel"])


def load_solved_config(bundle: Path) -> dict | None:
    """The bundle's persisted ``run_config.yaml`` as a plain mapping.

    ``run_capacity_hindcast.py`` dumps every ``ScenarioConfig`` field beside
    ``meta.json`` in the out-dir. ``run_record.as_attr_view`` accepts that dump
    directly, so the basis block can be checked against the config the solve
    actually ran on rather than against the CLI request. Returns ``None`` for a
    bundle that carries no dump (pre-FFR-3R out-dirs, or a hand-assembled one).
    """
    path = Path(bundle) / "run_config.yaml"
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text()) or None


def additions_basis_record(
    ledgers: dict,
    basis: str = ADDITIONS_BASIS_DEFAULT,
    solved_config: dict | None = None,
) -> dict:
    """The explicit, machine-readable provenance of the additions verdict.

    D-9(ii) scope item 2: a reader must be able to tell which basis a verdict
    used **without reading code**. This block rides into the committed hindcast
    sidecar (``register_hindcast`` embeds ``score.json`` wholesale), so the
    basis travels with the verdict.

    It also quantifies what the basis change moved, per ledger: the MW decided
    inside the window whose COD lands *after* it (invisible under the COD
    basis — the censoring D-9(ii) removes) and the MW commissioned inside the
    window whose decision predates it (counted under the COD basis, correctly
    dropped under the decision basis, since that decision was not the window's).

    Args:
        ledgers: ``{year: ledger_dict}`` from ``load_ledgers_for_run``.
        basis: The basis the verdict was scored on.
        solved_config: The bundle's ``run_config.yaml`` mapping, or ``None``.

    Returns:
        The basis block, ready to merge into ``score.json``.

    Raises:
        SystemExit: The block diverges from the solved config (``RecordSpec``).
    """
    rows = _entry_pipeline_rows(ledgers)
    decided = [r for r in rows if r.get("event") == "decided"]
    commissioned = [r for r in rows if r.get("event") == "commissioned"]
    years = sorted(int(y) for y in ledgers)
    first, last = (years[0], years[-1]) if years else (None, None)

    def _by_tech(sub: list[dict]) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in sub:
            out[r["tech"]] = round(out.get(r["tech"], 0.0) + float(r["mw"]) / 1000.0, 3)
        return out

    censored = (
        [r for r in decided if int(r["cod_year"]) > last] if last is not None else []
    )
    inherited = (
        [r for r in commissioned if int(r["decision_year"]) < first]
        if first is not None
        else []
    )

    record: dict = {
        "additions_basis": basis,
        "basis_definition": {
            ADDITIONS_BASIS_DECISION: (
                "an addition counts in the year the model DECIDED to build it "
                "(entry_pipeline decision_year); pipeline commissionings are "
                "reversed out of their cod_year"
            ),
            ADDITIONS_BASIS_COD: (
                "an addition counts in the ledger year it COMMISSIONS — the "
                "pre-D-9(ii) instrument, reported alongside for comparison"
            ),
        }[basis],
        "decision": "D-9(ii), signed 2026-08-04 (sitting Addendum K.2)",
        "ledger_year_span": [first, last],
        "pipeline_rows": {
            "decided": len(decided),
            "commissioned": len(commissioned),
        },
        "decided_in_window_cod_after_window_gw": _by_tech(censored),
        "commissioned_in_window_decided_before_window_gw": _by_tech(inherited),
        "note": (
            "Scored on the DECISION basis (D-9(ii)). Additions verdicts on this "
            "basis are NOT comparable to any additions verdict committed before "
            "2026-08-04, which were scored on the COD basis — the metric means "
            "something different. Retirements-side comparability is unaffected. "
            "See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md."
            if basis == ADDITIONS_BASIS_DECISION
            else (
                "COD basis, reported for comparison against the decision-basis "
                "verdict in this same score.json. NOT the graded instrument."
            )
        ),
    }
    if solved_config is not None:
        record.update(
            ADDITIONS_BASIS_RECORD_SPEC.build(
                solved_config, args_values={"additions_basis": basis}
            )
        )
        ADDITIONS_BASIS_RECORD_SPEC.assert_sourced(record, solved_config)
    else:
        # No dump to check against: record the ABSENCE rather than guessing the
        # gate from the CLI or from meta.json (guessing it is exactly the
        # FFR-3R defect). A null here means "not measured", never "off".
        record["entry_commissioning_lag"] = None
        record["config_source"] = (
            "run_config.yaml absent from the bundle — entry_commissioning_lag "
            "not verifiable against the solved config"
        )
    return record


def _gw_by_fuel(df: pd.DataFrame, kind: str | None = None) -> dict[str, float]:
    if df.empty:
        return {}
    sub = df if kind is None else df[df["kind"] == kind]
    return (sub.groupby("fuel")["mw"].sum() / 1000.0).round(3).to_dict()


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def _band(err_frac: float, tol: float) -> str:
    return "PASS" if abs(err_frac) <= tol else "FAIL"


def model_plant_code(unit_id: str) -> str | None:
    """Best-effort EIA plant code from a *model* retirement ``unit_id``.

    The economic screen retires generators at whatever grain the fleet carries
    when the screen runs, so ``unit_id`` takes several forms:

    * CAMPD per-plant tranche — ``COAL_South_p6183_committed`` → ``"6183"`` (the
      ``p<plant>`` token the binning layer stamps on every tranche);
    * raw EIA unit — ``3490_GEN1`` → ``"3490"`` (leading plant code);
    * legacy zone aggregate — ``coal_COAL_South_Central`` → ``None`` (plant
      identity was collapsed away pre-G-28; only fuel survives).

    Returns the plant code as a string, or ``None`` when identity is lost.
    """
    s = str(unit_id)
    m = re.search(r"_p(\d+)(?:_|$)", s)  # CAMPD tranche form
    if m:
        return m.group(1)
    m = re.match(r"(\d+)(?:_|$)", s)  # raw plant_generator form
    if m:
        return m.group(1)
    return None


def model_plant_gen(unit_id: str) -> tuple[str, str] | None:
    """`(plant_code, generator_id)` from a raw-EIA ``unit_id`` (``6023_1``).

    Announced/confirmed retirements are recorded at raw ``<plant>_<gen>`` grain
    (e.g. Byron ``6023_1``, Dresden ``869_2``), the grain the confirmed-registry
    reversal rows are keyed on. Returns ``None`` for tranche/zone forms (a
    plant-binned economic derate carries no single generator id — it can never be
    a registry reversal match, which is correct: reversal rows are unit-grain
    nuclear only).
    """
    m = re.fullmatch(r"(\d+)_([A-Za-z0-9]+)", str(unit_id))
    if m:
        return m.group(1), m.group(2)
    return None


# --------------------------------------------------------------------------- #
# Gate membership — the REACHABLE set (owner decision D-24)
# --------------------------------------------------------------------------- #
# D-24, SIGNED 2026-08-06 (sitting Addendum X.6). Evidence: FFR-7C
# ``docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md`` §5 +
# Addendum X.1. ERCOT's >=300 MW recall gate was measuring something no
# admissible screen can pass: of its two members, one (Decker Creek 2, 405 MW)
# is capacity the run's fleet never carried, and the other (Sandy Creek 1,
# 1008 MW) clears its going-forward bar in every window year on every variant —
# so a CORRECT economic screen must NOT retire it. A gate whose members are
# unreachable grades plumbing, not skill (rule 1 ``[R-STRUCT]``).
#
# THE MEMBER RULE. A target exit is a gate member iff BOTH hold:
#
#   (i)  the unit exists in the run's FLEET BASIS — the vintage fleet the run
#        actually built; and
#   (ii) its exit is REACHABLE by an admissible channel, either
#          * **economic** — no economic exclusion is recorded for it, or
#          * **instrument-driven** — a non-superseded confirmed-registry
#            instrument whose ``instrument_date <= the run's vintage cutoff``.
#            That is the confirmed-exits information gate's OWN rule
#            (``data.confirmed_retirements.load_confirmed_exits(as_of=...)``),
#            not a scorer invention: an instrument dated after the vintage is
#            unknowable at forecast start, so the channel cannot fire.
#
# Unreachable exits leave the DENOMINATOR and are listed in a NON-GATED
# diagnostic, so the blind spot stays visible on every report rather than
# silently shrinking the metric. An empty member set reports **n/a** — never
# 0/N, which would read as a total miss on exits nothing could have produced.
#
# FAIL-CLOSED. The gate excludes only on POSITIVE, CITED evidence from committed
# artifacts (the corrected target, ``data/raw/confirmed-retirements/``, and the
# per-unit exit decode below). A unit with no evidence either way stays IN. The
# two channel-applicability gates below work the same way: when the run's own
# config cannot corroborate that the evidence applies to THIS run, the exclusion
# is not taken.
EXIT_DECODE_EVIDENCE = {
    "ERCOT": {
        "path": "docs/handoffs/ffr-7c/exit-decode-2026-08-06.json",
        "citation": (
            "FFR-7C §2.2 (per-unit margin table) / §2.4 (fleet-basis facts) — "
            "docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md"
        ),
    },
    # NEISO-RC-R R3(i) (2026-08-31): fleet-basis facts measured per EIA-860
    # vintage (the decode's ``absent_from_vintage_year``), so the exclusion is
    # taken vintage-aware — a unit absent from the run's own vintage fleet is
    # excluded whatever the fleet's binning, and a 2020-vintage run (which
    # still carries e.g. Mystic 7) is untouched. Margin notes carried from the
    # Phase-0 finding's committed S-4b ledger extraction record NO economic
    # exclusion (every noted unit fails its bar — fail-closed, channel open).
    "NEISO": {
        "path": "docs/handoffs/neiso-rc-r/exit-decode-2026-08-31.json",
        "citation": (
            "NEISO-RC-R R3(i) per-vintage fleet-basis measurement — "
            "docs/handoffs/neiso-rc-r/exit-decode-2026-08-31.json (method "
            "header), executing FINDING-capx-neiso-rc-phase0-2026-08-30.md §6"
        ),
    },
}

# The exit decode's fleet-basis facts are read off the CAMPD per-plant bin sheet
# (``data/raw/reference/custom-bin-assignments.csv``), which is the fleet only
# when the run solved with ``use_campd_bins``. A run on the legacy equal-width
# heat-rate bins has a different basis, so the fleet-absence exclusion does not
# transfer to it and is not taken (fail-closed).
FLEET_EVIDENCE_CONFIG_GATE = "use_campd_bins"

# The economic exclusion says "an admissible ECONOMIC screen would not retire
# this unit". It is only decisive when the economic screen is what governs the
# unit's fuel: with ``forecast_fossil_retirement_economic`` off, step 1's
# announced-date channel is live for fossil and could reach the exit by a route
# the decode never measured — so the exclusion is not taken (fail-closed).
ECONOMIC_EVIDENCE_CONFIG_GATE = "forecast_fossil_retirement_economic"
# capx D42: the fossil announced-date step-1 channel (``fossil_announced_
# exits_enabled``) makes the announced route live for fossil under the DEFAULT
# ``forecast_fossil_retirement_economic=True`` too — the economic exclusion is
# then equally not decisive, and is not taken (fail-closed).
FOSSIL_ANNOUNCED_CONFIG_GATE = "fossil_announced_exits_enabled"


def load_solved_scenario_config(bundle: Path | None) -> dict | None:
    """The bundle's solved ``ScenarioConfig`` as a flat mapping, or ``None``.

    Reads ``run_config.yaml`` (the flat ``to_yaml_full`` dump) when present and
    falls back to ``run_config.json``'s nested ``scenario_config`` block, which
    is what older hindcast out-dirs carry. Distinct from
    :func:`load_solved_config`, which is the additions-basis ``RecordSpec``'s
    input and is deliberately left on the yaml-only path.
    """
    if bundle is None:
        return None
    y = Path(bundle) / "run_config.yaml"
    if y.exists():
        return yaml.safe_load(y.read_text()) or None
    j = Path(bundle) / "run_config.json"
    if j.exists():
        blob = json.loads(j.read_text())
        sc = blob.get("scenario_config") if isinstance(blob, dict) else None
        return sc if isinstance(sc, dict) else None
    return None


def vintage_cutoff_of(
    meta: dict | None = None, solved_config: dict | None = None
) -> date:
    """The run's vintage cutoff V — the last date knowable at forecast start.

    Prefers the solved config's ``eia860_vintage_year`` (the fleet snapshot the
    run initialised from), then ``meta.json``'s ``vintage_year``, and falls back
    to :data:`IS2020_CUTOFF` — the plain-hindcast vintage every registered
    bundle uses. Year-end, matching the confirmed-exit information gate's own
    convention (a 2020-vintage run knows every instrument public in 2020).
    """
    for src, key in ((solved_config, "eia860_vintage_year"), (meta, "vintage_year")):
        if isinstance(src, dict) and src.get(key) is not None:
            try:
                return date(int(src[key]), 12, 31)
            except (TypeError, ValueError):
                continue
    return IS2020_CUTOFF


def load_exit_decode(iso: str) -> dict[str, dict]:
    """Per-unit exit-decode evidence for an ISO, keyed by target ``unit_id``.

    Reads the committed decode named in :data:`EXIT_DECODE_EVIDENCE` and
    normalises each unit onto the two facts the member rule consumes, each
    carrying the verbatim decode text as its citation:

    * ``in_fleet`` — ``False`` when the decode records the unit as absent from
      the model's fleet (an ``ABSENT`` ``model_bin``), ``True`` when it names
      the bin that carries it, ``None`` when the decode is silent.
    * ``economic_excluded`` — ``True`` only when the decode adjudicates the exit
      **not** margin-driven under **both** bars (the ``gas_st``↔``gas_ct``
      taxonomy seam gives some units two). A seam-dependent verdict, or a
      margin-driven one, leaves the economic channel open (fail-closed).

    Returns ``{}`` for an ISO with no committed decode — which is every ISO but
    ERCOT, so no other ISO's gate membership changes.
    """
    spec = EXIT_DECODE_EVIDENCE.get(iso.upper())
    if spec is None:
        return {}
    path = Path(spec["path"])
    if not path.exists():
        return {}
    blob = json.loads(path.read_text())
    out: dict[str, dict] = {}
    for uid, u in (blob.get("units") or {}).items():
        bin_txt = str(u.get("model_bin") or "").strip()
        in_fleet = None
        if bin_txt:
            in_fleet = not bin_txt.upper().startswith("ABSENT")
        tgt = u.get("economically_consistent_target_bar")
        phys = u.get("economically_consistent_physical_bar")
        econ_excluded = None
        if isinstance(tgt, bool):
            # Not margin-driven under the bar actually applied AND (where the
            # seam gives a second bar) under the physical one too.
            econ_excluded = (not tgt) and (not phys if isinstance(phys, bool) else True)
        absent_vint = u.get("absent_from_vintage_year")
        out[str(uid)] = {
            "unit_id": str(uid),
            "name": u.get("name"),
            "mw": u.get("mw"),
            "in_fleet": in_fleet,
            # Vintage-aware fleet fact (NEISO-RC-R R3(i)): the first EIA-860
            # vintage whose OP-filtered fleet basis lacks the unit. When set,
            # the fleet-absence exclusion applies iff the RUN's vintage year
            # >= this value — replacing the CAMPD-bin-sheet applicability gate
            # for evidence measured directly off the vintage sheets.
            "absent_from_vintage_year": (
                int(absent_vint) if absent_vint is not None else None
            ),
            "fleet_note": bin_txt or None,
            "economic_excluded": econ_excluded,
            "economic_note": (
                None
                if econ_excluded is None
                else (
                    f"primary-year margin {u.get('primary_margin')} vs bar "
                    f"{u.get('bar_target_taxonomy')} $/kW-yr in "
                    f"{u.get('primary_year')} ({u.get('primary_margin_basis')})"
                    + (", bar-invariant" if u.get("bar_invariant") else "")
                )
            ),
            "citation": spec["citation"],
        }
    return out


def load_instrument_index(iso: str) -> dict[tuple[str, str], dict]:
    """Earliest non-superseded confirmed-registry instrument per ``(plant, gen)``.

    The same collapse ``data.confirmed_retirements.load_confirmed_exits`` does —
    superseded rows dropped (a counter-instrument suspends the exit), earliest
    instrument kept — so the scorer's view of the instrument channel is the
    mechanism's own view. ``{}`` when the ISO has no registry file.
    """
    path = Path("data/raw/confirmed-retirements") / f"{iso.lower()}.csv"
    if not path.exists():
        return {}
    lines = [
        ln
        for ln in path.read_text().splitlines(keepends=True)
        if not ln.lstrip().startswith("#")
    ]
    out: dict[tuple[str, str], dict] = {}
    for row in csv.DictReader(lines):
        if str(row.get("superseded") or "").strip().lower() in ("true", "1", "yes"):
            continue
        key = (
            str(row.get("plant_id") or "").strip(),
            str(row.get("generator_id") or "").strip(),
        )
        inst_date = pd.to_datetime(
            (row.get("instrument_date") or "").strip(), errors="coerce"
        )
        prev = out.get(key)
        if prev is not None and pd.notna(prev["instrument_date"]):
            if pd.isna(inst_date) or inst_date >= prev["instrument_date"]:
                continue
        out[key] = {
            "instrument_id": (row.get("instrument_id") or "").strip(),
            "instrument_date": inst_date,
            "confirmation_class": (row.get("confirmation_class") or "").strip(),
            "unit_name": (row.get("unit_name") or "").strip(),
        }
    return out


def classify_exit_reachability(
    iso: str,
    actuals: pd.DataFrame,
    *,
    vintage_cutoff: date | None = None,
    solved_config: dict | None = None,
    decode: dict[str, dict] | None = None,
    instruments: dict[tuple[str, str], dict] | None = None,
) -> dict:
    """Classify every thermal target exit as reachable or not (D-24).

    Implements the member rule stated above this function. The classification
    runs over **every** thermal retirement row, not just the >= ``LARGE_UNIT_MW``
    ones, so the diagnostic shows the whole blind spot; ``members`` is the
    subset that is both large enough to gate and reachable.

    Args:
        iso: ISO code (selects the committed decode + registry).
        actuals: The scoring target (``load_actuals`` output).
        vintage_cutoff: The run's V; defaults to :data:`IS2020_CUTOFF`.
        solved_config: The run's flat ``ScenarioConfig`` mapping, used ONLY to
            check that each evidence class applies to this run. ``None`` ⇒ the
            fleet-absence exclusion is not taken (fail-closed).
        decode / instruments: Injected evidence, for tests. Loaded from the
            committed artifacts when omitted.

    Returns:
        The reachability block. ``applied`` is ``False`` — and ``members`` is
        ``None``, meaning "do not filter" — when the target carries no
        ``unit_id`` column to key evidence on.
    """
    cutoff = vintage_cutoff or IS2020_CUTOFF
    decode = load_exit_decode(iso) if decode is None else decode
    instruments = load_instrument_index(iso) if instruments is None else instruments
    spec = EXIT_DECODE_EVIDENCE.get(iso.upper(), {})

    cfg = solved_config if isinstance(solved_config, dict) else {}
    use_bins = cfg.get(FLEET_EVIDENCE_CONFIG_GATE)
    fossil_econ = cfg.get(ECONOMIC_EVIDENCE_CONFIG_GATE)
    fossil_dated = cfg.get(FOSSIL_ANNOUNCED_CONFIG_GATE)
    fleet_applies = use_bins is True
    econ_applies = fossil_econ is not False and fossil_dated is not True

    block: dict = {
        "decision": "D-24, signed 2026-08-06 (sitting Addendum X.6)",
        "rule": (
            "a target exit gates the >=%g MW recall metric only if the unit "
            "exists in the run's fleet basis AND its exit is reachable by an "
            "admissible channel — economic (no exclusion recorded) or "
            "instrument-driven with instrument_date <= the run's vintage "
            "cutoff. Unreachable exits leave the denominator and are reported "
            "here, NON-GATED." % LARGE_UNIT_MW
        ),
        "vintage_cutoff": cutoff.isoformat(),
        "large_unit_mw": LARGE_UNIT_MW,
        "evidence": {
            "target": f"data/raw/_validation-source/capacity_actuals_{iso.lower()}.csv",
            "confirmed_registry": f"data/raw/confirmed-retirements/{iso.lower()}.csv",
            "exit_decode": spec.get("path"),
            "exit_decode_citation": spec.get("citation"),
        },
        "applicability": {
            FLEET_EVIDENCE_CONFIG_GATE: use_bins,
            "fleet_evidence_applied": fleet_applies,
            ECONOMIC_EVIDENCE_CONFIG_GATE: fossil_econ,
            FOSSIL_ANNOUNCED_CONFIG_GATE: fossil_dated,
            "economic_evidence_applied": econ_applies,
        },
        "fail_closed": (
            "excludes only on positive, cited evidence; a unit with no evidence "
            "either way stays IN the member set"
        ),
    }

    act = actuals[actuals["kind"] == "retirement"]
    act = act[act["fuel"].isin(THERMAL_FUELS)]
    if "unit_id" not in act.columns:
        block.update(
            {
                "applied": False,
                "members": None,
                "excluded": [],
                "n_target_large": int((act["mw"] >= LARGE_UNIT_MW).sum())
                if not act.empty
                else 0,
                "n_members": None,
                "n_excluded_gated": 0,
                "note": (
                    "target carries no unit_id column — evidence cannot be keyed "
                    "per unit, so no exclusion is taken (fail-closed)"
                ),
            }
        )
        return block

    members: list[str] = []
    excluded: list[dict] = []
    for _, a in act.sort_values("mw", ascending=False).iterrows():
        uid = str(a["unit_id"])
        mw = float(a["mw"])
        ev = decode.get(uid, {})
        pg = model_plant_gen(uid)
        inst = instruments.get(pg) if pg is not None else None
        inst_date = inst["instrument_date"] if inst else pd.NaT
        inst_reachable = bool(
            inst is not None
            and pd.notna(inst_date)
            and inst_date.date() <= cutoff  # the confirmed-exit information gate
        )
        econ_excluded = bool(econ_applies and ev.get("economic_excluded") is True)
        # Fleet-absence: vintage-aware evidence (absent_from_vintage_year —
        # measured off the EIA-860 vintage sheets, applies iff the run's own
        # vintage is at/after the absence; NEISO-RC-R R3(i)) takes precedence;
        # otherwise the CAMPD-bin-sheet fact behind the use_campd_bins gate.
        absent_vint = ev.get("absent_from_vintage_year")
        if absent_vint is not None:
            not_in_fleet = cutoff.year >= int(absent_vint)
        else:
            not_in_fleet = bool(fleet_applies and ev.get("in_fleet") is False)

        if inst is None:
            driver = (
                "not margin-driven (exit decode); no confirmed-registry "
                "instrument exists"
                if econ_excluded
                else "not established from committed artifacts"
            )
        else:
            d = "" if pd.isna(inst_date) else inst_date.date().isoformat()
            driver = (
                f"confirmed instrument {inst['instrument_id']}"
                f" ({inst['confirmation_class']}, instrument_date {d or 'unknown'})"
            )

        reason = why = None
        if not_in_fleet:
            reason = "not_in_fleet_basis"
            why = (
                f"{ev.get('fleet_note')} — no screen can retire capacity the "
                f"run's fleet never carried"
            )
        elif econ_excluded and not inst_reachable:  # neither channel can fire
            if inst is not None:
                reason = "post_vintage_instrument"
                d = "" if pd.isna(inst_date) else inst_date.date().isoformat()
                why = (
                    f"no admissible channel — economic screen must not retire it "
                    f"({ev.get('economic_note')}), and its only instrument "
                    f"({inst['instrument_id']}, {d}) post-dates the vintage "
                    f"cutoff {cutoff.isoformat()}"
                )
            else:
                reason = "no_instrument"
                why = (
                    f"no admissible channel — economic screen must not retire it "
                    f"({ev.get('economic_note')}), and no confirmed-registry "
                    f"instrument exists"
                )

        if reason is None:
            if mw >= LARGE_UNIT_MW:
                members.append(uid)
            continue
        excluded.append(
            {
                "unit_id": uid,
                "unit_name": ev.get("name") or (inst or {}).get("unit_name"),
                "mw": round(mw, 1),
                "fuel": a["fuel"],
                "exit_year": int(a["year"]),
                "driver": driver,
                "reason": reason,
                "why": why,
                "gated": mw >= LARGE_UNIT_MW,
                "citation": ev.get("citation")
                or block["evidence"]["confirmed_registry"],
            }
        )

    n_large = int((act["mw"] >= LARGE_UNIT_MW).sum())
    block.update(
        {
            "applied": True,
            "members": members,
            "excluded": excluded,
            "n_target_large": n_large,
            "n_members": len(members),
            "n_excluded_gated": sum(1 for r in excluded if r["gated"]),
            "note": (
                "NON-GATED diagnostic. Rows here left the recall denominator (or "
                "were never in it, below the size threshold); nothing in this "
                "block bands, and no verdict reads off it."
            ),
        }
    )
    return block


def plant_release_precision(
    mod_thermal: pd.DataFrame, act_thermal: pd.DataFrame
) -> dict:
    """Plant-grain release precision (capx D55 / D32 §2.3, §7 R4): reported only.

    ``released MW at real-exit plants ÷ released MW`` — of the thermal MW the
    model retired, the share landing at a plant (same EIA plant code, same
    fuel) that really retired anywhere in the scoring window. Returned for
    the window and per model ledger year, each split by channel: ``economic``
    (the screen-plus-floor release D32 characterised — the selection question)
    and ``all`` (every channel, incl. the dated/confirmed exits whose plant
    identity is an input rather than a choice). Timing is deliberately not
    scored here (a 2024 release at a plant that really left in 2025 counts);
    the timing band lives in its own metric.

    Model rows whose plant identity was collapsed away (``model_plant_code``
    → ``None``, legacy zone aggregates) count in the denominator as misses
    and are reported in ``released_mw_no_plant_identity`` so a low reading
    on an aggregate fleet is legible as identity loss rather than selection.
    A channel with no released MW reads ``precision: None`` (never 0). No
    band is attached and no consumer reads a verdict off this block.
    """
    real_plants: set[tuple[str, str]] = set()
    if "plant_id" in act_thermal.columns:
        for _, a in act_thermal.iterrows():
            if pd.notna(a["plant_id"]):
                real_plants.add((str(int(a["plant_id"])), str(a["fuel"])))

    def _block(rows: pd.DataFrame) -> dict:
        released = float(rows["mw"].sum()) if len(rows) else 0.0
        hit = 0.0
        no_identity = 0.0
        for _, r in rows.iterrows():
            pc = model_plant_code(r["unit_id"]) if "unit_id" in rows.columns else None
            if pc is None:
                no_identity += float(r["mw"])
            elif (pc, str(r["fuel"])) in real_plants:
                hit += float(r["mw"])
        return {
            "released_mw": round(released, 3),
            "released_mw_at_real_exit_plants": round(hit, 3),
            "released_mw_no_plant_identity": round(no_identity, 3),
            "precision": round(hit / released, 3) if released > 0.0 else None,
        }

    reason = (
        mod_thermal["reason"]
        if "reason" in mod_thermal.columns
        else pd.Series([None] * len(mod_thermal), index=mod_thermal.index)
    )
    channel = reason.map(channel_of) if len(mod_thermal) else reason
    econ = mod_thermal[channel == "economic"] if len(mod_thermal) else mod_thermal

    def _both(rows_all: pd.DataFrame, rows_econ: pd.DataFrame) -> dict:
        return {"economic": _block(rows_econ), "all": _block(rows_all)}

    per_year: dict[str, dict] = {}
    if "year" in mod_thermal.columns:
        for y in sorted({int(v) for v in mod_thermal["year"].dropna()}):
            m_all = mod_thermal[mod_thermal["year"] == y]
            m_econ = econ[econ["year"] == y] if len(econ) else econ
            per_year[str(y)] = _both(m_all, m_econ)
    return {
        "grain": "plant-code+fuel, window real-exit set; reported only (D32 R4)",
        "n_real_exit_plants": len(real_plants),
        "window": _both(mod_thermal, econ),
        "per_year": per_year,
    }


def score_retirements(
    model: pd.DataFrame, actuals: pd.DataFrame, reachability: dict | None = None
) -> dict:
    """Retirement GW (total + per-fuel), grain-corrected recall + false-retire.

    **Grain fix (G-31).** The economic screen retires *plant-binned tranches*
    (MW derates), never raw EIA units: one plant's coal exits as several tranche
    rows (must-run / committed / peak / econ), and pre-G-28 runs even collapse
    survivors into multi-GW zone aggregates. The old 1:1 ``fuel+size`` match
    (a model row within [0.5×, 1.5×] of one actual unit) therefore mis-scored
    every lumpy or split derate — a 4 GW zone-coal row can never sit inside
    [0.5×, 1.5×] of a 486 MW actual unit, so the whole derate scored as
    *false-retire* (the 94% artifact) while the real unit scored as *un-recalled*
    — even when the model retired exactly the right fuel in the right amount.

    The corrected grain scores capacity the way the screen can actually produce
    it — by fuel MW, plant identity not required (per the G-31 spec):

    * **recall** — a real retired unit (≥ ``LARGE_UNIT_MW``) is *recalled* when
      the model derated at least its MW of the **same fuel** (its plant-binned
      tranche is derated by its MW). Greedy, largest actual unit first, each
      claim consuming the model's per-fuel derate pool so two real units aren't
      both credited to the same MW.
    * **false-retire** — genuine over-retirement only: model-derated MW of a
      fuel in **excess** of what that fuel actually retired, summed over fuels.
      Grain-independent (a tranche split or a zone lump nets out); it flags the
      model retiring *more* coal than reality, never the model retiring the
      *right* coal in an unfamiliar shape. (When this stays high after the fix
      it is a real over-retirement — e.g. the G-30 scarcity-free screen exiting
      the whole coal fleet — a screen root-cause, not a scoring artifact.)

    ``plant_recall_frac`` is reported (not banded) as a stricter diagnostic: the
    share of large actual units whose exact plant the model also retired.

    ``plant_release_precision`` (capx D55, D32 §2.3 / §7 R4 — REPORTED ONLY,
    no band, no verdict, no consumer reads a status off it) is recall's
    mirror at plant grain: of the MW the model released, how much sits at a
    plant that really exited (same plant code AND same fuel, anywhere in the
    2021–2025 window) — ``released MW at real-exit plants ÷ released MW``.
    Per fuel-MW excess (``false_retire``) the model can never be "false"
    while it retires less of a fuel than reality did, whichever plants it
    lands on; this row is the selection question that grain is blind to
    (13.5 % on D31's 3.7 GW coal release; 100 % for a perfect selector).
    Reported for the whole window and per ledger year, and split by channel
    (``economic`` — the screen-plus-floor release the question is about —
    against ``all``, which folds in the dated/confirmed channels whose plant
    identity is an input). Rows whose plant identity was collapsed away
    (legacy zone aggregates) stay in the denominator and are counted
    separately; a channel with no released MW reads ``None``, never 0.

    **Gate membership (owner decision D-24).** ``reachability`` — the block
    :func:`classify_exit_reachability` returns — redefines the recall
    denominator as the **reachable** set: a target exit gates only if it exists
    in the run's fleet basis and an admissible channel could produce it.
    Unreachable exits are excluded and reported in the non-gated
    ``reachability`` block; an empty member set reports **n/a** (band ``SKIP``),
    never 0/N. ``None`` (the default) keeps the pre-D-24 denominator — every
    large target row — so a caller with no evidence to key on, and every
    existing caller, is unchanged.
    """
    act = actuals[actuals["kind"] == "retirement"]
    act_thermal = act[act["fuel"].isin(THERMAL_FUELS)]
    mod_thermal = model[model["fuel"].isin(THERMAL_FUELS)]

    act_gw = act_thermal["mw"].sum() / 1000.0
    mod_gw = mod_thermal["mw"].sum() / 1000.0
    total_err = (mod_gw - act_gw) / act_gw if act_gw else float("nan")

    # Per-fuel retired MW (grain-independent — a tranche split sums back).
    perfuel = {}
    fuels = set(act_thermal["fuel"]) | set(mod_thermal["fuel"])
    model_fuel_mw = mod_thermal.groupby("fuel")["mw"].sum().to_dict()
    actual_fuel_mw = act_thermal.groupby("fuel")["mw"].sum().to_dict()
    for f in sorted(fuels):
        a = actual_fuel_mw.get(f, 0.0) / 1000.0
        m = model_fuel_mw.get(f, 0.0) / 1000.0
        e = (m - a) / a if a else float("nan")
        perfuel[f] = {
            "actual_gw": round(a, 3),
            "model_gw": round(m, 3),
            "err_frac": None if np.isnan(e) else round(e, 3),
        }

    # --- Grain-corrected recall (G-31): per-fuel MW coverage --------------- #
    # A real retired unit is recalled when the model derated >= its MW of the
    # same fuel. Greedy largest-first so each unit claims distinct model MW.
    big = act_thermal[act_thermal["mw"] >= LARGE_UNIT_MW].sort_values(
        "mw", ascending=False
    )
    n_target_large = int(len(big))
    member_rule = "all-large-target-rows (pre-D-24)"
    applied_reach = bool(
        reachability
        and reachability.get("applied")
        and reachability.get("members") is not None
        and "unit_id" in big.columns
    )
    if applied_reach:
        member_rule = "reachable-set (D-24)"
        members = {str(u) for u in reachability["members"]}
        big = big[big["unit_id"].astype(str).isin(members)]
    fuel_pool = {f: float(mw) for f, mw in model_fuel_mw.items()}
    matched = 0
    for _, a in big.iterrows():
        f, m = a["fuel"], float(a["mw"])
        if fuel_pool.get(f, 0.0) + 1e-6 >= m:
            matched += 1
            fuel_pool[f] = fuel_pool.get(f, 0.0) - m
    recall = matched / len(big) if len(big) else float("nan")

    # Stricter plant-exact diagnostic (reported, not banded): how many large
    # actual units the model also retired at the *same plant* of the same fuel.
    mod_plant_fuel = set()
    for _, r in mod_thermal.iterrows():
        pc = (
            model_plant_code(r["unit_id"]) if "unit_id" in mod_thermal.columns else None
        )
        if pc is not None:
            mod_plant_fuel.add((pc, r["fuel"]))
    plant_matched = 0
    if "plant_id" in big.columns:
        for _, a in big.iterrows():
            if (str(int(a["plant_id"])), a["fuel"]) in mod_plant_fuel:
                plant_matched += 1
    plant_recall = plant_matched / len(big) if len(big) else float("nan")

    # capx D55 / D32 R4 — plant-grain RELEASE PRECISION (reported only). The
    # real-exit plant set is every (plant, fuel) with an actual thermal
    # retirement row in the window, any size (the selection question is
    # about where the release LANDS, not the ≥300 MW recall universe).
    release_precision = plant_release_precision(mod_thermal, act_thermal)

    # --- Grain-corrected false-retire (G-31): per-fuel excess -------------- #
    false_gw = 0.0
    for f in set(model_fuel_mw) | set(actual_fuel_mw):
        false_gw += (
            max(0.0, model_fuel_mw.get(f, 0.0) - actual_fuel_mw.get(f, 0.0)) / 1000.0
        )
    false_frac = false_gw / mod_gw if mod_gw else 0.0

    out = {
        "total_gw": {
            "actual": round(act_gw, 3),
            "model": round(mod_gw, 3),
            "err_frac": None if np.isnan(total_err) else round(total_err, 3),
            "band": _band(total_err, BANDS["thermal_gw_retired_total_frac"])
            if not np.isnan(total_err)
            else "SKIP",
        },
        "per_fuel": perfuel,
        "unit_recall_gt300": {
            "n_big_actual": int(len(big)),
            "matched": matched,
            "recall": None if np.isnan(recall) else round(recall, 3),
            "grain": "fuel-mw-coverage",  # G-31: not exact unit identity
            # D-24: the denominator is the REACHABLE set, and how it was
            # arrived at travels with the verdict — never basis-implicit.
            "member_rule": member_rule,
            "n_target_large": n_target_large,
            "n_excluded_unreachable": n_target_large - int(len(big)),
            "n_a": bool(applied_reach and len(big) == 0),
            "n_a_reason": (
                "no target exit >= %g MW is reachable by an admissible channel "
                "on this run's fleet basis — reported n/a, never 0/N (D-24)"
                % LARGE_UNIT_MW
            )
            if applied_reach and len(big) == 0
            else None,
            "plant_recall_frac": None
            if np.isnan(plant_recall)
            else round(plant_recall, 3),
            "plant_matched": plant_matched,
            "band": ("PASS" if recall >= BANDS["retire_recall_min"] else "FAIL")
            if not np.isnan(recall)
            else "SKIP",
        },
        # REPORTED ONLY (capx D55, D32 R4): no band, no verdict; see the
        # docstring. Sits beside plant_recall_frac's block, not inside it, so
        # no consumer keyed on unit_recall_gt300's schema changes.
        "plant_release_precision": release_precision,
        "false_retire": {
            "false_gw": round(false_gw, 3),
            "frac_of_model": round(false_frac, 3),
            "grain": "per-fuel-excess",  # G-31: genuine over-retire, not artifact
            "band": "PASS" if false_frac <= BANDS["false_retire_frac_max"] else "FAIL",
        },
    }
    if reachability is not None:
        # NON-GATED (D-24). It carries no band and no consumer reads a verdict
        # off it; it exists so the excluded blind spot is visible on every
        # report rather than silently shrinking the denominator.
        out["reachability"] = reachability
    return out


def score_additions(
    model: pd.DataFrame, actuals: pd.DataFrame, basis: str = ADDITIONS_BASIS_DEFAULT
) -> dict:
    """Cumulative additions by tech + tech-mix shares.

    ``basis`` is stamped into the result so a verdict is never basis-implicit
    (D-9(ii) scope item 2); it selects nothing here — the caller has already
    attributed ``model``'s rows via :func:`model_additions`.
    """
    act = actuals[actuals["kind"] == "addition"]
    by_tech = {}
    for tech in ADDITION_TECHS:
        a = act[act["fuel"] == tech]["mw"].sum() / 1000.0
        m = model[model["fuel"] == tech]["mw"].sum() / 1000.0
        e = (m - a) / a if a else float("nan")
        tol = (
            BANDS["add_gw_frac_storage"]
            if tech == "storage"
            else BANDS["add_gw_frac_default"]
        )
        by_tech[tech] = {
            "actual_gw": round(a, 3),
            "model_gw": round(m, 3),
            "err_frac": None if np.isnan(e) else round(e, 3),
            "band": _band(e, tol) if not np.isnan(e) else "SKIP",
        }
    # Tech-mix shares (of total additions).
    act_tot = act["mw"].sum() / 1000.0
    mod_tot = model["mw"].sum() / 1000.0
    shares = {}
    for tech in ADDITION_TECHS:
        a_share = (
            (act[act["fuel"] == tech]["mw"].sum() / 1000.0 / act_tot)
            if act_tot
            else 0.0
        )
        m_share = (
            (model[model["fuel"] == tech]["mw"].sum() / 1000.0 / mod_tot)
            if mod_tot
            else 0.0
        )
        dpp = m_share - a_share
        shares[tech] = {
            "actual_share": round(a_share, 3),
            "model_share": round(m_share, 3),
            "delta_pp": round(dpp, 3),
            "band": "PASS" if abs(dpp) <= BANDS["techmix_share_pp_max"] else "FAIL",
        }
    return {
        "basis": basis,
        "by_tech": by_tech,
        "shares": shares,
        "actual_total_gw": round(act_tot, 3),
        "model_total_gw": round(mod_tot, 3),
    }


def model_co2_by_year(bundle: Path) -> dict[int, float]:
    """Total modelled CO2 (metric tonnes) per scored year.

    The LP result does not carry an ``emissions`` array in the forecast path,
    so CO2 is reconstructed from the persisted dispatch × the fleet context's
    per-generator emission rate (tCO2/MWh) — the same quantity the emissions
    module computes, but self-contained here.
    """
    from market_sim.results.outputs import from_parquet, read_fleet_context

    out = {}
    for year in SCORED_YEARS:
        p = bundle / f"year_{year}.parquet"
        if not p.exists():
            continue
        res = from_parquet(DispatchResult, p)
        if res.emissions is not None:
            out[year] = float(np.asarray(res.emissions).sum())
            continue
        try:
            ctx = read_fleet_context(p)
        except ValueError:
            continue
        rate = np.asarray(ctx.emission_rate, dtype=float)  # tCO2/MWh per gen
        gen_mwh = np.asarray(res.dispatch, dtype=float).sum(axis=1)
        out[year] = float((gen_mwh * rate).sum())
    return out


def _iso_plant_codes_and_states(iso: str) -> tuple[set[int], list[str]]:
    """ORISPL/plant codes and the states EIA-860 maps to ``iso``'s BA.

    Mirrors ``build_capacity_actuals._plant_ba``: the plant sheet's ``Balancing
    Authority Code`` is the ISO boundary, and CAMPD ``facilityId`` is the same
    ORISPL code as EIA ``Plant Code``. Returns the plant-code set (for the CAMPD
    facility filter) and the distinct states those plants sit in (to bound which
    CAMPD state files are read).
    """
    plant = pd.read_parquet(Path("data/raw/eia-860/eia860_plant.parquet"))
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()].copy()
    plant["Plant Code"] = plant["Plant Code"].astype(float).astype(int)
    bas = {ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}
    sub = plant[plant["Balancing Authority Code"].isin(bas)]
    codes = set(int(c) for c in sub["Plant Code"].tolist())
    states = sorted({str(s).strip() for s in sub["State"].dropna() if str(s).strip()})
    return codes, states


def _actual_co2_facility(iso: str) -> dict[int, float]:
    """Facility-exact actual CO2 (metric tonnes), scored years only (rule 11).

    Filters CAMPD unit-level ``co2Mass`` (short → metric) to the plants EIA-860
    maps to ``iso``'s balancing authority, summed over the states the ISO spans.
    Used for footprint-crossing ISOs (``ISO_CAMPD_FACILITY``) where a state sum
    would double-count a neighbouring ISO. NEVER reads 2022/2026 (rule 22).
    """
    codes, states = _iso_plant_codes_and_states(iso)
    out: dict[int, float] = {}
    base = Path("data/raw/campd-unit-level")
    for year in SCORED_YEARS:
        total_short = 0.0
        found = False
        for st in states:
            p = base / f"{st}_{year}.parquet"
            if not p.exists():
                continue
            found = True
            df = pd.read_parquet(p, columns=["facilityId", "co2Mass"])
            fid = pd.to_numeric(df["facilityId"], errors="coerce")
            mask = fid.isin(codes)
            total_short += float(
                pd.to_numeric(df.loc[mask, "co2Mass"], errors="coerce").sum()
            )
        if found:
            out[year] = total_short * SHORT_TON_TO_METRIC
    return out


def actual_co2_by_year(iso: str) -> dict[int, float]:
    """Derive actual CO2 (metric tonnes) from CAMPD unit-level, scored years only.

    Footprint-crossing ISOs (``ISO_CAMPD_FACILITY``: MISO, NYISO) use a
    facility-exact BA crosswalk. Single-state-dominant ISOs (ERCOT, PJM) sum
    ``co2Mass`` (short tons → metric) over their CAMPD state files; ERCOT ≈ TX
    (slight overcount, flagged). NEVER reads 2022/2026 (rule 22).
    """
    if iso in ISO_CAMPD_FACILITY:
        return _actual_co2_facility(iso)
    states = ISO_CAMPD_STATES.get(iso, [])
    out: dict[int, float] = {}
    base = Path("data/raw/campd-unit-level")
    for year in SCORED_YEARS:
        total_short = 0.0
        found = False
        for st in states:
            p = base / f"{st}_{year}.parquet"
            if not p.exists():
                continue
            found = True
            df = pd.read_parquet(p, columns=["co2Mass"])
            total_short += float(pd.to_numeric(df["co2Mass"], errors="coerce").sum())
        if found:
            out[year] = total_short * SHORT_TON_TO_METRIC
    return out


def actual_co2_basis(iso: str) -> str:
    """One-line provenance label for the capacity-track CO2 ``actual``.

    The capacity-track actual is a CAMPD footprint sum, NOT the eGRID
    ISO-basis actual the FC-4 dispatch-skill co2 metric in the same score
    file scores against; the two were conflated once
    (``docs/handoffs/FINDING-capx-d5-crossover-co2-2026-08-30.md`` §2.3), so
    the basis is now stated in the artifact itself. The ERCOT/PJM STATE sums
    overcount their ISO footprint (whole-TX ≈ +11 % vs ERCOT eGRID; the
    PJM state sum ≈ +54 % vs PJM eGRID) — never decompose across the two
    co2 blocks.
    """
    if iso in ISO_CAMPD_FACILITY:
        return (
            "CAMPD unit-level co2Mass, facility-exact EIA-860 BA crosswalk "
            f"({iso} plants only; metric tonnes) — capacity-track basis, not "
            "the FC-4 eGRID basis"
        )
    states = "/".join(ISO_CAMPD_STATES.get(iso, [])) or "none"
    return (
        f"CAMPD unit-level co2Mass STATE SUM over {states} (whole-state "
        f"footprint, metric tonnes) — overstates the {iso} BA and is NOT the "
        "FC-4 eGRID ISO basis in the same score file; never compare across "
        "the two co2 blocks"
    )


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
def baseline_announced(iso: str) -> dict:
    """Announced-only baseline: the 2020-vintage planned schedule, verbatim."""
    vdir = Path("data/raw/eia-860/vintage_2020")
    out = {"retire_gw": 0.0, "add_gw": 0.0, "note": "2020-vintage planned schedule"}
    op = vdir / "eia860_generator_operable.parquet"
    if op.exists():
        df = pd.read_parquet(op)
        yr = pd.to_numeric(df.get("Planned Retirement Year"), errors="coerce")
        mw = pd.to_numeric(df.get("Nameplate Capacity (MW)"), errors="coerce")
        mask = yr.isin(list(range(2021, 2026)))
        out["retire_gw"] = round(float(mw[mask].sum()) / 1000.0, 3)
    prop = vdir / "eia860_generator_proposed.parquet"
    if prop.exists():
        df = pd.read_parquet(prop)
        mw = pd.to_numeric(df.get("Nameplate Capacity (MW)"), errors="coerce")
        out["add_gw"] = round(float(mw.sum()) / 1000.0, 3)
    return out


# --------------------------------------------------------------------------- #
# IS-2020 information-set scoring (RC-0B §c.5, T-R8) — no re-solve
# --------------------------------------------------------------------------- #
def channel_of(reason) -> str:
    """Map a ledger ``reason`` onto the ``{confirmed, announced, economic}``
    channel vocabulary (§c.5-4). Legacy ``"known"`` → ``announced``."""
    if reason is None or (isinstance(reason, float) and np.isnan(reason)):
        return "economic"
    r = str(reason)
    return _LEGACY_REASON.get(r, r)


def load_reversal_set(
    iso: str, cutoff: "date | None" = None
) -> dict[tuple[str, str], dict]:
    """Post-cutoff reversal rows from the confirmed-registry (§c.5-1).

    Membership test for the Byron/Dresden class: a confirmed-registry row with
    ``superseded=true`` whose original instrument was public on or before V
    (``instrument_date <= V``) and was superseded *only* by a counter-instrument
    dated **after** V (``superseding_instrument_date > V``). Keyed on
    ``(plant_id, generator_id)`` — the grain the model records nuclear exits on.

    ``cutoff`` is V; ``None`` (the T-R8 default) uses :data:`IS2020_CUTOFF`, so
    the ``--rescore`` lane is byte-identical. The default scoring path passes
    the run's own vintage cutoff (``vintage_cutoff_of``), so a non-2020-vintage
    leg classifies against ITS information set rather than 2020's.

    Eddystone (superseded by a DOE 202(c) order with **no**
    ``superseding_instrument_date`` populated) is correctly excluded: its
    reversal date is unknown to the registry, so it is not a knowable-at-V
    information-set-correct reversal. Diablo Canyon (SB 846, 2022-09) would
    qualify for any future CAISO window; none of the four T-R8 ISOs but PJM
    carries a post-V reversal row.

    Returns ``{(plant, gen): {instrument, unit_name, capacity_mw}}``; empty when
    the ISO has no registry file (read robustly past the ``#`` comment header —
    the registry carries commas inside quoted instrument text).
    """
    path = Path("data/raw/confirmed-retirements") / f"{iso.lower()}.csv"
    if not path.exists():
        return {}
    cutoff = pd.Timestamp(cutoff if cutoff is not None else IS2020_CUTOFF)
    lines = [
        ln
        for ln in path.read_text().splitlines(keepends=True)
        if not ln.lstrip().startswith("#")
    ]
    out: dict[tuple[str, str], dict] = {}
    for row in csv.DictReader(lines):
        superseded = str(row.get("superseded") or "").strip().lower() in (
            "true",
            "1",
            "yes",
        )
        if not superseded:
            continue
        sup_date = pd.to_datetime(
            (row.get("superseding_instrument_date") or "").strip(), errors="coerce"
        )
        inst_date = pd.to_datetime(
            (row.get("instrument_date") or "").strip(), errors="coerce"
        )
        # Knowable-at-V original, unknowable-at-V reversal (the §c.5-1 class).
        if pd.isna(sup_date) or sup_date <= cutoff:
            continue
        if pd.notna(inst_date) and inst_date > cutoff:
            continue
        key = (
            str(row.get("plant_id") or "").strip(),
            str(row.get("generator_id") or "").strip(),
        )
        out[key] = {
            "instrument": (row.get("superseding_instrument") or "").strip(),
            "unit_name": (row.get("unit_name") or "").strip(),
            "capacity_mw": row.get("capacity_mw"),
        }
    return out


def reversal_exposure(model: pd.DataFrame, reversal_set: dict) -> dict:
    """Model retirements that qualify for IS-2020 reversal exclusion (§c.5-1).

    A model row is reversal-exposed iff its ``(plant, generator)`` is in the
    post-cutoff reversal set. Its MW is **excluded from IS-2020 false-retire**
    and reported here as ``reversal_exposure_gw`` naming the reversing
    instrument. Raw scoring keeps the MW as false-retire (realized reality: the
    unit runs today). Returns the exposed rows, total GW, unit_ids, and the
    distinct instruments.
    """
    rows, exposed_ids = [], set()
    if not reversal_set or model.empty:
        return {"exposure_gw": 0.0, "rows": [], "unit_ids": set(), "instruments": []}
    for _, r in model.iterrows():
        pg = model_plant_gen(r["unit_id"])
        if pg is not None and pg in reversal_set:
            info = reversal_set[pg]
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["mw"]),
                    "plant_id": pg[0],
                    "generator_id": pg[1],
                    "unit_name": info["unit_name"],
                    "instrument": info["instrument"],
                }
            )
            exposed_ids.add(r["unit_id"])
    gw = round(sum(x["mw"] for x in rows) / 1000.0, 3)
    instruments = sorted({x["instrument"] for x in rows if x["instrument"]})
    return {
        "exposure_gw": gw,
        "rows": rows,
        "unit_ids": exposed_ids,
        "instruments": instruments,
    }


def score_retirements_is2020(
    model: pd.DataFrame,
    actuals: pd.DataFrame,
    reversal_set: dict,
    reachability: dict | None = None,
) -> dict:
    """IS-2020 retirement scoring: raw metric with reversal-exposed MW removed.

    Only the reversal exclusion (§c.5-1) changes the numbers here; the Palisades
    physical-exit convention (§c.5-2) and Indian Point coverage fix (§c.5-3) act
    through the **actuals** (RD-5), so they are already reflected in the raw pass
    and need no model-side adjustment. IS false-retire drops the information-set-
    correct reversals; recall is recomputed on the reduced model but is unchanged
    wherever the reversed fuel has no actual to cover (the PJM nuclear case).
    """
    exposure = reversal_exposure(model, reversal_set)
    keep = (
        model[~model["unit_id"].isin(exposure["unit_ids"])]
        if exposure["unit_ids"]
        else model
    )
    base = score_retirements(keep, actuals, reachability)
    base["reversal_exposure_gw"] = exposure["exposure_gw"]
    base["reversal_instruments"] = exposure["instruments"]
    base["reversal_rows"] = exposure["rows"]
    return base


def score_channels(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """Per-channel recall + false-retire (§c.5-4), keyed ``{confirmed, announced,
    economic}`` so an economic-screen grade is never polluted by an announced-
    channel event (or vice-versa).

    * **false-retire** is decomposed by allocating each fuel's *actual* retired
      MW across channels in a fixed priority order (confirmed → announced →
      economic); a channel's false-retire is its per-fuel model MW in excess of
      the actual MW still un-attributed when it is reached. The per-channel sum
      reproduces the raw total exactly, and — because the four T-R8 bundles are
      each single-channel per fuel — the allocation is order-independent here.
    * **recall** attributes each ≥300 MW actual unit to the first channel (same
      priority order) whose remaining same-fuel model pool alone covers it; the
      per-channel matched counts sum to the raw matched count wherever each fuel
      is retired by a single channel (all four bundles).
    """
    if "reason" not in model.columns:
        model = model.assign(reason="economic")
    model = model.assign(channel=model["reason"].map(channel_of))
    act = actuals[actuals["kind"] == "retirement"]
    act_th = act[act["fuel"].isin(THERMAL_FUELS)]
    actual_fuel_mw = act_th.groupby("fuel")["mw"].sum().to_dict()

    present = list(dict.fromkeys(model["channel"].tolist()))
    ordered = [c for c in CHANNEL_ORDER if c in present] + [
        c for c in present if c not in CHANNEL_ORDER
    ]

    # False-retire: priority allocation of actual MW pools.
    pool = dict(actual_fuel_mw)
    out: dict[str, dict] = {}
    for c in ordered:
        cm = model[model["channel"] == c]
        cfuel = cm.groupby("fuel")["mw"].sum().to_dict()
        false_gw = 0.0
        for f, mw in cfuel.items():
            avail = pool.get(f, 0.0)
            false_gw += max(0.0, mw - avail) / 1000.0
            pool[f] = max(0.0, avail - mw)
        out[c] = {
            "retired_gw": round(float(cm["mw"].sum()) / 1000.0, 3),
            "false_retire_gw": round(false_gw, 3),
            "model_fuel_gw": {f: round(v / 1000.0, 3) for f, v in cfuel.items()},
        }

    # Recall attribution: greedy, largest actual unit first, priority order.
    big = act_th[act_th["mw"] >= LARGE_UNIT_MW].sort_values("mw", ascending=False)
    rpool = {
        c: model[model["channel"] == c].groupby("fuel")["mw"].sum().to_dict()
        for c in ordered
    }
    matched = {c: 0 for c in ordered}
    for _, a in big.iterrows():
        f, m = a["fuel"], float(a["mw"])
        for c in ordered:
            if rpool[c].get(f, 0.0) + 1e-6 >= m:
                matched[c] += 1
                rpool[c][f] = rpool[c].get(f, 0.0) - m
                break
    for c in ordered:
        out[c]["recall_matched"] = matched[c]
    out["_n_big_actual"] = int(len(big))
    out["_legacy_known_mapped_to"] = "announced"
    return out


def additions_is2020(model_add: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """IS-2020 additions adjustment: exclude post-V restart additions (§c.5-2).

    Convention (Palisades): the physical 2022 exit is booked in the actuals and
    scores as a correct recall in both modes; the ~2025 *restart* is a post-V
    instrument, unknowable at forecast start, so it is excluded from IS-2020
    additions. A restart is an ``addition`` of a fuel at a ``plant_id`` that the
    same actuals record as an earlier in-window ``retirement`` of that fuel.

    Model additions carry no plant identity, so the exclusion is defined over the
    actuals only (the model cannot double-count a restart it never added). In the
    RD-5 actuals as landed there is **no** restart addition row — the coverage
    fix booked only Palisades' physical exit — so this is inert here; it is
    implemented for correctness and forward CAISO/Diablo windows.
    """
    act = actuals[actuals["kind"] == "addition"]
    excluded_gw = 0.0
    excluded_rows: list[dict] = []
    if "plant_id" in actuals.columns:
        retired_plants = set(
            actuals[actuals["kind"] == "retirement"]
            .apply(lambda r: (str(r.get("plant_id")), r["fuel"]), axis=1)
            .tolist()
        )
        for _, a in act.iterrows():
            if (str(a.get("plant_id")), a["fuel"]) in retired_plants:
                excluded_gw += float(a["mw"]) / 1000.0
                excluded_rows.append(
                    {
                        "plant_id": str(a.get("plant_id")),
                        "fuel": a["fuel"],
                        "mw": float(a["mw"]),
                    }
                )
    return {
        "restart_excluded_gw": round(excluded_gw, 3),
        "restart_rows": excluded_rows,
        "note": (
            "Post-V restart additions excluded from IS-2020 additions (§c.5-2). "
            "Inert in the RD-5 actuals as landed — the coverage fix booked only "
            "the physical exit, no restart addition row exists."
        ),
    }


# --------------------------------------------------------------------------- #
# Flip-gate extras (FF-1A): T-R10 no-inversion guard, LOYO folds, BLK-10
# backstop-fired MW — all scorer-side, computed from the committed evolution
# ledgers + RD-5 actuals. NO LP is solved here.
# --------------------------------------------------------------------------- #
# T-R10b zero-real-fuel accumulation threshold (GW). Pre-registered in the
# retirement-rule redesign memo §4 (ff-retirement-rule-redesign-2026-07.md):
# a fuel that retired ZERO in reality accumulating > 1 GW of model economic
# exits is a cross-fuel inversion, whatever the totals do.
TR10B_ZERO_REAL_GW_MAX = 1.0


def score_tr10(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """T-R10 no-inversion guard (redesign memo §4, pre-registered).

    Evaluated on the **economic channel only** (announced/confirmed events are
    instrument-driven, not decision-rule output — the PJM Byron/Dresden nuclear
    reversal must never trip this guard):

    * ``first_mover`` — fuel(s) of the earliest model economic-channel exit.
      **T-R10a** FAILs iff any first-mover fuel has actual retired MW = 0
      (the model's first economic wave hits a fuel reality never retired).
    * **T-R10b** FAILs iff any fuel with zero actual retirements accumulates
      more than ``TR10B_ZERO_REAL_GW_MAX`` GW of model economic exits.

    Vacuously PASS when the model has no economic thermal exits (no wave, no
    inversion). Bands are pre-registered and never widened (rules 1/14).
    """
    act = actuals[actuals["kind"] == "retirement"]
    act_th = act[act["fuel"].isin(THERMAL_FUELS)]
    actual_fuel_mw = act_th.groupby("fuel")["mw"].sum().to_dict()

    if "reason" not in model.columns:
        model = model.assign(reason="economic")
    econ = model[model["reason"].map(channel_of) == "economic"]
    econ_th = econ[econ["fuel"].isin(THERMAL_FUELS)]

    econ_fuel_gw = {
        f: round(mw / 1000.0, 3)
        for f, mw in econ_th.groupby("fuel")["mw"].sum().to_dict().items()
    }
    if econ_th.empty:
        return {
            "first_mover_fuels": [],
            "first_mover_year": None,
            "econ_exit_gw_by_fuel": {},
            "zero_real_fuels_over_1gw": [],
            "tr10a": "PASS",
            "tr10b": "PASS",
            "note": "no economic thermal exits — vacuous PASS",
        }
    first_year = int(econ_th["year"].min())
    first_movers = sorted(econ_th[econ_th["year"] == first_year]["fuel"].unique())
    tr10a_fail = any(actual_fuel_mw.get(f, 0.0) <= 0.0 for f in first_movers)
    zero_real_over = sorted(
        f
        for f, gw in econ_fuel_gw.items()
        if actual_fuel_mw.get(f, 0.0) <= 0.0 and gw > TR10B_ZERO_REAL_GW_MAX
    )
    return {
        "first_mover_fuels": first_movers,
        "first_mover_year": first_year,
        "econ_exit_gw_by_fuel": econ_fuel_gw,
        "actual_gw_by_fuel": {
            f: round(mw / 1000.0, 3) for f, mw in sorted(actual_fuel_mw.items())
        },
        "zero_real_fuels_over_1gw": zero_real_over,
        "tr10a": "FAIL" if tr10a_fail else "PASS",
        "tr10b": "FAIL" if zero_real_over else "PASS",
    }


def blk10_backstop_fired(ledgers: dict) -> dict:
    """BLK-10: precise reserve-margin-backstop fired MW (gap-register §3.9).

    Sums ``thermal_additions`` rows whose ``source == "reserve_backstop"`` —
    the adequacy backstop's own ledger channel (``gas_ct_adequacy_<year>``
    units) — per year and in total, alongside the economic/planned additions
    split, so the backstop's share of the build is separable from economic
    entry. Pure ledger arithmetic; no LP.
    """
    fired_rows: list[dict] = []
    by_source: dict[str, float] = {}
    for year, led in ledgers.items():
        for a in led.get("thermal_additions", []):
            src = a.get("source", "economic")
            by_source[src] = by_source.get(src, 0.0) + float(a["mw"])
            if src == "reserve_backstop":
                fired_rows.append(
                    {
                        "year": int(year),
                        "unit_id": a.get("unit_id"),
                        "fuel": a.get("fuel"),
                        "mw": round(float(a["mw"]), 3),
                    }
                )
    fired_mw = sum(r["mw"] for r in fired_rows)
    return {
        "fired_rows": fired_rows,
        "fired_mw_total": round(fired_mw, 3),
        "fired_gw_total": round(fired_mw / 1000.0, 3),
        "thermal_additions_mw_by_source": {
            k: round(v, 3) for k, v in sorted(by_source.items())
        },
    }


def loyo_folds(
    model: pd.DataFrame,
    actuals: pd.DataFrame,
    reversal_set: dict,
    reachability: dict | None = None,
) -> dict:
    """Leave-one-year-out folds within the scored years (rule 22 LOYO clause).

    Fold ``y`` re-scores the cumulative window with year ``y``'s events removed
    from BOTH the model ledger and the actuals (2021 seed-year and 2022-bridge
    events always stay — only scored years are held out). Scorer-side only: the
    fold is a re-score of the committed bundle, never a re-solve. Per fold:
    grain-corrected recall, false-retire (raw + IS-2020), and the T-R10a/b
    guard. The promotion criterion (plan §2.1 item 4 / rule 22) is that a
    verdict holds in >= 2 of 3 folds; ``holds_2of3`` grades exactly that for
    recall-PASS, T-R10a-PASS and T-R10b-PASS.

    ``reachability`` (D-24) is passed straight through to each fold: membership
    is a property of the target row, so dropping a fold's actuals drops that
    year's members with them. When every fold's recall is n/a — no reachable
    member survives in any fold — ``holds_2of3["recall_pass"]`` is ``None``
    (n/a), never ``False``: a >=2/3 bar over three n/a folds is not a failure.
    """
    folds: dict[str, dict] = {}
    for y in SCORED_YEARS:
        m = model[model["year"] != y]
        a = actuals[actuals["year"] != y]
        ret = score_retirements(m, a, reachability)
        ret_is = score_retirements_is2020(m, a, reversal_set, reachability)
        tr10 = score_tr10(m, a)
        rr = ret["unit_recall_gt300"]
        folds[str(y)] = {
            "held_out_year": y,
            "recall": rr["recall"],
            "recall_band": rr["band"],
            "matched": rr["matched"],
            "n_big_actual": rr["n_big_actual"],
            "false_retire_gw_raw": ret["false_retire"]["false_gw"],
            "false_retire_band_raw": ret["false_retire"]["band"],
            "false_retire_gw_is2020": ret_is["false_retire"]["false_gw"],
            "tr10a": tr10["tr10a"],
            "tr10b": tr10["tr10b"],
            "tr10_first_mover_fuels": tr10["first_mover_fuels"],
        }

    def _holds(key: str, ok: str) -> bool:
        return sum(1 for f in folds.values() if f[key] == ok) >= 2

    recall_na = bool(folds) and all(f["recall_band"] == "SKIP" for f in folds.values())

    return {
        "folds": folds,
        "holds_2of3": {
            "recall_pass": None if recall_na else _holds("recall_band", "PASS"),
            "tr10a_pass": _holds("tr10a", "PASS"),
            "tr10b_pass": _holds("tr10b", "PASS"),
        },
        "note": (
            "Scorer-side LOYO: fold y drops year-y events from model AND "
            "actuals; no re-solve. >=2/3 folds is the rule-22 promotion bar."
            + (
                " recall_pass is null: every fold's recall is n/a (no reachable "
                "member survives the fold), so the >=2/3 bar has nothing to "
                "grade — D-24."
                if recall_na
                else ""
            )
        ),
    }


def _flip_gate_extras(bundle: Path) -> int:
    """Compute T-R10 + LOYO + BLK-10 on a committed bundle and update its
    score.json (keys ``tr10``, ``tr10_is2020``, ``loyo``, ``blk10_backstop``).
    No LP is solved; the existing score keys are preserved."""
    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret = model_retirements(ledgers)
    reversal_set = load_reversal_set(iso)
    solved = load_solved_scenario_config(bundle)
    reach = classify_exit_reachability(
        iso,
        actuals,
        vintage_cutoff=vintage_cutoff_of(meta, solved),
        solved_config=solved,
    )

    tr10 = score_tr10(mret, actuals)
    exposure = reversal_exposure(mret, reversal_set)
    mret_is = (
        mret[~mret["unit_id"].isin(exposure["unit_ids"])]
        if exposure["unit_ids"]
        else mret
    )
    tr10_is = score_tr10(mret_is, actuals)
    loyo = loyo_folds(mret, actuals, reversal_set, reach)
    blk10 = blk10_backstop_fired(ledgers)

    score_path = cache_dir / "score.json"
    score = json.loads(score_path.read_text()) if score_path.exists() else {}
    score.update(
        {
            "tr10": tr10,
            "tr10_is2020": tr10_is,
            "loyo": loyo,
            "blk10_backstop": blk10,
            "flip_gate_extras": {
                "task": "FF-1A",
                "note": (
                    "T-R10 no-inversion guard + LOYO folds (2023-2025) + "
                    "BLK-10 backstop-fired MW — scorer-side, no re-solve."
                ),
                "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }
    )
    score_path.write_text(json.dumps(score, indent=2))

    h = loyo["holds_2of3"]
    print(
        f"[flip-gate] {iso} {bundle.name}: T-R10a {tr10['tr10a']} / "
        f"T-R10b {tr10['tr10b']} (first mover {tr10['first_mover_fuels']}); "
        f"LOYO holds>=2/3: recall={h['recall_pass']} tr10a={h['tr10a_pass']} "
        f"tr10b={h['tr10b_pass']}; BLK-10 fired {blk10['fired_gw_total']} GW"
    )
    for fy, f in loyo["folds"].items():
        print(
            f"[flip-gate]   fold -{fy}: recall "
            f"{f['matched']}/{f['n_big_actual']} ({f['recall_band']}), "
            f"false raw {f['false_retire_gw_raw']} GW, "
            f"tr10a {f['tr10a']} tr10b {f['tr10b']}"
        )
    print(f"[flip-gate] score.json: {score_path}")
    return 0


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt_band(x: str) -> str:
    return {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "SKIP": "—"}.get(x, x)


def render_reachability_section(reach: dict | None, rr: dict) -> list[str]:
    """The D-24 gate-membership disclosure + the NON-GATED unreachable list.

    Rendered under the retirement table on every report, whether or not the
    exclusion moved anything: the point of the diagnostic is that the blind spot
    stays visible. ``[]`` when the run carries no reachability block (pre-D-24
    denominator, nothing to disclose).
    """
    if not reach or not reach.get("applied"):
        return []
    L = [
        f"> **Gate membership (D-24, {reach['decision'].split(',', 1)[-1].strip()}):** "
        f"the >={reach['large_unit_mw']:.0f} MW recall denominator is the "
        f"**reachable** set — a target exit gates only if the unit exists in the "
        f"run's fleet basis AND an admissible channel could produce its exit "
        f"(economic with no exclusion recorded, or an instrument dated on or "
        f"before the run's vintage cutoff **{reach['vintage_cutoff']}**). "
        f"Members: **{rr['n_big_actual']} of {rr['n_target_large']}** target rows "
        f">={reach['large_unit_mw']:.0f} MW"
        + (
            f" — recall **n/a** (never 0/N): {rr['n_a_reason']}."
            if rr.get("n_a")
            else "."
        ),
        "",
    ]
    excl = reach.get("excluded") or []
    if not excl:
        L.append(
            "No target exit is classified unreachable on committed evidence "
            "(fail-closed: the gate excludes only on positive, cited evidence)."
        )
        L.append("")
        return L
    L.append(
        f"**Unreachable exits — NON-GATED diagnostic** ({len(excl)} rows, "
        f"{reach['n_excluded_gated']} of them >={reach['large_unit_mw']:.0f} MW and "
        "therefore out of the denominator). Nothing here bands:"
    )
    L.append("")
    L.append("| unit | MW | fuel | exit | driver | why unreachable | gated |")
    L.append("|---|--:|---|--:|---|---|:--|")
    for r in excl:
        name = r["unit_name"] or r["unit_id"]
        L.append(
            f"| `{r['unit_id']}` {name} | {r['mw']} | {r['fuel']} | {r['exit_year']} "
            f"| {r['driver']} | {r['reason']} — {r['why']} | "
            f"{'yes' if r['gated'] else 'no (below size threshold)'} |"
        )
    L.append("")
    L.append(
        f"_Evidence, per unit: {reach['evidence']['exit_decode_citation'] or '—'}; "
        f"`{reach['evidence']['confirmed_registry']}`. "
        f"{reach['fail_closed'].capitalize()}._"
    )
    L.append("")
    return L


def write_report(
    iso,
    variant,
    meta,
    ret,
    add,
    co2,
    baselines,
    report_path: Path,
    add_cod: dict | None = None,
    add_basis: dict | None = None,
    ret_is: dict | None = None,
    is_cutoff: str | None = None,
) -> None:
    """Render the markdown hindcast report.

    ``add_cod``/``add_basis`` render the D-9(ii) basis disclosure and the
    COD-basis comparison; omitted (``None``) they are simply not rendered.
    ``ret_is``/``is_cutoff`` render the policy-saved announced-exit note
    (§c.5-1 reversal exposure at the run's vintage cutoff V=``is_cutoff``)
    when the exposure is non-zero; omitted or zero-exposure they are not
    rendered.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    L = []
    L.append(f"# Capacity hindcast — {iso} 2021→2025 ({variant} fuel)")
    L.append("")
    L.append(
        f"_Generated {stamp} · W2-P5 · plan §1.4 · bundle `{meta.get('bundle', '')}`_"
    )
    L.append("")
    L.append(
        "Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. "
        "2021 seeds the price signal (not scored); **2022 is the quarantine bridge — "
        "evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a "
        "root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned."
    )
    L.append("")
    # Retirements
    L.append("## Retirements (thermal, cumulative 2021→2025)")
    tg = ret["total_gw"]
    L.append("")
    L.append("| metric | actual | model | err | band |")
    L.append("|---|--:|--:|--:|:--|")
    tg_err = "" if tg["err_frac"] is None else format(tg["err_frac"], "+.0%")
    L.append(
        f"| thermal GW retired | {tg['actual']} | {tg['model']} | "
        f"{tg_err} | {_fmt_band(tg['band'])} |"
    )
    rr = ret["unit_recall_gt300"]
    L.append(
        f"| unit recall >300MW | {rr['n_big_actual']} units | {rr['matched']} matched | "
        f"{('n/a' if rr.get('n_a') else '') if rr['recall'] is None else format(rr['recall'], '.0%')}"
        f" | {_fmt_band(rr['band'])} |"
    )
    fr = ret["false_retire"]
    L.append(
        f"| false-retire (GW) | — | {fr['false_gw']} | {format(fr['frac_of_model'], '.0%')} of model | {_fmt_band(fr['band'])} |"
    )
    L.append("")
    pr = (
        ""
        if rr.get("plant_recall_frac") is None
        else format(rr["plant_recall_frac"], ".0%")
    )
    L.append(
        "> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW "
        "coverage**, not exact unit identity — a real retired unit is *recalled* "
        "when the model derated ≥ its MW of the same fuel (its plant-binned tranche "
        "is derated by its MW), and *false-retire* is the model's per-fuel MW in "
        "**excess** of what that fuel actually retired. This retires the 94% "
        "false-retire artifact the old 1:1 `fuel+size` match produced against lumpy "
        f"tranche/zone derates. Stricter plant-exact recall (same plant, reported "
        f"only): **{pr or '—'}** ({rr.get('plant_matched', 0)}/{rr['n_big_actual']}). "
        "A false-retire that stays high after the grain fix is a genuine "
        "over-retirement (screen root-cause, e.g. G-30), not a scoring artifact."
    )
    L.append("")
    L.extend(render_release_precision_note(ret.get("plant_release_precision")))
    L.extend(render_reachability_section(ret.get("reachability"), rr))
    L.append("Per-fuel retired GW:")
    L.append("")
    L.append("| fuel | actual | model | err |")
    L.append("|---|--:|--:|--:|")
    for f, d in ret["per_fuel"].items():
        e = "" if d["err_frac"] is None else format(d["err_frac"], "+.0%")
        L.append(f"| {f} | {d['actual_gw']} | {d['model_gw']} | {e} |")
    L.append("")
    # Policy-saved announced exits (§c.5-1 reversal exposure): plants whose
    # announced retirement the model executed but which were saved at the
    # last moment by a public counter-instrument the run's information set
    # could not know. Rendered only when the run actually retired one.
    if ret_is is not None and ret_is.get("reversal_exposure_gw", 0.0) > 0.0:
        L.append("### Announced exits reversed by later policy (information-set note)")
        L.append("")
        L.append(
            f"**{ret_is['reversal_exposure_gw']} GW** of the model's retired "
            "capacity executed announced retirement dates that were REVERSED "
            "by a policy instrument dated after the run's vintage cutoff "
            f"(V = {is_cutoff or IS2020_CUTOFF.isoformat()}) — the plants were "
            "saved at the last moment and run today, so the raw pass counts "
            "them as false-retire while the information-set pass excludes "
            "them (ex-ante the exit was the knowable outcome). Raw stays the "
            "graded instrument; both are reported (RC-0B §c.5). Units:"
        )
        L.append("")
        L.append("| unit | fuel | MW | reversing instrument |")
        L.append("|---|---|--:|---|")
        for r in ret_is.get("reversal_rows", []):
            L.append(
                f"| {r['unit_name'] or r['unit_id']} | {r['fuel']} | "
                f"{r['mw']:.0f} | {r['instrument']} |"
            )
        fr_is = ret_is["false_retire"]
        L.append("")
        L.append(
            f"False-retire net of these reversals: **{fr_is['false_gw']} GW** "
            f"({format(fr_is['frac_of_model'], '.0%')} of model, "
            f"{_fmt_band(fr_is['band'])}) vs raw "
            f"{ret['false_retire']['false_gw']} GW. A hindcast leg launched "
            "with announced-exit verification armed (the harness default "
            "since 2026-08-22) counters these dates in the solve itself and "
            "shows zero exposure here."
        )
        L.append("")
    # Additions
    basis = add.get("basis", ADDITIONS_BASIS_DEFAULT)
    L.append(f"## Additions (cumulative 2021→2025) — **{basis} basis**")
    L.append("")
    if add_basis is not None:
        L.append(
            f"_Attribution basis: **{basis}** (owner decision "
            f"{add_basis.get('decision', 'D-9(ii)')}). "
            f"{add_basis.get('note', '')}_"
        )
        L.append("")
        cens = add_basis.get("decided_in_window_cod_after_window_gw") or {}
        inh = add_basis.get("commissioned_in_window_decided_before_window_gw") or {}
        L.append(
            "Basis effect — decided in-window with COD **after** the window "
            f"(invisible under the COD basis): `{cens or 'none'}`; commissioned "
            "in-window from a **pre-window** decision (dropped under the "
            f"decision basis): `{inh or 'none'}` (GW)."
        )
        L.append("")
    L.append("| tech | actual GW | model GW | err | band | Δ-share (pp) |")
    L.append("|---|--:|--:|--:|:--|--:|")
    for tech in ADDITION_TECHS:
        d = add["by_tech"][tech]
        s = add["shares"][tech]
        e = "" if d["err_frac"] is None else format(d["err_frac"], "+.0%")
        L.append(
            f"| {tech} | {d['actual_gw']} | {d['model_gw']} | {e} | {_fmt_band(d['band'])} "
            f"| {format(s['delta_pp'] * 100, '+.1f')} |"
        )
    L.append("")
    if add_cod is not None:
        L.append(
            f"COD-basis comparison (**not** the graded instrument; "
            f"model total {add_cod['model_total_gw']} GW vs decision-basis "
            f"{add['model_total_gw']} GW):"
        )
        L.append("")
        L.append("| tech | model GW (COD) | model GW (decision) | band (COD) |")
        L.append("|---|--:|--:|:--|")
        for tech in ADDITION_TECHS:
            c, d = add_cod["by_tech"][tech], add["by_tech"][tech]
            L.append(
                f"| {tech} | {c['model_gw']} | {d['model_gw']} | "
                f"{_fmt_band(c['band'])} |"
            )
        L.append("")
    # CO2
    L.append("## System CO2 (headline: 2025, ±10%)")
    L.append("")
    L.append("| year | model Mt | actual Mt | err | band |")
    L.append("|---|--:|--:|--:|:--|")
    for year in SCORED_YEARS:
        m = co2["model"].get(str(year)) or co2["model"].get(year)
        a = co2["actual"].get(str(year)) or co2["actual"].get(year)
        if m is None:
            continue
        mt_m = m / 1e6
        if a:
            err = (m - a) / a
            band = "PASS" if abs(err) <= BANDS["co2_2025_frac"] else "FAIL"
            band = band if year == CO2_HEADLINE_YEAR else "report-only"
            L.append(
                f"| {year} | {mt_m:.1f} | {a / 1e6:.1f} | {err:+.0%} | "
                f"{_fmt_band(band) if year == CO2_HEADLINE_YEAR else '(report-only)'} |"
            )
        else:
            L.append(f"| {year} | {mt_m:.1f} | (n/a) | — | — |")
    L.append("")
    L.append(
        "> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** "
        "(the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new "
        "capacity-path information). Supply the keeper CO2 gap to attribute the "
        "split; absent it, the table reports the *total* hindcast error only. "
        "Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly "
        "overcounts (El Paso/SPP-side TX plants)."
    )
    L.append("")
    # Baselines
    L.append("## Skill baselines (must beat on retirement recall + addition mix)")
    L.append("")
    L.append("| baseline | retire GW | add GW | note |")
    L.append("|---|--:|--:|---|")
    L.append("| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |")
    b = baselines["announced"]
    L.append(f"| (b) announced-only | {b['retire_gw']} | {b['add_gw']} | {b['note']} |")
    L.append(
        "| (c) AEO2021 regional | — | — | report-only context (not computed here) |"
    )
    L.append("")
    if meta.get("leakage_violations"):
        L.append("## ⚠️ Leakage-guard violations")
        for v in meta["leakage_violations"]:
            L.append(f"- {v}")
        L.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(L))


def render_rescore_section(
    iso: str, ret: dict, ret_is: dict, channels: dict, add_is: dict, stamp: str
) -> str:
    """The IS-2020 re-score section appended to a hindcast report (T-R8).

    Presents raw and IS-2020 metrics side by side (RC-0B §c.5: quoting only the
    flattering one is scoring abuse), the reversal-exposure line naming the
    instrument, and the per-channel recall/false-retire tables. The originals
    above this marker are preserved — this is scoring hygiene on the *committed*
    bundle, no re-solve.
    """
    fr, rr = ret["false_retire"], ret["unit_recall_gt300"]
    fr_is = ret_is["false_retire"]
    exp = ret_is.get("reversal_exposure_gw", 0.0)
    L = []
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"## IS-2020 re-score (T-R8, {stamp}) — no re-solve")
    L.append("")
    L.append(
        "Scoring-hygiene re-score of the **committed** bundle against RC-0B §c.5: "
        "**raw** grades realized usefulness against latest truth; **IS-2020** grades "
        "forecast skill against what was knowable at the 2020 vintage cutoff "
        f"(V = {IS2020_CUTOFF.isoformat()}). Both are reported side by side — neither "
        "replaces the other. No LP was solved; the originals above are preserved. "
        "The RD-5 actuals-coverage fix (plants 8907 Indian Point, 1715 Palisades) is "
        "already reflected in the raw pass; IS-2020 adds the Byron/Dresden reversal "
        "exclusion (§c.5-1)."
    )
    L.append("")
    L.append("| retirement metric | raw | IS-2020 |")
    L.append("|---|--:|--:|")
    L.append(
        f"| false-retire (GW) | {fr['false_gw']} ({_fmt_band(fr['band'])}) | "
        f"{fr_is['false_gw']} ({_fmt_band(fr_is['band'])}) |"
    )
    L.append(
        f"| false-retire (% of model) | {format(fr['frac_of_model'], '.0%')} | "
        f"{format(fr_is['frac_of_model'], '.0%')} |"
    )
    rr_is = ret_is["unit_recall_gt300"]

    def _recall_cell(x: dict) -> str:
        if x.get("n_a"):
            return "n/a"  # D-24: no reachable member, never 0/N
        return "" if x["recall"] is None else format(x["recall"], ".0%")

    L.append(
        f"| unit recall >300MW | {_recall_cell(rr)} "
        f"({rr['matched']}/{rr['n_big_actual']}) | "
        f"{_recall_cell(rr_is)} "
        f"({rr_is['matched']}/{rr_is['n_big_actual']}) |"
    )
    pr = rr.get("plant_recall_frac")
    L.append(
        f"| plant-exact recall (diagnostic) | "
        f"{('—' if pr is None else format(pr, '.0%'))} "
        f"({rr.get('plant_matched', 0)}/{rr['n_big_actual']}) | (same) |"
    )
    L.append(f"| reversal exposure (GW, §c.5-1) | — | {exp} |")
    L.append("")
    L.extend(render_release_precision_note(ret.get("plant_release_precision")))
    L.extend(render_reachability_section(ret.get("reachability"), rr))
    # Finding: plant-exact recall above fuel-MW recall means the model retired the
    # right plant(s) but carries a pmax below the EIA nameplate the RD-5 actuals
    # use — a units-basis near-miss, not a screen miss (rules 1/11: keep the
    # accurate actual, surface the basis gap rather than bend the metric).
    if pr is not None and rr["recall"] is not None and pr > rr["recall"] + 1e-9:
        L.append(
            "> **Recall-grain finding (§c.5-2/-3):** plant-exact recall "
            f"({format(pr, '.0%')}) exceeds fuel-MW-coverage recall "
            f"({format(rr['recall'], '.0%')}) — the model retired the correct "
            "plant(s) in the correct year, but its carried `pmax` sits below the "
            "EIA nameplate the RD-5 actuals use (Palisades: model 768.5 MW vs "
            "actual nameplate 811.8 MW, a 5% basis gap), so the strict ≥-MW "
            "coverage test marks it a near-miss. This is a nameplate-vs-pmax "
            "basis difference, **not** a screen error, and it is the correct "
            "recall §c.5-2/-3 intends — reported honestly at both grains, metric "
            "unbent (rules 1/11). The false-retire and reversal results are "
            "unaffected."
        )
        L.append("")
    if ret_is.get("reversal_rows"):
        L.append(
            f"> **Reversal exclusion (§c.5-1):** {exp} GW of model nuclear "
            "retirement is information-set-correct (mandated by an instrument "
            "public ≤ V) but reality-reversed by a post-V counter-instrument, so "
            "it is **excluded from IS-2020 false-retire** and reported as "
            "`reversal_exposure_gw`. Raw scoring keeps it as false-retire (the unit "
            "runs today). Reversing instrument(s): "
            + "; ".join(
                f"{r['unit_name']} ({r['unit_id']})" for r in ret_is["reversal_rows"]
            )
            + " — "
            + (
                ret_is["reversal_instruments"][0]
                if ret_is["reversal_instruments"]
                else ""
            )
            + "."
        )
        L.append("")
    # Per-channel table.
    L.append("Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):")
    L.append("")
    L.append(
        "| channel | retired GW | false-retire GW | recall (matched / big-actual) |"
    )
    L.append("|---|--:|--:|--:|")
    n_big = channels.get("_n_big_actual", 0)
    for c in CHANNEL_ORDER:
        if c not in channels:
            continue
        d = channels[c]
        L.append(
            f"| {c} | {d['retired_gw']} | {d['false_retire_gw']} | "
            f"{d['recall_matched']}/{n_big} |"
        )
    for c in channels:
        if c in CHANNEL_ORDER or c.startswith("_"):
            continue
        d = channels[c]
        L.append(
            f"| {c} | {d['retired_gw']} | {d['false_retire_gw']} | "
            f"{d['recall_matched']}/{n_big} |"
        )
    L.append("")
    if add_is.get("restart_excluded_gw", 0.0) or add_is.get("note"):
        L.append(f"> **Additions (§c.5-2):** {add_is['note']}")
        L.append("")
    return "\n".join(L)


def render_release_precision_note(prp: dict | None) -> list[str]:
    """Render the reported-only plant-grain release-precision block (capx D55).

    One blockquote line: window precision for the economic channel (the
    selection question) and for all channels, then the per-year economic
    readings. Absent on a score produced before the row existed → nothing.
    """
    if not prp:
        return []

    def _pct(block: dict) -> str:
        p = block.get("precision")
        return "—" if p is None else format(p, ".1%")

    def _mw(block: dict) -> str:
        return (
            f"{block.get('released_mw_at_real_exit_plants', 0.0):,.0f} / "
            f"{block.get('released_mw', 0.0):,.0f} MW"
        )

    w = prp.get("window", {})
    econ, alls = w.get("economic", {}), w.get("all", {})
    per_year = ", ".join(
        f"{y}: {_pct(v.get('economic', {}))} ({_mw(v.get('economic', {}))})"
        for y, v in sorted(prp.get("per_year", {}).items())
    )
    no_id = float(econ.get("released_mw_no_plant_identity", 0.0) or 0.0)
    return [
        "> **Plant-grain release precision (D32 R4, reported only — no band, no "
        "verdict):** of the MW the model released, the share landing at a plant "
        "(same plant code + fuel) that really exited in the window. Economic "
        f"channel **{_pct(econ)}** ({_mw(econ)}); all channels {_pct(alls)} "
        f"({_mw(alls)}); real-exit plant set {prp.get('n_real_exit_plants', 0)}. "
        f"Economic by year — {per_year or '—'}."
        + (
            f" {no_id:,.0f} MW released without plant identity (zone aggregate) "
            "counts as a miss."
            if no_id > 0.0
            else ""
        )
        + " A perfect selector reads 100 %; a random one reads the real exit "
        "rate of the retained MW (D32 §2.3: 13.5 % released vs 14.1 % retained "
        "on D31).",
        "",
    ]


def append_rescore(report_path: Path, section: str) -> None:
    """Append the re-score section to an existing report, preserving the original.

    Idempotent on the section marker: a prior IS-2020 re-score block for the same
    day is replaced rather than stacked, so re-running the scorer does not grow
    the file without bound."""
    marker = "## IS-2020 re-score (T-R8"
    body = report_path.read_text() if report_path.exists() else ""
    idx = body.find("\n---\n\n" + marker)
    if idx == -1:
        idx = body.find(marker)
        if idx != -1:  # marker without the divider prefix — trim from there
            idx = body.rfind("\n", 0, idx)
    if idx != -1:
        body = body[:idx].rstrip() + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(body.rstrip() + "\n" + section.rstrip() + "\n")


def _rescore(bundle: Path, report: Path | None) -> int:
    """T-R8 re-score: recompute retirements (raw + IS-2020 + per-channel) on the
    committed bundle with the current RD-5 actuals, preserve the existing
    ``co2``/``baselines`` (CO2 needs the uncommitted dispatch parquets — RD-5
    changes neither), update ``score.json``, and append the re-score section to
    the report. No LP is solved."""
    meta = json.loads((bundle / "meta.json").read_text())
    iso, variant = meta["iso"], meta["variant"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret = model_retirements(ledgers)
    madd = model_additions(ledgers, basis=ADDITIONS_BASIS_DECISION)
    madd_cod = model_additions(ledgers, basis=ADDITIONS_BASIS_COD)

    solved = load_solved_scenario_config(bundle)
    reach = classify_exit_reachability(
        iso,
        actuals,
        vintage_cutoff=vintage_cutoff_of(meta, solved),
        solved_config=solved,
    )
    ret = score_retirements(mret, actuals, reach)  # raw, RD-5 actuals
    add = score_additions(madd, actuals, basis=ADDITIONS_BASIS_DECISION)
    add_cod = score_additions(madd_cod, actuals, basis=ADDITIONS_BASIS_COD)
    add_basis = additions_basis_record(
        ledgers, ADDITIONS_BASIS_DECISION, load_solved_config(bundle)
    )
    reversal_set = load_reversal_set(iso)
    ret_is = score_retirements_is2020(mret, actuals, reversal_set, reach)
    channels = score_channels(mret, actuals)
    add_is = additions_is2020(madd, actuals)

    score_path = cache_dir / "score.json"
    score = json.loads(score_path.read_text()) if score_path.exists() else {}
    score.update(
        {
            "iso": iso,
            "variant": variant,
            "scored_years": list(SCORED_YEARS),
            "retirements": ret,
            "additions": add,
            "additions_cod_basis": add_cod,
            "additions_basis": add_basis,
            "retirements_is2020": ret_is,
            "retirement_channels": channels,
            "additions_is2020": add_is,
            "is2020_cutoff": IS2020_CUTOFF.isoformat(),
            "bands": BANDS,
            "rescore": {
                "task": "T-R8",
                "note": (
                    "IS-2020 scoring hygiene (RC-0B §c.5) — raw + IS-2020 + "
                    "per-channel. No re-solve; RD-5 actuals; co2/baselines "
                    "preserved (unchanged by RD-5)."
                ),
                "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }
    )
    score.setdefault("co2", {"model": {}, "actual": {}})
    score.setdefault("baselines", {"announced": baseline_announced(iso)})
    score_path.write_text(json.dumps(score, indent=2))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if report is None:
        report = _find_report(iso, variant, bundle.name)
    if report is not None:
        section = render_rescore_section(iso, ret, ret_is, channels, add_is, stamp)
        append_rescore(report, section)

    fr, fr_is = ret["false_retire"], ret_is["false_retire"]
    print(
        f"[rescore] {iso} {bundle.name}: raw false-retire {fr['false_gw']} GW "
        f"({fr['band']}) → IS-2020 {fr_is['false_gw']} GW ({fr_is['band']}); "
        f"reversal_exposure {ret_is.get('reversal_exposure_gw', 0.0)} GW"
    )
    print(f"[rescore] score.json: {score_path}")
    print(f"[rescore] report:     {report}")
    return 0


def _find_report(iso: str, variant: str, run_id: str) -> Path | None:
    """Locate the committed report for a bundle: newest ``<run_id>-<date>.md``."""
    rdir = Path("docs/hindcast-reports")
    cands = sorted(rdir.glob(f"{run_id}-*.md"))
    if cands:
        return cands[-1]
    cands = sorted(rdir.glob(f"{iso.lower()}-2021-2025-{variant}-*.md"))
    return cands[-1] if cands else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path, required=True, help="run_capacity_hindcast out-dir."
    )
    parser.add_argument(
        "--report-dir", type=Path, default=Path("docs/hindcast-reports")
    )
    parser.add_argument(
        "--rescore",
        action="store_true",
        help=(
            "T-R8 IS-2020 re-score: recompute retirements (raw + IS-2020 + "
            "per-channel) on the committed bundle, preserve co2/baselines, and "
            "APPEND a re-score section to the existing report (no re-solve)."
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Existing report to append the --rescore section to (default: auto-locate).",
    )
    parser.add_argument(
        "--flip-gate-extras",
        action="store_true",
        help=(
            "FF-1A scorer-side extras (no re-solve): T-R10 no-inversion guard "
            "(raw + IS-2020), LOYO folds within 2023-2025, and BLK-10 "
            "reserve-backstop fired MW — computed from the committed evolution "
            "ledgers + RD-5 actuals, merged into score.json."
        ),
    )
    args = parser.parse_args(argv)

    if args.flip_gate_extras:
        return _flip_gate_extras(args.bundle)

    if args.rescore:
        return _rescore(args.bundle, args.report)

    meta = json.loads((args.bundle / "meta.json").read_text())
    iso, variant = meta["iso"], meta["variant"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():  # bundle moved: re-derive under --bundle
        cache_dir = args.bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret = model_retirements(ledgers)
    # D-9(ii): the DECISION basis is the graded instrument; the COD basis is
    # computed alongside so both are comparable within this one score.json.
    madd = model_additions(ledgers, basis=ADDITIONS_BASIS_DECISION)
    madd_cod = model_additions(ledgers, basis=ADDITIONS_BASIS_COD)

    solved = load_solved_scenario_config(args.bundle)
    reach = classify_exit_reachability(
        iso,
        actuals,
        vintage_cutoff=vintage_cutoff_of(meta, solved),
        solved_config=solved,
    )
    ret = score_retirements(mret, actuals, reach)
    # Policy-saved annotation (default path, owner directive 2026-08-22): the
    # IS-<V> reversal-exclusion lane is computed alongside the raw pass on
    # EVERY score, not only under --rescore, so a bundle whose announced
    # channel executed exits that were later reversed by policy (Byron/Dresden
    # under IL CEJA's CMC) carries the note in its own score.json instead of
    # reading as unexplained model error. Raw stays the graded instrument;
    # both are reported side by side (RC-0B §c.5 — quoting only the
    # flattering one is scoring abuse). V is the run's own vintage cutoff.
    run_cutoff = vintage_cutoff_of(meta, solved)
    reversal_set = load_reversal_set(iso, cutoff=run_cutoff)
    ret_is = score_retirements_is2020(mret, actuals, reversal_set, reach)
    add = score_additions(madd, actuals, basis=ADDITIONS_BASIS_DECISION)
    add_cod = score_additions(madd_cod, actuals, basis=ADDITIONS_BASIS_COD)
    add_basis = additions_basis_record(
        ledgers, ADDITIONS_BASIS_DECISION, load_solved_config(args.bundle)
    )
    co2 = {
        "model": {str(k): v for k, v in model_co2_by_year(cache_dir).items()},
        "actual": {str(k): v for k, v in actual_co2_by_year(iso).items()},
        "actual_basis": actual_co2_basis(iso),
    }
    baselines = {"announced": baseline_announced(iso)}

    score = {
        "iso": iso,
        "variant": variant,
        "scored_years": list(SCORED_YEARS),
        "retirements": ret,
        # The information-set lane (§c.5-1 reversal exclusion at the run's own
        # vintage cutoff), always present so policy-saved exits are annotated
        # in the same artifact as the raw grade they inflate.
        "retirements_is": ret_is,
        "is_cutoff": run_cutoff.isoformat(),
        "additions": add,
        "additions_cod_basis": add_cod,
        "additions_basis": add_basis,
        "co2": co2,
        "baselines": baselines,
        "bands": BANDS,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (cache_dir / "score.json").write_text(json.dumps(score, indent=2))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Name the report after the bundle's run id (the out-dir name), so probe
    # arms of one ISO/variant scored the same day (e.g. the CR-3.1
    # -p2c-elcc / -p2c-base before/after pair) never overwrite each other;
    # falls back to the legacy iso-window-variant stem for bare dirs.
    run_id = args.bundle.name or f"{iso.lower()}-2021-2025-{variant}"
    report_path = args.report_dir / f"{run_id}-{stamp}.md"
    write_report(
        iso,
        variant,
        meta,
        ret,
        add,
        co2,
        baselines,
        report_path,
        add_cod,
        add_basis,
        ret_is=ret_is,
        is_cutoff=run_cutoff.isoformat(),
    )

    print(
        f"[score] {iso} {variant}: thermal-retire band {ret['total_gw']['band']}, "
        f"recall band {ret['unit_recall_gt300']['band']}"
    )
    if ret_is.get("reversal_exposure_gw", 0.0) > 0.0:
        print(
            f"[score] policy-saved announced exits: "
            f"{ret_is['reversal_exposure_gw']} GW retired on announced dates "
            f"later reversed by {'; '.join(ret_is['reversal_instruments']) or 'policy'} "
            f"— false-retire {ret['false_retire']['false_gw']} GW raw -> "
            f"{ret_is['false_retire']['false_gw']} GW net of reversals "
            f"(see the report's information-set note)"
        )
    print(f"[score] score.json: {cache_dir / 'score.json'}")
    print(f"[score] report:     {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
