"""Licence and structured-metadata extraction from dataset landing pages."""
from __future__ import annotations

import json
import re
from .base import NotImplementedTool


def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""
    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"), "description": clip(d.get("description")),
        "license": d.get("license"), "creator": name_of(d.get("creator")), "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"), "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"), "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"), "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [{k: x.get(k) for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                          if isinstance(x, dict) and x.get(k) is not None} for x in dist[:10]],
    }


def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    if jsonld is None:
        jsonld = jsonld_datasets(html)
        
    out = {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}
    
    # 1. Try JSON-LD first
    if jsonld:
        for item in jsonld:
            # Check if "Dataset" is in the type (handles both "Dataset" and "http://schema.org/Dataset")
            if "Dataset" in str(item.get("@type", "")) and "license" in item:
                lic = item["license"]
                lic_str = str(lic)
                
                # If it's a known non-license or explicitly unknown
                if "unknown" in lic_str.lower():
                    out["found_in"] = "json-ld"
                    out["snippet"] = lic_str
                    return out
                    
                # Normalize based on URL or string content
                lic_lower = lic_str.lower()
                if "odbl/1.0" in lic_lower: 
                    out["licence_name"] = "ODbL 1.0"
                elif "cc0-1.0" in lic_lower: 
                    out["licence_name"] = "CC0 1.0"
                elif "by-nc-sa/4.0" in lic_lower or "by-nc-sa 4.0" in lic_lower: 
                    out["licence_name"] = "CC BY-NC-SA 4.0"
                elif "by-nc/4.0" in lic_lower or "by-nc 4.0" in lic_lower: 
                    out["licence_name"] = "CC BY-NC 4.0"
                elif "by/4.0" in lic_lower or "cc by 4.0" in lic_lower or "licenses/by/4.0" in lic_lower: 
                    out["licence_name"] = "CC BY 4.0"
                
                if out["licence_name"]:
                    out["found_in"] = "json-ld"
                    out["snippet"] = lic_str
                    if isinstance(lic, dict): 
                        out["licence_url"] = lic.get("url")
                    elif isinstance(lic, str) and lic.startswith("http"): 
                        out["licence_url"] = lic
                    return out

    # 2. Try Regex Link Extraction
    # Look for OGL v3.0
    ogl_match = re.search(r'<a[^>]*href=["\'](https?://www\.nationalarchives\.gov\.uk/doc/open-government-licence/version/3/?)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
    if ogl_match:
        out["licence_name"] = "OGL v3.0"
        out["licence_url"] = ogl_match.group(1)
        out["found_in"] = "link"
        out["snippet"] = ogl_match.group(0)
        return out
        
    # Look for CC BY-NC 4.0
    cc_match = re.search(r'<a[^>]*href=["\'](https?://creativecommons\.org/licenses/by-nc/4.0/legalcode)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
    if cc_match:
        out["licence_name"] = "CC BY-NC 4.0"
        out["licence_url"] = cc_match.group(1)
        out["found_in"] = "link"
        out["snippet"] = cc_match.group(0)
        return out

    # Look for CC BY 4.0 in links
    cc_by_match = re.search(r'<a[^>]*href=["\'](https?://creativecommons\.org/licenses/by/4\.0/?)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
    if cc_by_match:
        out["licence_name"] = "CC BY 4.0"
        out["licence_url"] = cc_by_match.group(1)
        out["found_in"] = "link"
        out["snippet"] = cc_by_match.group(0)
        return out
        
    # 3. Try raw text matching as a last resort
    if ("Creative Commons Attribution 4.0" in html or "CC BY 4.0" in html) and out["found_in"] is None:
        out["licence_name"] = "CC BY 4.0"
        out["found_in"] = "text"
        out["snippet"] = "Creative Commons Attribution 4.0" 
        return out

    return out