# neiso-64 merit-order guard — patch application notes

Companion to `docs/handoffs/patches/README.md`. The CAMPD **economic-layup
merit-order guard** ships as two patches because both files it touches clear the
rule-27 300-line bar (`scripts/lib/outage_detect.py` 390 → 827,
`scripts/data/derive_campd_unit_outages.py` 1484 → 1599), so neither may be
landed as a regenerated full-file push.

**Apply lib first — the deriver imports from it:**

```
git apply docs/handoffs/patches/campd-merit-order-guard-lib.patch
git apply docs/handoffs/patches/campd-merit-order-guard-deriver.patch
```

Design frozen in `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`
§3a (owner sign-off 2026-07-25).

## What it does

A detected down window is reclassified as **economic layup** rather than a
mechanical outage when the unit's measured SRMC (CAMPD heat rate × delivered
fuel price) sat above `RCC(t)` — the capacity-weighted p90 SRMC of the units
measured running that hour — for ≥ 90 % of the window's hours. Layup windows
leave the availability envelope and are written to the labelled companion
`campd-unit-outages-layup[-{ISO}].csv`, which no loader reads by default.

## Gate and byte-inertness

`MERIT_ORDER_GUARD_ENABLED = False`; surfaced as `--merit-order-guard` on
`scripts/data/derive_campd_unit_outages.py`. **Proven inert at full extract
scale**: a full 2018–2026 re-derive with the flag absent reproduces every
committed extract blob exactly.

| ISO | committed extract blob | re-derived, guard off |
|---|---|---|
| NEISO | `a95c09288410b7bf2f8acce798445a629b277c65` | identical |
| CAISO | `3dc01fae376f932897706446d443370759ba84e8` | identical |
| NYISO | `181fefb98a89f60b6f41cce8f0fe1a02650dbd8d` | identical |
| ERCOT | `b4b48f5a7f8ecef5397bb3f8095a7988e07a9cc8` | identical |
| PJM   | `5283f5c66ef3ec68b1e98b2780d3627678df67c8` | identical |

Regenerate an ISO's corrected pair with:

```
python scripts/data/derive_campd_unit_outages.py --iso NEISO \
    --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 --merit-order-guard
```

and score it against the ISO's published instrument (no solve) with
`scripts/probes/_neiso64_meritguard_score.py`.
