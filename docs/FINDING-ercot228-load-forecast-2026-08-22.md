# FINDING — ercot-228: F4 load-forecast conservatism — **DATA-ABSENT** (no public 2023 DA-forecast vintage is retrievable; the only archive that has one is the owner-declined credentialed API)

**Session ercot-228 (spoke of the ercot-226/227 owner program; the dispatch
IS the owner — Amendment 3, "Proceed with all the factors to test not just
1 keep going"), 2026-08-22, branch `claude/ercot-2023-summer-scarcity-9lg3nm`
at `705ec9b`. Factor F4 ONLY. Committed record:
`results/calibration/ercot228_probe_f4.json` (full attempt log). Keeper
untouched: `2026-08-20-ercot223-arm-eventrelease`.**

## 1. The verdict

**DATA-ABSENT.** Phase A of the ercot-228 charter — retrieve any public
2023 vintage of the ERCOT day-ahead load forecast (NP3-560-CD by Forecast
Zone / NP3-561-CD by Weather Zone) — fails on every ERCOT-published
surface, and per the dispatch that is the honest terminal verdict: no
curation, no `PRECOMMIT-ercot228` mechanism pin beyond the dispatch's own,
no `ercot_load_forecast_margin` build, no solve. The ercot-226 F4
REFUTED-P0 prior (`ercot226_helddepth_phase0.json` F4 row) is thereby
*upgraded in kind*: what was "no measured series in the repo" is now "no
measured series retrievable from the public record at all" — measured this
session, URL by URL.

## 2. The data story (every attempt; full URLs + payloads in the probe JSON)

| # | route | outcome |
|---|---|---|
| 1 | `mis.ercot.com/misapp/GetReports.do` reportTypeId 12311/12312 | 302 → SiteMinder market-participant **client-certificate** wall; TLS handshake fails without a participant cert (same wall fetch_ercot_as_reports.py re-verified 2026-07-10) |
| 2 | `www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=12311` | live, 346 docs — a **7-day rolling window** (2026-08-15 → 2026-08-22; ExpiredDate = publish + 7 d). The right edge always tracks "now": 2023 will never re-enter it |
| 3 | same, reportTypeId 12312 | identical 7-day window |
| 4 | ERCOT's own EMIL catalog (`all-emil-items-search.json`) | advertised `misDisplayDuration_i = 7` for both products; a sweep of **every** load-forecast catalog item finds only rolling windows: NP3-562/565/566-CD + GEN-55-CD (7 d), NP8-927/928/929/930 accuracy reports (31 d — metrics, not vintages), NP12-753 settlement extract (31 d), NP4-159-CD distribution factors + NP3-778-M 36-month monthly (365 d — not DA vintages). **None reaches 2023** |
| 5 | `api.ercot.com/api/public-reports/archive/NP3-560-CD` | **401** missing subscription key. This credentialed archive is the one surface that does span the 2023 vintages — and it requires the data.ercot.com key the owner **closed permanently 2026-07-05** ("owner will not procure a data.ercot.com key", `docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E / open-items row 3). No credentials in the session env (swept) |
| 6 | any other ERCOT-published bulk archive | none exists: `gridinfo/load` carries current forecasts + actual-load archives only; the data-product pages front the same 7-day MIS listing |

## 3. What was pinned but never exercised

The dispatch pinned the mechanism form in advance and it is recorded
unbuilt (probe JSON `pinned_but_unexercised`): `ercot_load_forecast_margin`
(bool, default False, backcast-only), `margin_t = max(0, forecast_mw(t) −
actual_load(t))` added to the `ercot_ordc_total_reserve` requirement before
its MCL floor — RHS-only, zero LP growth, zero fitted scalars; DAM-close
vintage rule (last issuance before 10:00 CPT of the prior day); sign
UNCERTAIN with both stories stated. **No ScenarioConfig field was created**
— the matrix row records the adjudication, not an armed mechanism.

## 4. The reopen route (owner action, not a session action)

The WS-E HSL precedent (2026-07-06) applies exactly: the owner manually
downloading the 2023 NP3-560/561-CD archive zips through the
data.ercot.com Data Access Portal UI ("Search History") is an
already-authorized mechanism distinct from procuring an API key. If those
files land under `data/raw/ercot/`, Phases B–C of the ercot-228 charter
execute as precommitted. Two things carry over unchanged into any such
resumption: the ercot-216 §5 standing prior (reality's own ORDC ≈ $1 at
the missed hours) and the precommit §1 channel doctrine — improvement
carried by the model adder rather than λ fails adoption whatever it does
to C3a.

## 5. Session hygiene

W-2 honored: nothing dashboard-registered; the committed JSON + this
FINDING are the record. No keeper, F1/F1b/F3, or ercot226_* artifact was
touched beyond reading. Matrix: base row `ercot_load_forecast_margin`
added with the ERCOT cell **O** (open — blocked on an intake dependency,
the `demand_growth_vintage` CAISO-cell precedent for "blocker is an
intake, not a verdict"), every other shard `·`. Env verified at the keeper
pins (highspy 1.15.1 / pandas 3.0.5 / pyarrow 25.0.1 / numpy 2.4.6 /
scipy 1.17.1) though no solve ran.
