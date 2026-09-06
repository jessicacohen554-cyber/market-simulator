# `spp-hsl` — SPP wind curtailment / uncurtailed-HSL inputs

Opened **2026-09-06** by lane **SPP-12** (plan §6 manifest row 10). Sources and
exact URLs: `SOURCES.md`.

## What this is

The **curtailed** leg of SPP's variable-energy accounting. The program needs it
for the same reason MISO and NYISO needed theirs
(`docs/multi-iso/forecast-uncurtailed-hsl-finding-2026-07.md`,
`nyiso-uncurtailed-hsl-finding-2026-07.md`): a renewable upper bound built from
*delivered* generation is an upper bound on what the grid **took**, not on what the
fleet **could have produced**, and in a footprint that curtails ~10 % of its wind
that gap is not a rounding error. Rule 3 `[R-RENEW-VAR]` puts renewables on the LHS
with `ub = CF x capacity`; if that CF is built from curtailed output the model can
never dispatch the wind SPP actually spilled, and the congestion the spill
represents gets absorbed into the offer curves instead — which is exactly the kind
of silent compensation rule 14 `[R-ACCURATE]` exists to prevent.

## What landed: `spp_wind_curtailment_annual.csv`

**Transcribed from the SPP MMU's Annual State of the Market reports** — the
portal's own `ver-curtailments` product is blocked (below), so this is the
manifest row's stated manual fallback, taken.

| Metric | Years | Published or derived |
|---|---|---|
| `avg_hourly_curtailment_mw` | 2019, 2022, 2023, 2024, 2025 | **published** |
| `wind_generation_gwh` | 2024, 2025 | **published** (caveated — see below) |
| `wind_nameplate_mw` | 2023, 2024, 2025 | **published** |
| `curtailed_energy_gwh` | 2019, 2022, 2023, 2024, 2025 | derived: MW x 8760 / 1000 |
| `curtailment_share_pct` | 2024, 2025 | derived: curtailed / (wind gen + curtailed) |

The published series, so it is readable without opening the CSV:

| Year | Avg hourly curtailment | Basis |
|---|---|---|
| 2019 | 137 MW | wind |
| 2022 | 1,260 MW | wind |
| 2023 | 1,097 MW | wind |
| 2024 | 1,483 MW | wind |
| 2025 | 1,382 MW | variable energy resources (wind+solar) |

### Three things a consumer of this file must know

1. **SPP publishes no curtailment percentage.** The manifest row asks for an
   "annual wind curtailment %"; the ASOMs do not contain one. What they publish is
   an *average hourly MW*. The `curtailment_share_pct` rows are this lane's
   arithmetic over two published numbers, are labelled `derived=yes`, and carry
   their formula in the row's `note`. They are an order-of-magnitude figure
   (~10.5 % in 2024, ~9.9 % in 2025) — **not** a measured rate, and not a
   substitute for the per-hour curtailment the model would actually want.
2. **The basis changes at 2025.** The 2023 and 2024 editions title the figure
   *"Curtailments for wind resources"*; the 2025 edition titles it *"Curtailments
   for variable energy resources"*. The same 2025 page bounds the difference —
   *"solar curtailments average only 10 MW per hour and represent only 0.73 % of
   total curtailments"* — so the series is comparable in practice, but a strict
   like-for-like comparison of 2024 to 2025 is off by that ~0.7 %.
3. **`wind_generation_gwh` rests on a sentence whose year labels are
   inconsistent.** ASOM 2025 p. 50 reads: *"Annual wind generation dropped just
   slightly (0.2%) from 110,400 GWH in 2025 to 110,200 GWh in 2024."* Read
   literally that is a **rise** from 2024 to 2025, which contradicts "dropped". The
   assignment used (2024 = 110,400, 2025 = 110,200) is the only one consistent with
   the report's own stated −0.2 %. The verbatim sentence is in the row `note` so a
   reader can disagree.

## What is still missing

| Wanted | Status |
|---|---|
| Per-hour or per-interval curtailment (the model's real need) | **blocked** — portal `ver-curtailments`, 5-minute SPP-total VER curtailment |
| Per-resource / per-zone curtailment | **does not exist publicly** — SPP's own product description says *"SPP total VER curtailment (not per resource)"* |
| Uncurtailed HSL by unit | not published; the MISO/NYISO reconstruction route applies |
| Delivered-wind denominator at better than annual resolution | **blocked** — portal `generation-mix-historical` (`data/raw/spp-genmix/`) |

## Portal block (2026-09-06)

`portal.spp.org`'s `ver-curtailments` product — *"VER curtailment data in 5 minute
intervals for SPP total VER curtailment (not per resource)"*, `isPublic: true` —
returns an empty listing (`200 []`) and 404s on download for an anonymous caller,
like every other portal data product. Full evidence:
`docs/handoffs/FINDING-spp-12-2026-09-06.md`, and the identical block table in
`data/raw/spp-genmix/README.md`.
