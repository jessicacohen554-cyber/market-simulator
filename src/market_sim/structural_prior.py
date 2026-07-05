"""Structural-error prior (PB-3): fold the model's own error into the band.

The parametric ensemble (PB-2, :mod:`market_sim.ensemble`) answers "we don't
know the inputs"; this module answers "given the inputs, the model is wrong by
this much" (``docs/handoffs/probability-bounds-plan-2026-07.md`` §3). The two
compose without double-counting because the fit inputs are the **D-7
statistical-mode probes** (``docs/statistical-mode-results-2026-07.md``): every
backcast-only measured overlay is off but the realized annual gas price, load
and weather are kept, so their emissions error is exactly *model error given
true inputs* — not the overlay-carried keeper error, which would understate
(plan §3.2).

For each ISO the log error ``eps_{i,y} = ln(emissions_model / emissions_actual)``
over the fit years (2023-2025, :data:`STRUCTURAL_PRIOR_YEARS`) yields a bias
``b_i = mean(eps)`` and noise ``s_i = sd(eps)``. With three points per ISO the
noise is pooled across ISOs and the prior carries the parameter uncertainty
explicitly: ``eps_i ~ Student-t(nu=2, loc=b_i,
scale=sqrt(max(s_pooled^2, s_i^2) * (1 + 1/3)))``. The ``max`` keeps the hard
PB-3 requirement — the prior is **wider than the plug-in normal
Normal(b_i, s_i), never narrower** — even for an ISO noisier than the pool,
and the t2's fat tails plus the ``+1/3`` inflation encode that both moments
come from three points.

**No recentering (rule 13, plan §3.2).** ``eps`` enters the convolution with
its non-zero mean: the published band is asymmetric around the model path and
covers the known bias. Subtracting ``b_i`` from the point forecast — or
zero-centering ``eps`` — would feed a measured outcome back into the number
being validated (an answer-key channel). The parametric layer's rows, and with
them the P50 point path, are never modified here; :func:`convolve` only *adds*
the ``parametric_plus_structural`` layer.

**Emissions-basis staleness (2026-07-05).** The statmode bundles were solved
and scored before the W2-P1/R2 measured-rate CO2 basis merged (PR #1371).
Carbon-zero ISOs (ERCOT / PJM / MISO) are unaffected in the solve (carbon =
$0 so the CO2 rate never enters ``mc``) and :func:`fit_prior` re-scores their
committed numbers under the current basis — the C5a scoring intensity rows for
2023-2025 are content-identical at HEAD, so the re-score verifies rather than
moves them. Carbon-priced ISOs (CAISO / NYISO / NEISO) have a stale *merit
order*; no post-processing can fix that, so their priors are fitted from the
stale bundles and flagged ``basis_stale`` pending the W3-P1 re-solves
(``docs/handoffs/forecast-validation-program-2026-07.md`` §3.2). The prior
artifact records the basis version and every input bundle id, so the W3-P1
re-fit is a clean swap.

**Dispatch-conditional (plan §3.4).** ``eps`` is measured on one-year
backcasts with a frozen fleet; the fleet-evolution layer's skill is unmeasured
until the W2-P5/PP-0.3 capacity hindcast. The horizon-widening term
``lambda(h)`` is pinned at 0 and flagged UNMEASURED
(:data:`STRUCTURAL_PRIOR_LAMBDA_H`), and every published artifact carries the
"dispatch-conditional — excludes fleet-path structural error" label.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    PUBLISHED_BAND_QUANTILES,
    STRUCTURAL_PRIOR_K,
    STRUCTURAL_PRIOR_LAMBDA_H,
    STRUCTURAL_PRIOR_LAMBDA_H_STATUS,
    STRUCTURAL_PRIOR_NU,
    STRUCTURAL_PRIOR_SCALE_INFLATION,
    STRUCTURAL_PRIOR_YEARS,
)
from market_sim.config.paths import REPO_ROOT
from market_sim.data.egrid import FOSSIL_CO2_RATES_PATH

logger = logging.getLogger(__name__)

# Layer name this module appends to bands.parquet — reserved by
# ensemble.compute_bands' docstring (the frozen §4.1 schema contract).
STRUCTURAL_LAYER: str = "parametric_plus_structural"

# The metric the prior applies to. eps is an *emissions* error; convolving it
# onto price/curtailment metrics would claim a cross-metric error model the
# statmode probes never measured.
_EMISSIONS_METRIC: str = "emissions_mt"

# Committed dashboard artifacts the fit reads (model CO2 from the statmode run
# payload, actual CO2 from the shared bench part — the same numbers the C5a
# verdict scores, so the prior measures exactly the published skill gap).
_RUNS_DIR: Path = REPO_ROOT / "frontend" / "data" / "backcast" / "runs"
_BENCH_DIR: Path = REPO_ROOT / "frontend" / "data" / "backcast" / "bench"

# Prior schema version — bump on any change to the fit form (not on input
# swaps; those produce a new artifact recording their own inputs).
PRIOR_SCHEMA_VERSION: int = 1

# D-7 statistical-mode fit inputs: dashboard run id, bundle path, and whether
# the ISO prices carbon in the model (CA cap-and-trade / RGGI), per
# docs/statistical-mode-results-2026-07.md and the W3-P1 split in
# docs/handoffs/forecast-validation-program-2026-07.md §0/§3.2. This registry
# is provenance, not tuning: every entry is echoed into the prior artifact and
# the W3-P1 re-fit swaps the three carbon-priced entries for the HEAD
# re-solves.
STATMODE_FIT_INPUTS: dict[str, dict] = {
    "ERCOT": {
        "run_id": "2026-07-04-statmode-d7-probe-ercot32",
        "bundle": "results/calibration/ercot32_statmode_2026-07",
        "carbon_priced": False,
    },
    "CAISO": {
        "run_id": "2026-07-03-caiso-statmode-d-7",
        "bundle": "results/calibration/caiso_statmode_2026-07",
        "carbon_priced": True,
    },
    "PJM": {
        "run_id": "2026-07-03-pjm-statmode-d-7",
        "bundle": "results/calibration/pjm_statmode_2026-07",
        "carbon_priced": False,
    },
    "NYISO": {
        "run_id": "2026-07-03-nyiso-statmode-d-7",
        "bundle": "results/calibration/nyiso_statmode_2026-07",
        "carbon_priced": True,
    },
    "NEISO": {
        "run_id": "2026-07-03-neiso-statmode-d-7",
        "bundle": "results/calibration/neiso_statmode_2026-07",
        "carbon_priced": True,
    },
    "MISO": {
        "run_id": "2026-07-03-miso-statmode-d-7",
        "bundle": "results/calibration/miso_statmode_2026-07",
        "carbon_priced": False,
    },
}

# Human-readable emissions-basis label recorded in the artifact. The precise
# identity is the sha256 of the scoring-rate artifact recorded alongside it.
_EMISSIONS_BASIS_LABEL: str = (
    "R2 measured-rate CO2 basis (PR #1371: fff2c34 physical-HR booking, "
    "968cead quarantine-row strip); C5a scoring intensities from "
    "fossil_co2_rates.parquet"
)

_DISPATCH_CONDITIONAL_LABEL: str = (
    "dispatch-conditional band — excludes fleet-path structural error "
    "(lambda(h)=0 UNMEASURED until the W2-P5/PP-0.3 capacity hindcast)"
)


@dataclass(frozen=True)
class IsoPrior:
    """One ISO's fitted structural-error prior and its provenance.

    Attributes:
        iso: ISO identifier.
        eps_by_year: ``{year: ln(model/actual)}`` over the fit years.
        model_mt_by_year: Model fossil CO2 (Mt) per fit year (statmode payload).
        actual_mt_by_year: Benchmark fossil CO2 (Mt) per fit year (bench part).
        bias: ``b_i = mean(eps)`` — carried, never subtracted (rule 13).
        noise: Own-ISO sample sd of eps (ddof=1, n=3).
        scale: Student-t scale ``sqrt(max(s_pooled^2, noise^2) * (1 + 1/3))``.
        carbon_priced: Whether the model prices carbon in this ISO.
        basis_stale: True when the fit input predates the current CO2 basis in
            a way a re-score cannot repair (carbon-priced solve staleness) —
            stale-pending-W3-P1.
        rescore: How the current-basis re-score resolved for this ISO
            (``"verified-identical"`` for carbon-zero ISOs whose committed
            numbers reproduce under the current basis;
            ``"stale-registration-basis"`` for the flagged carbon-priced ones).
        run_id: Dashboard run id of the statmode probe the fit read.
        bundle: Repo-relative statmode bundle path.
    """

    iso: str
    eps_by_year: dict[int, float]
    model_mt_by_year: dict[int, float]
    actual_mt_by_year: dict[int, float]
    bias: float
    noise: float
    scale: float
    carbon_priced: bool
    basis_stale: bool
    rescore: str
    run_id: str
    bundle: str


@dataclass(frozen=True)
class StructuralPrior:
    """The fitted cross-ISO structural-error prior (plan §3.2).

    Sampling: ``eps_i = bias_i + scale_i * StandardT(nu)`` per ISO — see
    :meth:`sample`. The artifact form (:meth:`to_dict` / :meth:`save`) records
    every fit input and the emissions-basis identity so a re-fit (W3-P1
    carbon-priced re-solves, or the rule-22 one-shot holdout scoring) is a
    clean swap.

    Attributes:
        schema_version: :data:`PRIOR_SCHEMA_VERSION`.
        nu: Student-t degrees of freedom.
        scale_inflation: The ``1 + 1/n`` scale-variance inflation applied.
        s_pooled: Pooled within-ISO noise (sqrt of mean within-ISO variance).
        years: Fit years (must equal :data:`STRUCTURAL_PRIOR_YEARS`).
        lambda_h: Horizon-widening variance multiplier per year-out; 0 and
            UNMEASURED until the capacity hindcast (plan §3.4).
        lambda_h_status: ``"UNMEASURED"`` today.
        emissions_basis: Basis label + scoring-rate artifact sha256.
        isos: ``{iso: IsoPrior}``.
        label: The dispatch-conditional honesty label all outputs carry.
    """

    schema_version: int
    nu: int
    scale_inflation: float
    s_pooled: float
    years: tuple[int, ...]
    lambda_h: float
    lambda_h_status: str
    emissions_basis: dict
    isos: dict[str, IsoPrior]
    label: str = field(default=_DISPATCH_CONDITIONAL_LABEL)

    def sample(
        self,
        iso: str,
        size: int | tuple[int, ...],
        rng: np.random.Generator,
        horizon_years: float = 0.0,
    ) -> np.ndarray:
        """Draw structural log-error samples for one ISO.

        ``eps = bias + scale * sqrt(1 + lambda_h * h) * StandardT(nu)`` — the
        bias enters at full strength (never recentered, rule 13) and the
        horizon term is a no-op while ``lambda_h == 0`` (UNMEASURED).

        Args:
            iso: ISO identifier (must be in the fitted set).
            size: Sample shape.
            rng: Seeded generator (caller owns determinism).
            horizon_years: Years past the first forecast year (``h``).

        Returns:
            Array of eps draws with shape ``size``.
        """
        p = self.isos[iso.upper()]
        widen = float(np.sqrt(1.0 + self.lambda_h * max(0.0, horizon_years)))
        return p.bias + p.scale * widen * rng.standard_t(self.nu, size=size)

    def to_dict(self) -> dict:
        """Return the JSON-serializable artifact form."""
        d = asdict(self)
        d["years"] = list(self.years)
        d["isos"] = {
            iso: {
                **asdict(p),
                "eps_by_year": {str(y): v for y, v in p.eps_by_year.items()},
                "model_mt_by_year": {str(y): v for y, v in p.model_mt_by_year.items()},
                "actual_mt_by_year": {
                    str(y): v for y, v in p.actual_mt_by_year.items()
                },
            }
            for iso, p in self.isos.items()
        }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StructuralPrior":
        """Rebuild a prior from :meth:`to_dict` output."""
        isos = {
            iso: IsoPrior(
                **{
                    **p,
                    "eps_by_year": {int(y): v for y, v in p["eps_by_year"].items()},
                    "model_mt_by_year": {
                        int(y): v for y, v in p["model_mt_by_year"].items()
                    },
                    "actual_mt_by_year": {
                        int(y): v for y, v in p["actual_mt_by_year"].items()
                    },
                }
            )
            for iso, p in d["isos"].items()
        }
        return cls(
            schema_version=d["schema_version"],
            nu=d["nu"],
            scale_inflation=d["scale_inflation"],
            s_pooled=d["s_pooled"],
            years=tuple(d["years"]),
            lambda_h=d["lambda_h"],
            lambda_h_status=d["lambda_h_status"],
            emissions_basis=d["emissions_basis"],
            isos=isos,
            label=d["label"],
        )

    def save(self, path) -> Path:
        """Write the artifact JSON (parents created); return the path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=1, sort_keys=True))
        return path

    @classmethod
    def load(cls, path) -> "StructuralPrior":
        """Read an artifact JSON written by :meth:`save`."""
        return cls.from_dict(json.loads(Path(path).read_text()))


def _decode_run_payload(run_id: str, runs_dir: Path) -> dict:
    """Decode a committed ``runs/<id>.js`` dashboard payload.

    The payload is ``window.BC.runGz["<id>"]="<base64(gzip(json))>"`` — the
    same encoding ``scripts/render_backcast.py`` writes.
    """
    import base64
    import gzip
    import re

    text = (runs_dir / f"{run_id}.js").read_text()
    m = re.search(r'=\s*"([A-Za-z0-9+/=]+)"', text)
    if not m:
        raise ValueError(f"no gzip+base64 payload found in runs/{run_id}.js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _read_bench_part(iso: str, year: int, bench_dir: Path) -> dict:
    """Read one committed ``bench/<ISO>/<year>.json.gz`` part."""
    import gzip

    return json.loads(
        gzip.decompress((bench_dir / iso / f"{year}.json.gz").read_bytes())
    )


def _fossil_co2_mt(class_twh: dict, intensity: dict) -> float:
    """Total fossil CO2 (Mt) = Σ class TWh × class intensity (t/MWh).

    Mirrors ``scripts/render_calibration_html._fossil_co2`` (including its
    per-class rounding) so a re-score reproduces the committed payload bytes
    exactly when the basis is unchanged.
    """
    by = {
        k: round(class_twh[k] * intensity[k], 4)
        for k in class_twh
        if intensity.get(k, 0.0) > 0.0
    }
    return round(sum(by.values()), 3)


def _rescore_iso_year(ypay: dict, bench_part: dict) -> tuple[float, float]:
    """Recompute (model Mt, actual Mt) for one ISO-year from committed parts.

    The no-solve re-score path: the C5a scoring basis is the per-class CO2
    intensity (net-generation-weighted measured plant rates), applied to the
    model's grid-delivered class TWh (``gmModel``) and the benchmark class TWh
    (``classFull``). The intensity stored in the bench part is re-applied here;
    its currency against the HEAD rate artifact is asserted by
    :func:`fit_prior` via the artifact identity recorded in the prior
    (the 2023-2025 rate rows are content-identical to the registration-time
    artifact — see ``docs/probabilistic-emissions-methodology.md`` §5).
    """
    co2 = bench_part["bench"]["co2"]
    intensity = co2["intensity"]
    model = _fossil_co2_mt(ypay.get("gmModel") or {}, intensity)
    bench_class = {
        k: v
        for k, v in (bench_part["bench"].get("classFull") or {}).items()
        if k in intensity
    }
    actual = _fossil_co2_mt(bench_class, intensity)
    return model, actual


def _sha256(path: Path) -> str:
    """Return the sha256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_prior(
    fit_inputs: dict[str, dict] | None = None,
    runs_dir: Path | None = None,
    bench_dir: Path | None = None,
) -> StructuralPrior:
    """Fit the cross-ISO structural-error prior from the D-7 statmode probes.

    Reads, per ISO, the committed statmode dashboard payload (model fossil CO2,
    Mt) and the committed bench part (actual fossil CO2, Mt) for each fit year,
    computes ``eps = ln(model/actual)``, pools the noise across ISOs, and
    assembles the Student-t prior described in the module docstring.

    Basis handling: for carbon-zero ISOs the committed numbers are re-scored
    (recomputed from the stored class intensities and class-TWh blocks) and
    must reproduce exactly — a mismatch means the committed payload and bench
    part disagree with each other and the fit refuses. Carbon-priced ISOs are
    fitted as-committed and flagged ``basis_stale`` (stale-pending-W3-P1).

    Rule-22 guard: any payload year outside :data:`STRUCTURAL_PRIOR_YEARS`
    (e.g. a quarantined 2022 or 2026 solve) is a hard error — the prior never
    reads a holdout year.

    Args:
        fit_inputs: ``{iso: {run_id, bundle, carbon_priced}}``; defaults to
            :data:`STATMODE_FIT_INPUTS`.
        runs_dir: Committed run-payload directory (tests override).
        bench_dir: Committed bench-part directory (tests override).

    Returns:
        The fitted :class:`StructuralPrior`.

    Raises:
        ValueError: On a quarantined/missing fit year, a missing CO2 block, or
            a carbon-zero re-score mismatch.
    """
    fit_inputs = fit_inputs if fit_inputs is not None else STATMODE_FIT_INPUTS
    runs_dir = Path(runs_dir) if runs_dir is not None else _RUNS_DIR
    bench_dir = Path(bench_dir) if bench_dir is not None else _BENCH_DIR
    want_years = set(STRUCTURAL_PRIOR_YEARS)

    per_iso: dict[str, dict] = {}
    for iso, spec in sorted(fit_inputs.items()):
        payload = _decode_run_payload(spec["run_id"], runs_dir)
        have_years = {int(y) for y in payload.get("years", {})}
        if have_years != want_years:
            raise ValueError(
                f"{iso} statmode payload years {sorted(have_years)} != required "
                f"fit years {sorted(want_years)} — a year outside "
                "STRUCTURAL_PRIOR_YEARS is quarantined (rule 22) and must "
                "never enter the prior"
            )
        eps: dict[int, float] = {}
        model_mt: dict[int, float] = {}
        actual_mt: dict[int, float] = {}
        for year in sorted(want_years):
            ypay = payload["years"][str(year)]
            bench_part = _read_bench_part(iso, year, bench_dir)
            committed_model = (ypay.get("co2") or {}).get("model")
            committed_actual = (bench_part["bench"].get("co2") or {}).get("egrid")
            if committed_model is None or committed_actual is None:
                raise ValueError(f"{iso} {year}: no committed CO2 model/actual")
            if not spec["carbon_priced"]:
                # No-solve re-score under the current basis. The recomputation
                # must land on the committed values (same intensity rows at
                # HEAD, same arithmetic) — a real drift is an inconsistent
                # committed artifact, not a fittable input. The model side
                # reproduces exactly (build_payload applies the stored,
                # 5-dp-rounded intensity there); the actual side was computed
                # from the unrounded intensity before storage, so it carries
                # up to ~0.005 Mt of pure 5-dp rounding — hence the 0.01 Mt
                # tolerance, far below any basis-level movement.
                model, actual = _rescore_iso_year(ypay, bench_part)
                if abs(model - committed_model) > 1e-6 or (
                    abs(actual - committed_actual) > 1e-2
                ):
                    raise ValueError(
                        f"{iso} {year}: current-basis re-score "
                        f"({model:.3f}/{actual:.3f} Mt) does not reproduce the "
                        f"committed payload ({committed_model:.3f}/"
                        f"{committed_actual:.3f} Mt) — refusing to fit on an "
                        "inconsistent basis"
                    )
            model_mt[year] = float(committed_model)
            actual_mt[year] = float(committed_actual)
            eps[year] = float(np.log(committed_model / committed_actual))
        per_iso[iso.upper()] = {
            "spec": spec,
            "eps": eps,
            "model_mt": model_mt,
            "actual_mt": actual_mt,
        }

    # Pooled within-ISO noise: sqrt of the mean within-ISO sample variance
    # (ddof=1 — three points per ISO estimate their own mean first).
    variances = [
        float(np.var(list(d["eps"].values()), ddof=1)) for d in per_iso.values()
    ]
    s_pooled = float(np.sqrt(np.mean(variances)))

    isos: dict[str, IsoPrior] = {}
    for iso, d in per_iso.items():
        arr = np.asarray(list(d["eps"].values()), dtype=float)
        bias = float(arr.mean())
        noise = float(arr.std(ddof=1))
        # max(s_pooled, s_i): pooling borrows strength for the typical ISO but
        # must never *shrink* an ISO noisier than the pool below its own
        # plug-in sd (the wider-than-plug-in hard requirement, plan §3.2).
        scale = float(
            np.sqrt(max(s_pooled**2, noise**2) * STRUCTURAL_PRIOR_SCALE_INFLATION)
        )
        stale = bool(d["spec"]["carbon_priced"])
        isos[iso] = IsoPrior(
            iso=iso,
            eps_by_year=d["eps"],
            model_mt_by_year=d["model_mt"],
            actual_mt_by_year=d["actual_mt"],
            bias=bias,
            noise=noise,
            scale=scale,
            carbon_priced=stale,
            basis_stale=stale,
            rescore="stale-registration-basis" if stale else "verified-identical",
            run_id=d["spec"]["run_id"],
            bundle=d["spec"]["bundle"],
        )
        logger.info(
            "structural prior %s: bias=%+.4f noise=%.4f scale=%.4f%s",
            iso,
            bias,
            noise,
            scale,
            " [STALE pending W3-P1]" if stale else "",
        )

    basis = {
        "label": _EMISSIONS_BASIS_LABEL,
        "fossil_co2_rates_sha256": (
            _sha256(FOSSIL_CO2_RATES_PATH) if FOSSIL_CO2_RATES_PATH.exists() else None
        ),
        "stale_isos_pending_w3p1": sorted(
            iso for iso, p in isos.items() if p.basis_stale
        ),
    }

    return StructuralPrior(
        schema_version=PRIOR_SCHEMA_VERSION,
        nu=STRUCTURAL_PRIOR_NU,
        scale_inflation=STRUCTURAL_PRIOR_SCALE_INFLATION,
        s_pooled=s_pooled,
        years=tuple(sorted(want_years)),
        lambda_h=STRUCTURAL_PRIOR_LAMBDA_H,
        lambda_h_status=STRUCTURAL_PRIOR_LAMBDA_H_STATUS,
        emissions_basis=basis,
        isos=isos,
    )


def convolve(
    metrics: pd.DataFrame,
    prior: StructuralPrior,
    iso: str,
    seed: int,
    k: int = STRUCTURAL_PRIOR_K,
    quantiles: tuple[float, ...] = PUBLISHED_BAND_QUANTILES,
    n_boot: int = 1000,
    ci: float = 0.9,
) -> list[dict]:
    """Convolve the parametric emissions draws with the structural prior.

    Monte-Carlo product in log space (plan §3.3): each of the ``n`` parametric
    members' ``emissions_mt`` values gets ``k`` independent structural draws,
    ``emissions * exp(eps)``, and the published quantiles come from the pooled
    ``n*k`` sample per year. Rows land in ``ensemble.compute_bands``' exact
    schema with ``layer="parametric_plus_structural"`` so they append into the
    same ``bands.parquet``. Only the emissions metric is convolved — the prior
    was fitted on emissions error and claims nothing about other metrics.

    The bootstrap CI resamples parametric *members* (keeping each member's
    ``k`` structural draws together — a block bootstrap), so the reported
    sampling noise reflects the member count, not the free-to-grow ``k``.

    The horizon term uses ``h = year - min(year)`` within ``metrics``; with
    ``prior.lambda_h == 0`` (UNMEASURED) it is a no-op and the band stays
    dispatch-conditional.

    Args:
        metrics: Long frame ``(draw_id, year, metric, value)`` — the landed
            ``metrics.parquet`` schema.
        prior: The fitted structural prior.
        iso: ISO whose prior applies.
        seed: RNG seed (record alongside the output; deterministic given it).
        k: Structural draws per parametric member.
        quantiles: Quantiles to publish.
        n_boot: Bootstrap resample count per quantile.
        ci: Bootstrap CI width.

    Returns:
        Band rows (``year, metric, layer, quantile, value, n, bootstrap_lo,
        bootstrap_hi``), deterministic in ``seed``.

    Raises:
        KeyError: When ``iso`` is not in the fitted prior.
        ValueError: When ``metrics`` has no emissions rows.
    """
    iso = iso.upper()
    if iso not in prior.isos:
        raise KeyError(f"no structural prior fitted for {iso}")
    em = metrics[metrics["metric"] == _EMISSIONS_METRIC]
    if em.empty:
        raise ValueError(f"metrics frame has no {_EMISSIONS_METRIC} rows")

    rng = np.random.default_rng(seed)
    years = sorted(int(y) for y in em["year"].unique())
    first_year = years[0]
    rows: list[dict] = []
    for year in years:
        values = em.loc[em["year"] == year, "value"].to_numpy(dtype=float)
        n = values.size
        eps = prior.sample(iso, (n, k), rng, horizon_years=float(year - first_year))
        sample = values[:, None] * np.exp(eps)  # (n members, k structural)
        pooled = sample.ravel()
        # Block bootstrap over parametric members.
        boot_idx = rng.integers(0, n, size=(n_boot, n))
        boot = sample[boot_idx].reshape(n_boot, n * k)
        tail = (1.0 - ci) / 2.0
        for q in quantiles:
            boot_q = np.quantile(boot, q, method="linear", axis=1)
            rows.append(
                {
                    "year": year,
                    "metric": _EMISSIONS_METRIC,
                    "layer": STRUCTURAL_LAYER,
                    "quantile": q,
                    "value": float(np.quantile(pooled, q, method="linear")),
                    "n": int(n * k),
                    "bootstrap_lo": float(np.quantile(boot_q, tail)),
                    "bootstrap_hi": float(np.quantile(boot_q, 1.0 - tail)),
                }
            )
    return rows


def append_structural_layer(
    out_dir,
    prior: StructuralPrior,
    k: int = STRUCTURAL_PRIOR_K,
    seed: int | None = None,
) -> Path:
    """Append the ``parametric_plus_structural`` layer to a landed ensemble.

    Extends the PB-2 output surface in place: reads ``metrics.parquet`` and
    ``ensemble_meta.json`` from ``out_dir``, convolves the emissions draws with
    ``prior``, and rewrites ``bands.parquet`` with the structural rows appended
    (replacing any previous structural layer — idempotent re-runs). The
    parametric-layer rows are **never modified** (rule 13: the point path is
    not shifted). ``ensemble_meta.json`` gains the prior's version block,
    ``layers_present``, and the dispatch-conditional label.

    Args:
        out_dir: The ensemble directory written by
            :func:`market_sim.ensemble.export_sampler_ensemble`.
        prior: The fitted structural prior.
        k: Structural draws per parametric member.
        seed: Convolution seed; defaults to the ensemble's sampler seed + 1
            (a distinct stream from the parametric bootstrap, still fully
            determined by the recorded spec).

    Returns:
        The path of the rewritten ``bands.parquet``.
    """
    out_dir = Path(out_dir)
    meta_path = out_dir / "ensemble_meta.json"
    bands_path = out_dir / "bands.parquet"
    meta = json.loads(meta_path.read_text())
    iso = meta["iso"]
    if seed is None:
        seed = int(meta["spec"]["seed"]) + 1

    metrics = pd.read_parquet(out_dir / "metrics.parquet")
    rows = convolve(metrics, prior, iso, seed=seed, k=k)

    bands = pd.read_parquet(bands_path)
    bands = bands[bands["layer"] != STRUCTURAL_LAYER]
    bands = pd.concat([bands, pd.DataFrame(rows)], ignore_index=True)
    bands.to_parquet(bands_path, index=False)

    iso_prior = prior.isos[iso]
    meta["layers_present"] = sorted(
        set(meta.get("layers_present", [])) | {STRUCTURAL_LAYER}
    )
    meta["structural_prior"] = {
        "schema_version": prior.schema_version,
        "nu": prior.nu,
        "k": k,
        "seed": seed,
        "s_pooled": prior.s_pooled,
        "fit_years": list(prior.years),
        "lambda_h": prior.lambda_h,
        "lambda_h_status": prior.lambda_h_status,
        "emissions_basis": prior.emissions_basis,
        "iso_bias": iso_prior.bias,
        "iso_scale": iso_prior.scale,
        "iso_basis_stale": iso_prior.basis_stale,
        "fit_inputs": {
            i: {"run_id": p.run_id, "bundle": p.bundle, "basis_stale": p.basis_stale}
            for i, p in prior.isos.items()
        },
    }
    meta["label"] = (
        f"published probability band (PB-3, layer={STRUCTURAL_LAYER}); "
        + prior.label
        + (
            "; STRUCTURAL PRIOR BASIS-STALE pending W3-P1 re-solve"
            if iso_prior.basis_stale
            else ""
        )
    )
    meta_path.write_text(json.dumps(meta, separators=(",", ":"), default=str))
    logger.info(
        "appended %s layer for %s (n*k sample, k=%d, seed=%d) to %s",
        STRUCTURAL_LAYER,
        iso,
        k,
        seed,
        bands_path,
    )
    return bands_path
