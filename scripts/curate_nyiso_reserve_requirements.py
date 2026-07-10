"""Curate the ``nyiso-reserve-requirements`` and ``nyiso-operating-events`` datatypes.

Both flow from ``data/raw/NYISO-AS/requirements/`` (Ask B of
``docs/handoffs/nyiso-data-asks-2026-07.md`` — the measured inputs for the
issue-#1344 condition-varying downstate reserve requirement reconstruction):

* ``nyiso-reserve-requirements`` — the hand-transcribed published locational
  reserve requirement schedule (``nyiso_locational_reserve_requirements.csv``,
  one row per dated-version x region x product x period), written as a single
  spanning partition (``year=None``; the version evidence dates are columns).
* ``nyiso-operating-events`` — typed events parsed from the per-year MIS
  message logs (``realtime-events/``, ``oper-messages/``; fetched by
  ``scripts/fetch_nyiso_operating_events.py``): Thunderstorm Alert start/end,
  system state changes, reserve pick-ups, emergency capacity requests,
  out-of-merit reliability commitments and emergency energy transactions.
  Parse-only — window reconstruction/interpretation belongs to the consumer.
  Unmatched messages (price-correction notices etc.) stay in raw. Written as
  one spanning partition in source order with a stable ``seq``.

The extraction vocabulary was derived from a template census of the full
2018-2026H1 corpus (85 RealTimeEvents templates; the OperMessages OOM and
emergency-transaction families) — see the schema YAMLs for the controlled
vocabulary.

Run ``python scripts/curate_nyiso_reserve_requirements.py``.
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402

REQUIREMENTS_DATATYPE = "nyiso-reserve-requirements"
EVENTS_DATATYPE = "nyiso-operating-events"

_REQ_CSV = "nyiso_locational_reserve_requirements.csv"
_TZ = "America/New_York"

# --- RealTimeEvents extraction rules (template census 2018-2026H1) ---------
# Each: (event_type, action, start_of_day, compiled regex). First match wins.
_RTE_RULES: tuple[tuple[str, str, bool, re.Pattern[str]], ...] = (
    (
        "thunderstorm_alert",
        "start",
        False,
        re.compile(r"System now operating in thunderstorm alert", re.I),
    ),
    (
        "thunderstorm_alert",
        "end",
        False,
        re.compile(r"System no longer operating in thunderstorm alert", re.I),
    ),
    (
        "thunderstorm_alert",
        "start",
        True,
        re.compile(r"Start of day thunderstorm alert state is ACTIVE", re.I),
    ),
    (
        "system_state",
        "normal",
        False,
        re.compile(r"State Change\. System now operating in normal state", re.I),
    ),
    (
        "system_state",
        "alert",
        False,
        re.compile(r"State Change\. System now operating in alert state", re.I),
    ),
    (
        "system_state",
        "major_emergency",
        False,
        re.compile(
            r"State Change\. System now operating in major emergency state", re.I
        ),
    ),
    (
        "system_state",
        "normal",
        True,
        re.compile(
            r"Start of day system state is NORMAL|The start of the day is normal", re.I
        ),
    ),
    (
        "system_state",
        "alert",
        True,
        re.compile(r"Start of day system state is ALERT", re.I),
    ),
    (
        "system_state",
        "major_emergency",
        True,
        re.compile(r"Start of day system state is MAJOR EMERGENCY", re.I),
    ),
    (
        "reserve_pickup",
        "start",
        False,
        re.compile(r"NYISO has initiated reserve pick-?up", re.I),
    ),
    (
        "reserve_pickup",
        "end",
        False,
        re.compile(r"NYISO has terminated reserve pick-?up", re.I),
    ),
)
_RTE_CAPACITY = re.compile(
    r"Capacity request has been submitted for Proxy:\s*([A-Z0-9_-]+)", re.I
)

# --- OperMessages extraction rules -----------------------------------------
_OM_OOM = re.compile(
    r"^(?P<requestor>.*?)\s*(?P<verb>REQUESTS|UPDATES|REMOVES)\s+(?P<unit>.+?)\s+OUT OF MERIT",
    re.S,
)
_OM_EMERG = re.compile(
    r"^(?P<party>.+?)\s+Emergency transaction\s+(?P<verb>added|cut)\s+(?P<mw>\d+(?:\.\d+)?)\s*MWs?",
    re.I,
)
_OM_VERB_ACTION = {"REQUESTS": "requested", "UPDATES": "updated", "REMOVES": "removed"}


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _raw_dir(raw_root: Path) -> Path:
    return raw_root / "NYISO-AS" / "requirements"


# ---------------------------------------------------------------------------
# nyiso-reserve-requirements
# ---------------------------------------------------------------------------
def build_requirements_frame(raw_root: Path) -> pd.DataFrame:
    """Read and dtype-shape the transcribed requirement schedule onto its schema."""
    df = pd.read_csv(_raw_dir(raw_root) / _REQ_CSV)
    df.insert(0, "iso", "NYISO")
    df["hb_start"] = df["hb_start"].astype("float64")  # nullable int as float
    df["hb_end"] = df["hb_end"].astype("float64")
    df["requirement_mw"] = df["requirement_mw"].astype("float64")
    df["tsa_reduced_to_zero"] = df["tsa_reduced_to_zero"].astype(bool)
    df["evidence_start"] = pd.to_datetime(df["evidence_start"])
    df["evidence_end"] = pd.to_datetime(df["evidence_end"])
    df["notes"] = df["notes"].where(df["notes"].notna(), None)
    return df


# ---------------------------------------------------------------------------
# nyiso-operating-events
# ---------------------------------------------------------------------------
def _classify_rte(msg: str) -> tuple[str, str, bool, str | None, float | None] | None:
    """Classify one Real-Time Events message; None when not an event."""
    text = msg.strip()
    for event_type, action, sod, rx in _RTE_RULES:
        if rx.search(text):
            return event_type, action, sod, None, None
    m = _RTE_CAPACITY.search(text)
    if m:
        return "capacity_request", "submitted", False, m.group(1), None
    return None


def _classify_om(msg: str) -> tuple[str, str, bool, str | None, float | None] | None:
    """Classify one Operational Announcements message; None when not an event."""
    text = msg.strip()
    m = _OM_EMERG.match(text)
    if m:
        return (
            "emergency_transaction",
            m.group("verb").lower(),
            False,
            m.group("party").strip(),
            float(m.group("mw")),
        )
    m = _OM_OOM.match(text)
    if m:
        return (
            "oom_commitment",
            _OM_VERB_ACTION[m.group("verb")],
            False,
            m.group("unit").strip(),
            None,
        )
    return None


def _localize(ts: pd.Series) -> pd.Series:
    """Eastern prevailing wall-clock -> UTC, fall-back hour first-occurrence=EDT.

    Duplicate wall-clock stamps (the November repeated hour) are resolved in
    source order: pandas ``ambiguous="infer"`` needs monotonic input, which
    message logs are not guaranteed to be, so mark the first occurrence of
    each duplicated stamp as DST. The spring-forward gap gets shifted forward.
    """
    first = ~ts.duplicated(keep="first")
    return ts.dt.tz_localize(
        _TZ, ambiguous=first.to_numpy(), nonexistent="shift_forward"
    ).dt.tz_convert("UTC")


def _parse_stamps(raw: pd.Series, formats: tuple[str, ...]) -> pd.Series:
    """Parse wall-clock strings with an ordered deterministic format fallback.

    The RealTimeEvents feed mixes "MM/DD/YYYY HH:MM:SS" with a legacy
    "M/D/YYYY H:MM" (no seconds, no zero-padding); no per-element format
    inference is used — each candidate format is tried in order.
    """
    out = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    for fmt in formats:
        mask = out.isna()
        if not mask.any():
            break
        out[mask] = pd.to_datetime(raw[mask], format=fmt, errors="coerce")
    if out.isna().any():
        bad = raw[out.isna()].iloc[0]
        raise ValueError(f"unparseable timestamp {bad!r} for formats {formats}")
    return out


def build_events_frame(raw_root: Path) -> pd.DataFrame:
    """Parse both message-log feeds into the typed-event schema shape."""
    specs = (
        (
            "realtime_events",
            "realtime-events",
            ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"),
            _classify_rte,
        ),
        ("oper_messages", "oper-messages", ("%d-%b-%Y %H:%M",), _classify_om),
    )
    out_rows: list[dict] = []
    for source_dataset, subdir, ts_formats, classify in specs:
        files = sorted((_raw_dir(raw_root) / subdir).glob("*.csv"))
        seq = 0
        for f in files:
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                seq += 1
                hit = classify(str(row["message"]))
                if hit is None:
                    continue
                event_type, action, sod, detail, mw = hit
                out_rows.append(
                    {
                        "iso": "NYISO",
                        "source_dataset": source_dataset,
                        "seq": seq,
                        "timestamp_raw": str(row["timestamp_local"]),
                        "ts_formats": ts_formats,
                        "event_type": event_type,
                        "action": action,
                        "start_of_day": sod,
                        "detail": detail,
                        "mw": mw,
                        "message": str(row["message"]),
                        "source_file": str(row["source_file"]),
                    }
                )
    events = pd.DataFrame(out_rows)
    events["timestamp_local"] = events.groupby(
        "source_dataset", group_keys=False
    ).apply(
        lambda g: _parse_stamps(g["timestamp_raw"], g["ts_formats"].iloc[0]),
        include_groups=False,
    )
    events = events.drop(columns=["timestamp_raw", "ts_formats"])
    events["timestamp_utc"] = events.groupby("source_dataset", group_keys=False)[
        "timestamp_local"
    ].apply(_localize)
    events["mw"] = events["mw"].astype("float64")
    cols = [
        "iso",
        "source_dataset",
        "seq",
        "timestamp_utc",
        "timestamp_local",
        "event_type",
        "action",
        "start_of_day",
        "detail",
        "mw",
        "message",
        "source_file",
    ]
    return events[cols]


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write both Ask-B partitions.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    written: list[Path] = []

    req = build_requirements_frame(raw_root)
    path = clean_io.write_clean(
        req,
        REQUIREMENTS_DATATYPE,
        iso="NYISO",
        source=f"{_rel(_raw_dir(raw_root) / _REQ_CSV)} (hand-transcribed from the "
        "dated Locational Reserve Requirements PDFs; see raw README)",
    )
    clean_io.validate_clean(path)
    written.append(path)
    print(f"wrote {path}  ({len(req)} rows)")

    events = build_events_frame(raw_root)
    path = clean_io.write_clean(
        events,
        EVENTS_DATATYPE,
        iso="NYISO",
        source=f"{_rel(_raw_dir(raw_root))}/{{realtime-events,oper-messages}}/*.csv "
        "(NYISO MIS P-35/P-25 via scripts/fetch_nyiso_operating_events.py)",
    )
    clean_io.validate_clean(path)
    written.append(path)
    print(f"wrote {path}  ({len(events)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    del args
    written = curate()
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
