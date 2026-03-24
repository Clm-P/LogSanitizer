# LogSanitizer — Project Context

## Architecture
- Single-file SPA: `log-sanitizer.html`
- Zero NPM dependencies, Vanilla JS only
- Tailwind CSS via CDN Play
- Served by Apache on CentOS 9 (HTTPS, port 443)

## Code structure (inside log-sanitizer.html)
1. `RULES_DICTIONARY` : array of all regex rules
2. `PROFILES_REGISTRY` : profiles registry (Standard, Tenable, Cloud…)
3. `SanitizationEngine` : engine with consistent mapping
4. `CATEGORIES` / `STAT_META` : UI category configuration
5. UI Controller : interface management functions (bottom of file)

## Adding a regex rule
Add an object to RULES_DICTIONARY with:
- id, name, category, cssClass, prefix, regex, priority
- (optional) validator: function to filter false positives
- (optional) extractMatch: to capture a sub-group instead of the full match
- Note: the `profiles` field is inherited from old rules and ignored by the engine

Available categories: ip | email | key | path | user | hostname | cred

## Adding a profile (e.g. Splunk, Trellix)
Add an object to PROFILES_REGISTRY with:
- id: unique identifier
- name, icon, description: UI display
- categories: array of categories to enable, or 'all'
No changes to existing rules needed.

## Conventions
- Commits in English, prefixed: feat:, fix:, docs:, refactor:
- Everything must stay in a single HTML file
- Do not break offline compatibility (no external dependencies other than Tailwind CDN)
