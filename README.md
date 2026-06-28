# Archipelago Mini & CLI Tracker (AP Tracker)

Un tracker de progression léger, rapide et local pour les jeux multiworld **Archipelago**. Il analyse en temps réel les objets obtenus et calcule l'accessibilité des emplacements restants en fonction de la logique du jeu.

---

## 🚀 Fonctionnalités principales
* **Calcul de logique local** : Détermine instantanément quels emplacements sont accessibles (*in logic*) dans votre partie.
* **Chargement optimisé** : Importation dynamique des dépendances et gestion rapide du cache pour un démarrage quasi instantané.
* **Double Interface** : 
  * Une interface graphique moderne (GUI) pour un confort visuel.
  * Une interface en ligne de commande (CLI) ultra-légère, sans dépendance lourde, idéale pour une utilisation en arrière-plan ou sans affichage.

---

## 🛠️ Fonctionnement des 2 exécutables

Le projet est configuré pour compiler deux exécutables principaux grâce à PyInstaller :

### 1. `AP_Mini_Tracker` (Interface Graphique - GUI)
Cet exécutable propose une interface visuelle simple construite avec **Tkinter** et s'appuyant sur un arrière-plan en ligne de commande pour le traitement logique.

Il est compilé sous forme d'un dossier partagé contenant deux variantes :
* **`AP_Mini_Tracker.exe`** : Lance l'interface graphique standard. La console système reste invisible en arrière-plan.
* **`AP_Mini_Tracker_CLI.exe`** : Lance l'interface graphique mais garde une invite de commande (console) ouverte à côté. C'est idéal pour visualiser les logs de connexion ou déboguer les temps de chargement en direct.
* **Changement de Slot Dynamique** : Une fois connecté, l'interface affiche tous les joueurs/slots présents sur le serveur Archipelago. Vous pouvez cliquer sur le nom d'un autre joueur pour basculer instantanément sur son tracker.

### 2. `AP_CLI_Tracker` (Ligne de commande pure - CLI)
Cet exécutable est compilé en un **seul fichier autonome (onefile)**. 
* Il **exclut** totalement les bibliothèques d'interface lourdes (comme Kivy, Tkinter ou Pillow), ce qui le rend extrêmement léger (démarrage ultra-rapide et faible empreinte mémoire).
* Il se lance directement dans votre terminal Windows (cmd, PowerShell).
* Il affiche en temps réel le nombre d'emplacements vérifiés et accessibles.

---

## 🖥️ Utilisation et Arguments en ligne de commande

Les deux exécutables acceptent des arguments en ligne de commande pour automatiser la connexion.

### Arguments disponibles :
| Argument | Raccourci | Description |
| :--- | :--- | :--- |
| `--server <adresse>` | `-h` / `--host` | Adresse du serveur Archipelago (ex: `archipelago.gg:38281` ou `38281`). |
| `--slot <nom>` | `-s` | Nom de votre slot (joueur) dans la partie. |
| `--password <mdp>` | `-p` | Mot de passe du serveur (si configuré). |
| `--players-dir <chemin>` | - | Chemin vers le dossier contenant les fichiers YAML des joueurs (par défaut : `./players`). |
| `--silent` | - | Désactive les logs d'information verbeux dans la console. |

### Exemples d'utilisation :

**Lancer la GUI avec connexion automatique :**
```bash
AP_Mini_Tracker.exe --server archipelago.gg:38281 --slot MonPseudo --password monmotdepasse
```

**Lancer le Tracker CLI directement dans le terminal :**
```bash
AP_CLI_Tracker.exe --server localhost:38281 --slot MonPseudo
```

---

## 📦 Compilation des Exécutables

Si vous souhaitez recompiler les fichiers exécutables vous-même à partir du code source Python, vous aurez besoin de `PyInstaller`. Exécutez l'une des commandes suivantes à la racine du projet :

* **Pour compiler le dossier GUI (`AP_Mini_Tracker`) :**
  ```bash
  pyinstaller AP_Mini_Tracker.spec
  ```
  *Le résultat sera généré dans le répertoire `dist/AP_Mini_Tracker/`.*

* **Pour compiler le fichier CLI unique (`AP_CLI_Tracker`) :**
  ```bash
  pyinstaller AP_CLI_Tracker.spec
  ```
  *Le résultat sera généré sous forme d'un exécutable unique dans `dist/AP_CLI_Tracker.exe`.*
