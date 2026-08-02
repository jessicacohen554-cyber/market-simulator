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
