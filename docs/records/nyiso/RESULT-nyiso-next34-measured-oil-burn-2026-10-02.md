# RESULT — NYISO-NEXT-34: measured oil burn — the off-cap object closes; the cap-binding cost is real (G-5 FAIL, mistimed MLK tail); hold — 2026-10-02

- **Pre-registration:** `docs/records/nyiso/PRECOMMIT-nyiso-next34-measured-oil-burn-2026-10-02.md` (merged in #7022, pin `00648e6e`).
- **Phase 0:** `docs/records/nyiso/FINDING-nyiso-next34-feb2023-oilburn-phase0-2026-10-02.md`.
- **Legs:** five year-isolated shards (rule 36), all at `00648e6e47353de9d3bbb4131504bee2259f4d6b`. Bytes were verified on disk
  before archiving. Provenance SHAs are in `.gitignore`.
- **Runs registered (probes, rule 15), on held draft PR #7053 (not on `main`: audit E13 until the owner rules):** `2026-10-02-nyisonext34-oilburn-probe` (bundle `results/calibration/nyisonext34_span`,
  2022–2025) and `2026-10-02-nyisonext34-oilburn-2021-probe` (`nyisonext34_2021`).
- **Benchmark basis.** Registration rebuilt the NYISO `bench/` parts on main's current reference data (EIA-923 Final
  2025, #7015). The keeper was re-scored on the same parts: still CALIBRATED, C3a unchanged. Every number below,
  keeper and arm alike, is on that one basis.

> **Superseded basis (added at merge, 2026-10-02).** While these shards solved, main promoted a new NYISO keeper,
> `2026-10-02-w0-nyiso` (bundle `w0_nyiso_span`, 2021–2025 in one bundle; the W0 EIA-860 settlement re-solve). Its
> C3a vs RT is +4.3 / −0.7 / +2.0 / −0.8 / −7.7. This arm was solved on the outgoing `nyisonext26p` recipe, so it is
> **not promotable** (option A below is void), and every "keeper" number below means `nyisonext26p`. The mechanism
> evidence carries forward: the off-cap half closes the object, and the cap-binding half reproduces NEXT-24. Any
> retest re-bases on `w0_nyiso_span`.

## 1. Gates (PRECOMMIT §3)

| gate | result |
|---|---|
| G-1 leg acceptance (pin; config = keeper + `dual_fuel_measured_oil_burn`) | PASS, 5/5 |
| G-2 live (generator-hours priced at the measured mix) | PASS: 901k / 939k / 871k / 896k / 848k |
| G-3 demand / slack vs keeper | PASS: 0.0 / 0.0 GWh, every year |
| G-4 C6 / C8 | PASS, every year |
| **G-5** no new D-4 FAIL row ≥ 5 GWh | **FAIL, 2025 only:** `nyiso_gas_commitment_bridge × CC_REGULAR`, plant 55405, **5.6 GWh**, 32 h. The keeper's row for the same plant passes at 2.4 GWh. No other new row in any year. |
| G-6a Feb 2023 \|error\| vs RT falls | PASS: −9.7 → **−5.6 %** |
| G-6b off-cap high-oil-day Σ\|err\| falls in ≥ 4/5 years | PASS, 4/5 (2024 flat: 167.0 → 167.5) |
| G-7 C3a band, 2025 ≥ −9.6, C3b rise ≤ 0.02, C1/C2/C4 not downgraded | PASS, every year |

Gate JSON: `results/phase0/nyiso/_nyisonext34_gates.json`.

## 2. Scores (rubric 3.13, one benchmark basis)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| C3a vs RT, keeper | +3.4 | −2.1 | +0.4 | −2.6 | −9.6 |
| **C3a vs RT, arm** | +4.4 | −0.6 | +1.2 | −2.0 | **−8.3** |
| C3b NRMSE, keeper | .118 | .146 | .130 | .126 | .161 |
| **C3b NRMSE, arm** | .118 | **.131** | .123 | .130 | **.154** |
| C3c h > $300, model / RT actual, keeper | 0 / 3 | 1 / 101 | 0 / 10 | 0 / 13 | 8 / 42 |
| C3c, arm | 0 / 3 | 5 / 101 | 0 / 10 | 0 / 13 | 36 / 42 → "PASS" (mistimed, see below) |
| Σ\|err\|, off-cap high-oil days, keeper → arm | 247 → 232 | 748 → 626 | 219 → 193 | 167 → 168 | 336 → 295 |
| Σ\|err\|, cap-binding high-oil days, keeper → arm (reported) | 64 → 69 | 1,241 → 1,216 | — | 40 → 52 | 317 → 379 |

- **Determination:** span CALIBRATED, 2021 CALIBRATED. The ISO is CALIBRATED either way.
- **Feb 2023** closes 4 of the 9.7 pt (−5.6 %). The rest is the trade-dated Feb 2 spike (flow-date, out of scope).
- **The C3c 2025 "PASS" is a count match on mistimed hours. It is not evidence.**
  - All 28 new tail hours are NYC / Long Island on **Jan 17–19 (+ 4 h Jan 20)**. Measured NYC RT > $300 on those days: 1 h on 1/17, 0 on 1/18–1/19.
  - The measured tail is **Jan 20–22** and **Jun 23–25**. The June hours are unchanged (5 h, as the keeper).
  - NYC daily mean, keeper → arm vs RT: 1/17 190 → **277** vs 135; 1/18 170 → 229 vs 106; 1/19 175 → 228 vs 107.
  - This is NEXT-24 §2c exactly. On the MLK weekend package the cap binds, and the measured mix *replaces* it (rule 19).
    Units that burned little oil are then priced on the ~$70 spot print, which NEXT-24 showed they did not pay
    (contract gas, unmeasured).
- **40 % of the 2025 C3a gain is that same error.** The arm − keeper shift is +1.26 pt: Jan 17–19 +0.49 (days already
  over RT), Jan 20–24 +0.27, Feb +0.18, Dec +0.17, Jun–Jul +0.11. Net of Jan 17–19, C3a 2025 would be ≈ −8.8.
- **Cap-binding high-oil days** worsen in 2021 / 2024 / 2025 (table above). The predicted cost is larger than
  the bracket suggested.

## 3. Reading

The two halves of the mechanism behave differently, as phase 0 and NEXT-24 together predicted:

- **Off-cap cells (gas ≤ oil).** Oil burned while gas was cheap is a real, measured cost the parity cap cannot
  represent. These cells close the object: Feb 2023 and the off-cap high-oil days in 4 of 5 years.
- **Cap-binding cells (gas > oil).** The measured mix replaces the cap with `f·oil + (1−f)·spot gas`. NEXT-24 showed
  the non-switching units were not paying spot. This half produces the MLK overshoot, the mistimed C3c hours,
  the worse cap-binding days and the extra bridge commitment behind the G-5 row.

The pre-fixed promotion rule fails (G-5). The C3c and part of the C3a improvements are compensating errors, so this
arm should **not** be promoted as solved. The structural question is now narrow: scope the measured mix to the
off-cap cells, and keep the parity cap where it binds. That is a new field, not a re-tune: zero parameters, and the
scope boundary is the existing cap test (`gas > oil`, `dual_fuel_switch_mask`). It needs its own PRECOMMIT and solve.

## 4. DECISION CARD (owner)

| | option | what it does |
|---|---|---|
| A (void: keeper superseded) | Promote `nyisonext34` as is; ledger the G-5 row under NEXT-31. | C3a 2025 margin 0.4 → 1.7 pt, but ~0.5 pt of it is MLK over-pricing; C3c 2025 "passes" on mistimed hours. |
| **B (recommended)** | **Hold the keeper.** Keep this run as a probe. Next lane (NYISO-NEXT-35), re-based on `w0_nyiso_span`: an off-cap-scoped variant, measured mix only where gas ≤ oil and the parity cap untouched where it binds. PRECOMMIT + 5 shards. | Tests the half of the mechanism the evidence supports. The cell stays O. |
| C | Reject `dual_fuel_measured_oil_burn` for NYISO (R on G-5). | Closes the lever, including its off-cap half. |

Bundles (slim, registered) are on held PR #7053, branch `claude/nyisonext34-probe`: `results/calibration/nyisonext34_span`, `results/calibration/nyisonext34_2021`.
Full legs, including `dispatch/<year>_P1.parquet`, are on `claude/nyisonext34-20{21..25}` (transport only).
If the owner picks A, the promotion costs zero LP: `promote_keeper.py --iso NYISO --bundle results/calibration/nyisonext34_span --fold results/calibration/nyisonext34_2021=…`.
