"""Content-addressed on-disk memo for small derived mappings.

The generalization of :mod:`market_sim.data.egrid_sheets` (wall-clock item
A-2) to derivations whose result is a *mapping* rather than a DataFrame.
Wall-clock item A-4: a handful of ``data_prep`` sites are pure functions of
bytes already on disk, cost seconds of CPU, and are memoized only by
``functools.lru_cache`` — so every process pays them again in whichever year
first touches them, which is exactly the year-1 ``data_prep`` premium
(``docs/handoffs/wallclock-baseline-2026-07.md`` §WALLCLOCK A-4).

The pattern, unchanged from A-2 and restated so this module reads on its own:

* **Content-addressed, hence self-invalidating.** The memo file name carries a
  sha256 digest over *every* source file's bytes together with the caller's
  own parameters. A repaired or re-released source hashes differently, so its
  memo simply does not exist yet and is recomputed; a stale memo can never be
  served for changed source bytes. Nothing is invalidated by hand and there is
  no configuration flag.
* **JSON, never pickle.** A-2 mirrors a DataFrame and uses parquet; a mapping
  of ``{int: float}`` / ``{int: str}`` is JSON, which has the same property
  that matters — there is no ``allow_pickle`` path and no executable payload,
  nothing that could deserialize into code — and, unlike parquet, no library
  metadata to shift under a pyarrow upgrade. Every value read back is re-typed
  and re-validated before it reaches a caller (:func:`_decode_mapping`).
* **Exact, or not memoized at all.** ``json`` serializes a float through
  ``repr``, i.e. the shortest string that round-trips to the identical double,
  so a memo read is bit-equal to the computation it replaces. The one case
  where that argument does not hold is a non-finite value (``NaN`` never
  compares equal to itself), so a mapping carrying one is **refused** for
  writing and recomputed forever rather than served from a memo whose identity
  cannot be proved. The byte gate is ``atol=rtol=0``; nothing here may weaken
  it.
* **Advisory, never authoritative.** Any failure anywhere — unhashable source,
  unwritable directory, corrupt or hand-edited JSON, a value of the wrong type
  — is logged and falls back to the caller's own ``compute``. The memo is a
  cache, so a degraded cache costs wall-clock and nothing else.
* **A fresh object per call.** Both branches hand back a mapping this call
  built, so a caller that mutates its result can never poison a later one.

Wall-clock only: this module changes no value the LP ever sees.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
from pathlib import Path
from typing import Callable, Sequence, TypeVar

logger = logging.getLogger(__name__)

#: Bytes per chunk when digesting a source file. 1 MiB keeps a 21 MB workbook
#: hash off the peak-RSS ledger entirely (rule 12's concurrency cap is
#: memory-bound). Same value, and same reason, as ``egrid_sheets``.
_HASH_CHUNK_BYTES: int = 1 << 20

#: Characters of the hex digest kept in a memo file name. 16 hex chars is
#: 64 bits — collision-free for the handful of (sources, params) combinations
#: that exist, and short enough to keep the name readable. Shared with
#: ``egrid_sheets`` so the two families of derivative files look alike.
_DIGEST_CHARS: int = 16

_V = TypeVar("_V", float, str)


def content_digest(
    sources: Sequence[Path],
    params: Sequence[str] = (),
    chars: int = _DIGEST_CHARS,
) -> str:
    """Return the short hex digest identifying one (sources, params) pair.

    Hashes each source file's bytes in order, then the caller's parameters, so
    the digest changes when *either* the source data or the requested
    derivation changes.

    Parameters are length-prefixed before hashing so no two parameter tuples
    can serialize identically (``("ab", "c")`` and ``("a", "bc")`` differ).

    Args:
        sources: Source files, in a caller-fixed order. Every one is read.
        params: Extra strings identifying the derivation (sheet names, column
            lists, a namespace, a value type).
        chars: Hex characters of the digest to keep.

    Returns:
        The leading ``chars`` hex characters of the sha256 digest.

    Raises:
        OSError: If a source file cannot be read.
    """
    digest = hashlib.sha256()
    for source in sources:
        with Path(source).open("rb") as handle:
            for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
                digest.update(chunk)
    for part in params:
        digest.update(f"{len(part)}:{part}".encode())
    return digest.hexdigest()[:chars]


def _memo_path(anchor: Path, namespace: str, digest: str) -> Path:
    """Return the memo file path for one derivation.

    ``<anchor-stem>.<digest>.<namespace>.json``, beside the anchor source —
    the A-2 layout, in a directory ``.gitignore`` already excludes, so a memo
    is never committed.
    """
    return anchor.with_name(f"{anchor.stem}.{digest}.{namespace}.json")


def _encodable(mapping: dict[int, _V], value_type: type) -> bool:
    """Return True when ``mapping`` round-trips through JSON exactly.

    Keys must be ints (they serialize as decimal strings and parse back
    unambiguously) and values must be exactly ``value_type``. A float value
    must additionally be finite: ``NaN`` is not equal to itself, so a memo
    holding one could never be *proved* identical to the computation it
    replaces, and this module refuses to write what it cannot prove.
    """
    for key, value in mapping.items():
        if type(key) is not int or type(value) is not value_type:
            return False
        if value_type is float and not math.isfinite(value):
            return False
    return True


def _decode_mapping(raw: object, value_type: type[_V]) -> dict[int, _V] | None:
    """Re-type a parsed JSON object into ``{int: value_type}``, or ``None``.

    Returns ``None`` — meaning "recompute" — for anything that is not exactly
    a flat object of int-parseable keys mapping to values of the requested
    type. Deliberately strict: a memo is machine-local, disposable and
    unauthenticated, so it is re-validated rather than trusted.
    """
    if not isinstance(raw, dict):
        return None
    out: dict[int, _V] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            return None
        try:
            ikey = int(key)
        except ValueError:
            return None
        if value_type is float:
            # ``json`` parses an unsuffixed integer literal as ``int``; a
            # float-valued mapping whose value happens to be integral (6.0)
            # therefore returns as ``6``. Accept and re-type it — but never a
            # bool, which is an ``int`` subclass and is not a heat rate.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            fvalue = float(value)
            if not math.isfinite(fvalue):
                return None
            out[ikey] = fvalue  # type: ignore[assignment]
        else:
            if not isinstance(value, str):
                return None
            out[ikey] = value  # type: ignore[assignment]
    return out


def _write_memo(mapping: dict[int, _V], memo: Path) -> None:
    """Write ``mapping`` to ``memo`` atomically; log and give up on failure.

    Written to a process-unique temporary name in the same directory and then
    ``os.replace``d into place, so a concurrent reader (rule 12 permits two
    simultaneous invocations) sees either no memo or a complete one — never a
    half-written file.
    """
    tmp = memo.with_name(f"{memo.name}.{os.getpid()}.tmp")
    try:
        # ``allow_nan=False`` is belt-and-braces over ``_encodable``: a
        # non-finite value raises here rather than emitting the non-standard
        # ``NaN`` token.
        tmp.write_text(
            json.dumps({str(k): v for k, v in mapping.items()}, allow_nan=False)
        )
        os.replace(tmp, memo)
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("disk memo write failed (%s): %s", memo.name, exc)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def memoized_mapping(
    namespace: str,
    sources: Sequence[Path],
    compute: Callable[[], dict[int, _V]],
    value_type: type[_V],
    params: Sequence[str] = (),
) -> dict[int, _V]:
    """Return ``compute()``, served from a content-addressed memo when possible.

    Equivalent in every observable way to calling ``compute()`` — the memo
    holds the identical mapping, keys and values re-typed to the same Python
    types, and is invalidated automatically by any change to ``sources``.

    Args:
        namespace: Short identifier for the derivation; part of the memo's
            digest and of its file name, so two derivations over the same
            sources can never collide.
        sources: The on-disk inputs the derivation reads, in a fixed order.
            The first is the *anchor*: the memo is written beside it.
        compute: The derivation. Called on a memo miss, and on every failure
            of the memo path.
        value_type: ``float`` or ``str`` — the mapping's value type, enforced
            on both write and read.
        params: Extra strings identifying this derivation's variant (a flag, a
            vintage year). Folded into the digest.

    Returns:
        ``{int: value_type}``, a fresh dict on every call.
    """
    memo: Path | None
    anchor = Path(sources[0])
    try:
        memo = _memo_path(
            anchor,
            namespace,
            content_digest(sources, (namespace, value_type.__name__, *params)),
        )
    except OSError as exc:  # unreadable source — let ``compute`` report it
        logger.warning("disk memo digest failed (%s): %s", namespace, exc)
        memo = None

    if memo is not None and memo.exists():
        try:
            decoded = _decode_mapping(json.loads(memo.read_text()), value_type)
        except Exception as exc:  # noqa: BLE001 - any unreadable memo recomputes
            # Deliberately broad: a corrupt, truncated or hand-edited memo must
            # degrade to the computation rather than fail the solve.
            logger.warning("disk memo read failed (%s): %s", memo.name, exc)
            decoded = None
        if decoded is not None:
            return decoded
        logger.warning("disk memo rejected as malformed (%s)", memo.name)

    result = compute()
    if memo is not None and _encodable(result, value_type):
        _write_memo(result, memo)
    return result
