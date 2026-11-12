"""Deterministic red-flag rules, run on every catalog record before the Risk Assessor agent.

Why rules and an agent? Rules are cheap, repeatable and testable, and they catch what can be
read from structured fields. The agent adds judgement flags (conflicts, consent gaps,
representativeness, ...) and may dismiss a rule flag only with a written reason, and the
orchestrator enforces that.

Each rule: (record, candidate, use_case, settings) -> list of {"code", "evidence"}.
"""
from __future__ import annotations

import re
from datetime import date
from datetime import datetime

Flag = dict

GRAIN_ORDER = ["minute", "15min", "30min", "hourly", "daily", "weekly", "monthly", "quarterly", "annual"]
INACTIVE_STATUSES = {"deprecated", "archived", "frozen", "retired", "decommissioned", "superseded"}


def _flag(code: str, evidence: str) -> Flag:
    return {"code": code, "evidence": evidence}


def _d(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Provided rules (read these as worked examples)
# ---------------------------------------------------------------------------
def rule_licence(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal":
        return []
    lic = record.get("licence") or {}
    name = (lic.get("name") or "").strip()
    flags = []
    if not name or name.lower() in {"unknown", "none", "null", "not found", "n/a"}:
        flags.append(_flag("LIC-UNKNOWN", f"No licence established. Evidence field: {lic.get('evidence')!r}"))
    elif re.search(r"\bNC\b|non[- ]?commercial", name, re.I):
        flags.append(_flag("LIC-NONCOMMERCIAL", f"Licence {name!r} restricts commercial use"))
    elif re.search(r"\bBY\b|attribution|OGL|open government", name, re.I):
        flags.append(_flag("LIC-ATTRIBUTION", f"Licence {name!r} requires attribution"))
    if lic.get("mixed_sources"):
        flags.append(_flag("LIC-MIXED", "Record states that parts come from upstream providers with different terms"))
    return flags


def rule_agreement(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = ((record.get("licence") or {}).get("agreement_status") or "").lower()
    if record["kind"] == "vendor_feed" and status not in {"active", "signed"}:
        return [_flag("LIC-AGREEMENT-NOT-ACTIVE", f"Vendor feed with agreement_status={status or 'unknown'!r}")]
    return []


def rule_access(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    acc = record.get("access") or {}
    flags = []
    if acc.get("auth_required") or (acc.get("classification") or "").lower() == "restricted":
        flags.append(_flag("ACC-RESTRICTED", f"auth_required={acc.get('auth_required')}, "
                                             f"classification={acc.get('classification')}, process={acc.get('request_process')!r}"))
    if (acc.get("method") or "").lower() in {"manual_export", "manual", "spreadsheet", "email"}:
        flags.append(_flag("ACC-MANUAL", f"Access method {acc.get('method')!r}"))
    if acc.get("reachable") is False:
        flags.append(_flag("ACC-UNREACHABLE", "Record states the source could not be reached or restored"))
    return flags


def rule_payload(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    size = (record.get("access") or {}).get("approx_size_bytes")
    limit = settings["rules"]["large_payload_bytes"]
    if isinstance(size, int) and size > limit:
        return [_flag("OPS-LARGE-PAYLOAD", f"approx_size_bytes={size:,} > {limit:,}")]
    return []


def rule_pii(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    pii_fields = [f["name"] for f in (record.get("schema") or {}).get("fields", []) if f.get("pii") is True]
    declared = (record.get("declared_metadata") or {}).get("contains_pii")
    if pii_fields or declared is True:
        return [_flag("GOV-PII", f"PII fields: {pii_fields or 'declared contains_pii=true'}")]
    return []


def rule_owner(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal" and not ((record.get("ownership") or {}).get("owner") or "").strip():
        return [_flag("GOV-OWNER-UNKNOWN", "Internal source with no recorded owner")]
    return []


def rule_status(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = (record.get("status") or "").lower()
    if status in INACTIVE_STATUSES:
        return [_flag("GOV-DEPRECATED", f"status={status!r}")]
    return []


# ---------------------------------------------------------------------------
# LEARNER TODO (G4): three rules. tests/test_learner_gaps.py::test_g4_* checks them.
# ---------------------------------------------------------------------------
def rule_temporal_coverage(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    flags = []
    temp = record.get("temporal", {})
    if not temp or temp.get("grain") == "static" or not temp.get("start"):
        return flags

    start_str = temp["start"]
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_str = temp.get("end")
    as_of_str = uc["as_of"]
    as_of = datetime.strptime(as_of_str, "%Y-%m-%d")
    
    if end_str:
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        years_diff = (as_of - end_date).days / 365.25
        if years_diff > settings["rules"]["stale_after_years"]:
            flags.append({"code": "FRS-STALE", "evidence": f"Data ends on {end_str}, which is more than {settings['rules']['stale_after_years']} years before {as_of_str}."})
    else:
        end_date = as_of

    threshold = settings["rules"]["partial_window_threshold"]
    windows = uc.get("windows", [])
    
    fractions = []
    for win_id in candidate.get("target_windows", []):
        if isinstance(windows, dict):
            win_def = windows.get(win_id)
        else:
            win_def = next((w for w in windows if w["id"] == win_id), None)
            
        if not win_def: 
            continue
        
        w_start = datetime.strptime(win_def["start"], "%Y-%m-%d")
        w_end = datetime.strptime(win_def["end"], "%Y-%m-%d")
        w_duration = (w_end - w_start).days + 1
        
        overlap_start = max(start_date, w_start)
        overlap_end = min(end_date, w_end)
        overlap_days = max(0, (overlap_end - overlap_start).days + 1)
        
        fraction = overlap_days / w_duration
        fractions.append((win_id, win_def, fraction))
        
    # The test expects the evidence string to name the window(s) and dates
    if fractions and all(f[2] == 0 for f in fractions):
        win_names = ", ".join([f[0] for f in fractions])
        flags.append({
            "code": "COV-OUT-OF-WINDOW", 
            "evidence": f"Data [{start_str}, {end_str}] does not overlap target window(s): {win_names}."
        })
    else:
        for win_id, win_def, fraction in fractions:
            if 0 < fraction < threshold:
                flags.append({
                    "code": "COV-PARTIAL-WINDOW", 
                    "evidence": f"Data [{start_str}, {end_str}] only partially covers '{win_id}' (fraction {fraction:.2f} < {threshold})."
                })

    return flags

def rule_grain(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    flags = []
    rec_grain = record.get("temporal", {}).get("grain")
    if not rec_grain or rec_grain in ("event", "static", "unknown"):
        return flags
        
    try:
        rec_idx = GRAIN_ORDER.index(rec_grain)
    except ValueError:
        return flags

    min_grain_idx = -1
    min_grain_name = ""
    
    for need_id in candidate.get("need_ids", []):
        for need in uc.get("needs", []):
            if need["id"] == need_id:
                # FIX: Safely check both possible schema structures for min_grain
                need_grain = need.get("temporal", {}).get("min_grain") or need.get("min_grain")
                if need_grain in GRAIN_ORDER:
                    idx = GRAIN_ORDER.index(need_grain)
                    if min_grain_idx == -1 or idx < min_grain_idx:
                        min_grain_idx = idx
                        min_grain_name = need_grain

    if min_grain_idx != -1 and rec_idx > min_grain_idx:
        flags.append({"code": "COV-GRAIN-MISMATCH", "evidence": f"Record grain '{rec_grain}' is coarser than minimum required '{min_grain_name}'."})
        
    return flags

def rule_metadata_contradiction(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    flags = []
    declared = record.get("declared_metadata", {})
    has_missing = str(declared.get("has_missing_values", "")).strip().lower()
    
    if has_missing in ("no", "false"):
        notes = " ".join(record.get("documentation_excerpts", []) + record.get("quality_notes", [])).lower()
        notes = notes.replace("no missing values", "")
        
        contradictions = ["missing values", "absence of value", "-200", "?", "nan"]
        if any(c in notes for c in contradictions):
            flags.append({"code": "DQ-METADATA-CONTRADICTION", "evidence": "Contradiction: says no missing values, but docs mention them."})
            
    return flags


RULES = [rule_licence, rule_agreement, rule_access, rule_payload, rule_pii, rule_owner, rule_status,
         rule_temporal_coverage, rule_grain, rule_metadata_contradiction]


def evaluate(record: dict, candidate: dict, uc: dict, settings: dict) -> tuple[list[Flag], list[str]]:
    """Run every rule. Returns (flags, warnings). A rule that is not implemented yet is skipped with a warning."""
    flags: list[Flag] = []
    warnings: list[str] = []
    for rule in RULES:
        try:
            for f in rule(record, candidate, uc, settings):
                flags.append({**f, "raised_by": f"rule:{rule.__name__}"})
        except NotImplementedError as exc:
            warnings.append(f"{rule.__name__} skipped: {exc}")
    seen, unique = set(), []
    for f in flags:
        if f["code"] not in seen:
            seen.add(f["code"])
            unique.append(f)
    return unique, warnings
