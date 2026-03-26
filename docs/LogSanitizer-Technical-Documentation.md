# LogSanitizer — Technical Documentation

**Version**: 1.0
**Classification**: Internal
**Audience**: CISO, Design Authority, Security Architects
**Last updated**: 2026-03-25

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Security Architecture](#3-security-architecture)
4. [Functional Overview](#4-functional-overview)
5. [Detection Rules Reference](#5-detection-rules-reference)
6. [Sanitization Profiles](#6-sanitization-profiles)
7. [Sanitization Engine](#7-sanitization-engine)
8. [Deployment Models](#8-deployment-models)
9. [Data Flow Diagrams](#9-data-flow-diagrams)
10. [Customization & Extensibility](#10-customization--extensibility)
11. [Performance Characteristics](#11-performance-characteristics)
12. [Risk Assessment](#12-risk-assessment)
13. [Compliance Considerations](#13-compliance-considerations)
14. [Operational Guide](#14-operational-guide)

---

## 1. Executive Summary

LogSanitizer is a **zero-server, client-side log sanitization tool** that strips sensitive data (IP addresses, credentials, API keys, usernames, file paths, hostnames) from log files before they are shared with third parties, published in tickets, or transmitted outside the organization.

**Key properties:**

- **No data leaves the browser** — all processing is performed locally in the user's browser using JavaScript. No backend, no API calls, no telemetry.
- **Deterministic anonymization** — identical sensitive values always map to the same replacement tag within a session, preserving correlations for analysis while removing actual values.
- **Air-gap compatible** — the portable version (`log-sanitizer.html`) is a single self-contained HTML file with zero external dependencies.
- **Extensible** — administrators manage shared detection rules and profiles via JSON files; users can create personal overrides stored in their browser.

---

## 2. Problem Statement

Security operations teams routinely need to share log extracts with vendors, auditors, or cross-functional teams. These logs frequently contain:

- Internal IP addresses and network topology indicators
- User credentials and session tokens
- API keys, AWS ARNs, JWTs, and other secrets
- Internal hostnames, file paths, and UNC paths
- Email addresses and account identifiers

Manual redaction is error-prone and time-consuming. Automated server-side solutions introduce data-handling risks (logs must transit a server). LogSanitizer addresses both issues by providing **automated, browser-local sanitization** with a deterministic mapping that enables post-sanitization analysis.

---

## 3. Security Architecture

### 3.1 Zero-Trust Data Handling

```
  User's Browser (trust boundary)
  ┌─────────────────────────────────────────────────┐
  │                                                   │
  │   Log file ──► SanitizationEngine ──► Sanitized   │
  │     (in)          (JS, local)           (out)     │
  │                                                   │
  │   Mapping table stays in memory only              │
  │   No localStorage of log content                  │
  │   No network calls for processing                 │
  │                                                   │
  └─────────────────────────────────────────────────┘
           │                          │
           │ (never transmitted)      ▼
           ▼                    User downloads
      Original log              sanitized file
      (remains local)           + mapping JSON
```

**No data exfiltration vector exists** — the application makes no outbound network requests for log processing. The only network activity is the initial page load and (in deployed mode) fetching the shared rules/profiles JSON files, which contain no user data.

### 3.2 Technology Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Vanilla JavaScript (ES2020) | No build pipeline, no supply chain risk |
| Styling | Custom CSS utility classes | No CDN dependency (Tailwind removed) |
| Dependencies | **Zero** (no npm, no node_modules) | Eliminates supply chain attack surface |
| Server | Apache on CentOS 9 (HTTPS, port 443) | Static file serving only |
| Storage | Browser localStorage (custom rules/profiles only) | No server-side database |

### 3.3 Threat Model

| Threat | Mitigation |
|---|---|
| Data exfiltration via network | No backend; no outbound API calls; all processing is client-side |
| XSS via malicious log content | All output passed through `escapeHtml()` before DOM insertion |
| XSS via malicious custom rules (localStorage) | Rule names, IDs, profile icons escaped with `escapeHtml()` in all template literals |
| Supply chain compromise | Zero dependencies; no npm, no CDN, no build step |
| Unauthorized rule modification (deployed) | Shared rules/profiles are read-only JSON on the server; only admins with filesystem access can modify them |
| localStorage poisoning | Custom rules are validated (regex compilation tested) before use; malformed data fails gracefully |

---

## 4. Functional Overview

### 4.1 User Workflow

```
1. Load log file    ──►  Drag & drop, file browse, or paste text
                          (also supports Ctrl+V global shortcut)

2. Select profile   ──►  Standard, Network, Application, Cloud,
                          Tenable/Nessus, or a custom profile

3. Toggle categories ──► Enable/disable: IPs, Emails, Keys, Paths,
                          Users, Hostnames, Credentials

4. Review results   ──►  Side-by-side view (original vs sanitized)
                          with color-coded highlights per category

5. Export           ──►  Download sanitized file (.txt)
                          Copy to clipboard
                          Export mapping table (JSON)
```

### 4.2 Supported Input Formats

`.txt`, `.log`, `.json`, `.csv`, `.xml`, `.yaml`, `.yml`

Files are read as plain text via `FileReader.readAsText()`. No parsing of structured formats is performed — the regex engine operates on raw text content.

### 4.3 Output Artifacts

| Artifact | Format | Contains |
|---|---|---|
| Sanitized log | Plain text | Original log with sensitive values replaced by tags (e.g. `[IP_1]`, `[EMAIL_3]`) |
| Mapping table | JSON | Bidirectional mapping: tag <-> original value, category, occurrence count |

The mapping table enables authorized personnel to reverse the sanitization when needed, while the sanitized log can be safely shared externally.

---

## 5. Detection Rules Reference

LogSanitizer ships with **23 detection rules** organized into 7 categories. Rules execute in priority order (lower number = higher priority).

### 5.1 IP Addresses & MAC (`ip`)

| Rule | Priority | Detects | Validator |
|---|---|---|---|
| `ipv6` | 10 | Full/abbreviated IPv6, IPv4-mapped, link-local (fe80::) | — |
| `ipv4` | 20 | Standard IPv4 (0.0.0.0–255.255.255.255) | Rejects version numbers (e.g. "version 1.2.3.4") |
| `mac_address` | 25 | MAC addresses (colon or dash separated) | — |

### 5.2 Email Addresses (`email`)

| Rule | Priority | Detects |
|---|---|---|
| `email` | 30 | Standard email format (user@domain.tld) |

### 5.3 API Keys, Tokens & Secrets (`key`)

| Rule | Priority | Detects | Notes |
|---|---|---|---|
| `aws_key` | 40 | AWS access keys (AKIA/ASIA prefix) | 20-character format |
| `aws_arn` | 41 | AWS ARNs (arn:aws:service:region:account:resource) | Includes 12-digit account ID |
| `uuid` | 43 | UUIDs (8-4-4-4-12 hex format) | — |
| `generic_api_key` | 45 | Key-value patterns: api_key=, secret=, password=, token=, etc. | Extracts value only (capture group) |
| `bearer_token` | 46 | Bearer authentication tokens (20+ characters) | — |
| `jwt_token` | 47 | JSON Web Tokens (eyJ...eyJ...signature) | 3-part base64url structure |
| `high_entropy_hex` | 48 | Long hex strings (32+ chars) | Entropy filter: requires 6+ unique hex digits |
| `session_id` | 49 | Session identifiers (JSESSIONID, PHPSESSID, sid, sess) | Extracts value only |

### 5.4 Credentials (`cred`)

| Rule | Priority | Detects | Notes |
|---|---|---|---|
| `scan_credentials` | 50 | Scan tool credentials (smb_login, ssh_password, wmi_user, etc.) | Covers SMB, SSH, WMI, Telnet, RSH, RDP, FTP |
| `snmp_community` | 51 | SNMP community strings and community names | — |

### 5.5 File Paths (`path`)

| Rule | Priority | Detects |
|---|---|---|
| `unc_path` | 59 | Windows UNC paths (`\\server\share\...`) |
| `path_windows` | 60 | Windows drive paths (`C:\Users\...`) |
| `path_unix` | 61 | Unix paths under known roots (/home, /var, /etc, /opt, /usr, /tmp, /srv, /mnt, /root, /proc, /sys, /dev, /log, /data, /app, /config, /backup) |

### 5.6 User Accounts (`user`)

| Rule | Priority | Detects | Validator |
|---|---|---|---|
| `username_pattern` | 70 | Label-based usernames: user=, login=, account=, owner=, author=, created_by=, assignee=, admin=, operator= | Extracts value only |
| `windows_domain_user` | 71 | `DOMAIN\username` format | Rejects leading backslash (avoids UNC path collision) |

### 5.7 Hostnames & URLs (`hostname`)

| Rule | Priority | Detects |
|---|---|---|
| `hostname` | 80 | Internal domains: .internal, .local, .corp, .intranet, .lan, .private, .home, .test, .dev, .staging, .prod, .int, .ad, .mil, .dom, .domain |
| `url` | 81 | Full HTTP/HTTPS URLs |
| `nessus_host_info` | 83 | Nessus output patterns: "NetBIOS name:", "DNS Name:", "Common Name:", "Hostname:" |

---

## 6. Sanitization Profiles

Profiles determine which **categories** of rules are active during sanitization.

| Profile | Icon | Categories | Use Case |
|---|---|---|---|
| **Standard** | Shield | **All** | Default. Maximum protection when sharing logs externally |
| **Network** | Globe | ip, hostname | Network infrastructure logs, firewall exports, PCAP metadata |
| **Application** | Gear | user, path, key, email | Application error logs, stack traces, audit trails |
| **Cloud** | Cloud | key, hostname, ip, email | AWS CloudTrail, Azure Activity Logs, GCP audit logs |
| **Tenable / Nessus** | Microscope | ip, key, user, hostname, cred | Nessus scan reports, SecurityCenter exports |

Custom profiles can be created by users (stored in browser localStorage) or by administrators (added to `data/shared-profiles.json`).

---

## 7. Sanitization Engine

### 7.1 Algorithm

The engine uses a **two-pass approach**:

```
Pass 1 — Detection
  For each active rule (sorted by priority ascending):
    Execute regex against the full text
    Apply validator function (if defined) to filter false positives
    Apply extractMatch function (if defined) to isolate sub-group
    Assign a deterministic replacement tag via getOrCreateTag()
    Record: { start, end, tag, cssClass, originalValue }

Pass 2 — Deduplication & Replacement
  Sort all replacements by position (ascending)
  Remove overlapping matches (keep the one that starts first;
    for same start position, keep the longest)
  Build sanitized text and highlighted HTML in a single forward pass
```

### 7.2 Consistency Guarantee

The `getOrCreateTag()` method ensures **deterministic mapping**:

```
Same input value  →  Same replacement tag (within a session)

Example:
  "192.168.1.100" appears 47 times in the log
  → All 47 occurrences become [IP_1]
  → The mapping table records: [IP_1] ↔ 192.168.1.100 (count: 47)
```

This preserves analytical value: an analyst can see that `[IP_1]` communicated with `[IP_3]` on `[HOST_2]` without knowing the actual addresses.

### 7.3 Tag Format

Tags follow the pattern `[PREFIX_N]` where:
- `PREFIX` is the rule's prefix (e.g. IP, EMAIL, AWS_KEY, PATH, USER, HOST, CRED)
- `N` is a sequential counter per prefix, starting at 1

### 7.4 Overlap Resolution

When multiple rules match the same text region:
- Replacements are sorted by start position
- For overlapping regions, the first (highest-priority) match wins
- This prevents double-sanitization (e.g., an email address being matched by both the email rule and the hostname rule)

---

## 8. Deployment Models

### 8.1 Portable Mode (`log-sanitizer.html`)

```
Single HTML file — fully self-contained
├── CSS (utility classes, no CDN)
├── HTML (UI structure)
└── JavaScript
    ├── RULES_DICTIONARY (23 rules, hardcoded)
    ├── PROFILES_REGISTRY (5 profiles, hardcoded)
    ├── SanitizationEngine
    └── UI Controller
```

**Characteristics:**
- Zero network requirements — works on air-gapped systems
- Can be distributed via USB, email, or file share
- Rules are embedded and cannot be centrally updated
- Custom rules/profiles stored in browser localStorage

**Use cases:** Incident response on isolated systems, field operations, personal workstations without server access.

### 8.2 Deployed Mode (`index.html` + `data/`)

```
/var/www/logsanitizer/          (Apache docroot)
├── index.html                  (application)
└── data/
    ├── shared-rules.json       (admin-managed, 23 rules)
    └── shared-profiles.json    (admin-managed, 5 profiles)
```

**Characteristics:**
- Served via Apache/HTTPS on CentOS 9 (port 443)
- Rules and profiles loaded from server JSON files at startup
- Centralized rule management — admins update JSON files, all users get the changes on next page load
- Falls back gracefully if JSON files are unavailable (works like portable mode)
- Custom user rules/profiles still stored in browser localStorage

**Precedence model:**

```
Final active rules = shared-rules.json (read-only)
                   + localStorage custom rules (per-user)

Final profiles     = shared-profiles.json (read-only)
                   + localStorage custom profiles (per-user)
```

Users see shared rules/profiles as locked (read-only) in the UI. They can duplicate them to create editable custom variants.

### 8.3 Validators Registry

Since JSON cannot carry JavaScript functions, validator logic is stored in a **registry pattern** in `index.html`:

```javascript
const VALIDATORS = {
  ipv4_version_filter: (match, context, matchIndex) => { ... },
  hex_entropy_filter:  (match) => { ... },
  windows_domain_filter: (match) => { ... },
};
```

JSON rules reference validators by ID (`"validatorId": "ipv4_version_filter"`). During hydration, the validator function is resolved from the registry and attached to the rule object.

**Adding a new validator:** Define the function in the `VALIDATORS` object, then reference its key in the JSON rule's `validatorId` field.

---

## 9. Data Flow Diagrams

### 9.1 Sanitization Flow

```
                          ┌─────────────────────┐
                          │   User's Browser     │
                          │                       │
  Log file (.txt/.log)    │   ┌───────────────┐   │
  ─────────────────────►  │   │ FileReader    │   │
                          │   │ (readAsText)  │   │
                          │   └──────┬────────┘   │
                          │          ▼             │
                          │   ┌───────────────┐   │
  Profile selection  ───► │   │ Sanitization  │   │
  Category toggles   ───► │   │ Engine        │   │
                          │   │               │   │
                          │   │ Pass 1: Detect│   │
                          │   │ Pass 2: Replace│  │
                          │   └──────┬────────┘   │
                          │          │             │
                          │    ┌─────┼──────┐     │
                          │    ▼     ▼      ▼     │
                          │  Plain  HTML  Mapping  │
                          │  text   view  table    │
                          │    │     │      │     │
                          └────┼─────┼──────┼─────┘
                               ▼     ▼      ▼
                          Download  UI    JSON
                          (.txt)  display  export
```

### 9.2 Data Persistence Flow (Deployed Mode)

```
  ┌──────────────┐         ┌────────────────────────┐
  │ Admin        │         │ Web Server (Apache)     │
  │              │  edit   │                          │
  │ SSH / SFTP ──┼────────►│ data/shared-rules.json  │
  │              │         │ data/shared-profiles.json│
  └──────────────┘         └───────────┬──────────────┘
                                       │ fetch (HTTPS)
                           ┌───────────▼──────────────┐
                           │ User's Browser            │
                           │                            │
                           │ Shared rules  (read-only)  │
                           │       +                    │
                           │ localStorage  (read-write) │
                           │ ├── custom rules           │
                           │ └── custom profiles        │
                           │                            │
                           │ Import ◄── JSON file       │
                           │ Export ──► JSON file        │
                           └────────────────────────────┘
```

---

## 10. Customization & Extensibility

### 10.1 Adding a Shared Rule (Admin)

Edit `data/shared-rules.json` and add an object:

```json
{
  "id": "my_custom_pattern",
  "name": "Internal Project Codes",
  "category": "key",
  "prefix": "PROJECT",
  "priority": 90,
  "regexPattern": "\\bPRJ-[0-9]{4,8}\\b",
  "regexFlags": "g"
}
```

Optional fields:
- `"extractGroup": true` — use capture group 1 instead of the full match
- `"validatorId": "my_validator"` — reference a validator function (must be added to the `VALIDATORS` object in `index.html`)

### 10.2 Adding a Shared Profile (Admin)

Edit `data/shared-profiles.json` and add:

```json
{
  "id": "splunk",
  "name": "Splunk",
  "icon": "📊",
  "description": "Splunk logs — index, sourcetype, credentials",
  "categories": ["user", "key", "hostname", "ip", "cred"]
}
```

Available categories: `ip`, `email`, `key`, `path`, `user`, `hostname`, `cred`
Use `"categories": "all"` to enable every category.

### 10.3 User Custom Rules (Browser)

Users can create personal rules via the **Rules Manager** UI:
1. Click the Rules button in the control bar
2. Click **+ New rule**
3. Fill in: name, category, prefix, priority, regex pattern, flags
4. Optionally enable capture group extraction
5. Test the rule with sample input using the **Live test** panel
6. Save — the rule is stored in browser localStorage

### 10.4 Import / Export

Users can share custom rules and profiles with colleagues via JSON files:

| Action | Location | Format |
|---|---|---|
| Export custom rules | Rules Manager > Export | `logsanitizer-custom-rules.json` |
| Import custom rules | Rules Manager > Import | Same JSON format |
| Export custom profiles | Profile Manager > Export | `logsanitizer-custom-profiles.json` |
| Import custom profiles | Profile Manager > Import | Same JSON format |

Imported rules are merged with existing custom rules. ID collisions are resolved by appending a timestamp suffix.

---

## 11. Performance Characteristics

### 11.1 Optimizations

| Feature | Trigger | Mechanism |
|---|---|---|
| **Virtual scrolling** | Files with > 3,000 lines | Only visible lines are rendered in the DOM; off-screen lines are computed on scroll |
| **Async processing** | Files > 512 KB | Processing yields to the browser event loop via `setTimeout`, preventing UI freeze |
| **Debounced category toggles** | Rapid toggle clicks | 300ms debounce prevents redundant re-sanitization runs |
| **Stale result guard** | New sanitization triggered during processing | A processing ID counter discards results from superseded runs |

### 11.2 Scalability

| Metric | Typical Value |
|---|---|
| Small log (< 100 KB, < 1,000 lines) | Instant (< 100ms) |
| Medium log (1 MB, ~10,000 lines) | 1–3 seconds |
| Large log (10 MB, ~100,000 lines) | 5–15 seconds (virtual scrolling active) |
| Memory usage | Proportional to log size + mapping table |

The main bottleneck is regex execution in JavaScript. For very large files (> 50 MB), users should consider splitting logs before sanitization.

---

## 12. Risk Assessment

### 12.1 Residual Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Regex miss** — a sensitive pattern not covered by existing rules | Medium | Medium | Custom rules can be added; Live test panel validates detection; Standard profile enables all rules |
| **False positive** — non-sensitive data incorrectly redacted | Low | Low | Validator functions filter known false positives; side-by-side view enables manual review |
| **localStorage tampering** — malicious custom rules injected | Very Low | Low | Rules are validated at load time; regex compilation errors are caught; HTML output is escaped |
| **Shared JSON file tampering** — admin-managed rules modified maliciously | Very Low | Medium | Server-side file permissions (root-owned); HTTPS serving; standard server hardening applies |
| **Browser memory exhaustion** — very large log file | Low | Low | Virtual scrolling limits DOM size; user guidance on file size limits |

### 12.2 What LogSanitizer Does NOT Do

- **Does not guarantee 100% detection** — novel or unusual formats may evade regex rules. Manual review of the sanitized output is recommended for high-sensitivity scenarios.
- **Does not encrypt** — sanitized output is anonymized, not encrypted. The mapping table (if exported) contains the bidirectional mapping and must be handled according to the same classification as the original log.
- **Does not persist state server-side** — there is no audit trail of who sanitized what. Organizations requiring this should implement logging at the web server level (access logs).

---

## 13. Compliance Considerations

### 13.1 GDPR / Data Privacy

LogSanitizer supports GDPR compliance by enabling the removal of personally identifiable information (PII) from logs **before** they are shared with third parties. Specifically:
- IP addresses (Article 4 — personal data when attributable)
- Email addresses
- Usernames and account identifiers
- File paths containing usernames (e.g. `/home/jdoe/`)

Since all processing occurs client-side, **no personal data is transmitted to or stored on the server**.

### 13.2 PCI-DSS

Relevant for sanitizing logs that may contain:
- API keys and tokens (Requirement 3 — protect stored cardholder data)
- Credentials and session identifiers (Requirement 8 — authenticate access)
- Internal network topology (Requirement 1 — network segmentation)

### 13.3 Classification Handling

The portable version (`log-sanitizer.html`) can be used on classified systems without network connectivity. The deployed version makes no outbound connections beyond serving static files on the internal network.

---

## 14. Operational Guide

### 14.1 Deployment Steps

```bash
# 1. Copy files to Apache docroot
cp index.html /var/www/logsanitizer/
cp -r data/   /var/www/logsanitizer/

# 2. Set ownership and permissions
chown -R apache:apache /var/www/logsanitizer/
chmod 644 /var/www/logsanitizer/index.html
chmod 755 /var/www/logsanitizer/data/
chmod 644 /var/www/logsanitizer/data/*.json

# 3. Apache virtual host (minimal)
<VirtualHost *:443>
    ServerName logsanitizer.corp.internal
    DocumentRoot /var/www/logsanitizer
    SSLEngine on
    SSLCertificateFile    /etc/pki/tls/certs/logsanitizer.crt
    SSLCertificateKeyFile /etc/pki/tls/private/logsanitizer.key

    <Directory /var/www/logsanitizer>
        Options -Indexes
        AllowOverride None
        Require all granted
    </Directory>

    # Cache policy for shared data files
    <LocationMatch "^/data/.*\.json$">
        Header set Cache-Control "no-cache, must-revalidate"
    </LocationMatch>
</VirtualHost>
```

### 14.2 Updating Shared Rules

```bash
# Edit the rules file
vim /var/www/logsanitizer/data/shared-rules.json

# Validate JSON syntax
python3 -m json.tool /var/www/logsanitizer/data/shared-rules.json > /dev/null

# Users get the update on next page load (no restart needed)
```

### 14.3 Distributing the Portable Version

```bash
# The portable version is a single file
cp log-sanitizer.html /media/usb/LogSanitizer.html

# It can also be emailed or placed on a file share
# No installation required — double-click to open in any modern browser
```

### 14.4 Browser Compatibility

| Browser | Minimum Version | Notes |
|---|---|---|
| Chrome / Edge | 88+ | Full support |
| Firefox | 85+ | Full support |
| Safari | 14+ | Full support |
| Internet Explorer | Not supported | Uses ES2020 features (async/await, optional chaining) |

---

*Document prepared for internal review. For questions or change requests, contact the Security Engineering team.*
