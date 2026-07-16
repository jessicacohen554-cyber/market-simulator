# MISO M-1 max-gen registry POPULATED — the F4 block is lifted for 8 qualifying windows (2026-07-16)

**Session:** `claude/miso-68-cottonwood-keeper-c24hnj` (the miso-68 promotion
session). **Supersedes** the F4 engagement in
`docs/handoffs/miso-phase-b-m1-maxgen-findings-2026-07.md` **for the windows
below** — the OASIS/`cdn.misoenergy.org` access items remain open (re-verified
blocked this session: OASIS CONNECT 502 policy denial, misoenergy.org 403),
but they are no longer the binding constraint: **the 2025 MISO SOM was
published in July 2026** (after the F4 memo was written) and, together with
the IMM Summer-2025 quarterly and the on-disk 2023/2024 SOMs, primary-sources
every material window. Registry: `data/raw/maxgen-events/miso/miso.csv`
(9 rows, every row cited), curated to `data/clean/maxgen-events/MISO/` via the
new `maxgen-events` datatype (schema + registry-pattern intake per the
data-intake contract; tests `tests/test_curate_maxgen_events.py`).

## 1. What the primary sources say (per design window)

| design window | prior status (F4 memo) | adjudication THIS session (primary source) |
|---|---|---|
| Aug 24 2023 Max Gen Event | unconfirmed | **CONFIRMED + hours.** Step 2A Event declared 08:00 EST to begin 12:00 (2023 SOM pp.11-12); Max Gen Alert issued Aug 22 (two days ahead); STR +900 MW Aug 21-25 |
| Jan 14-17 2024 "Max Gen Emergency" | CONTRADICTED | **DEFINITIVELY ABSENT.** 2024 SOM p.10: MISO "effectively managed the system without recourse to Emergency operations"; only Conservative Operations Jan 14 (bad TO flow data, Fig 7). No ladder declaration at any level |
| *(not in design)* Aug 23-27 2024 hot-weather event | — | **NEW WINDOW FOUND.** Max Gen Warning Aug 26 **13:00-20:00 EST** with Tier 0+1 emergency pricing (~+$60/MWh Tier-0 effect), inside Aug 23-27 Conservative Ops; annual peak Aug 26 (2024 SOM p.15) |
| Jun 23-24 2025 Max Gen Event | event-level only | **CONFIRMED.** Jun 23 = Maximum Generation Emergency Step 1 (EEA1), Midwest — the year's only Event day; 565 MW emergency energy; >4 GW trapped South by RDT. Jun 24 = Max Gen Warning, Midwest (2025 SOM pp.iii/14-15, Fig 9/10) |
| Jul 24/28/29 2025 advisories/warnings | unconfirmed | **CONFIRMED + hours for Jul 28.** Ladder (Fig 9, column-position-verified): Jul 24 Capacity Advisory; Jul 28 Max Gen Alert **14:00-22:00 EST** + system-wide Capacity Advisory **Jul 28 12:00 - Jul 29 22:00**; Jul 29 Max Gen Warning (daily-highest). Quarterly p.23 itemizes the Jul 28-29 timeline |
| Jan/Feb/Sep/Oct 2025 | unconfirmed | **Jan = Enzo, NO declaration** — operators raised DA/RT STR requirements instead (2025 SOM p.iii; already the model's measured-reserve-requirements channel). Feb 20-21: nothing found. Sep 16 = **Local Transmission Emergency** (500 kV outage, South — transmission instrument, outside the capacity ladder); Sep-Oct TLR software error → 19 hours repriced under Continuing Error (Oct 9 largest). Oct 6 is post-ER25-579 regime |

Sources (all fetched/verified this session, URLs in the registry rows): 2023
SOM Report Body (on disk), 2024 SOM Report Body (on disk), **2025 MISO SOM**
(`potomaceconomics.com/wp-content/uploads/2026/07/2025-State-of-the-Market-Report.pdf`,
archived to `data/raw/MISO/2025-MISO-SOM_Report.pdf`), **IMM Quarterly
Summer-2025** (`.../2025/11/IMM-Quarterly-Report_Summer-2025-MSC.pdf`,
archived alongside). The IMM/SOM record is primary at the event level (the F4
memo itself accepted "the 2023 SOM emergency table" as sufficient); the OASIS
`Capacity_Emergency_Historical_Information.pdf` remains the **upgrade path**
for endpoint precision on the day-scoped rows when access lands.

## 2. In-merit certificate pre-read (design M-2 guard 2, computed on the committed DA hub record)

Guard 2 (≥2 distinct window hours with DA hub LMP > $150, region-scoped
hubs): **8 of 9 registry rows qualify** —

| window | distinct HE > $150 | max $ | qualifies |
|---|---|---|---|
| 2023 Aug 22-24 (alert, pre-event) | 0 | 134 | **NO** (slack — correctly carries no derates) |
| 2023 Aug 24 Step-2A (noon-EOD) | 5 | 219 | yes |
| 2024 Aug 26 Warning 13:00-20:00 | 2 | 169 | yes (at threshold) |
| 2025 Jun 23 EEA1 (Midwest/North hubs) | 8 | 316 | yes |
| 2025 Jun 24 Warning (Midwest) | 9 | 330 | yes |
| 2025 Jul 24 Capacity Advisory | 6 | 282 | yes |
| 2025 Jul 28-29 Capacity Advisory | 16 | 435 | yes |
| 2025 Jul 28 Max Gen Alert | 7 | 406 | yes |
| 2025 Jul 29 Warning | 8 | 435 | yes |

Certificate-sensitivity note (design asked for the [$120,$200] insensitivity
check): the design's claim holds for every window it knew about, but the
newly-found **Aug-26-2024 Warning peaks at $169** — thresholds above $169
would drop it. The deriver must state this measured fact in its docstring at
derivation (not retune around it): the window is a declared, Tier-0/1-priced
emergency whose in-merit depth is genuinely shallower than the 2023/2025
events.

## 3. Tail coverage — what M-2 can and cannot reach (recomputed, DA Indiana >$200)

- **2023 (1 tail hour):** Aug 24 HE17 — **inside** the Step-2A window. 1/1.
- **2024 (24 tail hours):** Jan 14 (2h) / Jan 15 (7h) / Jan 16 (13h) / Jan 17
  (2h) — **all outside any declared window** (§1: no Jan-2024 declaration
  exists). **0/24.** The design's 2024 C3c expectation (4h → [12,48] via the
  Jan window) is REVISED: **M-2 contributes ~nothing to C3c-2024.** The
  Jan-2024 tail is a *winter fuel-supply/derate/congestion* phenomenon (2024
  SOM: pipeline restrictions, holiday-weekend gas-trading risk premia,
  increased notification times, cold derates, 3.2 GW exports/wheels to SPP) —
  its own lane, distinct from declared-window unavailability.
- **2025 (38 tail hours):** Jun 23 (6h) + Jun 24 (5h) + Jul 24 (3h) + Jul 28
  (6h) + Jul 29 (6h) = **26/38 inside qualifying windows**; outside: Jan 20-22
  (8h — Enzo, raised-STR channel), Feb 20-21 (2h), Sep 29 (1h), Oct 6 (1h,
  post-ER25-579). C3c-2025 target [19,76]: reachable from in-window hours
  alone if M-2 + the miso-67/68 separation engage them.

## 4. Consequences for the composed-probe expectations (design §4, revised)

- C3a-2025 (−14.3% on the miso-68 keeper): unchanged thesis — Jun/Jul
  separation + event-window honesty; Jan-2025 leg is the measured-reserve
  (STR) channel, not M-2.
- C3c-2025 0h → **[19,76] band via the 26 in-window hours** (was: same band,
  but now with per-window primary confirmation).
- C3c-2024: **expectation retired.** 4h vs 24h stands unless/until a winter
  fuel-security/derate lane (rule-19-reconciled with `gas_daily_shape`,
  CAMPD winter outage truth, and the seam/wheel representation) is chartered.
  If C1+C3a reach PASS and C3c-2024 remains the sole miss, the honest verdict
  path is a **ledgered measured-input caveat** (the NEISO/ERCOT precedent),
  not a forced mechanism.
- C1 CC_REGULAR-2023 (−8.28): M-2's 2023 footprint is one afternoon — not a
  C1 lever. The residual stays owned by the price-formation/dispatch question
  (miso-68 promotion record).

## 5. Also found (side lanes, not this charter)

- **DOE emergency orders (Jun + Dec 2025) directed 1.6 GW of retiring MISO
  coal to stay online** (2025 SOM p.75), prohibited from being capacity
  resources. Flag for the confirmed-retirements registry: potential
  `superseding_instrument` rows (counter-instrument class already in schema).
- **Sep-Oct 2025 TLR repricing** (19 hours across 8 market days, Continuing
  Error provisions; largest Oct 9): a measured actual-price-formation anomaly
  inside the bench window — context for any future Sep/Oct-2025 residual
  read; no model change is admissible from it.
- **Emergency-pricing tiers documented** (2023 SOM p.10, 2025 SOM fn.17):
  Alert → 4-h online resources price-set in ELMP; Warning → Tier 1 ($500/MWh
  offer floor) + non-firm export curtailment + external capacity calls;
  Step 2 → Tier 2 + LMRs. If C3c stays dark after M-2 (fallback F5), THIS is
  the measured MISO-parameter basis for the scarcity-depth charter — a
  declared-window ELMP emergency-pricing treatment, not an ERCOT/NYISO
  analogue import (rule 25).

## 6. What remains for Phase B execution (design §6, from step 4)

1. **M-2 deriver** (`unit_outage_maxgen_events`, gated default-OFF) on the
   frozen guards — now scoped to the 8 qualifying windows; ±45-day
   capability basis; disjointness vs std/short extracts; certificate
   sensitivity note per §2.
2. **Composed probe** (miso-68 keeper stack + M-2), 2023+2024+2025 one bundle
   + same-box base, per-year+reuse on a ≤16 GB box (this container: 15 GB —
   the per-year pattern is mandatory).
3. Reads per design §4 as revised in §4 above; fallbacks F2/F3/F5 unchanged
   (F1 is moot — miso-67/68 landed; F4 is discharged for these windows).
4. Registration chain per design §6.7 (D4_WINDOWS entry for the maxgen
   mechanism id = exactly the registry windows).
