## 1. Executive summary

**Verdict: not feasible yet.** The must need N2 (mapping of product codes across the 2024 code change) is unmet, so the overall verdict is not_feasible. The other needs can move forward in parallel.

Facts that drive the verdict:

- **N2 is unmet.** The wiki page product_codes_2024 (2024-04-02) says codes ending in "L" were replaced from 2024-04-01 and that no mapping table exists. The only product list (internal.sales.products) holds current codes only. Name matching is possible but not unique.
- **N1 (daily sales) is achievable with conditions.** internal.sales.daily_by_product covers 2022-01-01 onward and refreshes daily (last refreshed 2026-10-14). Access needs Retail Operations approval. The 2024-02-05 to 2024-03-10 till gap must be treated as missing, not zero. The catalog omits this gap.
- **N3 (daily max temperature) is achievable with conditions.** api.open_meteo_archive returns temperature_2m_max. The shop's town is not named in any source. Probes used Milan-area coordinates. Licence is CC BY 4.0 with a mixed upstream-licence flag that needs Legal sign-off before production.
- **N4 (public holidays) is achievable with conditions.** api.nager_public_holidays returns national holidays. Its data licence is unknown (only the MIT repository licence was found). 2025 has not been probed.
- **N5 (shop calendar and events) is unmet.** internal.store.calendar was rejected for a row-count contradiction (about 1,500 rows in the catalog versus roughly 4,660 implied by its daily span). Its schema is undocumented. It has not been sampled.

## 2. Need coverage

| need id | need | priority | status | best source(s) | gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met_with_conditions | internal.sales.daily_by_product | Retail Operations access approval. 2024-02-05 to 2024-03-10 gap must be handled as missing. Zero-row convention, timezone, refunds/voids and VAT basis unconfirmed. |
| N2 | Mapping of product codes before and after the 2024 code change | must | **unmet** | none | No mapping table exists (wiki product_codes_2024). internal.sales.products holds current codes only. Name matching is not unique. |
| N3 | Daily maximum temperature | must | met_with_conditions | api.open_meteo_archive | Shop town unconfirmed. Timezone must be set to Europe/Rome. Legal sign-off on mixed upstream licences. Modelled grid data, not station data. |
| N4 | Public holidays in Italy | should | met_with_conditions | api.nager_public_holidays | Data licence and commercial use unknown. 2025 not probed. Full list not checked against the official calendar. No local or patron-saint holidays. |
| N5 | Shop opening days and local events | should | **unmet** | none | Only candidate internal.store.calendar was rejected (row-count contradiction). event_name undocumented. Not sampled. |

## 3. Source assessments

Sources are grouped by verdict. No source is rated plain "feasible". Three are feasible with conditions. Two are not feasible.

### 3.1 With conditions

**internal.sales.daily_by_product** (N1, N2)
- *What it is:* Units sold and revenue in EUR per product code per day, from the till system. Owner Retail Operations. About 310,000 rows. Catalog coverage starts 2022-01-01, open-ended, daily refresh.
- *Verdict:* feasible_with_conditions, for N1 only.
- *Key flags:* ACC-RESTRICTED (major; confidential, access by request to Retail Operations). INT-JOIN-KEY-MISMATCH (major; codes changed 2024-04-01 with no mapping). DQ-SEMANTIC-ENCODING (major; product meaning is carried in code suffixes).
- *Conditions:* access approval; a documented old-to-new code bridge before any before/after analysis; treat the 2024 gap as missing; confirm zero-row convention, timezone cut-off, refund/void handling and gross or net of VAT; confirm the table covers only the Valdena shop (no store column).

**api.open_meteo_archive** (N3)
- *What it is:* Gridded reanalysis weather by point coordinates. Daily max 2 m temperature (temperature_2m_max, °C) is available for a chosen location. Licence CC BY 4.0. Owner not stated.
- *Verdict:* feasible_with_conditions.
- *Key flags:* LIC-MIXED (major; upstream sources have differing licences, and the Copernicus C3S licence PDF was not read). LIC-ATTRIBUTION (minor; a "Weather data by Open-Meteo.com" link is required).
- *Conditions:* the owner confirms the shop's town (the probe location is an assumption); set timezone=Europe/Rome; probe the full window 2023-06-01 to 2026-03-31 for gaps (only endpoint dates were sampled, and archive coverage to 2026-03-31 is unconfirmed); Legal sign-off before production (prototyping allowed now); disclose that data is modelled, not observed.

**api.nager_public_holidays** (N4)
- *What it is:* REST API giving the national public-holiday list by year and country (IT). Owner nager.at (Nager.Date project). Probed for 2023, 2024 and 2026, each HTTP 200. Daily grain. Metadata refresh cadence unknown.
- *Verdict:* feasible_with_conditions.
- *Key flags:* none raised by rules. Open items: data licence unknown (repository is MIT, no separate data licence found); commercial use unknown; 2025 not probed; probe counts of 13 and 14 holidays exceed the commonly cited ~12 and are unverified; catalog lists /api/v3 while the README documents /api/v4.
- *Conditions:* written confirmation of commercial use of the data; probe 2025; check the full list against the official national calendar; confirm the endpoint version; source local holidays elsewhere (N5 or a local calendar). If commercial use cannot be confirmed, the source should be treated as LIC-UNKNOWN and rejected.

### 3.2 Not feasible

**internal.sales.products** (N2)
- *What it is:* Static product master of about 64 rows (product_code, product_name, category), current codes only. Owner Retail Operations. Last metadata update 2025-03-31.
- *Verdict:* not_feasible for N2.
- *Key flags:* INT-NO-JOIN-KEY (major). It holds no pre-2024 codes. The wiki says no mapping table exists. The name bridge is not unique. Its last update (2025-03-31) also predates part of the recent window (freshness gap, not a rule flag).
- *Conditions to revisit:* a historical product master with pre-2024 codes and a mapping table, from Retail Operations. None is documented in the sources read.

**internal.store.calendar** (N5)
- *What it is:* One row per day with an is_open flag and free-text event_name. Owner Store Operations. Catalog coverage from 2022-01-01, weekly refresh, last updated 2026-10-10. No wiki page documents it. Not sampled.
- *Verdict:* not_feasible (rejected under calibration rule 4).
- *Key flags:* DQ-METADATA-CONTRADICTION (major). Catalog row count is about 1,500, but the daily span implies about 4,660 rows. The catalog says "Either the table has gaps or the row count is stale. Not resolved." DQ-UNDOCUMENTED-SCHEMA (major). Three columns with one-line descriptions only. No wiki backlinks.
- *Conditions to revisit:* Store Operations reconciles the row count and gaps, documents event_name, and confirms whether is_open was recorded for 2024-02-05 to 2024-03-10. N5 is a should need, so this does not block the must needs.

## 4. Red-flag register

| source_id | code | severity | evidence | raised by (rule or judgement) |
|---|---|---|---|---|
| internal.sales.daily_by_product | ACC-RESTRICTED | major | auth_required=true; classification confidential; access by request to Retail Operations | rule |
| internal.sales.daily_by_product | INT-JOIN-KEY-MISMATCH | major | Codes ending in "L" replaced from 2024-04-01; no mapping table; name matching not unique (wiki product_codes_2024) | judgement |
| internal.sales.daily_by_product | DQ-SEMANTIC-ENCODING | major | Product meaning carried in code suffixes; catalog says only "see the product list" | judgement |
| internal.sales.products | INT-NO-JOIN-KEY | major | Lists only current codes; no mapping exists (wiki product_codes_2024) | judgement |
| internal.store.calendar | DQ-METADATA-CONTRADICTION | major | Catalog row count about 1,500 vs about 4,660 implied by daily span to 2026-10-10 | judgement |
| internal.store.calendar | DQ-UNDOCUMENTED-SCHEMA | major | One-line column descriptions only; event_name format and population unknown; no wiki page | judgement |
| api.open_meteo_archive | LIC-MIXED | major | Upstream licences differ (DWD/ECMWF CC-BY, UK Met Office CC-BY-SA, C3S/Météo-France under Copernicus PDF not read) | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | Attribution link required next to displayed data | rule |
| api.nager_public_holidays | (none raised) | — | Open items: data licence unknown; commercial use unknown; 2025 not probed; endpoint version unclear | — |

Also recorded, not a rule flag: the 2024-02-05 to 2024-03-10 till gap (internal.sales.daily_by_product) is omitted from the catalog but not contradicted by it.

## 5. Conditions and owners

| condition | source(s) | who can resolve it | blocking which need |
|---|---|---|---|
| Access approval for till sales data; confirm warehouse location is reachable | internal.sales.daily_by_product | Retail Operations | N1 |
| Documented old-to-new product code bridge; resolve duplicate names | internal.sales.daily_by_product; internal.sales.products | Retail Operations (historical product master and mapping table) | N2 (must) |
| Treat 2024-02-05 to 2024-03-10 as missing; record in pipeline spec | internal.sales.daily_by_product | Analytics team; Retail Operations to confirm | N1 |
| Confirm zero-row convention, cut-off timezone, refund/void handling, gross/net VAT, single-shop scope | internal.sales.daily_by_product | Retail Operations | N1 |
| Confirm shop town and coordinates; record assumption | api.open_meteo_archive | Shop owner | N3 |
| Set timezone=Europe/Rome; confirm daily boundaries | api.open_meteo_archive | Analytics team | N3 |
| Probe full window 2023-06-01 to 2026-03-31 for gaps | api.open_meteo_archive | Analytics team | N3 |
| Legal sign-off on Open-Meteo mixed licences, Copernicus terms, attribution | api.open_meteo_archive | Legal | N3 (production use) |
| Written confirmation of commercial use of holiday data | api.nager_public_holidays | Legal / data governance | N4 |
| Probe 2025; check full list vs official calendar; confirm v3 vs v4 endpoint | api.nager_public_holidays | Analytics team | N4 |
| Local holidays (patron saint) sourced elsewhere | api.nager_public_holidays | Shop owner; Store Operations | N4 (local part) |
| Reconcile row count and gaps; document event_name and is_open for the 2024 gap | internal.store.calendar | Store Operations | N5 (should) |

## 6. Recommended next steps

1. **Raise the N2 request first, with Retail Operations.** Ask for a historical product master with pre-2024 codes and any mapping table. This is the only route to a feasible verdict, because N2 is a must need.
2. **Raise the access request to Retail Operations for internal.sales.daily_by_product (N1).** Ask them to answer the till-convention questions in section 5 at the same time.
3. **Confirm the shop's town with the owner.** Record the location as an assumption in decisions.md before any weather pull.
4. **Start Legal review in parallel.** Cover the Open-Meteo mixed licences and Copernicus terms (N3), and the Nager.Date data licence and commercial use (N4).
5. **Ask Store Operations to reconcile internal.store.calendar (N5, should).** This can run later.
6. **Once the gate is passed, profile in this order:**
   - the sales data's 2024 gap and zero-day convention, and the code-bridge coverage, before any before/after comparison;
   - the Open-Meteo window for gaps, at the confirmed location and timezone;
   - the Nager.Date 2025 probe and the full list against the official calendar.

## 7. Open questions for the human reviewer

1. Which town is the shop in? The probes used Milan-area coordinates, which are only a probe. No source names the town.
2. Does a historical product master with pre-2024 codes and a mapping table exist, and who holds it? Without it, N2 stays unmet and the overall verdict stays not_feasible.
3. Can products that did not change code across 2024-04-01 be compared on their own as a fallback? The discovery did not assess this.
4. Is commercial use of the Nager.Date holiday data permitted? The data licence is unknown.
5. Does Legal accept the Open-Meteo mixed upstream licences for production, given the Copernicus terms were not read?
6. Does internal.sales.daily_by_product cover only the Valdena shop? The table has no store column.
7. Are zero-sales days stored as zero rows or omitted?
8. Is revenue_eur gross or net of VAT?
9. Is the 2024-02-05 to 2024-03-10 gap meant to be treated as missing, and was is_open recorded for those dates?
10. Is the catalog row count for internal.store.calendar stale, or does the calendar have gaps?
11. Which Nager.Date endpoint version (v3 or v4) should be used?
12. Who owns the local holiday calendar (patron-saint day) if it is needed for N4?

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-12T07:14:30Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. Which town is the shop in? The probes used Milan-area coordinates, which are only a probe. No source names the town.
2. Does a historical product master with pre-2024 codes and a mapping table exist, and who holds it? Without it, N2 stays unmet and the overall verdict stays not_feasible.
3. Can products whose codes did not change across 2024-04-01 be compared on their own as a fallback? The discovery did not assess this.
4. Is commercial use of the Nager.Date holiday data permitted? The data licence is unknown.
5. Does Legal accept the Open-Meteo mixed upstream licences for production, given the Copernicus terms were not read?
6. Does internal.sales.daily_by_product cover only the Valdena shop? The table has no store column.
7. Are zero-sales days stored as zero rows or omitted?
8. Is revenue_eur gross or net of VAT?
9. Is the 2024-02-05 to 2024-03-10 gap to be treated as missing, and was is_open recorded for those dates?
10. Is the catalog row count for internal.store.calendar stale, or does the calendar have gaps?
11. Which Nager.Date endpoint version (v3 or v4) should be used?
12. Who owns the local holiday calendar (patron-saint day) if it is needed for N4?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
