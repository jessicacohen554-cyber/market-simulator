# ADDENDUM 4 — **Stage A's headline is a five-year artifact. At full horizon the CES premium is NOT entry-masked: it builds 5,156.6 MW of new nuclear and cuts 73.7 Mt of CO2.**

**Written with `CAP-STATE-TIGHT` and `CES-T80` still solving.** It reports the `CES-P60 − REF`
delta, which is the first Stage-B *comparison* the campaign has been able to make — both legs are
registered, both reproduced their pre-declared keys, both are on the 206-row surface, and both
passed the 2026–2030 identity gate **exactly**. Nothing here needs the remaining legs, and nothing
here is revised by them.

---

## 1. The finding, against this lane's own Stage-A headline

`FINDING-scn-ws5a-policy-nyiso-2026-09-07.md` is titled: *"the CES premium is entry-masked at
every committed rung and reaches NYISO only through the CCS retrofit."* Over 2026–2030 that was
correct and is not withdrawn. **Over 2026–2050 it is false, and the mechanism it named is the
transitional one, not the durable one.**

| | Stage A (2026–2030, $60) | **Stage B (2026–2050, $60)** |
|---|---|---|
| Δ `builds_renew` / VRE | **+156.6 MW**, at 2030 only | **+2,000 to +2,156.6 MW**, every year from 2031 |
| Δ nuclear | +500.4 MW at 2030 (the S15 bracket's one find) | **0 → +5,156.6 MW by 2050** |
| Δ `gas_cc_ccs` | +1,634.4 MW at 2030, the named channel | peaks **+3,634.4 MW** (2034–46), then **falls to +634.4 MW** by 2050 |
| Δ CO2 | small | **−73.702 Mt cumulative**; −18.0 % at 2050 |
| Δ `lw_price` | −$13.79 at 2030 | **−$39.55/MWh at 2050** |

**The entry response was never absent — it was not yet delivered.** A five-year window ends before
the build pipeline (COD lag, queue caps, per-tech growth limits) can put steel in the ground, so
Stage A measured the *lag*, not a *mask*. **This is the single strongest argument the campaign has
produced for why ruling S18 authorised a full horizon at all**, and it is the correction that most
changes how the Stage-A synthesis should be read.

**And the channel inverts.** CCS is what the premium can reach *quickly* — a retrofit on an
existing host — so it dominates the first two decades. Nuclear is what the premium reaches
*eventually*, and once it arrives it displaces the retrofit: Δ`gas_cc_ccs` runs **+3,634.4 →
+1,634.4 → +634.4 MW** across 2046 → 2047 → 2049 while Δnuclear runs **+4,500 → +5,156.6 MW**.
Reading the 5-year window as "the premium's real channel is CCS" therefore gets the long-run
answer exactly backwards.

### 1.1 The delta, per year (both legs committed, both registered)

| year | Δ CO2 Mt | Δ `lw_price` | Δ VRE MW | Δ CCS MW | Δ nuclear MW | Δ clean TWh | REF neg-h % | P60 neg-h % |
|---|---|---|---|---|---|---|---|---|
| 2028 | +0.085 | −0.27 | 0.0 | +15.1 | 0.0 | 0.000 | 0.00 | 0.00 |
| 2030 | −5.244 | −13.79 | +156.6 | +1,634.4 | +500.0 | +4.249 | 0.00 | 0.00 |
| 2032 | −3.564 | −26.53 | +2,156.6 | +2,634.4 | +1,000.0 | +10.813 | 0.00 | 1.24 |
| 2035 | −2.680 | −31.18 | +2,000.0 | +3,634.4 | +1,656.6 | +15.847 | 0.00 | 10.08 |
| 2040 | −2.839 | −34.33 | +2,156.6 | +3,634.4 | +3,000.0 | +22.952 | 0.22 | 12.91 |
| 2045 | −3.268 | −33.38 | +2,000.0 | +3,634.4 | +4,156.6 | +21.830 | 2.53 | 15.93 |
| 2050 | −3.311 | **−39.55** | +2,156.6 | **+634.4** | **+5,156.6** | +24.294 | 4.30 | **16.55** |

At 2050: `total_cap` 81,020.7 → 87,333.9 MW; `co2_mt` 18.352 → 15.041 (**−18.0 %**); VRE
34,743.4 → 36,900.0 MW.

**A $60/MWh clean-attribute premium LOWERS the energy price by $39.55/MWh at 2050.** That is not a
paradox and is stated as arithmetic: the premium is paid on attributes, not into the energy
market, and the capacity it induces displaces gas on the margin. Any welfare reading has to net
the attribute payment against the energy saving, which this lane does not attempt and does not
have the instrument for.

---

## 2. The cost of that build, reported at full magnitude rather than buried

The premium's overbuild is what makes `CES-P60` FAIL three invariants where Stage A's five-year
version failed none — and the three are one causal chain, not three faults:

1. **I12 (reserve margin) FAIL** — 25.6 % (2031) to **32.5 %** (2035) against a requirement-implied
   band of [8.2 %, 23.2 %]. Sustained for two decades. The premium buys capacity the adequacy
   requirement never asked for.
2. **I14 (price sanity) WARN** — negative-price hours **0.00 % → 16.55 %** of the year. Overbuilt
   zero-marginal-cost capacity prices the energy market negatively for a sixth of all hours.
3. **I9 (storage integrity) FAIL — and this one is a MODEL finding, not a scenario result.**
   Simultaneous charge+discharge reaches **19.46 % of throughput** from 2032. Rule 9's
   `[R-EPSILON]` ε = 0.001 $/MWh tiebreaker exists precisely to stop that, and it is **overwhelmed
   once prices go deeply negative**: when charging is paid more than ε, cycling against itself is
   profitable and the LP takes it. The ε was sized for a market whose prices are non-negative
   almost always; a 16.5 %-negative-hours year is outside what it was scoped for.

**I9 is ROUTED, not repaired.** `src/market_sim/**` is outside this lane's regions, ε is a
registered constant, and changing it would move every ISO's keys. It is reported here with its
trigger condition (negative-price share above roughly 10 %) so the owning lane can size the fix
against evidence rather than intuition. **It is also a caution for any future high-VRE or
high-premium scenario on any ISO**, since nothing about it is NYISO-specific.

---

## 3. Predictions scored by this comparison

**P-3 (`CES-P60` vs `CES-T80` are NOT one instrument at two levels) — HALF-SCORED, and the half
that landed is confirmed.** `CES-P60`'s `clean_region_duals` reads **`None` in all 25 years**,
exactly as an *exogenous premium* must: it creates no clean-tier row, so there is no dual. The
`CES-T80` half — whether the *target row* produces a real dual and whether its retrofit build
stays near zero against P60's — is scored when that leg lands. **The two legs are still never
presented as one instrument at two levels.**

**P-9 (`rps_dual`) — CONFIRMED AGAIN, and now under a much harder test.** `rps_dual` = **40.0000
in all 25 years of `CES-P60`**, at `STATE_RPS_ACP["NYISO"]`, *even with +5.2 GW of new nuclear,
+2.2 GW of VRE and +24.3 TWh of clean generation over REF*. The RPS row never becomes interior.
The premium outbids the row inside `max()` rather than reaching it — Stage A's §7.1 finding,
holding at ten times the build.

**P-2 (`CES-T80` is the case the horizon transforms) — NOT YET SCORED**, and this addendum
sharpens the bar it must clear: P60 is now known to move +5,156.6 MW of nuclear by 2050, so
"CES-T80 separates from REF more than Stage A's +156.6 MW of solar" is no longer a demanding
prediction. The real question P-2 must answer is whether the **target row** reaches the same
channels the **premium** does, or whether the `ccs.py:475-476` coverage seam (P-3) keeps it out of
the retrofit while the nuclear channel stays open to both.

---

## 4. Status

| leg | key | surface | identity gate | registered |
|---|---|---|---|---|
| `REF` | `f1a2ef17634b0467` ✓ | 206 ✓ | **PASS**, 232 scalars, 0.000e+00 | ✓ I3 declared |
| `CES-P60` | `ddff74e2738eaf96` ✓ | 206 ✓ | **PASS**, 233 scalars, 0.000e+00 | ✓ I3/I9/I12 declared |
| `CAP-STATE-TIGHT` | `462d197ef1f9e023` | 206 | — | solving, 18/25 years at last report |
| `CES-T80` | `fc3ad07981d95d84` | 206 | — | solving |
| `ALL-CLEAN` | `774db75da9f4d95a` | 206 | — | queued (S14 caps the track at 2) |
| `CARB-MID` | — | — | — | **killed at phase 0**, 25 solve-years not spent |

`scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` reads **EXIT 0** after
each registration (latest: 181 sidecars / 2,534 records / 223 declared FAILs).

**Two exact identity passes in two attempts.** The pre-registered WARN band (1e-9 < |rel| ≤ 1e-6)
has never been used, on 465 scalars.

---

*Written before `CAP-STATE-TIGHT`, `CES-T80` or `ALL-CLEAN` returned. Parent:
`docs/handoffs/PRECOMMIT-scn-ws5b-nyiso-2026-09-07.md`, ADDENDUM 1–3.*
