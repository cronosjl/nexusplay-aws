# NexusPlay — Architecture Microservices Serverless

[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)

**NexusPlay** est une plateforme de mini-jeux multijoueurs conçue pour une haute disponibilité et une scalabilité extrême. Ce projet implémente une architecture microservices serverless robuste sur AWS, automatisée via une pipeline CI/CD complète.

##  Documentation Détaillée

Pour approfondir certains aspects techniques, veuillez consulter les documents suivants :
*   📖 [Guide de Mise en Œuvre](docs/guide.md) : Détails sur l'exploitation SRE, la gestion des secrets et la configuration avancée.
*   🧪 [Protocole de Test & POC](docs/projet.md) : Comment valider les performances, rapport complet du Proof of Concept et galerie de preuves.

---

## ️ Architecture du Système

L'architecture repose sur une approche **Event-Driven** et **Serverless**, garantissant une isolation complète des services et une mise à l'échelle automatique sans gestion de serveurs.

```mermaid
graph TD
    User((Joueur)) --> Route53[Route 53 HA DNS]
    Route53 --> APIGW[AWS API Gateway]
    
    subgraph "Couche de Distribution"
        APIGW --> Cache[(API Cache - Prod)]
    end

    subgraph "Microservices (AWS Lambda)"
        APIGW -- /games --> GameService[Game Service]
        APIGW -- /users --> UserService[User Service]
        APIGW -- /notifications --> NotifService[Notification Service]
    end

    subgraph "Gestion & Monitoring"
        GameService & UserService & NotifService --> CloudWatch[CloudWatch Metrics/Logs]
        CloudWatch --> Alarms[CloudWatch Alarms]
        Alarms --> SNS[Amazon SNS]
        SNS --> Email((Alertes SRE))
        
        GameService & UserService --> Secrets[AWS Secrets Manager]
    end

    subgraph "CI/CD Pipeline"
        GH[GitHub Actions] --> Lint[Linting]
        Lint --> Deploy[Automated Deploy]
        Deploy --> FuncTest[Functional Tests]
        FuncTest --> LoadTest[Locust Load Test]
    end
```

### Points Clés
- **Haute Disponibilité :** Multi-AZ par défaut via API Gateway et Lambda.
- **DNS HA :** Configuration Route 53 avec basculement automatique.
- **Scalabilité :** Passage de 0 à des milliers de requêtes instantanément.
- **Performance :** Mise en cache API Gateway (TTL 300s sur Prod).

---

##  Stack Technique

| Domaine | Technologies |
| :--- | :--- |
| **Cloud Provider** | Amazon Web Services (AWS) |
| **Compute** | AWS Lambda (Python 3.10) |
| **API Management** | AWS API Gateway (REST, Regional) |
| **Sécurité** | AWS IAM, AWS Secrets Manager |
| **Messaging** | Amazon SNS (Simple Notification Service) |
| **Observabilité** | CloudWatch (Logs, Metrics, Alarms, Dashboards) |
| **CI/CD** | GitHub Actions |
| **Tests** | Pytest (Fonctionnels), Locust (Charge) |

---

##  Guide de Déploiement

### 1. Préparation
```bash
make install
```

### 2. Déploiement via Terraform
Le déploiement est automatisé via **Terraform** pour garantir une infrastructure immuable :
1. **IAM Roles** : Provisionnement des rôles et politiques de sécurité.
2. **Services AWS** : Création de SNS, Secrets Manager et CloudWatch Alarms.
3. **Lambda & API Gateway** : Déploiement des microservices et exposition via l'API Gateway avec cache.

```bash
terraform init
terraform apply
```

---

##  Guide SRE & Ops (Exploitation)

###  Monitoring & Observabilité
Accédez aux métriques via la console CloudWatch :
- **Logs** : Préfixe `/aws/lambda/nexusplay-*`.
- **Alarmes** : Errors > 5 ou Duration > 5s déclenchent une alerte SNS.

![Metrics CloudWatch](images/monitoringcentralisecloudwatchmetrics.png)
*Analyse des métriques détaillées par service.*

###  Gestion des Secrets
Tous les secrets sont centralisés dans **AWS Secrets Manager** (`nexusplay/config`). Ne jamais stocker de secrets en clair dans le code.

![Secret Management](images/Integrerunsysteemedegestiondessecretssecuriseviaawssecretmanager.png)

###  Incident Response (Playbook)

| Incident | Action Immédiate |
| :--- | :--- |
| **Erreurs 5XX** | Consulter CloudWatch Logs pour identifier l'exception Python. |
| **Timeout (504)** | Vérifier la latence des services externes ou augmenter le timeout Lambda. |
| **Throttling** | Analyser la concurrence Lambda et demander une augmentation de quota si nécessaire. |

---

##  Rapport du POC (Proof of Concept)

### Objectifs Atteints
- **Microservices** : 3 services isolés (Game, User, Notif). ✅
- **Auto-scaling** : Validation de la montée en charge automatique. ✅
- **CI/CD** : Pipeline complet automatisé (Lint -> Deploy -> Test -> Load Test). ✅
- **Haute Disponibilité** : Architecture Multi-AZ et DNS HA simulé. ✅

### Résultats des Tests de Charge
Simulation avec 20 utilisateurs simultanés via Locust :
- **Taux de succès** : 100%
- **Temps de réponse moyen** : ~150ms

![Load Test Result](images/testdechargepourvaliderlesperformancesavecCICD..png)

---

##  Galerie Complète des Preuves Techniques

###  Logique Microservices & API
| Image | Description |
| :--- | :--- |
| ![Lambda](images/logiquemicroservicesfonctionlambda.png) | Fonctions Lambda déployées. |
| ![API Gateway](images/Logiquemicroservicesapigateway.png) | Structure des ressources API. |
| ![API Details](images/Logiquemicroservicesapigatewaydetails.png) | Configuration des méthodes. |

### ⚖ Équilibrage de Charge & Réseau
| Image | Description |
| :--- | :--- |
| ![Network Mapping](images/equilibragedeschargesloadbalancernetworkmapping.png) | Flux réseau du load balancer. |
| ![LB Dashboard](images/equilibragedeschargesloadbalancerdashboard.png) | Dashboard de performance. |
| ![LB Monitoring](images/equilibragedeschargesloadbalancermonitoring.png) | Métriques de trafic. |

###  Haute Disponibilité DNS
| Image | Description |
| :--- | :--- |
| ![Route 53](images/serveurDNShautementdisponiblerouteS3.png) | Route 53 vers S3/Static. |
| ![VPC 1](images/serveurDNShautementdisponiblevpc1.png) | VPC Multi-AZ (Partie 1). |
| ![VPC 2](images/serveurDNShautementdisponiblevpc2.png) | VPC Multi-AZ (Partie 2). |

### 🚀 Scalabilité Automatique
| Image | Description |
| :--- | :--- |
| ![Auto-scaling 1](images/autoscaling1.png) | Politique d'Auto-scaling. |
| ![Auto-scaling 2](images/autoscaling2.png) | Concurrence et limites. |
| ![Auto-scaling 3](images/autoscaling3.png) | Événements de mise à l'échelle. |

###  Monitoring & Alerting (CloudWatch)
| Image | Description |
| :--- | :--- |
| ![Alarms](images/monitoringcentralisecloudwatchalarms.png) | Alarmes CloudWatch actives. |
| ![Dashboard](images/monitoringcentralisecloudwatchdashboard.png) | Dashboard opérationnel. |
| ![Dashboard Details](images/monitoringcentralisecloudwatchdashboarddetails.png) | Widgets de monitoring. |
| ![Resource Health](images/monitoringcentralisecloudwatchResourceHealth.png) | État de santé des ressources. |

###  Pipeline CI/CD (GitHub Actions)
| Image | Description |
| :--- | :--- |
| ![Pipeline 1](images/pipeline.png) | Workflow global réussi. |
| ![Pipeline 2](images/pipeline2.png) | Historique des déploiements. |
| ![Lint](images/pipelinedetailslint.png) | Détails du Linting. |
| ![Deploy](images/pipelinedetailsdeploy.png) | Détails du Déploiement. |
| ![Config Test](images/pipelinegenerateconfig.jsonfortestingstages.png) | Génération du fichier config. |

---

### 🔗 Liens Utiles
*   [📖 Guide de Mise en Œuvre](docs/guide.md)
*   [🧪 Rapport de Projet & POC](docs/projet.md)

---

## ✍️ Auteurs
Ce projet a été réalisé par :
*   **ABDOULAYE SIDIBE**
*   **Jean Louis DJIONGO DONGMO**
