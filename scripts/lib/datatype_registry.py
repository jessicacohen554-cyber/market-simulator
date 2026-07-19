"""Factory for the per-datatype ISO registries under ``scripts/lib/<datatype>/``.

Most curated datatypes share the same registry scaffolding: a frozen
``IsoSpec`` dataclass that per-ISO sibling modules register at import time, a
``REGISTRY`` dict, an idempotent import-walk loader, a raw-directory resolver,
and a canonical-dtype ``finalize`` that coerces + reorders + sorts a parsed
frame. Only the *data-specific* pieces differ per datatype (the columns, the
extra spec fields, the controlled-vocabulary checks, and the unified-CSV
parser).

:func:`make_registry` builds the shared scaffolding from a small declarative
config so a datatype's ``__init__.py`` declares only what is genuinely
datatype-specific and re-exports the machinery::

    _R = make_registry(
        DATATYPE, CANONICAL_COLUMNS,
        [("iso", str), ("default_area_type", str),
         ("metric_aliases", dict, field(default_factory=dict)), ...],
        package=__name__, iso_modules=("pjm", "miso", ...),
        raw_subpath=(DATATYPE,), string_cols=_STRING_COLS,
        float_cols=_FLOAT_COLS, sort_by=("delivery_year", ...),
    )
    IsoSpec, REGISTRY, register = _R.IsoSpec, _R.REGISTRY, _R.register
    load_registry, raw_dir_for, finalize = _R.load_registry, _R.raw_dir_for, _R.finalize

The datatype's ``validate_tidy`` / ``parse_unified_csv`` / ``parse_iso`` stay in
the package (they carry the value-level vocab rules and the source-specific
reshaping) and use the ``finalize`` this factory produced.
"""

from __future__ import annotations

import importlib
from dataclasses import make_dataclass
from pathlib import Path
from typing import Callable, Sequence


class Registry:
    """The shared registry machinery a datatype package re-exports.

    Attributes mirror the module-level names the packages have always exposed:
    ``IsoSpec`` (the frozen dataclass), ``REGISTRY`` (ISO-label -> spec), and the
    ``register`` / ``load_registry`` / ``raw_dir_for`` / ``finalize`` callables.
    """

    def __init__(
        self,
        *,
        datatype: str,
        canonical_columns: tuple[str, ...],
        IsoSpec: type,
        REGISTRY: dict,
        register: Callable,
        load_registry: Callable,
        raw_dir_for: Callable,
        finalize: Callable,
    ) -> None:
        self.datatype = datatype
        self.canonical_columns = canonical_columns
        self.IsoSpec = IsoSpec
        self.REGISTRY = REGISTRY
        self.register = register
        self.load_registry = load_registry
        self.raw_dir_for = raw_dir_for
        self.finalize = finalize


def make_registry(
    datatype: str,
    canonical_columns: Sequence[str],
    spec_fields: Sequence[tuple],
    *,
    package: str,
    iso_modules: Sequence[str],
    raw_subpath: Sequence[str],
    string_cols: Sequence[str],
    float_cols: Sequence[str],
    int_cols: Sequence[str] = (),
    sort_by: Sequence[str],
    na_position: str = "last",
    register_check: Callable | None = None,
) -> Registry:
    """Build the shared registry machinery for one datatype.

    Args:
        datatype: hyphenated datatype name (matches the schema file stem).
        canonical_columns: the tidy column order the finalizer emits.
        spec_fields: :func:`dataclasses.make_dataclass` field specs for
            ``IsoSpec`` — ``(name, type)`` for a required field or
            ``(name, type, default)`` for one with a default (must include the
            required ``iso`` field first).
        package: the calling package's ``__name__`` — used to import the ISO
            sibling modules and to stamp ``IsoSpec.__module__``.
        iso_modules: sibling module names to import so their ``register`` runs.
        raw_subpath: path parts under ``raw_root`` before the ``<iso>`` dir.
        string_cols: columns coerced to the pandas ``string`` dtype.
        float_cols: columns coerced to ``float64``.
        int_cols: further numeric columns coerced to ``float64`` (kept separate
            for parity with packages that classified an integer-like column).
        sort_by: columns the finalizer sorts on.
        na_position: ``"last"`` or ``"first"`` for the finalizer sort.
        register_check: optional ``(spec) -> None`` validator run before a spec
            is stored (raises on invalid input).

    Returns:
        A :class:`Registry` bundling ``IsoSpec`` and the shared callables.
    """
    import pandas as pd

    canonical_columns = tuple(canonical_columns)
    string_cols = tuple(string_cols)
    float_cols = tuple(float_cols)
    int_cols = tuple(int_cols)
    sort_by = list(sort_by)

    IsoSpec = make_dataclass("IsoSpec", list(spec_fields), frozen=True)
    IsoSpec.__module__ = package
    IsoSpec.__doc__ = f"Declarative description of one ISO's {datatype} source."

    REGISTRY: dict = {}
    _state = {"loaded": False}

    def register(spec):
        """Register an ``IsoSpec`` under its ISO label. Returns the spec."""
        if register_check is not None:
            register_check(spec)
        REGISTRY[spec.iso.upper()] = spec
        return spec

    def load_registry() -> dict:
        """Import every available ISO module (idempotent) and return the registry."""
        if not _state["loaded"]:
            for name in iso_modules:
                try:
                    importlib.import_module(f"{package}.{name}")
                except ModuleNotFoundError:
                    continue  # ISO not implemented yet — additive by design.
            _state["loaded"] = True
        return REGISTRY

    def raw_dir_for(iso: str, raw_root: Path) -> Path:
        """Directory holding an ISO's raw ``{datatype}`` inputs."""
        d = Path(raw_root)
        for part in raw_subpath:
            d = d / part
        return d / iso.lower()

    def finalize(df):
        """Coerce a parsed frame to the canonical dtypes + column order."""
        out = df.copy()
        for col in canonical_columns:
            if col not in out.columns:
                out[col] = pd.NA
        for col in string_cols:
            out[col] = out[col].astype("string")
        for col in (*float_cols, *int_cols):
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
        out = out[list(canonical_columns)]
        out = out.sort_values(sort_by, na_position=na_position).reset_index(drop=True)
        return out

    return Registry(
        datatype=datatype,
        canonical_columns=canonical_columns,
        IsoSpec=IsoSpec,
        REGISTRY=REGISTRY,
        register=register,
        load_registry=load_registry,
        raw_dir_for=raw_dir_for,
        finalize=finalize,
    )
