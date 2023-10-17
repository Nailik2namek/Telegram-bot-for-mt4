# Telegram-bot-for-mt4

# Documentation d'Installation et d'Exécution

Ce document explique comment installer et exécuter le bot Telegram pour le trading sur MetaTrader 4 à l'aide du code hébergé sur GitHub, en utilisant Render et MetaApi. Assurez-vous de suivre attentivement les étapes pour configurer le bot correctement.

## Prérequis

Avant de commencer, assurez-vous que vous avez les éléments suivants en place :

1. Un compte Telegram.

2. Un compte MetaTrader 4 fonctionnel.

3. Un compte MetaApi. Vous pouvez vous inscrire et obtenir les informations d'identification nécessaires [ici](https://app.metaapi.io/register).

4. Python 3.x installé sur votre système.

## Configuration

1. **GitHub Repository :** Clonez le dépôt GitHub du bot à partir de [https://github.com/VOTRE_UTILISATEUR/NOM_DU_REPO](https://github.com/VOTRE_UTILISATEUR/NOM_DU_REPO).

2. **API Key MetaApi :** Ajoutez votre clé API MetaApi à la variable d'environnement `API_KEY` sur Render.

3. **ID de Compte MetaTrader 4 :** Ajoutez votre ID de compte MetaTrader 4 à la variable d'environnement `ACCOUNT_ID` sur Render.

4. **Jeton Telegram :** Créez un nouveau bot Telegram en discutant avec le BotFather et ajoutez le jeton à la variable d'environnement `TOKEN` sur Render.

5. **Compte Telegram Autorisé :** Ajoutez votre nom d'utilisateur Telegram (sans "@") à la variable d'environnement `TELEGRAM_USER` sur Render pour autoriser uniquement votre compte à utiliser le bot.

6. **Heroku (optionnel) :** Si vous prévoyez d'utiliser Heroku, configurez les variables d'environnement dans votre application.

## Exécution avec Render

1. Créez un compte sur [Render](https://render.com/) si vous n'en avez pas déjà un.

2. Créez un nouveau service Render.

3. Configurez le service Render pour cloner automatiquement le dépôt GitHub.

4. Ajoutez des variables d'environnement pour `API_KEY`, `ACCOUNT_ID`, `TOKEN`, et `TELEGRAM_USER` dans les paramètres du service Render.

5. Déployez le service Render.

6. Le bot doit démarrer automatiquement.

## Commandes du Bot

- `/start` : Affiche un message de bienvenue.
- `/help` : Affiche une liste de commandes et des exemples de trades.
- `/trade` : Permet de saisir un trade pour exécution.
- `/calculate` : Calcule les informations pour un trade sans l'exécuter.
- `/connect` : Connecte le bot à votre compte MetaTrader 4.
- `/setlanguage` : Définit la langue préférée.
- `/setcurrency` : Définit la devise préférée.
- `/cancel` : Annule une opération en cours.
