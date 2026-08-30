# ISO-NE ARA-cycle requirement set — same-cycle extract (capx-S4b)

The published same-cycle restatement of ISO-NE's capacity requirement for the
Capacity Commitment Periods the model's NEISO adequacy anchors are
vintage-anchored to. This is the primary-source record behind the ARA-3
re-vintage of three `config/capacity_market.py` registry entries
(`PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]`,
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]`,
`ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]`), replacing the original FCA-17
auction values (intake audit:
`docs/handoffs/FINDING-capx-s4b-neiso-ara-2026-08-30.md`).

## Sources (authoritative; NOT committed — re-fetchable, identity-pinned)

| document | published | sha256 |
|---|---|---|
| `icr_for_aras.pdf` (FERC filing, "ICR … and Other Related Values for the 2026-2027 and 2027-2028 CCPs for use in Annual Reconfiguration Auctions") | 2025-11-21 | `36c2bdf13d55a3ceda5edb00720df2426d6df90b5df0d7583a68ddeab2af139e` |
| `2026_celt.xlsx` (2026 CELT Report) | 2026-05-01 | `f799af42cce1376cd4aaae71b77f3374a8612ff34e67c5a48de9106664e76980` |
| `2025_celt.xlsx` (2025 CELT Report) | 2025-05-01 | `3c4ed6ac549b1b61e32935a2943b5ccb2b3befe4cc7da05f44eb735908e5d55c` |

- Filing: https://www.iso-ne.com/static-assets/documents/100029/icr_for_aras.pdf
- 2026 CELT: https://www.iso-ne.com/static-assets/documents/100035/2026_celt.xlsx
- 2025 CELT: https://www.iso-ne.com/static-assets/documents/100023/2025_celt.xlsx

**Re-fetch command** (downloads, verifies the pinned sha256s, cross-checks the
filing transcription against the PDF text, re-extracts the CELT cells by their
own header/row labels, and rewrites the extract):

```
python3 scripts/data/fetch_isone_ara_requirements.py            # rebuild
python3 scripts/data/fetch_isone_ara_requirements.py --check    # drift check
```

## What the extract is

`ara_requirement_values.csv` — one row per published value
(`source, published, ccp, vintage, metric, season, value_mw`), transcribed as
published (rules 13/14: no fitting, no rescaling, zero free parameters):

- **From the filing** (pp. 12 & 16, "Proposed Values and Demand Curves"):
  ICR / HQICC / Net ICR / 50-50 summer peak (net of BTM PV) for
  **ARA 3 of CCP 2026-27** (Net ICR 30,050 / peak 26,648 / HQICC 1,009) and
  **ARA 2 of CCP 2027-28** (29,855 / 26,417 / 1,041). The peaks embed the
  Passive Demand Response reconstitution adjustments the filing itself cites
  to CELT §6.3 (testimony pp. 10-11) — the same net-of-BTM-PV basis the
  shipped FCA-17 peak used.
- **From CELT sheet `4.1 Summary of CSOs`** (ISO New England Total block):
  active/passive/total demand-capacity-resource CSOs and the net import CSO,
  per CCP **at the auction vintage the sheet's own column header labels**
  ("Includes ARA 3 Results" etc.). The 2026 CELT's CCP 2026/27 column is the
  ARA-3-inclusive record — the same-cycle companion of the filing's ARA-3
  requirement values; the 2025 CELT rows preserve the prior (ARA-1) rung so
  the vintage ladder FCA-17 → ARA 1 → ARA 3 is on the committed record.

## Why the DR companion is the ARA-3-inclusive CSO (the vintage-pairing rule)

The shipped FCA-17 trio paired the **pre-auction requirement filing** (Net ICR
30,305, Docket ER23-405-000) with the **auction-outcome DR** (2,940 MW cleared,
FCA-17 results) — requirement-for-the-auction with obligations-from-the-auction,
the same-cycle discipline D2-B verified as fork-3 CLOSED. The exact ARA-3
analogue is the Nov 21 2025 filing's requirement FOR ARA 3 paired with the DR
CSO **including ARA 3's outcome** (2,639.682 MW, 2026 CELT). The net import
CSO (409.31 MW, same column) is the same-cycle restatement of the FCA-17
567 MW cleared-import credit and moves with the set for the same reason — the
one discipline S-4's §6.3 refused to break with an unpaired swap.

## Registry derivations (all three from the ARA-3 / CCP 2026-27 rows)

```
PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]          = 30,050 / 26,648 − 1 = 0.12766
ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"] = 2,639.682 / 30,050 = 0.08784
ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]            = 409.31
⇒ DR-netted requirement factor (1−f)(NetICR/peak)  = 1.0286103   (was 1.0024544)
```

Re-derive when ISO-NE publishes a newer same-cycle set — the next ARA ICR
filing, a newer CELT vintage, or the reformed prompt-schedule CCP 2028/29
values (expected late 2026/early 2027, which would supersede this set and
re-anchor the CCP) — never because a residual moved (rule 23).
