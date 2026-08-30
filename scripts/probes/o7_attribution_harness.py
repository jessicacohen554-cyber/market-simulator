"""O7 attribution harness — the finding-§5 decomposition probe (owner ruling 2026-08-30).

**Charter:** ``docs/FINDING-o7-p0-seam-restoration-2026-08-26.md`` §5 (build
exactly what it assesses) + ``docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md``
(the construction, fixed ex ante — read it before editing this file; its HP-1
falsifier is a STOP-REPORT condition, never a widened seam).

The ercot-188 (c2) refinement ``ercot_econ_curve_top_refine`` writes heat rates
into the BASE fleet, so its arm-vs-off A/B moves P0 by construction and the
offer-surface family's P0 bit-identity proof is forfeit — every whole-solve
delta confounds the ladder's pricing channel with commitment-side motion
(FINDING-ercot188 §6.2: "there is no counterfactual in which the ladder moves
and the commitment does not"). This harness manufactures that counterfactual
AS AN INSTRUMENT, with zero mechanism change and zero keeper motion:

* **Leg A (keeper arm)** — the keeper recipe replayed exactly, capture-only.
* **Leg C (control)** — the keeper recipe with the refinement off (the
  ``prb_overrides`` channel, the only channel the field rides); also saves the
  coarse fleet's ``(unit_ids, pmax, mc_base)`` capture.
* **Leg L (de-laddered arm)** — the keeper recipe replayed exactly, with ONE
  additive ``(n_gen, T)`` component merged into the composed ``mc_bid_adjust``
  argument of ``run_energy_solve``: on each refined plant's top sub-slice rows,
  ``Δmc = mc_base_coarse[parent top block] − mc_base_refined[sub-slice]``
  (the fleet-diff form of the finding's formula — the pipeline's own mc_base
  builder reproduces every heat-rate-linked and mc_base-resident rung term by
  construction). The seam applies it strictly AFTER ``r0``
  (``pipeline/solve.py``), so **leg L's P0 is bit-identical to leg A's by
  construction** — proven with content-addressed hashes, never asserted.

Decomposition, on any scored scalar s (finding §5):

* pricing channel                 = s(A) − s(L)   (bit-identical-P0 pair)
* whole-solve A/B                 = s(A) − s(C)
* commitment channel + interaction = s(L) − s(C)  (reported at full magnitude,
  never as a pure commitment number — finding §5 limit (iii))

**Leg L is an instrument, not a market state** (rule 13): it is never
registered, never dashboarded, never a keeper input. The harness lives in
``scripts/probes/`` (default-off by being a probe), adds no ScenarioConfig
field, no CLI flag, and no ``src/`` line — the disarmed path is HEAD itself.

Usage::

    python scripts/probes/o7_attribution_harness.py --year 2023

Rule 22: years are restricted to {2023, 2024, 2025}. Legs run sequentially
(rule 12; each is a full per-plant ERCOT solve) as subprocesses of this parent,
so every leg gets a fresh deterministic heap. Solve directories are temporary;
the committed artifact is the decomposition JSON (pattern:
``results/calibration/ercot188_p0_delta.json``).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Reproducibility pin (same as replay_keeper / ercot188_p0_delta, same reason):
# every leg's P0 must be basis-independent — no disk-basis seed, no cross-year
# apply. Set BEFORE the solve core is imported (child legs import it lazily).
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

FIELD = "ercot_econ_curve_top_refine"

#: Default bundle per object year — the CALIBRATED two-config ERCOT keeper
#: (2026-08-25-234-eastex-identity forward + the 2023 carve-out
#: 2026-08-25-236-swcap-clip-k33). Read-only inputs; never written.
DEFAULT_BUNDLES = {
    2023: "results/calibration/ercot236_k33_clip",
    2024: "results/calibration/ercot234_eastex_identity",
    2025: "results/calibration/ercot234_eastex_identity",
}

LEGS = ("control", "keeper", "delad")

#: A row is "on" in an hour when its dispatch clears this (MW) — the
#: ercot188_p0_delta convention (dispatch dust below it is LP noise).
ON_MW = 1e-6

#: Suffixes produced by ``_econ_curve_steps`` (``econc00`` …) — the only rows
#: SCHEME R1 can touch. Everything else must be identical between the coarse
#: and refined builds (asserted).
ECONC_RE = re.compile(r"econc\d{2}$")


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested on toy systems — tests/test_o7_attribution_harness.py)
# ---------------------------------------------------------------------------


def canon_hash(arr) -> str:
    """Content-addressed SHA-256 of one array (or ``None``), canonically.

    The serialization is ``dtype | shape | C-order bytes`` so two arrays hash
    equal iff they are bitwise-identical in value, shape and dtype. ``None``
    (e.g. an absent storage block) hashes to a fixed sentinel so composite
    hashes stay well-defined.
    """
    h = hashlib.sha256()
    if arr is None:
        h.update(b"none")
        return h.hexdigest()
    a = np.ascontiguousarray(np.asarray(arr))
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def float_bits(x: float) -> str:
    """Bit-exact serialization of one float (``float.hex()``)."""
    return float(x).hex()


def p0_hashes(r0) -> dict:
    """Hash the P0 solution — per-field plus a composite over all of it.

    ``r0`` is a ``DispatchResult``. The composite covers every solution block
    the result carries (thermal, renewables, slack/dump, prices, storage,
    flows, objective), so "the P0s are bit-identical" is a single hash
    comparison; the per-field hashes make any mismatch attributable.
    """
    fields = (
        "dispatch",
        "wind_dispatched",
        "solar_dispatched",
        "slack",
        "dump",
        "prices",
        "storage_charge",
        "storage_discharge",
        "storage_soc",
        "flows",
    )
    out = {name: canon_hash(getattr(r0, name, None)) for name in fields}
    out["objective_value"] = float_bits(r0.objective_value)
    comp = hashlib.sha256()
    for name in (*fields, "objective_value"):
        comp.update(name.encode())
        comp.update(str(out[name]).encode())
    out["composite"] = comp.hexdigest()
    return out


def run_stats(mw: np.ndarray) -> tuple[int, int]:
    """Return ``(starts, on_hours)`` for one row's hourly MW (188 convention)."""
    on = np.asarray(mw) > ON_MW
    if not on.any():
        return 0, 0
    starts = int(np.count_nonzero(on & ~np.concatenate(([False], on[:-1]))))
    return starts, int(on.sum())


def split_unit_id(uid: str) -> tuple[str, str]:
    """Split ``{group}_{zone}_p{plant}_{suffix}`` into (prefix, suffix)."""
    prefix, _, suffix = uid.rpartition("_")
    return prefix, suffix


def build_deladder_map(coarse_ids: list[str], refined_ids: list[str]) -> dict:
    """Map the two fleets' rows for the de-laddering construction.

    Implements precommit §1.2 exactly. Per plant-bin prefix, with ``m`` coarse
    ``econcNN`` rows and ``m'`` refined ones (each sorted by suffix index):

    * ``m' == m``      → refinement did not fire: pair positionally (identity
      pairs, Δ = 0, mc equality asserted downstream).
    * ``m' == 2m − 1`` → SCHEME R1 fired: body rows ``k ∈ [0, m−2]`` pair
      positionally; sub-slice rows ``k ∈ [m−1, 2m−2]`` all map to the coarse
      ``econc{m−1}`` parent (Δ rows).
    * anything else    → ``ValueError`` (a stop-report condition, no fallback).

    Non-candidate rows must form identical unit_id sets in both fleets
    (``ValueError`` otherwise) and pair by id.

    Returns a dict with integer index arrays into each fleet:
    ``target_refined`` / ``target_parent_coarse`` (the Δ rows and their coarse
    parents, aligned), ``equal_pairs_coarse`` / ``equal_pairs_refined`` (every
    row-pair that must be bitwise-equal in mc_base: body rows, unrefined
    candidates, and all non-candidates), and ``refined_plants`` (prefixes where
    R1 fired).
    """
    c_idx: dict[str, int] = {u: i for i, u in enumerate(coarse_ids)}
    r_idx: dict[str, int] = {u: i for i, u in enumerate(refined_ids)}
    if len(c_idx) != len(coarse_ids) or len(r_idx) != len(refined_ids):
        raise ValueError("duplicate unit_ids in a fleet — mapping undefined")

    def _candidates(ids: list[str]) -> dict[str, list[tuple[int, str]]]:
        by_prefix: dict[str, list[tuple[int, str]]] = {}
        for u in ids:
            prefix, suffix = split_unit_id(u)
            if ECONC_RE.fullmatch(suffix):
                by_prefix.setdefault(prefix, []).append((int(suffix[-2:]), u))
        for rows in by_prefix.values():
            rows.sort()
        return by_prefix

    c_cand = _candidates(coarse_ids)
    r_cand = _candidates(refined_ids)
    if set(c_cand) != set(r_cand):
        only_c = sorted(set(c_cand) - set(r_cand))[:5]
        only_r = sorted(set(r_cand) - set(c_cand))[:5]
        raise ValueError(
            "econc plant-bin prefixes differ between the fleets: "
            f"coarse-only {only_c}, refined-only {only_r}"
        )

    c_cand_ids = {u for rows in c_cand.values() for _, u in rows}
    r_cand_ids = {u for rows in r_cand.values() for _, u in rows}
    c_other = set(coarse_ids) - c_cand_ids
    r_other = set(refined_ids) - r_cand_ids
    if c_other != r_other:
        only_c = sorted(c_other - r_other)[:5]
        only_r = sorted(r_other - c_other)[:5]
        raise ValueError(
            "non-econc rows differ between the fleets (the builds differ by "
            f"more than SCHEME R1): coarse-only {only_c}, refined-only {only_r}"
        )

    tgt_r: list[int] = []
    tgt_parent: list[int] = []
    eq_c: list[int] = []
    eq_r: list[int] = []
    refined_plants: list[str] = []
    for prefix in sorted(c_cand):
        crows = c_cand[prefix]
        rrows = r_cand[prefix]
        m, mp = len(crows), len(rrows)
        c_ks = [k for k, _ in crows]
        r_ks = [k for k, _ in rrows]
        if c_ks != list(range(m)) or r_ks != list(range(mp)):
            raise ValueError(
                f"{prefix}: non-contiguous econc indices (coarse {c_ks}, "
                f"refined {r_ks})"
            )
        if mp == m:
            for (_, cu), (_, ru) in zip(crows, rrows):
                eq_c.append(c_idx[cu])
                eq_r.append(r_idx[ru])
        elif m >= 2 and mp == 2 * m - 1:
            refined_plants.append(prefix)
            for (_, cu), (_, ru) in zip(crows[: m - 1], rrows[: m - 1]):
                eq_c.append(c_idx[cu])
                eq_r.append(r_idx[ru])
            parent = c_idx[crows[m - 1][1]]
            for _, ru in rrows[m - 1 :]:
                tgt_r.append(r_idx[ru])
                tgt_parent.append(parent)
        else:
            raise ValueError(
                f"{prefix}: econc row counts (coarse {m}, refined {mp}) match "
                "neither the unrefined (m'==m) nor the SCHEME R1 (m'==2m-1) "
                "geometry — stop-report condition, no fallback"
            )
    for u in sorted(c_other):
        eq_c.append(c_idx[u])
        eq_r.append(r_idx[u])

    return {
        "target_refined": np.asarray(tgt_r, dtype=int),
        "target_parent_coarse": np.asarray(tgt_parent, dtype=int),
        "equal_pairs_coarse": np.asarray(eq_c, dtype=int),
        "equal_pairs_refined": np.asarray(eq_r, dtype=int),
        "refined_plants": refined_plants,
    }


def compute_deladder_delta(
    mapping: dict,
    coarse_mc: np.ndarray,
    refined_mc: np.ndarray,
    coarse_pmax: np.ndarray,
    refined_pmax: np.ndarray,
    *,
    cap_atol_mw: float = 1e-6,
) -> tuple[np.ndarray, dict]:
    """Build Δmc from the two mc_base matrices, enforcing the precommit asserts.

    Asserts (each a hard ``ValueError`` — stop-report conditions):

    * every ``equal_pairs`` row-pair is bitwise-equal in mc_base and equal in
      pmax — the internal control that the builds differ by SCHEME R1 alone;
    * per refined plant, each sub-slice's pmax equals ``parent / n_sub`` and
      their sum equals the parent top block (``cap_atol_mw``).

    Returns ``(delta, diagnostics)`` where ``delta`` is ``(n_refined, T)``,
    zero off the target rows, and
    ``delta[row] = coarse_mc[parent] − refined_mc[row]`` on them.
    """
    eq_c = mapping["equal_pairs_coarse"]
    eq_r = mapping["equal_pairs_refined"]
    if not np.array_equal(coarse_mc[eq_c], refined_mc[eq_r]):
        bad = np.flatnonzero(
            ~np.all(coarse_mc[eq_c] == refined_mc[eq_r], axis=1)
        )[:5]
        raise ValueError(
            "mc_base differs on rows the refinement cannot touch (pair "
            f"indices {bad.tolist()}) — the two builds differ by more than "
            "SCHEME R1; stop-report condition"
        )
    if not np.allclose(coarse_pmax[eq_c], refined_pmax[eq_r], atol=cap_atol_mw):
        raise ValueError("pmax differs on rows the refinement cannot touch")

    tgt_r = mapping["target_refined"]
    tgt_p = mapping["target_parent_coarse"]
    delta = np.zeros_like(refined_mc)
    n_sub_by_parent: dict[int, int] = {}
    for p in tgt_p:
        n_sub_by_parent[int(p)] = n_sub_by_parent.get(int(p), 0) + 1
    for parent, n_sub in n_sub_by_parent.items():
        rows = tgt_r[tgt_p == parent]
        expect = coarse_pmax[parent] / n_sub
        if not np.allclose(refined_pmax[rows], expect, atol=cap_atol_mw):
            raise ValueError(
                f"sub-slice capacities of parent row {parent} are not "
                f"parent/n ({refined_pmax[rows]} vs {expect})"
            )
        if abs(refined_pmax[rows].sum() - coarse_pmax[parent]) > cap_atol_mw * n_sub:
            raise ValueError(
                f"sub-slice capacities of parent row {parent} do not conserve "
                "the top block"
            )
    if tgt_r.size:
        delta[tgt_r] = coarse_mc[tgt_p] - refined_mc[tgt_r]
    diag = {
        "rows_targeted": int(tgt_r.size),
        "plants_refined": len(mapping["refined_plants"]),
        "rows_equal_asserted": int(eq_c.size),
        "delta_abs_max_usd_mwh": float(np.abs(delta[tgt_r]).max()) if tgt_r.size else 0.0,
        "delta_capwtd_mean_usd_mwh": (
            float(
                (delta[tgt_r].mean(axis=1) * refined_pmax[tgt_r]).sum()
                / max(1e-9, refined_pmax[tgt_r].sum())
            )
            if tgt_r.size
            else 0.0
        ),
    }
    return delta, diag


def rung_spread(mc_bid: np.ndarray, mapping: dict, pmax: np.ndarray) -> dict:
    """Per-plant spread of the assembled P1 bid across sub-slice rows.

    The precommit §1.3 residual-disclosure: Δmc de-ladders ``mc_base`` only, so
    any rung structure left by P1-only adjust components keyed to a row's own
    multiplier shows up here. For each refined plant and hour, spread = max −
    min of ``mc_bid`` across its sub-slice rows; reported as the capacity-
    weighted mean over plants of the annual mean spread, plus the global max.
    """
    tgt_r = mapping["target_refined"]
    tgt_p = mapping["target_parent_coarse"]
    if not tgt_r.size:
        return {"plants": 0}
    means, caps, gmax = [], [], 0.0
    for parent in np.unique(tgt_p):
        rows = tgt_r[tgt_p == parent]
        block = mc_bid[rows]
        spread_t = block.max(axis=0) - block.min(axis=0)
        means.append(float(spread_t.mean()))
        caps.append(float(pmax[rows].sum()))
        gmax = max(gmax, float(spread_t.max()))
    means_a, caps_a = np.asarray(means), np.asarray(caps)
    return {
        "plants": int(means_a.size),
        "capwtd_mean_annual_spread_usd_mwh": float(
            (means_a * caps_a).sum() / max(1e-9, caps_a.sum())
        ),
        "max_hourly_spread_usd_mwh": gmax,
    }


# ---------------------------------------------------------------------------
# The run_energy_solve wrapper (child legs)
# ---------------------------------------------------------------------------


class HarnessSpy:
    """Wraps ``scripts.run_calibration.run_energy_solve`` for one leg.

    Capture-only on legs A (keeper) and C (control); on leg L (delad) it also
    merges Δmc into the composed ``mc_bid_adjust`` before delegating — the ONE
    intervention the harness makes, at the existing P1-only seam. On leg C it
    saves the coarse fleet capture the delad leg consumes.
    """

    def __init__(self, leg: str, capture_dir: Path, orig):
        self.leg = leg
        self.capture_dir = capture_dir
        self.orig = orig
        self.calls: list[dict] = []
        self._delta: np.ndarray | None = None
        self._delta_diag: dict | None = None
        self._mapping: dict | None = None

    # -- helpers -----------------------------------------------------------
    def _coarse_capture_path(self) -> Path:
        return self.capture_dir / "coarse_capture.npz"

    def _load_coarse(self) -> dict:
        path = self._coarse_capture_path()
        if not path.exists():
            raise SystemExit(
                f"{path} missing — run the control leg first (it saves the "
                "coarse fleet capture the delad/keeper mapping consumes)"
            )
        with np.load(path, allow_pickle=False) as z:
            return {
                "unit_ids": [str(u) for u in z["unit_ids"]],
                "pmax": z["pmax"],
                "mc_base": z["mc_base"],
            }

    def _prep_mapping(self, unit_ids, pmax, mc_base, config) -> None:
        """Build the row mapping (+ Δmc on the delad leg) on the first call."""
        coarse = self._load_coarse()
        self._mapping = build_deladder_map(coarse["unit_ids"], unit_ids)
        if self.leg == "delad":
            self._delta, self._delta_diag = compute_deladder_delta(
                self._mapping,
                coarse["mc_base"],
                mc_base,
                coarse["pmax"],
                pmax,
            )
            # SWCAP composition guard (precommit §1.3): Δmc is computed on the
            # pre-clip mc_base, valid because every econc row sits strictly
            # below the clip level so the pre-P0 clip is a no-op on them.
            tgt = self._mapping["target_refined"]
            par = self._mapping["target_parent_coarse"]
            clip = None
            if getattr(config, "ercot_offer_swcap_clip", False):
                from market_sim.config.constants import (
                    ERCOT_SWCAP_SHED_TIEBREAK_EPS,
                )

                clip = float(config.voll) - ERCOT_SWCAP_SHED_TIEBREAK_EPS
                hi = max(
                    float(mc_base[tgt].max()) if tgt.size else 0.0,
                    float(coarse["mc_base"][par].max()) if par.size else 0.0,
                )
                if hi >= clip:
                    raise SystemExit(
                        f"STOP-REPORT: an econc row reaches the SWCAP clip "
                        f"level ({hi} >= {clip}); the pre-P0 clip is not a "
                        "no-op on the Δ rows and the precommit composition "
                        "does not hold"
                    )
                self._delta_diag["swcap_clip_level"] = clip
                self._delta_diag["max_target_row_mc_usd_mwh"] = hi
            np.savez_compressed(
                self.capture_dir / "deladder_delta.npz", delta=self._delta
            )

    # -- the wrapper -------------------------------------------------------
    def __call__(self, fleet, fleet_arrays, demand, mc_base, dispatch_kwargs,
                 config, **kwargs):
        call_no = len(self.calls) + 1
        t0 = time.perf_counter()
        armed = bool(getattr(config, FIELD, False))
        if self.leg in ("keeper", "delad") and not armed:
            raise SystemExit(f"leg {self.leg}: {FIELD} is OFF in the replayed config")
        if self.leg == "control" and armed:
            raise SystemExit(f"leg control: {FIELD} is ON — the override did not take")
        if getattr(config, "iso", "") != "ERCOT":
            raise SystemExit("the harness is ERCOT-only (rule 25)")

        unit_ids = [str(g.unit_id) for g in fleet]
        pmax = np.array([float(g.pmax_mw or 0.0) for g in fleet], dtype=float)

        if call_no == 1 and self.leg == "control":
            np.savez_compressed(
                self._coarse_capture_path(),
                unit_ids=np.array(unit_ids),
                pmax=pmax,
                mc_base=np.asarray(mc_base, dtype=float),
            )
        if call_no == 1 and self.leg in ("keeper", "delad"):
            self._prep_mapping(unit_ids, pmax, mc_base, config)

        if self.leg == "delad":
            base_adjust = kwargs.get("mc_bid_adjust")
            kwargs = dict(kwargs)
            kwargs["mc_bid_adjust"] = (
                self._delta if base_adjust is None else base_adjust + self._delta
            )

        es = self.orig(
            fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kwargs
        )

        # -- capture -------------------------------------------------------
        sfx = np.array([split_unit_id(u)[1] for u in unit_ids])
        is_cmt = np.char.startswith(sfx, "committed")
        cmt_rows = {
            unit_ids[i]: list(run_stats(es.r0.dispatch[i]))
            for i in np.flatnonzero(is_cmt)
        }
        min_gen = getattr(es.p1_fleet_arrays, "min_gen", None)
        dem_t = demand.sum(axis=0)
        lw_t = (es.p1.prices * demand).sum(axis=0) / np.where(dem_t > 0, dem_t, 1.0)
        p1_slack = float(es.p1.slack.sum())
        cap: dict = {
            "call": call_no,
            "n_gen": len(unit_ids),
            "mc_base_hash": canon_hash(mc_base),
            "demand_hash": canon_hash(demand),
            "p0": p0_hashes(es.r0),
            "markup_hash": canon_hash(es.markup),
            "p1_min_gen_hash": canon_hash(min_gen),
            "p1_floored_mwh": (
                float(np.asarray(min_gen).sum()) if min_gen is not None else 0.0
            ),
            "markup_target_rows_nonzero": (
                bool(np.abs(es.markup[self._mapping["target_refined"]]).max() > 0)
                if self._mapping is not None
                and self._mapping["target_refined"].size
                else None
            ),
            "committed_rows": cmt_rows,
            "p0_total_twh": float(es.r0.dispatch.sum() / 1e6),
            "p1": {
                "lw_price_usd_mwh": float((lw_t * dem_t).sum() / dem_t.sum()),
                "price_q": {
                    "p50": float(np.quantile(lw_t, 0.50)),
                    "p95": float(np.quantile(lw_t, 0.95)),
                    "p99": float(np.quantile(lw_t, 0.99)),
                    "max": float(lw_t.max()),
                },
                "hours_ge_1000": int((lw_t >= 1000.0).sum()),
                "shed_mwh": p1_slack,
                "shed_hours": int((es.p1.slack.sum(axis=0) > 1e-3).sum()),
                "total_dispatch_twh": float(es.p1.dispatch.sum() / 1e6),
                "storage_discharge_twh": (
                    float(es.p1.storage_discharge.sum() / 1e6)
                    if es.p1.storage_discharge is not None
                    else 0.0
                ),
            },
            "wall_s": round(time.perf_counter() - t0, 1),
        }
        if self._mapping is not None:
            cap["rung_spread_mc_bid"] = rung_spread(es.mc_bid, self._mapping, pmax)
        if self.leg == "delad" and call_no == 1 and self._delta_diag:
            cap["deladder"] = self._delta_diag
        np.savez_compressed(
            self.capture_dir / f"{self.leg}_call{call_no}_p1_lw.npz", lw_t=lw_t
        )
        self.calls.append(cap)
        return es


# ---------------------------------------------------------------------------
# Child: run one leg
# ---------------------------------------------------------------------------


def run_leg(leg: str, year: int, bundle: Path, capture_dir: Path) -> None:
    """Replay one leg through ``solve_and_persist`` with the spy installed."""
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    import scripts.run_calibration as rc

    meta = json.loads((bundle / "meta.json").read_text())
    if meta.get("iso") != "ERCOT":
        raise SystemExit("the harness is ERCOT-only (rule 25)")
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["note"] = f"o7 attribution harness leg {leg} — throwaway, never registered"
    if leg == "control":
        kwargs.setdefault("prb_overrides", {})
        kwargs["prb_overrides"] = {**(kwargs["prb_overrides"] or {}), FIELD: False}

    spy = HarnessSpy(leg, capture_dir, rc.run_energy_solve)
    rc.run_energy_solve = spy
    post_step_error = None
    t0 = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix=f"o7leg_{leg}_") as td:
            kwargs["run_dir"] = Path(td) / "solve"
            try:
                rcf.solve_and_persist(**kwargs)
            except (Exception, SystemExit) as exc:  # noqa: BLE001
                if len(spy.calls) < 2:
                    raise
                # The solves completed and the captures are on disk; a
                # post-solve persistence/scoring failure is recorded loudly
                # rather than discarding the measurement.
                post_step_error = repr(exc)
    finally:
        rc.run_energy_solve = spy.orig

    if len(spy.calls) != 2:
        raise SystemExit(
            f"leg {leg}: expected exactly 2 run_energy_solve calls (the "
            f"keeper recipe's adaptive two-pass), saw {len(spy.calls)}"
        )
    out = {
        "leg": leg,
        "year": year,
        "bundle": str(bundle),
        "calls": spy.calls,
        "post_step_error": post_step_error,
        "wall_s": round(time.perf_counter() - t0, 1),
        "env": {
            "MARKET_SIM_WARMSTART": os.environ.get("MARKET_SIM_WARMSTART", ""),
            "MARKET_SIM_WARMSTART_XYEAR": os.environ.get(
                "MARKET_SIM_WARMSTART_XYEAR", ""
            ),
            "MARKET_SIM_P1_FLOOR_INPLACE": os.environ.get(
                "MARKET_SIM_P1_FLOOR_INPLACE", ""
            ),
        },
    }
    (capture_dir / f"{leg}.json").write_text(json.dumps(out, indent=1))
    print(f"[o7] leg {leg} done in {out['wall_s']}s -> {capture_dir / (leg + '.json')}")


# ---------------------------------------------------------------------------
# Parent: orchestrate legs, verify HP-1, compose the decomposition report
# ---------------------------------------------------------------------------

#: P0-side keys that must be bitwise-equal between legs A and L per call
#: (HP-1). ``composite`` covers the whole solution; the rest attribute a miss.
_HP1_KEYS = ("composite", "dispatch", "prices", "objective_value")


def verify_bit_identity(keeper: dict, delad: dict) -> dict:
    """HP-1: leg L's P0/markup/floors bitwise-equal leg A's, per call."""
    per_call = []
    ok = True
    for kc, dc in zip(keeper["calls"], delad["calls"]):
        row = {"call": kc["call"]}
        for key in _HP1_KEYS:
            eq = kc["p0"][key] == dc["p0"][key]
            row[f"p0_{key}_equal"] = eq
            ok &= eq
        for key in ("markup_hash", "p1_min_gen_hash", "mc_base_hash"):
            eq = kc[key] == dc[key]
            row[f"{key}_equal"] = eq
            ok &= eq
        eq = kc["committed_rows"] == dc["committed_rows"]
        row["committed_run_stats_equal"] = eq
        ok &= eq
        per_call.append(row)
    ok &= len(keeper["calls"]) == len(delad["calls"])
    return {"verdict": "PASS" if ok else "FAIL", "per_call": per_call}


def commitment_delta(a: dict, b: dict, pmax_by_uid: dict) -> dict:
    """188-style commitment-channel context between two legs' scored calls."""
    ra = a["calls"][-1]["committed_rows"]
    rb = b["calls"][-1]["committed_rows"]
    shared = sorted(set(ra) & set(rb))
    moved = [u for u in shared if ra[u] != rb[u]]
    return {
        "committed_rows_shared": len(shared),
        "rows_with_moved_commitment": len(moved),
        "capacity_mw_with_moved_commitment": float(
            sum(pmax_by_uid.get(u, 0.0) for u in moved)
        ),
        "d_starts": int(
            sum(rb[u][0] - ra[u][0] for u in shared)
        ),
        "d_on_hours": int(sum(rb[u][1] - ra[u][1] for u in shared)),
    }


def compose_report(year: int, bundle: Path, capture_dir: Path) -> dict:
    """Assemble the decomposition JSON from the three legs' captures."""
    legs = {}
    for leg in LEGS:
        legs[leg] = json.loads((capture_dir / f"{leg}.json").read_text())

    bit = verify_bit_identity(legs["keeper"], legs["delad"])

    with np.load(capture_dir / "coarse_capture.npz", allow_pickle=False) as z:
        pmax_by_uid = {
            str(u): float(p) for u, p in zip(z["unit_ids"], z["pmax"])
        }

    def scored(leg: str) -> dict:
        return legs[leg]["calls"][-1]["p1"]

    a, l, c = scored("keeper"), scored("delad"), scored("control")

    def d(key: str) -> dict:
        return {
            "keeper_A": a[key],
            "delad_L": l[key],
            "control_C": c[key],
            "pricing_channel_A_minus_L": a[key] - l[key],
            "whole_ab_A_minus_C": a[key] - c[key],
            "commitment_plus_interaction_L_minus_C": l[key] - c[key],
        }

    git_sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    delad_call1 = legs["delad"]["calls"][0]
    report = {
        "probe": "o7_attribution_harness",
        "charter": "docs/FINDING-o7-p0-seam-restoration-2026-08-26.md §5 "
        "(owner ruling 2026-08-30, Door 2)",
        "precommit": "docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md",
        "what_this_is": (
            "A decomposition INSTRUMENT: leg L replays the keeper recipe with "
            "the refined ladder de-priced from the P1 objective only, so "
            "keeper-vs-L measures the ladder's pricing channel at the "
            "keeper's own (hash-proven bit-identical) P0 commitment state. "
            "Leg L is never registrable (rule 13); nothing here touches the "
            "keeper's artifacts."
        ),
        "year": year,
        "bundle": str(bundle),
        "git_sha": git_sha,
        "bit_identity_HP1": bit,
        "deladder": delad_call1.get("deladder"),
        "residual_rung_spread_mc_bid": {
            "keeper_A": legs["keeper"]["calls"][-1].get("rung_spread_mc_bid"),
            "delad_L": legs["delad"]["calls"][-1].get("rung_spread_mc_bid"),
        },
        "markup_target_rows_nonzero": delad_call1.get("markup_target_rows_nonzero"),
        "attribution": {
            "lw_price_usd_mwh": d("lw_price_usd_mwh"),
            "shed_mwh": d("shed_mwh"),
            "price_quantiles": {
                leg: scored(k)["price_q"]
                for leg, k in (("keeper_A", "keeper"), ("delad_L", "delad"),
                               ("control_C", "control"))
            },
            "hours_ge_1000": {
                "keeper_A": a["hours_ge_1000"],
                "delad_L": l["hours_ge_1000"],
                "control_C": c["hours_ge_1000"],
            },
        },
        "commitment_context_HP3": {
            "control_vs_keeper_p0": commitment_delta(
                legs["keeper"], legs["control"], pmax_by_uid
            ),
            "note": (
                "Fresh context at the 236 recipe; the 188-era 73/132-row / "
                "12,474 MW measurement is the finding's record and is cited, "
                "not re-derived."
            ),
        },
        "legs": legs,
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, default=2023, choices=(2023, 2024, 2025))
    ap.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="keeper bundle to replay (default: the year's designated keeper)",
    )
    ap.add_argument("--capture-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--leg",
        choices=LEGS,
        default=None,
        help="internal: run one leg in this process (parent spawns these)",
    )
    ap.add_argument(
        "--legs",
        default="control,keeper,delad",
        help="comma list of legs the parent runs (default: all three)",
    )
    args = ap.parse_args()

    bundle = args.bundle or (REPO / DEFAULT_BUNDLES[args.year])
    if args.leg is not None:
        if args.capture_dir is None:
            raise SystemExit("--leg requires --capture-dir")
        args.capture_dir.mkdir(parents=True, exist_ok=True)
        run_leg(args.leg, args.year, bundle, args.capture_dir)
        return

    capture_dir = args.capture_dir or Path(
        tempfile.mkdtemp(prefix=f"o7harness_{args.year}_")
    )
    capture_dir.mkdir(parents=True, exist_ok=True)
    print(f"[o7] capture dir: {capture_dir}")
    for leg in [s.strip() for s in args.legs.split(",") if s.strip()]:
        if (capture_dir / f"{leg}.json").exists():
            print(f"[o7] leg {leg}: capture exists, skipping")
            continue
        print(f"[o7] running leg {leg} ({args.year}, {bundle.name}) ...")
        rc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--leg",
                leg,
                "--year",
                str(args.year),
                "--bundle",
                str(bundle),
                "--capture-dir",
                str(capture_dir),
            ],
            check=False,
        )
        if rc.returncode != 0:
            raise SystemExit(f"leg {leg} failed (exit {rc.returncode})")

    report = compose_report(args.year, bundle, capture_dir)
    out = args.out or (
        REPO / f"results/calibration/o7_attribution_harness_{args.year}.json"
    )
    out.write_text(json.dumps(report, indent=1))
    bit = report["bit_identity_HP1"]
    att = report["attribution"]["lw_price_usd_mwh"]
    print(f"\n[o7] wrote {out}")
    print(f"[o7] HP-1 bit-identity (keeper vs delad P0): {bit['verdict']}")
    print(
        "[o7] 2023 lw price  A(keeper) {:.4f} | L(delad) {:.4f} | C(control) "
        "{:.4f}".format(att["keeper_A"], att["delad_L"], att["control_C"])
    )
    print(
        "[o7] pricing channel (A-L) {:+.4f} | whole A/B (A-C) {:+.4f} | "
        "commitment+interaction (L-C) {:+.4f} $/MWh".format(
            att["pricing_channel_A_minus_L"],
            att["whole_ab_A_minus_C"],
            att["commitment_plus_interaction_L_minus_C"],
        )
    )
    if bit["verdict"] != "PASS":
        raise SystemExit(
            "STOP-REPORT: HP-1 falsified — P0 is NOT bit-identical across the "
            "keeper/delad pair. Per the precommit, file a stop-report against "
            "docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md; do not "
            "widen the seam."
        )


if __name__ == "__main__":
    main()
