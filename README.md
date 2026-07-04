# Archipelago Mini & CLI Tracker (AP Tracker)

[Version Française](#version-française) | [English Version](#english-version)

---

## English Version

A lightweight, fast, and local progress tracker for **Archipelago** multiworld games. It analyzes obtained items in real-time and computes the accessibility of remaining locations based on game logic.

---

### 🚀 Key Features
* **Local Logic Calculation**: Instantly determines which locations are accessible (*in logic*) in your game.
* **Optimized Loading**: Dynamic import of dependencies and fast cache management for a near-instant startup.
* **Dual Interface**: 
  * A modern graphical interface (GUI) for visual comfort.
  * An ultra-lightweight command-line interface (CLI) with no heavy dependencies, ideal for running in the background or without a display.

---

### 🛠️ How the 2 Executables Work

The project is configured to compile two main executables within the same shared folder using PyInstaller (`AP_Mini_Tracker.spec`):

#### 1. `AP_Mini_Tracker.exe` (Graphical Interface - GUI)
This executable offers a simple visual interface built with **Tkinter**.
* The system console remains invisible in the background.
* **Dynamic Slot Swapping**: Once connected, the interface displays all players/slots present on the Archipelago server. You can click on another player's name to instantly switch to their tracker.

#### 2. `AP_Mini_Tracker_CLI.exe` (Pure Command Line - CLI)
This executable runs directly in your Windows terminal (cmd, PowerShell) and displays the tracker in pure text mode.
* It displays the number of checked and accessible locations in real-time.

---

### 🖥️ Usage and Command Line Arguments

Both executables accept command line arguments to automate connection.

#### Available Arguments:
| Argument | Shortcut | Description |
| :--- | :--- | :--- |
| `--server <address>` | `-h` / `--host` | Archipelago server address (e.g. `archipelago.gg:38281` or `38281`). |
| `--slot <name>` | `-s` | Your slot (player) name in the game. |
| `--password <pwd>` | `-p` | Server password (if configured). |
| `--players-dir <path>` | - | Path to the folder containing players' YAML files (default: `./players`). |
| `--silent` | - | Disables verbose information logs in the console. |

#### Usage Examples:

**Launch the GUI with auto-connect:**
```bash
AP_Mini_Tracker.exe --server archipelago.gg:38281 --slot MyNickname --password mypassword
```

**Launch the CLI Tracker directly in the terminal:**
```bash
AP_Mini_Tracker_CLI.exe --server localhost:38281 --slot MyNickname
```

---

### 📦 Compiling the Executables

If you wish to recompile the executable files yourself from the Python source code, you will need `PyInstaller`. Run the following command at the root of the project:

```bash
pyinstaller AP_Mini_Tracker.spec
```

The output will be generated in the `dist/AP_Mini_Tracker/` directory, containing:
* **`AP_Mini_Tracker.exe`** (GUI)
* **`AP_Mini_Tracker_CLI.exe`** (CLI)

---

## Version Française

Un tracker de progression léger, rapide et local pour les jeux multiworld **Archipelago**. Il analyse en temps réel les objets obtenus et calcule l'accessibilité des emplacements restants en fonction de la logique du jeu.

---

### 🚀 Fonctionnalités principales
* **Calcul de logique local** : Détermine instantanément quels emplacements sont accessibles (*in logic*) dans votre partie.
* **Chargement optimisé** : Importation dynamique des dépendances et gestion rapide du cache pour un démarrage quasi instantané.
* **Double Interface** : 
  * Une interface graphique moderne (GUI) pour un confort visuel.
  * Une interface en ligne de commande (CLI) ultra-légère, sans dépendance lourde, idéale pour une utilisation en arrière-plan ou sans affichage.

---

### 🛠️ Fonctionnement des 2 exécutables

Le projet est configuré pour compiler deux exécutables principaux au sein d'un même dossier partagé grâce à PyInstaller (`AP_Mini_Tracker.spec`) :

#### 1. `AP_Mini_Tracker.exe` (Interface Graphique - GUI)
Cet exécutable propose une interface visuelle simple construite avec **Tkinter**.
* La console système reste invisible en arrière-plan.
* **Changement de Slot Dynamique** : Une fois connecté, l'interface affiche tous les joueurs/slots présents sur le serveur Archipelago. Vous pouvez cliquer sur le nom d'un autre joueur pour basculer instantanément sur son tracker.

#### 2. `AP_Mini_Tracker_CLI.exe` (Ligne de commande pure - CLI)
Cet exécutable se lance directement dans votre terminal Windows (cmd, PowerShell) et affiche le tracker en mode texte pur.
* Il affiche en temps réel le nombre d'emplacements vérifiés et accessibles.

---

### 🖥️ Utilisation et Arguments en ligne de commande

Les deux exécutables acceptent des arguments en ligne de commande pour automatiser la connexion.

#### Arguments disponibles :
| Argument | Raccourci | Description |
| :--- | :--- | :--- |
| `--server <adresse>` | `-h` / `--host` | Adresse du serveur Archipelago (ex: `archipelago.gg:38281` ou `38281`). |
| `--slot <nom>` | `-s` | Nom de votre slot (joueur) dans la partie. |
| `--password <mdp>` | `-p` | Mot de passe du serveur (si configuré). |
| `--players-dir <chemin>` | - | Chemin vers le dossier contenant les fichiers YAML des joueurs (par défaut : `./players`). |
| `--silent` | - | Désactive les logs d'information verbeux dans la console. |

#### Exemples d'utilisation :

**Lancer la GUI avec connexion automatique :**
```bash
AP_Mini_Tracker.exe --server archipelago.gg:38281 --slot MonPseudo --password monmotdepasse
```

**Lancer le Tracker CLI directement dans le terminal :**
```bash
AP_Mini_Tracker_CLI.exe --server localhost:38281 --slot MonPseudo
```

---

### 📦 Compilation des Exécutables

Si vous souhaitez recompiler les fichiers exécutables vous-même à partir du code source Python, vous aurez besoin de `PyInstaller`. Exécutez la commande suivante à la racine du projet :

```bash
pyinstaller AP_Mini_Tracker.spec
```

Le résultat sera généré dans le répertoire `dist/AP_Mini_Tracker/`, contenant :
* **`AP_Mini_Tracker.exe`** (GUI)
* **`AP_Mini_Tracker_CLI.exe`** (CLI)
