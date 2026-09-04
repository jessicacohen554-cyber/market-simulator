# PJM capacity-market-auction-supply (RPM BRA Demand Resource offered / cleared, UCAP)

`pjm.csv` — the PJM RPM Base Residual Auction's Demand Resource (DR) offered
and cleared quantities in UCAP MW per delivery year, 2020/21 through 2027/28,
transcribed by capx D48 (2026-09-04) from the BRA Results reports (payloads
NOT committed — the corpus posture for publication PDFs; sha256 identity
records and re-fetch URLs below).

**Single-source series.** Every row is read from ONE table — the 2027/2028
BRA Report's Table 5 ("Generation, DR and EE Resources offered and cleared
in the RTO translated into UCAP"), PJM's own trend table carrying every
delivery year since 2017/18 in one place — and cross-checked against the
per-year reports' own Demand Resources sections / Table 3A / Table 6 /
Table 8 (each cross-check is recorded in the row's `vintage` column). One
restatement is recorded, not reconciled: the 2024/25 cleared DR reads
7,992.7 in the trend table where the 2024/25 report printed 7,985.2 (a 7.5 MW
difference). The 2025/26 offered value 6,084.8 is reproduced exactly from
the 2025/26 report's Table 8 as DR Annual 5,962.5 + the 122.3 MW Summer DR
matched with Winter capability.

**RPM-only.** The series is what OFFERED INTO / CLEARED IN the BRA. DR
nominated in FRR capacity plans is NOT in it (2026/27: the 2026/27 BRA
Report Table 6 total of 5,795 MW UCAP — the existing
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]` operand — adds 264.4 MW
of FRR-committed DR to this series' 5,530.6). A consumer counting the RTO's
whole DR base therefore under-credits by the FRR share (conservative,
the PRD-exclusion precedent).

**Consumer.** `DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO["PJM"]`
(`src/market_sim/config/capacity_market.py`) carries the OFFERED rows —
the market's recurring qualified-DR supply census, the analogue of the
model's installed-fleet census — behind the default-OFF
`ScenarioConfig.pjm_demand_response_supply` gate, reconciled to this file
byte-for-byte by `tests/unit/model/test_capacity.py`. The CLEARED rows are
validation observables (rule 13 `[R-MEASURED]`, the schema header's
posture): never a target.

## Source identity (sha256, fetched 2026-09-04 through the session proxy)

| delivery year | file (re-fetch URL) | sha256 |
|---|---|---|
| 2021/2022 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2021-2022/2021-2022-base-residual-auction-report.ashx | `800e4b3a86058ad80fc9be55e530c0e78f931471cd23ebaa2c3cf8514c8720f4` |
| 2022/2023 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2022-2023/2022-2023-base-residual-auction-report.ashx | `ca9d51b9246e988e24d0beb3bae23d201fac6ecf7116ddad8575dc4e1e28b69a` |
| 2023/2024 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2023-2024/2023-2024-base-residual-auction-report.ashx | `ef82660e4204c4148d7402ff80ff1ac48ee830c117b30f4c336b6b54e1c0f51f` |
| 2024/2025 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2024-2025/2024-2025-base-residual-auction-report.ashx | `00ddf7c9c8fcbda69d251df76db00720a633156afd27454e8fcf2c05a1807816` |
| 2025/2026 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2025-2026/2025-2026-base-residual-auction-report.ashx | `6d47fb09d2052b102279ecf0e8748a4186a93e37d11bdf5b1bbf02d0db1b8350` |
| 2026/2027 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2026-2027/2026-2027-bra-report.pdf | `15effa7b903d026468cdea0b7eb2654eeb1f70d02a436c92289bff062fd257be` |
| 2027/2028 | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2027-2028/2027-2028-bra-report.pdf | `d2280c610b96dcbb24c58dbfc258ac09ae10f59d59da2e713b25890219c5f570` |

Licensing note: PJM publishes these reports "For Public Use"; see
`docs/data-licensing.md`.
