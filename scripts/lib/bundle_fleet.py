"""Rebuild a calibration bundle's fleet exactly as it solved — no LP.

Every PJM (and CAISO/ERCOT) no-LP pre-check works the same way: take a
registered bundle's ``meta.json``, hand it back to
``run_calibration.run_year(..., fleet_only=True)``, and measure the arms on the
fleet/offer arrays the keeper actually built. The pattern is only sound if the
reconstruction carries **every** flag the bundle recorded.

``scripts/data/derive_pjm_ordc_overlay._run_year_kwargs`` forwards a
hand-curated subset — the keys the ORDC overlay happened to need. On the
pjm-121 PJM keeper that subset drops **38 non-default ``run_year`` flags**,
among them ``tranche_startup_amortization`` / ``_measured_runs`` /
``_conditional_runs`` (the pjm-103 start-cost pricing that owns the CT stack),
``ct_netload_drag`` + ``ct_drag_overrides`` and ``gas_st_netload_drag`` +
``gas_st_drag_overrides`` (the drag mechanisms that own the CT and ST_GAS
offers), ``ct_intermediate_split``, ``coal_sync_srmc_tranche`` and
``coal_mustrun_online_pmin``. A probe run on that reconstruction measures a
fleet the keeper never solved.

:func:`full_run_year_kwargs` is the widened replacement (first written as
``scripts/probes/pjm123_composite_precheck.full_run_year_kwargs``, promoted
here by pjm-124 per the frontier handoff §5): it keeps the proven base mapping
— which carries the renamed keys, e.g. ``prb_overrides`` <-
``coal_prb_sigmoid_overrides`` — and then overlays every remaining ``meta`` key
that ``run_year`` actually accepts. :func:`reconstruct_bundle_fleet` wraps the
whole reconstruction, including the year-chain gas-price fallback and the
fidelity guard that hard-fails on a dropped gate.

Callers must have the repo root on ``sys.path`` (see :func:`ensure_probe_path`)
so ``run_calibration`` and ``derive_pjm_ordc_overlay`` resolve as canonical
``scripts.*`` package modules — never as second bare-name copies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: Repo root (``scripts/lib/bundle_fleet.py`` -> ``parents[2]``).
REPO = Path(__file__).resolve().parents[2]

#: ``run_year`` takes these four positionally — never re-passed from ``meta``.
POSITIONAL = frozenset({"year", "iso", "hours", "gas_price"})

#: Flags whose loss silently changes what a PJM probe measures. Any of these
#: recorded ON in a bundle's ``meta.json`` must survive into the reconstructed
#: ``ScenarioConfig`` — the pjm-123 fidelity guard, generalized. The offer-path
#: gates own the merit order the arms diff against; the reserve gates own the
#: co-optimization layout a reserve-supply probe measures (pjm-124).
DEFAULT_REQUIRED_FLAGS: tuple[str, ...] = (
    "pjm_offer_midcurve_conditional",
    "tranche_startup_amortization",
    "tranche_startup_measured_runs",
    "tranche_startup_conditional_runs",
    "ct_netload_drag",
    "gas_st_netload_drag",
    "energy_reserve_coopt",
    "pjm_reserve_pergen",
)

#: Sequence-valued ``meta`` keys compared element-wise by the fidelity guard —
#: a silently-narrowed scope is as damaging as a dropped boolean.
DEFAULT_REQUIRED_SEQUENCES: tuple[str, ...] = ("pjm_offer_midcurve_segments",)


def ensure_probe_path() -> None:
    """Put the repo, ``src``, ``scripts`` and ``scripts/data`` on ``sys.path``.

    The repo root itself must be present so ``scripts.lib.clean_io`` resolves as
    a package — without it the ``data/clean`` readers silently fall back and the
    measured overlays (east interface cut, ramp capability) refuse to load.
    """
    for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)


def full_run_year_kwargs(meta: dict) -> dict:
    """Rebuild a bundle's ``run_year`` kwargs from EVERY flag its meta records.

    Since caiso-244 this is a thin wrapper over
    :func:`scripts.replay_keeper.run_year_kwargs` — the strict, remapping
    ``meta.json`` -> ``solve_and_persist`` reconstruction (``build_kwargs``)
    restricted to the subset ``solve_and_persist`` hands to ``run_year``, under
    ``run_year``'s own names. One mapping, one place: the hand-curated base
    subset this function used to start from (``derive_pjm_ordc_overlay
    ._run_year_kwargs``) and the by-parameter-name overlay it added are both
    retired here, because a by-name overlay silently drops every key whose
    ``run_year`` kwarg is spelled differently — the caiso-243 §7.3 instrument
    defect (``coal_prb_sigmoid_overrides`` -> ``prb_overrides`` and its 36
    structural flags). Measured on all six designated keepers before the
    switch (caiso-244), the old path and the strict path agreed on every
    recorded key except ``None`` vs ``{}`` for empty override dicts, which
    ``run_year`` treats identically — so existing callers are unchanged in
    effect and now fail loudly instead of silently on a future rename.

    Args:
        meta: The bundle's ``meta.json``.

    Returns:
        The ``run_year`` kwargs, with ``fleet_only=True`` (no LP) and
        ``ttc_overrides={}`` (the solve's own value) — ready to splat after the
        four positional arguments.
    """
    ensure_probe_path()
    from scripts.replay_keeper import run_year_kwargs

    kwargs = run_year_kwargs(meta)
    kwargs["ttc_overrides"] = {}
    kwargs["fleet_only"] = True
    return kwargs


def clear_fleet_caches() -> None:
    """Drop the fleet-builder caches that would defeat a second in-process rebuild.

    ``campd_bins._CAMPD_BINS_CACHE`` memoizes the curated-CSV bin frame on a key
    that does not see patched literals or monkeypatched seams, and several
    loaders in the same module are ``lru_cache``d. A probe that rebuilds the
    same year twice in one process (a keeper pass and a patched variant) must
    clear both between passes or the second rebuild reads the first's fleet.
    Promoted from the caiso-240 census probe (``_clear_fleet_caches``) so
    every variant-diff probe shares one implementation.
    """
    from market_sim.data.fleet import campd_bins as cb

    cb._CAMPD_BINS_CACHE.clear()
    for name in dir(cb):
        fn = getattr(cb, name, None)
        if callable(fn) and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def bundle_gas_price(meta: dict, year: int) -> float:
    """Return the gas price the bundle solved ``year`` on.

    A year-chain bundle's merged ``meta`` records ``gas_prices`` for the LAST
    invocation only, so an earlier year falls back to the same Henry Hub actual
    ``run_calibration_full`` itself resolves for that year — the value the chain
    solved on, not a guess.

    Args:
        meta: The bundle's ``meta.json``.
        year: The solve year.

    Returns:
        The gas price in $/MMBtu.
    """
    price = (meta.get("gas_prices") or {}).get(str(year))
    if price is not None:
        return float(price)
    ensure_probe_path()
    from scripts import run_calibration_full as rcf

    return float(rcf._henry_hub_actual(rcf._load_reference(), year))


def assert_reconstruction_fidelity(
    meta: dict,
    config,
    required_flags: tuple[str, ...] = DEFAULT_REQUIRED_FLAGS,
    required_sequences: tuple[str, ...] = DEFAULT_REQUIRED_SEQUENCES,
) -> None:
    """Hard-fail when the reconstruction dropped a gate the bundle recorded.

    A silent reconstruction drift must be an error, not a quiet null result that
    makes every measured delta meaningless.

    Args:
        meta: The bundle's ``meta.json``.
        config: The reconstructed ``ScenarioConfig``.
        required_flags: Boolean gates that must survive when recorded ON.
        required_sequences: Sequence-valued keys compared element-wise.

    Raises:
        SystemExit: On any dropped gate or narrowed scope.
    """
    for field in required_flags:
        if bool(meta.get(field, False)) and not bool(getattr(config, field, False)):
            raise SystemExit(
                f"reconstruction dropped {field} (bundle records it ON) — the "
                "keeper arm would not be the keeper"
            )
    for field in required_sequences:
        if field not in meta:
            continue
        got = list(getattr(config, field, None) or ())
        want = list(meta.get(field) or ())
        if got != want:
            raise SystemExit(
                f"reconstructed {field} {got!r} != the bundle's {want!r} — the "
                "keeper arm would not be the keeper"
            )


def reconstruct_bundle_fleet(
    bundle: Path,
    year: int,
    required_flags: tuple[str, ...] = DEFAULT_REQUIRED_FLAGS,
    required_sequences: tuple[str, ...] = DEFAULT_REQUIRED_SEQUENCES,
    verbose: bool = True,
) -> tuple[dict, dict]:
    """Rebuild ``bundle``'s ``year`` fleet with no LP, fidelity-guarded.

    Args:
        bundle: The calibration bundle directory (carries ``meta.json``).
        year: The solve year to reconstruct.
        required_flags: Boolean gates that must survive (see
            :func:`assert_reconstruction_fidelity`).
        required_sequences: Sequence-valued keys compared element-wise.
        verbose: Print a one-line reconstruction banner.

    Returns:
        ``(state, meta)`` — ``run_year``'s ``fleet_only`` state dict (``fleet``,
        ``fleet_arrays``, ``config``, ``mc_base``, ``demand``, the renewable
        capacity/CF arrays) and the bundle's ``meta.json``.

    The rebuild also carries :data:`replay_keeper.DERIVED_RUN_YEAR_INPUTS` — the
    ``run_year`` inputs ``solve_and_persist`` derives from its own locals and
    the bundle therefore never records, recovered from the bundle's own
    sidecars by :func:`replay_keeper.derived_run_year_inputs`. Today that is
    ``inject_biomass_mustrun``, which ``run_year`` passes as
    ``drop_biomass_units``: without it the rebuild carries phantom biomass LP
    rows the scored solve never had (caiso-248), and the rebuilt fleet is then
    not row-aligned with the bundle's own per-unit artifacts. Measured on the
    CAISO 2024 keeper at caiso-285: 1,905 rebuilt rows against the solve's
    1,705, a strict superset of exactly 200 biomass rows, which broke the
    row alignment of ``hourly/p0_commitment_<year>.parquet`` and
    ``floors/<year>_P1.npz``. ``replay_keeper`` has documented this duty since
    caiso-248 (*"every fleet-only rebuild should splat this"*), but the
    SANCTIONED helper every such rebuild is supposed to go through did not,
    so the duty could not be discharged by using the sanctioned route.
    """
    ensure_probe_path()
    from scripts.replay_keeper import derived_run_year_inputs
    from scripts.run_calibration import run_year

    meta = json.loads((Path(bundle) / "meta.json").read_text())
    gas_price = bundle_gas_price(meta, year)
    if verbose:
        print(f"reconstructing {meta['iso']} {year} fleet from {bundle} (no LP) ...")
    state = run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        gas_price,
        **full_run_year_kwargs(meta),
        **derived_run_year_inputs(bundle, year),
    )
    assert_reconstruction_fidelity(
        meta, state["config"], required_flags, required_sequences
    )
    return state, meta
