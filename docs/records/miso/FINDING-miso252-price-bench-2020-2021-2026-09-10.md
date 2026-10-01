# FINDING — miso-252: MISO 2020/2021 price comparison. Hourly LMPs need the API key; the MMU's published annual prices are reachable, and they say 2020 is materially over-priced

```
SESSION : miso-252
ISO     : MISO
ASK     : "Go get 2020 and 2021 lmps for comparison"
RESULT  : hourly LMPs BLOCKED (verified, §1). A published annual substitute WAS obtained (§2),
          and it produces a usable comparison with an honest basis band (§3).
HEADLINE: 2021 is FINE (-2.7% to +12.5%, inside the in-sample range).
          2020 is NOT (+26.9% to +46.8%, ~4x the worst in-sample year).
```

## 1. Hourly LMPs for 2020/2021 are blocked on `MISO_PRICING_API_KEY` — now verified, not inherited

Every public route was tested today rather than taken on trust:

| route | result |
|---|---|
| `docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv` | **404** for 2020-07-15 and 2021-07-15. Retention floor re-measured: **2022-12-31 → 404, 2023-01-01 → 200** — unchanged from the 2026-07-09 verification in `fetch_miso_hub_lmp.py`, so this is a fixed floor, not a moving window. |
| five further archive shapes (`.zip`, `_dalmp`, `_da_exante_lmp`, `_rt_lmp_final`, `archive/…`) for 2021 | **404** on all five |
| MISO Data Exchange Pricing API `apim.misoenergy.org/pricing/v1` | **401** — *"Access denied due to missing subscription key"*, keyless and with an empty header |
| `MISO_PRICING_API_KEY` in env or `.env` | **absent** |
| `misoenergy.org` Market Report Archives page | **403** to any client (bot protection), incl. a browser UA |
| anything already in `data/raw` carrying MISO 2020/2021 prices | **none** |

`data/raw/lmp-data/MISO/` holds **94 chunk files for 2022** and none for 2020/2021 — 2022 had already
aged off the docs window, so a previous session staged it **through the API**. The key therefore
exists somewhere; it is simply not in this environment.

**This is the single unblocker for C3a/C3b/C3c on 2020 and 2021.** With it:
`fetch_miso_hub_lmp.py --years 2020 2021` then `derive_miso_hub_lmp.py`, then re-score the folded
rungs **in place** — no re-solve, the bundles are committed.

## 2. What IS reachable: the MMU's published annual real-time energy price

Potomac Economics (MISO's IMM) publishes the annual figure in each State of the Market report.
Fetched today, and **read from the MISO volumes** — the first 2021 candidate URL turned out to be
the **ERCOT** SOM and was discarded before any number was taken from it:

| year | figure | source |
|---|---|---|
| 2020 | **$22/MWh** | `2020-MISO-SOM_Report_Body_Compiled_Final_rev-6-1-21.pdf` p7 — *"a 16 percent decrease in real-time energy prices throughout MISO, which averaged $22 per MWh in 2020"* |
| 2021 | **$39/MWh** | `2021-MISO-SOM_Report_Body_Final.pdf` p7 — *"real-time energy prices throughout MISO, which averaged $39 per MWh"* |
| 2023 | $37/MWh | `2023-MISO-SOM_Report_Body-Final.pdf` p7 |
| 2024 | $31/MWh | `2024-MISO-SOM_Report_Body_Final.pdf` p7 |

(The 2025 volume states the **all-in** price, $53/MWh, in the equivalent sentence — a different
quantity, so it is not used as a basis point.)

## 3. THE BASIS PROBLEM, AND HOW IT IS BOUNDED RATHER THAN IGNORED

The SOM figure is a MISO-wide real-time average rounded to whole dollars; the repo's C3a bench
(`actual_lmp_hourly_MISO.parquet`) is the **hub-mean** hourly series. These are **not the same
quantity**, and the gap is not constant:

| year | SOM | hub bench RT mean | SOM / bench |
|---|---:|---:|---:|
| 2023 | $37 | $31.79 | **1.164** (+16.4 %) |
| 2024 | $31 | $30.80 | **1.007** (+0.7 %) |

So the SOM runs **+0.7 % to +16.4 % above** the hub bench, and a single year's spread (16 pp) is
wider than the model's own in-sample error. **The SOM figure is therefore NOT a substitute bench and
must not be fed to the C3a scorer** — it is an order-of-magnitude comparison with the band carried
explicitly.

**Comparison, with the band applied:**

| year | model LW price | SOM | vs SOM | implied hub-bench | **model vs implied bench** |
|---|---:|---:|---:|---:|---:|
| **2020** | $27.74 | $22 | +26.1 % | $18.90 – $21.86 | **+26.9 % to +46.8 %** |
| **2021** | $37.69 | $39 | −3.4 % | $33.51 – $38.74 | **−2.7 % to +12.5 %** |

In-sample C3a, for scale (model vs the same hub bench, all PASS):

| 2023 | 2024 | 2025 |
|---:|---:|---:|
| +8.4 % | +6.8 % | −0.5 % |

## 4. What this says

* **2021's price level is not a defect.** Its band (−2.7 % to +12.5 %) straddles the in-sample range
  (−0.5 % to +8.4 %). Whatever is wrong with the 2021 rung — and its C1 miss on `CC_REGULAR` is
  −32.06 TWh — it is **not** a price-level error.
* **2020's price level IS a defect, and it is large.** Even at the most generous end of the basis
  band the model is **+26.9 %** high, against a worst in-sample year of +8.4 %. The most pessimistic
  end is +46.8 %. No plausible basis correction closes a gap that size.
* **This qualifies the "2020 is a clean year" reading.** miso-251 recorded 2020 as
  `CALIBRATED-WITH-CAVEATS` with **ZERO fails and target grade 5/5** — but its sole caveat reason
  was *unscored price criteria*, i.e. the 5/5 was earned on a rubric with C3a/C3b/C3c **missing**.
  On this evidence 2020 would very likely **FAIL C3a** once priced. The grade did not measure what
  it appeared to measure, and 2020 should not be quoted as the recipe's clean out-of-regime year
  until it has a real price bench.

**Rule 30(c) is unaffected:** these are held-out years; they cannot certify or decertify MISO, whose
determination stays the train-tier `CALIBRATED`. This is reported, not absorbed.

## 5. Provenance

The four SOM PDFs were fetched to the session scratchpad, not committed — `data/raw/MISO/`'s posture
is payload-gitignored with only `README.md` + `SHA256SUMS.txt` tracked (BLOAT-B-2), and the two new
volumes are **hand-read citation sources** exactly like the three already listed there. Their URLs
are recorded in §2 so any reader can re-fetch and re-verify the quoted sentences.

## 6. Owner action

**Supply `MISO_PRICING_API_KEY`** and 2020/2021 gain a real hourly bench with no re-solve. That is
the only thing standing between these two rungs and a scored C3a/C3b/C3c — and, on §4's evidence,
the 2020 result would be worth knowing.
