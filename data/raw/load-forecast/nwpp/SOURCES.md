# NWPP long-term load forecast — the assembly rule

`nwpp.csv` — the `load-forecast` datatype's NWPP partition. Landed
**2026-09-13** by lane **NWPP-12**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` manifest row 9, hard gate
**G12**; FINDING `docs/handoffs/FINDING-nwpp-12-2026-09-13.md`).

## The headline, because gate G12 turns on it

**A citable long-term load forecast exists for this footprint, with an edition
and a vintage ≥ 2020 — but only as an ASSEMBLY, because the Northwest Power
Pool publishes no footprint-wide long-term load forecast.** NWPP is a pool of
17 balancing authorities, not an ISO; it issues no Gold Book, CELT, LTLF or ITP
equivalent. Every long-term load number for this footprint is published by an
individual utility in its own state-regulated Integrated Resource Plan.

So the assembly is the forecast, and the assembly is documented here rather
than buried in a derivation.

**Declared edition and vintage for `scripts/lib/load_forecast/nwpp.py`
(NWPP-20's file, not this lane's):**

```
edition = "Participant IRP assembly (2025 cycle)"
vintage = 2025
default_basis = "unspecified"
```

`vintage = 2025` is the **latest constituent publication vintage that actually
supplies a row** (PacifiCorp 2025 IRP filed 2025-03-31; Idaho Power 2025 IRP
June 2025). NorthWestern's **2026** Montana IRP is newer and is in the corpus,
but supplies **no** row (its load tables are images — see "Publishers that
supply no row"), so dating the assembly 2026 would overstate it.

`edition` and `vintage` are also **per row** in `nwpp.csv`, so the mixed
constituent vintages stay visible instead of being flattened into the
spec-level label. A consumer reading only the spec sees 2025; a consumer
reading the rows sees that PSE's two rows are a 2023 publication.

## The assembly rule, stated so it can be checked

1. **One publisher, one `area`, `area_type = "planning_area"`** — the same
   convention `data/raw/load-forecast/soco/soco.csv` uses for "Georgia Power
   Company". No row is attributed to "NWPP" as a whole, because no publisher
   forecasts that footprint.
2. **Published values only, in the units the publisher printed them in.**
   Nothing is converted, rescaled, interpolated or summed. In particular:
   - Idaho Power's energy series is published in **aMW** (Table 8.1, printed
     p. 87). The datatype's `energy_gwh` metric cannot carry aMW without a
     conversion, and this lane does not make it — **no energy row is written for
     Idaho Power.** The same applies to PSE's `2,551 → 3,699 aMW`.
   - PacifiCorp publishes a **summer coincident** peak, so its rows use
     `summer_peak_mw`. Idaho Power and PSE publish an **annual system** peak, so
     theirs use `annual_peak_mw`. These are different quantities and the metric
     column keeps them apart rather than pooling them.
3. **Publisher gaps are reproduced, not filled.** Idaho Power's Table 8.2 jumps
   from the 2024 actual straight to 2026 — **there is no 2025 row in the
   publication and there is none here.**
4. **Percentiles map onto the canonical scenario axis** and the publisher's own
   label is preserved: Idaho Power 10th → `low`, 50th → `mid`, 95th → `high`,
   with `published_case` carrying "10th Percentile" / "50th Percentile" /
   "95th Percentile". Its `2024 (Actual)` row is `scenario = "actual"`, which is
   what the datatype reserves that label for (rule 13 `[R-MEASURED]`: carried so
   a CAGR can be anchored on the publication's own base year, never a scoring
   target).
5. **Nothing is scaled to the footprint.** See Coverage.

## Coverage — and why it is the load-bearing caveat

| Publisher | Rows | Model BA(s) | 2024 share of footprint demand |
|---|---|---|---|
| PacifiCorp | 20 (`summer_peak_mw`, 2025–2044) | `PACE` + `PACW` | 18.10 % + 7.30 % = **25.40 %** |
| Idaho Power | 61 (`annual_peak_mw`, 2024 actual + 2026–2045 × 3 scenarios) | `IPCO` | **6.43 %** |
| Puget Sound Energy | 2 (`annual_peak_mw`, 2024 and 2045) | `PSEI` | **8.53 %** |
| **Total** | **83** | 4 of 17 BAs | **40.36 %** |

Shares are the plan's own measured 2024 EIA-930 BA shares
(`nwpp-addition-plan-2026-09.md` §2.5). **`BPAT` — 20.26 % of footprint demand,
the single largest BA — supplies no row**, because BPA publishes no IRP.

**A consumer that needs a footprint-wide growth path cannot get it by summing
these rows**, and must not try: 60 % of the footprint is absent, PacifiCorp's
metric is a summer coincident peak while the other two are annual system peaks,
and peaks do not add across non-coincident systems in any case (NV Energy's own
IRP makes exactly this point about its two companies — `nwpp-planning/README.md`
§4.5). What these rows **are** good for is a **per-publisher growth rate** that a
`DEMAND_GROWTH_RATES["NWPP"]` derivation can weight, with the weighting declared
and the 60 % gap declared with it.

Two CAGRs the publications state themselves, usable directly and preferable to
re-deriving them from the rows:

- PacifiCorp, printed p. 114: *"compound annual growth rate (CAGR) of **1.67
  percent** over the period 2025 through 2044"* (system summer coincident peak).
- Idaho Power, printed p. 89: peak growth **1.8 %** 2026–2045 at every
  percentile (and printed p. 87: energy **2.3 %** at the 50th).
- PSE, Ch. 6 printed p. 6.1: peak **1.7 %**/yr and energy **1.8 %**/yr,
  2024–2045.

## Publishers that supply no row, and why

Each was fetched and read this session; none is blocked by a host.

| Publisher | BA | Reason |
|---|---|---|
| **Bonneville Power Administration** | `BPAT` | **Publishes no IRP.** BPA is a federal power marketing administration, not a state-regulated utility, and files no integrated resource plan with a commission. Nothing was found in this session to transcribe |
| **NorthWestern Energy** | `NWMT` | 2026 Montana IRP is in the corpus, but Table 29 ("Peak Loads and Imports 2024") and Figure 48 (historic peak shape) are **images**; `pypdfium2` returns nothing for them |
| **NV Energy** | `NEVP` | 2024 Joint IRP Vol. 6 Table LF-1 ("Annual Native Energy (GWh) and Peak (MW)") is an **image**. The narrative CAGRs ARE transcribed in `nwpp-planning/README.md` §4.5 (2025–2044 coincident-peak CAGR 2.2 %, system peak +4,811 MW) but a CAGR is not a series and is not written here as one |
| **Portland General Electric** | `PGE` | Table 104 ("Peak load forecast by Need Future and season, MW", printed p. 469) is an **image**. PGE's only transcribable peak figure is a footnote approximation (*"peak load of approximately 4,000 MW"*), which is not a forecast row |
| **Avista** | `AVA` | The 2025 Electric IRP prints growth **rates** (summer peak +1.14 %/yr, winter +1.12 %/yr, 20-year; last 10 years 1.7 %) and Figure 1's series is an **image**. Rates without a base year are not a series |
| Chelan / Douglas / Grant County PUDs, Seattle City Light, Tacoma Power, WAPA-UGP West, Avangrid, Gridforce | 8 BAs | No IRP found in this session. Several are municipal or federal and file no state IRP |

Every "image" row above is a **table-extraction** limit, not a fetch failure.
A follow-up that needs those series should plan on image extraction or hand
transcription from the public PDFs (`data/raw/nwpp-planning/SOURCES.md`), not
another fetch.

## Rule 13 `[R-MEASURED]` posture

Identical to the datatype's: every row is a **forward-looking published input**
that regenerates when the publisher issues its next IRP and responds to changed
conditions (these are exactly the documents that re-forecast when load,
policy or resource costs move). The one `scenario = "actual"` row is Idaho
Power's own 2024 peak, printed beside its forecast and carried only as the
publication's base-year anchor — never a scoring target and never something a
model output may be pinned to.
