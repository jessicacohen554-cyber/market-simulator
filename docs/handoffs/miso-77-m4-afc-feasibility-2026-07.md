# miso-77 — M4 feasibility investigation: public per-flowgate MW-limit series for MISO

**Status: INVESTIGATION COMPLETE — VERDICT: GO (qualified). No LP, no build, no solve.**
Owner-selected lane (2026-07-19 session): charter
`docs/handoffs/miso-nc-price-separation-design-2026-07.md` §3 **M4** — "If a
measured per-flowgate MW-limit series proves publicly fetchable, the
congestion component becomes representable and gets its OWN charter."
This document is that investigation's record: fetchability, coverage
(2023–2025 train window), and flowgate→zone-boundary mapping feasibility.
Per the M4 clause, the *design* is deliberately out of scope here — a GO
verdict buys a charter, not a mechanism.

## 1. Verdict

- **GO (qualified):** a measured per-flowgate MW-limit series **is publicly
  fetchable** for the CMP/M2M coordinated-flowgate universe, with full
  2023–2025 coverage, **on the same no-auth channel the repo already uses**
  (`docs.misoenergy.org/marketreports/`, the miso-76 lmp-components and RDT
  intake channel) — not via OASIS AFC queries.
- The **literal OASIS-AFC route is NOT publicly fetchable as a series**:
  OATI webSmartOASIS query APIs return 403 without a registered session, and
  no public historical AFC archive was found. What OASIS does expose
  publicly is *static* per-flowgate seasonal ratings + TRM/CBM and the
  coordinated-flowgate registry (PDF snapshots, §2c).
- Qualifications that bound the future charter (§5): the East boundary class
  is only ~25 % covered (the congestion there remains substantially
  data-blocked — the miso-76 R2 cancellation corridor), no shift-factor /
  PTDF data is published anywhere in the family (the central representation
  risk in a 6-zone network), and the hourly *operationally binding* (derated)
  limit is not published — the fetchable limit classes are seasonal/daily
  ratings and hourly FFE entitlements.

## 2. Source inventory (what exists, with fetch evidence 2026-07-19)

### 2a. Fetchable series — `docs.misoenergy.org/marketreports/` (no auth, proven channel)

| report | granularity | content | verified coverage |
|---|---|---|---|
| `M2M_FFE_YYYY_MM_DD.CSV` | daily file, **hourly rows** | per-flowgate (NERC ID, monitoring/non-monitoring RTO, description) **Firm Flow Entitlement MW** + Adjusted FFE | 2023-01-01, 2023-01-03, 2023-02-15, 2023-06-01, 2024-10-29, 2025-01-15→2025-06-01 monthly probes, 2025-12-31 all HTTP 200 (~1.2–2.0 MB each; one 404 at 2025-06-15 = single missing day). 764 flowgates in the 2024-10-29 file; 1,084-flowgate universe by 2025 |
| `Allocation_on_MISO_Flowgates_YYYY_MM_DD.csv` | daily snapshot | per-flowgate per-entity **Allocation (MW)** by direction + **"Allocation to Rating Percentage"** → the pair **implies the total flowgate rating in MW** (e.g. FG 556: 168.7 MW @ 56 % fwd and 132.7 MW @ 44 % rev both imply ≈ 301 MW total) | 2023-06-01, 2024-10-29, 2025-06-01 all 200 (339–518 KB); 493 flowgates on 2024-10-29, incl. reciprocal-N rows |
| `M2M_Settlement_srw_YYYY.csv` | annual file, **hourly rows** | per-flowgate hourly **shadow prices (both RTOs), market flows MW, FFEs both sides, credits** — MISO–PJM *and* MISO–SPP (SWPP) | 2023 (13.5 MB), 2024 (17.7 MB), 2025 (19.6 MB) all 200; 385 distinct flowgates in 2024 (MISO-monitored 185: 115 vs SWPP + 70 vs PJM) |
| `M2M_Flowgates_as_of_YYYYMMDD.CSV` | daily snapshot | flowgate registry: NERC ID → monitoring/non-monitoring RTO + description | 2023-06-01, 2024-10-30, 2025-06-01 all 200 |

**Rating cross-check:** Allocation-implied total ratings agree with the OASIS
static ratings PDF (§2c): FG 556 `StLine_Roxanna138_flo_WiltonCenter_Dumont765`
implied ≈ 301 MW vs published 299 (winter) / 288 (summer); FG 575
`QUAMECCORWEM` implied ≈ 1,412 vs 1,406 / 1,180. Two independent publications
of the same physical quantity — the rating series is measured, not inferred.

### 2b. Fetchable statics — OASIS `MISOdocs` (OATI-hosted; see fetch notes §6)

- `AFC_FG_RATINGS_TRM_CBM.pdf` — per-flowgate **winter/summer ratings MW +
  TRM + CBM + PIRULE/CIRULE** (FG ID, OASIS pathcode, owner). Current
  snapshot only; no historical archive found.
- `MISO-COORDINATED_FLOWGATES.pdf` — NERC ID → full flowgate description
  (monitored element + contingency branch names), owner, coordinated
  entities.
- ATC information index: `.../woa/docs/MISO/MISOdocs/ATC_Information.html`
  (links the above + ATCID/CBMID/TRMID methodology documents).

### 2c. NOT publicly fetchable (adjudicated this session)

- **OASIS AFC hourly postings/history:** webSmartOASIS query endpoints
  (`/webSmartOASIS/HomePage/GetTab`, SystemData displays) return **HTTP 403**
  without a registered OASIS session; the classic NAESB S&CP CGI templates
  are dead (404 / "contact Support"). No public historical AFC file archive
  exists under `MISOdocs`.
- **MISO Data Exchange:** key-gated (matches the RDT adjudication 2026-07-11,
  re-verified 2026-07-12 — `data/raw/transfer-constraint-binding/MISO/README.md`).
- **bc_HIST / pbc:** carry **no MW limit and no flow** (charter §2b stands).
  The RDT modeled (operator-derated) limit series likewise remains
  unpublished — and the same is true here: **no source publishes the hourly
  operationally-binding derated limit**; the fetchable limit classes are
  seasonal/daily ratings (2a/2b) and hourly FFE entitlements.

## 3. Coverage: how much of the measured congestion sits on fetchable-limit flowgates

Method: aggregate each year's DA `bc_HIST` by constraint (Σ|shadow price|,
answer-class data used ONLY to locate/rank congestion — rule 13), then
token-match constraint name + contingency description against the
year-matched M2M/FFE/Allocation flowgate-description universe (normalized
station-name tokens, 6-char prefixes, ≥2 shared tokens; ≥3 = conservative
bound). Zone-boundary classes via the `_miso76_bc_boundary_rank.py` LBA
crosswalk. Spot-checks of the top matches are genuine (e.g. `AURORA-REEDS
FLO EUREKA SPRGS-BVR DAM` → `TMP246_LN_Aurora_Reed_Springs_161_kV_LO_LN_
Beaver_Eureka_S`; `FORMAN TR12 FLO WAHPETON-HANKINSON` →
`Forman_230_115_TR1_flo_Hankinson_Wahpeton_230kV`; `OAHE-SULLYBT` 5-token).

| DA year | Σ\|SP\| matched ≥2 tok | ≥3 tok (conservative) |
|---|---|---|
| 2023 | **68.9 %** | 52.2 % |
| 2024 | **73.9 %** | 51.3 % |
| 2025 | **72.3 %** | 39.5 % |

Boundary-class coverage (≥2-token, share of that class's Σ|SP| matched):

| class | share of Σ\|SP\| (23/24/25) | covered % (23/24/25) |
|---|---|---|
| EXT (seam) | 26/32/21 | **90/90/88** |
| West-internal | 26/20/23 | **74/78/74** |
| Plains-internal | 15/10/10 | 43/49/51 |
| Indiana-internal | 7/9/11 | 77/64/75 |
| East-internal | 8/5/6 | **27/23/27** |
| Illinois-internal | 5/4/– | 83/85/– |
| EXT\|West, EXT\|Plains | – | 95–100 |

Of the ≥3-token matched mass (2024): hourly FFE series exists for **85 %**,
hourly settlement flows/shadow-prices for **90 %**, allocation-implied
rating for **44.5 %**.

**Reading:** the fetchable universe covers the seams near-fully and the
wind-belt (West) at ~three-quarters — exactly where the miso-76 charter
located the loss-inexplicable separation (congestion carries 62–105 % of the
measured Midwest separation). The **East-internal class stays ~75 %
uncovered**: the East-2025 cancellation that tripped R2 remains mostly
data-blocked even under M4, and any future charter must disclose that — the
congestion representable from this data is the seam + wind-belt component,
not the Michigan-internal component.

## 4. Rule-13 admissibility by series

- **Flowgate ratings** (Allocation-implied daily; OASIS seasonal statics):
  physical equipment property; regenerates for a forward year; responds to
  changed conditions (seasonal). **Admissible input class.**
- **FFE (hourly)**: a CMP market-design entitlement (firm-reservation
  derived), with a forward analogue in principle — but the future charter
  must state its forward regeneration story explicitly before FFE is used as
  anything but context (rule 12's window/driver/forward-story test applies
  to whatever mechanism consumes it).
- **Market flows + shadow prices + credits (settlement, bc_HIST)**: the
  ANSWER class. Validation/location only, never an input (rule 13) — same
  standing as the miso-76 bc_HIST layer.

## 5. What the M4 charter (next session, charter-first) must resolve

1. **Crosswalk curation.** There is **no shared key** between `bc_HIST`
   (`Constraint_ID`, free-text names) and the M2M family (NERC flowgate ID).
   The token-match here is a feasibility heuristic; an intake needs a
   curated name-based crosswalk (NERC ID ↔ constraint name ↔ From/To CA →
   model zones). Feasible — descriptions carry station names and the
   Allocation/registry files carry owners — but it is manual curation work
   and must be frozen against residuals (rule 23).
2. **Representation without shift factors.** No PTDF/shift-factor data is
   published anywhere in this family. A branch-level flowgate cannot be
   placed on a 6-zone reduced network without an apportionment choice — the
   exact concern that refuted M1 (charter §3). The charter must find a
   representation that does not invent one (candidates to be adjudicated
   THERE, not here; the M1 refutation stays binding for naive per-corridor
   caps).
3. **Which series is the cap.** Rating (total MW, admissible, but a
   *simultaneous-total* not a per-direction market limit) vs FFE
   (entitlement share, hourly, needs a forward story). Also state the
   derated-limit gap (§2c) explicitly.
4. **East disclosure.** ~75 % of East-internal congestion mass is outside
   the fetchable universe — the charter must scope its claim to the covered
   classes and keep the East gap in the documented-limitation ledger.
5. **Intake mechanics.** New datatype via the data-intake skill
   (schema-first, train-window quarantine guard like `fetch_miso_bc_hist.py`);
   bulk mirrors gitignored with sha256 README rows (precedent: bc_HIST);
   OASIS statics mirrored as source snapshots.

## 6. Fetch-environment notes (reproducibility)

- `docs.misoenergy.org` — plain `curl --cacert /root/.ccr/ca-bundle.crt`,
  no auth, no UA games. The entire §2a family lives here.
- OATI (`www.oasis.oati.com`) — TLS chains to OATI's **private webCARES CA**
  (`OATI WebCARES Root CA` → `webCARES Server Issuing CA 2025`), absent from
  public trust stores, and the cert-repository hosts serve the same private
  chain (bootstrap circle). Working probe: capture the issuing CA from the
  TLS handshake (`openssl s_client -showcerts -proxy …`), then Python
  `ssl.VERIFY_X509_PARTIAL_CHAIN` pinned to it, plus a browser User-Agent
  (the OATI server 503/403s non-browser clients). A production intake of the
  §2b statics should install OATI's published webCARES root properly instead
  of the handshake pin.
- Evidence files (session scratchpad, not committed): sampled CSVs and PDFs
  listed in §2, plus `2023/2024/2025_da_bc_HIST.csv` re-fetched via the
  sanctioned `fetch_miso_bc_hist.py` URL (gitignored-mirror class).

## 7. Out-of-scope (unchanged)

The C3a-2025/C3c irreducible tail; the declined determination path;
direction-symmetric losses (lane b, separate charter if ever selected); D1
Z2/Z7 split; all-ISO `gas_daily_shape` interp fix; PJM merit-cap twin.
