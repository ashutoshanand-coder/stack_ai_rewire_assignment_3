
# UC1 Air quality and traffic: initial data-feasibility memo

Client: Valdena Civic Health Office (fictional, northern Italy). As-of date: 2026-10-15. Overall discovery verdict: **not_feasible** as specified.

## 1. Executive summary

The use case is not feasible as specified: no usable source meets the must-level pollutant need (N1) for the prototype window, and the must-level traffic need (N2) has no link to the monitoring stations.

Facts that drive the verdict:

- **N1 prototype is unmet.** The only public hourly pollutant candidate, UCI 360 (`link.uci_360`), is rejected. Its metadata says there are no missing values, but its notes say missing values are coded as -200, and the sample confirms this. It also ends 2005-02-28, so it covers about 0.91 of the prototype window. It is single-site, and its licence conflicts with a "research only" note. The Chicago link (`link.data_open_air_chicago_hour_aggre_d4970b`) is unreachable (DOMAIN_NOT_ALLOWLISTED), unlicensed and outside Italy.
- **N1 production depends on internal access.** The city station data (`internal.airq.station_readings`) starts 2023-01-01 in the catalog. It is access-restricted, has no station coordinates, and conflicts with the wiki on whether station VR-03 stopped on 2024-06-30.
- **N2 has no station join and an unadjusted series break.** Traffic counts (`internal.traffic.hourly_counts`) have no counter-to-station mapping. The wiki records that counters were replaced on 2024-03-18 and counting changed from per-direction to both-directions. The catalog does not mention this.
- **N3 and N4 are met with conditions.** Open-Meteo (`api.open_meteo_archive`) responded for both windows in probes, but it gives reanalysis grid values, not station data, and the client site is unknown. The clinic daily district counts (`internal.clinic.resp_visits_daily`) are the only source the clinic policy permits. Their respiratory definition, district code list and suppression rule are undocumented.
- **The discovery model suggests a narrower path.** The rationale proposes that the use case could move to feasible_with_conditions for a production-only scope, once internal access, station mapping and Legal sign-off are cleared. This is a suggestion from the discovery output and has not been decided.

## 2. Need coverage

| Need ID | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations | must | partially_met | internal.airq.station_readings; api.open_meteo_archive (not a pollutant source) | Prototype window has no usable pollutant source. UCI 360 rejected. Station data starts 2023-01-01 in catalog and is access-restricted. VR-03 status conflicts between catalog and wiki. |
| N2 | Hourly vehicle traffic near monitoring stations | must | partially_met | internal.traffic.hourly_counts | Production counts exist, but no counter-to-station mapping. Undocumented 2024-03-18 series break. Link to N1 unproven. |
| N3 | Hourly temperature and humidity | must | met_with_conditions | api.open_meteo_archive | Reanalysis grid, not station data. Client site coordinates unknown. Production needs Legal sign-off. C3S upstream terms not read. |
| N4 | Daily respiratory clinic visits by district | should | met_with_conditions | internal.clinic.resp_visits_daily | Access not yet granted. Legal basis not confirmed. Respiratory definition, district code list and suppression rule undocumented. |
| N5 | Patient-level clinic visit records | could | unmet | none | clinic.patient_visits is prohibited for this analysis by the clinic data policy. |
| N6 | National yearly context: deaths linked to PM2.5 | could | unmet | link.europa_sdg_11_52_099aa6 (rejected) | Licence unknown. Covers 2005-2023 only, so no production-window coverage. Rate unit undocumented. |

## 3. Source assessments

### Feasible
No source is rated plain feasible.

### Feasible with conditions

**api.open_meteo_archive**: Open-Meteo historical weather API. It returns hourly reanalysis temperature (°C) and relative humidity (%) for any latitude and longitude. It is not station observation data.
- Verdict: feasible_with_conditions. Only register source for hourly T and RH that responded for both windows.
- Flags: LIC-MIXED (major): the licence page lists C3S/Copernicus reanalysis with its own licence link beside CC BY 4.0. The C3S terms have not been read. LIC-ATTRIBUTION (minor): attribution text required. COV-GEO-MISMATCH (minor, judgement): the probe point returned a grid cell, not a station; the client site is unknown.
- Probe values: the record summary gives 45.45/9.17 at 138 m. The discovery result gives 45.448/9.169 at 138 m. Both are recorded here. The probe point 45.46/9.19 is a test value, not a confirmed site.
- Coverage: the record gives no start or end date and no refresh cadence. These are unknown. Only the probe windows were tested.
- Conditions: Legal sign-off for production (the register says not_required_open_data, but the policy source says otherwise). Read the C3S terms. Client site coordinates. Attribution. Validate against station readings and align UTC. Read the archive docs for coverage and refresh.

**internal.airq.station_readings**: City station readings, hourly NO2 (µg/m³) and PM2.5 (µg/m³), keyed by station_id with UTC timestamps. Owner: Environment Monitoring Unit. Catalog about 4.2 million rows, hourly refresh, coverage from 2023-01-01 with no end date.
- Verdict: feasible_with_conditions. Only internal source for N1 in production. Does not cover the prototype window.
- Flags: ACC-RESTRICTED (major): access requires a request to the Environment Monitoring Unit and was not tested. GOV-CATALOG-WIKI-CONFLICT (major, judgement): the catalog says the network is active and other stations report continuously. The wiki (last edited 2024-07-01) says VR-03 was switched off on 2024-06-30. INT-NO-JOIN-KEY (major, judgement): no coordinates or station-to-location mapping.
- Conditions: access request; confirm export completeness for 2024-2025; document the VR-03 gap and reconcile catalog and wiki; obtain station coordinates; confirm handling of faults, zeros, negatives and missing values; confirm use terms beyond "internal".

**internal.clinic.resp_visits_daily**: Daily respiratory visit counts per district of residence, held in the Valdena health warehouse. Owner: Clinical Analytics. Catalog says there are no patient identifiers. Coverage from 2022-01-01, open-ended, daily refresh, last refresh 2026-10-14.
- Verdict: feasible_with_conditions. Only source the clinic policy permits for district-level counts. Meets N4 at daily grain for the production window.
- Flags: ACC-RESTRICTED (major): access not yet probed. GOV-PURPOSE-LIMITATION (major, judgement): wiki clinic_data_policy (last edited 2025-02-01) allows only daily counts by district. Postcode and age band must not leave clinic systems. DQ-UNDOCUMENTED-SCHEMA (major, judgement): "respiratory" is undefined and no suppression rule is documented. INT-JOIN-KEY-MISMATCH (major, judgement): district is free text, with no code list or boundary version.
- Conditions: warehouse access; legal basis confirmed by the Data Protection Office; respiratory definition; district code list and boundary history 2022-2026; small-cell suppression rule; daily completeness and zero handling (not yet sampled). No patient-level data.

**internal.traffic.hourly_counts**: Hourly vehicle counts per road counter (counter_id, ts_local, vehicles). Owner: Mobility Office. Described as counters "near the monitoring stations". Catalog about 15 million rows, coverage from 2021-01-01, open-ended, hourly refresh.
- Verdict: feasible_with_conditions. Only internal hourly traffic source for N2 in production. Usable only once counters are mapped to stations and the break is handled.
- Flags: ACC-RESTRICTED (major): access via the Mobility Office, reachability unknown. GOV-CATALOG-WIKI-CONFLICT (major, judgement): the wiki (counter_replacement_2024, edited 2024-04-02) records a break on 2024-03-18. The catalog export of 2026-10-14 has no note. INT-NO-JOIN-KEY (major, judgement): no counter-to-station mapping or distances. DQ-UNDOCUMENTED-SCHEMA (major, judgement): direction is not a column, vehicle class is undefined, no break adjustment. DQ-DST-ARTEFACTS (minor, judgement): ts_local has no documented zone or DST rule.
- Conditions: access; counter-to-station mapping; a documented adjustment at 2024-03-18, or limit the production model to post-2024-03-18 counts; time zone and DST rule; vehicle class; first and last dates.

### Not feasible

**link.uci_360**: UCI 360 Air Quality. Hourly readings from a gas multisensor device at one road-level site in an unnamed Italian city, March 2004 to February 2005, with reference analyser values for CO, NMHC, benzene, NOx and NO2. It has no traffic, clinic or district fields.
- Verdict: not_feasible. Rejected for a metadata contradiction, staleness and partial window coverage. The discovery output notes it could serve only as a method sandbox, and only after the owner clarifies terms. That is a human decision, not a finding.
- Flags: DQ-METADATA-CONTRADICTION (major, rule): metadata says no missing values, notes say -200 codes missing values, and the sample confirms -200 in several fields. DQ-SENTINEL-VALUES (major, judgement): about 18.5% of CO(GT) and 64% of NMHC(GT) are -200 in the sample. C6H6(GT) has negatives. FRS-STALE (major, rule): data ends 2005-02-28. COV-PARTIAL-WINDOW (major, rule): covers about 0.91 of the prototype window. LIC-ATTRIBUTION (minor, rule): "CC BY 4.0" conflicts with the notes. GOV-PURPOSE-LIMITATION (major, judgement): "research purposes only; commercial purposes fully excluded". INT-REPRESENTATIVENESS (major, judgement): one device, one site, one year. INT-NO-JOIN-KEY (major, judgement): no station ID, coordinates or district code. FRS-METADATA-DATE-MISLEADING (minor, judgement): the metadata_last_updated date of 2024-03-10 refers to the UCI page, not the data.

**link.data_open_air_chicago_hour_aggre_d4970b**: Open Air Chicago hourly aggregations, a data.gov landing page for a US city.
- Verdict: not_feasible. Unreachable, unlicensed and not in Italy. Cannot serve N1. The discovery output says not to pursue another route to this data.
- Flags: ACC-UNREACHABLE (blocker, rule): catalog.data.gov returned DOMAIN_NOT_ALLOWLISTED. LIC-UNKNOWN (blocker, rule): no licence read. COV-GEO-MISMATCH (major, judgement): US city, while UC1 is Italy.

**link.europa_sdg_11_52_099aa6**: Eurostat SDG 11.5.2, premature deaths from PM2.5 exposure, Italy, annual, JSON-stat. Two units (NR and RT). National context only.
- Verdict: not_feasible. Licence unknown and no production-window coverage. N6 is a could-need, so the gap is limited.
- Flags: LIC-UNKNOWN (blocker, rule): no licence found; the copyright page redirected to an EU Login page. COV-PARTIAL-WINDOW (major, rule): data 2005-01-01 to 2023-12-31, fraction 0.24 of the prototype window, none for production. DQ-UNDOCUMENTED-SCHEMA (major, judgement): rate denominator not stated; 2006 absent from the time dimension.

## 4. Red-flag register

| Source ID | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| api.open_meteo_archive | LIC-MIXED | major | C3S licence beside CC BY 4.0; C3S terms not read | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | Attribution text required | rule |
| api.open_meteo_archive | COV-GEO-MISMATCH | minor | Grid cell, not station; client site unknown | judgement |
| internal.airq.station_readings | ACC-RESTRICTED | major | Access request to Environment Monitoring Unit; not tested | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Catalog says active; wiki says VR-03 off 2024-06-30 | judgement |
| internal.airq.station_readings | INT-NO-JOIN-KEY | major | No coordinates or station mapping | judgement |
| internal.clinic.resp_visits_daily | ACC-RESTRICTED | major | Access via Clinical Analytics; not probed | rule |
| internal.clinic.resp_visits_daily | GOV-PURPOSE-LIMITATION | major | Policy allows daily district counts only | judgement |
| internal.clinic.resp_visits_daily | DQ-UNDOCUMENTED-SCHEMA | major | Respiratory undefined; no suppression rule | judgement |
| internal.clinic.resp_visits_daily | INT-JOIN-KEY-MISMATCH | major | Free-text district; no code list | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | Mobility Office access; reachability unknown | rule |
| internal.traffic.hourly_counts | GOV-CATALOG-WIKI-CONFLICT | major | 2024-03-18 counter change in wiki, absent from catalog | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | No counter-to-station mapping | judgement |
| internal.traffic.hourly_counts | DQ-UNDOCUMENTED-SCHEMA | major | Direction, class and break adjustment undocumented | judgement |
| internal.traffic.hourly_counts | DQ-DST-ARTEFACTS | minor | No documented zone or DST rule | judgement |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | DOMAIN_NOT_ALLOWLISTED | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence read | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | US city | judgement |
| link.europa_sdg_11_52_099aa6 | LIC-UNKNOWN | blocker | No licence found | rule |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Covers 0.24 of prototype; no production | rule |
| link.europa_sdg_11_52_099aa6 | DQ-UNDOCUMENTED-SCHEMA | major | Rate denominator missing; 2006 absent | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Metadata vs -200 notes; confirmed in sample | rule |
| link.uci_360 | FRS-STALE | major | Ends 2005-02-28 | rule |
| link.uci_360 | COV-PARTIAL-WINDOW | major | Covers 0.91 of prototype | rule |
| link.uci_360 | LIC-ATTRIBUTION | minor | CC BY 4.0 vs research-only notes | rule |
| link.uci_360 | GOV-PURPOSE-LIMITATION | major | Research only; commercial use excluded | judgement |
| link.uci_360 | DQ-SENTINEL-VALUES | major | -200 in CO, NMHC; negatives in C6H6 | judgement |
| link.uci_360 | INT-REPRESENTATIVENESS | major | One device, one site, one year | judgement |
| link.uci_360 | INT-NO-JOIN-KEY | major | No station ID or location | judgement |
| link.uci_360 | FRS-METADATA-DATE-MISLEADING | minor | 2024 metadata date vs 2004-2005 data | judgement |

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve | Blocking which need |
|---|---|---|---|
| Access for production window | internal.airq.station_readings | Environment Monitoring Unit | N1 (production) |
| Export completeness 2024-2025; VR-03 status reconciled | internal.airq.station_readings | Environment Monitoring Unit; data steward (Giulia Rossi) for VR-03 | N1 (production) |
| Station coordinates or station-to-location mapping | internal.airq.station_readings; internal.traffic.hourly_counts | Environment Monitoring Unit; Mobility Office | N1, N2 |
| QC handling (faults, zeros, negatives, missing values) | internal.airq.station_readings | Environment Monitoring Unit | N1 |
| Access to traffic counts | internal.traffic.hourly_counts | Mobility Office | N2 |
| Counter-to-station mapping | internal.traffic.hourly_counts | Mobility Office | N2 |
| Adjustment or split at 2024-03-18 | internal.traffic.hourly_counts | Mobility Office | N2 |
| Time zone and DST rule for ts_local | internal.traffic.hourly_counts | Mobility Office; data engineering | N2 |
| Access to clinic warehouse | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Legal basis for daily district counts | internal.clinic.resp_visits_daily | Data Protection Office | N4 |
| Respiratory definition; district code list and boundary version | internal.clinic.resp_visits_daily | Clinical Analytics | N4 |
| Small-cell suppression rule | internal.clinic.resp_visits_daily | Data Protection Office | N4 |
| Legal sign-off for production use | api.open_meteo_archive | Legal | N3 (production) |
| Read C3S upstream terms; confirm attribution | api.open_meteo_archive | Legal | N3 |
| Client site coordinates | api.open_meteo_archive; internal.airq.station_readings | Health Office / project lead | N3, N1 (location) |
| Validate reanalysis vs station data; UTC alignment | api.open_meteo_archive | Data engineering | N3 |
| Licence and research-only restriction | link.uci_360 | UCI / dataset owner | N1 (prototype) |
| Correct metadata contradiction; confirm -200 handling | link.uci_360 | UCI / dataset owner; data engineering | N1 (prototype) |
| Licence determination | link.europa_sdg_11_52_099aa6 | Legal | N6 |
| Rate denominator | link.europa_sdg_11_52_099aa6 | Eurostat documentation | N6 |
| Allowlist approval (not recommended) | link.data_open_air_chicago_hour_aggre_d4970b | Allowlist owner | N1 (prototype); not recommended |
| Patient-level records prohibited | clinic.patient_visits (no source assessed) | Clinic data policy owner | N5 |

## 6. Recommended next steps

1. Decide whether the use case proceeds as specified (not feasible), or narrows to a production-only scope. Do not treat the discovery model's suggestion as settled.
2. Raise the access request to the Environment Monitoring Unit for `internal.airq.station_readings`. Ask for export completeness, VR-03 status, station coordinates and QC rules.
3. Raise the access request to the Mobility Office for `internal.traffic.hourly_counts`. Ask for the counter-to-station mapping, the 2024-03-18 adjustment and the DST rule.
4. Raise the access request to Clinical Analytics for `internal.clinic.resp_visits_daily`. Ask for the respiratory definition, district code list, boundary version and suppression rule. Ask the Data Protection Office for the legal basis.
5. Ask Legal to clear production use of Open-Meteo, and to read the C3S terms.
6. Ask the Health Office to supply the client site coordinates. Record them in decisions.md and replace the probe point.
7. Decide whether UCI 360 may be used as a method sandbox. This needs the owner's written licence position first. Do not use it for production.
8. Do not pursue the Chicago link. Do not pursue the Eurostat cube until its licence is established.
9. Once access and the N1/N2 mapping conditions are met, profile first: station hourly completeness and -sentinel rates for 2024-2025; traffic counts either side of 2024-03-18; and an Open-Meteo vs station comparison for T and RH. Sample only.

## 7. Open questions for the human reviewer

1. Does the Health Office accept that no usable public source exists for the prototype window, or should the prototype be dropped?
2. Is UCI 360 acceptable as a sandbox, given its research-only notes and the unresolved CC BY 4.0 label, and who will ask the owner?
3. Which city, and which coordinates, will the Health Office use for the Open-Meteo call and the station join?
4. Should the production scope be narrowed to post-2024-03-18 traffic counts if no 2024 adjustment exists?
5. Is the VR-03 switch-off on 2024-06-30 correct, and which of the catalog or wiki is authoritative?
6. Does the Data Protection Office accept daily district counts as a legal basis for the warning model?
7. Is N6 (national PM2.5 context) still wanted, given its unknown licence and missing production coverage?
8. Is the discovery model's claim that the register's "not_required_open_data" conflicts with policy correct, and which Legal position governs?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-12T06:48:40Z (model claude-haiku-5-5). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. Does the Health Office accept that no usable public source exists for the prototype window, or should the prototype be dropped?
2. Is UCI 360 acceptable as a method sandbox, given its research-only notes and the unresolved CC BY 4.0 label, and who will ask the owner for written terms?
3. Which city and coordinates will the Health Office use for the Open-Meteo call and the station join?
4. Should the production scope be narrowed to post-2024-03-18 traffic counts if no 2024 adjustment is documented?
5. Is the VR-03 switch-off on 2024-06-30 correct, and which of the catalog or wiki is authoritative?
6. Does the Data Protection Office accept daily district counts as the legal basis for the warning model?
7. Is N6 (national PM2.5 context) still wanted, given its unknown licence and missing production coverage?
8. Which Legal position governs Open-Meteo production use, given the register says not_required_open_data while the policy source says otherwise?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
