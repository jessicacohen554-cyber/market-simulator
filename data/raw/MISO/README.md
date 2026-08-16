# MISO — raw publications (payload gitignored)

Potomac Economics' **MISO State of the Market (SOM)** volumes and its **IMM
Quarterly Reports** to the MISO Market Subcommittee. Potomac is MISO's
Independent Market Monitor.

> **Payload posture.** The 7 PDFs (31.0 MiB) are **gitignored and no longer
> tracked at tip** — BLOAT-B-2 corpus conversion,
> `docs/bloat-removal-plan-2026-08.md` §4.5 item B5 (class-approved under
> release-plan §6 decision 4). Only this README and `SHA256SUMS.txt` are
> tracked. Nothing in `src/`, `scripts/` or `tests/` opens these files: they are
> **hand-read citation sources** (e.g. the MISO-SOM-grounded near-cost coal
> floor cited at `src/market_sim/pipeline/backcast_config.py:675`, the RDT
> limits restated at `constants.py:4106`). Re-verified by fresh grep at
> `315a245` (2026-08-15).

## Sources

Every URL below was fetched and **verified byte-exact against the committed
file on 2026-08-15** (HTTP 200, `Content-Length` equal to the manifest's
`size_bytes`).

| File | Report | Source URL |
|---|---|---|
| `2023-MISO-SOM_Report_Body-Final.pdf` | 2023 SOM for MISO, report body | <https://www.potomaceconomics.com/wp-content/uploads/2024/06/2023-MISO-SOM_Report_Body-Final.pdf> |
| `2024-MISO-SOM_Report_Body_Final.pdf` | 2024 SOM for MISO, report body | <https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-MISO-SOM_Report_Body_Final.pdf> |
| `2024-MISO-SOM_Appendix_Final.pdf` | 2024 SOM for MISO, analytic appendix | <https://www.potomaceconomics.com/wp-content/uploads/2025/07/2024-MISO-SOM_Appendix_Final.pdf> |
| `2025-MISO-SOM_Report.pdf` | 2025 SOM for MISO | <https://www.potomaceconomics.com/wp-content/uploads/2026/07/2025-State-of-the-Market-Report.pdf> ⚠ **renamed on intake** |
| `IMM-Quarterly-Report_Spring-2025-MSC.pdf` | IMM Quarterly, Spring 2025 | <https://www.potomaceconomics.com/wp-content/uploads/2025/06/IMM-Quarterly-Report_Spring-2025-MSC.pdf> |
| `IMM-Quarterly-Report_Summer-2025-MSC.pdf` | IMM Quarterly, Summer 2025 | <https://www.potomaceconomics.com/wp-content/uploads/2025/11/IMM-Quarterly-Report_Summer-2025-MSC.pdf> |
| `IMM-Quarterly-Report_Fall-2025_MSC.pdf` | IMM Quarterly, Fall 2025 | <https://www.potomaceconomics.com/wp-content/uploads/2025/12/IMM-Quarterly-Report_Fall-2025_MSC.pdf> |

⚠ **The 2025 MISO SOM was renamed when it was intaken.** Potomac publishes it
as `2025-State-of-the-Market-Report.pdf` — the *same* base name it uses for the
ERCOT volume, which is why it was disambiguated to `2025-MISO-SOM_Report.pdf`
on disk. Fetching it needs an explicit `-o`, not `curl -O`. (Verified: the
published file is byte-identical to the committed one at 4,904,565 B.)

Landing page (if a URL ever moves): <https://www.potomaceconomics.com/markets-monitored/miso/>.
The `wp-content/uploads/<YYYY>/<MM>/` segment is the WordPress upload month, so
it does **not** generalize from the report period — take the URLs above verbatim.

## Recovery / re-fetch

1. **Restore from git history — DEAD since the 2026-08-16 history rewrite**
   (`cleanup-large-blobs.yml` run #18 / 31955205445, owner decision;
   `docs/FINDING-history-rewrite-2026-08-16.md`). The pin
   `315a24524a851566c3d32cc88668fa32dcbd1d74` no longer resolves and its
   rewritten twin `94b9cda540b8` no longer carries these PDFs (verified
   2026-08-16) — the payload blobs were stripped. `SHA256SUMS.txt` stays as
   the identity record a re-fetch is verified against.

2. **Re-fetch from the publisher.** Run from this directory:

   ```
   xargs -n1 curl -fLO <<'URLS'
   https://www.potomaceconomics.com/wp-content/uploads/2024/06/2023-MISO-SOM_Report_Body-Final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-MISO-SOM_Report_Body_Final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/07/2024-MISO-SOM_Appendix_Final.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/06/IMM-Quarterly-Report_Spring-2025-MSC.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/11/IMM-Quarterly-Report_Summer-2025-MSC.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/12/IMM-Quarterly-Report_Fall-2025_MSC.pdf
   URLS
   curl -fL -o 2025-MISO-SOM_Report.pdf \
     https://www.potomaceconomics.com/wp-content/uploads/2026/07/2025-State-of-the-Market-Report.pdf
   sha256sum -c <(awk '$1 !~ /^#/ && NF>=3 {s=$1; $1=$2=""; sub(/^ +/,""); print s "  " $0}' SHA256SUMS.txt)
   ```

   `SHA256SUMS.txt` carries the sha256 + byte size of all 7 payloads as of the
   pin sha, so a re-fetch is verifiable rather than merely plausible.
