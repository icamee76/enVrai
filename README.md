Un petit programmes en Python pour détecter les tics de langage (en vrai, du coup, en gros...).

Le script écoute en continu et transcrit en texte (avec Whisper, la bibiothèque open source d'Open AI).

Le script détecte ensuite des chaines de caractères spécifiques (on pourrait y ajouter des regexp mais c'est déjà très efficace comme ça) et déclenche des mp3 de réponse. 
Par exemple : "en vrai" déclenche un magnifique "ta gueule" (généré une fois pour toute sur le site d'Elevenlabs)
On peut aussi, pour certaines chaines, demander que le script fasse réécouter ce qui a été dit de façon à bien entendre à quel moment et qui à dit ça. PAr exemple : "du coup" déclenche "ta gueule" et ensuite fait écouter ce qui vient d'être dit.

Une interface d'administration, web, permet 
- Pour les expressions
  - d'ajouter, supprimer, ou modifier les expressions détectées
  - de déterminer toutes les variations d'une expression qui peuvent être détectées. Par ex : toto, to to, tautau, teauteau...
  - de choisir quel MP3 va être joué
  - de décider s'il faut réécouter ce qui vient dêtre dit
  - de désactiver ou activer la détection de cette expression.
- Pour les statistiques
  - de compter chaque les tics de langage détectés lors de cette session (depuis le mancement du script)
  - de revoir les dernières détections horodatées et d'entendre le mp2 joué
  - de réécouter les moments où les expressions ont été détectées et de les télécharger
- Pour la configuration
  - de savoir quel modèle whisper est utilisé
  - de changer le modèle whisper utilisé (le teléchargement se fera à chaud), de tiny à large (5 modèles)
- Pour les mp3
  - de lister les mp3 disponible dans le dossier "mp3"
  - de les écouter 
