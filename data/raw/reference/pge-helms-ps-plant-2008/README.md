# PG&E "Helms Pumped Storage Plant" presentation (NW Wind Integration Forum, 2008-10-17)

The plant owner's own public technical presentation on the Helms Pumped
Storage Plant (FERC P-2735) — the citation source for Helms' pump-mode
rating and reservoir volumes in `constants.CAISO_PS_PLANT_PARAMS` (lane 5,
caiso-197, GATESPEC-caiso195-ps-physical-2026-08-11).

## Provenance

- **Author/publisher:** Manho Yeung, Pacific Gas and Electric Company;
  presented at the Northwest Wind Integration Forum Workshop, October 17,
  2008; hosted publicly by the Northwest Power and Conservation Council.
- **URL:** https://www.nwcouncil.org/sites/default/files/ManhoYeung_1.pdf
- **Retrieved:** 2026-08-16, HTTP 200 through the environment's configured
  proxy, 254,161 bytes (application/pdf, 12 pages).
- **sha256:** `39b009adda3dea63dc746205252bddeb34dc00d9867843db2351e5e1b66dce84`
- **License/access:** public conference material on a public agency site,
  no login/paywall.

## Load-bearing quotes (pages 4-5)

- "Three units; **1,212 MW generating; 930 MW pumping**" (p.4, Installed
  Capacity row; restated p.5: "1,212 MW total in generation mode, and
  930 MW total in pump mode").
- Upper reservoir: "Courtright Lake **123,000 Acre Feet**"; lower
  reservoir: "Lake Wishon **129,000 Acre Feet**" (p.4).
- Generating-mode flow: "travel at **9,000 cubic feet per second** ...
  drop **1,744 vertical feet**" (p.5).
- Average natural in-flow energy: "<100 GWh per year" (p.4) — NOT
  represented in the storage block (no inflow term); unchanged from the
  incumbent aggregate representation.

## Use

`CAISO_PS_PLANT_PARAMS[6100]`: `pump_mw = 930.0` (direct quote);
`energy_mwh = 200,424` = 123,000 AF × 1,212 MW / (9,000 cfs = 743.80 AF/h)
— gross upper-reservoir volume, the GATESPEC §4.1 more-capability
direction. Reproduction arithmetic:
`results/calibration/_caiso197_ps_citations.json`.
