# PRECOMMIT — closeout-PJM-w2 phase 0 (ZERO LP)

Lane `closeout-PJM-w2` (branch `claude/closeout-pjm-w2`, cut from `1e3e4177`), chartered by the close-out desk
(`session_01ERkBTm23ZAP4CTZnJVD9Ss`). Keeper `2026-10-03-closeout-pjm-nuc-keeper`
(bundle `results/calibration/closeout_pjm_nuc_full_span`), rubric v3.20. Owner direction 2026-10-03: *"There are
definitely uncalibrated ISOs that should be being rerun and tested."*

## 1. Queue position (plan §3.6, rulings §5.0)

| step | status at charter | source |
|---|---|---|
| 0a–0e censuses | DONE (wave 1) | `FINDING-pjm-closeout-wave1-censuses-2026-10-02.md` |
| 1 L1 coal reserve pool | CLOSED (no-op) | plan §3.6 |
| 2 L2 incremental HR | CLOSED (desk, #7073) | plan §5.0 desk rulings |
| 3 `gas_offer_margin_anchor_vintage` | R; re-test needs a corrected S4a/S3 PRECOMMIT; recorded near-inert on price (≤ 1 pp) | PJM shard cell |
| **4 L3 Elliott overlay** | **highest-ranked open step (desk pointer)** | plan §3.6 |
| COAL_BIT 2019–21 | OPEN, no mechanism (R-55/R-56) | §5.0 |
| CC_REGULAR 2022 | NOT CHARTERED (#7166) | §5.0 R-56 desk log |
| 2025 C3a/C3b | documented FAIL, no re-open (R-37) | §5.0 |
| zonal-loss double count | known boundary (R-61) | §5.0 |

R-26 ("Accept as data-limited", 2026-10-02) closed the temperature-curve route to Elliott (v1/v2). The step-4
form the desk names here — an **event-windowed add of measured published forced outage** (`gen_outages_by_type`,
on disk) — is a backcast outage overlay (rule 13's admissible class) and was never built; wave-1 census 0b failed
the *level* form, and flagged the *event-increment* form (the only variant that confirms) as a double-count risk.
This phase 0 measures the increment form's reach so the question is settled on numbers rather than wording.

## 2. Bars (taken unchanged from plan §3.6, fixed 2026-10-02 — none is set by this lane)

- **R1 (step 4 gate):** under the overlay, the Dec 23–24 2022 load-weighted mean model price can reach ≥ $800/MWh
  and C3b 2022 ≤ 0.20.
- **R2 (mechanism liveness, necessary for R1):** at least one Elliott-window hour falls below the `pjm_primary`
  requirement after the overlay (the ORDC $850/$300 steps and VOLL $2,000 are the only routes to ≥ $800 in this LP).
- **Reach form (the most favourable admissible one):** per hour, increment = (published RTO forced, lead 0 −
  its 20–22 Dec mean) − (model thermal unavailable − its 20–22 Dec mean), clipped ≥ 0, withdrawn from the keeper's
  in-LP thermal headroom; upper-bound price = walk of the residual stack (units with headroom, P1 offer `mc`)
  upward from the cleared price by the increment.
- **Kill:** R2 = 0 hours and the walk's Dec 23–24 mean < $800 ⇒ NOT CHARTERED; nothing built, no shard.
- **If it clears:** build default-off, PJM-scoped, with `--no-` flag, matrix row + every shard, 7 year-isolated
  shards; C1 PASS→FAIL declared none expected (2022 thermal energy moves only inside Dec 23–28); C3a/C3b in other
  years must be byte-identical (overlay windowed to 2022).

## 3. Next steps if the kill applies

Step 3 is admissible only on a corrected PRECOMMIT; its recorded price reach (≤ 1 pp) is checked against the
2022 need (C3a −16.7 % → ≥ −10 %) before any charter. Every other §3.6 row is DONE / CLOSED / ruled. If nothing
clears, the lane reports the queue exhausted with the owner asks.
