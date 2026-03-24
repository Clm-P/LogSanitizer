# LogShield — Zero-Server Log Sanitizer

Application web de sanitization de logs **100% locale** (zéro backend, zéro connexion réseau).
Conçue pour les environnements airgapped et le traitement de logs confidentiels.

## Fonctionnalités
- Drag & drop (.txt, .log, .json, .csv, .xml, .yaml)
- 16 règles de détection regex (IPv4/IPv6, emails, clés API, chemins, etc.)
- 4 profils de nettoyage (Standard, Réseau, Applicatif, Cloud)
- Anonymisation cohérente (même IP → même tag partout)
- Vue diff côte à côte avec highlights colorés
- Export fichier nettoyé + table de mapping JSON

## Utilisation
Ouvrir `log-sanitizer.html` dans un navigateur. Aucune installation requise.
