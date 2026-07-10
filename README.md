# Archipelago Mini & CLI Tracker (AP Tracker)

[Version Française](#version-française) | [English Version](#english-version)

---

## English Version

A lightweight, fast, and local progress tracker for **Archipelago** multiworld games. It analyzes obtained items in real-time and computes the accessibility of remaining locations based on game logic.

This project is built upon the work of the team behind the [Universal Tracker](https://github.com/FarisTheAncient/Archipelago/).

---

### 🚀 Key Features
* **Local Logic Calculation**: Instantly determines which locations are accessible (*in logic*) in your game.
* **Optimized Loading**: Dynamic import of dependencies and fast cache management for a near-instant startup.
* **Dual Interface**: 
  * A modern graphical interface (GUI) for visual comfort.
  * An ultra-lightweight command-line interface (CLI) with no heavy dependencies, ideal for running in the background or without a display.

---

### ⚠️ Essential Prerequisites

For the tracker to work correctly, you must:
1. **Install the `.apworld` files** corresponding to the games in your multiworld into your local Archipelago installation folder (typically `%localappdata%/Archipelago/custom_worlds/`).
2. **Place the game configuration `.yaml` files** in the `players` directory (or specified via the `--players-dir` argument).

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
| `--ap-dir <path>` | - | Custom path to the Archipelago installation directory. |
| `--silent` | - | Disables verbose information logs in the console. |

#### Usage Examples:


**Launch the GUI with auto-connect:**
```bash
AP_Mini_Tracker.exe --server archipelago.gg:38281 --slot MyNickname --password mypassword
```

> [!NOTE]
> For `AP_Mini_Tracker.exe` (GUI), auto-connection is only triggered if **both** `--server` and `--slot` are provided. If only one or none is provided, the fields will be pre-filled with the arguments (or default/saved settings), and you must click the **Connect** button manually.


**Launch the CLI Tracker directly in the terminal:**
```bash
AP_Mini_Tracker_CLI.exe --server localhost:38281 --slot MyNickname
```
---

### 📺 OBS / Stream Integration (Text Files)

The tracker automatically exports real-time progression statistics to text files in the application directory. You can use these files directly in OBS Studio (using "Text (GDI+)" sources) to create live overlays for your streams.

The following files are updated in real-time:
* **`remaining_locations.txt`**: The list of all currently accessible locations (in logic), with a clean header.
* **`obs_stats.txt`**: A combined summary containing the slot name, the game, the checks count, and the number of accessible locations:
  ```text
  Slot: MyNickname | Game: Super Mario World
  Checks: 15 / 120
  Accessible: 4
  ```
* **`obs_checks.txt`**: The raw check count formatted as `checked / total` (e.g., `15 / 120`).
* **`obs_accessible.txt`**: The raw number of locations accessible in logic (e.g., `4`).
* **`obs_slot.txt`**: The slot and game name formatted as `SlotName (Game)` (e.g., `MyNickname (Super Mario World)`).

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

Ce projet se base sur le travail réalisé par l'équipe d' [Universal Tracker](https://github.com/FarisTheAncient/Archipelago/).

---

### 🚀 Fonctionnalités principales
* **Calcul de logique local** : Détermine instantanément quels emplacements sont accessibles (*in logic*) dans votre partie.
* **Chargement optimisé** : Importation dynamique des dépendances et gestion rapide du cache pour un démarrage quasi instantané.
* **Double Interface** : 
  * Une interface graphique moderne (GUI) pour un confort visuel.
  * Une interface en ligne de commande (CLI) ultra-légère, sans dépendance lourde, idéale pour une utilisation en arrière-plan ou sans affichage.

---

### ⚠️ Prérequis indispensables

Pour que le tracker fonctionne correctement, vous devez :
1. **Installer les fichiers `.apworld`** correspondants aux jeux de votre multiworld dans votre dossier Archipelago local (généralement `%localappdata%/Archipelago/custom_worlds/`).
2. **Placer les fichiers `.yaml`** de configuration de la partie dans le dossier `players` (ou spécifié via l'argument `--players-dir`).

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
| `--ap-dir <chemin>` | - | Chemin personnalisé vers le répertoire d'installation d'Archipelago. |
| `--silent` | - | Désactive les logs d'information verbeux dans la console. |

#### Exemples d'utilisation :


**Lancer la GUI avec connexion automatique :**
```bash
AP_Mini_Tracker.exe --server archipelago.gg:38281 --slot MonPseudo --password monmotdepasse
```

> [!NOTE]
> Pour `AP_Mini_Tracker.exe` (GUI), la connexion automatique se lance uniquement si les **deux** arguments `--server` et `--slot` sont fournis. Si un seul argument (ou aucun) est fourni, les champs seront pré-remplis avec les arguments (ou vos derniers paramètres sauvegardés), et vous devrez cliquer sur le bouton **Connect** pour lancer la connexion.


**Lancer le Tracker CLI directement dans le terminal :**
```bash
AP_Mini_Tracker_CLI.exe --server localhost:38281 --slot MonPseudo
```
---

### 📺 Intégration OBS / Stream (Fichiers Texte)

Le tracker exporte automatiquement les statistiques de progression en temps réel dans des fichiers texte situés dans le dossier de l'application. Vous pouvez utiliser ces fichiers directement dans OBS Studio (via des sources "Texte (GDI+)") pour afficher votre progression en direct sur votre stream.

Les fichiers suivants sont mis à jour en temps réel :
* **`remaining_locations.txt`** : La liste de tous les emplacements actuellement accessibles (in logique), avec un en-tête propre.
* **`obs_stats.txt`** : Un résumé combiné contenant le nom du joueur, le jeu, le nombre de vérifications et le nombre d'emplacements accessibles :
  ```text
  Slot: MonPseudo | Game: Super Mario World
  Checks: 15 / 120
  Accessible: 4
  ```
* **`obs_checks.txt`** : Le nombre brut de vérifications sous la forme `checked / total` (ex: `15 / 120`).
* **`obs_accessible.txt`** : Le nombre brut d'emplacements accessibles en logique (ex: `4`).
* **`obs_slot.txt`** : Le nom du joueur et du jeu sous la forme `Joueur (Jeu)` (ex: `MonPseudo (Super Mario World)`).

---

### 📦 Compilation des Exécutables

Si vous souhaitez recompiler les fichiers exécutables vous-même à partir du code source Python, vous aurez besoin de `PyInstaller`. Exécutez la commande suivante à la racine du projet :

```bash
pyinstaller AP_Mini_Tracker.spec
```

Le résultat sera généré dans le répertoire `dist/AP_Mini_Tracker/`, contenant :
* **`AP_Mini_Tracker.exe`** (GUI)
* **`AP_Mini_Tracker_CLI.exe`** (CLI)
