#!/usr/bin/env bash
# ============================================================
# Atlas Preview — Domain Reconnaissance Pipeline (Illustrative)
# ============================================================
# This script demonstrates the structure and logic of domain-
# level OSINT reconnaissance used within the Atlas framework.
#
# NOTE:
# - This is a preview, not the full Atlas implementation.
# - Enrichment APIs, historical data, and clustering logic
#   are intentionally excluded.
# ============================================================

set -euo pipefail

DOMAIN="$1"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUTDIR="atlas_preview_${DOMAIN}_${TIMESTAMP}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain>"
  exit 1
fi

mkdir -p "$OUTDIR"/{dns,http,ssl,favicon,meta}

# ------------------------------------------------------------
# 1. DNS RECONNAISSANCE (PASSIVE)
# ------------------------------------------------------------
dig +short A "$DOMAIN"        > "$OUTDIR/dns/a_records.txt"      || true
dig +short NS "$DOMAIN"       > "$OUTDIR/dns/ns_records.txt"     || true
dig +short MX "$DOMAIN"       > "$OUTDIR/dns/mx_records.txt"     || true

# ------------------------------------------------------------
# 2. HTTP METADATA
# ------------------------------------------------------------
curl -sI "https://$DOMAIN"    > "$OUTDIR/http/headers.txt"       || true
curl -s  "https://$DOMAIN"    > "$OUTDIR/http/index.html"        || true

# ------------------------------------------------------------
# 3. SSL CERTIFICATE SNAPSHOT
# ------------------------------------------------------------
echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates \
  > "$OUTDIR/ssl/certificate_meta.txt" || true

# ------------------------------------------------------------
# 4. FAVICON HASH (FINGERPRINT PREPARATION)
# ------------------------------------------------------------
FAVICON_URL="https://$DOMAIN/favicon.ico"
curl -s "$FAVICON_URL" -o "$OUTDIR/favicon/favicon.ico" || true

if command -v mmh3 >/dev/null 2>&1; then
  python3 - <<EOF > "$OUTDIR/favicon/favicon_hash.txt"
import mmh3, base64
with open("$OUTDIR/favicon/favicon.ico","rb") as f:
    data = base64.b64encode(f.read())
    print(mmh3.hash(data))
EOF
else
  echo "mmh3 not installed" > "$OUTDIR/favicon/favicon_hash.txt"
fi

# ------------------------------------------------------------
# 5. METADATA SUMMARY (ANALYST-READABLE)
# ------------------------------------------------------------
cat <<EOF > "$OUTDIR/meta/summary.txt"
Atlas Preview — Domain Reconnaissance Summary
=============================================

Domain:        $DOMAIN
Timestamp:     $TIMESTAMP

Artifacts collected:
- DNS records (A / NS / MX)
- HTTP headers and HTML snapshot
- SSL certificate metadata
- Favicon hash (when available)

Notes:
- This preview demonstrates data collection and normalization only.
- Correlation, enrichment, and clustering are part of the full Atlas framework.
EOF

echo "[+] Atlas preview completed: $OUTDIR"
