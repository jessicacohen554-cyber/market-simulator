# NYISO capacity-deliverability (LCR% / ICAP req / Bulk Power Transmission Limit)

Drop the retrieved unified CSV here as **`nyiso.csv`**.

- **area_type:** `locality` (statewide IRM row uses `rto`, area = NYCA).
- **delivery_year:** capability-year label, "2024/2025" (May 1 – April 30).
- **areas:** NYC (Load Zone J), Long Island (Load Zone K), G-J (Zones G,H,I,J),
  plus NYCA for the statewide IRM.
- **native → canonical metric:** Locational Minimum ICAP Requirement →
  `requirement` (carry both the MW in `value_mw` and the LCR% as a decimal
  fraction in `value_pu`, e.g. 0.810); Bulk Power Transmission Limit (a.k.a.
  Transmission Security Limit, "Studied" row) → `import_limit`; IRM →
  `system_requirement` (`value_pu`); the report's own **true N-1-1 Transmission
  Security Limit** (TABLE 1 note 2) → `transfer_security_limit` — see below.

### `import_limit` vs `transfer_security_limit` (nyiso-130)

These are two DIFFERENT quantities and only the second is a transfer limit on an
hour. The Locality Bulk Power Transmission Capability Report's headline "Locality
Limit" — the `import_limit` row — is the transfer limit **net of a generation
loss-of-source contingency**. TABLE 1 note 2 of the 2024-25, 2025-26 and 2026-27
editions says so verbatim and identically:

> "The true N-1-1 Transmission Security Limit is 940 in this scenario, the Bulk
> Transfer Limit accounts for the loss-of-source of 660 MW."

so for Long Island (Zone K): `import_limit` 275 = 940 − 660 (Neptune HVDC). The
`import_limit` row is what the LCR **TSL Floor Calculation** consumes — the 2023
LCR Report enters it as `Transmission Security Limit (MW) [B] = Studied 325` and
computes `UCAP Requirement [C] = [A] − [B]` against a **load forecast** — i.e. a
capacity-adequacy accounting term, not an hourly bound. `transfer_security_limit`
carries the interface's actual N-1-1 transfer capability, which is what an hourly
energy transfer bound needs (`ScenarioConfig.nyiso_li_tsl_n11_security`).

The Zone-K interface itself is TSL-report Appendix A: Dunwoodie (Zone I) → Long
Island (Y49 Sprain Brook–East Garden City, Y50 Dunwoodie–Shore Road, both
345 kV) **plus** the two PAR-controlled 138 kV NYC (Zone J) → Long Island ties
(Jamaica–Valley Stream 901L_M, Jamaica–Lake Success 903), whose base case assumes
a net 300 MW flowing K→J. So 940 MW is a **net** Zone-K import limit, and the
UDR-backed external cables (Neptune / Cross Sound / Northport-Norwalk 1385) are
counted separately — matching the model's two-link split exactly.

**2023/2024 provenance, declared:** the 2023-24 edition (`Summer2023_N-1-1_
Analysis_FINAL_DRAFT_20221018.pdf`, TABLE 1) prints only the 325 MW headline and
no true-N-1-1 figure, so its `transfer_security_limit` row carries the **940 MW
published in the 2024-25 edition** and its `source_doc`/`source_page` name that
document rather than the 2023-24 one. Grounds: identical interface, identical
limiting element and rating (Dunwoodie–Shore Road Y50 345 kV @ LTE 964 MVA),
identical 660 MW Neptune loss-of-source, and NYISO's own Table 4 recording the
Zone-K limit **unchanged 2022 → 2023** with the later 325 → 275 move attributed
purely to *"a change in methodology of this study"*. The arithmetically implied
2023-24 value is 325 + 660 ≈ 985 MW, so 940 is the **tighter** of the two and no
per-year value is fitted.

- Locality Bulk Power Transmission Capability / TSL reports carrying the Zone-K
  table (the `transfer_security_limit` source):
  - 2023-24: https://www.nyiso.com/documents/20142/34388803/Summer2023_N-1-1_Analysis_FINAL_DRAFT_20221018.pdf
  - 2024-25: https://www.nyiso.com/documents/20142/40834869/2024-25%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report.pdf
  - 2025-26: https://www.nyiso.com/documents/20142/47642242/2025-26%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report_Final.pdf
  - 2026-27: https://www.nyiso.com/documents/20142/53789919/2026%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report.pdf

## Authoritative sources

- LCR Study reports (LCR% + ICAP req + TSL Floor Calculation table):
  - 2023-24: https://www.nyiso.com/documents/20142/35886565/2023-LCR-Report.pdf
  - 2024-25 (final Apr-2024 revision): https://www.nyiso.com/documents/20142/42519933/2024-2025-LCR-Report.pdf
  - 2025-26: https://www.nyiso.com/documents/20142/49410485/2025-2026-LCR-Report-Clean.pdf
- Locality Bulk Power Transmission Capability Reports (MW transfer-limit detail):
  - 2024-25: https://www.nyiso.com/documents/20142/40834869/2024-25%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report.pdf
  - 2025-26: https://www.nyiso.com/documents/20142/47642242/2025-26%20Locality%20Bulk%20Power%20Transmission%20Capability%20Report_Final.pdf
- IRM (NYSRC NYCA ICR): https://www.nysrc.org/documents/reports/nysrc-new-york-control-area-installed-capacity-requirement-reports

Note: NYC (Zone J) 2024-25 LCR was corrected 81.7% → **80.4%** in Apr 2024; use
80.4%. Required years (backcast): 2023/2024, 2024/2025, 2025/2026.

**STATUS:** `nyiso.csv` committed (PR #1261) — LI (Zone K), NYC (Zone J), G-J
and NYCA rows for 2023/24–2025/26. This is the authoritative source for the
audit C-17 re-grounding of the Long Island self-supply floor; see the rule-14
boundary-mismatch note at `constants.py::NYISO_LOCAL_SELFSUPPLY_FRAC` and open
root-cause issue #1345 (the published LI LCR% is a peak-capacity ratio, so it
cannot re-ground the all-hours energy self-supply fraction as a scalar).
