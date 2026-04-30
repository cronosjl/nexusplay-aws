# 🎮 NexusPlay — Architecture Microservices AWS

> Plateforme de mini-jeux multijoueurs hautement disponible et scalable

---

## 🏗️ Architecture Globale
                    ┌─────────────────────────────────────────┐
                    │           GitHub Actions CI/CD           │
                    │  lint → deploy → test → load-test        │
                    └──────────────┬──────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AWS API Gateway (REST)                         │
│              Cache activé sur PROD (TTL 300s)                    │
│                                                                  │
│   /games          /users          /notifications                 │
│      │               │                   │                       │
└──────┼───────────────┼───────────────────┼───────────────────────┘
│               │                   │
▼               ▼                   ▼
┌────────────┐  ┌────────────┐  ┌──────────────────┐
│   Lambda   │  │   Lambda   │  │     Lambda       │
│game-service│  │user-service│  │notif-service     │
│ Python3.10 │  │ Python3.10 │  │ Python3.10       │
└────────────┘  └────────────┘  └────────┬─────────┘
│
▼
┌──────────────────┐
│   AWS SNS Topic   │
│  nexusplay-alerts │
└──────────────────┘
┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  CloudWatch     │   │ Secrets Manager  │   │   IAM Role       │
│  Dashboards     │   │ nexusplay/config │   │ NexusPlayLambda  │
│  Alarms/Logs    │   │ db_pass/api_key  │   │ Role             │
└─────────────────┘   └──────────────────┘   └──────────────────┘

---

## ☁️ Services AWS Utilisés

| Service | Icône | Rôle | Points |
|---------|-------|------|--------|
| **AWS Lambda** | ƛ | 3 microservices serverless auto-scalables | Microservices + Scalabilité |
| **API Gateway** | 🌐 | Point d'entrée REST, cache prod, 3 stages | Load balancing + Cache |
| **Amazon SNS** | 📢 | Notifications email/alertes en temps réel | Notifications incidents |
| **CloudWatch** | 📊 | Monitoring, alarms, logs centralisés | Monitoring centralisé |
| **Secrets Manager** | 🔐 | Gestion sécurisée des secrets et configs | Gestion des secrets |
| **IAM** | 🔑 | Rôle d'exécution avec permissions minimales | Sécurité |
| **Route 53** | 🌍 | DNS haute disponibilité Active/Backup | DNS HA |
| **GitHub Actions** | ⚙️ | CI/CD automatisé lint→deploy→test→loadtest | CI/CD |

---

## 🎯 Couverture des exigences du projet

| Exigence | Solution | Statut |
|----------|----------|--------|
| Logique microservices (2+ services) | 3 Lambda indépendants (game/user/notif) | ✅ |
| Équilibrage de charge + redondance | API Gateway Regional multi-AZ | ✅ |
| Scalabilité automatique | Lambda scale automatiquement 0→∞ | ✅ |
| Monitoring centralisé | CloudWatch Alarms + Logs sur chaque Lambda | ✅ |
| Pipeline CI/CD | GitHub Actions (lint→deploy→test→load) | ✅ |
| Test de charge avec CI/CD | Locust 20 users, 30s sur prod dans pipeline | ✅ |
| Cache performances | API Gateway cache 0.5GB TTL 300s sur prod | ✅ |
| Gestion des secrets | AWS Secrets Manager nexusplay/config | ✅ |
| Notifications incidents | SNS Topic nexusplay-alerts | ✅ |
| DNS haute disponibilité | Route 53 Active/Backup | ✅ |

---

## 📁 Structure du Projet
nexusplay-aws/
├── services/
│   ├── game_service/
│   │   └── lambda_function.py    # CRUD jeux + système join
│   ├── user_service/
│   │   └── lambda_function.py    # CRUD joueurs + leaderboard
│   └── notification_service/
│       └── lambda_function.py    # Alertes via SNS
├── scripts/
│   ├── deploy.py                 # Déploiement complet AWS
│   ├── test_api.py               # Tests fonctionnels
│   └── load_test.py              # Tests de charge Locust
├── .github/
│   └── workflows/
│       └── cicd.yml              # Pipeline CI/CD complet
├── monitoring/                   # Rapports load test
├── Makefile                      # Commandes simplifiées
├── requirements.txt
└── README.md

---

## 🚀 Déploiement

### Prérequis
```bash
pip install -r requirements.txt
```

### Configurer AWS (Whizlabs sandbox)
```bash
nano ~/.aws/credentials
```
```ini
[default]
aws_access_key_id=VOTRE_ACCESS_KEY
aws_secret_access_key=VOTRE_SECRET_KEY
```

### Recréer le rôle IAM (nouvelle sandbox)
```bash
aws iam create-role \
  --role-name NexusPlayLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"}]}'

aws iam attach-role-policy --role-name NexusPlayLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam attach-role-policy --role-name NexusPlayLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess
aws iam attach-role-policy --role-name NexusPlayLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

### Déployer
```bash
make deploy
```

### Tester
```bash
make test              # stage dev
make test STAGE=prod   # stage prod
make test-all          # tous les stages
```

### Load test
```bash
make load-test
```

---

## 🌐 Endpoints API

### Game Service — `/games`
| Méthode | Action | Body |
|---------|--------|------|
| GET | Liste tous les jeux | — |
| GET | Détail jeu | `?id=1` |
| POST | Créer un jeu | `{"name": "...", "max_players": 50}` |
| POST | Rejoindre un jeu | `{"id": "1", "action": "join"}` |
| PUT | Mettre à jour | `{"id": "1", "status": "maintenance"}` |
| DELETE | Supprimer | `{"id": "1"}` |

### User Service — `/users`
| Méthode | Action | Body |
|---------|--------|------|
| GET | Leaderboard trié par score | — |
| GET | Profil joueur | `?id=1` |
| POST | Créer joueur | `{"username": "...", "email": "..."}` |
| PUT | Mettre à jour score | `{"id": "1", "score": 2000}` |
| DELETE | Supprimer | `{"id": "1"}` |

### Notification Service — `/notifications`
| Méthode | Action | Body |
|---------|--------|------|
| GET | Health check | — |
| POST | Envoyer alerte | `{"type": "alert", "message": "...", "subject": "..."}` |

---

## 📡 Stages de déploiement

| Stage | Branche Git | URL | Cache |
|-------|-------------|-----|-------|
| dev | develop | `https://{api_id}.../dev` | ❌ |
| test | test | `https://{api_id}.../test` | ❌ |
| prod | main | `https://{api_id}.../prod` | ✅ 300s |

---

## 📊 Monitoring CloudWatch

Pour chaque Lambda, 2 alarmes sont configurées :
- **Errors** — déclenche si > 5 erreurs/minute
- **Duration** — déclenche si latence > 5000ms

Logs accessibles via :
AWS Console → CloudWatch → Log Groups → /aws/lambda/nexusplay-*

---

## 🔥 Pipeline CI/CD
Push sur GitHub
│
▼
┌─────────────┐
│  1. LINT    │ flake8 sur services/ et scripts/
└──────┬──────┘
│
▼
┌─────────────┐
│  2. DEPLOY  │ python scripts/deploy.py
└──────┬──────┘
│
▼
┌─────────────┐
│  3. TEST    │ python scripts/test_api.py {stage}
└──────┬──────┘
│ (prod uniquement)
▼
┌─────────────┐
│ 4. LOAD TEST│ Locust 20 users / 30s
└──────┬──────┘
│
▼
┌─────────────┐
│  ARTIFACT   │ config.json + rapport HTML
└─────────────┘

---

## 👥 Équipe

| Membre | Rôle |
|--------|------|
| Jean-Louis | Infrastructure AWS + CI/CD |
| Coéquipier | Services Lambda + Tests |

---

## ⚡ Commandes Make

```bash
make help        # Affiche l'aide
make install     # Installe les dépendances
make deploy      # Déploie sur AWS
make test        # Teste le stage dev
make test-all    # Teste tous les stages
make load-test   # Lance Locust load test
make lint        # Vérifie le code
make clean       # Nettoie les fichiers temporaires
```
