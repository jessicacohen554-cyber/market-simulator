# NRC Approved Power Uprate Applications — snapshot (HISTORICAL context)

- **Source:** <https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/approved-applications.html>
- **Accessed:** 2026-07-20 (WebFetch → markdown; living page — pinned audit snapshot)
- **Why it is context, not registry data:** every uprate on this list is ALREADY
  APPROVED and reflected in the plant's current EIA-860 nameplate MW. The registry's
  `capacity_mw` is the post-uprate EIA nameplate, so these historical uprates must
  NOT be re-added as `announced_uprate_mw` (that column is for FORWARD, not-yet-in-
  nameplate uprates — see `nrc-expected-power-uprates-2026-07-20.md`). This snapshot
  documents that the modeled fleet is largely already uprated (most units carry an
  Extended and/or MUR uprate), so the forward uprate headroom is modest.
- Page summary at access: **172 approved applications**, total ≈ 24,089 MWt / 8,030 MWe.

## Latest approved uprate per modeled-ISO nuclear unit (illustrative subset)

Extended power uprates (EPU) are the material ones; MUR (~1.4–1.7%) are small
measurement-recapture gains. Representative EPU rows for modeled units:

| Plant | Unit | Uprate Type | Approved | MWt increase | Modeled ISO |
|---|---|---|---|---|---|
| Clinton | 1 | Extended | 2002-04-05 | 579 | MISO |
| Monticello | 1 | Extended | 2013-12-09 | 229 | MISO |
| Point Beach | 1,2 | Extended | 2011-05-03 | 260 ea | MISO |
| Arkansas Nuclear One | 2 | Extended | 2002-04-24 | 211 | MISO |
| Dresden | 2,3 | Extended | 2001-12-21 | 430 ea | PJM |
| Quad Cities | 1,2 | Extended | 2001-12-21 | 446 ea | PJM |
| Grand Gulf | 1 | Extended | 2012-07-18 | 510 | MISO |
| Peach Bottom | 2,3 | Extended | 2014-08-25 | 437 ea | PJM |
| Susquehanna | 1,2 | Extended | 2008-01-30 | 463 ea | PJM |
| Hope Creek | 1 | Extended | 2008-05-14 | 501 | PJM |
| Nine Mile Point | 2 | Extended | 2011-12-22 | 521 | NYISO |
| Ginna | 1 | Extended | 2006-07-11 | 255 | NYISO |
| Beaver Valley | 1,2 | Extended | 2006-07-19 | 211 ea | PJM |
| Waterford | 3 | Extended | 2005-04-15 | 275 | MISO |

(The full 172-row list on the source page includes MUR uprates for essentially the
entire fleet and out-of-scope plants; only EPUs for modeled units are transcribed
here as the salient context. Re-query the source for the complete table.)
