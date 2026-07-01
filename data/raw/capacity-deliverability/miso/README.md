# MISO capacity-deliverability (LRR / LCR / CIL / CEL / ZIA by LRZ × season)

The unified CSV lives here as **`miso.csv`** (740 rows, PY2023/2024 through
PY2025/2026). MISO is **seasonal** (summer / fall / winter / spring) since
Planning Year 2023-24, so every row carries a real `season`.

- **area_type:** `lrz` (system/subregional PRMR rows use `rto`, area = RTO /
  North / South).
- **delivery_year:** planning-year label, "2024/2025" (June 1 – May 31).
- **areas:** LRZ 1–10. (1 MN/ND, 2 WI/MI-UP, 3 IA, 4 IL, 5 MO, 6 IN, 7 MI-LP,
  8 AR, 9 LA/E-TX, 10 MS; South = 8/9/10.)
- **native → canonical metric:** LRR → `requirement` (also a per-unit ratio →
  `value_pu`); LCR → `local_clearing_requirement`; CIL → `import_limit`;
  CEL → `export_limit`; ZIA → `import_ability`; PRMR → `system_requirement`.
- "No Limit Found" CEL cells → leave `value_mw` blank (never 0).

## Authoritative sources

LOLE Study Reports give the initial per-season CIL/CEL/LRR/ZIA; PRA Results
postings give as-cleared LCR/CIL/ZIA/CEL/PRMR by zone. Download the raw PDF and
text-extract (pdfminer.six / pdftotext) — the decks are image-heavy.

- LOLE PY2023-24: https://cdn.misoenergy.org/PY%202023-2024%20LOLE%20Study%20Report626798.pdf
- LOLE PY2024-25: https://cdn.misoenergy.org/LOLE%20Study%20Report%20PY%202024-2025631112.pdf
- LOLE PY2025-26: https://cdn.misoenergy.org/PY%202025-2026%20LOLE%20Study%20Report685316.pdf
- 2023 PRA Results: https://cdn.misoenergy.org/2023%20Planning%20Resource%20Auction%20(PRA)%20Results628925.pdf
- 2024 PRA Results: https://cdn.misoenergy.org/2024%20PRA%20Results%20Posting%2020240425632665.pdf
- 2025 PRA Results: https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%2020250529_Corrections694160.pdf

Required years (backcast): 2023/2024, 2024/2025, 2025/2026.
