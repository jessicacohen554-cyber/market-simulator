# NRC Expected Power Uprate Applications — snapshot

- **Source:** <https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/expected-applications.html>
- **Accessed:** 2026-07-20 (WebFetch → markdown; living page — pinned audit snapshot)
- **What it is:** ANNOUNCED-but-not-yet-submitted power uprates. The primary source for the registry's `announced_uprate_mw` / `uprate_status=announced_intent` rows. Per-unit MWt is **not published** on this page (summary total only: 32 expected uprates ≈ 7,336 MWt across all years), so the registry records `uprate_status=announced_intent` with `announced_uprate_mw` blank and cites this list.
- **Companion:** the *pending* (under-review) uprate list was empty at access ("There are no power uprate applications currently under review", page last updated 2021-11-19), and the *approved* uprate list is HISTORICAL (already reflected in EIA-860 nameplate) — see `nrc-approved-power-uprates-2026-07-20.md`.

## Expected applications — modeled ISOs only (attributable units)

| CY | Applicant | Plant | Uprate Type | Planned Submission | Modeled ISO |
|---|---|---|---|---|---|
| 2027 | PSEG | Salem 1 | Stretch | Q2 2027 | **PJM** |
| 2027 | PSEG | Salem 2 | Stretch | Q2 2027 | **PJM** |
| 2029 | Vistra Operating | Perry 1 | Extended | Q3 2029 | **PJM** |
| 2030 | Vistra Operating | Beaver Valley 2 | Extended | Q3 2030 | **PJM** |
| 2031 | Vistra Operating | Beaver Valley 1 | Extended | Q3 2031 | **PJM** |
| 2032 | Vistra Operating | Davis-Besse | Extended | Q3 2032 | **PJM** |

## Constellation "Proprietary" entries — NOT attributable

The list carries multiple 2026–2030 "Constellation Energy — Proprietary — Extended/MUR"
rows whose plant is withheld. They cannot be mapped to a specific unit and are
therefore **not** recorded against any registry row (rule 5 — no unattributed
assignment). Constellation's fleet in the modeled ISOs (Byron, Braidwood, LaSalle,
Limerick, Dresden, Quad Cities, Calvert Cliffs, Peach Bottom, Nine Mile Point,
FitzPatrick, Clinton, Ginna, Crane) are the candidates; a future intake with a
de-anonymized filing should attribute them.

## Out-of-modeled-ISO expected uprates (context, excluded)

Brunswick 1-2, McGuire 1-2, Hatch 1-2, Catawba 1, Vogtle 1-2 (Southern/Duke SERC);
Columbia, Wolf Creek (SPP/NW) — not in the six modeled ISOs.
