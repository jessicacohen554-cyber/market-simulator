# ISO-NE capacity-market-demand-curve (FCA / MRI parameters)

Drop the retrieved unified CSV here as **`neiso.csv`** (the raw subdir is
`neiso/`, matching `iso=NEISO` — the model's ISO label per
`config/iso_configs.py` — not ISO-NE's own "ISO-NE" branding).

- **metric:** `net_cone`, `irm` (native alias `icr` — Installed Capacity
  Requirement, note in `source_page` whether ISO-NE published it in MW or as a
  reserve-margin ratio), `price_cap` (native alias `auction_starting_price`),
  `curve_point`.
- **delivery_year:** the Capability Year the FCA covers.
- **y_unit:** ISO-NE publishes FCA prices in $/kW-month.

## Authoritative sources

- ISO-NE Forward Capacity Market hub: https://www.iso-ne.com/markets-operations/markets/forward-capacity-market
- FCA results / Key Parameters filings: https://www.iso-ne.com/markets-operations/markets/forward-capacity-market/fcm-participation

**STATUS:** `neiso.csv` committed — Net CONE + price cap (Auction Starting
Price = max(CONE, 1.6×Net CONE), verified arithmetically against every FCA
11-18 row) for Capability Years 2020/2021-2027/2028 (FCA 11 through FCA 18),
plus the full 5-point piecewise demand curve for FCA 11 (the only auction
where ISO-NE published discrete MW/$ breakpoints; later FCAs publish only the
anchor parameters, not the curve shape). Note: ISO-NE's demand curve has been
MRI-based since FCA 11 (2017), not a recent change — the "MRI arriving with
FCA19" framing in some secondary commentary conflates the long-standing
MRI-based demand curve with a separate, still-pending proposal to use an
MRI-like methodology for individual-resource capacity accreditation. FCA19 has
been repeatedly delayed (now targeted Feb 2028); FCA18 (Feb 2024, CCP
2027/2028) is the most recent completed auction. See
`docs/handoffs/capacity-market-intake-2026-07.md`.

**STATUS (2026-08-02, FFR-2C — checked, NO newer vintage exists).** The on-disk
last vintage, **2027-2028 (FCA 18)**, remains current: it is the last forward
capacity auction ISO-NE has ever held. FCA 19 is delayed to February 2028 and the
Forward Capacity Market is being replaced by the prompt/seasonal design — CAR-PD
was accepted by FERC on 2026-03-30 (Docket ER26-925) and CAR-SA, which carries
the successor market's parameters, is expected Q4 2026 and unpublished. The
FCA-19 paper Net CONE (9.614 $/kW-month = 115.37 $/kW-yr, from the Nov-2023
MOPR-elimination filing, sha256 `7a69dd08f8cfa7345faee79a8847db96fff8a6b2f8572ec3d705bcffc4ecd16e`)
exists but clears no auction against it.

So this is **not** a retrieval gap and there is nothing to intake. How to
represent ISO-NE past 2027/2028 — hold FCA 18 flat, or encode FCA 19 as an
explicitly-labelled superseded vintage — is **owner decision FF-G3 D4**
(`docs/handoffs/ff-g3-net-cone-forward-2026-07.md` §5).

## NEISO-RC-R R2 intake (2026-08-31) — clearing evidence + Net ICR + the FCA 13 published tail

The `reliability_requirement` (Net ICR, MW) and clearing-outcome `curve_point`
rows added 2026-08-31 re-derive the model's NEISO vintage curves from published
auction evidence (charter: `docs/handoffs/capx-director-prompt-pack-2026-08.md`
§NEISO-RC-R, executing `FINDING-capx-neiso-rc-phase0-2026-08-30.md` §6 R2).
Derivation admissibility (rules 13/14/23): **the FCA clears ON the system-wide
demand curve**, so each auction's published (cleared MW, clearing price) is a
measured point on that year's published curve — verified exactly on the two
FCAs whose curve segments are themselves published: FCA 11 ($5.297 at
35,835 MW lands on the slide-14 piecewise table's last segment) and FCA 13
($3.800 at 34,839 MW lands on the ICR-filing tail segment to the third
decimal: 7.03×(35,713−34,839)/(35,713−34,097) = 3.802). No parameter comes
from any model residual. The Dynamic De-List Bid Threshold was examined as a
candidate anchor and NOT used: it is a de-list *review* threshold (a
supply-side administrative bar — $4.300/kW-month at FCA 15, per the ISO's
public information filing for FCA 15), not a point on the demand curve;
clearing prices below it (every FCA 14–17 clear) confirm the auctions cleared
on the curve with dynamic de-listing active.

Source identity record (sha256 of each retrieved document, accessed 2026-08-31):

| document | sha256 |
|---|---|
| `summary_of_historical_icr_values.xlsx` (Net ICR / Net CONE per FCA; "As of December 2025" edition) | `2b54e8b5b4fd8618f95321c8d96adfc5db5e889b2acb06a1c28e85a03978dec1` |
| `fca-results-report.pdf` (concatenated official FCA 8–18 result reports; clearing prices) | `96efddaa2e941857693007610554d9f96558dc59cbe545372188aed30bde769d` |
| `icr_filing_fca_13.pdf` (ER19-291-000; FCA 13 transition-tail segment, testimony p.48) | `1c6f1728ec6bd53ea95b69c77908b6e2eea15d66abfce95a845ae756dfc3897b` |
| `a03_fca18_icr_related_value_calculation_assumptions.pdf` (FCA 18 Net CONE / starting price) | `e041d7dc399fa14c58a1ee213283796f8f4b7f26c9e1524c2083342e4ea4c457` |
| `20200205_pr_fca14_initial_results.pdf` (33,956 MW; surplus 1,466 ⇒ Net ICR 32,490 ✓) | `7ff5b46ac88d9722f36ba76586c8523932615f0a65dc2d0f733c14ce5cc4e395` |
| `20210226_pr_fca15_final_results.pdf` (34,621 MW; also tabulates FCA 11/12/13: 35,835/$5.30, 34,828/$4.63, 34,839/$3.80) | `895350ee178de8f8a7182609c6c3869f8c44017e29c7d623d3c09653c9ffc81e` |
| `20220309_pr_fca16_initial_results.pdf` (32,810 MW; Net ICR 31,645 ✓) | `b28ebc2e1617bea3a21f6ece6727dfdc1e0a12241eaecb3fa2141ccd6acac7d4` |
| `20230310_pr_fca17_initial_results_final.pdf` (31,370 MW) | `fb7e917640ec9312c1e8c377a010898531179bc8f94c3b274b752f13670f7fc0` |
| `20240209_pr_fca18_initial_results.pdf` (31,556 MW; Net ICR 30,550 ✓) | `9c355d8059fb1bb0a0f0458f273c3c6f81bc1476d298e3f7488a940483262041` |

Recovery is re-fetch from the URLs in the CSV rows (payloads not committed —
bloat discipline; the sha256 table above is the identity record).

**What the derived normalized MRI-era clearing points show** (x = cleared MW ÷
Net ICR, y = clearing price ÷ Net CONE): FCA 18 (1.0329, 0.3944) · FCA 17
(1.0351, 0.3520) · FCA 16 (1.0368, 0.3469) · FCA 15 (1.0406, 0.2999) · FCA 14
(1.0451, 0.2444) — five auctions across five years, monotone in normalized
space, tracing one common curve tail; the published FCA 13 tail zero-crosses at
35,713/33,750 = 1.0582. This REFUTES the Phase-0 finding's premise that the
FCA-11-geometry zero-cross at 1.083 underpays at surplus: the measured MRI-era
curve sits BELOW the linear FCA-11 geometry throughout (1.0, 1.06] and reaches
zero EARLIER (~1.058–1.065), not later. Real FCAs cleared $2.00–3.58/kW-month
at 3.3–4.5% surplus — never at the ≥8% surplus positions where the model's
screens evaluate the curve.
