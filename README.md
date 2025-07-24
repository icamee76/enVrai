# enVrai en bref
Un petit programmes en Python pour détecter **les tics de langage** (en vrai, du coup, en gros...). Mais aussi pour s'amuser à **déclencher des sons ou des phrases audio** quand un mot où une expression sont détectés.
<kbd><img width="600" alt="Capture d'écran de l'interface qui présente les statistiques de détection des expressions" src="https://github.com/user-attachments/assets/c29601c3-b03b-436a-833a-b2aea0d186ee" /></kbd>

# enVrai ça marche comment ?
Le script écoute en continu et transcrit en texte (avec **Whisper**, la bibliothèque open source d'Open AI).

Le script détecte ensuite des chaines de caractères spécifiques dans le transcript (on pourrait y ajouter des regexp mais c'est déjà très efficace comme ça) et déclenche des mp3 de réponse. 
- Par exemple : "en vrai" déclenche un magnifique "ta gueule" (généré une fois pour toute sur le site d'Elevenlabs)

On peut aussi, pour certaines chaines, demander que le script fasse réécouter ce qui a été dit de façon à bien entendre à quel moment et qui à dit ça.
- Par exemple : "du coup" déclenche "ta gueule" et ensuite fait écouter ce qui vient d'être dit.

Une interface d'admin web permet de modifier les expressions, d'avoir des statistiques des expressions détectées, de choisir le modèle Whisper et de lister les mp3.

# Installation
En ligne de commande (CLI) : 
- créer un dossier : `mkdir enVrai`
- aller dedans :  `cd enVrai`
- copier les fichiers et dossiers du projet dans le dossier
- créer un venv : `python -m venv venv` [optionnel mais conseillé]
- activer l'environnement virtuel : `venv\Scripts\activate.bat` (cmd sous Windows), `venv\Scripts\Activate.ps1` (powershell sous Windows) ou `source venv/bin/activate` (terminal sous MacOS) [optionnel mais conseillé]
- installer les dépendances du projet : `pip install -r requirements.txt`

# Lancement de enVrai
Avec l'environnement virtuel activé et dans le dossier enVrai : 
- taper `python main.py` pour lancer enVrai (la config se trouve dans config.json)

ou
- taper `python main.py --web` pour lancer enVrai et son interface web d'administration

<kbd><img width="400" alt="Capture d'écran du démmarrage d'enVrai dans un terminal" src="https://github.com/user-attachments/assets/2156e24e-d018-4bc8-aebe-5ee8d8c897c4" /></kbd>

# Administration
Pour accéder à l'admin http://localhost:5010

L'**interface d'administration web**, permet : 
- Pour **les expressions**
  - d'ajouter, supprimer, ou modifier les expressions détectées
  - de déterminer toutes les variations d'une expression qui peuvent être détectées. Par ex : toto, to to, tautau, teauteau...
  - de choisir quel MP3 va être joué
  - de décider s'il faut réécouter ce qui vient dêtre dit
  - de désactiver ou activer la détection de cette expression.
- Pour **les statistiques**
  - de compter chaque les tics de langage détectés lors de cette session (depuis le mancement du script)
  - de revoir les dernières détections horodatées et d'entendre le mp2 joué
  - de réécouter les moments où les expressions ont été détectées et de les télécharger
- Pour **la configuration**
  - de savoir quel modèle whisper est utilisé
  - de changer le modèle whisper utilisé (le teléchargement se fera à chaud), de tiny à large (5 modèles)
- Pour **les mp3**
  - de lister les mp3 disponible dans le dossier "mp3"
  - de les écouter

Todo :
- quand on demande à enVrai de rejouer ce qui a déclenché la détection d'expression (par ex : "En gros, c'est top ce que tu as fait"), le micro reste ouvert et enVrai risque donc de détecter à nouveau l'expression ce qui mène à une boucle détection.
- il manque un VAD pour éviter que la transcription soit envoyée à Whisper alors que personne ne parle (pour l'instant on écoute en coutinu et on envoie a Whisper un morceau toutes les x secondes). Cela empècherait enVrai de consommer inutilement des ressources.
- 
