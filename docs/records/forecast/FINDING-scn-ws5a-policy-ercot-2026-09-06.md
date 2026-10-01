# FINDING — SCN-WS5A-POLICY-ERCOT: the eleven Stage A-POLICY legs at THE PIN, scored against the committed REF

**Lane** SCN-WS5A-POLICY-ERCOT (resumed) · **Model** Fable (`claude-fable-5-1`; the eleven solves ran in
four owner-launched Opus sub-lanes G1–G4, ADDENDUM A(d)) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-ercot-r2-mmt8w7` · **PRECOMMIT** `docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md`
(+ ADDENDUM A) · **Protocol the sub-lanes executed** `docs/handoffs/SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md`
· **Campaign** `scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` · **Charter** v6-RESUME (ledger §5.3).

Every number below is read from a committed artifact: the eleven legs' `full_horizon_summary.json` /
`run_config.json` / `duals.json`, the four group reports under `results/scn-campaign-policy-2026-09-06/ERCOT/report/G*/`
(absolute columns), and the committed REF / LOAD-HI absolutes in
`results/scn-campaign-load-2026-09-06/ERCOT/report/*` (`*_bau` columns) and their summaries. No number was produced
by a solve in this session.

---

## 0. Bottom line

1. **All eleven legs solved clean at THE PIN** (`bdfb3095`): every `cache_key` equals its §2 value, every `git.sha` is the
   pin, `git.dirty` false, 5/5 years, `error` null, FAIL set exactly `{I3, I12}` in every arm (REF's own), every FAIL
   declared, invariant audit **EXIT 0** on `main` (124 sidecars / 1,736 records / 129 declared FAILs). 55 solve-years,
   **86.6 min of LP summed across four containers**, peak RSS 4.20 GB (§6).
2. **THE CONTROL IS VALID FOR 2026–2027 AND INVALID FROM 2028 — and the reason is a finding, not an accident.**
   P-1 is an EXACT HIT: `CARB-MID` 2027 reproduces WS-1b's arm to every quoted digit (255.0452 Mt / $984.247 /
   4,621,769.86 MWh / 0.3519), and every carbon arm's 2026 is bit-identical to REF (max |Δgeneration| = 0.000000 MWh).
   But **every policy leg converts gas-CC to CCS from 2028** — 2.93–3.00 GW per year, the 3 GW/yr/ISO retrofit cap
   binding, at a level that does not depend on the policy (CARB-LO $4/t: 2,932 MW; CARB-HI $15/t: 2,984 MW; CES-P10:
   2,986 MW; VOL-HI, whose row cannot credit CCS and carries carbon $0: 2,764 MW in 2029). The committed REF (solved at
   `1cc45bb2`, before capx D65-B) converts **none**. So **capx D65-B (the capture VOM adder 8.0 → 2.95) is LIVE on
   ERCOT at the pin**: PRECOMMIT §5.1's argument that "a change to the capture VOM adder cannot move a fleet that
   converts nothing" was wrong in exactly the way rule 29(b) warns about — it classified a screen input as inert
   because the pre-fix output was zero. **Prediction P-7 MISSES at full magnitude and its pre-registered consequence
   applies: the D77/D65-B seam is live for ERCOT, form 4 fails from 2028, and a control solve is EARNED.** Routed as
   the first item of §7 — ERCOT's REF / LOAD-HI / LOAD-HI-ORGANIC are the fourteenth–sixteenth contaminated legs of
   ruling S8's set, excluded on a premise the pin falsifies.
3. **What is campaign-grade now:** the 2026–2027 deltas on every axis; the duals and escape regimes in every year
   (G4, G7 exact); the dispatch footprints; and every **leg-vs-leg comparison at 2028–2030**, where both sides sit
   on the same pin (§2.6). **What is NOT:** any 2028–2030 delta vs REF (contaminated by the conversion REF was never
   given the chance to make), and — as G2 declared before any solve — every ERCOT price level and captured price in
   every year (REF sheds 0.38 → 127.2 TWh at $91 → $4,438/MWh).
4. **A structural defect in the clean rows, found by the gate that was written to celebrate it.** G8 ("curtailment
   before thermal") PASSES in letter in every row case: curtailment goes to exactly 0.000 TWh the year the row
   binds, with thermal, storage and unserved unchanged. But the un-curtailed 4.33–4.92 TWh appears in `total_gen_mwh`
   and in **I3's dump line** ("dump 2.15 % / 2.41 % of renewable pot." — a line REF's I3 does not carry) — i.e. the LP
   dispatches the curtailed wind/solar into the **Dump column at ε cost** and the row credits it. A curtailed MWh
   earns no certificate in any real REC market; the rows credit the generator column, not delivered energy. This
   satisfies the federal CES target and the voluntary row with ~4.9 TWh of phantom clean energy per year before any
   escape is paid. Routed (§7 item 2) to the row owners; it changes no level here but every credited/escape volume in
   §2.4–§2.5 is overstated by the dumped MWh.
5. **The CES premium ladder does NOT saturate at THE PIN** (P-8 MISS): CES-P30 commissions 1,000 MW more solar in
   2029 and 5,000 MW of wind in 2030 that CES-P20 does not, 2030 clean share 0.4058 vs 0.3992, CO2 299.59 vs 303.08
   Mt. WS-2b's `iso_budget_exhausted` saturation was a property of its POC base, not of the mechanism.
6. **The first policy-side deployment reading, and its adequacy cost.** `CES-T80`'s $50 ACP dual makes solar entry
   beat gas-CC in the 2029 screen: it commissions **3,500 MW more solar and 3,000 MW less gas-CC** than REF — and
   sheds **+16.8 TWh more** in 2029 and +16.4 TWh in 2030 (reserve margin −0.225 vs −0.206). On an energy-only ISO in
   shortage, a clean target that prices only attributes buys clean energy and adequacy loss in the same screen.
   Carbon and premium arms leave the entry mix almost untouched (+500 MW solar in 2029 under carbon). ERCOT converts
   CCS in every arm from 2028 — but that row is the pin's, not the policy's (item 2), so **the retrofit reading is a
   null pending the control**.
7. Two cases stay KILLED at zero LP exactly as the PRECOMMIT proved (`VOL-MID` slack all five years; `CAP-STATE-TIGHT`
   resolves to no program); nothing here reopens them.

---

## 1. Phase 0 — already done; cited, not re-derived

PRECOMMIT §2–§5 and ADDENDUM A: fourteen keys reproduced at the pin (14/14), P3 re-asserted from the matrix YAML at
the pin, G-DRIFT `bdfb3095..992760ec` all INERT for an ERCOT forecast leg (11 non-merge solve-path commits), and the
two kills — **`VOL-MID`** (V = 80.3–198.5 TWh < eligible generation 197.3–234.9 TWh in every year; REF's optimum is
feasible with ESC = 0 at the same objective ⇒ dual 0, byte-identical) and **`CAP-STATE-TIGHT`**
(`CAP_AND_TRADE_PROGRAMS.get("ERCOT")` is `None`; `resolve_carbon_program` returns before `mass_cap_enabled` is
read ⇒ no LP input differs). The slot statement (S14; the four parallel sub-lanes are the owner sequencing it) is
ADDENDUM A(d). **One phase-0 conclusion is now falsified by measurement and is this FINDING's headline (§0 item 2):
§5.1's D65-B-inert-for-ERCOT classification.** Everything else in phase 0 stands.

## 1.1 Solve integrity (RESOLVE PRECOMMIT §4.2 form), all eleven

| case | key (= §2) | `git.sha` | dirty | years | FAIL | WARN | declared |
|---|---|---|---|---|---|---|---|
| CARB-LO | `c1e09985c3e4fa56` | pin | false | 5 | I3 I12 | I13 I14 | yes |
| CARB-MID | `ab8d79646b49abbd` | pin | false | 5 | I3 I12 | I13 I14 | yes |
| CARB-HI | `73dadcb65d74acce` | pin | false | 5 | I3 I12 | I13 I14 | yes |
| CES-P10 | `17e0b252e13a484a` | pin | false | 5 | I3 I12 | I13 I14 | yes |
| CES-P20 | `5a89c34af859160c` | pin | false | 5 | I3 I12 | I14 | yes |
| CES-P30 | `8588e1b0d055e772` | pin | false | 5 | I3 I12 | I14 | yes |
| CES-T80 | `e6638b058ce4d5fb` | pin | false | 5 | I3 I12 | I14 | yes |
| CARB-MID+LOAD-HI | `b99311bb1f3032e0` | pin | false | 5 | I3 I12 | I14 | yes |
| VOL-HI | `76ef5a80df6a9277` | pin | false | 5 | I3 I12 | I13 I14 | yes |
| CES-P20+VOL-HI | `5b7774c817ee425b` | pin | false | 5 | I3 I12 | I14 | yes |
| ALL-CLEAN | `619cfffde44422b2` | pin | false | 5 | I3 I12 | I14 | yes |

Run ids `ercot-2026-2030-scn-campaign-policy-2026-09-06-<case>` (`+` → `-plus-`), sidecars under
`frontend/data/hindcast/`. REF's own set is FAIL {I3, I12} / WARN {I13, I14}; an arm losing the I13 WARN is not a flip
(G5).

---

## 2. Per-case deltas vs REF — with the leakage line beside every CO2 number

**Leakage line, once for every table:** `import_co2_mt_reported` = **0.0 in every arm and every year BY
CONSTRUCTION** — ERCOT has no import node in the six-ISO topology, so no leakage can be booked, and **every ERCOT CO2
delta below is an UPPER BOUND on the in-ISO abatement** (a real ERCOT is weakly interconnected, but the model cannot
price the DC ties). Same statement WS-1b-r2 made for its ERCOT pair.

**Control validity, once for every table:** `valid` = both sides on comparable code for that year. **2026–2027:
VALID** (D65-B's seam is inert before `ccs_retrofit_available_year` 2028; P-1's exact identity proves it).
**2028–2030: CONTAMINATED** — REF (pre-D65-B) converts nothing; every arm converts at the cap. A 2028–2030 delta vs
REF mixes the policy with the pin's own retrofit screen and is reported at magnitude, never quoted as the policy's.

**Price disclosure, once:** `lw_price` is shown arm / REF only so the reader sees the regime; no ERCOT price delta is
campaign-grade in any year (G2).

### 2.1 Carbon — CARB-LO / CARB-MID / CARB-HI (RFF low / mid / high; 2026 knot $0 in all three)

| case | year | valid | ΔCO2 Mt (arm) | import CO2 | Δunserved TWh | Δclean share | Δcurt TWh | lw_price arm / REF |
|---|---|---|---|---|---|---|---|---|
| CARB-LO ($2.00/t) | 2027 | yes | **−0.3930** (255.58) | 0.0 | 0.0000 | 0.0000 | 0.000 | 983.3 / 982.3 |
| CARB-MID ($3.75/t) | 2027 | yes | **−0.9280** (255.05) | 0.0 | 0.0000 | 0.0000 | 0.000 | 984.2 / 982.3 |
| CARB-HI ($7.50/t) | 2027 | yes | **−2.3348** (253.64) | 0.0 | 0.0000 | 0.0000 | 0.000 | 986.2 / 982.3 |
| all three | 2026 | yes | 0.0000 (214.39) | 0.0 | 0.0000 | 0.0000 | 0.000 | 91.0 / 91.0 |
| CARB-LO | 2028 / 2029 / 2030 | **no** | −8.45 / −18.24 / −26.61 | 0.0 | 0.00 / +2.28 / +2.89 | +0.029 / +0.057 / +0.080 | 0 / 0 / +0.007 | 3216.9 / 3872.1 / 4454.5 vs 3216.0 / 3846.0 / 4437.5 |
| CARB-MID | 2028 / 2029 / 2030 | **no** | −8.58 / −18.29 / −26.64 | 0.0 | 0.00 / +2.28 / +2.89 | +0.029 / +0.057 / +0.081 | 0 / 0 / +0.007 | 3217.7 / 3872.8 / 4455.0 |
| CARB-HI | 2028 / 2029 / 2030 | **no** | −8.95 / −18.53 / −26.74 | 0.0 | 0.00 / +2.28 / +2.89 | +0.030 / +0.057 / +0.081 | 0 / 0 / +0.007 | 3219.4 / 3874.5 / 4456.1 |

**2027 by-fuel footprint (TWh, valid):** CARB-LO coal −0.509 / gas_cc +0.644 / gas_st −0.151; CARB-MID coal −1.290
/ gas_cc +1.272 / gas_ct +0.154 / gas_st −0.171; CARB-HI coal −3.511 / gas_cc +2.916 / gas_ct +0.715 / gas_st −0.189;
**nuclear, hydro, wind, solar exactly 0.0000 in all three** (G3 PASS). The mechanism is the coal→gas-CC merit-order
substitution at ~1:1 energy (P-4 HIT). **The dose-response is SUPER-linear, not sub-linear:** LO/MID/HI = 0.42× /
1× / 2.52× for 0.53× / 1× / 2× the price (P-5: LO inside its band, HI MISSES its −1.4 to −2.0 band at −2.33 — the
$7.50/t price crosses a second coal/gas spread that $3.75 does not). **2028–2030 is the pin's CCS conversion**: gas_cc
−22.1 / −70.5 TWh against gas_cc_ccs +22.4 / +70.6 TWh at 2028 / 2030 in every carbon arm within 0.5 TWh of each
other; the +2.28 / +2.89 TWh of extra unserved in 2029–30 is the capture parasitic derate on 5.9 / 8.9 GW of converted
CC, identical to the 0.0001 TWh across all three arms and CES-P10/P20 — i.e. not a carbon response. The $7.50 → $15/t
carbon **does** add something on top (§2.6).

### 2.2 CES premium ladder — CES-P10 / CES-P20 / CES-P30

| case | year | valid | ΔCO2 Mt | import | Δunserved TWh | Δclean share | Δcurt TWh | Δavg price $/MWh | neg-price h arm / REF |
|---|---|---|---|---|---|---|---|---|---|
| CES-P10 | 2026 / 2027 | yes | −0.0001 / 0.0000 | 0.0 | 0 / 0 | 0 / 0 | 0 / 0 | −0.68 / −0.71 | 599 / 522 · 624 / 546 |
| CES-P20 | 2026 / 2027 | yes | 0.0000 / 0.0000 | 0.0 | 0 / 0 | 0 / 0 | 0 / 0 | −1.36 / −1.43 | 599 / 522 · 624 / 546 |
| CES-P30 | 2026 / 2027 | yes | 0.0000 / 0.0000 | 0.0 | 0 / 0 | 0 / 0 | 0 / 0 | −2.05 / −2.14 | 599 / 522 · 624 / 546 |
| CES-P10 | 2028 / 2029 / 2030 | **no** | −7.64 / −17.58 / −26.04 | 0.0 | 0 / +2.28 / +2.89 | +0.030 / +0.058 / +0.081 | 0 / 0 / +0.006 | −0.71 / +25.4 / +18.1 | 624 / 0 |
| CES-P20 | 2028 / 2029 / 2030 | **no** | −7.66 / −17.24 / −25.80 | 0.0 | 0 / +2.28 / +1.31 | +0.030 / +0.058 / +0.082 | 0 / 0 / −0.006 | −1.43 / +24.7 / −6.4 | 624 / 0 |
| CES-P30 | 2028 / 2029 / 2030 | **no** | −7.61 / −19.43 / −29.29 | 0.0 | 0 / +6.97 / +4.90 | +0.030 / +0.063 / +0.089 | 0 / 0 / −0.009 | −2.14 / +68.6 / −15.3 | 624 / 0 |

**The premium has NO dispatch footprint in 2026–2027** (every fuel row Δ = 0.0000 TWh in all three arms; CES-P10's
2026 max |Δgen| is 232.6 MWh — a tie-break) and moves prices only through the offer: negative-price hours 522 → 599
(2026) and 546 → 624 (2027), captured wind price −$0.9 / −$1.8 per MWh at P20 / P30, average price −$0.7 / −$1.4 /
−$2.1 — the premium's own arithmetic (P-10's price and negative-hour directions HIT; curtailment does **not** rise —
MISS — because ERCOT's curtailment is fixed by the dump floor at 4.9 TWh in every non-row arm). **Its content is the
entry screen**, which is 2029–2030 (§4): P10 = REF's build; P20 adds 2,000 MW wind in 2030 in place of solar; P30
adds 1,000 MW solar (2029) and 5,000 MW wind for 1,000 MW less gas-CC. **P-8 (P20 ≈ P30 within 1 %) MISSES**: clean
share 0.3992 vs 0.4058, commissioned VRE 8,346.9 + 6,654.6 vs 9,346.9 + 6,654.6 MW, CO2 303.08 vs 299.59 Mt. The
ladder is monotone and unsaturated through $30 at the pin. P-9 (P10 separates from P20) HITS only at 2030 wind
(+2,000 MW) and by 0.0011 of clean share — below the saturation point the ERCOT response to $10 → $20 is small.

### 2.3 CES target — CES-T80 (0.55 in 2026 → 0.80 by 2035; ACP $50/MWh)

| year | valid | ΔCO2 Mt | import | Δunserved TWh | Δclean share | Δcurt TWh | CES dual $/MWh | lw arm / REF |
|---|---|---|---|---|---|---|---|---|
| 2026 | yes | +0.0003 | 0.0 | 0.0000 | +0.0043 | **−4.334** | **50.0000** | 91.0 / 91.0 |
| 2027 | yes | −0.0014 | 0.0 | 0.0000 | +0.0047 | **−4.908** | **50.0000** | 982.3 / 982.3 |
| 2028 | no* | +0.0002 | 0.0 | 0.0000 | +0.0045 | −4.908 | 50.0000 | 3216.0 / 3216.0 |
| 2029 | no | −16.73 | 0.0 | **+16.818** | +0.0492 | −4.908 | 50.0000 | 4023.3 / 3846.0 |
| 2030 | no | −27.26 | 0.0 | **+16.447** | +0.0764 | −4.919 | 50.0000 | 4537.6 / 4437.5 |

\* 2028 is byte-close to REF in this arm (no conversion yet — the row cases convert a year later than the others,
§2.6), so the 2028 row happens to be readable: the target's whole 2026–2028 dispatch content is the −4.33 / −4.91
TWh of "un-curtailment", and that is the **dump artefact of §0 item 4** — `total_gen_mwh` rises by exactly
Δ(wind+solar), storage charge Δ ≤ 0.0025 TWh, unserved Δ = 0, thermal Δ ≤ 0.004 TWh, and I3 gains a "dump 2.15 % /
2.41 % of renewable pot." line. **G4 PASSES exactly**: dual = ACP $50.0000 in all five years (escape regime every
year, as P-11 predicted from REF's falling clean share 0.3953 → 0.3172). Credited share reaches 0.3996 / 0.3566 /
0.3302 / 0.3738 / 0.3936 (the 2029 rise is the entry response, §4), never 0.55; escape ≈ target·D − credited ≈
90 / 131 / 161 / 138 / 133 TWh on the report's `clean_share × generation` proxy (V is not persisted — WS-3b's
routed deviation 5 — so this is the report-layer reading, and it is overstated by the ~4.9 TWh dumped).

### 2.4 Voluntary — VOL-HI (`high`: s_base 0.08, f_commit 1.0, WTP $7.0/MWh)

| year | valid | ΔCO2 Mt | import | Δunserved | Δclean share | Δcurt TWh | dual $/MWh | V − G_elig TWh (escape proxy) | lw arm / REF |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | yes | +0.0003 | 0.0 | 0 | 0.0000 | 0.000 | **0.0** | −78.0 (slack) | 91.0 / 91.0 |
| 2027 | yes | −0.0014 | 0.0 | 0 | 0.0000 | 0.000 | **0.0** | −25.3 (slack) | 982.3 / 982.3 |
| 2028 | no* | +0.0002 | 0.0 | 0 | +0.0045 | **−4.908** | **7.0** | +24.5 | 3216.0 / 3216.0 |
| 2029 | no | −7.95 | 0.0 | 0 | +0.0298 | −4.908 | **7.0** | +59.0 | 3846.0 / 3846.0 |
| 2030 | no | −16.01 | 0.0 | 0 | +0.0548 | −4.919 | **7.0** | +100.8 | 4437.5 / 4437.5 |

**G7 PASSES exactly and P-12 HITS to the digit**: dual 0 / 0 / 7.0 / 7.0 / 7.0 — slack while V < G, the escape
firing at the `high` ceiling from 2028 (the year V = 227.9 TWh outgrows eligible generation 198.5 → 203.4 TWh). The
escape proxy is `V − Σ(wind + solar)` from the class energies, 24.5 / 59.0 / 100.8 TWh (PRECOMMIT's pre-dispatch
29.5 / 63.9 / 105.7 less the 4.9 TWh the row "recovers" — by dumping it, §0 item 4). **Price and unserved are
byte-identical to REF in every year** (the $7 escape is 0.2 % of a $4,000 scarcity price, P-15's reasoning), and the
2029–2030 CO2 delta is the pin's CCS conversion (2,764 / 3,000 MW), not the row (P-15 MISSES at magnitude for that
reason: |ΔCO2| = 7.95 / 16.01 Mt > 2 Mt). \* 2028: no conversion yet in this arm.

### 2.5 The combined legs — both nettings (ruling S11 / G9)

**CES-P20+VOL-HI.** Dispatch: identical to VOL-HI's row footprint (Δcurt −4.908 from 2028, dual 0 / 0 / 7 / 7 / 7)
laid over CES-P20's offer effect (neg-price hours 599 / 624). **Deployment: identical to CES-P20 in every year**
(2029: gas_cc 4,344.8 + solar 3,900 + wind 4,446.9 + retrofit 2,968.6 MW; 2030: +2,000 MW wind) — **P-16 HITS**: the
$20 premium beats the $7 ceiling in the screens' `max()`, so the voluntary dual is irrelevant to entry while remaining
the row's own escape price. CO2 vs CES-P20: +0.0001 / +0.0010 / 0.0000 Mt at 2028–2030 (import 0.0). The two nettings
are trivial here by construction (a premium has no row): *counts-toward* = *additional* = the voluntary escape above.

**ALL-CLEAN** (carbon mid + growth high + DC high + CES target/ACP 50 + voluntary high). Duals **[50.0, 7.0] in all
five years** (federal, voluntary), P-13 HIT. Vs REF it is dominated by the load half: ΔCO2 +41.63 / +42.78 / +6.81 /
−0.42 / −11.78 Mt (import 0.0; the sign flips as the pin's conversion and the extra solar overtake the load-driven
fossil increase), Δunserved +2.3 / +66.7 / +186.4 / +284.6 / +411.6 TWh, `hours_ge_500` = 8,760 from 2028 — the
LOAD-HI adequacy collapse the load lane measured, unchanged by any policy row. **Vs CARB-MID+LOAD-HI** (its own
pairing base at the same pin, valid in every year): ΔCO2 **+0.0000** Mt in 2028–2030, Δunserved 0, deployment
identical — the CES target and the voluntary row add **no** dispatch or entry content on top of carbon + DC-high load
at ERCOT, because under 8,760 scarcity hours every eligible MWh is already dispatched and every screen already builds
at its cap. Both nettings, per year (report-layer arithmetic, `clean_share × generation` as credited, V from
PRECOMMIT §3.1, D = generation):

| year | credited ~TWh | 0.55·D | **counts-toward** escape (as built) | V | **additional** escape = max(0, 0.55·D + V − credited) | CES dual under each |
|---|---|---|---|---|---|---|
| 2026 | 240.4 | 372.6 | **132.2** | 226.1 | 358.3 | 50.0 / 50.0 |
| 2027 | 242.2 | 411.0 | **168.8** | 345.9 | 514.7 | 50.0 / 50.0 |
| 2028 | 263.9 | 415.9 | **152.0** | 467.9 | 620.0 | 50.0 / 50.0 |
| 2029 | 303.2 | 453.7 | **150.5** | 592.8 | 743.2 | 50.0 / 50.0 |
| 2030 | 344.5 | 489.7 | **145.2** | 720.9 | 866.2 | 50.0 / 50.0 |

Counts-toward is the headline (as built); additional beside it. Under either netting the row is in the escape regime
in every year at ERCOT, so the CES dual is the ACP under both and D-6's choice moves the escape volume, not the price.
Neither is asserted as the answer; D-6 is open. Credited volumes include the dumped MWh (§0 item 4).

### 2.6 Leg-vs-leg at 2028–2030 — the comparisons that ARE valid on the pin

| comparison (both at `bdfb3095`) | 2028 | 2029 | 2030 | reading |
|---|---|---|---|---|
| CARB-HI − CARB-LO, CO2 Mt | −0.495 | −0.290 | −0.134 | the carbon response **saturates under scarcity** as P-6 reasoned — for +$11/t at 2028 and +$22/t at 2030 the extra abatement shrinks toward zero (2027: −1.94 Mt for +$5.50) |
| CARB-MID − CARB-LO | −0.126 | −0.053 | −0.029 | same |
| CES-P30 − CES-P10 | +0.032 | −1.847 | −3.250 | the premium's content is entry (2029–30), not dispatch |
| CES-P20 − CES-P10 | −0.017 | +0.342 | +0.243 | P20's extra 2,000 MW wind displaces solar, CO2 slightly up |
| (CES-P20+VOL-HI) − CES-P20 | +0.0001 | +0.0010 | 0.0000 | the voluntary row adds nothing to a premium arm (P-16) |
| CES-T80 − VOL-HI, CO2 / unserved TWh | 0.000 / 0.000 | −8.78 / +16.82 | −11.26 / +16.45 | both row cases convert a year late; the target's own content is the 2029 entry swap (§4) and its adequacy cost |
| ALL-CLEAN − (CARB-MID+LOAD-HI) | 0.0000 | 0.0000 | 0.0000 | rows are inert on top of carbon + DC-high load |

### 2.7 CARB-MID+LOAD-HI vs LOAD-HI (its pairing base, `31cf71afda5c610d` at `1cc45bb2`)

2026: identical. 2027 (valid): ΔCO2 **−0.0232 Mt** (coal −0.005, gas_cc +0.073, gas_st −0.059 TWh), Δunserved 0 —
at LOAD-HI's 2027 (7,095 scarcity hours, 71 TWh unserved) the $3.75/t price finds almost no coal→gas swap left to
make: **the carbon axis is 40× weaker on the high-load posture than on REF (−0.928 Mt)**, the same saturation as
§2.6 row 1 arriving two years earlier. 2028–2030 contaminated (LOAD-HI converts nothing at `1cc45bb2`; the arm
converts 2,996 / 3,000 / 3,000 MW): ΔCO2 −9.02 / −17.12 / −25.18 Mt reported, not quoted.

---

## 3. Gate verdicts G1–G12 (structural, STOP-only; nothing gated on a residual)

| gate | verdict | evidence |
|---|---|---|
| **G1** premise reproduces at the pin | **PASS** | ADDENDUM A(a) 14/14 keys; A(b) P3; the resolved $/t of §4.1 is what every carbon arm carries (2026 $0, 2027 2.00 / 3.75 / 7.50) |
| **G1a** carbon arms' 2026 ≡ REF | **PASS, bit-identical** | co2 214.3926 = 214.3926, lw 91.037 = 91.037, max \|Δgeneration_by_fuel\| = **0.000000 MWh** in all three |
| **G2** REF-side precondition | **PASS (asserted, not discovered)** | REF unserved 0.38 → 127.2 TWh, reserve margin +0.033 → −0.253, FAIL {I3, I12}, `hours_ge_500` 74 → 7,962 — exactly as declared. Consequence carried in every §2 table: no ERCOT price level or captured price is campaign-grade in any year |
| **G3** footprint confinement | **PASS 2026–2028; 2029–2030 PASS on dispatch, entry moves noted** | carbon 2027: every zero-carbon row 0.0000 TWh. 2029–30: +1.1 TWh solar from a +500 MW solar build under carbon (entry, not dispatch) — inside the contaminated window. CES arms: eligible/ineligible shares + the dual only (2026–27 dispatch Δ = 0 exactly). Voluntary: eligible rows + escape only; thermal Δ ≤ 0.004 TWh |
| **G4** CES-T80 dual identity | **PASS, exact** | dual = 50.0000 in all five years, target unmet in every year (credited ≤ 0.40 < 0.55) |
| **G5** no non-target invariant flips PASS → FAIL | **PASS, all eleven** | every arm FAIL = {I3, I12} = REF; WARN sets are REF's or a subset |
| **G6** no new unserved where the mechanism cannot raise demand | **PASS 2026–2028; 2029–2030 NOT SCORABLE vs REF** | CARB-*, CES-P*, VOL-HI: Δunserved = 0.0000 in 2026–2028. 2029–30: +2.28 / +2.89 TWh in every converting arm identically (the capture derate on the pin's conversion, which REF was never given the chance to make); VOL-HI 0.0000 in all five years. **CES-T80 2029–30: +16.8 / +16.4 TWh is REAL** (its 3,000 MW gas-CC displaced by solar) and is reported as the adequacy cost in §4, not as a gate kill — the mechanism did what its dual says, at a price the gate now discloses |
| **G7** voluntary dual bounded | **PASS, exact** | 0 / 0 / 7.0 / 7.0 / 7.0 on VOL-HI and CES-P20+VOL-HI; 7.0 all five years on ALL-CLEAN; escape = shortfall (§2.4) |
| **G8** curtailment before thermal | **PASS in letter — FAILS in substance (§0 item 4)** | first binding year: Δcurt −4.908 TWh, \|Δfossil\| ≤ 0.004 TWh. But the recovered MWh is dumped, not delivered: the row is satisfied by phantom clean energy. The gate as written cannot distinguish the two; it is re-specified in §7 item 2 |
| **G9** both nettings on the combined legs | **PASS** | §2.5, counts-toward headline, additional beside it, CES dual under each |
| **G10–G12** CAP-STATE-TIGHT | **N/A** | killed at phase 0 on a proven identity; never in ERCOT's chartered set |

**No gate kills an arm.** The two findings that matter — the live D65-B seam and the dump crediting — are things the
gates surfaced (P-7's consequence clause; G8's mechanism claim) rather than things they were built to catch, and both
are routed, not scored.

**FC-6 paired battery, REF / CARB-MID.** The committed-config half (`--paired-run-configs`, G1's
`fc6_paired_premise.json`): **P1.premise FAIL — "MIS-CONSTRUCTED: high-arm effective carbon ≤ base in 1/5 years
(2026: Δ+0.00 $/t)"**, P1 SKIP at that grain. This is the RFF ladder's own construction — every path anchors 2026 at
$0 (PRECOMMIT §4.1, G1a) — meeting a checker premise that demands a strict increase in **every** year; WS-1b hit the
same wall and re-scoped to 2027. Reported at full magnitude; the checker's every-year strictness is routed (§7 item 3).
P1 scored from the summaries at the grain the checker itself uses for P2: cumulative CO2 base **1,390.128 Mt** vs
high **1,335.689 Mt** ⇒ PASS (contaminated years included); **2026–2027 only: 470.366 vs 469.438 Mt ⇒ PASS** on the
valid window.

---

## 4. The deployment response — the campaign's first policy-side reading (vs REF's ledger)

REF builds: 2027 gas_ct 880 + wind 553 + solar 100; 2028 gas_cc 674 + gas_ct 411; 2029 gas_cc 4,344.8 + gas_ct 500
+ solar 3,400 + wind 4,446.9, retires gas_st 446; 2030 gas_cc 3,000 + gas_ct 2,345.4 + solar 6,654.6 MW. No retrofits.

| arm | retirements vs REF | entry vs REF | retrofits (gas_cc → gas_cc_ccs) |
|---|---|---|---|
| CARB-LO / MID / HI | none (446 MW gas_st in all) | 2029: +500 MW solar (3,900 vs 3,400), gas_ct 500 → 0; otherwise REF's build | 2,932 / 2,947 / 2,984 MW (2028), 2,997 / 2,981 / 2,981 (2029), 3,000 (2030) — **the pin's, not the policy's** (§0 item 2) |
| CES-P10 | none | = carbon arms' (+500 MW solar 2029) | 2,986 / 2,983 / 3,000 |
| CES-P20 | none | + 2030: **+2,000 MW wind, −2,000 MW solar** | 2,986 / 2,969 / 3,000 |
| CES-P30 | none | 2029: **+1,500 MW solar, −1,000 MW gas_cc**; 2030: **+5,000 MW wind, −5,000 MW solar** | 2,991 / 2,999 / 2,994 |
| CES-T80 | none | 2029: **+3,500 MW solar, −3,000 MW gas_cc**, gas_ct 500 → 0; 2030: +5,000 MW wind, −5,000 MW solar | 0 / 2,951 / 2,998 (a year late) |
| VOL-HI | none | REF's build exactly | 0 / 2,764 / 3,000 (a year late) |
| CES-P20+VOL-HI | none | = CES-P20 exactly | = CES-P20 |
| CARB-MID+LOAD-HI, ALL-CLEAN | none | = LOAD-HI's build exactly (2029 gas_ct 2,345 + solar 1,555; 2030 gas_ct 3,000 + solar 1,000 + wind 5,000) | 2,996 / 3,000 / 3,000 |

Readings: (i) **no policy retires anything** — REF's single 446 MW gas_st exit is the only retirement in every arm,
because on an ISO shedding 41–127 TWh every thermal unit is inframarginal against $4,000+ scarcity; (ii) **the
attribute price is an entry signal and only an entry signal** at ERCOT: the premium starts displacing solar with wind
at $20 and gas-CC with VRE at $30; the $50 target does it hardest and pays +16.8 TWh of unserved for it; (iii) the
voluntary row at $7 moves no build in any arm; (iv) **the CCS retrofit row is a NULL for the policy reading** — it is
present in every arm at the cap and absent from REF for a code reason, and only the routed control can say whether
CARB-HI's 2,984 vs CARB-LO's 2,932 MW is signal. ERCOT converts no CCS **in response to any policy here** as far as
this record can show.

---

## 5. PRECOMMIT §6 predictions, scored as written

| # | prediction | verdict | measured |
|---|---|---|---|
| P-1 | CARB-MID 2027 = WS-1b to 4 dp | **HIT, exact** | 255.0452 Mt / 984.247 / 4,621,769.86 / 0.3519 / import 0.0 |
| P-2 | carbon arms' 2026 ≡ REF | **HIT** | max \|Δgen\| 0.000000 MWh |
| P-3 | CO2 ↓, price ↑ monotone REF → LO → MID → HI, 2027–2030 | **HIT** | 2027: 255.97 / 255.58 / 255.05 / 253.64; lw 982.3 / 983.3 / 984.2 / 986.2; ordering holds in every year |
| P-4 | coal → gas-CC ~1:1, zero-carbon Δ = 0 | **HIT** (2027) | MID coal −1.290 / gas_cc +1.272; zero-carbon 0.0000 |
| P-5 | LO −0.3 to −0.7; HI −1.4 to −2.0 (sub-linear) | **LO HIT (−0.393); HI MISS (−2.335, super-linear 2.52× MID)** | a second coal/gas spread opens between $3.75 and $7.50 |
| P-6 | ΔCO2 shrinks toward 0 by 2029–30 under scarcity | **MISS vs REF (contaminated: −26 Mt); HIT leg-vs-leg** | HI − LO: −1.94 (2027) → −0.49 → −0.29 → −0.13 Mt |
| P-7 | no gas_cc_ccs in any carbon arm | **MISS, full magnitude** | 2,932–2,984 MW in 2028 in every arm; 22.4–22.8 TWh; the pre-registered consequence (D77/D65-B live, control re-stated) applies |
| P-8 | P20 ≈ P30 within 1 % | **MISS** | clean 0.3992 vs 0.4058 (1.7 %), VRE 15.0 vs 16.0 GW, CO2 303.08 vs 299.59 |
| P-9 | P10 separates from P20 | **HIT, weakly** | +2,000 MW wind at 2030, clean +0.0011 |
| P-10 | clean ↑, VRE ↑, avg price ↓, neg hours 0 → >0, curtailment ↑ | **4 of 5 HIT; curtailment MISS** | curtailment flat (dump floor 4.9 TWh) |
| P-11 | CES-T80 in escape regime every year, dual = $50 exactly | **HIT, exact** | 50.0000 × 5 |
| P-12 | VOL-HI dual 0 / 0 / 7 / 7 / 7, escape ≈ 29.5 / 63.9 / 105.7 | **HIT, exact on the dual; escape 24.5 / 59.0 / 100.8** | the 4.9 TWh "recovery" is the dump |
| P-13 | ALL-CLEAN dual $7 all five years | **HIT** | [50.0, 7.0] × 5 |
| P-14 | curtailment falls before thermal moves | **HIT in letter, falsified in substance** | §0 item 4 |
| P-15 | voluntary \|ΔCO2\| < 2 Mt every year | **HIT 2026–2028 (≤ 0.002); MISS 2029–30 (7.95 / 16.01, the pin's conversion)** | |
| P-16 | voluntary dual irrelevant to deployment under a $20 premium | **HIT** | CES-P20+VOL-HI build ≡ CES-P20 |
| P-17 | both nettings reported, counts-toward headline | **done** | §2.5 |

Twelve hits, five misses, none explained away. The two most reasoned predictions (P-6, P-7) are the two that taught
the most: P-7's miss re-opened the control, P-6's leg-vs-leg hit is the campaign's carbon-under-scarcity result.

---

## 6. Wall / RSS per solve-year (card D-5's input) — all in owner-launched sub-lane containers

| case | 2026 | 2027 | 2028 | 2029 | 2030 | leg total |
|---|---|---|---|---|---|---|
| CARB-LO | 3.65 min / 3.31 GB | 2.12 / 4.01 | 1.73 / 3.53 | 1.32 / 3.54 | 1.21 / 3.55 | 10.0 min |
| CARB-MID | 3.10 / 3.29 | 1.93 / 4.04 | 1.91 / 4.05 | 1.31 / 3.73 | 1.23 / 3.54 | 9.5 |
| CARB-HI | 3.19 / 3.26 | 1.97 / 3.98 | 1.80 / 3.92 | 1.36 / 3.91 | 1.27 / 3.91 | 9.6 |
| CES-P10 | 2.82 / 3.26 | 1.55 / 3.37 | 1.46 / 3.53 | 1.08 / 3.54 | 0.99 / 3.54 | 7.9 |
| CES-P20 | 2.35 / 3.34 | 2.01 / 3.42 | 1.34 / 4.00 | 1.08 / 3.54 | 0.88 / 3.55 | 7.7 |
| CES-P30 | 2.33 / 3.50 | 1.45 / 3.43 | 1.50 / 3.92 | 1.17 / 4.03 | 0.95 / 3.55 | 7.4 |
| CES-T80 | 2.62 / 3.36 | 1.57 / 3.41 | 1.84 / 3.64 | 1.08 / 4.20 | 0.82 / 3.70 | 7.9 |
| CARB-MID+LOAD-HI | 2.24 / 3.33 | 1.42 / 3.41 | 0.81 / 3.54 | 0.69 / 3.54 | 0.46 / 3.37 | 5.6 |
| VOL-HI | 2.18 / 3.44 | 1.28 / 3.47 | 1.72 / 3.99 | 1.00 / 3.60 | 0.85 / 3.60 | 7.0 |
| CES-P20+VOL-HI | 2.68 / 3.29 | 1.34 / 3.35 | 1.78 / 4.16 | 1.08 / 3.96 | 0.87 / 3.59 | 7.8 |
| ALL-CLEAN | 2.52 / 3.31 | 1.53 / 3.39 | 0.93 / 3.40 | 0.75 / 3.39 | 0.50 / 3.24 | 6.2 |

**55 solve-years, 86.6 min of LP summed across the four containers** (G1 29.1, G2 23.0, G3 20.5, G4 14.0 min);
wall-clock ≈ the longest group. Peak RSS **4.20 GB** (CES-T80 2029). The PRECOMMIT's 6.5–7 min/leg was right on
the CES legs and ~40 % low on the carbon legs, whose 2026 LP (3.1–3.7 min) is the slow one; the deep-shortage years
are fast because the LP is degenerate on slack.

---

## 7. Routed to SCN-DESK — not executed, outside this lane's regions

1. **ERCOT's REF, LOAD-HI and LOAD-HI-ORGANIC are contaminated legs and must be re-solved at THE PIN** into
   `results/scn-campaign-load-2026-09-06-r2/ERCOT/<CASE>/` with same-id re-registration, exactly RESOLVE's protocol
   (PRECOMMIT-scn-ws5a-resolve §4). Ruling S8 excluded them as "CCS-clean at `1cc45bb2`"; §0 item 2 shows the
   cleanliness was the pre-fix screen's, and capx D65-B is LIVE on ERCOT. Under rule 29(b) this is the LIVE-hunk case
   that **earns** a control solve; under charter P2 ("never re-solve REF") it is the desk's call, so it is routed with
   a ready sub-lane prompt (this session's closing message) rather than run. Until it lands, every 2028–2030 delta vs
   REF in §2 is a number with a code seam inside it. The synthesis and cost table (RESOLVE's owed addendum) gain three
   legs. **The G-DRIFT lesson for the record:** an input change to a screen is never inert because the screen's
   pre-change output was zero — it is inert only if the changed input cannot cross the screen's threshold.
   **DISCHARGED 2026-09-07 — `docs/handoffs/ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md`.** The three legs
   were re-solved at THE PIN (`FINDING-scn-ws5a-resolve-ercot-2026-09-07.md`) and the eleven policy legs are
   re-differenced against that REF there. **The embargo above is lifted, and §2 / §4 at 2029–2030 are superseded by
   the addendum's §5 Table A** — 2026–2028 are unchanged to the digit. Headlines: ~60 % of the 2030 abatement was the
   control's own retrofit screen (CARB-HI −26.7447 → **−10.7360 Mt**); **VOL-HI's whole CO2 effect was the control**
   (−16.0087 → **+0.0000 Mt**, so §5's P-15 re-scores MISS → **HIT**); §2.5's ALL-CLEAN **sign flip is WITHDRAWN**
   (2029/2030 vs REF −0.4245 / −11.7753 → **+7.5276 / +4.2334 Mt**); §4 reading (iv)'s *"the CCS retrofit row is a
   NULL for the policy reading"* is **FALSE** — the policy converts 2.93–3.00 GW at 2028 where REF converts none, and
   carries a durable +3.17 to +3.23 GW at 2029–2030; and §2.1's attribution of the +2.28 / +2.89 TWh of extra unserved
   to the capture derate is **replaced** — the derate moves unserved by exactly zero, the driver is the 500 MW gas-CT
   the arms do not build in 2029 (addendum §4.2).
2. **The clean rows credit dumped energy** (§0 item 4). `Σ_g credit·P + Σ W + Σ S + ESC ≥ target·D` reads the
   generator columns; the energy balance lets the LP raise `W`/`S` to their CF bound and absorb the surplus in
   `Dump[z,t]` at ε. Fix belongs to `model/lp/rows.py` (WS-2a / WS-3b regions): credit **delivered** eligible energy
   — `W + S − Dump` restricted to the eligible share, or an explicit `≤ demand`-side crediting cap. Consequences
   until fixed: every credited volume in §2.3–§2.5 is high by ~4.9 TWh/yr at ERCOT, every escape low by the same,
   and G8/P-14 as specified cannot distinguish un-curtailment from dumping — re-specify G8 as "Δcurtailment < 0 AND
   Δdump ≤ 0". The un-curtailed 4.9 TWh is exactly REF's whole curtailment, so the row's first act at ERCOT is an
   accounting move, not a dispatch one.
3. **`check_forecast_invariants.py`'s carbon-pair premise** requires a strict carbon increase in every year and so
   declares every RFF-ladder pair mis-constructed on the 2026 $0 knot (§3, FC-6). A premise that asks for "≥ in every
   year and > in at least one" scores the ladder as built. Scorer region, not this lane's.
4. **CES-T80's adequacy cost** — the target buys +3,500 MW solar for −3,000 MW gas-CC in 2029 and pays +16.8 TWh of
   unserved in an ISO already shedding 76 TWh (§4). A campaign-level statement about a clean target on an energy-only
   ISO without a capacity instrument; belongs beside the load lane's adequacy reading, not in this lane's gates.
5. **PRECOMMIT §9 item 4 (VOL-MID inert across the T1-F window; D-3c's new-builds-only crediting leg is what would
   change it)** — already carried to card D-3c by the desk (ledger §0 r#17). Stated here as routed; not acted on.
   Note the dump finding sharpens it: under new-builds-only crediting the row could not be met by dumping existing
   fleet output either.
6. **§9 item 3** (the campaign YAML's stale 122 GW ERCOT tail-regime prose) — the desk's records item; not touched.
7. **Naming:** run ids lower-case the case and spell `+` as `-plus-`; the sibling policy lanes may differ. One
   convention per campaign is the desk's to fix in the registry.
8. **The four sub-lane branches** (`claude/scn-ws5a-policy-ercot-solve-g{1,2,3,4}-*`) merged by the repository's
   automation within seconds of push, as every lane's PR does; the `report/G*` split is the artefact of that
   parallelism (each group's report is referenced to its own first case; REF differencing is this document's).

## 8. Files

- `docs/handoffs/FINDING-scn-ws5a-policy-ercot-2026-09-06.md` — this document.
- `docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md` — ADDENDUM A appended (commit `867a1915`, merged).
- `docs/handoffs/SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md` — the protocol the four sub-lanes ran.
- `results/scn-campaign-policy-2026-09-06/ERCOT/<CASE>/{full_horizon_summary.json, run_config.json, duals.json}` ×11,
  `CARB-MID/fc6_paired_premise.json`, `bundle/G{1..4}/`, `report/G{1..4}/` — committed by the sub-lanes
  (`7f4d17c3`…`c629432e`).
- `frontend/data/hindcast/ercot-2026-2030-scn-campaign-policy-2026-09-06-<case>.json` ×11 + their lines in
  `frontend/data/hindcast/invariant-failures.json` — the sub-lanes'.
- `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §5.1 rows 3 and 7 (Carbon / CES premium / CES target /
  Voluntary, ERCOT) and `docs/handoffs/scenario-desk-ledger-2026-09.md` §3 mirror — this commit.
- `docs/codebase-site/data/mechanism-matrix/ERCOT.js` — the four cells, last commit.

**Duties.** No default moved, no knob moved, no `ScenarioConfig` field added; DOF ledger zero; no `authorized_price_tuning`.
Consumed, never edited: the campaign YAML, the base YAML, `src/`, every script, every committed bundle. Forecast
namespace only (§7.5); backcast byte-identity untouched by construction. Rule 29(c): no screen or control bundle
exists in this lane's tree — the control it needs is routed, not solved. Rule 27: no ≥300-line source file rewritten;
every push fetch-back verified.
