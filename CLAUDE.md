# LogShield — Contexte projet

## Architecture
- Application SPA mono-fichier : `log-sanitizer.html`
- Zéro dépendance NPM, Vanilla JS uniquement
- Tailwind CSS via CDN Play
- Servie par Apache sur CentOS 9 (HTTPS, port 443)

## Structure du code (dans log-sanitizer.html)
- `RULES_DICTIONARY` : tableau de règles regex (ligne ~180)
- `SanitizationEngine` : classe moteur avec mapping cohérent
- `CATEGORIES` / `STAT_META` : config UI des catégories
- Contrôleur UI : fonctions de gestion de l'interface (bas du fichier)

## Pour ajouter une règle regex
Ajouter un objet dans RULES_DICTIONARY avec : id, name, category,
cssClass, prefix, regex, profiles, priority, et optionnellement
validator et extractMatch.

## Conventions
- Commits en français, préfixés : feat:, fix:, docs:, refactor:
- Tout doit rester dans un seul fichier HTML
- Ne pas casser la compatibilité offline (pas de dépendance externe autre que Tailwind CDN)
