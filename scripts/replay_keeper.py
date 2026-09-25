"""Byte-faithful re-solve of a committed calibration keeper from its bundle.

A keeper's ``meta.json`` is the authoritative snapshot of the keyword arguments
``run_calibration_full.solve_and_persist`` was called with (it is written from
those kwargs at solve time). This driver reads that snapshot and replays the
solve into the bundle directory, regenerating every output the registration
pipeline needs — crucially ``btm.parquet`` (the behind-the-meter CHP host steam
held out of the LP), which the parallel CAISO/PJM re-gates predate. The BTM
write is solve-invariant (``btm_twh = EIA-923 class total − grid dispatch`` and a
held-out CHP plant's grid dispatch is ~0), so the re-solve reproduces the
keeper's dispatch and only *adds* the BTM basis the original bundle lacked.

After the solve the driver regenerates ``legitimacy_diagnostics.json`` for the
output bundle through the same ``scripts/legitimacy_diagnostics.py`` post-step
the normal calibration path uses, so C8 always has a fresh committed artifact
to score (closes the ercot-193-disclosed replay-path gap).

The original ``meta.timestamp`` date is preserved so the dashboard run id
(``<date>-<shorthand>``) is unchanged — the re-solve fixes the keeper in place,
it does not mint a new run.

Usage:
    python scripts/replay_keeper.py results/calibration/<bundle> [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Reproducibility pin: a byte-faithful keeper replay must be basis-independent,
# so force the cross-year LP warm-start OFF regardless of the ambient
# environment. Cross-year warm-start is basis-neutral on the calibration path
# (objective/prices/total-gen bit-identical) but reshuffles marginal-tie
# dispatch by ~0.003%, which would make a replay's per-plant parquet differ from
# the cold-solved committed bundle and break the D-13 bench-repro byte-identity
# gate. ``solve_and_persist`` is called directly here (not via the CLI
# ``main()``), so it never sees the calibration CLI's default-ON gate.
# ``MARKET_SIM_P1_BASIS_SEED`` is pinned beside it since PERF-C S1
# (2026-09-20): the same-year P1 basis seed used to be armed INSIDE the
# cross-year gate, so the line above implied it off. ``pipeline.solve`` now
# gates it on its own env var, and the seed is the same warm-start class — it
# reshuffles marginal ties on the cold-rebuilt P1 a floor bridge routes to —
# so a byte-faithful replay must pin it explicitly or inherit it by accident.
DETERMINISM_ENV = {
    "MARKET_SIM_WARMSTART_XYEAR": "0",
    "MARKET_SIM_P1_BASIS_SEED": "0",
}

from scripts import run_calibration_full as rcf  # noqa: E402

# meta.json key -> solve_and_persist kwarg, where the names differ.
_REMAP = {
    "commitment_screen_coal": "screen_coal",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are not solve kwargs (provenance / derived / recorded only).
_IGNORE = {
    "timestamp",
    "gas_prices",
    "passes",
    "td_loss_factor",
    "shared_inputs",
    "git_sha",
    # Origin-durable basis anchor (run_calibration_full._basis_sha). Pure
    # provenance, written fresh by every solve_and_persist — a replay must
    # carry the REPLAY's basis, never the original's, so this is ignored on
    # the way in and (unlike the timestamp date) never restored on the way
    # out; see _restore_display_date (caiso-122 §1 / caiso-123).
    "basis_sha",
    "highspy_version",
    # Runtime environment block (python/platform + numerics stack versions).
    # Provenance only — never a solve kwarg. main() surfaces a mismatch as a
    # loud non-fatal WARNING; here it must be ignored so build_kwargs (and the
    # --reuse-solved comparator that calls it) does not treat it as unmapped.
    "environment",
    # Composite per-year recipe overlay (ercot-256, CONSUMED since ercot-260).
    # A composite bundle's meta.json carries ONE config — for ERCOT the
    # forward one — while its carve-out years solved under a different recipe.
    # This block records the EXACT per-year key overlay a replay needs, which
    # closes the two-config provenance defect that blocked ercot-254, -255 and
    # -259 (replay silently applying the forward config to a carve-out year).
    # It is not itself a solve_and_persist kwarg, so build_kwargs must skip it
    # exactly like "environment"; the overlay reaches the solve through
    # enforce_single_recipe_partition, which routes each key down the same two
    # channels --set uses. ercot-256 applied it by hand (--set); consuming it
    # automatically is the FIX, and it IS attempted here.
    "config_partition_overrides",
    "iso",
    "years",
    "hours",
    # --reuse-solved labeling block: which years a mixed bundle byte-copied
    # from which source bundle. Pure provenance — the recipe kwargs above are
    # complete regardless, and a replay of a mixed bundle re-solves every
    # year fresh (which is exactly what "reused years are not fresh
    # evidence" demands of a re-gate).
    "reuse",
    # Free-text note naming the model changes a bundle's session landed
    # (ercot-261 writes one). Recorded-only provenance in the same class as
    # "timestamp"/"git_sha"/"basis_sha" — it selects no mechanism and has no
    # solve_and_persist kwarg, so a replay carries the REPLAY's own note (the
    # --note flag) and never the original's. Ignored deliberately per this
    # guard's own instruction; verified to be the SOLE unmapped key of
    # ercot261_five_year_keeper, which it was blocking from replay entirely.
    "model_changes_note",
    # Composition provenance: {source bundle: [years it contributed]}, written
    # when a rule-32 [R-SHARD] parent composes per-year shard bundles into one
    # multi-year bundle. Pure provenance in the same class as "reuse" (which
    # records the same shape for --reuse-solved) — it names where a solved year
    # came from and selects no mechanism, so a replay re-solves every year fresh
    # off the recipe kwargs, which are complete on their own. NOT to be confused
    # with "config_partition_overrides" above: that key carries a per-year key
    # OVERLAY a replay must apply, and it is consumed, not dropped. A composite
    # whose years solved under different recipes therefore still carries the
    # overlay and is still replayed correctly; this key alone means only that
    # the bundle was assembled from shards. Ignored deliberately per this
    # guard's own instruction; it was the SOLE unmapped key of pjm_d4_2_TP /
    # pjm_d4_2_A, which it was blocking from replay entirely (pjm-d4-3).
    "composed_from",
}
# Recorded-only env-gated probe values: resolved inside backcast_config from
# env vars (ERCOT_ZONAL_GAS / ERCOT_WEST_NETLOAD_GAS /
# ERCOT_WEST_GAS_DELIVERED_FLOOR — no solve_and_persist kwarg exists, rule-24
# exception; see the meta-writer comment in run_calibration_full.py). The
# meta.json value is provenance. A kwargs replay can reproduce only the INERT
# state; a bundle that ARMED one must re-solve with the same env var, so
# build_kwargs hard-errors rather than silently dropping the mechanism.
_ENV_GATED_INERT: dict = {
    "ercot_zonal_gas_basis": False,
    "ercot_west_netload_gas_shape": False,
    "ercot_west_gas_delivered_floor": None,
}
# ScenarioConfig fields DELETED by rule-26 [R-DELETE] collapses AFTER some
# registered bundles solved: their meta.json still records the field, and the
# recorded value is provenance. Keyed field -> (owning_iso, unconditional
# value the collapse made the only behaviour). Outside the owning ISO the
# mechanism was never reachable (rule 25 [R-ISO-SCOPE]), so the recorded
# default is inert and the key is skipped; inside it, only a bundle recording
# the now-unconditional value replays at HEAD — the other polarity selected a
# basis that no longer parses, and its epoch note says "read, never
# replayed", so build_kwargs hard-errors rather than silently replaying a
# different mechanism.
_RULE26_DELETED_UNCONDITIONAL: dict[str, tuple[str, object]] = {
    # nyiso-136 collapse (cache.py epoch 2026-08-15): market-solar
    # cod_basis=True is now NYISO's only basis. First keeper meta carrying
    # the recorded key: pjm-162 inputclock (solved at c447199 while the
    # field lived; promoted pjm-163, 2026-08-16).
    "nyiso_solar_registry_cod_dates": ("NYISO", True),
    # miso-177 (2026-08-22): the transient session field that delivered the
    # measured-rho arm before the same-day owner ruling deleted the RHO_CLIP
    # floor globally (nyiso-151, decision-card option A) — the field was
    # removed in the same session's reconciliation, never reaching main.
    # True (the arm/keeper 2026-08-22-miso-177-rho-measured) is the
    # unconditional post-ruling behaviour: the seam consumes the measured
    # 0.1764 by default, so the recorded key replays byte-equivalently.
    # False (the control 2026-08-22-miso-177-control) selected the deleted
    # 0.5-floor basis and correctly hard-errors as historical-record-only —
    # the same non-replayability the owner's ruling gave every pre-ruling
    # MISO bundle, the miso-175 keeper included.
    "miso_online_rho_no_floor": ("MISO", True),
    # caiso-236 (2026-09-02) deleted `caiso_bidir_intertie` from ScenarioConfig
    # under rule 26 [R-DELETE] and registered it in
    # scenarios._CACHE_KEY_RETIRED_FIELDS, but did not extend THIS registry — so
    # every keeper meta recording the key became unmappable and build_kwargs
    # hard-errored, taking the keeper-replay guard family red on main (xiso-7
    # §7; seven tests across test_replay_keeper_strict, test_forecast_parity and
    # test_ff_readiness_battery). False is the unconditional post-deletion
    # behaviour: the field was off on the CAISO keeper AND off in the CAISO
    # defaults, i.e. unreachable in every shipped configuration. The inert SET is
    # declared because every keeper meta of all six ISOs records the key as None
    # — the tri-state CLI's "flag never set", which resolves to that same False
    # default — and not one records False literally; both drop safely.
    # A bundle that recorded True selected the
    # fitted 4,361 MW aggregate export cap that no longer exists at HEAD and
    # still hard-errors as historical-record-only — the miso-50..53 strictness
    # is preserved, not relaxed. Successor mechanism: caiso_per_hub_intertie.
    "caiso_bidir_intertie": ("CAISO", (False, None)),
}


def _rule26_inert(unconditional: object) -> tuple:
    """Return the recorded values that are INERT for a rule-26-deleted field.

    A registry entry declares either a single value or a TUPLE of them whose
    FIRST element is the canonical now-unconditional behaviour (the value the
    error messages name) and whose remaining elements are other recordings that
    resolve to it. The case that needs the tuple is ``None``: a tri-state CLI
    flag writes ``None`` into meta.json for "never set", which resolves to the
    field's default, so for a field whose default WAS the unconditional
    behaviour both ``None`` and the explicit value are inert. Declaring the set
    per field keeps that from becoming a blanket "None is always safe" rule,
    which would be false for a field whose default was the OTHER polarity.
    """
    return unconditional if isinstance(unconditional, tuple) else (unconditional,)


def _strip_rule26_from_override_dict(channel: str, overrides: dict, meta: dict) -> dict:
    """Drop rule-26-deleted fields recorded INSIDE a generic override dict.

    ``_RULE26_DELETED_UNCONDITIONAL`` is applied to top-level meta keys, but the
    same field can also reach ``ScenarioConfig`` through a generic
    override channel that is splatted with ``with_overrides(**d)`` —
    ``coal_prb_sigmoid_overrides`` is one, and NYISO keepers record ~33 flags in
    it. A field deleted from ``ScenarioConfig`` then raises ``TypeError`` from
    inside ``run_year`` no matter how carefully the top-level keys were mapped,
    which is what made the designated NYISO keeper unreplayable at HEAD
    (discovered nyiso-140).

    Applies the SAME polarity check as the top-level path rather than dropping
    blindly: a recorded value equal to the now-unconditional behaviour is inert
    and safely dropped; the other polarity selected a basis that no longer
    exists, so it hard-errors instead of silently replaying a different
    mechanism (the miso-50..53 strictness).

    Args:
        channel: The override-dict meta key, for the error message.
        overrides: The recorded override mapping.
        meta: The whole bundle meta (for the solve's ISO).

    Returns:
        *overrides* without the rule-26-deleted entries (a copy only when one
        was present, so the common path is unchanged).
    """
    hits = [k for k in overrides if k in _RULE26_DELETED_UNCONDITIONAL]
    if not hits:
        return overrides
    out = dict(overrides)
    for k in hits:
        owner_iso, unconditional = _RULE26_DELETED_UNCONDITIONAL[k]
        inert = _rule26_inert(unconditional)
        v = out.pop(k)
        if meta.get("iso") == owner_iso and v not in inert:
            raise SystemExit(
                f"bundle records the rule-26-deleted field {k}={v!r} inside "
                f"{channel} on an {owner_iso} solve: the basis that value "
                f"selected no longer exists at HEAD (the collapse made "
                f"{inert[0]!r} unconditional), so a kwargs replay would "
                "run a DIFFERENT mechanism than the bundle. Historical record "
                "— read, never replayed (see the cache.py epoch note)."
            )
    return out


def build_kwargs(meta: dict) -> dict:
    """Map a bundle's meta.json onto solve_and_persist's keyword arguments.

    STRICT: every meta key must map to a solve kwarg or be a curated
    provenance/recorded-only key — an unmapped key is a hard error, never a
    silent drop. This is the closure of the miso-50..53 regression class
    (recipes reconstructed from a lossy channel silently dropped the whole
    keeper structure; see the CLAUDE.md critical lesson and
    results/calibration/FINDING-miso-august-scarcity-2026-07.md §1): the
    meta.json replay is the ONLY sanctioned recipe reconstruction, and it
    refuses to lose structure quietly.
    """
    params = set(inspect.signature(rcf.solve_and_persist).parameters)
    kwargs: dict = {}
    unmapped: list[str] = []
    for k, v in meta.items():
        if k in _IGNORE:
            continue
        if k in _RULE26_DELETED_UNCONDITIONAL:
            owner_iso, unconditional = _RULE26_DELETED_UNCONDITIONAL[k]
            inert = _rule26_inert(unconditional)
            if meta.get("iso") == owner_iso and v not in inert:
                raise SystemExit(
                    f"bundle records the rule-26-deleted field {k}={v!r} on an "
                    f"{owner_iso} solve: the basis that value selected no "
                    f"longer exists at HEAD (the collapse made {inert[0]!r} "
                    "unconditional), so a kwargs replay would run a DIFFERENT "
                    "mechanism than the bundle. Historical record — read, "
                    "never replayed (see the cache.py epoch note)."
                )
            continue
        if k in _ENV_GATED_INERT:
            if v != _ENV_GATED_INERT[k]:
                raise SystemExit(
                    f"bundle armed the env-gated probe {k}={v!r}, which has no "
                    "solve kwarg — a kwargs replay cannot reproduce it; re-run "
                    "with the original env var set instead"
                )
            continue
        key = _REMAP.get(k, k)
        if key == "coal_plant_monthly_pricing":
            # Not a direct kwarg: the False case rides the prb_overrides channel
            # (default True is the per-ISO base, so only an explicit off matters).
            if v is False:
                kwargs.setdefault("prb_overrides", {})
                kwargs["prb_overrides"]["coal_plant_monthly_pricing"] = False
            continue
        if key == "ercot_ep_gas_basis_receipts_fallback":
            # Not a direct kwarg either: the calibration CLI arms it through the
            # generic prb_overrides ScenarioConfig channel
            # (``run_calibration_full.py`` ~line 14247,
            # ``True if args.ercot_ep_gas_basis_receipts_fallback else None``),
            # and the consumer reads it straight off the effective config
            # (``data/fuel/basis/ercot.py`` ~line 830, ``getattr(config, ...)``),
            # so prb_overrides IS the faithful route — the same one this very
            # bundle's sibling key ``ercot_ep_gas_basis_corroborated`` already
            # travels in, under ``coal_prb_sigmoid_overrides``.
            #
            # It reaches meta.json's TOP LEVEL instead because the ercot-265
            # promotion (``c79e89ef``) stamped it there as a provenance record
            # of the False -> True arming; ``solve_and_persist``'s meta literal
            # has never emitted this key, so nothing else could have. That stamp
            # made the ERCOT keeper UNREPLAYABLE ON EVERY YEAR — the key sits in
            # the base recipe and ``build_kwargs`` runs once, before the year
            # loop — and all five ERCOT MER shards stopped here on 2026-09-19
            # (docs/handoffs/FINDING-ercot-mer-replay-blocked-2026-09-19.md).
            #
            # Routed PER-KEY and deliberately NOT as a blanket "any
            # ScenarioConfig field falls through to prb_overrides": the unmapped
            # hard stop below is the miso-50..53 lossy-reconstruction guard, and
            # widening it wholesale would silently admit every future stray key.
            # This mirrors the ``coal_plant_monthly_pricing`` precedent above.
            #
            # Only a True is written, matching the CLI's ``... else None``: the
            # ScenarioConfig default is already False, so a recorded False needs
            # no override and must not fabricate one.
            #
            # DEFENSIVE COPY, not setdefault-and-mutate: ``prb_overrides`` is
            # bound straight off ``meta["coal_prb_sigmoid_overrides"]``, so
            # writing through it would mutate the caller's parsed meta.json and
            # contaminate every later reconstruction from the same dict (the
            # same trap ``apply_config_overlay`` already guards against, and one
            # this very patch fell into first time out).
            if v:
                kwargs["prb_overrides"] = dict(kwargs.get("prb_overrides") or {})
                kwargs["prb_overrides"]["ercot_ep_gas_basis_receipts_fallback"] = True
            continue
        if key in params:
            if isinstance(v, dict) and v:
                v = _strip_rule26_from_override_dict(k, v, meta)
            kwargs[key] = v
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(
            "meta.json keys not bound to solve_and_persist kwargs: "
            f"{sorted(unmapped)} — extend replay_keeper._REMAP/_IGNORE "
            "deliberately; silent drops are the miso-50..53 regression class"
        )
    # Pre-driver bundle backstop: the WP-B curtailment driver became the ERCOT
    # backcast default-ON (owner GO 2026-07-07), and its solve kwarg is
    # tri-state (None = per-ISO backcast_config default). A bundle solved
    # before the driver existed carries no key in meta.json — replaying it
    # byte-faithfully means the driver OFF, not today's default, so pin the
    # kwarg to False when meta is silent. Post-driver bundles record their
    # resolved True/False (or an explicit null) and are unaffected.
    if (
        meta.get("iso", "").upper() == "ERCOT"
        and "ercot_wtx_curtailment_driver" not in meta
    ):
        kwargs["ercot_wtx_curtailment_driver"] = False
    # Same backstop for the coal econ marginal-HR floor, which became the ERCOT
    # backcast default-ON at the ercot-115 promotion (2026-07-26) and whose
    # solve kwarg is likewise tri-state. A bundle solved before the promotion
    # carries no key in meta.json; replaying it byte-faithfully means the floor
    # OFF, not today's default. Post-promotion bundles record their resolved
    # value and are unaffected.
    if (
        meta.get("iso", "").upper() == "ERCOT"
        and "coal_econ_marginal_hr_bound" not in meta
    ):
        kwargs["coal_econ_marginal_hr_bound"] = False
    translate_legacy_coal_keys(kwargs)
    return kwargs


def translate_legacy_coal_keys(kwargs: dict) -> None:
    """Translate a pre-COAL-SUB recipe's bare ``"COAL"`` class keys, in place.

    COAL-SUB (owner instruction 2026-09-25, verbatim: "we need to completely
    eliminate the class Coal From the model altogether all coal should be
    sorted into its subclass") deleted the bare ``COAL`` class, and the
    calibration channels now REFUSE it
    (``pipeline/backcast_config._deep_merge_offer_curve``). A keeper recorded
    before that carries it in ``offer_curve_overrides`` (PJM, SPP) and in the
    full ``prb_overrides["offer_curve_by_group"]`` curve (MISO). Its semantics at
    record time: the ``COAL`` entry reached exactly the coal units whose
    SUBCLASS had no curve of its own. Every base curve those patches merge
    onto carries all four subclasses (``offer_curve_base/generic.py`` and the
    ``backcast_config`` base block), so a patch's ``COAL`` entry reached no
    rank-resolved unit, and a full recorded curve's ``COAL`` entry reached none
    whose subclass it also names. Both are therefore folded by
    :func:`~market_sim.config.plant_taxonomy.fold_legacy_coal_key`, which
    carries the value only onto a subclass nothing else covers — so every
    rank-resolved unit replays byte-identically, and the only units that move
    are the former generic-bucket ones, which now read their own subclass.
    """
    from market_sim.config.plant_taxonomy import COAL_CLASSES, fold_legacy_coal_key

    for key in ("offer_curve_overrides", "offer_curve_deltas"):
        if kwargs.get(key):
            kwargs[key] = fold_legacy_coal_key(dict(kwargs[key]), covered=COAL_CLASSES)
    prb = kwargs.get("prb_overrides")
    if prb and prb.get("offer_curve_by_group"):
        # DEFENSIVE COPY: prb_overrides is bound straight off meta.json.
        kwargs["prb_overrides"] = dict(prb)
        kwargs["prb_overrides"]["offer_curve_by_group"] = fold_legacy_coal_key(
            dict(prb["offer_curve_by_group"])
        )


#: ``meta.json`` schema tag of the composite per-year recipe overlay
#: (:data:`CONFIG_PARTITION_KEY`). Written by
#: ``scripts/stamp_config_partition.py``; consumed by
#: :func:`config_partition_overlay`.
CONFIG_PARTITION_SCHEMA = "composite-per-year-recipe/v1"

#: The ``meta.json`` key carrying that overlay.
CONFIG_PARTITION_KEY = "config_partition_overrides"


def config_partition_overlay(meta: dict, year: int) -> dict:
    """The extra ``ScenarioConfig`` keys ``year`` actually solved under.

    A COMPOSITE bundle spans years that solved under DIFFERENT configs, but
    ``meta.json`` can record only one — for the ERCOT two-config keeper the
    FORWARD one (owner ruling 2026-08-26; ``keepers/ERCOT.json``
    ``config_partition``). Its carve-out years additionally carried
    ``ercot_offer_swcap_clip=true`` and the x33.0 ``offer_curve_by_group``
    peak bands, neither of which is a ``solve_and_persist`` kwarg and neither
    of which any ``meta.json`` recorded — so a replay silently solved the
    FORWARD config on a carve-out year and reported that as the keeper
    (measured: ercot-259's control replayed the keeper on 2023 and solved
    ``swcap=False`` / CC_REGULAR ``peak=4.576``, C3a -39.6 %, against the
    keeper's own ``peak=151.008`` and C3a -7.3 %).

    :data:`CONFIG_PARTITION_KEY` closes that: it records, per year, the EXACT
    key overlay on top of the meta recipe. This reads it. Years absent from
    the block solved the base recipe and return ``{}``, so a one-config bundle
    (no block at all) is unaffected.

    Returns:
        The year's overlay, ``_``-prefixed schema/annotation keys stripped.
    """
    block = meta.get(CONFIG_PARTITION_KEY) or {}
    entry = block.get(str(int(year))) or {}
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def partition_years_by_recipe(
    meta: dict, years: "list[int]"
) -> "list[tuple[dict, list[int]]]":
    """Group ``years`` by the overlay each one solved under, in first-seen order.

    One ``solve_and_persist`` call carries ONE config, so a span whose years
    do not share an overlay cannot be replayed by a single invocation — see
    :func:`enforce_single_recipe_partition`.
    """
    groups: "list[tuple[dict, list[int]]]" = []
    for y in years:
        overlay = config_partition_overlay(meta, y)
        for g_overlay, g_years in groups:
            if g_overlay == overlay:
                g_years.append(int(y))
                break
        else:
            groups.append((overlay, [int(y)]))
    return groups


def apply_config_overlay(kwargs: dict, overlay: dict) -> None:
    """Apply a per-year recipe overlay to reconstructed replay ``kwargs``.

    Routes each key through the SAME two channels ``--set`` uses — the
    explicit ``solve_and_persist`` kwarg when one exists AND the generic
    ``prb_overrides`` ``ScenarioConfig`` channel when the key is a config
    field — because ``run_year``'s application order is mixed and a
    single-channel write is silently re-stomped by the other (the ERCOT-65
    defect class; see the ``--set`` comment in :func:`main`). This is exactly
    the channel the ercot-256 promotion set these keys through by hand, so a
    consumed overlay reproduces the leg rather than approximating it.

    Applied BEFORE ``--set`` so an operator override still wins.

    Raises:
        SystemExit: a key nothing would consume — never a silent drop
            (the miso-50..53 lossy-reconstruction class ``build_kwargs``
            exists to prevent).
    """
    if not overlay:
        return
    from market_sim.config.scenarios import ScenarioConfig

    cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
    # DEFENSIVE COPY, not setdefault-and-mutate: ``build_kwargs`` binds the
    # override bag straight off ``meta``, so writing through it would mutate
    # the caller's parsed meta.json — contaminating the BASE recipe for every
    # later group of the same span (measured: a forward-leg replay picked up
    # the carve-out's swcap/peak from a preceding carve-out leg). Same guard
    # the per-flag override blocks in ``run_replay_bundle`` already use.
    kwargs["prb_overrides"] = dict(kwargs.get("prb_overrides") or {})
    for key, val in overlay.items():
        routed = False
        if key in solve_params:
            kwargs[key] = val
            routed = True
        if key in cfg_fields:
            kwargs["prb_overrides"][key] = val
            routed = True
        if not routed:
            raise SystemExit(
                f"{CONFIG_PARTITION_KEY} records {key!r}, which is neither a "
                "solve_and_persist kwarg nor a ScenarioConfig field at HEAD — "
                "nothing would consume it, so the replay would solve a "
                "DIFFERENT recipe than the bundle records"
            )


def enforce_single_recipe_partition(
    meta: dict, years: "list[int]", kwargs: dict
) -> None:
    """Consume the per-year recipe overlay for ``years``, or refuse the span.

    A composite bundle's span is replayable one RECIPE GROUP at a time,
    because ``solve_and_persist`` carries one config per call. When ``years``
    share an overlay it is applied and the replay is faithful; when they do
    not, this HARD FAILS and names the groups, rather than silently solving
    one group's config over the whole span — which is the defect itself.

    The mixed span is solved by chaining one invocation per group with
    ``--years`` and ``--reuse-solved`` (CLAUDE.md rule 12's per-year chain,
    already the idiom for an ERCOT full span, whose single-year LP needs
    6-9 GB).
    """
    groups = partition_years_by_recipe(meta, [int(y) for y in years])
    if len(groups) > 1:
        detail = "; ".join(
            f"{sorted(g_years)} -> "
            + (", ".join(sorted(g_overlay)) if g_overlay else "the base recipe")
            for g_overlay, g_years in groups
        )
        raise SystemExit(
            f"bundle records a {CONFIG_PARTITION_KEY} overlay that splits the "
            f"requested span into {len(groups)} recipe groups ({detail}). One "
            "solve carries ONE config, so replaying them together would solve "
            "a single group's recipe over every year — the two-config replay "
            "defect this block exists to close. Chain one invocation per "
            "group with --years (and --reuse-solved to carry solved years "
            "forward)."
        )
    apply_config_overlay(kwargs, groups[0][0] if groups else {})


#: ``run_year`` parameters that are NEVER part of a bundle's recipe: the four
#: positional arguments, the per-call plumbing ``solve_and_persist`` fills in
#: itself (``ttc_overrides``, ``must_run_mw``, ``demand``, ``xyear_cache``) and
#: the probe-only ``fleet_only`` switch. A fleet-only rebuild passes these
#: itself; they are excluded from :func:`run_year_kwargs` so a probe can splat
#: the result straight into ``run_year(year, iso, hours, gas_price, {}, ...)``.
RUN_YEAR_NON_RECIPE: frozenset[str] = frozenset(
    {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "must_run_mw",
        "demand",
        "xyear_cache",
        "fleet_only",
    }
)

#: solve_and_persist kwarg -> run_year kwarg, where ``solve_and_persist`` hands
#: the value to ``run_year`` under a DIFFERENT name (read off its own
#: ``run_year(...)`` call). Everything else is passed name-for-name.
RUN_YEAR_REMAP: dict[str, str] = {
    "commitment": "commitment_enabled",
    "screen_coal": "commitment_screen_coal",
}
# (``inject_biomass_mustrun`` and ``must_run_mw`` are also renamed in that call,
# but from LOCALS ``solve_and_persist`` derives itself — not recorded kwargs —
# so they are plumbing, not recipe; ``must_run_mw`` is in RUN_YEAR_NON_RECIPE.)


def run_year_kwargs(meta: dict) -> dict:
    """Return a bundle's recipe as ``run_calibration.run_year`` keyword arguments.

    THE ONLY SANCTIONED FLEET-ONLY RECONSTRUCTION (caiso-243 §7.3 / caiso-244).
    Every zero-LP probe that rebuilds a keeper's fleet, offers or fuel prices
    with ``run_year(..., fleet_only=True)`` must take its kwargs from here.

    Why this exists: from caiso-202 to caiso-243 the CAISO lane's probes
    rebuilt the recipe as ``{k: v for k, v in meta.items() if k in
    run_year's parameters}`` — a filter by parameter NAME. That silently drops
    every meta key whose ``run_year`` kwarg is spelled differently, above all
    ``coal_prb_sigmoid_overrides`` -> ``prb_overrides``, the generic override
    bag that carries dozens of structural flags on EVERY ISO's keeper (36 on
    CAISO: the daily citygate spot level, capacity deliverability, scarcity,
    the RA bridge, hydro, measured heat rates, WEFOR, ...), plus
    ``coal_bit_passthrough_sigmoid`` -> ``coal_bit_sigmoid`` and
    ``coal_bit_sigmoid_overrides`` -> ``bit_overrides``. A probe on that
    reconstruction measured a lookalike recipe, not the keeper — the CAISO
    keeper prices gas at the daily spot level, the probes rebuilt it on the
    monthly survey (``PRECOMMIT-caiso243-ADDENDUM-recipe-repair-2026-09-04.md``).

    This function goes through :func:`build_kwargs` — the STRICT meta ->
    ``solve_and_persist`` mapping that hard-errors on any unmapped key, applies
    the rule-26 deletion registry and the env-gated-probe guard — and then
    keeps exactly the subset ``solve_and_persist`` hands to ``run_year``, under
    the names ``solve_and_persist`` uses in its own call
    (:data:`RUN_YEAR_REMAP`). It is therefore the recipe the solve ran, not a
    lookalike, and it fails loudly rather than dropping structure.

    What a fleet-only rebuild still cannot reproduce, by construction: the
    ``solve_and_persist`` kwargs that ``run_year`` does not take — the ERCOT
    post-LP price overlays, ``btm_backfill_year`` (a benchmark-side mirror),
    ``strict_demand_profile`` (which selects the ``demand`` object handed to
    ``run_year``). None touches the fleet, the offers or the fuel prices, but a
    probe that measures prices or demand must check them:
    :func:`run_year_unreachable` lists the ones the bundle records away from
    ``solve_and_persist``'s own default.

    Args:
        meta: The bundle's ``meta.json``.

    NOT INCLUDED, and the caller must add them:
    :data:`DERIVED_RUN_YEAR_INPUTS` — the ``run_year`` inputs
    ``solve_and_persist`` derives from its own locals and the bundle therefore
    never records, so nothing here can map them and
    :func:`run_year_unreachable` cannot report them either. Splat
    :func:`derived_run_year_inputs` alongside this result (caiso-248).

    Returns:
        Keyword arguments for ``run_year`` — WITHOUT the positional four,
        ``ttc_overrides``, ``fleet_only`` or the per-call plumbing
        (:data:`RUN_YEAR_NON_RECIPE`); the caller supplies those.
    """
    from scripts.run_calibration import run_year

    params = set(inspect.signature(run_year).parameters)
    full = build_kwargs(meta)
    out: dict = {}
    for key, value in full.items():
        target = RUN_YEAR_REMAP.get(key, key)
        if target in params and target not in RUN_YEAR_NON_RECIPE:
            out[target] = value
    return out


#: run_year inputs the bundle NEVER records, because ``solve_and_persist``
#: derives them from its own locals rather than from a recorded kwarg. They are
#: invisible to BOTH :func:`run_year_kwargs` (nothing to map) and
#: :func:`run_year_unreachable` (which can only report recorded keys), so a
#: fleet-only rebuild silently omits them unless the caller recovers them —
#: which is what :func:`derived_run_year_inputs` is for.
#:
#: ``inject_biomass_mustrun``: ``solve_and_persist`` injects the residual
#: must-run classes (``_INJECTED_MUSTRUN_CLASSES``) from measured EIA-923
#: energy and sets this flag from ``"biomass" in must_run``; ``run_year`` then
#: passes it as ``drop_biomass_units``, REMOVING the raw biomass LP units so
#: they are not served twice. A rebuild that omits it carries phantom biomass
#: units the scored solve never had (caiso-248; it invalidated caiso-247's
#: DOM_OTHER attribution).
DERIVED_RUN_YEAR_INPUTS: tuple[str, ...] = ("inject_biomass_mustrun",)


def derived_run_year_inputs(bundle: "Path | str", year: int) -> dict:
    """Recover the unrecorded ``run_year`` inputs from a bundle's own sidecars.

    See :data:`DERIVED_RUN_YEAR_INPUTS`. Every fleet-only rebuild should splat
    this into ``run_year`` alongside :func:`run_year_kwargs`.

    ``inject_biomass_mustrun`` is recovered from the committed
    ``hourly/class_hourly_<year>.parquet``: an injected class is a MONTHLY STEP
    profile — annual measured energy shaped by a 12-vector, constant inside a
    month — so it shows at most 12 distinct levels joined by at most 11 change
    points. The test is deliberately calendar-agnostic: ``run_calibration_full``
    builds its month map from the REAL calendar, so in a leap year the steps sit
    on 8784-clock boundaries (CAISO 2024 biomass steps at hour 1440 = 31 d +
    29 d) while the model clock is 8760 — a "flat within my months" test misses
    that year entirely.

    A near-zero class can meet the shape test by coincidence (CAISO 2023 ``oil``
    is 65 MWh in two levels); harmless, because only ``biomass`` is consumed.

    Args:
        bundle: The keeper bundle directory.
        year: The solve year whose sidecar to read.

    Returns:
        ``{"inject_biomass_mustrun": bool}``.

    Raises:
        FileNotFoundError: If the bundle has no ``class_hourly`` sidecar for
            ``year`` — the caller must not silently assume ``False``.
    """
    import numpy as np
    import pandas as pd

    path = Path(bundle) / "hourly" / f"class_hourly_{int(year)}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} — cannot recover {DERIVED_RUN_YEAR_INPUTS} without it; "
            "a fleet-only rebuild that assumes False carries phantom biomass "
            "LP units (caiso-248)."
        )
    frame = pd.read_parquet(path)
    frame = frame[frame["pass"] == "P1"]
    injected: set[str] = set()
    for klass, grp in frame.groupby("klass", observed=True):
        hours = int(grp["hour"].max()) + 1
        series = np.zeros(max(hours, 1))
        series[grp["hour"].to_numpy(int)] = grp["mw"].to_numpy(float)
        if series.sum() <= 0:
            continue
        vals = np.round(series, 6)
        if len(np.unique(vals)) <= 12 and int((np.diff(vals) != 0).sum()) <= 11:
            injected.add(str(klass))
    return {"inject_biomass_mustrun": "biomass" in injected}


def run_year_unreachable(meta: dict) -> dict:
    """Return the recorded solve kwargs a fleet-only ``run_year`` rebuild cannot carry.

    The complement of :func:`run_year_kwargs` inside :func:`build_kwargs`:
    every ``solve_and_persist`` kwarg the bundle records that ``run_year`` has
    no parameter for (after :data:`RUN_YEAR_REMAP`), restricted to the ones
    whose recorded value differs from ``solve_and_persist``'s own default — a
    default-valued key is inert in the solve too, so only a non-default one
    marks something the rebuild silently lacks. A probe records the result in
    its provenance block; an empty dict means the rebuild is the whole
    recipe the fleet/offer/fuel path ever saw.

    Args:
        meta: The bundle's ``meta.json``.

    Returns:
        ``{solve_kwarg: recorded_value}`` for the non-default unreachable keys.
    """
    from scripts.run_calibration import run_year

    run_params = set(inspect.signature(run_year).parameters)
    solve_params = inspect.signature(rcf.solve_and_persist).parameters
    full = build_kwargs(meta)
    out: dict = {}
    for key, value in full.items():
        target = RUN_YEAR_REMAP.get(key, key)
        if target in run_params:
            continue
        default = solve_params[key].default if key in solve_params else None
        if value != default:
            out[key] = value
    return out


def _warn_on_environment_mismatch(meta: dict) -> None:
    """Print a loud (non-fatal) WARNING when the runtime environment drifted.

    A byte-faithful replay is only meaningful under the same solver/numerics
    stack the keeper was solved with (alternate-optimal vertices move across
    versions). We surface any drift so a non-reproducing replay can be traced to
    it — but never fail: a bundle solved before the environment block existed
    records nothing, and the operator may deliberately replay on a new stack.
    """
    recorded = meta.get("environment")
    if not recorded:
        return  # pre-environment-block bundle; nothing to compare
    current = rcf._environment_block()
    diffs: list[str] = []
    for field in ("python_version", "platform"):
        if recorded.get(field) != current.get(field):
            diffs.append(
                f"{field}: bundle {recorded.get(field)!r} != now {current.get(field)!r}"
            )
    rec_pkgs = recorded.get("packages") or {}
    cur_pkgs = current.get("packages") or {}
    for name in sorted(set(rec_pkgs) | set(cur_pkgs)):
        if rec_pkgs.get(name) != cur_pkgs.get(name):
            diffs.append(
                f"{name}: bundle {rec_pkgs.get(name)!r} != now {cur_pkgs.get(name)!r}"
            )
    if diffs:
        print(
            "WARNING: replay environment differs from the bundle's recorded "
            "environment — byte-identity is not guaranteed:\n  " + "\n  ".join(diffs),
            file=sys.stderr,
        )


def _write_legitimacy_diagnostics(run_dir: Path, iso: str) -> None:
    """Generate ``<run_dir>/legitimacy_diagnostics.json`` via the S1 suite.

    The normal calibration path produces this artifact as a post-solve step:
    the operator runs ``scripts/legitimacy_diagnostics.py --bundle <dir>
    --iso <ISO> --json-out <dir>/legitimacy_diagnostics.json`` (the
    ``calibration_verdict._LEGIT_HOWTO`` contract), and the rubric's C7/C8
    score from the committed artifact without ever recomputing it. The replay
    driver historically stopped at the solve, leaving a replayed bundle with
    no artifact for C8 to score — the ercot-193-disclosed tooling gap
    (calibration-log "Disclosures" block / FINDING-ercot193-soc-regate §4).
    Close it by invoking the SAME entry point on the replayed bundle: same
    suite, same CLI surface, no second implementation ([R-ONE-MECH] spirit).
    A replayed bundle has everything the post-step needs — the solve just
    rewrote ``floors/*.npz`` and the dispatch parquets — so nothing is
    approximated.

    A diagnostics gate FAIL does not fail the replay: ``--json-out`` is
    written before the suite's exit code is decided, and the artifact's job
    is disclosure (the rubric scores from its contents). Likewise a hard
    error in the suite is reported loudly with the manual fallback command
    rather than discarding a completed multi-hour solve at the finish line.
    """
    from scripts import legitimacy_diagnostics as ld

    json_out = run_dir / "legitimacy_diagnostics.json"
    argv = ["--bundle", str(run_dir), "--iso", iso, "--json-out", str(json_out)]
    try:
        rc = ld.main(argv)
    except (Exception, SystemExit) as exc:
        print(
            "WARNING: legitimacy diagnostics generation failed "
            f"({exc!r}) — the replayed bundle carries no fresh "
            "legitimacy_diagnostics.json; run scripts/legitimacy_diagnostics.py "
            f"--bundle {run_dir} --iso {iso} --json-out {json_out} manually",
            file=sys.stderr,
        )
        return
    print(f"legitimacy diagnostics written -> {json_out}")
    if rc != 0:
        print(
            "WARNING: legitimacy diagnostics gate FAIL on the replayed bundle "
            "(artifact still written; C7/C8 score from its contents — see the "
            "report above)",
            file=sys.stderr,
        )


def _restore_display_date(run_dir: Path, orig_ts: str) -> str:
    """Restore ONLY the original date prefix of the replayed meta timestamp.

    The dashboard run id is ``<date>-<shorthand>``, so a byte-faithful
    in-place replay keeps the original DATE (id stability) while the
    time-of-day stays the replay's. Every other meta.json field —
    ``basis_sha`` and ``git_sha`` above all — is left as solve_and_persist
    freshly wrote it: a replayed bundle's provenance must date the bytes on
    disk, not the destroyed original session (caiso-122 §1: the hybrid
    timestamp plus a dead ``git_sha`` left the keeper with no usable basis
    anchor; ``basis_sha`` is that anchor and restoring it here would re-open
    the defect). Returns the timestamp written back.
    """
    meta_path = run_dir / "meta.json"
    new_meta = json.loads(meta_path.read_text())
    new_ts = new_meta.get("timestamp", "")
    new_meta["timestamp"] = orig_ts[:10] + new_ts[10:] if new_ts else orig_ts
    meta_path.write_text(json.dumps(new_meta, indent=2) + "\n")
    return new_meta["timestamp"]


def pin_determinism_env() -> None:
    """Apply :data:`DETERMINISM_ENV` to ``os.environ``.

    Called from :func:`main`, not at import time. The pin is right for this
    script's own process and wrong for anyone else's — a by-path or ordinary
    import (``scripts/knob_jacobian.py`` imports this module for
    :func:`build_kwargs`) would otherwise inherit it silently. It is the same
    import-time pattern that poisoned the pytest process through
    ``capture_keeper_goldens.py``
    (``docs/FINDING-fast-tier-repair-2026-09.md`` §4b, routed for this script
    at §7.6); here the pinned value equals ``pipeline/solve.py``'s own default,
    so no CLI behaviour changes either way.
    """
    for _k, _v in DETERMINISM_ENV.items():
        os.environ[_k] = _v


def main() -> None:
    # Reproducibility pin, applied here rather than at import time — see
    # pin_determinism_env. main() is this module's only solve entry.
    pin_determinism_env()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="bundle dir, e.g. results/calibration/<name>")
    ap.add_argument(
        "--out-dir",
        default=None,
        help="solve into this dir instead of the bundle (default: in place)",
    )
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=JSON",
        help="ScenarioConfig override applied on top of the keeper config via "
        "the generic prb_overrides channel (repeatable), e.g. "
        "--set capacity_deliverability_limits=true. The value is JSON. Turns "
        "the byte-faithful replay into a single-delta A/B probe of the keeper "
        "— pair with --out-dir and --note so the probe never overwrites the "
        "keeper bundle.",
    )
    ap.add_argument(
        "--note",
        default=None,
        help="free-text run note recorded in the new bundle's run_config.json "
        "(defaults to the BTM-basis replay note)",
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="solve only these years instead of the bundle's full span — the "
        "per-year invocation chain of CLAUDE.md rule 12 (a single year's "
        "per-plant LP already needs most of a small box's RAM, so a fresh "
        "process per year avoids heap-fragmentation OOM). Pair later "
        "invocations with --reuse-solved so already-solved years byte-copy "
        "forward. A partial-years replay is a NEW run, never the keeper "
        "fixed in place (its meta timestamp is not restored).",
    )
    ap.add_argument(
        "--reuse-solved",
        default=None,
        metavar="BUNDLE",
        help="byte-copy already-solved years from this prior bundle when its "
        "recipe matches exactly (run_calibration_full.plan_reuse_solved — "
        "same gate as the calibration CLI's --reuse-solved). Reused years "
        "are copies, not fresh evidence.",
    )
    ap.add_argument(
        "--enable-legacy-p2",
        action="store_true",
        help="unlock the ARCHIVED P2 commitment pass when the REPLAYED RECIPE "
        "arms it (meta.json commitment/persist_p2_state/...). Without this a "
        "bundle recorded with commitment=true is a hard error instead of a "
        "silent re-arm: P0/P1 are the only production passes and every run is "
        'scored on P1 (CLAUDE.md "Dispatch & Commitment"). To move a recipe '
        "onto the production basis instead, pass --set commitment=false.",
    )
    ap.add_argument(
        "--offer-curve-json",
        default=None,
        metavar="JSON_OR_PATH",
        help="replace the keeper's offer_curve_overrides with this "
        "class->band mapping (inline JSON or a path, same shape/validation "
        "as run_calibration_full --offer-curve-json). Single-delta offer-"
        "surface probe of the keeper — pair with --out-dir and --note.",
    )
    ap.add_argument(
        "--persist-p0-commitment",
        action="store_true",
        help="also write hourly/p0_commitment_<year>.parquet (the bit-packed "
        "P0 on/off pattern) and hourly/startup_run_ratio_<year>.parquet, the "
        "same artifacts run_calibration_full's flag of this name writes. "
        "WRITE-ONLY and additive: it is read after both LPs have already run, "
        "so it CANNOT change the solve and the replay stays byte-faithful. "
        "Needed because the P0 run pattern is the sole input to the RA "
        "must-offer bridge's candidacy detector, and no committed CAISO "
        "bundle carries it — a keeper solved without the flag cannot be "
        "interrogated about WHICH units it bridged (caiso-284 phase 0). "
        "Exposed here rather than left to a hand-rebuilt "
        "run_calibration_full invocation so an instrumented replay stays a "
        "one-command shard: rule 32(c)(6) forbids a shard editing scripts/.",
    )
    ap.add_argument(
        "--persist-p0-dispatch",
        action="store_true",
        help="also write hourly/p0_dispatch_<year>.parquet (the P0 dispatch in "
        "MW) and hourly/p0_prices_<year>.parquet (the P0 zonal duals), the "
        "same artifacts run_calibration_full's flag of this name writes. "
        "WRITE-ONLY and additive, on the same argument as the flag above: read "
        "after both LPs have run, so the replay stays byte-faithful. The "
        "on/off pattern that flag writes recovers the RA bridge's detected "
        "runs but NOT the two screens that then act on them — the "
        "startup_aware run screen scores runs on (price - mc) x dispatch and "
        "the surplus decommit screen derives absorption from the interchange "
        "rows' dispatch, both in MW and both against the P0 duals rather than "
        "the P1 prices the committed sidecars carry. With this pair a later "
        "session replays the detector exactly at zero LP instead of bounding "
        "it analytically (caiso-287; RESULT-caiso286 section 7).",
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    orig_ts = meta.get("timestamp", "")
    _warn_on_environment_mismatch(meta)

    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["iso"] = meta["iso"]
    # Rule 22 gate. This driver calls solve_and_persist DIRECTLY rather than
    # through run_calibration_full.main(), so until 2026-08-05 it reached the
    # solver without passing the freeze or marker checks at all: --years 2022
    # on any keeper bundle solved a holdout year with no gate. That is the same
    # hole holdout-policy-memo-2026-07.md (b)(2) closed at the calibration CLI's
    # own entry point, reopened by a second entry point. Gate here too, with the
    # identical function, so the two paths cannot diverge.
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir) if args.out_dir else bundle
    if args.reuse_solved is not None:
        kwargs["reuse_solved"] = Path(args.reuse_solved)
    # COMPOSITE per-year recipe (ercot-260). meta.json carries ONE config; a
    # composite bundle's other years solved under a recorded overlay. Consume
    # it for the requested span — or refuse a span that mixes recipes — BEFORE
    # the --set loop, so an explicit operator override still wins.
    enforce_single_recipe_partition(meta, kwargs["years"], kwargs)
    # --set routes through BOTH channels: the explicit solve_and_persist kwarg
    # (when one exists) AND the generic prb_overrides ScenarioConfig channel
    # (when the key is a config field). run_year's override application order
    # is mixed — prb_overrides applies after most explicit kwargs but BEFORE a
    # trailing block of them (e.g. ercot_ecrs_conservative_deployment at
    # run_calibration.py::run_year), so a prb-only --set of such a key is
    # silently re-stomped by the meta's kwarg value (the ERCOT-65 defect class,
    # kwarg-over-prb direction — discovered when an ecrs A/B replayed the
    # keeper byte-identically, ercot84 2026-07-18). Writing the same value to
    # both channels makes the last-applied channel carry it either way, and
    # keeps the recorded meta/run_config internally consistent.
    if args.overrides:
        from market_sim.config.scenarios import ScenarioConfig

        cfg_fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
        solve_params = set(inspect.signature(rcf.solve_and_persist).parameters)
    for spec in args.overrides:
        key, _, raw = spec.partition("=")
        if not key or not raw:
            raise SystemExit(f"--set expects KEY=JSON, got {spec!r}")
        val = json.loads(raw)
        routed = False
        if key in solve_params:
            kwargs[key] = val
            routed = True
        if key in cfg_fields:
            kwargs.setdefault("prb_overrides", {})
            kwargs["prb_overrides"][key] = val
            routed = True
        if not routed:
            raise SystemExit(
                f"--set {key}: neither a solve_and_persist kwarg nor a "
                "ScenarioConfig field — nothing would consume it"
            )
    if args.offer_curve_json is not None:
        kwargs["offer_curve_overrides"] = rcf._parse_offer_curve_json(
            args.offer_curve_json, flag="--offer-curve-json"
        )
    if args.note is not None:
        kwargs["note"] = args.note
    # Write-only persistence flag, applied AFTER the --set loop and BEFORE the
    # legacy-P2 gate, on the persist_p2_state precedent. Only ever turned ON
    # here: the absence of the flag leaves whatever the keeper's own meta
    # recorded, so a replay of a bundle that already had it keeps it.
    if args.persist_p0_commitment:
        kwargs["persist_p0_commitment"] = True
    if args.persist_p0_dispatch:
        kwargs["persist_p0_dispatch"] = True
    # ARCHIVED-P2 gate on the RECONSTRUCTED recipe (audit row O5). Placed AFTER
    # the --set loop so `--set commitment=false` is what disarms it, and before
    # the solve so a bundle recorded with commitment=true can never re-arm P2
    # implicitly. run_calibration_full's own CLI gate only sees parsed CLI args
    # and is blind to this path.
    rcf.enforce_legacy_p2_kwargs(kwargs, args.enable_legacy_p2)
    kwargs.setdefault(
        "note",
        "BTM-basis re-solve: byte-faithful replay of the committed keeper "
        "config from meta.json, adding btm.parquet (behind-the-meter CHP held "
        "out of the LP) so the benchmark scores on the grid-delivered basis.",
    )

    print(f"replaying {bundle} ({meta['iso']} {meta['years']}) ...")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")

    # Preserve the original run id: restore the meta.json timestamp date so the
    # dashboard id (<date>-<shorthand>) is unchanged. Only for byte-faithful
    # full-span replays IN PLACE — an overridden run (--set /
    # --offer-curve-json), a partial-years chain invocation (--years), or a
    # solve redirected to a different --out-dir is a NEW run, not the keeper
    # fixed in place, and must mint its own dated id.
    #
    # The --out-dir clause is miso-117: a ZERO-DELTA CONTROL arm takes no
    # --set, so it satisfied every other condition and inherited the keeper's
    # date — dating a bundle solved 2026-08-03 as 2026-07-31, three days before
    # its own treatment arm (which carries --set and is dated correctly). One
    # A/B, two dates, and the control's dashboard id claiming a solve date it
    # does not have. The bundle is not the keeper's, so its id is not the
    # keeper's either.
    redirected = args.out_dir is not None and Path(args.out_dir).resolve() != (
        bundle.resolve()
    )
    if (
        orig_ts
        and not args.overrides
        and args.offer_curve_json is None
        and args.years is None
        and not redirected
    ):
        _restore_display_date(run_dir, orig_ts)
        print(f"restored meta timestamp date -> {orig_ts[:10]}")

    # Post-solve diagnostics artifact, exactly as the normal calibration path
    # produces it (see _write_legitimacy_diagnostics). After the date restore
    # so the suite reads the bundle in its final on-disk state.
    _write_legitimacy_diagnostics(run_dir, meta["iso"])


if __name__ == "__main__":
    main()
