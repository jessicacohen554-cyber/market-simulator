# Cross-model benchmark corridor (T3.3) + SOM net-revenue check (T3.2) — 2026-07-13 (P-3C)

**Session.** P-3C of `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
(§2 Tier 3). Report only — **no LP was solved**, nothing registered on any
dashboard, no holdout year touched (rule 22). External projections and monitor
net-revenue tables are **validation observables — compared, never fit**
(rules 1/13). The companion verdict rewrite is
`docs/forecasting-entry-exit-assessment.md` (same session).

**Model-side coverage caveat (read first).** The P-3A per-year parquets/ledgers
live in the gitignored `results/full-horizon/` cache and were not present in
this session's fresh container. The model side of the corridor is therefore
built from the **committed** P-3A artifacts: the reserve-margin and
capacity/price/CO2 snapshot tables in
`docs/handoffs/full-horizon-findings-2026-07-12.md` (§5, §7 — 2026/2030
anchors for all four scored ISOs, 2040/2050 trend anchors) and the committed
per-year ERCOT golden fixture `tests/golden/ercot_2026_2040.json` (annual CO2,
LW price, and end-2040 capacity/builds for the pinned reference scenario).
Per the manager's scoping, **NYISO (1/25 years) and MISO (0/25, hard blocker)
are absent, not data points.** Where a 2035 number is not committed, the
comparison anchors at 2030 and the 2040 trend and says so — no interpolation
is presented as model output. The model config is the P-3A reference:
`mode="forecast"`, all defaults — notably `capacity_market_clearing=False`
(fixed capacity price), `datacenter_load_path="off"` (no DC block), no carbon
price binding, CAMPD bins.

**External benchmark vintages** (full citations inline): EIA AEO2025 reference
case (Apr 2025 — **pre-OBBBA law baseline incl. EPA CAA §111**, so its coal
trajectory is regulatory-assumption-heavy); NREL Standard Scenarios 2024
Mid-case (Jan 2025, the latest edition); ERCOT CDR Dec 2025; PJM 2026 Load
Forecast (Jan 2026) + 4R study (Feb 2023); CPUC PSP D.24-02-047 (Feb 2024) +
2025–26 TPP (Feb 2025); CAISO 2026 Summer Assessment; ISO-NE CELT 2026 (May
2026); NYISO 2026 Gold Book (draft). AEO2025 ERCOT-regional tables and NREL
SS2024 regional 2030/2035 capacity tables are **not retrievable as static
citable files** (interactive viewers only) — noted where it limits a row.

---

## 1. T3.3 — corridor tables and divergence explanations

Convention: divergence >15 % (or opposite sign/direction) gets a lettered
ours-vs-theirs paragraph. **Divergence is not failure; unexplained divergence
is.** Verdicts per row: IN CORRIDOR / EXPLAINED DIVERGENCE / **UNEXPLAINED —
route to root cause**.

### 1.1 ERCOT

| Quantity | Model (P-3A ref / golden) | External | Verdict |
|---|---|---|---|
| Peak-load growth | mid path: 5 %/yr to 2030, 2.5 %/yr after (`DEMAND_GROWTH_RATES`, DC block off) | CDR Dec 2025 firm summer peak 88.6 GW (2026) → 132.2 GW (2030) protocol-prescribed (~10.5 %/yr bookend); 91.0 GW with SB6 curtailment (~0.6 %/yr) | IN CORRIDOR (inside ERCOT's own scenario spread) — **D1** |
| Reserve margin 2026 / 2030 | 14.9 % / 9.0 % (trough 2.6 % in 2037) | CDR 18.3 % (2026); 2030: −12.7 % protocol vs +27.0 % with SB6 | direction IN CORRIDOR — D1 |
| Solar additions by 2030 | ≈0 economic; golden cumulative solar build 10 GW by **2040** | CDR-eligible planned solar **+29.4 GW by summer 2030**; AEO2025 national solar +162 GW 2024→2030 | **EXPLAINED DIVERGENCE — D2** |
| Storage additions | golden: iron_air 9 GW by 2040 + pace-mapped batteries (per-year series not committed) | CDR planned battery +22.9 GW by 2030 | UNDER-BUILT vs CDR, partially explained — D2 |
| Gas additions | golden: gas_cc +5.0, gas_ct +4.3 GW by 2040 | CDR planned gas/diesel +3.3 GW by 2030; AEO2025 national gas +212 GW by 2035 (CT-heavy) | IN CORRIDOR near-term; far below AEO's national gas revival pro-rata — D3 |
| Coal capacity 2040 | 12.7 GW (≈no retirement after 1.85 GW in 2027) | AEO2025 national coal 168.5→68.8 (2030) →3.3 GW (2035); NREL SS2024 Mid: unabated coal ~gone by 2032 | **EXPLAINED DIVERGENCE — D4** |
| Geothermal / iron-air | **EGS 14 GW + iron_air 9 GW built by 2040** (golden) | ~0 in CDR/AEO/SS2024 for ERCOT-scale EGS by 2040 | **UNEXPLAINED — D5, route to root cause** |
| CO2 trajectory | +34 % by 2040 (155→208 Mt P-3A; golden 151→238) | AEO2025 power CO2 falls steeply (coal exit + solar); SS2024 −64 % CO2e by 2035 | **EXPLAINED DIVERGENCE — D4/D2 compound** |
| LW price 2040 | $216/MWh (P-3A per-plant) vs $70 (golden) — both scarcity-inflated | no external outlook sustains VOLL-era prices; CDR presumes entry closes the gap | **EXPLAINED (mechanism) — D6**, incl. an internal-consistency flag |

**D1 — load growth (in corridor, but only because ERCOT's own spread is huge).**
Ours: a two-era scalar (5 %→2.5 %) with the data-center block off. Theirs: the
Dec-2025 CDR's protocol-prescribed view adds ~44 GW of firm peak in four years
(overwhelmingly contracted large loads), while its SB6-curtailment scenario
adds ~2 GW. The model's mid path lands between ERCOT's own bookends, so the
corridor test passes — but for the wrong reason: the model is *not modeling*
the large-load question that defines the spread (DC block exists, default
off; `DATACENTER_ADDITIONS_MW` is the scenario axis). Any ERCOT adequacy
claim for 2028–2030 is dominated by an input the reference config turns off.

**D2 — solar (and storage) additions: the model misses the defining build-out.**
Ours: essentially zero economic solar entry (10 GW cumulative by 2040 in the
golden fixture; the 2021–25 hindcast built 0 vs 25.1 GW actual). Theirs: 29.4
GW of CDR-eligible planned solar by 2030 alone; AEO2025 has national solar
capacity roughly doubling by 2030 and tripling-plus by 2035 (127.7→238→476 GW
power-sector). This is blocker **BLK-8** of the companion verdict (solar entry
economics zero in both hindcasts, root cause undiagnosed) compounded by the
short construction-committed horizon of the planned-additions channel.
Storage under-build vs the CDR's +22.9 GW is the same family, though the
hindcast showed the storage *pace* mechanism itself is calibrated (+2 %) —
the forecast gap is the pace mapping's later-year values, not the stack.
Explained (known blockers), but it invalidates the ERCOT energy-mix corridor
through 2035.

**D3 — gas: direction matches the AEO revival, magnitude doesn't.** Ours: +9.3
GW gas by 2040. Theirs: AEO2025 adds ~212 GW nationally by 2035 (gas CT more
than doubles), driven by data-center load; ERCOT's near-term CDR planned gas
is only +3.3 GW by 2030 (so near-term we are fine), but with the DC block off
and #2064's under-entry the model never develops AEO-style gas expansion even
as its own reserve margin collapses to 2.6 %. Same root causes as D1/D6.

**D4 — coal: the model keeps ERCOT coal that AEO/NREL retire, and the
divergence is a policy-input choice, not a screen success.** Ours: 12.7 GW of
ERCOT coal still standing in 2040 (confirmed-exit registry only; the economic
screen retires 1.85 GW in 2027 and then nothing). Theirs: AEO2025's near-total
national coal exit by 2035 is driven by CAA §111 compliance dates (a
regulation the model deliberately does not hard-code — and which is
OBBBA/administration-sensitive; AEO2025 froze law as of Dec 2024), and NREL
SS2024 Mid retires unabated coal by ~2032 on economics+policy. With no carbon
price and no §111 analogue in the reference config, retained coal is the
*expected* model behavior — an explained divergence that shifts the question
to the scenario system (carbon/policy bundles exist for exactly this). The
adversarial note: the same screen over-retired 14 GW of ERCOT coal in the
2021–25 hindcast, so "keeps coal in the forecast" is price-path luck, not
demonstrated retirement skill (companion verdict rows 5, BLK-5).

**D5 — 14 GW of EGS geothermal + 9 GW iron-air by 2040: UNEXPLAINED, new
root-cause item.** Ours: the golden fixture's largest single new-entry
technology for ERCOT is enhanced geothermal (14 GW = the 2 GW/yr queue cap
binding every year from `egs_available_year=2030`), plus 9 GW iron-air. Theirs:
no external outlook (CDR queue, AEO2025, SS2024 — SMR <5 GW and H2-CT 2 GW
are the *largest* nascent-tech entries in SS2024 Current Policies) projects
ERCOT-scale EGS this decade-and-a-half. A model whose solar entry is $0-broken
while EGS clears its CONE screen at the cap every year has an entry-economics
*ordering* problem, not just a solar problem — the suspect inputs are the D4
audit-row Wright's-law cost decline on hardcoded deployment and the
"engineering judgment" 2 GW/yr cap (`constants.py:3240`). No gap-register row
exists for this; one should be opened alongside BLK-8.

**D6 — sustained scarcity prices by 2040 (and an internal flag).** Ours: LW
price $216/MWh in the P-3A per-plant 2040 vs $70 in the committed golden
fixture at the same year — both driven by de-firming scarcity (VOLL hours),
neither resembling any external equilibrium view (every outlook assumes entry
responds before sustained VOLL pricing). The mechanism is the companion
verdict's row 11 (#2064 + energy-only under-entry). The **3× spread between
the two committed model artifacts for the same nominal year** additionally
flags that the reference trajectory is sitting on a knife-edge (a handful of
scarcity years dominate the LW average) — worth remembering when quoting any
single ERCOT far-year price.

### 1.2 PJM

| Quantity | Model (P-3A, 22/25 yrs) | External | Verdict |
|---|---|---|---|
| Load growth | mid 3.5 %/yr near / 1.8 % long | PJM 2026 forecast: summer peak +3.6 %/yr (10-yr), winter +4.0 %/yr, energy +5.3 %/yr | IN CORRIDOR (near-term) |
| Near-term adequacy | RM 6.3 % (2026) → 0.3 % (2031) — de-firming phase | 2027/28 BRA procured 5.2 % **short** of the reliability requirement (first shortfall ever); 2025/26–2026/27 cleared at/near cap | direction IN CORRIDOR — D7 |
| Thermal retirements to 2030 | ≈0 fossil (4.1 GW nuclear-only in hindcast; ~0 in forecast) | PJM 4R: **40 GW at risk by 2030** (6 done + 6 announced + 25 policy + 3 economic); AEO2025 retires 100 GW of national coal by 2030 | **EXPLAINED DIVERGENCE — D8** |
| Thermal capacity 2040 | 170 → **244 GW** (+74 GW) | AEO2025 national gas +212 GW by 2035 — PJM pro-rata ≈ +40–50 GW, *net of* coal exit; PJM queue is 94 % renewables | half-explained — D8/D9 |
| VRE 2040 | 25 → 50.5 GW | queue 94 % renewables (~5 % completion rate); AEO2025 solar ×3.7 by 2035 nationally | **EXPLAINED DIVERGENCE — D9** |
| CO2 2040 | 303 → **476 Mt (+57 %)** | AEO2025 power-sector CO2 falls through 2035 (coal→3 GW national); SS2024 −64 % by 2035 | **EXPLAINED DIVERGENCE — D8+D9 compound** |
| RM late-horizon | 17.7 % (2040) → 31.9 % (2047) | no external analogue (planning targets ≈ IRM ~18 %) | EXPLAINED (BLK-9 overshoot) |

**D7 — near-term tightness: the one place the model and the market agree.**
Ours: PJM de-firms to RM 0.3 % by 2031. Theirs: the real 2027/28 BRA just
cleared short of its requirement for the first time in RPM history, at
near-cap prices, on data-center load growth. The *direction and timing* of
Phase-1 tightness is corroborated. The agreement is partly coincidental —
the model gets there without the 40 GW of 4R retirements (it retires ~0) and
without the full DC load (block off), i.e., two compensating omissions — so
this row is corroboration of the stress, not of the mechanism.

**D8 — retirements: the model retires nothing PJM itself says is leaving.**
Ours: ≈0 fossil retirements through 2047 (and the hindcast's only exits were
4.1 GW of *nuclear*, 100 % false). Theirs: PJM's own 4R study put 40 GW (21 %
of installed capacity) at risk by 2030 — 6 GW of it already deactivated when
the study printed — and AEO2025's reference case removes most of the national
coal fleet by 2030–2035. The cause is fully diagnosed in the companion
verdict §2 (BLK-9): the fixed capacity payment covers every fossil class's
going-forward cost 1.6–4.5× in PJM, so the economic screen cannot produce an
exit; the confirmed-exit registry covers only instrument-bound units. This is
the single largest explained divergence in the corridor and the reason the
PJM 2040 CO2/thermal rows cannot be quoted.

**D9 — VRE build: model builds gas where the queue builds renewables.** Ours:
+74 GW thermal vs +25.5 GW VRE by 2040. Theirs: 94 % of the PJM queue is
renewables (even at ~5 % completion that implies a solar-led mix), AEO2025
solar nearly quadruples by 2035, and PJM's shortfall auctions are exactly the
capacity-price signal that CR-1 (default off) would translate into entry. VRE
entry sees no capacity revenue at all in the model (BLK-7) and solar entry is
broken (BLK-8), so entry defaults to gas_cc/gas_ct via the backstop and CONE
screens. Explained; blocks the energy-mix corridor.

### 1.3 CAISO

| Quantity | Model (P-3A, 25/25 yrs) | External | Verdict |
|---|---|---|---|
| Base-year adequacy | RM **−12.7 %** (2026), I7 FAIL (accredited 42.8 < req 56.4 GW) | CAISO 2026 Summer Assessment: PRM **30.8 %** in the tightest hour, 2.5 GW surplus | **EXPLAINED DIVERGENCE (basis bug) — D10** |
| New clean build by 2035 | (per-year series not committed; 2050 VRE 129 GW, +100 GW vs 2026) | CPUC PSP: ~56 GW new clean by 2035 (19 GW solar, 15.7 GW 4-h + 2.8 GW 8-h battery); 2025–26 TPP: >60 GW by 2035 | scale roughly IN CORRIDOR at 2035-ish; composition unverifiable this session |
| RM trajectory | 25.3 % (2030) → **59.7 % (2040)** | CPUC plans to the ~17–25 % PRM band; no outlook approaches 60 % | **EXPLAINED DIVERGENCE — D11** |
| Curtailment | dump → 29 % of renewable potential by 2050 | CAISO curtailment ~single-digit % today; IRP portfolios co-optimize storage to bound it | EXPLAINED — D11 consequence |
| CO2 | −82 % by 2040 (37.8 → 6.9 Mt 2050) | SB100/IRP trajectory: deep decarb by 2045 | direction IN CORRIDOR (achieved by the wrong mechanism — D11) |

**D10 — the CAISO base year contradicts the ISO's own summer assessment by
~43 pp of PRM.** Ours: 2026 accredited firm 42.8 GW vs a 56.4 GW requirement
(−12.7 % RM). Theirs: CAISO's 2026 assessment shows a 30.8 % PRM against a
25 % requirement with a surplus. A 2026 *starting point* this wrong is not a
forecast error — it is the #1532-family accreditation/requirement basis
mismatch surfacing on the supply side (P-3A ranked issue #3; PJM, whose basis
was partially corrected, passes I7). Everything downstream of the CAISO
backstop in 2026–2030 (its 25-pp RM swing in four years) inherits it.

**D11 — the 60 % reserve margin is the fixed-price overshoot, not a view.**
Ours: backstop + entry with a capacity price that never falls (T2.1/T2.2b)
overshoot to RM 60 % and 29 % curtailment. Theirs: CPUC's portfolios hold the
PRM band because procurement *stops* when RA is met. The model's CAISO
decarbonization number (−82 %) therefore cannot be quoted as skill: it is
reached by over-building VRE ~2× the planned pace late-horizon. Explained
(BLK-9 / capacity-price non-response); blocks RM, curtailment, and mix rows.

### 1.4 NEISO

| Quantity | Model (P-3A, 25/25 yrs) | External | Verdict |
|---|---|---|---|
| Load growth | mid 1.5 %/yr near / 1.0 % long (annual energy) | CELT 2026: energy +0.9 %/yr to 2035; summer peak +0.6 %/yr; **winter +2.6 %/yr (region flips winter-peaking by ~2030s)** | level IN CORRIDOR; **shape divergence — D12** |
| RM trajectory | 5.0 % (2026) → 29.3 % (2030) → **67.5 % (2050)**, strictly monotone | ICR-based planning ~mid-teens margins; ISO-NE 2050 study plans to *meet* 51–57 GW winter peaks, not to triple-cover summer | **EXPLAINED DIVERGENCE — D13** |
| Thermal 2050 | 23.5 → 30.8 GW (**+7.3 GW gas grows**) | no New England outlook adds net gas capacity to 2050; FCA prices low (2024 CCP15 $2.61/kW-mo) signalling surplus, not entry | **EXPLAINED DIVERGENCE — D13** |
| VRE 2050 | 4.1 → 73.1 GW | 2050 Transmission Study integrates ~9.6 GW OSW; CELT BTM-solar modest; no 73 GW VRE view exists for NEISO | over-build, same mechanism — D13 |
| Retirements | **0 MW thermal, 25/25 years** (P-3B T2.4c) | ~5 GW of NE oil/coal steam is retirement-watch in every regional outlook | **EXPLAINED DIVERGENCE — BLK-9** |
| CO2 | −69 % by 2040 (24.3 → 7.6 Mt 2050) | state mandates target deep decarb | direction IN CORRIDOR (wrong mechanism, as CAISO) |

**D12 — the model grows the wrong peak.** Ours: one summer-anchored growth
scalar. Theirs: CELT 2026's defining feature is the winter flip (+2.6 %/yr
winter vs +0.6 %/yr summer; heating electrification adds 5.5 GW to the
2035/36 winter peak). A single-season peak basis misses the constraint that
will actually bind New England adequacy in the 2030s — this is a *load-shape*
gap (audit D3's "no electrification shape decomposition", documented
limitation), separate from the capacity-price story, and it makes even a
fixed-price NEISO adequacy read structurally summer-biased.

**D13 — NEISO is the cleanest exhibit of the BLK-9 overshoot.** Ours: RM
climbs monotonically to 67.5 % with zero retirements and *growing* gas
capacity, while the real FCM has spent most of the last decade clearing at
surplus-signalling prices near or below $3/kW-mo. Theirs: ISO-NE plans
resources against the ICR, and its own monitor shows entry economics that
don't support new gas. Every NEISO capacity-side row past ~2030 is the
fixed-price artifact P-3B measured directly (T2.1/T2.2b/T2.4); explained, and
quotable only as a diagnostic of the mechanism, never as a forecast.

### 1.5 Corridor bottom line

Of the four scored ISOs: **near-term load and near-term adequacy direction
are in corridor everywhere scored** (D1/D7 — with the compensating-omission
caveats noted); **every capacity-evolution quantity past ~2030 diverges from
every external benchmark, and all but one divergence is explained by the
already-registered blockers** (BLK-7/8/9, #1532, #2064, DC-block-off — see
the companion verdict §5). The one genuinely **unexplained** divergence is
**D5 (ERCOT 14 GW EGS + 9 GW iron-air)** — new root-cause item, no existing
gap-register row. The corridor exercise also surfaced one internal
consistency flag (D6: golden vs per-plant 2040 LW price 3× apart) and one
input-shape gap promoted in priority by external evidence (D12: NEISO winter
peak).

---

## 2. T3.2 — screen revenue vs published monitor net revenue

Extends the ERCOT-only capacity-economics §5 audit to every ISO with a
published SOM. Two honesty notes: **(a)** the model column for the
capacity-market ISOs' *total* screen revenue is **not measurable this
session** — per-class screen-revenue logs are produced at solve time and the
P-3A cache is gone; only ERCOT has a committed screen-revenue artifact
(stage-2 grid JSON). What *is* exact without a solve is the **capacity leg**
(flat `net_cone × (1−EFORd)`), tabulated below. **(b)** Monitor figures are
published numbers with vintages cited; MISO and NYISO publish new-unit net
revenue **as charts only** (no numeric tables) — prose verdicts are quoted
instead of guessed values.

### 2.1 ERCOT (energy-only): model screens vs Potomac SOM

| Quantity | 2023 | 2024 | 2025 | Source |
|---|--:|--:|--:|---|
| SOM new-CT net revenue $/kW-yr | 224–257 | **68** | 52.6 (Houston ~59, West ~177) | Potomac SOM 2023 Fig 45 p.76; 2024 Fig 56 p.81; 2025 pp.97–103 |
| SOM new-CC net revenue $/kW-yr | 228–272 | 89 | 83.0 | same |
| Peaker Net Margin $/kW-yr | ~264 | ~99 | ~79 | SOM 2023 Fig 49; ERCOT MIS (Jan 2025); SOM 2025 p.97 |
| CONE comparator $/kW-yr | 80–130 | 102–106 | PUCT planning CONE **140** (Jul 2024); legacy 105 kept for the PNM threshold | SOM vintages above |
| **Model** screen CT revenue (attainable pro-forma, first screen year, stage-2 basis) | — | — | — | **17.2 $/kW-yr** (hindcast 2021 screen; `fom-scarcity-grid-2026-07-05-stage2.json`) |
| **Model** keeper-vintage CT net (pre-AS-co-opt, 2026-06 assessment) | 12.3 | 1.7 | 0.8 | superseded vintage; kept for trend |

**Read.** The screens now capture on the order of **~25 % of the SOM CT
anchor in a mild year** (17.2 vs ~68) and far less against 2023's ECRS-driven
~$240 — up from ~2–6 % at the 2026-06 assessment, still nowhere near
entry/exit-grade. Note the monitors themselves moved: 2025 CT net revenue
(52.6) is *below* the new $140 planning CONE — the real market is also
signalling "no entry", so the model's *direction* in mild years is right
while its level remains ~3–4× short. Gap owner: G-20/G-22 (AS co-opt +
scarcity level); `as_revenue_enabled` still default off. Also note the SOM
2024 CT/CC row prints a $/MWh unit where its own figure axis is $/kW-yr — a
known typo in the source, values used as $/kW-yr.

### 2.2 Capacity-market ISOs: the flat capacity leg vs what the market actually paid

Model capacity leg (CT basis, `net_cone × (1−EFORd_ct)`, constant every
forecast year) against the published capacity price actually cleared:

| ISO | Model flat CT capacity leg $/kW-yr | Actual cleared capacity $/kW-yr | Model ÷ actual | Source (actual) |
|---|--:|---|---|---|
| PJM | 94.0 | 2023: ~15.0 ($41/MW-day) · 2024: ~11.3 ($31/MW-day) · 2025/26: ~62 ($170/MW-day most zones) | **6.3× / 8.3× / 1.5×** | Monitoring Analytics 2025 SOM Vol 2 §7 Table 7-5 |
| MISO | 75.2 | PY23/24: ~3.4 ($9.25/MW-day avg) · PY24/25: ~7.3 (~$20/MW-day) · PY25/26: ~78 (~$215/MW-day, new RBDC) | **22× / 10× / 1.0×** | Potomac MISO SOM 2024 pp.79–84 (on-disk PDF) |
| NYISO | 103.4 | 2025/26 spot: NYC 132, ROS 51 (74 % of Net CONE) | **0.8× NYC / 2.0× ROS** | Potomac NYISO SOM 2025 pp.5, 91 (on-disk PDF) |
| NEISO | 89.3 | 2024 CCP15: ~31 ($2.61/kW-mo) | **2.9×** | ISO-NE IMM 2024/2025 AMR pp.51–62 |
| CAISO | 84.6 | CPM soft cap 88.1; CPUC 2023 RA report system ~174 | 0.5–1.0× (bilateral, no auction) | DMM 2024 annual pp.103–110; registry citation |

**Read.** The fixed capacity leg is not a conservative stub — it is a
**volatility eraser with a long-side bias**: it overpaid PJM/MISO capacity
6–22× in the surplus years 2023–24 and *underpays* the shortage prints
(PJM 2025/26 98.5 $/kW-yr cleared vs 94 paid; NYISO NYC 132 vs 103). Combined
with the ratio finding (`capacity-revenue-fom-ratio-2026-07-13.md`: the leg
alone covers every fossil class's going-forward cost ≥1.26×), this is the
quantitative form of the T2.4a/T2.4c failures. The CR-1 curve would have
tracked the 2023–25 swing (P-2A validated the shape and the PJM spike
direction) — it is the position/basis inputs, not the instrument, that keep
it off (P-2A §7).

### 2.3 Monitor net revenue vs cost — the external corridor the screens must eventually match

For the record (and for the next re-run of this check after a solve persists
per-class screen revenue), the published totals the screens should reproduce:

| ISO | Class | Net revenue (latest yrs) | Monitor cost comparator | Split note | Source |
|---|---|---|---|---|---|
| PJM | new CT | 60.3 / 73.0 / **89.4** $/kW-yr energy (2023/24/25) + capacity above | 20-yr levelized 163–193 $/kW-yr; 2025 recovery 77 %, covers cost in 5 zones | energy vs capacity explicit; capacity dominant only in 2025 | MA 2025 SOM §7 Tables 7-6/7-8/7-9 |
| PJM | new CC | 90.1 / 98.1 / **117.7** energy | 183–223; 2025 recovery 80 % | same | Tables 7-10/7-11 |
| MISO | CT/CC | charts only; "well short of those needed to support investment" (2023); "decreased … in most zones" (2024) | Zone-5 CONE ~131.7 $/kW-yr | PRA leg tiny pre-2025 (~3 %), step-change PY25/26 | MISO SOM 2023 pp.74–75; 2024 pp.80–81 (on-disk) |
| NYISO | new CT (NYC) | charts only; **below CONE every year 2022–2025, all locations** | gross CONE per demand-curve reset; NYC 5-yr avg spot 107.6 $/kW-yr "well below Net CONE" | capacity/E&AS/subsidy stacked in figs | NYISO SOM 2024 pp.11–13; 2025 pp.26–28 (on-disk) |
| NYISO | battery 2h/4h | below CONE even with incentives; Index Storage Credit must supply 32–40 % of 4-h revenue | — | state+federal subsidy share 47–58 % | SOM 2025 pp.27–28 |
| NEISO | CC | 2024 ~78 → 2025 **~202 $/kW-yr total** (capacity+E&AS > gross CONE, 2nd time in 5 yrs) | gross CONE CC ~175, CT ~127 $/kW-yr (FCA18) | explicit energy/AS/dual-fuel/capacity stack | ISO-NE AMR 2024 pp.61–63; 2025 pp.49–52 |
| NEISO | CT | 2024 ~73 → 2025 ~100 | same | same | same |
| CAISO | CT / CC | 2024 energy-only: CT 10–16, CC 14–19 $/kW-yr | annualized fixed ~140–172; GFC 32–42; AS adds ≤2.7 | RA-contract revenue not estimated by DMM | DMM 2024 annual pp.103–112 |
| ERCOT | — | §2.1 above | — | energy+AS only | — |

Coverage gaps, stated: MISO/NYISO numeric values unpublished (charts);
MISO 2025 SOM and CAISO DMM 2025 annual not yet released as of 2026-07-13;
no ERCOT/PJM battery net-revenue benchmark published. **Standing-check
protocol:** the next P-3A-class run should persist per-class screen revenue
(the stage-2 diagnostic log already exists for ERCOT; extend to all ISOs) so
this table gains its model column without a dedicated solve.

---

## 3. Actions routed (no fixes attempted here)

1. **New root-cause item (unexplained divergence D5):** ERCOT entry-mix
   inversion — EGS 14 GW at its queue cap + iron-air 9 GW while solar entry
   is zero. Open a gap-register row next to BLK-8; suspects: Wright's-law
   cost path on hardcoded deployment (audit D4) and the uncited 2 GW/yr EGS
   cap.
2. **Internal consistency flag (D6):** golden-fixture vs per-plant P-3A 2040
   ERCOT LW price differ 3× ($70 vs $216) on nominally the same reference
   scenario — reconcile configs or document the fleet-representation
   sensitivity before quoting either.
3. **Load-shape gap promoted (D12):** NEISO winter-peak flip (CELT 2026) —
   the summer-anchored growth scalar misses the binding 2030s constraint;
   ties to audit D3's documented electrification-shape limitation.
4. **T3.2 standing check:** persist per-class screen-revenue logs in every
   full-horizon/hindcast run so §2.3's model column populates without
   bespoke solves.
5. Everything else diverges for **already-registered** causes: BLK-7/8/9,
   #1532 (+D10 base-year CAISO), #2064, `datacenter_load_path="off"` — see
   the companion verdict's blocker register.

## 4. What this session did / did not do

- **Did:** compiled the corridor from committed P-3A artifacts + the golden
  fixture against AEO2025 / NREL SS2024 / ERCOT CDR Dec-2025 / PJM 2026
  forecast + 4R / CPUC PSP+TPP / CAISO 2026 summer assessment / ISO-NE CELT
  2026 / NYISO Gold Book 2026 (all cited with vintages); refreshed the
  SOM/PNM net-revenue table for all six monitors (ERCOT/PJM numeric;
  MISO/NYISO chart-verdicts from the on-disk PDFs; ISO-NE/CAISO numeric);
  computed the flat-capacity-leg vs cleared-price comparison; rewrote
  `docs/forecasting-entry-exit-assessment.md` (companion deliverable).
- **Did not:** solve any LP; touch any parameter, threshold, or curve;
  register anything on any dashboard; solve/score 2022 or H1-2026 (external
  delivery-year data ≤2025/26 plus already-published monitor reports only —
  H1-2026-delivery auction rows were not used in any verdict).

*Produced 2026-07-13 (P-3C). External sources accessed 2026-07-13; primary
URLs inline. Model anchors: `docs/handoffs/full-horizon-findings-2026-07-12.md`
§5/§7; `tests/golden/ercot_2026_2040.json`; `docs/handoffs/equilibrium-battery-2026-07-12.md`;
`docs/handoffs/capacity-revenue-fom-ratio-2026-07-13.md`;
`fom-scarcity-grid-2026-07-05-stage2.json`; hindcast reports 2026-07-12.*
