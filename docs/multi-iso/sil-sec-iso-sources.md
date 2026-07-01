# Simultaneous Import/Export Limits (SIL/SEC) — Per-ISO Data Sources

Aggregate simultaneous transfer constraints cap the total flow across ALL
external border links of an ISO's import/export zone.  The constraint binds
only when several paths would load simultaneously past the network's real
simultaneous capability — which is materially less than the sum of individual
path ratings because the paths share upstream/downstream network capacity.

## Implementation

| ISO   | Limit Name                  | Cap (MW) | Bidir | Where Defined                              |
|-------|-----------------------------|----------|-------|--------------------------------------------|
| CAISO | `WECC_import_simultaneous`  | 7,500    | Yes   | `iso_configs.py` → `_caiso_config()`       |
| PJM   | `PJM_simultaneous_import`   | 10,500   | Yes   | `interchange_config.py` → `EXTERNAL_SIMULTANEOUS_LIMITS` |
| MISO  | `MISO_simultaneous_import`  | 8,700    | Yes   | `interchange_config.py` → `EXTERNAL_SIMULTANEOUS_LIMITS` |
| NYISO | `NYISO_simultaneous_import` | 4,350    | Yes   | `interchange_config.py` → `EXTERNAL_SIMULTANEOUS_LIMITS` |
| NEISO | `HQ_import_simultaneous`    | 3,850    | Yes   | `iso_configs.py` → `_neiso_config()`       |
| ERCOT | N/A                         | —        | —     | DC ties (~1.2 GW) embedded in demand       |

CAISO and NEISO have their external zones baked into the ISO config, so their
InterfaceLimit lives directly in the config builder.  PJM, MISO, and NYISO
have external zones appended dynamically by `extend_with_import_node()`, so
their SIL/SEC is stored in `EXTERNAL_SIMULTANEOUS_LIMITS` and the
InterfaceLimit is built dynamically with link references matching the
actually-appended border links.

## Data Sources by ISO

### PJM — 10,500 MW

PJM publishes **CETL** (Capacity Emergency Transfer Limit) per LDA via the
RTEP process and conducts **simultaneous-feasibility studies** for the RPM
Base Residual Auction.  PJM's functional equivalent of an aggregate SIL is
the **Capacity Import Limit (CIL)**, set per the LOLE study.

The system-wide aggregate simultaneous import capability is ~10,500 MW — well
below the sum of individual seam limits (MISO 7.3 + NYISO 3.9 + Carolinas
2.4 + TVA 1.6 + LGEE 1.1 = 16.3 GW) and far below the border-link TTC sum
(30.2 GW), because the western interfaces (AP-South, Bedington-BlackOak)
share downstream 500 kV capacity.

**Primary sources:**
- PJM RTEP Annual Report — CETL tables
- PJM Manual 14B §3.3 — simultaneous feasibility methodology
- RPM Base Residual Auction planning parameters (published annually)
- PJM Manual 18 — Capacity Market, external capacity resources
- PJM Manual 20A — Resource Adequacy Analysis (CETO/CETL methodology)

### MISO — 8,700 MW

MISO publishes **CIL/CEL** (Capacity Import Limit / Capacity Export Limit)
with the annual **Planning Resource Auction (PRA)** via the LOLE study.

The system-wide CIL is ~8,700 MW — below the sum of individual seam limits
(PJM 7.3 + SPP 4.0 + South 3.0 = 14.3 GW), because the contract-path RDT
bottleneck between MISO Midwest and MISO South limits how much of each seam
can flow simultaneously.

**Primary sources:**
- MISO PRA clearing results (published annually)
- MISO LOLE Study Report
- MISO Transmission Expansion Plan (MTEP)

### NYISO — 4,350 MW

NYISO publishes external interface transfer limits via the **Gold Book**
(Load & Capacity Data Report) and the **IRM/LCR** (Installed Reserve Margin /
Locational Capacity Requirement) study.  NYISO also files a seasonal **SIL**
with FERC per Order 697.

The total simultaneous import capability is ~4,350 MW — below the sum of
border-link TTCs (Upstate_West 3.0 + NYC 1.0 + Long_Island 1.2 = 5.2 GW),
because the downstate import interfaces (Dunwoodie-South 3.9 GW into NYC,
cable-limited 1.65 GW into LI) share upstream transmission.

**Primary sources:**
- NYISO Gold Book (annual, Load & Capacity Data Report)
- NYISO IRM/LCR studies (NYSRC, annual)
- NYISO Reliability Needs Assessment / Comprehensive Reliability Plan
- NYISO FERC Order 697 SIL filing (seasonal)
- NYISO TTCF (seasonal transfer limit documents, mis.nyiso.com)

### NEISO — 3,850 MW

The three HQ_import border links (HQ_import→Boston 2,000 + HQ_import→North
900 + HQ_import→Connecticut 1,500 = 4,400 MW sum of individual TTCs) share
upstream Hydro-Quebec export capacity and New England import interface
capability.  The aggregate simultaneous import is ~3,850 MW.

**Primary sources:**
- ISO-NE Capacity, Energy, Loads, and Transmission (CELT) Report
- ISO-NE Installed Capacity Requirement (ICR) / Regional System Plan (RSP)
  tie-benefit analysis
- ISO-NE Forward Capacity Market qualification rules

### CAISO — 7,500 MW

Already implemented.  The WECC_import simultaneous cap of 7,500 MW sits
between the CAISO RA summer peak import assumption (5,500 MW) and the
EIA-930 CISO measured p01 extreme (~8,300 MW).  The sustained p05 import is
~7,500 MW.

**Primary sources:**
- CAISO Maximum Import Capability (MIC) document (annual, ~11,665 MW total)
- CAISO Simultaneous Import Limit (SIL) study (filed with FERC, AD10-2)
- CAISO RA summer import assumption (5,500 MW peak hours)
- EIA-930 CISO net-interchange 2023–2025

### ERCOT — N/A

ERCOT has no external import zone in the model.  Its DC ties (~1.2 GW total:
East 820 MW + Laredo 100 MW + Eagle Pass 36 MW + Railroad 300 MW) are small
relative to the system and are embedded in the demand signal.

**Reference:** ERCOT Capacity, Demand, and Reserves (CDR) Report.
