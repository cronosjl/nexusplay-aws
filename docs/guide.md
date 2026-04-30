#  Guide SRE & Ops — NexusPlay

Ce guide détaille les procédures d'exploitation, de maintenance et de monitoring pour la plateforme **NexusPlay**.

---

##  Gestion de l'Infrastructure (IaC)

Le déploiement de l'infrastructure est entièrement géré avec **Terraform**, garantissant une gestion d'état précise et une reproductibilité totale des ressources AWS (Lambda, API Gateway, SNS, etc.).

### Cycle de Vie d'une Ressource
1. **Initialisation** (`terraform init`) : Prépare le backend et télécharge les providers nécessaires.
2. **Planification** (`terraform plan`) : Visualise les changements avant application.
3. **Déploiement** (`terraform apply`) : Provisionne et configure les ressources sur AWS.
4. **Destruction** (`terraform destroy`) : Nettoie l'environnement si nécessaire.

![Network Mapping](../images/equilibragedeschargesloadbalancernetworkmapping.png)
*Cartographie réseau de l'équilibrage de charge.*

![DNS Configuration](../images/serveurDNShautementdisponiblevpc1.png)
*Configuration des zones DNS et du VPC pour la haute disponibilité.*

---

##  Monitoring & Observabilité

### Tableaux de Bord CloudWatch
Pour visualiser la santé du système, accédez à la console CloudWatch :
- **Métriques Clés** : `Invocations`, `Errors`, `Duration`, `Throttles`.
- **Logs de Service** : Accessibles sous le préfixe `/aws/lambda/nexusplay-*`.

![Metrics CloudWatch](../images/monitoringcentralisecloudwatchmetrics.png)
*Analyse des métriques détaillées par service.*

![Health Check](../images/monitoringcentralisecloudwatchResourceHealth.png)
*Vue sur l'état de santé des ressources AWS.*

### Gestion des Alertes
Les alarmes sont configurées pour être auto-réparatrices (dans la mesure du possible) et informatives.
- **Seuil d'erreur** : Si le taux d'erreur dépasse 5%, une investigation immédiate est requise sur le service concerné.
- **Latence (Latency P99)** : Une latence élevée indique généralement un problème de démarrage à froid (Cold Start) ou un goulot d'étranglement sur une ressource externe.

![SNS Notifications](../images/notification2.png)
*Système de notification configuré via SNS.*

---

##  Gestion des Secrets

Tous les secrets sont centralisés dans **AWS Secrets Manager**. 

![Secret Management Details](../images/Integrerunsysteemedegestiondessecretssecuriseviagithub.png)
*Alternative de gestion des secrets via GitHub Secrets pour la pipeline.*

### Structure du Secret `nexusplay/config`
```json
{
  "db_password": "...",
  "api_key": "...",
  "jwt_secret": "...",
  "sns_topic_arn": "..."
}
```

**Note Sécurité** : Ne jamais ajouter de secrets dans le code source ou dans les fichiers `config.json` générés. Utilisez toujours l'API AWS pour récupérer les valeurs dynamiquement.

---

##  Optimisation des Performances

### Mise en Cache API Gateway
Le stage `prod` utilise un cache de **0.5 GB** avec un **TTL de 300 secondes**.
- **Avantage** : Réduction drastique du nombre d'invocations Lambda pour les requêtes de lecture répétitives (ex: Leaderboard).
- **Invalidation** : Si nécessaire, le cache peut être vidé via la console AWS ou via une commande CLI.

![API Cache Configuration](../images/cacheperformance.png)
*Optimisation des performances via la mise en cache.*

### Réduction des Cold Starts
- Les fonctions Lambda sont configurées avec **128MB** de RAM. Pour des performances accrues, augmenter cette valeur alloue proportionnellement plus de puissance CPU.

![Auto-scaling Configuration](../images/autoscaling2.png)
*Détails de la configuration de scalabilité des fonctions Lambda.*

---

##  Procédure de Test de Charge

Pour valider un changement majeur d'architecture :
1. Déployer sur le stage `test`.
2. Lancer Locust en local ou via un runner :
   ```bash
   locust -f scripts/load_test.py --host <URL_STAGE_TEST> --users 50 --spawn-rate 5
   ```
3. Surveiller les métriques CloudWatch pour détecter d'éventuels `Throttles`.

![Locust Load Test](../images/testdechargepourvaliderlesperformancesavecCICD..png)
*Analyse des résultats de tenue en charge.*

---

##  Pipeline CI/CD (GitHub Actions)

L'automatisation est au cœur de NexusPlay. Chaque commit déclenche un workflow rigoureux.

![Pipeline Overview](../images/pipeline2.png)
*Vue d'ensemble de l'exécution de la pipeline.*

### Étapes Clés :
1. **Linting** : Vérification du style de code Python (PEP8).
   ![Lint Details](../images/pipelinedetailslint.png)
2. **Déploiement** : Mise à jour de l'infrastructure via **Terraform**.
   ![Deploy Details](../images/pipelinedetailsdeploy.png)
3. **Tests de Stage** : Validation automatique après chaque déploiement.
   ![Config Generation](../images/pipelinegenerateconfig.jsonfortestingstages.png)

---

##  Incident Response (Playbook)

| Incident | Action Immédiate |
| :--- | :--- |
| **Erreurs 5XX en masse** | Vérifier les logs CloudWatch pour les exceptions Python (SyntaxError, ModuleNotFoundError). |
| **Timeout API (504)** | Vérifier si la Lambda dépasse les 30s ou si une ressource externe (SNS, Secret) est inaccessible. |
| **Quota de Concurrence Atteint** | Demander une augmentation de quota ou optimiser le temps d'exécution des fonctions. |

---

**Tip** : 

Toujours vérifier le stage `dev` avant de pusher vers `main` pour garantir la stabilité de la pipeline CI/CD.
