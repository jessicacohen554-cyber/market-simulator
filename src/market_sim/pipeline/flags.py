"""Declarative backcast flag registry (refactor-consolidation plan §5).

The backcast flag surface is encoded three times — the ~232-flag argparse
group in ``scripts/run_calibration_full.py``, the ~200-kwarg ``run_year``
signature, and the ``backcast_config`` build — and the ERCOT-65 recorder
defect class is exactly what that triplication breeds: a flag whose CLI
spelling, solve kwarg, and recorded ``run_config`` name drift apart until
what the LP solved with is not what the audit trail says.

This module is the single declarative table replacing the hand-written
encodings **incrementally, one flag family at a time**. Each
:class:`FlagSpec` row records the full journey of one flag:

``cli`` spelling(s) → argparse ``dest`` → ``solve_and_persist`` kwarg
(``solve_param``) → ``ScenarioConfig`` field (``config_field``) → the
``meta.json`` recorded name (``recorded_name``, when it differs).

From the table this module GENERATES:

* the argparse definitions (:func:`add_flag_arguments`) — byte-equivalent
  option strings, dests, defaults, actions, and help text to the
  hand-written originals they replace;
* the ``solve_and_persist`` kwarg dict (:func:`solve_kwargs_from_args`) for
  every row that maps to a direct solve kwarg (rows that ride an
  override-dict channel — ``prb_overrides`` — keep their hand-written
  channel plumbing and are marked ``channel=...``).

Each migrated family lands with a recorded-config fidelity test
(``tests/test_flag_registry.py``) pinning the parser defaults, the
dest→kwarg mapping, the ``ScenarioConfig`` field existence, and the
meta/recorded-name aliases — the structural fix for the ERCOT-65 class.

Migrated families so far: ``coal``. The remaining families (offer-surface,
storage, gas, interchange, …) migrate by moving their ``add_argument``
definitions into rows here, one family per change, each with its fidelity
test — never a bulk rewrite.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

__all__ = [
    "FlagSpec",
    "FLAG_REGISTRY",
    "add_flag_arguments",
    "solve_kwargs_from_args",
    "iter_family",
]


@dataclass(frozen=True)
class FlagSpec:
    """One backcast CLI flag's full journey, declaratively.

    Attributes:
        cli: Option strings, primary spelling first (aliases follow).
        dest: The argparse namespace attribute.
        kind: One of ``"float"`` (typed value flag), ``"bool_opt"``
            (``argparse.BooleanOptionalAction``), ``"store_true"``.
        default: The argparse default (``None`` valid for ``"float"``).
        help: The exact help text (byte-identical to the hand-written
            definition this row replaced).
        family: Flag family key (``"coal"``, ``"storage"``, …).
        solve_param: The ``solve_and_persist`` keyword this flag feeds, or
            ``None`` when the flag rides an override-dict channel instead.
        config_field: The ``ScenarioConfig`` field the value ultimately
            lands on (``None`` for pure plumbing flags).
        channel: The override-dict channel name for ``solve_param=None``
            rows (e.g. ``"prb_overrides"``) — their main-call plumbing stays
            hand-written until the channel itself is registry-generated.
        recorded_name: The ``meta.json`` key when it differs from
            ``solve_param`` (the capture/replay alias map).
    """

    cli: tuple[str, ...]
    dest: str
    kind: str
    default: object
    help: str
    family: str
    solve_param: str | None
    config_field: str | None
    channel: str | None = None
    recorded_name: str | None = None
    extra_argparse: dict = field(default_factory=dict)


_COAL_FLAGS: tuple[FlagSpec, ...] = (
    FlagSpec(
        cli=("--coal-lignite-mustrun",),
        dest="coal_lignite_mustrun",
        kind="float",
        default=None,
        help="Override mine-mouth lignite coal must-run %% (sweep knob).",
        family="coal",
        solve_param="coal_lignite_mustrun",
        config_field="coal_lignite_mustrun_override",
    ),
    FlagSpec(
        cli=("--coal-prb-mustrun",),
        dest="coal_prb_mustrun",
        kind="float",
        default=None,
        help="Override PRB coal must-run %% (sweep knob).",
        family="coal",
        solve_param="coal_prb_mustrun",
        config_field="coal_prb_mustrun_override",
    ),
    FlagSpec(
        cli=("--coal-prb-passthrough",),
        dest="coal_prb_passthrough",
        kind="float",
        default=1.0,
        help="PRB above-must-run fuel passthrough (1.0 = off).",
        family="coal",
        solve_param="coal_prb_passthrough",
        config_field="coal_prb_passthrough",
    ),
    FlagSpec(
        cli=("--coal-prb-sigmoid", "--prb-passthrough-sigmoid"),
        dest="coal_prb_sigmoid",
        kind="bool_opt",
        default=True,
        help="Gas-key the PRB passthrough: a logistic of the monthly gas "
        "price replaces the flat --coal-prb-passthrough (deep discount "
        "when gas is cheap, none/markup when dear). Params resolve "
        "from the per-ISO COAL_SIGMOID_DEFAULTS curve; no curve for "
        "the ISO = flat passthrough. (--prb-passthrough-sigmoid is "
        "the legacy spelling.)",
        family="coal",
        solve_param="coal_prb_passthrough_sigmoid",
        config_field="coal_prb_passthrough_sigmoid",
    ),
    FlagSpec(
        cli=("--coal-mustrun-per-plant",),
        dest="coal_mustrun_per_plant",
        kind="bool_opt",
        default=True,
        help="Use per-plant CAMPD-derived coal must-run floors "
        "(fleet.COAL_MUSTRUN_BY_PLANT) instead of uniform lignite/PRB "
        "must-run overrides.",
        family="coal",
        solve_param="coal_mustrun_per_plant",
        config_field="coal_mustrun_per_plant",
    ),
    FlagSpec(
        cli=("--coal-drop-pof",),
        dest="coal_drop_pof",
        kind="bool_opt",
        default=True,
        help="Drop the statistical planned-outage (POF) derate on coal "
        "(planned maintenance comes from the historic outage overlay); "
        "keep WEFOR in non-summer months and the derate all year.",
        family="coal",
        solve_param="coal_drop_pof",
        config_field="coal_drop_pof",
    ),
    FlagSpec(
        cli=("--coal-mustrun-online-pmin",),
        dest="coal_mustrun_online_pmin",
        kind="bool_opt",
        default=False,
        help="Size the coal must-run band to the measured online-net-MW "
        "synchronization Pmin (thermal_tranches mustrun_online_pct) "
        "instead of the take-or-pay contract floor. Pairs with "
        "--coal-sync-srmc-tranche to hold units synchronized at their "
        "measured online minimum.",
        family="coal",
        solve_param="coal_mustrun_online_pmin",
        config_field="coal_mustrun_online_pmin",
    ),
    FlagSpec(
        cli=("--coal-sync-srmc-tranche",),
        dest="coal_sync_srmc_tranche",
        kind="bool_opt",
        default=False,
        help="Split the coal online-Pmin band into a fuel-free contracted "
        "_mustrun tranche and a full-SRMC _sync tranche, and force both "
        "on (scaled by the measured online fraction) so coal holds at "
        "its measured synchronization floor instead of price-following "
        "to zero. Requires --coal-mustrun-online-pmin.",
        family="coal",
        solve_param="coal_sync_srmc_tranche",
        config_field="coal_sync_srmc_tranche",
    ),
    FlagSpec(
        cli=("--coal-sync-ensemble-level",),
        dest="coal_sync_ensemble_level",
        kind="bool_opt",
        default=False,
        help="Place the coal synchronization floor as pmin x online_frac in "
        "EVERY hour (the continuous-relaxation image of the measured "
        "commitment) instead of the full pmin on the top online_frac "
        "fraction of hours by the window series. Same measured annual "
        "synchronized MWh; REPLACES the window, never stacks on it. "
        "Requires --coal-sync-srmc-tranche.",
        family="coal",
        solve_param="coal_sync_ensemble_level",
        config_field="coal_sync_ensemble_level",
    ),
    FlagSpec(
        cli=("--coal-bit-sigmoid",),
        dest="coal_bit_sigmoid",
        kind="bool_opt",
        default=False,
        help="Gas-key the bituminous coal passthrough: above-must-run bit "
        "tranches get a fuel discount when gas is cheap and a markup "
        "when dear (coal_bit_passthrough_* params), tracking the "
        "bit-vs-gas-CC merit-order crossover. Off = full fuel cost.",
        family="coal",
        solve_param="coal_bit_sigmoid",
        config_field="coal_bit_passthrough_sigmoid",
        recorded_name="coal_bit_passthrough_sigmoid",
    ),
    # Marginal-coal measured-SRMC offer bound: the econ*/peak coal tranches
    # buy fuel at market, so their offers are clamped to >= full measured
    # delivered fuel cost (passthrough >= 1.0); the committed/must-run bands
    # keep the contracted take-or-pay discount. Removes the sigmoid's fitted
    # discount from the marginal tranches (FINDING-miso-burndown-2026-07.md
    # Evidence 2). Off by default (existing keepers unchanged).
    FlagSpec(
        cli=("--coal-econ-srmc-bound",),
        dest="coal_econ_srmc_bound",
        kind="bool_opt",
        default=False,
        help="Clamp marginal (econ*/peak) coal tranche fuel passthrough to "
        ">= 1.0 so no marginal coal offer sits below the plant's "
        "measured incremental delivered SRMC. Committed/must-run bands "
        "keep their take-or-pay discount.",
        family="coal",
        solve_param="coal_econ_srmc_bound",
        config_field="coal_econ_srmc_bound",
    ),
    # ERCOT-111 measured incremental-heat-rate floor on the COAL econ ramp: a
    # coal econ band may carry a MARKUP above its physical basis but never a bid
    # BELOW it, so econ_low/econ_high are clamped up to the ISO's own measured
    # CAMPD marginal heat rate for COAL (derive_campd_marginal_hr artifact).
    # Removes a fitted degree of freedom; adds no tunable.
    FlagSpec(
        cli=("--coal-econ-marginal-hr-bound",),
        dest="coal_econ_marginal_hr_bound",
        kind="bool_opt",
        # TRI-STATE (default None, not False): the floor became the ERCOT
        # backcast default-ON at the ercot-115 promotion. A False default would
        # make every CLI run pass an explicit False and silently SCRUB that
        # per-ISO default, so the promotion would never take effect on the
        # calibration path. None = keep the per-ISO backcast_config default;
        # --coal-econ-marginal-hr-bound / --no-coal-econ-marginal-hr-bound force
        # it on/off (BooleanOptionalAction).
        default=None,
        help="Floor each coal class's econ_low/econ_high offer-curve band at "
        "the ISO's own MEASURED CAMPD marginal (incremental) heat rate for "
        "COAL (data/raw/reference/<iso>_campd_marginal_hr_summary.csv), so no "
        "coal econ tranche bids below the physical cost of its next MWh. "
        "Markups above the measured basis, the committed/must-run take-or-pay "
        "bands and the peak scarcity wall are untouched.",
        family="coal",
        solve_param="coal_econ_marginal_hr_bound",
        config_field="coal_econ_marginal_hr_bound",
    ),
    FlagSpec(
        cli=("--coal-lignite-sigmoid",),
        dest="coal_lignite_sigmoid",
        kind="bool_opt",
        default=False,
        help="Gas-key the lignite coal passthrough: above-must-run lignite "
        "tranches get a fuel discount when gas is cheap (mine-mouth "
        "take-or-pay fixed costs are sunk) rising to full cost when "
        "dear (coal_lignite_passthrough_* params), tracking the "
        "lignite-vs-gas-CC merit-order crossover. Off = full fuel cost.",
        family="coal",
        solve_param=None,
        config_field="coal_lignite_passthrough_sigmoid",
        channel="prb_overrides",
    ),
    FlagSpec(
        cli=("--coal-sub-sigmoid",),
        dest="coal_sub_sigmoid",
        kind="bool_opt",
        default=False,
        help="Gas-key the subbituminous coal passthrough on its own curve "
        "(coal_sub_passthrough_* params / per-ISO defaults). Off = full "
        "fuel cost.",
        family="coal",
        solve_param=None,
        config_field="coal_sub_passthrough_sigmoid",
        channel="prb_overrides",
    ),
    FlagSpec(
        cli=("--coal-waste-sigmoid",),
        dest="coal_waste_sigmoid",
        kind="bool_opt",
        default=False,
        help="Gas-key the waste-coal passthrough on its own curve "
        "(coal_waste_passthrough_* params / per-ISO defaults). Off = "
        "full fuel cost.",
        family="coal",
        solve_param=None,
        config_field="coal_waste_passthrough_sigmoid",
        channel="prb_overrides",
    ),
    FlagSpec(
        cli=("--coal-warm-committed",),
        dest="coal_warm_committed",
        kind="store_true",
        default=False,
        help="Exempt CAMPD coal committed tranches from the P1 "
        "startup-amortization markup when the plant has a must-run "
        "floor: the mustrun tranche keeps the boiler online, so "
        "committed-band dispatch is a hot-unit ramp, not a cold start. "
        "Off (default) keeps the legacy $100/MW coal start markup, "
        "which prices the committed band above the econ ramp (the "
        "run-97b inversion).",
        family="coal",
        solve_param=None,
        config_field="coal_warm_committed",
        channel="prb_overrides",
    ),
)

FLAG_REGISTRY: dict[str, tuple[FlagSpec, ...]] = {
    "coal": _COAL_FLAGS,
}


def iter_family(family: str) -> tuple[FlagSpec, ...]:
    """Return the registry rows for one flag family (KeyError if unknown)."""
    return FLAG_REGISTRY[family]


def add_flag_arguments(parser: argparse.ArgumentParser, family: str) -> None:
    """Generate a family's argparse definitions from the registry.

    Byte-equivalent to the hand-written ``add_argument`` calls each row
    replaced: same option strings (aliases included), same ``dest``, same
    default, same action/type, same help text. Only the position in
    ``--help`` output changes (the family renders as one contiguous run).
    """
    for spec in iter_family(family):
        kwargs: dict = {"help": spec.help, **spec.extra_argparse}
        if spec.kind == "float":
            kwargs.update(type=float, default=spec.default)
        elif spec.kind == "bool_opt":
            kwargs.update(action=argparse.BooleanOptionalAction, default=spec.default)
        elif spec.kind == "store_true":
            kwargs.update(action="store_true")
        else:  # pragma: no cover - registry authoring error
            raise ValueError(f"unknown FlagSpec.kind {spec.kind!r}")
        # argparse derives the dest from the primary spelling; pass it
        # explicitly only when it differs (keeps generated calls minimal
        # and mirrors the hand-written originals).
        derived = spec.cli[0].lstrip("-").replace("-", "_")
        if spec.dest != derived:
            kwargs["dest"] = spec.dest
        parser.add_argument(*spec.cli, **kwargs)


def solve_kwargs_from_args(args: argparse.Namespace, family: str) -> dict:
    """Return the family's direct ``solve_and_persist`` kwargs from ``args``.

    Covers every row with a ``solve_param``; rows riding an override-dict
    channel (``channel=...``) are excluded — their plumbing stays with the
    channel until the channel itself is registry-generated.
    """
    return {
        spec.solve_param: getattr(args, spec.dest)
        for spec in iter_family(family)
        if spec.solve_param is not None
    }
