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
  `system_requirement` (`value_pu`).

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
