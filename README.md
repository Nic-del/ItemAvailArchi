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

Le projet est configuré pour compiler deux exécutables principaux au sein d'un même dossier partagé grâce à PyInstaller (`AP_Mini_Tracker.spec`) :

### 1. `AP_Mini_Tracker.exe` (Interface Graphique - GUI)
Cet exécutable propose une interface visuelle simple construite avec **Tkinter**.
* La console système reste invisible en arrière-plan.
* **Changement de Slot Dynamique** : Une fois connecté, l'interface affiche tous les joueurs/slots présents sur le serveur Archipelago. Vous pouvez cliquer sur le nom d'un autre joueur pour basculer instantanément sur son tracker.

### 2. `AP_Mini_Tracker_CLI.exe` (Ligne de commande pure - CLI)
Cet exécutable se lance directement dans votre terminal Windows (cmd, PowerShell) et affiche le tracker en mode texte pur.
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
AP_Mini_Tracker_CLI.exe --server localhost:38281 --slot MonPseudo
```

---

## 📦 Compilation des Exécutables

Si vous souhaitez recompiler les fichiers exécutables vous-même à partir du code source Python, vous aurez besoin de `PyInstaller`. Exécutez la commande suivante à la racine du projet :

```bash
pyinstaller AP_Mini_Tracker.spec
```

Le résultat sera généré dans le répertoire `dist/AP_Mini_Tracker/`, contenant :
* **`AP_Mini_Tracker.exe`** (GUI)
* **`AP_Mini_Tracker_CLI.exe`** (CLI)
