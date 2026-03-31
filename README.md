# LogSanitizer — Zero-Server Log Sanitizer

A **100% local** web application for log sanitization — no backend, no network connection, no data leaves your machine.
Designed for air-gapped environments and the processing of confidential logs.

> **Disclaimer:** This tool is regex-based and cannot guarantee complete sanitization. Sensitive data in unexpected formats may not be detected. Always review the output before sharing.

---

## Two variants

| File | Use case | Dependencies |
|---|---|---|
| `log-sanitizer.html` | Portable / offline | Tailwind CSS via CDN (one-time load) |
| `index.html` | Served by Apache (CentOS 9, HTTPS port 443) | Fully self-contained, no CDN |

---

## Features

- **Drag & drop** or **paste** text — supports `.txt`, `.log`, `.json`, `.csv`, `.xml`, `.yaml`
- **25 built-in detection rules** across 7 categories (see below)
- **5 sanitization profiles** — Standard, Network, Application, Cloud, Tenable/Nessus
- **Consistent anonymization** — the same value always maps to the same tag throughout the file
- **Side-by-side diff view** with color-coded highlights
- **Export** sanitized file + JSON mapping table
- **Rules Manager** — view built-in rules and create custom ones (stored in the browser)
- **Profile Manager** — create, import, and export custom profiles
- **Versioning** — version displayed in the UI header (`v1.0.0`)

---

## Detection rules (25 built-in)

### IP / Network (`ip`)
| Rule | Example detected |
|---|---|
| IPv4 Addresses | `192.168.1.10` |
| IPv6 Addresses | `fe80::1` |
| MAC Addresses | `00:1A:2B:3C:4D:5E` |

### Email (`email`)
| Rule | Example detected |
|---|---|
| Email Addresses | `user@corp.internal` |

### Keys & Tokens (`key`)
| Rule | Example detected |
|---|---|
| AWS Keys | `AKIAIOSFODNN7EXAMPLE` |
| AWS ARNs | `arn:aws:iam::123456789012:user/...` |
| UUIDs | `550e8400-e29b-41d4-a716-446655440000` |
| Hashes — labeled | `sha256=abc123...`, `md5: def456...` |
| Hashes — standalone (MD5/SHA1/SHA256/SHA512) | bare 32/40/64/128-char hex strings |
| Password hashes (bcrypt/argon2/sha-crypt) | `$2b$12$...`, `$argon2id$...` |
| Generic API Keys | `api_key=abc123...` |
| Bearer Tokens | `Bearer eyJhb...` |
| JWT Tokens | `eyJhbGciOiJIUzI1NiJ9...` |
| Hex Tokens (high entropy) | long hex strings with sufficient entropy |
| Session IDs | `JSESSIONID=abc...`, `phpsessid=...` |

### Paths (`path`)
| Rule | Example detected |
|---|---|
| Windows Paths | `C:\Users\admin\secret.txt` |
| Unix Paths | `/home/user/config/...` |
| UNC Paths | `\\server\share\file` |

### Users (`user`)
| Rule | Example detected |
|---|---|
| Usernames (patterns) | `username=jdoe`, `login: admin` |
| Windows DOMAIN\User | `CORP\john.doe` |

### Hostnames / URLs (`hostname`)
| Rule | Example detected |
|---|---|
| Hostnames / Internal Domains | `server01.corp.internal` |
| Full URLs | `https://internal.app.corp/...` |
| NetBIOS / DNS Name (Nessus) | `DNS Name: dc01.corp.local` |

### Credentials (`cred`)
| Rule | Example detected |
|---|---|
| Scan Credentials (SSH/SMB/WMI) | `smb_password=...` |
| SNMP Community Strings | `community string: public` |

---

## Profiles

| Profile | Categories activated |
|---|---|
| **Standard** | All rules |
| **Network** | `ip`, `hostname` |
| **Application** | `user`, `path`, `key`, `email` |
| **Cloud** | `key`, `hostname`, `ip`, `email` |
| **Tenable / Nessus** | `ip`, `key`, `user`, `hostname`, `cred` |

Custom profiles can be created in the UI and exported/imported as JSON.

---

## Usage

Open `log-sanitizer.html` in a browser — no installation required.

For the deployed version (`index.html`), serve from Apache. The server version loads shared rules and profiles from `data/shared-rules.json` and `data/shared-profiles.json`.

---

## Extending

### Adding a detection rule
Add an object to `RULES_DICTIONARY` in `log-sanitizer.html`:
```js
{
  id: 'my_rule',          // unique string
  name: 'My Rule',        // display name
  category: 'key',        // ip | email | key | path | user | hostname | cred
  cssClass: 'san-key',    // CSS highlight class
  prefix: 'MY_TOKEN',     // replacement prefix
  priority: 90,           // lower = applied first
  regex: /pattern/g,
  // optional:
  validator: (match) => true,           // return false to discard a match
  extractMatch: (full, groups) => groups[0], // capture a sub-group only
}
```

For the server version, add the equivalent entry to `data/shared-rules.json`.

### Adding a profile
Add an object to `PROFILES_REGISTRY` in `log-sanitizer.html`:
```js
{
  id: 'splunk',
  name: 'Splunk',
  icon: '📊',
  description: 'Splunk logs — index, sourcetype, credentials',
  categories: ['user', 'key', 'hostname', 'ip', 'cred'],
}
```

---

## Versioning

Version is set via `APP_VERSION` in both `index.html` and `log-sanitizer.html`.

```
MAJOR — breaking changes (e.g. data format change)
MINOR — new features (new rule categories, new profile types)
PATCH — bug fixes
```

Release process:
1. Update `APP_VERSION = '1.x.x'` in both HTML files
2. `git commit -m "feat: release v1.x.x"`
3. `git tag v1.x.x`

---

## Architecture

- Single-file SPA — everything in one `.html` file (portable version)
- Zero NPM dependencies — Vanilla JS only
- Tailwind CSS via CDN Play (portable) or inlined utility classes (deployed)
- Offline compatible — no external runtime dependencies
