# FINDING miso-211 — THE RDT SOUTH→NORTH BINDING STATE: the model's corridor carries ~360 MW north where MISO's ran at the limit in half the shoulder hours, and the reason is not the limit — the model's South generates 3.4 GW less than the real South in exactly those hours (3.3 GW of it gas) — so the object is REAL and LARGE (the missing Midwest−South separation is worth 0.67 / 0.47 of the 2025 shoulder / tail gaps as a ceiling) but the charter's lever, a measured RDT LIMIT, cannot reach it: REFUSED, NO SOLVE (2026-09-04)

**Keeper unchanged: `2026-09-04-miso-210-clock`.** NO LP, NO KEEPER MOVE, NO
MECHANISM ARMED, NO FIELD, NO RUN REGISTERED. PREREG
`PREREG-miso211-rdt-binding-state-2026-09-04.md` pushed blind at `5320e4dc`
before any adjudicating statistic; record `_miso211_rdt_binding_state.json`;
instruments `scripts/probes/_miso211_rdt_binding_state.py` (first pass),
`_miso211_rdt_followup.py` and `_miso211_rdt_south_gas.py` (two disclosed
post-hoc blocks, §5). Rule 22: 2023–2025 only.

---

## 0. The verdict in one paragraph

The pre-registered decision rules pointed two ways and the finding follows
both. **R-3 CLEARS its line** (the 2025 separation ceiling is 0.675 of the
shoulder gap and 0.472 of the tail gap on the whole-separation construction;
0.305 / 0.119 on the RDT-attributable, shadow-bounded one) — the object is
licensed. **R-2 refuses the R-4 lever**: R-1a and R-2b both hold, so the LP
does not bind the corridor because its South has nothing to send, not because
the limit is set wrong; a measured hourly RDT limit caps a flow the LP does
not produce (357 MW mean S→N in the 177 real binding shoulder hours of 2025,
at the 2,300 MW free tier in 2.8 % of them). The cell is minted **R** as
pre-registered for that branch; the reach numbers are recorded because they
license the OBJECT, whose admissible lever is on the South supply side (§4).

## 1. Footing (N-1)

Populations and gaps reproduce miso-207/208 on the miso-210 keeper: 2023
shoulder −10.958 / tail −151.537 and 2024 −18.652 / −290.021 to the decimal;
2025 −43.703 / −636.853 vs miso-207's −43.727 / −636.862 — the 0.024 / 0.009
difference is the miso-210 clock repair's own price move (Jul 28 h11 and the
2025 edges), i.e. the keeper changed, not the instrument. The real S→N
binding shares reproduce miso-208 EXACTLY (0.1852 / 0.5413 / 0.5043 shoulder;
0.6667 / 0.3333 / 0.6667 tail; 0.0936 / 0.2629 / 0.3246 other daytime). The
South balance identity closes to **0.004 MW** on the full dispatch (§5 item 1).

## 2. R-1 — the LP's corridor in the hours MISO's RDT bound South→North

| year / population | real S→N hours (any / majority) | LP S→N flow mean / p90 (MW) | LP at 2,300 free tier | LP flowing N→S | LP N→S mean (MW) | model Indiana−South spread | real mean \|shadow\| |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2025 shoulder (351 h) | **177 / 7** | **357 / 1,197** | **2.8 %** | **59.9 %** | 851 | −$0.16 | $30.5 |
| 2025 tail (15 h) | 10 / 7 | 556 / 960 | **0 %** | 20 % | 356 | −$0.01 | $120.2 |
| 2024 shoulder | 190 / 31 | 424 / 1,783 | 6.3 % | 62.6 % | 839 | −$0.00 | $23.8 |
| 2024 tail | 5 / 3 | 322 / 658 | 0 % | 40 % | 530 | $0.00 | $56.3 |
| 2023 shoulder | 65 / 2 | 846 / 2,300 | 12.3 % | 32.3 % | 321 | +$0.14 | $76.8 |
| 2023 tail | 10 / 0 | 1,027 / 1,890 | 10 % | 10 % | 13 | +$0.21 | $295.9 |

Annual census, 2025: the real RDT bound S→N in **1,395 h** and N→S in 43 h;
the LP reached its S→N free tier in **58 h** (35 of them real S→N hours) and
its N→S free tier in **4,668 h** (219 of them real S→N hours). **R-1a RIGHT,
R-1b RIGHT, R-1c RIGHT, R-1d reproduction exact.** The LP runs the wheel the
wrong way in 60 % of the hours the real one bound northward — miso-186's
scarce-set signature (9/47 → 7/47) is the shoulder's everyday state.

## 3. R-2 — WHY: (b), the South has no surplus; (a) discriminated out; (c) closed

**R-2c (routing around): CLOSED.** demand − generation − storage − slack = Σ
into-South links (N→S − S→N + external_South) to **0.004 MW** max residual
in every year on the full dispatch; `MISO_external_South>MISO-South` is the
only non-RDT term. No bypass exists.

**R-2b (South surplus), the 2025 shoulder hours where the real RDT bound
S→N (177 h), GW mean, corrected basis (§5 item 1):**

| | measured (rf_al / sr_gfm) | model | model − measured |
|---|---:|---:|---:|
| South boundary net intake (+ = imports) | **−2.857** | **+0.050** | **+2.907** |
| South load | 27.03 | 26.57 | −0.46 |
| South generation, total | 29.89 | 26.50 | **−3.39** |
| — gas | 18.90 | 15.56 | **−3.33** |
| — solar | 1.95 | 1.70 | −0.26 |
| — coal | 3.06 | 3.23 | +0.17 |
| — nuclear / hydro / wind / other | 5.18 / 0.42 / 0.04 / 0.34 | 5.13 / 0.50 / 0.06 / 0.33 | −0.05 / +0.07 / +0.02 / −0.01 |

The real South exported 2.9 GW while the model's South sat at balance. The
model's South LOAD is 0.46 GW BELOW measured (which should make it export
MORE), so the entire gap and then some is GENERATION: **−3.39 GW, of which
gas is −3.33**. The same signs and sizes in every year and both populations
(2024 shoulder gap 2.16 GW, gas −3.23; 2023 1.19, gas −2.66; 2025 tail 2.66,
gas −2.66): a chronic South-gas shortfall, not a 2025 or a tail phenomenon.
**R-2b RIGHT** (measured ≤ −1.5, model ≥ −0.5, gap ≥ 1.0; generation term
≥ 70 % — it is 117 %; gas below measured).

**R-2a (limit level): NOT the operative cause.** With the LP sending 357 MW
north (p90 1,197) against a 2,300 MW free tier, no lower measured limit could
bind — the corridor is slack by 1,900 MW on average in the very hours the
real one was at its limit. The published handle on the real limit's regime
(the mean |shadow| $30 in the binding shoulder hours, mostly step-1 $40-class
with step-2 excursions) is reported, not used.

**The South gas gap: PRICED OUT, not unavailable (post-hoc block 2, `_miso211_rdt_south_gas.py`, disclosed).** In the 177 real S→N binding shoulder hours of 2025 the model's South gas fleet has **20.27 GW available** (availability-derated), dispatches **15.56 GW** against **18.90 GW measured** (sr_gfm), and leaves **4.71 GW idle** — of which **3.52 GW sits within $20 of the model's own South price** and 2.25 GW within $10. Measured output exceeds the model's available South gas capability in 46 of the 177 hours, by 0.235 GW mean over all of them — an availability residual of ~7 % of the gap, the miso-186 class, secondary. The marginal MW the model would need to reach the measured gas level is offered at **$65 (p50) / $117 (mean)** against a model South price of **$48.3** — while the ACTUAL South hubs cleared at **$41.6** with 18.9 GW of gas running. So the real South ran 3.3 GW of gas at $42 that the model offers at $58–65 and up: **the model's South gas is over-costed relative to the market that dispatched it**, by ~$7 at the margin already (model South price above actual) and by $17+ for the units needed. Same picture every year (2024: 20.15 available / 15.83 run / 19.06 measured, idle-within-$20 3.64 GW, marginal $53 vs South price $35, actual $27; 2023: 20.79 / 16.90 / 19.56, 3.95 GW, $49 vs $37, actual $32) and in the tail (2025: 20.36 / 17.68 / 20.34, 5/10 hours capability-short by 0.43 GW — the tail has a larger availability share).

**What this names, and does not build.** The successor is the **South gas delivered-cost basis** — the delivered gas price and heat-rate basis the model assigns MISO-South gas plants (the `miso_zonal_gas_basis` South leg, measured CC/CT heat rates, the CHP rows) checked against the South's own hub prices (Henry Hub / TETCO ELA / Columbia Gulf) and CAMPD heat input in these hours — a rule-14 accurate-input question, not a fitted offer level (the offer family's level/spread cells R/I stay closed: they were system-wide dispersion levers; this is a South-localized COST basis with a measured source). Its phase 0 must show, before any solve: (i) the model's South gas mc in the binding hours decomposes into fuel × heat rate × margin with each leg beside its measured counterpart; (ii) the mc reduction needed (~$17 at the 3.3 GW margin) is explained by a measured input, or is not; (iii) leave-one-year-out on 2023/2024 (same signs there). A ~3 GW South export the LP would then send north at the 2,300 MW free tier would bind the corridor exactly where MISO's did — at which point, and only then, the measured-limit question re-opens.


## 4. R-3 — static reach on both populations

| construction | 2025 shoulder | 2025 tail | 2024 shoulder | 2024 tail | 2023 shoulder | 2023 tail |
|---|---:|---:|---:|---:|---:|---:|
| **R-3a strand** (miso-208 verbatim, re-measured) | **0.048** | 0.007 | 0.088 | 0.003 | 0.059 | 0.015 |
| **R-3b separation ceiling, whole** (Indiana − South hubs, measured, in binding hours) | **0.675** | **0.472** | 0.830 | 0.115 | 0.451 | 0.716 |
| **R-3b RDT-attributable** (bounded by the PBC shadow) | **0.305** | 0.119 | 0.496 | 0.065 | 0.380 | 0.704 |
| measured separation in binding hours ($) | 58.3 | 451.1 | 28.6 | 100.1 | 26.5 | 162.9 |
| model spread in binding hours ($) | −0.16 | −0.01 | −0.00 | 0.00 | +0.14 | +0.21 |

R-3a reproduces miso-208 exactly (0.048 / 0.007) — stranding the South
cushion is worth nothing, because the cushion is not the object. **R-3b is
the object**: in the 2025 shoulder hours MISO's RDT bound northward, the
real market separated Indiana from the South hubs by **$58** and the model
by **−$0.16**; the missing separation, applied to the model's Indiana price
with its South price held fixed, is worth **0.675 of the shoulder gap and
0.472 of the tail gap** — the first candidate in this lane to clear the
both-populations line since miso-178. The RDT's OWN price (the shadow-bounded
variant) carries 0.305 / 0.119: the corridor constraint is the largest single
piece of the separation in the shoulder, and the rest ($28 of the $58) is
the separation the RDT does not price by itself (RPE-only binding, internal
M2M flowgates, losses).

**Prediction scored: WRONG in the interesting direction.** The PREREG
predicted the measured separation at $8–20 and the shoulder share at
0.10–0.25 (NOT cleared, 0.65). It is $58 and 0.675. The Midwest−South
separation in the shoulder is not a minor price object; it is the
second-largest identified component of the shoulder gap after the level
itself, and the model carries none of it.

**Why the R-4 lever is nonetheless refused.** The pre-registered R-2 rule:
if R-1a and R-2b hold, "the LP does not bind the corridor because its South
has no surplus at the Midwest price, and a measured RDT limit would be the
wrong lever (it caps a flow the LP does not send)". Both hold. A lower limit
on a corridor carrying 357 MW changes nothing; a HIGHER limit would let the
LP move more only if the South had more to send, which is the (b) object.
**`miso_rdt_measured_limit` is minted R** at MISO with these numbers — the
lever, not the object, is refused.

## 5. Reported against interest

1. **Instrument correction, disclosed (the miso-186 §7 pattern):** the first
   pass read the model's South generation from `hourly/unit_hourly`, which
   carries only the thermal/hydro/nuclear UNITS — the LP's zonal wind/solar
   variables and the biomass/OTHER/oil bins are absent from it — so the
   first-pass by-fuel table read model South solar as **0.0 GW** against
   1.95 measured and the R-2c identity left a 1.1–3.8 GW residual. Both
   blocks were re-computed from the zone-resolved `dispatch/<year>_P1.parquet`
   (`post_hoc` in the record): the residual closes to 0.004 MW, the solar row
   becomes −0.26 GW, and the gas row (−3.33) is unchanged because gas units
   ARE in `unit_hourly`. No threshold moved; the first-pass numbers stay in
   the record beside the corrected ones.
2. **The separation ceiling is a CEILING**, not a mechanism's reach: it holds
   the model's South price fixed and credits the whole measured separation to
   Indiana. A model that actually exported 2.9 GW north would lower its South
   price as it raised the Midwest's; the Indiana-side share of the
   separation is unknown from this measurement. The shadow-bounded variant
   (0.305 / 0.119) is the conservative reading, and on it the tail is NOT
   cleared.
3. **The tail does not clear on the RDT's own price** (0.119): the 2025 tail
   separation ($451) is far above the RDT shadow ($120) — the tail is the
   system-energy / RT-dynamics regime miso-203/204/207 named, and this object
   does not change that.
4. **R-3a's exact reproduction (0.048 / 0.007)** is the honest measure of the
   charter's ORIGINAL framing ("strand the South cushion"): that framing was
   the wrong object, and this session retires it.
5. **The N-1 gap footing missed its ±0.01 line in 2025 by 0.024** — the keeper
   changed between miso-207 and now (miso-210), not the instrument; the
   binding shares reproduce exactly.
6. Nothing here is a residual chase: every quantity is a measured binding
   state, a measured regional balance, or a topology identity; C3a was never
   read as a target.

## 6. My prior, scored against interest

| # | prediction | conf. | measured | verdict |
|---|---|---:|---|---|
| R-1a | LP S→N at free tier < 10 % of real binding shoulder hours; mean flow < 1,200 MW | 0.75 / 0.6 | 2.8 %; 357 MW | RIGHT |
| R-1b | LP runs N→S in ≥ 30 % of them | 0.6 | 59.9 % | RIGHT |
| R-1c | tail: LP S→N binds in 0 real-binding tail hours | 0.8 | 0 / 10 | RIGHT |
| R-1d | shares reproduce miso-208 ± 2 pp | — | exact | RIGHT |
| R-2a | limit level not operative | 0.75 | corridor slack by ~1.9 GW | RIGHT |
| R-2b | measured ≤ −1.5, model ≥ −0.5, gap ≥ 1.0 GW; generation ≥ 70 %; gas below measured | 0.65 / 0.6 / 0.65 | −2.86 / +0.05 / 2.91; 117 %; gas −3.33 | RIGHT |
| R-2c | identity holds, no bypass | 0.95 | 0.004 MW (after the basis correction) | RIGHT |
| R-3a | 0.03–0.07 shoulder / ≤ 0.02 tail | 0.7 | 0.048 / 0.007 | RIGHT |
| R-3b | separation $8–20; share 0.10–0.25 shoulder (NOT cleared); ≤ 0.05 tail | 0.6 / 0.85 | **$58; 0.675 shoulder, 0.472 tail (whole); 0.305 / 0.119 (RDT-bounded)** | **WRONG — the result** |
| R-3 verdict | NOT CLEARED | 0.65 | CLEARED (whole), shoulder-only (bounded) | **WRONG** |
| R-4 | not reached; row minted R | 0.75 | R-4 refused by the R-2 rule; row minted R | RIGHT on the outcome, by the other branch |

Read honestly: every corridor-state and supply-side prediction was right;
the one prediction about PRICE — how much Midwest−South separation the real
market carried in those hours — was wrong by 3–4×, and it is the result.
Eleventh consecutive MISO session whose most useful output came from the part
of the prior that was wrong.

## 7. Governance

Rule 15: zero-solve, nothing registered. Rule 28(a): no R/I/G cell
re-tested; `measured_interface_limits` R, `m2m_seam_entitlement_cap` G,
`miso_south_firm_export_block` G, `miso_south_export_ladder_rt_tail` R
untouched. Rule 28(b)/(c): `rdt_tcdc` (K) carries appended evidence; base
row `miso_rdt_measured_limit` added (field-less adjudicated mechanism-in-kind,
the miso-182 precedent) with MISO cell R and `.` in the five other shards;
§5.4 stamp. Rule 25: only MISO's cell carries a verdict. Rule 22: 2023–2025.
Rule 13: `rf_al` / `sr_gfm` / PBC read as diagnostics, never LP inputs. Rule
27: blob-verify after push.

**Records:** this file; `PREREG-miso211-rdt-binding-state-2026-09-04.md` @
`5320e4dc`; `_miso211_rdt_binding_state.json` (first pass + `post_hoc`);
`scripts/probes/_miso211_rdt_binding_state.py`, `_miso211_rdt_followup.py`,
`_miso211_rdt_south_gas.py`.

Next shorthand: **miso-212**.
