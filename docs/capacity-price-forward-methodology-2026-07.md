# Forward net-CONE / capacity-price methodology (FF-G3, 2026-07)

**Session:** FF-G3 (lane L-CAP), branch
`claude/forward-net-cone-vintages-txs2an`, 2026-07-20. **Status:** standing
methodology reference for the *forward-year* (2026–2050) net-CONE anchor that
drives every capacity-market ISO's retirement / entry / storage economics.
Companion to the historical-vintage machinery in
`config/constants.py` (`MARKET_DESIGN`, `MARKET_DESIGN_VINTAGES`,
`resolve_demand_curve_vintage`) and the CR-1/CR-2 validation work
(`docs/handoffs/capacity-price-validation-2026-07-12.md`). Session handoff +
owner-decision box: `docs/handoffs/ff-g3-net-cone-forward-2026-07.md`.

Everything here is **forecast-only surface**: capacity evolution and the
capacity-price seam run only in `mode="forecast"` (`runner.py`), so backcast
keepers are byte-identical to before this session (§7). No default is flipped;
no LP was solved.

---

## 1. The gap this addresses

`resolve_demand_curve_vintage(iso, year)` **holds-last** for any year after an
ISO's most recent published delivery-year vintage (its docstring, third
bullet). A 2026–2050 forecast therefore reads **one frozen net-CONE anchor for
every year past the last auction on disk**. Because real-world CONE has moved
sharply — PJM's just-cleared 2028/2029 BRA net-CONE is **+34 %** over the
2027/2028 value now on disk (§3.1) — that frozen anchor is a live bias on
2030s+ retirement and entry economics in every capacity-market ISO.

This was named "CR-2 follow-up: per-forecast-year net-CONE" in
`docs/handoffs/capacity-price-validation-2026-07-12.md` §6/§7 and routed to the
curve-eligibility lane by `docs/handoffs/ff-2b-adequacy-basis-2026-07.md`, but
never chartered until FF-G3. This is that charter.

Two distinct sub-problems, kept separate throughout:

1. **Re-anchoring** — the last *published* vintage on disk is stale (PJM 2027/28
   vs the cleared 2028/29). The fix is intaking each newly-published vintage.
   This session is **blocked** from completing it (§6: the machine-readable
   sources are bot-walled in this environment) and files the researched values
   as MANUAL DOWNLOADS NEEDED.
2. **Forward evolution** — how the anchor should behave for years *beyond* the
   last published vintage. This session **designs** the explicit rule (§2) as an
   alternative to silent hold-last, findings-first, default-OFF.

## 2. Design — the forward-evolution rule

Shipped this session (all default-inert; scope guard: the pricing seam
`MarketDesign.capacity_price_per_firm_mw_yr` is **untouched** — FF-2C owns
wiring the resolver into the seam and the per-ISO clearing flips):

- **`ScenarioConfig.net_cone_forward_escalation`** (`config/scenarios.py`),
  `"hold_last"` (default) | `"reindex_net"` | `"reindex_gross"`. In
  `_CACHE_KEY_OPTIONAL_FIELDS` (default dropped from the hash → every existing
  cache key byte-stable) and `__post_init__`-coerced to `"hold_last"` in a plain
  backcast (no capacity evolution there). Tier-2 sensitivity axis.
- **`constants.forward_net_cone_anchor(iso, year, escalation, *, rate,
  eas_offset_per_kw_yr)`** — the pure resolver layered on
  `resolve_demand_curve_vintage`. It escalates the anchor **only for years after
  the last published vintage's start year**; a year at/before it returns the
  published anchor unchanged (rule 13). Returns `None` for CAISO/ERCOT (no
  vintage table → caller keeps the fixed proxy).
- **`constants.NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO`** — the cited per-ISO
  **real** escalation rate the reindex modes use when no explicit rate is
  passed. **0.0 for every ISO** (§4 finding), so with no override every mode
  collapses to `hold_last` — the byte-identity guarantee and the honest central
  result.

The three modes:

| mode | formula (year `n` past last vintage; `a` = last published net-CONE, `o` = E&AS offset) | fidelity |
|---|---|---|
| `hold_last` | `a` | status quo; the seam reads this today |
| `reindex_net` | `a · (1+rate)ⁿ` | LOW — indexes net-CONE directly; the field does **not** do this (§4) |
| `reindex_gross` | `(a+o)·(1+rate)ⁿ − o` | HIGH (field-standard) — escalate GROSS, re-net the offset. `o` here is the published gross−net gap held real-flat (offline illustration); the **structurally-faithful** version re-nets against the model's OWN simulated E&AS margin each forecast year, wired at solve time by FF-2C. |

## 3. Per-ISO grounding

### 3.1 PJM (RPM VRR curve)

- **On disk (last encoded vintage):** 2027/2028, net-CONE **242.52 $/MW-day
  UCAP = 88.52 $/kW-yr** (`pjm.csv`; `MARKET_DESIGN_VINTAGES["PJM"]`).
- **Newest published (researched, NOT yet encoded — §6):** **2028/2029 BRA**,
  cleared July 2026, net-CONE **325.69 $/MW-day UCAP = 118.88 $/kW-yr** (Gross
  CONE ICAP 223,800 $/MW-yr; E&AS offset 129,887; Net CONE ICAP 93,913),
  price collar cap/floor 325.00/175.00 $/MW-day (FERC ER26-1556). First delivery
  year on the new Brattle-2025 Quad/Periodic-Review gross-CONE basis (ER26-455)
  — hence the +34 % step. Source: PJM 2028/2029 RPM BRA Planning Period
  Parameters (posted 2026-04-29). sha256 of the report PDF pinned in the raw
  README; the Table-3 net-CONE is an image in the PDF and the machine-readable
  XLSX is bot-walled here (§6).
- **Escalation method:** Gross CONE re-derived bottom-up in the periodic
  Quad/Periodic Review (the current one = **Brattle 2025 CONE Report**); between
  reviews the Benchmark Gross CONE is escalated by the **"Applicable BLS
  Composite (construction-cost) Index" × 1.022** (bonus-depreciation
  adjustment), per **OATT Attachment DD §5.10(a)(iv)** / Manual 18. Net CONE =
  escalated Gross − forward E&AS offset (shaped on the prior 3 calendar years'
  LMPs). Brattle recommends escalating the Reference Price **on inflation only**
  for out-years 2029/30–2031/32. (Handy-Whitman is PJM's *Avoidable Cost Rate*
  escalator, **not** CONE.)

### 3.2 NYISO (ICAP demand curve)

- **On disk:** 2025-2026, NYCA Annual Reference Value **50.55 $/kW-yr**
  (`nyiso.csv`).
- **Cycle:** the **2025-2029 Demand Curve Reset** (FERC ER25-596, accepted
  2025-01-28); reference resource switched to a **2-hour Li-ion BESS** (was a
  CT). Only 2025-2026 (on disk) and **2026-2027** (posted ~Nov 2025) are
  published; 2027-2028 / 2028-2029 post ~Nov 2026 / ~Nov 2027.
- **Newest published (researched, NOT retrieved — §6):** 2026-2027 annual-update
  parameter sheet exists but its numeric NYCA ARV was not obtainable (document-
  library URL not locatable; MANUAL DOWNLOAD).
- **Escalation method:** quadrennial reset (bottom-up study) + **annual updates**
  escalating three inputs (tariff **MST 5.14.1.2.2.1**): gross CONE by a
  **composite escalation factor** = technology-weighted blend of BLS PPI
  Materials (WPUID612), BLS QCEW NY utility-construction labor (NAICS 2371), BLS
  PPI Gas & Steam Turbines (WPU1197), and the **BEA GDP implicit price deflator**;
  the Net-EAS offset re-estimated on a rolling 3-year window then escalated by the
  GDP-deflator. (Prior-cycle 2024-2025 update: composite factor 15.89 %/16.66 %,
  net-EAS escalation 11.40 % — reflecting the 2022-24 surge; current-cycle
  factors not retrieved.) **Not Handy-Whitman, not a single CPI.**

### 3.3 ISO-NE (Forward Capacity Market → terminating)

- **On disk:** 2027-2028, FCA 18 net-CONE **9.078 $/kW-mo × 12 = 108.94
  $/kW-yr** (`neiso.csv`) — the LAST forward auction actually **held** (cleared
  $3.58/kW-mo, 2024-02-05).
- **Regime transition (the key finding):** the **FCM is being replaced by a
  prompt/seasonal capacity market** for the CCP beginning 2028-06-01. CAR-PD
  (prompt auction + 1-yr deactivation) was **accepted by FERC 2026-03-30**
  (ER26-925-000); CAR-SA (seasonal split + resource-capacity accreditation) is
  expected to file Q4 2026. **The successor market has NO published net-CONE or
  demand-curve numeric parameters as of mid-2026 — design only.**
- **Newest published (researched, regime-superseded):** ISO-NE *did* publish
  forward CONE/Net CONE for the **2028/2029 CCP** in its Nov-2023 MOPR-
  elimination filing — Net CONE **9.614 $/kW-mo (= 115.37 $/kW-yr)** / Gross CONE
  14.759, at the proposed 8.96 % ATWACC. **No forward auction will clear against
  these** (FCA 19 is superseded), so they are documented, not encoded.
- **Escalation method:** bottom-up DCF CONE study each full-recalculation cycle
  (next full recalc at FCA 21) + **interim-year updates for inflation (capital)
  and fuel** (Tariff **§III.13**). Handy-Whitman (Total Other Production Plant,
  North Atlantic) escalates the FCM **qualification thresholds**, *not* the
  CONE/Net CONE figure itself.

### 3.4 MISO (seasonal PRA / RBDC)

- **On disk:** PY2025-2026, North/Central Net CONE **79,800 $/MW-yr = 79.8
  $/kW-yr** (`miso.csv`; seasonal RBDC carried).
- **Newest published (researched, aggregates only — §6):** **PY2026-2027 CONE &
  Net-CONE Update** (FERC **ER26-139-000**, filed 2025-10-15, eff. 2025-12-15) —
  N/C aggregate Net CONE ≈ **81.0 $/kW-yr** (South ≈ 76.1). Per-LRZ Net CONE is
  the filing's **Attachment C** (not in the transmittal/RASC deck) and the
  PY2026-27 seasonal RBDC point tables are a separate RASC/BPM-011 posting —
  both MANUAL DOWNLOAD.
- **Escalation method:** CONE **re-derived bottom-up every year** (Tariff
  **§69A.8**, BPM-011 App. R) from the EIA Feb-2020 capital-cost report
  (advanced-CT Case 6), costs converted to planning-year dollars via the **CBO
  implicit GDP price deflator (~2.03 % for PY26/27)** + O&M escalation, with
  annual tax/cost-of-debt refreshes. Net CONE = CONE − trailing-3-yr
  inframarginal rents (gas-futures-scaled).

### 3.5 CAISO (bilateral RA — no CONE curve)

- **On disk / registry:** fixed proxy **90 $/kW-yr** in both modes (no vintage
  table). The honest administrative analogues:
  - **CPM soft-offer cap** = **$7.34/kW-mo = $88.09/kW-yr** (FERC ER24-1225, eff.
    2024-06-01 = 120 % × the CEC study's $73.41/kW-yr going-forward fixed cost
    for a 550 MW CC). **Static, reviewed only every 4 years** (next ~2028) — **no
    forward escalating schedule exists.**
  - CPUC Annual RA Report weighted-average prices (2023 report: system $14.33 /
    local $11.21 / flexible $7.80 $/kW-mo) — **backward-looking reported
    transaction averages**, no forward benchmark.
- **Forward treatment:** hold flat until the next 4-yearly reset (which
  re-derives from the reference CC's going-forward cost). `forward_net_cone_anchor`
  returns `None` for CAISO → the caller keeps the fixed proxy, consistent with
  the field finding that CAISO has no forward CONE trajectory.

## 4. Field survey — how forward capacity price is treated

Surveyed 2026-07-20 (full ledger in the handoff). The load-bearing finding:

> **Every ISO / Brattle process that sets a multi-year forward capacity
> parameter escalates GROSS CONE by a construction-cost index and independently
> recomputes the E&AS (net) offset each year — net-CONE is always a derived
> residual, never an independently escalated series.**

| model / practice | forward capacity-price treatment | source |
|---|---|---|
| **NREL ReEDS** | no admin CONE; planning-reserve-margin (PRM) constraint, capacity value = the constraint **dual** (analysts may substitute the annualized CT cost) | NREL fy22osti/81611 |
| **EIA NEMS / AEO EMM** | no admin CONE; regional reserve-margin constraint, cost allocated to customers as a capacity component | EIA EMM AEO2025 doc |
| **EPA IPM** | reserve-margin constraints from NERC/RTO targets; capacity value = constraint dual | EPA IPM Ch.2 |
| **PJM** | gross CONE re-studied (Brattle Quad Review); between studies BLS-Composite × 1.022; net = gross − forward E&AS | OATT Att. DD §5.10; Brattle 2025 |
| **ISO-NE** | bottom-up DCF study + interim inflation/fuel updates; HW on qualification thresholds only | Tariff §III.13 |
| **NYISO** | quadrennial reset + annual composite-index (BLS PPI + BEA deflator) on gross; net-EAS re-estimated | MST 5.14.1.2.2.1 |
| **MISO** | annual bottom-up recompute (EIA capital data × GDP deflator); net = CONE − 3-yr rents | Tariff §69A.8 |
| **Brattle** | fresh bottom-up gross for the anchor year, then escalate gross by a construction/PPI index, re-net the offset; Reference Price on inflation only for out-years | Brattle 2025 PJM CONE report |
| **IMMs** (Monitoring Analytics / Potomac) | report net revenue vs Net CONE year-by-year off updated forward E&AS; no smooth multi-year forward net-CONE series | PJM/ISO-NE SOM/EMM reports |

**Why net-indexing (candidate b) is disfavored:** gross CONE and the E&AS
offset are driven by different, often opposing forces (2022–2025: capital +43–46 %
*and* energy prices up → net-CONE can move any direction while gross rises
monotonically). A single index on net-CONE — a residual of two large numbers —
has no physical referent and diverges fast over 25 years.

**Why hold-flat (candidate c) is a placeholder:** it ignores the documented
~24–46 % real capital surge. It is defensible in REAL terms **only** when the
last-published vintage is kept current by re-anchoring (§1 sub-problem 1) — which
is exactly why re-anchoring, not smooth escalation, is the primary fix.

**Central real rate = 0.0 (the finding, not a placeholder):** because the field
re-nets and re-anchors rather than trending real net-CONE, and Brattle's own
out-year guidance is inflation-only, `NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO`
is 0.0 for every ISO. A positive real rate is an explicit **structural-tightness
sensitivity** (the 2022–25 turbine surge persisting), never a default.

## 5. Delta ledger — old (on-disk hold-last) vs newest published forward anchor

The re-anchoring gap a curve-ON forecast would pick up by intaking the newest
vintage (all default-inert until FF-2C wires the seam AND an ISO's clearing flip
is on — most are curve-eligible but default-OFF):

| ISO | on-disk anchor ($/kW-yr) | newest published ($/kW-yr) | Δ | encode-able now? |
|---|--:|--:|--:|---|
| PJM | 88.52 (2027/28) | **118.88** (2028/29, cleared 7/2026) | **+34.3 %** | No — Table-3 image + XLSX bot-walled (§6) |
| NYISO | 50.55 (2025-26) | (2026-27) — not retrieved | — | No — sheet not locatable (§6) |
| NEISO | 108.94 (2027-28, FCA18) | 115.37 (2028-29, FCA19 *regime-superseded*) | +5.9 % | No — regime-superseded; FCM terminating |
| MISO | 79.80 (PY25-26) | ~81.0 (PY26-27 N/C aggregate) | +1.5 % | No — per-LRZ Net CONE in Attachment C (§6) |
| CAISO | 90.0 (fixed proxy) | 88.09 (CPM soft cap, static to ~2028) | −2.1 % | n/a — no vintage table / no forward schedule |

## 6. Divergence quantification (2026–2040) — hold vs the two reindex rules

Illustrative, at **+2 %/yr REAL** index escalation (a mid structural-tightness
sensitivity; the cited central rate is 0.0 → all modes = hold_last). Anchors are
each ISO's on-disk net-CONE curve anchor ($/kW-yr); `reindex_gross` uses the
published gross/net **leverage** (PJM 2.18, NYISO 2.53, NEISO 1.57, MISO 1.59)
so an `r` on gross moves net-CONE by ≈ leverage × `r`:

| ISO | anchor | reindex_net 2030/2035/2040 | reindex_gross 2030/2035/2040 | 2040 Δ (net / gross) |
|---|--:|--|--|--|
| PJM | 88.52 | 93.9 / 103.7 / 114.5 | 100.4 / 121.7 / 145.3 | **+29 % / +64 %** |
| NYISO | 50.55 | 55.8 / 61.6 / 68.0 | 63.8 / 78.5 / 94.7 | **+35 % / +87 %** |
| NEISO | 108.94 | 115.6 / 127.6 / 140.9 | 119.4 / 138.2 / 159.0 | **+29 % / +46 %** |
| MISO | 79.80 | 88.1 / 97.3 / 107.4 | 93.0 / 107.7 / 123.8 | **+35 % / +55 %** |

Reproduce with `forward_net_cone_anchor(iso, year, mode, rate=0.02,
eas_offset_per_kw_yr=…)`. The gross/net leverage is why the mode choice is
material: at the same index rate `reindex_gross` moves net-CONE ~1.6–2.5× more
than `reindex_net`. Every $/kW-yr of net-CONE flows straight into the
retirement/entry screens' capacity-revenue term (rule-1 mechanism), so the
2035+ divergence directly re-weights the fossil-exit vs new-entry balance.

## 7. Verification

- `tests/test_net_cone_forward.py` (19 tests): `hold_last` ≡ the seam's current
  hold-last anchor for every ISO/year (byte-identity); central-rate collapse;
  reindex arithmetic identity; no-escalation at/before the last vintage;
  `reindex_gross` re-net + requires-offset; CAISO/ERCOT → None; registry hygiene
  (exactly the capacity-market ISOs, all rates 0.0); config default / cache-
  neutrality / reindex-changes-key / backcast coercion / validation.
- **Default `cache_key` cache-neutral** — reverting the change and re-adding it
  reproduces the same base-main key (`494427c4405cba78` on current main; the
  field is dropped from the hash at its `"hold_last"` default).
- `tests/test_capacity_demand_curve.py` (58) + `tests/test_config.py` (…) green;
  no vintage anchor changed (no new vintage encoded — §6).
- Pricing seam untouched; no LP solved; nothing registered on any dashboard.

## 8. Gaps / MANUAL DOWNLOADS NEEDED (re-anchoring backlog)

Bot-walled in this environment (standard fetch returns empty/JS shells; the
agents' curl workarounds got PDFs but the numeric tables are images and the
XLSX/eLibrary attachments need an interactive download). Each needs a manual
download + byte-verified intake through the curation pipeline before its anchor
is encoded (rule 13 — no guessing). Values are researched, cited, and pinned by
sha256 where a PDF was obtained (raw README table):

1. **PJM 2028/2029** net-CONE 325.69 $/MW-day UCAP — Table 3 is an image in the
   report PDF (sha256 pinned); the machine-readable Planning-Parameters XLSX is
   bot-walled. Also needs the VRR point a/b/c x-positions (the 2028/29 VRR
   *equation* changed: `max(1.15·Gross − 75 %·E&AS, 0.2·Gross)`).
2. **NYISO 2026-2027** annual-update parameter sheet — document-library URL not
   locatable.
3. **MISO PY2026-2027** per-LRZ Net CONE (FERC eLibrary ER26-139 Attachment C)
   and the seasonal RBDC point tables (RASC/BPM-011 posting).
4. **ISO-NE 2028-2029** FCA 19 parameters exist (Net CONE 9.614 $/kW-mo) but are
   **regime-superseded** (FCM terminating); the prompt/seasonal successor's
   parameters are unpublished (design only). Encode only if/when the successor
   market publishes numeric parameters, or as an explicitly-labelled superseded
   historical vintage.
5. **BLK-9 interaction (report-only, do NOT fix here):** the fixed capacity
   payment clears 1.26–4.92× of FOM for every fossil class, inverting economic
   retirement onto nuclear (gap-register BLK-9). A higher forward net-CONE
   (re-anchoring or a positive reindex rate) *widens* that inversion; a lower one
   narrows it. FF-G3's anchor work feeds that chain — its resolution rides the
   BLK-3/BLK-4 accreditation-basis migration, never a payment haircut (rule 13).

## 9. Maintenance rules

- **Re-anchor on a source update, never on a residual** (rules 13/23). Each new
  published vintage lands as: append `<iso>.csv` rows + README sha256 row →
  encode the `MarketDesignVintage` → the `test_capacity_demand_curve.py`
  reconciliation asserts equality. Adding a vintage automatically re-bases
  `forward_net_cone_anchor`'s hold-last / escalation start year.
- **The escalation rate moves only on a published-index or field-guidance change**,
  cited in the commit. The shipped central 0.0 is a finding (inflation-only), not
  a tuned value.
- **Wiring is FF-2C's** (`net_cone_forward_escalation` → the pricing seam) jointly
  with the per-ISO `capacity_market_clearing` flip; the faithful `reindex_gross`
  E&AS re-net is supplied by the model's own simulated offset there, not the
  held-flat published gap used for the §6 illustration.
