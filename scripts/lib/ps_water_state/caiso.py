"""CAISO ps-water-state spec — the Helms (FERC P-2735) FLA hourly record.

CAISO's hourly split of pumped-storage operation from conventional hydro is
non-public at fleet coverage (FINDING-caiso141 §A/§B; caiso-186 §a.1 re-verified
five public walls). Helms — the dominant piece of the uninstrumented 60.3% of
the model's 2,077.6 MW PS fleet — published its own measured hourly operations
record in the PUBLIC Final License Application on FERC eLibrary: Appendix B1
(Hydrology), PG&E HEC-DSS records 2001-01-01 .. 2022-09-30 (see
:func:`scripts.lib.ps_water_state.parse_helms_fla_appb1_hourly`).

``DATA NEEDED``: (a) Helms 2022-10-01 → present — PG&E holds it; no public
filing carries it yet (the relicensing record's data cut-off is 2022-09-30);
(b) Eastwood (SCE, ~200 MW) hourly operations — no public record located;
(c) the DWR facilities (San Luis/Gianelli, Hyatt-Thermalito — 39.7% of the
fleet) have CDEC hourly telemetry in acre-feet/flow grain needing their own
reader and an AF→MWh derivation with cited plant parameters. Each is one more
:class:`PsSource` (plus a reader) here — no shared-code change. See
``data/raw/ps-water-state/README.md``.
"""

from __future__ import annotations

from . import IsoSpec, PsSource, register

#: FERC eLibrary accession carrying the public Helms FLA (April 2024). The
#: xlsx is file "02_Helms FLA_P-2735_PUBLIC_Vol I_App B1 Hydrology.xlsx" of
#: this accession's transmittal list.
HELMS_FLA_ACCESSION = "20240418-5301"

#: eLibrary web-API download endpoint the snapshot was retrieved through
#: (POST {"fileidLst": [<fileId>], "Islegacy": false}); the fileId is recorded
#: in the raw README and the fetch script.
ELIBRARY_DOWNLOAD_URL = (
    "https://elibrary.ferc.gov/eLibrarywebapi/api/File/DownloadP8File"
)

SPEC = register(
    IsoSpec(
        iso="CAISO",
        sources=(
            PsSource(
                plant="HELMS",
                filename="helms_fla_appb1_hydrology.xlsx",
                url=ELIBRARY_DOWNLOAD_URL,
                accession=HELMS_FLA_ACCESSION,
            ),
        ),
    )
)
