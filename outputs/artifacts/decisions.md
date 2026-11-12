# Discovery Decisions & Engineering Log

## 1. City Coordinates Assumption (Config Exception)
- **Chosen City:** Milan / Valdena region, northern Italy (`latitude: 45.46`, `longitude: 9.19`)[cite: 5].
- **Reason:** Both UC1 and UC2 are set in Valdena (fictional, northern Italy)[cite: 1, 5], whereas `config/external_sources_register.json` shipped with Lisbon (`38.72, -9.14`) as the default Open-Meteo query[cite: 5]. Updated `default_query` to `45.46, 9.19` so API probes sample northern Italian meteorology[cite: 1, 5].

## 2. Host Allowlist Decisions (G6)
- **`ec.europa.eu` (Added):** Required to inspect the prescribed Eurostat JSON-stat API (`sdg_11_52`) for UC1 need N6[cite: 1, 10]. Minimal exact host added; no wildcard subdomains permitted[cite: 1].
- **`catalog.data.gov` (Not Added — Intentional Refusal):** Kept off `config/allowlist.json`[cite: 1]. The Chicago dataset link (`https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations`) was accepted at the candidate gate to verify that the HTTP guardrail refuses unapproved external domains (`DOMAIN_NOT_ALLOWLISTED`) and records the refusal as an audit finding[cite: 1, 3, 9].

## 3. G1 & G3 Implementation Edge Cases
- **G1 (`extract_licence` in `discovery_agent/tools/licence.py`):** Handled schema.org JSON-LD `@type` values formatted either as `"Dataset"` or full URIs (`"http://schema.org/Dataset"`), normalized licence URLs to canonical names (`CC BY 4.0`, `CC0 1.0`, `ODbL 1.0`, `OGL v3.0`), and explicitly treated `"Unknown"` licence strings as `licence_name: None` (triggering `LIC-UNKNOWN`) rather than a valid licence[cite: 1].
- **G3 (`jsonstat_summary` in `discovery_agent/tools/formats.py`):** Handled both dictionary-indexed and list-indexed JSON-stat 2.0 `dimension.*.category.index` structures, sorted time values (noting missing years such as `2006` in Eurostat `sdg_11_52`)[cite: 10], computed missing cell counts across sparse value arrays[cite: 10], and flagged non-ISO country codes (`EL`, `UK`) with `NON_ISO_GEO_CODES`.

## 4. G4 & G5 Feasibility Rules and Calibration
- **Feasible-for-One-Need / Window Example (`internal.airq.station_readings` in UC1):** Satisfies `N1` (`hourly` pollutant grain) for the `production` window (`2024-01-01` to `2025-12-31`) as `feasible_with_conditions`[cite: 1, 3, 4], but fails `N1` for the `prototype` window (`2004-03-10` to `2005-04-04`) because `temporal.start` is `2023-01-01` (`COV-OUT-OF-WINDOW` when evaluated against prototype)[cite: 3, 4, 6].
- **Dismissed / Contextualized Flags:** For `link.uci_360`, `FRS-STALE` (data ending `2005-02-28`)[cite: 3, 4] is expected because the candidate specifically targets the 2004–2005 historical `prototype` window[cite: 1, 4]; however, `DQ-METADATA-CONTRADICTION` (`has_missing_values: "no"` vs. `-200` sentinels)[cite: 3, 4, 11] and `GOV-PURPOSE-LIMITATION` (research-only note)[cite: 3, 4, 11] independently force a `not_feasible` verdict under our G5 calibration rules[cite: 3, 4].

## 5. G7 Agent Failure & Fix
- **Failure Found in Trace (`outputs/UC2/trace.jsonl:83`):** During UC2 `assess`, `risk_assessor` failed schema validation on turn 1 (`ok: false`, `"api.nager_public_holidays: invalid red-flag code 'LIC-UNKNOWN-DATA'"`), inventing a custom flag code outside the allowed taxonomy and forcing an extra LLM retry turn. Similar schema-drift errors occurred in UC1 (`trace.jsonl:29, 91, 93`).
- **Root-Cause Fix:** Added an explicit **Schema & Flag Taxonomy Strictness** section to `discovery_agent/prompts/risk_assessor.md` instructing the model to only emit exact red-flag codes from the defined taxonomy and never invent custom codes or undocumented keys.
- **Before vs. After Measurement (`UC2` `--from-stage assess`):**
  - **Before:** `risk_assessor` took **2 turns** with **1 schema validation error** (`invalid red-flag code 'LIC-UNKNOWN-DATA'`).
  - **After:** `risk_assessor` completed in **1 turn** with **0 validation errors** (`2` total LLM calls across `assess..memo`).
- **Project Decision Impact:** Preventing invalid flag codes stops the Risk Assessor from wasting retry turns, exceeding `max_turns` on complex multi-source runs, or silently dropping a risk flag that should trigger `feasible_with_conditions` or `not_feasible`.

## 6. Source Suggestions (Step 2b)
- **Search Query Executed (`scripts/web_search.py`):** `"EEA air quality monitoring stations Italy hourly dataset"`.
- **Candidate Leads Returned & Decisions:**
  - `https://discomap.eea.europa.eu/map/fme/AirQualityExport.htm` (EEA Air Quality Download Service, E1a/E2a hourly station data for `IT`): **Rejected for direct pipeline ingestion** — interactive export portal rather than a direct static file/API link, and `discomap.eea.europa.eu` is not on `config/allowlist.json` (preserving G6 allowlist minimality)[cite: 1].
  - `https://www.dati.lombardia.it/` (ARPA Lombardia open data portal): **Rejected for UC1** — covers Lombardy regional stations rather than confirmed Valdena civic boundaries, and host is not allowlisted[cite: 1].