"""Stitching the rolling windows into the year schedule, checkpoints, the sidecar frame.

:class:`UcSchedule` holds ``u`` / ``v`` / ``w`` for every integer cluster over
the full ``T`` hours (int16, rule 8: every hour is covered). Each solved
window contributes its first ``W`` hours (:meth:`UcSchedule.keep`); the state
it hands to the next window is :meth:`UcSchedule.state_for`. After every
completed calendar month the partial schedule and the solve log are written
to the stage's artifact directory (:meth:`UcSchedule.checkpoint`, plan E9), so
a shard near its budget always has an artifact (rule 32 stop rule).

The ``uc_schedule_<y>.parquet`` sidecar is :func:`schedule_frame` (DESIGN
section 4): one row per (cluster, hour), zstd, ``hour`` delta-packed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.fleet import FleetArrays
from market_sim.model.uc.params import UcClusterParams
from market_sim.model.uc.window import WindowResult, WindowState

#: Hours per calendar month (non-leap; the model year is 8760 h, rule 8).
_MONTH_HOURS = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)
_MONTH_END = np.cumsum(_MONTH_HOURS)


def month_boundaries(T: int = HOURS_PER_YEAR) -> np.ndarray:
    """Hour index at which each calendar month ends (clipped to ``T``)."""
    return np.minimum(_MONTH_END, T)


class UcSchedule:
    """The year's commitment schedule of the integer clusters.

    Args:
        params: The cluster struct-of-arrays.
        T: Hours in the year.
        hist_hours: How many hours of start/stop history the carried state
            keeps (the longest min-up / min-down among the integer clusters).
    """

    def __init__(
        self,
        params: UcClusterParams,
        T: int,
        hist_hours: int,
        record_states: bool = False,
    ) -> None:
        self.params = params
        self.int_idx = params.integer_clusters
        self.n_int = int(self.int_idx.size)
        self.T = int(T)
        self.H = int(max(hist_hours, 0))
        self.u = np.full((self.n_int, self.T), -1, dtype=np.int16)
        self.v = np.zeros((self.n_int, self.T), dtype=np.int16)
        self.w = np.zeros((self.n_int, self.T), dtype=np.int16)
        self.dispatch_prev: np.ndarray | None = None  # (n_gen,) kept hour's dispatch
        self.soc_prev: np.ndarray | None = None
        self.kept_until = 0
        self.windows: list[dict] = []
        #: ``record_states``: the ``(dispatch_prev, soc_prev)`` handed to the
        #: window starting at each kept frontier, keyed by that frontier —
        #: what a PAIRED bench run replays so an arm solves the same window
        #: problems as the base arm (``UcStage.run(pin=...)``).
        self.record_states = bool(record_states)
        self.prev_states: dict[int, tuple[np.ndarray, np.ndarray | None]] = {}

    def copy(self) -> "UcSchedule":
        """An independent copy (arrays copied; the recorded states are not carried)."""
        out = UcSchedule(self.params, self.T, self.H)
        out.u = self.u.copy()
        out.v = self.v.copy()
        out.w = self.w.copy()
        out.dispatch_prev = (
            None if self.dispatch_prev is None else self.dispatch_prev.copy()
        )
        out.soc_prev = None if self.soc_prev is None else self.soc_prev.copy()
        out.kept_until = self.kept_until
        return out

    @classmethod
    def from_frame(
        cls, params: UcClusterParams, T: int, hist_hours: int, frame: pd.DataFrame
    ) -> "UcSchedule":
        """Rebuild a complete schedule from a ``uc_schedule_<y>.parquet`` frame.

        The DA-schedule reuse across runs (``uc_da_schedule_reuse_bundle``,
        owner ruling R15) reads a committed leg's schedule this way. The
        frame's clusters and plant codes must be exactly the integer set of
        ``params`` (in order) and every hour ``0 .. T`` present; anything else
        raises (the input digest already certified the same problem, so a
        mismatch here is a corrupt or foreign file).
        """
        out = cls(params, T, hist_hours)
        k = out.int_idx
        f = frame.sort_values(["cluster", "hour"], kind="stable")
        clusters = np.unique(f["cluster"].to_numpy())
        if not np.array_equal(clusters, np.sort(k)) or f.shape[0] != k.size * T:
            raise ValueError(
                "uc_schedule frame does not cover the stage's integer clusters "
                f"x {T} hours (frame clusters {clusters.size}, rows {f.shape[0]}; "
                f"stage integer clusters {k.size})"
            )
        order = np.searchsorted(np.sort(k), k)  # frame block of each stage cluster
        codes = f["plant_code"].to_numpy().reshape(k.size, T)[order, 0]
        if not np.array_equal(codes, params.plant_code[k].astype(np.int64)):
            raise ValueError("uc_schedule frame plant codes differ from the stage's")
        for name in ("u", "v", "w"):
            arr = f[name].to_numpy().reshape(k.size, T)[order]
            setattr(out, name, arr.astype(np.int16))
        out.kept_until = int(T)
        return out

    # ------------------------------------------------------------------ keep
    def keep(self, result: WindowResult, t0: int, keep_hours: int) -> int:
        """Record the first ``keep_hours`` of a window solved at ``t0``; return the new frontier."""
        t1 = min(t0 + keep_hours, self.T, t0 + result.dispatch.shape[1])
        n = t1 - t0
        if self.n_int:
            self.u[:, t0:t1] = result.u[:, :n]
            self.v[:, t0:t1] = result.v[:, :n]
            self.w[:, t0:t1] = result.w[:, :n]
        self.dispatch_prev = result.dispatch[:, n - 1].copy()
        self.soc_prev = (
            result.storage_soc[:, n - 1].copy()
            if result.storage_soc is not None
            else None
        )
        self.kept_until = t1
        if self.record_states:
            self.prev_states[t1] = (self.dispatch_prev, self.soc_prev)
        return t1

    def keep_from(self, pin: "UcSchedule", t0: int, keep_hours: int) -> int:
        """Advance along ``pin``'s kept schedule and states instead of a solved window (paired runs)."""
        t1 = min(t0 + keep_hours, self.T, pin.kept_until)
        if self.n_int:
            self.u[:, t0:t1] = pin.u[:, t0:t1]
            self.v[:, t0:t1] = pin.v[:, t0:t1]
            self.w[:, t0:t1] = pin.w[:, t0:t1]
        if t1 not in pin.prev_states:
            raise ValueError(
                f"the pinned schedule recorded no state at hour {t1}; build it "
                "with record_states=True"
            )
        self.dispatch_prev, self.soc_prev = pin.prev_states[t1]
        self.kept_until = t1
        if self.record_states:
            self.prev_states[t1] = (self.dispatch_prev, self.soc_prev)
        return t1

    def state_for(
        self,
        t0: int,
        fleet: FleetArrays,
        u_init: np.ndarray | None,
        p0: np.ndarray | None,
        soc0: np.ndarray | None,
    ) -> WindowState:
        """The :class:`WindowState` a window starting at ``t0`` receives.

        ``t0 == 0`` takes ``u_init`` / ``p0`` / ``soc0`` (the P0-derived first
        state, DESIGN section 2.2); later windows take the kept schedule.
        """
        if self.kept_until == 0 or t0 <= 0:
            return WindowState(
                u_prev=np.asarray(u_init, dtype=float)
                if u_init is not None
                else np.zeros(self.n_int),
                v_hist=np.zeros((self.n_int, 0)),
                w_hist=np.zeros((self.n_int, 0)),
                soc_prev=None if soc0 is None else np.asarray(soc0, dtype=float),
                p_prev=None if p0 is None else np.asarray(p0, dtype=float),
                avail_prev=np.asarray(fleet.availability, dtype=float)[:, self.T - 1]
                if p0 is not None
                else None,
            )
        lo = max(0, t0 - self.H)
        d_prev, s_prev = self.prev_states.get(t0, (self.dispatch_prev, self.soc_prev))
        return WindowState(
            u_prev=self.u[:, t0 - 1].astype(float),
            v_hist=self.v[:, lo:t0].astype(float),
            w_hist=self.w[:, lo:t0].astype(float),
            soc_prev=s_prev,
            p_prev=d_prev,
            avail_prev=np.asarray(fleet.availability, dtype=float)[:, t0 - 1],
        )

    # ---------------------------------------------------------------- outputs
    def is_complete(self) -> bool:
        """Every hour of every integer cluster has a kept value."""
        return self.kept_until >= self.T and (
            self.n_int == 0 or bool((self.u >= 0).all())
        )

    def online_units(self) -> np.ndarray:
        """``(n_int, T)`` units online (``-1`` where not yet kept)."""
        return self.u

    def checkpoint(self, out_dir: Path, month: int, log: dict) -> Path:
        """Write ``checkpoint_<month>.npz`` and the partial log (plan E9)."""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"checkpoint_{month:02d}.npz"
        np.savez_compressed(
            path,
            u=self.u,
            v=self.v,
            w=self.w,
            kept_until=np.array([self.kept_until]),
            int_idx=self.int_idx,
        )
        (out_dir / "uc_solve_log_partial.json").write_text(
            json.dumps(log, indent=1, default=_json_default)
        )
        return path

    def frame(
        self, fleet: FleetArrays, year: int, noload_per_unit: np.ndarray | None = None
    ) -> pd.DataFrame:
        """The ``uc_schedule_<y>.parquet`` rows (cluster x hour, long).

        ``noload_per_unit`` (``(n_int, T)`` $/h per unit) is carried as a
        column (the no-load leg of the make-whole, readable from the bundle).
        ``floor_mw`` is the cluster floor ``mlf * pbar * a * u`` (``mlf`` times
        ``online_mw``, on ``fleet``'s availability) before the member allocation
        (``pipeline.uc.merit_floor_allocation``).
        """
        p = self.params
        k = self.int_idx
        T = self.T
        a = p.cluster_availability(fleet)[k]  # (n_int, T)
        u = self.u.astype(float)
        online_mw = u * p.pbar_mw[k][:, None] * a
        floor_mw = p.mlf[k][:, None] * online_mw
        hours = np.tile(np.arange(T, dtype=np.int32), self.n_int)
        return pd.DataFrame(
            {
                "year": np.full(hours.size, int(year), dtype=np.int16),
                "hour": hours,
                "cluster": np.repeat(k.astype(np.int32), T),
                "plant_code": np.repeat(p.plant_code[k].astype(np.int64), T),
                "uc_class": np.repeat(p.family[k].astype(str), T),
                "u": self.u.ravel(),
                "n": np.repeat(p.n_units[k].astype(np.int16), T),
                "v": self.v.ravel(),
                "w": self.w.ravel(),
                "online_mw": online_mw.ravel().astype(np.float32),
                "floor_mw": floor_mw.ravel().astype(np.float32),
                "noload_usd_per_unit_h": (
                    np.asarray(noload_per_unit, dtype=float).ravel().astype(np.float32)
                    if noload_per_unit is not None
                    else np.zeros(hours.size, dtype=np.float32)
                ),
            }
        )


def write_schedule_parquet(frame: pd.DataFrame, path: Path) -> Path:
    """Write the schedule frame zstd-compressed with ``hour`` delta-packed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(
        table,
        path,
        compression="zstd",
        use_dictionary=["uc_class"],
        column_encoding={"hour": "DELTA_BINARY_PACKED"},
    )
    return path


def _json_default(o):
    """JSON encoder fallback for numpy scalars / arrays."""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def write_solve_log(log: dict, path: Path) -> Path:
    """Write ``uc_solve_log_<y>.json``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=1, default=_json_default))
    return path
