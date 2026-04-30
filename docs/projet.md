#  Rapport de Projet : NexusPlay

##  Présentation Générale
NexusPlay est un prototype d'architecture microservices serverless conçu pour répondre aux besoins d'une startup de jeux vidéo. L'objectif était de créer une infrastructure **Hautement Disponible**, **Scalable** et **Automatisée**.

##  Architecture Réalisée
Le système est composé de :
- **3 Microservices** : Game Service, User Service, Notification Service.
- **API Gateway** : Point d'entrée unique avec gestion de stages (`dev`, `test`, `prod`) et mise en cache.
- **Serverless Compute** : AWS Lambda pour une scalabilité infinie.
- **Sécurité** : Secrets Manager pour la configuration et IAM pour les rôles.
- **Monitoring** : CloudWatch Alarms + SNS pour les notifications d'incidents.
- **CI/CD** : GitHub Actions automatisant le cycle de vie du logiciel.

##  Objectifs Atteints

### 1. Logique Microservices
Trois services distincts communiquent de manière asynchrone ou via l'API Gateway :
- **User Service** : Gère les profils et scores.
- **Game Service** : Gère la logique de création et de ralliement aux jeux.
- **Notification Service** : Gère les alertes système et les communications.

![Architecture Microservices](../images/logiquemicroservicesfonctionlambda.png)
*Visualisation de la logique serverless et des fonctions Lambda.*

### 2. Équilibrage de Charge & Haute Disponibilité
Utilisation d'**AWS API Gateway** (Regional) qui répartit automatiquement la charge sur les instances Lambda s'exécutant dans plusieurs zones de disponibilité.
Mise en place de **Route 53** pour la gestion DNS avec une stratégie Active/Backup (simulation).

![Configuration API Gateway](../images/Logiquemicroservicesapigateway.png)
*Point d'entrée unique et gestion des routes.*

![Route 53 HA DNS](../images/serveurDNShautementdisponiblerouteS3.png)
*Architecture DNS pour la haute disponibilité.*

### 3. Scalabilité Automatique
Grâce à **AWS Lambda**, l'infrastructure s'adapte instantanément au trafic, passant de 0 à des milliers d'utilisateurs sans intervention manuelle.

![Auto-scaling Lambda](../images/autoscaling1.png)
*Preuve de la capacité de mise à l'échelle automatique.*

### 4. Monitoring Centralisé
Déploiement automatique d'alarmes CloudWatch sur :
- Le taux d'erreur (Errors > 5).
- La latence d'exécution (Duration > 5s).
Notifications envoyées à un topic **SNS** centralisé.

![CloudWatch Alarms](../images/monitoringcentralisecloudwatchalarms.png)
*Système d'alerting configuré pour la résilience.*

### 5. Pipeline CI/CD & Tests de Charge
Une pipeline GitHub Actions déclenche :
1. **Linting** : Validation de la qualité du code.
2. **Déploiement** : Mise à jour automatique de l'infra sur AWS.
3. **Tests Fonctionnels** : Vérification des endpoints.
4. **Tests de Charge** : Simulation de trafic via Locust (20 users) pour valider la tenue en charge en production.

![Pipeline CI/CD](../images/pipeline.png)
*Workflow GitHub Actions automatisé.*

### 6. Optimisation & Sécurité
- **Cache** : Activation du cache sur le stage `prod` pour améliorer les performances de lecture.
- **Secrets** : Intégration complète avec **AWS Secrets Manager** pour éviter toute fuite de données sensibles.

![Secrets Manager](../images/Integrerunsysteemedegestiondessecretssecuriseviaawssecretmanager.png)
*Gestion centralisée et sécurisée des secrets.*

##  Résultats des Tests de Charge
Les tests effectués avec Locust ont montré une stabilité parfaite :
- **Nombre d'utilisateurs** : 20
- **Taux de succès** : 100%
- **Temps de réponse moyen** : ~150ms

##  Annexe : Galerie Complète des Preuves Techniques

Cette section regroupe l'intégralité des captures d'écran validant la mise en œuvre de l'architecture NexusPlay.

###  Logique Microservices & API
| Image | Description |
| :--- | :--- |
| ![Lambda](../images/logiquemicroservicesfonctionlambda.png) | Liste des fonctions Lambda déployées. |
| ![API Gateway](../images/Logiquemicroservicesapigateway.png) | Structure des ressources API Gateway. |
| ![API Details](../images/Logiquemicroservicesapigatewaydetails.png) | Détails de configuration des méthodes API. |

###  Équilibrage de Charge & Réseau
| Image | Description |
| :--- | :--- |
| ![Network Mapping](../images/equilibragedeschargesloadbalancernetworkmapping.png) | Schéma de flux réseau du load balancer. |
| ![LB Dashboard](../images/equilibragedeschargesloadbalancerdashboard.png) | Dashboard de performance du Load Balancer. |
| ![LB Monitoring](../images/equilibragedeschargesloadbalancermonitoring.png) | Métriques de trafic de l'équilibrage de charge. |

###  Haute Disponibilité DNS
| Image | Description |
| :--- | :--- |
| ![Route 53](../images/serveurDNShautementdisponiblerouteS3.png) | Configuration Route 53 vers S3/Static. |
| ![VPC 1](../images/serveurDNShautementdisponiblevpc1.png) | Configuration VPC Multi-AZ (Partie 1). |
| ![VPC 2](../images/serveurDNShautementdisponiblevpc2.png) | Configuration VPC Multi-AZ (Partie 2). |

###  Scalabilité Automatique
| Image | Description |
| :--- | :--- |
| ![Auto-scaling 1](../images/autoscaling1.png) | Politique d'Auto-scaling Lambda. |
| ![Auto-scaling 2](../images/autoscaling2.png) | Configuration de la concurrence et des limites. |
| ![Auto-scaling 3](../images/autoscaling3.png) | Historique des événements de mise à l'échelle. |

###  Monitoring & Alerting (CloudWatch)
| Image | Description |
| :--- | :--- |
| ![Alarms](../images/monitoringcentralisecloudwatchalarms.png) | Liste des alarmes CloudWatch actives. |
| ![Dashboard](../images/monitoringcentralisecloudwatchdashboard.png) | Dashboard opérationnel global. |
| ![Dashboard Details](../images/monitoringcentralisecloudwatchdashboarddetails.png) | Détails des widgets de monitoring. |
| ![Metrics](../images/monitoringcentralisecloudwatchmetrics.png) | Exploration des métriques personnalisées. |
| ![Resource Health](../images/monitoringcentralisecloudwatchResourceHealth.png) | État de santé des ressources surveillées. |

###  Système de Notification (SNS)
| Image | Description |
| :--- | :--- |
| ![Notif 1](../images/notification1.jpeg) | Configuration du topic SNS NexusPlay. |
| ![Notif 2](../images/notification2.png) | Détails des abonnements aux alertes. |

###  Sécurité & Secrets
| Image | Description |
| :--- | :--- |
| ![Secrets Manager](../images/Integrerunsysteemedegestiondessecretssecuriseviaawssecretmanager.png) | Secret `nexusplay/config` dans AWS. |
| ![GitHub Secrets](../images/Integrerunsysteemedegestiondessecretssecuriseviagithub.png) | Configuration des secrets dans GitHub Actions. |

###  Performance & Cache
| Image | Description |
| :--- | :--- |
| ![Cache](../images/cacheperformance.png) | Activation du cache sur le stage Prod. |

###  Pipeline CI/CD (GitHub Actions)
| Image | Description |
| :--- | :--- |
| ![Pipeline 1](../images/pipeline.png) | Workflow global réussi. |
| ![Pipeline 2](../images/pipeline2.png) | Historique des déploiements. |
| ![Lint](../images/pipelinedetailslint.png) | Détails de l'étape de Linting. |
| ![Deploy](../images/pipelinedetailsdeploy.png) | Détails de l'étape de Déploiement. |
| ![Config Test](../images/pipelinegenerateconfig.jsonfortestingstages.png) | Génération du fichier config.json. |
| ![Monitoring Build](../images/pipelinecreatemonitoring.png) | Création des ressources de monitoring via pipeline. |

###  Tests de Charge
| Image | Description |
| :--- | :--- |
| ![Load Test](../images/testdechargepourvaliderlesperformancesavecCICD..png) | Rapport Locust final validant la charge. |

---
