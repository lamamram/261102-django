# Formation Django — 5 jours (initiation + approfondissement)

Programme de référence : [Dawan — Django : initiation / approfondissement](https://www.dawan.fr/formations/python/django/django-initiation-approfondissement) (12 blocs).

## Projet fil rouge : **GestiFormation**

SaaS de gestion d'organisme de formation : catalogue de formations, sessions, inscriptions, factures, administration, e-mailing, exports.

| Jour | Blocs programme | Livré dans GestiFormation |
|---|---|---|
| **J1** | 1–4 : découverte, structure, URLs & vues, templates | Projet + app `catalog`, 3 pages (accueil, catalogue, détail), 404, thème commun |
| **J2** | 5–6 : formulaires, ORM (F, héritage, relations) | Modèles `Formation`/`Session`/`Client`, migrations, formulaires de saisie |
| **J3** | 7–9 : ModelForms, admin, authentification | Inscriptions, admin sur mesure, comptes & permissions |
| **J4** | 10–11 : i18n, tests | Catalogue fr/en, suite de tests (vues, client) |
| **J5** | 12 : e-mail, exports, OAuth, déploiement | E-mails d'inscription, export CSV, login social, config production |

## Répertoires

```
formation-django/
├── README.md                 ← ce fichier
└── jour1/
    ├── support.md            ← support pédagogique complet du jour 1
    └── assets/
        ├── mvt.svg           ← schéma MVT
        ├── cycle-requete.svg ← cycle de vie d'une requête
        └── structure-app.svg ← structure projet / applications
```

## Conventions du support

- `> 💡` : note pédagogique formateur (à ne pas forcément projeter)
- `> ⚠️` : piège fréquent des stagiaires
- `> 🛠️ Atelier` : séquence de travail stagiaire, avec checklist
- Code de référence : **Django 5.2 LTS**, **Python ≥ 3.11**
