[English](./README.md) | [简体中文](./README.zh-CN.md) | [Français](./README.fr.md)

---

# T4T - Exécuteur de Tâches Automatisées Extensible

T4T (Task for Things) est un outil puissant d'exécution de tâches automatisées construit avec Python et PyQt. Il fournit une interface utilisateur graphique pour créer, gérer et surveiller diverses tâches automatisées. La philosophie de conception fondamentale de T4T est la modularité et l'extensibilité, permettant aux utilisateurs d'étendre infiniment ses fonctionnalités en développant des modules personnalisés.

## Fonctionnalités Clés

*   **Interface Utilisateur Graphique**: Fournit une interface graphique intuitive et facile à utiliser pour que les utilisateurs puissent gérer et surveiller les tâches.
*   **Planification de Tâches**: Planificateur de tâches puissant intégré qui prend en charge les tâches chronométrées, récurrentes et basées sur des événements.
*   **Conception Modulaire**: Les utilisateurs peuvent développer et intégrer de nouveaux modules fonctionnels selon leurs propres besoins.
*   **Bus de Messages**: Bus de messages basé sur MQTT pour le découplage et la communication asynchrone entre les modules et les tâches.
*   **Gestion de l'État**: Surveillance et gestion en temps réel de l'état des tâches et de l'ensemble du système.
*   **Support Multilingue**: Prend en charge les interfaces chinoise, anglaise et française.
*   **Personnalisation du Thème**: Prend en charge les thèmes clair et sombre, et permet aux utilisateurs de personnaliser les thèmes.
*   **Système de Journalisation**: Fonctions de journalisation et de visualisation intégrées pour un débogage et un suivi faciles.

## Démarrage Rapide

### Prérequis

*   Python 3.10+
*   PyQt5

### Installation

1.  Clonez ce dépôt sur votre machine locale:
    ```bash
    git clone https://github.com/johnnyzhao5619/T4T.git
    cd T4T
    ```

2.  Créez et activez un environnement virtuel Python:
    ```bash
    python -m venv venv
    source venv/bin/activate  # sur Windows, utilisez `venv\Scripts\activate`
    ```

3.  Installez les dépendances:
    ```bash
    pip install -r requirements.txt
    ```

### Exécution

```bash
python main.py
```

## Guide d'utilisation

1.  **Créer une tâche**:
    *   Cliquez sur le bouton "Nouvelle tâche" dans l'interface principale.
    *   Dans la boîte de dialogue qui apparaît, sélectionnez un module de tâche.
    *   Configurez les paramètres de la tâche selon les besoins du module.
    *   Cliquez sur "OK" pour créer la tâche.

2.  **Gérer les tâches**:
    *   Dans la liste des tâches de l'interface principale, vous pouvez voir l'état de toutes les tâches.
    *   Sélectionnez une tâche pour afficher ses informations détaillées, ses journaux et sa sortie dans la zone de détails à droite.
    *   Vous pouvez démarrer, arrêter, modifier et supprimer des tâches.

3.  **Paramètres système**:
    *   Dans le menu "Paramètres", vous pouvez configurer les paramètres du système, tels que la langue, le thème, etc.

## Structure du Projet

```
T4T/
├───core/         # Logique métier principale
├───docs/         # Documentation du projet
├───i18n/         # Fichiers de langue d'internationalisation
├───logs/         # Fichiers journaux
├───modules/      # Modules fonctionnels enfichables
├───services/     # Services d'arrière-plan (par exemple, Broker MQTT)
├───tests/        # Cas de test
├───themes/       # Fichiers de thème
├───utils/        # Classes utilitaires
├───view/         # Composants d'interface PyQt
├───main.py       # Point d'entrée principal du programme
└───requirements.txt # Dépendances Python
```

## Développement de modules

L'un des principaux avantages de T4T est sa conception modulaire. Vous pouvez facilement créer vos propres modules pour étendre ses fonctionnalités.

1.  **Créer un répertoire de module**:
    *   Dans le répertoire `modules/`, créez un nouveau dossier pour votre module (par exemple, `my_module`).

2.  **Écrire le code du module**:
    *   Dans le répertoire du module, créez un fichier Python (par exemple, `my_module.py`).
    *   Dans ce fichier, implémentez une classe qui hérite de `core.module_manager.BaseModule`.
    *   Implémentez la méthode `run`, qui est la logique principale du module.

3.  **Créer manifest.yaml**:
    *   Dans le répertoire du module, créez un fichier `manifest.yaml` pour décrire les métadonnées du module, telles que le nom, la description, la version et la classe d'entrée.

Pour plus de détails, veuillez consulter `docs/development_guide.md`.

## Contribuer

Nous accueillons toutes les formes de contributions ! Qu'il s'agisse de signaler un bogue, de soumettre une demande de fonctionnalité ou de contribuer directement au code.

Veuillez vous assurer que votre code respecte le style de codage existant du projet et passe tous les tests avant de soumettre une Pull Request.

## Licence

Ce projet est sous licence [MIT](LICENSE).