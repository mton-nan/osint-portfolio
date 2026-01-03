#!/usr/bin/env python3

import os
import requests
import argparse
from urllib.parse import quote

# =========================
# CONFIG
# =========================

OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

CSE_ENGINES = {
    "investigative": os.getenv("CSE_INVESTIGATIVE"),
    "media": os.getenv("CSE_MEDIA"),
    "official": os.getenv("CSE_OFFICIAL"),
    "international": os.getenv("CSE_INTERNATIONAL"),
    "regional": os.getenv("CSE_REGIONAL"),
    "business": os.getenv("CSE_BUSINESS"),
}

if not OPENSANCTIONS_API_KEY or not GOOGLE_API_KEY:
    raise RuntimeError(
        "Missing API keys. Set OPENSANCTIONS_API_KEY and GOOGLE_API_KEY "
        "as environment variables."
    )

# =========================
# OPENSANCTIONS
# =========================

def check_opensanctions(entity, schema="Person"):
    query = quote(entity)
    url = (
        "https://api.opensanctions.org/search/default"
        f"?q={query}&schema={schema}&limit=10"
    )
    headers = {"Authorization": f"ApiKey {OPENSANCTIONS_API_KEY}"}

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        hits = data.get("results", [])

        results = []
        relevant_hits = 0

        for hit in hits:
            caption = hit.get("caption", "Unknown")
            datasets = ", ".join(hit.get("datasets", []))
            topics = ", ".join(hit.get("properties", {}).get("topics", []))

            results.append(f"{caption} | {datasets} | {topics}")

            if any(
                k in (datasets + topics).lower()
                for k in ["sanction", "ua_", "ukraine", "nsdc", "russian", "corruption"]
            ):
                relevant_hits += 1

        return results, relevant_hits

    except Exception as e:
        return [f"Error: {e}"], 0


# =========================
# GOOGLE CSE
# =========================

def google_cse_search(query, cse_type, limit=5):
    cx = CSE_ENGINES.get(cse_type)
    if not cx:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": cx,
        "q": query,
        "num": limit,
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("items", [])
    except Exception:
        return []


# =========================
# OPENDATABOT SIGNALS (PUBLIC, SIGNAL-BASED)
# =========================

def analyze_opendatabot_signals(results):
    flags = {
        "rnbo": False,
        "owner": False,
        "beneficiary": False,
    }

    for r in results:
        text = (r.get("title", "") + " " + r.get("snippet", "")).lower()

        if "рнбо" in text:
            flags["rnbo"] = True
        if "власник" in text:
            flags["owner"] = True
        if "бенефіціар" in text:
            flags["beneficiary"] = True

    return flags


# =========================
# NAME VARIANTS
# =========================

def generate_name_variants(name):
    variants = {name}
    parts = name.split()

    if all(ord(c) < 128 for c in name):
        if len(parts) == 2:
            variants.add(f"{parts[1]} {parts[0]}")
        elif len(parts) == 3:
            variants.add(f"{parts[2]} {parts[0]} {parts[1]}")

    if len(parts) == 2:
        variants.add(f"{parts[1]} {parts[0]}")
    elif len(parts) == 3:
        variants.add(f"{parts[1]} {parts[0]} {parts[2]}")

    return list(variants)


# =========================
# INVESTIGATIVE QUERIES
# =========================

def generate_investigative_queries(entity):
    ua_keywords = [
        "розслідування",
        "корупція",
        "НАБУ",
        "САП",
        "ВАКС",
        "БЕБ",
        "ДБР",
        "Bihus",
        "OCCRP",
    ]

    return list({entity} | {f"{entity} {kw}" for kw in ua_keywords})


# =========================
# INVESTIGATIVE RISK BOOST
# =========================

def investigative_risk_boost(investigative_results):
    high_risk_keywords = [
        "kickback",
        "embezzlement",
        "nabu",
        "набу",
        "bribe",
        "corruption scheme",
        "money laundering",
    ]

    hits = 0
    matched = set()

    for r in investigative_results:
        text = f"{r.get('title','')} {r.get('snippet','')}".lower()
        for kw in high_risk_keywords:
            if kw in text:
                hits += 1
                matched.add(kw)

    if hits >= 2:
        return 6, list(matched)
    if hits == 1:
        return 4, list(matched)
    return 0, []


# =========================
# RECONSTRUCTION RISK FLAG
# =========================

def reconstruction_risk_flag(entity, matched_keywords):
    energy_terms = ["energy", "nuclear", "power", "energo", "grid"]

    if matched_keywords and any(t in entity.lower() for t in energy_terms):
        return (
            "Medium-High: Anti-corruption signals combined with "
            "energy or reconstruction sector exposure."
        )

    return "Low: No direct reconstruction-related corruption signals identified."


# =========================
# COLLECT OSINT
# =========================

def collect_osint(entity, schema):
    aggregated = {
        "sanctions_hits": 0,
        "investigative": [],
        "business_flags": {"rnbo": False, "owner": False, "beneficiary": False},
    }

    for variant in generate_name_variants(entity):
        _, hits = check_opensanctions(variant, schema)
        aggregated["sanctions_hits"] += hits

        for q in generate_investigative_queries(variant):
            aggregated["investigative"].extend(
                google_cse_search(q, "investigative", limit=10)
            )

        business_results = google_cse_search(variant, "business", limit=10)
        flags = analyze_opendatabot_signals(business_results)

        for k in aggregated["business_flags"]:
            aggregated["business_flags"][k] |= flags[k]

    return aggregated


# =========================
# REPORT (CLI ONLY)
# =========================

def generate_report(entity, schema):
    osint = collect_osint(entity, schema)

    score = min(osint["sanctions_hits"] * 3, 6)
    score += 2 if osint["investigative"] else 0
    score += 3 if osint["business_flags"]["rnbo"] else 0
    score += 2 if (
        osint["business_flags"]["owner"] or osint["business_flags"]["beneficiary"]
    ) else 0

    boost, matched = investigative_risk_boost(osint["investigative"])
    score = min(score + boost, 10)

    risk_level = "LOW" if score <= 3 else "MEDIUM" if score <= 6 else "HIGH"

    print("\n==============================")
    print(f"ENTITY: {entity}")
    print("==============================")
    print(f"OVERALL RISK: {risk_level} ({score}/10)")
    print("\nReconstruction / Donor Risk:")
    print(reconstruction_risk_flag(entity, matched))
    print("\nNote: This is a public OSINT triage output. Manual review required.")


# =========================
# CLI
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoriTool OSINT triage utility")
    parser.add_argument("entity", help="Person or company name")
    parser.add_argument("--schema", default="Person", choices=["Person", "Company"])
    args = parser.parse_args()

    generate_report(args.entity, args.schema)
