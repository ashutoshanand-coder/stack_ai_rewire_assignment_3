# Written Walkthrough: AI-Native Data Discovery

## 1. Deterministic Rule Explained (`rule_temporal_coverage` in `discovery_agent/risk_rules.py`)
`rule_temporal_coverage` compares a dataset's `[temporal.start, temporal.end]` interval (treating `end: null` as open-ended up to `uc["as_of"]`) against each window in `candidate["target_windows"]`[cite: 1]. It computes the inclusive day-overlap fraction for each target window: if all target windows have `0` overlap, it raises `COV-OUT-OF-WINDOW`; otherwise, if any window's overlap fraction is below `settings["rules"]["partial_window_threshold"]` (`0.95`), it raises `COV-PARTIAL-WINDOW`[cite: 1]. Independently, if `temporal.end` is more than `stale_after_years` (`5` years) before `uc["as_of"]`, it raises `FRS-STALE`[cite: 1].

## 2. Traced Claim in `signoff.json`
- **Claim:** In `outputs/UC1/signoff.json`, `traced_conclusion` cites `link.uci_360` and field `declared_metadata.has_missing_values` (`"no"`).
- **Trace:** While `declared_metadata.has_missing_values` claims no missing values[cite: 4, 11], `documentation_excerpts` notes `"Missing values are tagged with -200 value"` and `sample_data_file` confirmed `-200` sentinels in ~18.5% of `CO(GT)` and ~64% of `NMHC(GT)` rows[cite: 4, 11], triggering `DQ-METADATA-CONTRADICTION`[cite: 3, 4].
- **What could change it:** If the UCI dataset owner corrected the metadata and clarified commercial/prototyping reuse permissions, the source could be reconsidered solely as an offline method-prototyping sandbox[cite: 3, 4].

## 3. Rejected Source & Rationale
- **Source:** `link.data_open_air_chicago_hour_aggre_d4970b` (`https://catalog.data.gov/dataset/open-air-chicago-hour-aggregations`)[cite: 4, 9].
- **Why Rejected:** First, `catalog.data.gov` is intentionally excluded from `config/allowlist.json`, so `inspect_dataset_link` refused the HTTP request (`DOMAIN_NOT_ALLOWLISTED`, `ACC-UNREACHABLE`)[cite: 1, 4, 9]. Second, the dataset covers Chicago (US) rather than northern Italy (`COV-GEO-MISMATCH`), making it unusable for Valdena's air-quality needs[cite: 3, 4, 9].

## 4. Memo Conclusion Explained
- **Conclusion:** Both UC1 and UC2 are `not_feasible` as originally specified, but can move to `proceed_with_conditions` once key internal blockers are cleared[cite: 3, 4].
- **Reasoning:** In UC1, no valid public pollutant dataset covers the 2004–2005 prototype window, and production modeling requires access to `internal.airq.station_readings` and `internal.traffic.hourly_counts` plus resolving the VR-03 station shutoff (`2024-06-30`) and traffic counter direction break (`2024-03-18`)[cite: 3, 4]. In UC2, `internal.sales.products` lacks pre-`2024-04-01` product codes (`N2` unmet), requiring Retail Operations to supply a legacy mapping table before modeling the full history window.