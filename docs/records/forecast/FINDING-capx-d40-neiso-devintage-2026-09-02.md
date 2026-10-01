# FINDING — capx D40: the NEISO adequacy requirement devintaged onto ISO-NE's published per-CCP Net ICR series (D33 R-A), one x-convention for position and curve (R-B) — BUILT, DEFAULT-OFF, LOYO-scored on committed artifacts: the denominator artifact is removed where the fleet is clean (+21.4 → −2.1 pts at the 2023 entry), the residual flips to the SHORT side D33 named, and the post-wave years are unscoreable until D37 re-solves on a fleet the armed screens produced

**Lane:** capx D40 (the repair lane D33 routed; charter: R-A and R-B as
`FINDING-capx-d33-neiso-position-2026-09-02.md` §4 specifies them, mirroring the
PJM published-FPR path, card C-A hold-last, rule-28 duties default-off, rule-22
LOYO before any default moves). Branch `claude/capx-d40-neiso-devintage-4spxmd`.
**ZERO solves, no fetch.** Every number below is read from a committed artifact
(the `neiso-2023-2027-crossover-rcrepair` evolution ledgers; the committed
demand-curve / icr-ara rows) or computed by evaluating HEAD's own committed
machinery — the new resolver, the new position transform, and the R2 vintage
curves — on those artifacts (instrument + rows committed under
`docs/handoffs/d40/`). No keeper / shard / marker / board / verdict / `neiso-t3`
write; the backcast namespace is untouched (§6). No new workflow.

## 0. Verdict (one paragraph)

**R-A and R-B are built, gated default-OFF behind one `ScenarioConfig` field
(`neiso_net_icr_requirement`), and behave exactly as D33 pre-stated.** Armed, the
NEISO requirement is ISO-NE's own published FCA Net ICR × (1 − f_DR) for every
delivery year 2020/21–2027/28 (the model's peak drops out — the auction's own
denominator), the last CCP's published Net-ICR/peak ratio × peak beyond FCA 18
(card C-A hold-last realised as a ratio, so the held bar scales with load), and
the composite before FCA 11; the CR-1 position is re-expressed on the published
curve's own x-convention (`pos_raw = f + (1 − f)·pos_net`). Consequence at the
screen grain, on the committed crossover ledgers: **+5,489 / +5,399 / +2,226 /
+658 / +530 MW** of requirement in 2023–2027 (the D33 artifact removed at the
published grain); the **clean 2023 entry position goes +21.43 → −2.13 pts** vs
the real FCA 14 and the **2024 entering position +17.83 → −3.87 pts** — the
denominator artifact is gone and what remains is the −2..−4-pt **SHORT** residual
D33 §3.2 named (census supply below the real cleared quantity); the floor's
admissible exit budget at the 2023 entry **collapses 6,263 → 774 MW (−88 %)**
and to **62 MW** at the 2024 entry, so the 2,878 MW exit wave the OFF artifact
produced is forbidden under the arm. **The rule-22 LOYO, scored honestly on
committed artifacts, is 11/12 folds PASS and 1 FAIL** — and the failing fold
(entering-fleet position, held-out 2025) is measured on a fleet that is the OFF
artifact's own product (the post-wave 2025 fleet), as are the 2024/2025
post-evolution rows where the arm reads 8–12 pts short. **Capacity revenue on
HEAD's vintage curves OVER-pays at the corrected positions in every year
($55.20 vs real $24.01 at the 2023 entry)**, because a −2-pt short residual on
ISO-NE's steep MRI curve is worth +$30/kW-yr — the supply-side wedge is now
visible at full magnitude, and it is the next identified object (R-C), not this
lever's. **Recommendation (the owner arms): arm the lever for the D37 NEISO T1-H
re-run — the only instrument that can score 2024/2025 on a fleet the armed
screens produced — and leave the DEFAULT off until that armed re-solve
LOYO-scores clean.** Sign discipline held throughout (§5): nothing was sized by
any residual; the published series is the identification, full stop.

## 1. What landed (the resolver + registry data path)

| surface | change |
|---|---|
| `config/capacity_market.py` | `NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"]` — FCA-vintage Net ICRs for CCPs 2020/21–2027/28 (34,075 / 33,725 / 33,750 / 32,490 / 33,270 / 31,645 / 30,305 / 30,550 MW), digitized from the committed `demand-curve/neiso/neiso.csv` `reliability_requirement` rows and reconciled against them byte-for-byte, set-equal, by `TestNeisoNetIcrRequirement`; `NET_ICR_HOLD_LAST_RATIO_BY_ISO["NEISO"] = 29,855 / 26,417` (ARA 2 of CCP 2027/28, the committed icr-ara extract), reconciled to that extract by test. |
| `model/capacity_evolution/retirements.py` | `net_icr_requirement_armed(config, iso)` — the ONE gate predicate (rule 19) both halves consult: the default-OFF flag AND a registry entry (NEISO alone, rule 25). `resolve_published_net_icr_mw(config, iso, peak, year)` — the PJM `resolve_forecast_pool_requirement` pattern: in-table CCP → absolute MW; strictly beyond the last CCP → `peak × hold ratio`; pre-table, in-gap, `year=None`, unarmed, off-registry → `None`. `resolve_adequacy_requirement_mw` gains construction 0: `Net ICR × (1 − f_DR)` when that resolves, else the unchanged FPR / composite paths. |
| `model/capacity_evolution/adequacy.py` | `curve_convention_position(config, iso, pos)` — R-B: `f + (1 − f)·pos` when armed; `capacity_reserve_position` returns through it. The floor and backstop are untouched (they test `firm ≥ requirement`, convention-invariant). |
| `config/scenarios.py` | `neiso_net_icr_requirement: bool = False` (placed at the END of the field list so no matrix `:line` anchor shifts); registered in `_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` and `TIER_TAGS` at 1 (pinned default key `603c2498bf71d21d` **unmoved**, measured; an armed NEISO config keys distinctly `62923af0… → 6a3958c0…`); coerced to the dataclass default in a plain backcast, kept in a hindcast (`mode="forecast", hindcast=True`). |
| `scripts/run_capacity_hindcast.py` | `--neiso-net-icr-requirement` (BooleanOptionalAction, `None` inherits the default) threaded into the config and the run-record provenance (`FromConfig(cast=bool)`), so D37 can arm it and the arm lands in `run_config.json` (rule 24). |
| rule 28 | base row `neiso_net_icr_requirement` (mode F, cat capacity) + a cell in all six shards: NEISO `cell "." / fc "O"` with the evidence below; the five others `.` with the rule-25 reason each. `check_mechanism_matrix.py --base origin/main` green (its `--fix-anchors` repaired the `:line` digits the two registry insertions shifted — digits only). |
| tests | `tests/unit/model/test_capacity.py::TestNeisoNetIcrRequirement` — 12 tests: CSV/extract reconciliation, default-off byte-identity, absolute in-table, pre-table/None fall-through, ratio hold-last (scales with peak; sits +0.22 % over the composite; a series with no hold ratio holds nothing), in-table gap never bridged, the R-B algebra incl. the D33 row (1.2594 → 1.2366), end-to-end position with the rule-14 sign, other ISOs inert with the flag armed, backcast coercion / hindcast keep / cache key. |

**Choices the charter left open, decided and recorded:**

- **FCA vintage, not the ARA restatement, for the in-table series.** The R2
  vintage curves normalise their x by the FCA Net ICR
  (`_NEISO_MRI_CLEARING_POINTS`: cleared/Net ICR per FCA), so R-B's "one
  denominator object on both sides of `evaluate_demand_curve`" is satisfied
  only by the FCA series. The ARA-3/ARA-2 restatements (30,050 / 29,855) are
  later same-cycle vintages of the last two CCPs; they are not mixed in, and
  the last one supplies the hold-last ratio instead.
- **Hold-last is a RATIO, not a frozen MW.** PJM's held object (the FPR) is a
  ratio to peak. An absolute Net ICR held flat over 2028–2050 against a growing
  peak is a collapsing margin by construction and fails the rule-13 forward
  test ("would it respond to changed conditions?"); the last CCP's published
  Net-ICR/50-50-peak pair (ARA 2 of 2027/28, 1.1301) is the same construct the
  composite already uses, re-anchored on the LAST CCP. Beyond the table the
  armed requirement is `1.0022 ×` the composite — the golden's 2028+ years are
  essentially untouched (D33 §7's exposure split, confirmed §3).
- **DR netting under the series.** `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO
  ["NEISO"]` is *defined* as DCR CSO ÷ Net ICR (its citation block), so the
  requirement is `Net ICR_ccp × (1 − f)` — the netted MW reproduces ISO-NE's own
  supply-side DCR counting at the published quantity. The per-CCP DCR CSO
  series (R-C, intake §6(b) of D33) replaces `f × Net ICR` when it lands; it
  is not fabricated here.
- **One lever for R-A and R-B**, as D33 specified ("land WITH R-A"): the R-B
  term is algebraic in `f` (no data), the two share one gate predicate, and the
  decomposition (§2) reports the halves separately so neither hides the other.
- **CCP label.** `capacity_deliverability.resolve_delivery_year` keys its
  planning-year set on the clean-partition alias `ISONE` and returns a bare
  calendar label for the model name `NEISO`; the resolver builds
  `"YYYY/YYYY+1"` itself (documented in its docstring). Not repaired in that
  helper — out of this lane's seam and a latent no-op today (no NEISO caller).

## 2. Consequence at the screen grain (committed crossover ledgers, zero solves)

Instrument: `docs/handoffs/d40/devintage-screen-grain-2026-09-02.py` (rows in
the sibling JSON; stdout committed). OFF = HEAD (the composite, net convention,
what D28/D33 reported); ON = the armed lever exactly as `capacity_reserve_position`
would return it (R-A denominator + R-B transform); real = cleared ÷ Net ICR, the
FCA's own convention. `firm_enter` is what the year's screens priced;
`firm_post` is the fleet in service in the delivery year (comparable to the real
cleared quantity).

**Requirement (net convention, MW)**

| yr (FCA) | peak | req OFF | req ON | Δ | Net ICR | firm enter | firm post |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 (14) | 23,475 | 24,147 | 29,636 | **+5,489** | 32,490 | 30,410 | 30,410 |
| 2024 (15) | 24,255 | 24,949 | 30,347 | **+5,399** | 33,270 | 30,410 | 27,532 |
| 2025 (16) | 25,898 | 26,639 | 28,865 | +2,226 | 31,645 | 27,532 | 26,775 |
| 2026 (17) | 26,235 | 26,985 | 27,643 | +658 | 30,305 | 26,775 | 28,308 |
| 2027 (18) | 26,576 | 27,336 | 27,866 | +530 | 30,550 | 28,308 | 30,019 |

**Positions vs the real FCA** (ON on the curve's raw convention, R-B applied;
"R-A only" = the net-convention position without R-B, for the split)

| yr (FCA) | real | OFF post | gap | ON post | gap | R-A only | OFF enter | gap | ON enter | gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 (14) | 1.0451 | 1.2594 | **+21.43** | 1.0238 | **−2.13** | 1.0261 | 1.2594 | +21.43 | 1.0238 | **−2.13** |
| 2024 (15) | 1.0406 | 1.1035 | +6.29 | 0.9154 | −12.52 | 0.9072 | 1.2189 | +17.83 | 1.0019 | **−3.87** |
| 2025 (16) | 1.0368 | 1.0051 | −3.17 | 0.9339 | −10.29 | 0.9276 | 1.0335 | −0.33 | 0.9579 | −7.89 |
| 2026 (17) | 1.0351 | 1.0490 | +1.39 | 1.0220 | −1.32 | 1.0241 | 0.9922 | −4.29 | 0.9714 | −6.38 |
| 2027 (18) | 1.0329 | 1.0982 | +6.52 | 1.0705 | +3.75 | 1.0773 | 1.0356 | +0.26 | 1.0145 | −1.85 |

Readings, each measured:

1. **Where the fleet is clean, the artifact is gone.** 2023 is the base year
   (no evolution; entering = post) and its fleet owes nothing to the OFF
   requirement: +21.43 → −2.13 pts. The 2024 ENTERING fleet is the same clean
   census (the wave executes in 2024): +17.83 → −3.87 pts. These are the two
   rows D33's decomposition predicted (+23.8 / +22.5 pts of requirement term)
   and they land within its brackets.
2. **The residual flips to the SHORT side, at the magnitude D33 §3.2 named.**
   Under the R-B convention the model's 2023 supply is 30,410 firm + 2,854 DR
   (= f × Net ICR) = 33,264 MW vs the real cleared 33,956 — **−692 MW**; D33
   measured −1,221 MW with the composite-derived DR (2,325); the difference is
   the DR construction, not the fleet. Either way the census is BELOW the
   market's cleared quantity — the accreditation numerator is not long, and
   R-C (the DR / import side-car series) is the next identified object.
3. **The post-wave rows are the OFF artifact's product and cannot be scored
   here.** The 2024/2025 post-evolution fleets embed the 2,877.7 MW executed
   exit wave (2,171.0 retirement + 706.7 Mystic derate, ledger-exact), which
   the screens produced against the too-small OFF requirement. Under the arm
   that wave is forbidden (§2 budget table): the ON positions of 0.915/0.934
   price a fleet that would not exist under the arm. The 2026/2027 rows
   inherit the rebound the same way. This is exactly the D33 §5 caveat, now
   measured: **a re-solve is the instrument, and it is D37's.**
4. **R-B is third-order and in the direction D33 sized**: at the 2023 row the
   transform moves 1.0261 → 1.0238 (−0.23 pts; the composite-era mis-pairing
   was +2.3 pts at 1.2594 because the term grows with surplus).

**Capacity revenue on HEAD's vintage curves ($/kW-yr)**

| yr (FCA) | OFF post | ON post | OFF enter | ON enter | real clearing |
|---|---:|---:|---:|---:|---:|
| 2023 (14) | 0.00 | **55.20** | 0.00 | **55.20** | 24.01 |
| 2024 (15) | 0.00 | 167.18 | 0.00 | 100.88 | 31.33 |
| 2025 (16) | 81.19 | 148.80 | 34.30 | 148.80 | 31.09 |
| 2026 (17) | 15.11 | 52.64 | 116.14 | 153.13 | 31.08 |
| 2027 (18) | 0.00 | 0.00 | 38.20 | 79.95 | 42.96 |

5. **The $0-at-long readings are gone, and the curve now OVER-pays.** At the
   clean 2023 entry the arm pays $55.20 against a real $24.01 — a −2.1-pt
   short residual on the MRI curve's steep inner segment (net-CONE at 1.0 →
   0.39 × net-CONE at 1.033) is worth +$31/kW-yr. D33 §5 quoted $28 at the
   same row; that figure evaluated the NET-convention position on a bracketed
   DR midpoint (3,300 MW), and is superseded by this measured $55.20 at the
   R-B position with the registry's own `f × Net ICR` DR. The direction is the
   pre-stated one (revenue UP in the long years); the magnitude overshoots the
   market because the model sits SHORT of it — the supply side, again.
6. **Sign discipline (rule 14):** every movement is in the direction D33
   pre-stated — requirement UP, position SHORTER, revenue UP in the $0 years,
   the wave budget DOWN — and none of it was sized to any residual.

**Floor exit budget at entry (`firm_enter − requirement`, MW) and floor binding
on the as-solved post fleet**

| yr | budget OFF | budget ON | ratio | floor binds post-fleet OFF → ON |
|---|---:|---:|---:|---|
| 2023 | +6,263 | **+774** | 0.12 | no → no |
| 2024 | +5,461 | **+62** | 0.01 | no → **yes** (as-solved fleet 27,532 < 30,347) |
| 2025 | +893 | −1,333 | — | no → **yes** |
| 2026 | −210 | −868 | — | no → no |
| 2027 | +972 | +442 | 0.45 | no → no |

7. **The S-123 lesson holds in reverse.** A requirement repair RELEASES or
   WITHHOLDS budget; it does not choose composition. Here it withholds: the
   2024 wave's admissible size drops from 5,461 MW to 62 MW, and on the
   as-solved post fleets the floor would have RETAINED ~2.8 GW in 2024 and
   ~2.1 GW in 2025 (firm_post below the ON requirement). WHICH units the floor
   keeps is the `_floor_retention_merit` key's decision — the D17/D27 finding
   ("the floor-retention key owns exit composition") applies unchanged, and
   D37 measures it.

**Hold-last edge.** At the 2027 ledger peak (26,576 MW): 2027 ON 27,866 MW
(absolute FCA 18) → 2028 ON 27,396 MW (held ratio), a **−1.69 %** step; 2028
OFF (composite) 27,336 MW; **ON/OFF beyond the table = 1.0022**. The lever
primarily repairs the crossover/hindcast window and leaves the golden's
2028–2050 requirement within a quarter of a percent of HEAD — D33 §7's
exposure split, measured.

## 3. The rule-22 leave-one-year-out score (full magnitude)

The lever carries **zero fitted parameters** (the published series is the
identification), so a fold's "training" decision is the sign test on the two
training years — does arming reduce the absolute error in BOTH? — and the
held-out year is scored on the same criterion. A fold FAILS when a train-armed
lever degrades the held-out year: in-sample gain with held-out degradation is
overfitting, not skill. Scored over the training window 2023–2025 only; the
forward years 2026/27 are reported above, never scored.

| metric | held-out | train arms? | held-out \|err\| OFF → ON | fold |
|---|---|---|---:|---|
| position (post fleet) | 2023 | no | 0.2143 → 0.0213 | PASS |
| position (post fleet) | 2024 | no | 0.0629 → 0.1252 | PASS (held-out degrades) |
| position (post fleet) | 2025 | no | 0.0317 → 0.1029 | PASS (held-out degrades) |
| position (entering fleet) | 2023 | no | 0.2143 → 0.0213 | PASS |
| position (entering fleet) | 2024 | no | 0.1783 → 0.0387 | PASS |
| position (entering fleet) | **2025** | **yes** | **0.0033 → 0.0789** | **FAIL** |
| capacity revenue (post) | 2023 | no | 24.01 → 31.19 | PASS (held-out degrades) |
| capacity revenue (post) | 2024 | no | 31.33 → 135.85 | PASS (held-out degrades) |
| capacity revenue (post) | 2025 | no | 50.10 → 117.71 | PASS (held-out degrades) |
| capacity revenue (enter) | 2023 | no | 24.01 → 31.19 | PASS (held-out degrades) |
| capacity revenue (enter) | 2024 | no | 31.33 → 69.54 | PASS (held-out degrades) |
| capacity revenue (enter) | 2025 | no | 3.21 → 117.71 | PASS (held-out degrades) |

**12 folds, 1 FAIL — and what the table actually says, stated plainly:**

- **The position metric on the entering fleet is the one clean LOYO** (the
  entering fleet of 2023 and 2024 is the un-evolved census; only 2025's is
  post-wave). It trains to ARM on {2023, 2024} — both improve by 17–19 pts —
  and the held-out 2025 DEGRADES (−0.33 → −7.89 pts). **That is the failing
  fold, reported at full magnitude.** Its mechanism is measured, not argued:
  the 2025 entering fleet is 27,532 MW because 2,878 MW exited in 2024 against
  a 5,461 MW OFF budget that the arm reduces to 62 MW; OFF's −0.33 pts is two
  errors cancelling (a requirement 5,399 MW too small against a fleet the
  same artifact thinned), and the arm removes one of them. A fold measured on
  a fleet the OFF arm produced cannot certify the ON arm either way.
- **The post-fleet position folds never train to ARM** (2024/2025 degrade
  in-sample for the same post-wave reason), so no fold fails, and no
  in-sample case for arming is made on them either.
- **The capacity-revenue metric degrades in EVERY year, in-sample and out.**
  This is the honest headline of the revenue leg: at the corrected positions
  HEAD's curves over-pay the market in every year, because the model's
  position is short of the real one and ISO-NE's curve is steep there. The
  lever removes the $0 readings D28 chartered against, and exposes a
  supply-side wedge it was never identified to close.

**What this LOYO can and cannot certify.** It certifies that the denominator
artifact is removed at the published grain where the fleet is uncontaminated
(the 2023 entry, the 2024 entry) and that the lever's sign is as declared. It
cannot certify the 2024/2025 delivery-year positions or any revenue level,
because those rows price a fleet the artifact produced. **The certifying
instrument is a re-solve with the arm on** — the D37 NEISO T1-H — scored LOYO
on the fleet the armed screens produce. This lane does not run it (charter).

## 4. Arming recommendation (the owner arms; this lane recommends)

**Recommend: ARM for the D37 measurement posture; do NOT flip the default.**

- *For arming (structure, rules 1/14):* a published per-CCP requirement series
  over a single-vintage composite is the more faithful market structure by
  construction — the same reason the PJM FPR path exists — and its sign and
  magnitude landed exactly where D33 pre-stated them. Rule 1 forbids rejecting
  a structurally-correct mechanism because a residual moved the wrong way,
  and the revenue-leg "wrong way" here is the supply-side wedge becoming
  visible, not the lever misbehaving.
- *Against a default flip now (rule 22):* the LOYO on committed artifacts has
  one failing fold and a revenue leg that degrades in every year; both are
  measured on artifact-contaminated fleets, but "unscoreable" is not "clean",
  and rule 22 puts the burden on a clean held-out score BEFORE a default
  moves. That score exists only after an armed re-solve.
- *The consequence to expect in D37, pre-stated so it cannot be traded:* the
  2024 wave shrinks to ≤ 62 MW of admissible exit (plus whatever the floor
  retains), the dip-year over-payment ($116 entering 2026) does not form,
  storage/CT entry in 2026 re-times, and the terminal position lands nearer
  1.00–1.03 than 1.10. Retirements HARDER, entry EARLIER, the oscillator
  damped at its source. If instead D37 measures the 2023 entry paying ~$55
  against a market that paid $24 and a 2024 floor retaining ~2 GW of units
  the real market de-listed, that is the R-C / de-list-wedge object
  (D33 §3.2, D28's clearing half) — route it, do not tune this lever to it.

## 5. Governance attestation

- **Rule 13/14/23:** the identification is the committed published series
  (FCAs 11–18) and the committed ARA-2 pair; every constant is reconciled to
  its committed source row by test; nothing anywhere was sized from a
  residual; the sign was pre-stated by D33 and is measured in that direction.
- **Rule 22:** LOYO scored over 2023–2025 on committed artifacts BEFORE any
  default moves (§3); no out-of-training year solved, scored or registered;
  the holdout freeze is not implicated (nothing solved). The 2026/27 crossover
  forward rows are reported, never scored.
- **Rule 24:** the gate is a `ScenarioConfig` field, threaded to
  `run_config.json` and the hindcast run record; the two registries are
  cited constants (the S-123 registry-constant pattern).
- **Rule 25:** NEISO only by construction — the registry holds one ISO and
  the predicate requires an entry; measured inert on PJM/MISO/ERCOT with the
  flag armed (test). PJM's FPR path is byte-identical.
- **Rule 27:** Fable session; local edits, exact on-disk bytes pushed; ≥300-line
  files (`capacity_market.py`, `scenarios.py`, `retirements.py`, `adequacy.py`,
  `run_capacity_hindcast.py`, `test_capacity.py`, the matrix base) blob-verified
  against the remote after push (record in the PR/commit trailer).
- **Rule 28:** row + six cells in the same PR, NEISO `fc: O` with this
  finding as evidence; `check_mechanism_matrix.py --base origin/main` and
  `check_cache_key_registration.py --base origin/main` both green. Off-queue
  by charter: NEISO's backcast lever queue is CLEARED (§5.6) and this is a
  forecast-lane requirement repair routed by D33 §4.
- **Backcast blast radius (charter STOP condition): NOT triggered.** Swept:
  `resolve_adequacy_requirement_mw` is reached only from `evolve_fleet`
  (reliability floor, backstop, CR-1 position), `check_forecast_invariants.py`
  (I7/I12, forecast lane) and `validate_capacity_prices.py` (a forecast probe);
  a backcast solves every year with `fleet=None` and never evolves, and the
  field is coerced to its default in a plain backcast. Pinned default cache
  key `603c2498bf71d21d` unmoved (measured); NEISO backcast keys unmoved
  (the field is dropped at its default).
- **Collision:** D39 (entry screens, docs-only), D41 (CCS constants), D32
  (MISO) — no shared surface; the matrix base row is the one deliberately
  non-parallel edit (rule 28c), inserted next to the D31 row; the
  `--fix-anchors` digit repair touched no cell or note.
- **Tests:** `tests/unit/model`, `tests/regression`, `tests/unit/config`,
  `tests/unit/scripts` lanes green at HEAD of this branch; the 12 new tests
  green; ruff clean.

## 6. Handoff to D37 (explicit)

**D37 input from D40: the lever `neiso_net_icr_requirement` is BUILT and
DEFAULT-OFF; arm it on the NEISO T1-H re-run with
`scripts/run_capacity_hindcast.py … --neiso-net-icr-requirement` (distinct cache
key; the arm lands in `run_config.json` and the run record). Score the armed
run's positions and capacity revenue LOYO within 2023–2025 against the real FCA
rows (the §2 tables are the OFF baseline and the committed-artifact ON bound);
the pre-stated expectations are §4's. If the armed run's 2023 entry still pays
~$55 against $24 and the 2024 floor retains ~2 GW, that is the supply-side
wedge (R-C DR/import side-cars; the qualified-vs-cleared de-list wedge) —
route it to the director as the next object; do not tune this lever.** The
default flip is an owner decision on D37's clean LOYO, not on this finding.
