# LogSanitizer — Zero-Server Log Sanitizer

A **100% local** web application for log sanitization (no backend, no network connection).
Designed for air-gapped environments and the processing of confidential logs.

## Features
- Drag & drop (.txt, .log, .json, .csv, .xml, .yaml)
- 16 regex detection rules (IPv4/IPv6, emails, API keys, paths, etc.)
- 4 sanitization profiles (Standard, Network, Application, Cloud)
- Consistent anonymization (same IP → same tag everywhere)
- Side-by-side diff view with color-coded highlights
- Export sanitized file + JSON mapping table

## Usage
Open `log-sanitizer.html` in a browser. No installation required.

