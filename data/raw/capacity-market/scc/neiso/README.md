# ISO-NE Seasonal Claimed Capability — conventional-hydro extract (capx-S4)

Per-resource summer/winter Seasonal Claimed Capability (SCC) of ISO-NE's
ACTIVE conventional-hydro fleet, transcribed from ISO-NE's own monthly SCC
report. This is the primary-source record behind
`config/capacity_market.py::HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"]`
(the capx-S4 intake closing the FFR-1C open item — ISO-NE publishes **no
hydro class rating**, so the class factor is the aggregate of its own
per-resource record; derivation and population audit:
`docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md`).

## Source (authoritative)

- **Report:** ISO-NE ISO Express → Operations Reports → **Seasonal Claimed
  Capability** — "A Monthly Listing of ISO-New England Participant Generator
  Assets and Demand Response Resources and their seasonal capabilities."
- **Landing page:**
  https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seasonal-claimed-capability
- **Re-fetch command** (the tree is JS-driven; the script drives its
  `docWidgetGetMore` listing endpoint and bootstraps the `isox_token`
  session cookie, the same pattern as `fetch_neiso_morning_report.py`):

  ```
  PYTHONPATH=src:. python3 scripts/data/fetch_isone_scc_hydro.py --month august --year 2026
  ```

- **Source workbook identity** (the workbook itself is NOT committed — it is
  re-fetchable and 1.2 MB; the committed deliverable is the hydro extract):

  | workbook | published | sha256 |
  |---|---|---|
  | `scc_august_2026.xlsx` | 2026-08-06 | `7fbc8e5b0befe41bfa2c4a89f572a6e57b4794e52988a30b06d5a28c39654b5a` |

## What the extract is

`scc_hydro_<month>_<year>.csv` — one row per ACTIVE asset of the
hydraulic-turbine unit types **HDP** (conv. daily pondage), **HDR** (conv.
daily run-of-river), **HW** (conv. weekly pondage), **HL** (tidal), from the
workbook's `SCC_Report_Current` sheet. Unit type **PS** (Hydraulic
Turbine - Reversible) = pumped storage is **excluded** — a storage resource
in this model, never part of the conventional-hydro accreditation pool.
Values are transcribed as published (rules 13/14: no fitting, no rescaling).
The parse is guarded two ways on every run: the summer/winter season blocks
are assigned from the workbook's own merged header labels (not column
positions), and the whole sheet is cross-footed against the
`SCC_Report_Summary` totals before anything is written.

August 2026 vintage: **244 assets, summer SCC 1,396.472 MW, winter SCC
1,433.690 MW**. The 200 `Intermittent` assets carry ISO-NE's own
`Median Reliability Hours Calculation` values, i.e. the tariff's
intermittent-hydro median-output construction is applied by ISO-NE itself
(Market Rule 1 §III.13.1.2.2.1.1 defines the non-intermittent summer
Qualified Capacity as the 5-yr median of these summer SCC ratings — see
`../../accreditation-filings/neiso/README.md` for the tariff research).

## How the class factor is derived

```
HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"]
  = Σ(summer SCC, this extract) / modelled_hydro_nameplate_mw("NEISO")
  = 1,396.472 / 1,899.5 = 0.7352
```

The denominator is the model's OWN accreditation basis (EIA-923 2024 final
census, the same population `_hydro_firm_mw` multiplies), so the credited
ledger term equals ISO-NE's published aggregate capability by construction
and model plants absent from the FCM record enter at zero (conservative
floor). Vintage stability: the same aggregation on the August 2024 /
August 2025 reports gives 0.7389 / 0.7063.

Re-derive when the source updates (a newer SCC vintage or a newer EIA
census — rule 23), never because a residual moved.
