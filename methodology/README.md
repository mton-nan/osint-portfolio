# OSINT Methodology & Ethics

## Overview
This portfolio reflects a structured OSINT methodology grounded in
domain-level and infrastructure-focused analysis.
The approach combines passive technical reconnaissance, systematic
documentation, and analyst-led interpretation.

The methodology is operationalized through an internal framework
(Atlas), which enforces consistency, traceability, and verification
across investigations.

## Investigative scope
Investigations typically focus on:
- Domains and related infrastructure
- Hosting and IP overlap
- SSL certificates and historical issuance
- Tracking identifiers (e.g. analytics, counters)
- Technical fingerprints indicating coordination

Only passive, open-source techniques are used.

## Investigation workflow
Each investigation follows a repeatable sequence:

1. **Target definition**
   - Domain or domain set (cluster)
   - Clear research question or hypothesis

2. **Passive data collection**
   - DNS records (A, NS, reverse DNS)
   - WHOIS (local and API-based, where available)
   - HTTP headers and publicly accessible HTML
   - SSL certificates and certificate transparency logs
   - Favicon retrieval and hashing
   - Historical DNS data (when available)

3. **Artifact preservation**
   - Raw outputs stored separately from analysis
   - Logs retained to support reproducibility
   - Machine-readable summaries generated per target

4. **Correlation & Pattern analysis**
   - Reuse of infrastructure elements
   - Repeated SSL certificate attributes
   - Shared tracking identifiers
   - Identical or recurring favicon hashes
   - Overlapping historical IP space

5. **Cluster-Level synthesis**
   - Aggregation of multiple targets
   - Identification of recurring technical fingerprints
   - Separation of signal from coincidence

6. **Analytical reporting**
   - Human-readable summaries
   - Explicit differentiation between facts and interpretation
   - Clear articulation of confidence and uncertainty

## Verification standards
- Findings are supported by multiple independent signals
- Single indicators are not treated as sufficient proof
- Technical overlap is evaluated in context (hosting providers, CDNs, reuse patterns)
- Absence of data is documented explicitly

## Automation philosophy
Automation is used to:
- Reduce manual repetition
- Ensure consistency of data collection
- Preserve analytical focus

Automation does **not**:
- Generate conclusions
- Assign intent
- Replace analyst judgment

## Ethical principles
- Passive OSINT only (no intrusion, scanning, or exploitation)
- No interaction with investigated entities
- No publication of sensitive operational details
- Protection of vulnerable groups and avoidance of harm amplification

## Limitations
OSINT findings are constrained by:
- Visibility of open sources
- Accuracy of third-party datasets
- Infrastructure reuse by unrelated actors

All conclusions are framed within these limitations.
