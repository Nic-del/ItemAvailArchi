import sys
import os
import logging
import json
import asyncio
import tempfile
import re
import types

# Mock ModuleUpdate to bypass Python version checks
mock_module_update = types.ModuleType("ModuleUpdate")
mock_module_update.update = lambda *args, **kwargs: None
sys.modules["ModuleUpdate"] = mock_module_update

# Save the original console streams before Kivy can override them
original_stdout = sys.stdout
original_stderr = sys.stderr

class DummyStream:
    def write(self, data): pass
    def flush(self): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()



# Disable Kivy window and logs globally for CLI/Subprocess
os.environ["KIVY_WINDOW"] = "dummy"
os.environ["KIVY_NO_WINDOW"] = "1"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_GRAPHICS_WINDOW_STATE"] = "hidden"
os.environ["KIVY_GRAPHICS_HIDDEN"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"

# Add paths
tracker_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(tracker_dir))
sys.path.insert(0, tracker_dir)

def get_workspace_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "--silent" in sys.argv:
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.path.join(get_workspace_path(), "tracker_error.log"), 'w', buffering=1, encoding="utf-8")
    sys.stderr.write("=== Tracker CLI Started in Silent Mode ===\n")

# Try local portable directories first, fall back to default global location
base_dir = os.path.dirname(tracker_dir)
portable_ap_dir = os.path.join(base_dir, "Archipelago")
if os.path.exists(portable_ap_dir):
    ap_dir = portable_ap_dir
elif os.path.exists(os.path.join(tracker_dir, "Archipelago")):
    ap_dir = os.path.join(tracker_dir, "Archipelago")
else:
    ap_dir = r"C:\ProgramData\Archipelago"

ap_source_dir = r"C:\Users\Linksweld\Downloads\Archipelago-main\Archipelago-main"

# Only append external libraries and source paths to sys.path when running in source mode.
# When frozen, PyInstaller already contains all the dependencies compiled for the correct Python version.
if not getattr(sys, 'frozen', False):
    if os.path.exists(ap_dir):
        # Only load lib / library.zip if they are compiled for a compatible Python version to avoid ZipImportError bad magic number
        lib_compatible = True
        lib_zip_path = os.path.join(ap_dir, "lib", "library.zip")
        if os.path.exists(lib_zip_path):
            try:
                import zipfile
                import importlib.util
                with zipfile.ZipFile(lib_zip_path, 'r') as z:
                    for name in z.namelist():
                        if name.endswith('.pyc'):
                            with z.open(name) as f:
                                magic = f.read(4)
                                if magic != importlib.util.MAGIC_NUMBER:
                                    lib_compatible = False
                                break
            except Exception:
                lib_compatible = False
        else:
            lib_compatible = False

        if lib_compatible:
            sys.path.append(os.path.join(ap_dir, "lib"))
            sys.path.append(lib_zip_path)
        sys.path.append(ap_dir)

    if os.path.exists(ap_source_dir):
        sys.path.insert(0, ap_source_dir)

# Force version_tuple to be Version(0, 6, 7) to allow maximum core version compatible apworlds (like ladx) to load
import Utils
Utils.version_tuple = Utils.Version(0, 6, 7)
Utils.__version__ = "0.6.7"

# Force user_path to point to resolved ap_dir for loading custom_worlds, etc.
def patched_user_path(*args):
    if not args:
        return ap_dir
    if args[0] in ("custom_worlds", "worlds"):
        return os.path.join(ap_dir, "custom_worlds", *args[1:])
    return os.path.join(ap_dir, *args)
Utils.user_path = patched_user_path



# Save original showwarning before Kivy overrides it
import warnings
original_showwarning = warnings.showwarning

# Configure Kivy to run hidden and disable its logging redirection to prevent infinite recursion
os.environ["KIVY_WINDOW"] = "dummy"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_GRAPHICS_WINDOW_STATE"] = "hidden"
os.environ["KIVY_GRAPHICS_HIDDEN"] = "1"
os.environ["KIVY_NO_WINDOW"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
try:
    import kvui
except BaseException:
    # kvui/kivy may fail to load or call sys.exit(1) on initialization when running without display providers.
    # To prevent later imports of kvui from raising assertion/import errors, we mock it dynamically.
    import types
    class DummyClass:
        def __init__(self, *args, **kwargs):
            pass
    class DynamicMockModule(types.ModuleType):
        def __getattr__(self, name):
            return DummyClass
    mock_kvui = DynamicMockModule("kvui")
    sys.modules["kvui"] = mock_kvui

# Restore root logger to console stream, overriding Kivy log redirection
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
console_handler = logging.StreamHandler(sys.stdout if sys.stdout is not None else DummyStream())
console_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
root_logger.addHandler(console_handler)

# Completely restore warnings and standard streams to defaults to bypass Kivy overrides
warnings.showwarning = original_showwarning
if "--silent" not in sys.argv:
    sys.stdout = original_stdout if original_stdout is not None else sys.stdout
    sys.stderr = original_stderr if original_stderr is not None else sys.stderr



# Fast scanning & selective loading structures
import re
import zipfile
import json
import importlib
import importlib.util

game_to_world_file = {}
active_game_name = None
allowed_entries = {"generic"}

def scan_available_worlds():
    global game_to_world_file
    if game_to_world_file:
        return game_to_world_file

    paths_to_scan = []
    
    local_worlds_dir = None
    if os.path.exists(ap_source_dir):
        local_worlds_dir = os.path.join(ap_source_dir, "worlds")
    elif os.path.exists(os.path.join(ap_dir, "worlds")):
        local_worlds_dir = os.path.join(ap_dir, "worlds")
        
    if local_worlds_dir and os.path.exists(local_worlds_dir):
        paths_to_scan.append((local_worlds_dir, True))
        
    custom_worlds_dir = os.path.join(ap_dir, "custom_worlds")
    if os.path.exists(custom_worlds_dir):
        paths_to_scan.append((custom_worlds_dir, False))

    for folder, is_relative in paths_to_scan:
        try:
            for entry in orig_scandir(folder):
                if entry.name.startswith(("_", ".")):
                    continue
                if entry.is_dir():
                    init_path = os.path.join(entry.path, "__init__.py")
                    if os.path.exists(init_path):
                        try:
                            with open(init_path, "r", encoding="utf-8-sig") as f:
                                chunk = f.read()
                            match = re.search(r'\bgame\s*(?::\s*\w+)?\s*=\s*[\'"]([^\'"]+)[\'"]', chunk)
                            if match:
                                game_to_world_file[match.group(1).lower()] = (entry.name, False)
                        except Exception:
                            pass
                elif entry.is_file() and entry.name.endswith(".apworld"):
                    try:
                        with zipfile.ZipFile(entry.path, "r") as z:
                            for name in z.namelist():
                                if name.endswith("archipelago.json"):
                                    with z.open(name) as f:
                                        manifest = json.loads(f.read().decode("utf-8"))
                                        game = manifest.get("game")
                                        if game:
                                            game_to_world_file[game.lower()] = (entry.name, True)
                                    break
                    except Exception:
                        pass
        except Exception:
            pass

    game_to_world_file["generic"] = ("generic", False)
    return game_to_world_file

def ensure_world_loaded(game_name):
    if not game_name:
        return True
    
    # We must first ensure worlds is imported
    from worlds.AutoWorld import AutoWorldRegister
    if game_name in AutoWorldRegister.world_types:
        return True

    mapping = scan_available_worlds()
    game_lower = game_name.lower()
    if game_lower not in mapping:
        return False

    entry_name, is_zip = mapping[game_lower]
    allowed_entries.add(entry_name)
    allowed_entries.add(entry_name.lower())

    if not is_zip:
        try:
            importlib.import_module(f"worlds.{entry_name}")
            return True
        except Exception as e:
            sys.stderr.write(f"Failed to dynamically import worlds.{entry_name}: {e}\n")
            return False
    else:
        try:
            custom_worlds_dir = os.path.join(ap_dir, "custom_worlds")
            apworld_path = os.path.join(custom_worlds_dir, entry_name)
            if not os.path.exists(apworld_path):
                local_worlds_dir = None
                if os.path.exists(ap_source_dir):
                    local_worlds_dir = os.path.join(ap_source_dir, "worlds")
                elif os.path.exists(os.path.join(ap_dir, "worlds")):
                    local_worlds_dir = os.path.join(ap_dir, "worlds")
                if local_worlds_dir:
                    apworld_path = os.path.join(local_worlds_dir, entry_name)
            
            import zipimport
            from pathlib import Path
            importer = zipimport.zipimporter(apworld_path)
            world_name = Path(entry_name).stem
            
            spec = importer.find_spec(f"worlds.{world_name}")
            if spec:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"worlds.{world_name}"] = module
                spec.loader.exec_module(module)
                return True
        except Exception as e:
            sys.stderr.write(f"Failed to dynamically load apworld {entry_name}: {e}\n")
            return False
    return False

# Patch os.scandir to selectively filter and hide tracker.apworld
orig_scandir = os.scandir
class PatchedScandirIterator:
    def __init__(self, orig_iterator, path):
        self.orig_iterator = orig_iterator
        self.is_worlds_dir = False
        path_norm = os.path.normpath(path).lower()
        if "worlds" in path_norm or "custom_worlds" in path_norm:
            self.is_worlds_dir = True

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            entry = next(self.orig_iterator)
            if entry.name == "tracker.apworld":
                continue
            if self.is_worlds_dir and active_game_name is not None:
                # Filter out other game worlds to speed up loading
                name_lower = entry.name.lower()
                if entry.name not in allowed_entries and name_lower not in allowed_entries:
                    is_world = False
                    if entry.is_dir() and os.path.exists(os.path.join(entry.path, "__init__.py")):
                        is_world = True
                    elif entry.is_file() and entry.name.endswith(".apworld"):
                        is_world = True
                    if is_world:
                        continue
            return entry

    def __enter__(self):
        if hasattr(self.orig_iterator, "__enter__"):
            self.orig_iterator.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self.orig_iterator, "__exit__"):
            return self.orig_iterator.__exit__(exc_type, exc_val, exc_tb)

def patched_scandir(path="."):
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
    return PatchedScandirIterator(orig_scandir(path), path)
os.scandir = patched_scandir

class SettingsDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

logger = logging.getLogger("TrackerCLI")

GUI_MODE = "--gui" in sys.argv
SILENT_MODE = "--silent" in sys.argv

if SILENT_MODE:
    logging.getLogger().setLevel(logging.WARNING)

class IdleContext:
    def __init__(self):
        self.exit_event = asyncio.Event()
        self.server_task = None
        self.game = None
        self.temp_dir_obj = None
        self.reconnecting = False
        self.items_received = []
        self.locations_checked = set()
        self.checked_locations = set()
        self.missing_locations = set()
        self.local_items = []
        self.auth = "OOT"
        self.selected_slot_name = "OOT"
        
    async def shutdown(self):
        pass

    async def disconnect(self, allow_autoreconnect: bool = False):
        pass

# Dynamic initialization of heavy context modules
_context_classes_initialized = False
CLITrackerContext = None
server_loop = None
AutoWorldRegister = None
TrackerWorld = None

def initialize_dynamic_imports(game_name=None):
    global _context_classes_initialized, CLITrackerContext, server_loop, AutoWorldRegister, TrackerWorld, active_game_name
    if _context_classes_initialized:
        if game_name:
            ensure_world_loaded(game_name)
        return
        
    if game_name:
        active_game_name = game_name
        mapping = scan_available_worlds()
        game_lower = game_name.lower()
        if game_lower in mapping:
            allowed_entries.add(mapping[game_lower][0])
            allowed_entries.add(mapping[game_lower][0].lower())
            
    from tracker.TrackerClient import TrackerGameContext as TGC, server_loop as sl
    from worlds.AutoWorld import AutoWorldRegister as AWR
    from tracker import TrackerWorld as TW
    
    server_loop = sl
    AutoWorldRegister = AWR
    TrackerWorld = TW
    
    # Initialize settings
    TrackerWorld._AutoWorldRegister__settings = SettingsDict({
        "sorting_method": "apworld",
        "include_location_name": True,
        "include_region_name": False,
        "hide_excluded_locations": False,
        "use_split_map_icons": True,
        "enforce_deferred_entrances": "default",
        "display_glitched_logic": True,
        "save_entered_commands": True,
        "sorting_priorities": {},
        "player_files_path": os.path.join(ap_dir, "Players")
    })
    
    class DynamicCLITrackerContext(TGC):
        def __init__(self, server_address, password, slot_name):
            super().__init__(server_address, password, no_connection=False, print_list=False, print_count=False)
            self.auth = slot_name
            self.selected_slot_name = slot_name
            self.temp_dir_obj = None
            self.reconnecting = False

        async def disconnect(self, allow_autoreconnect: bool = False):
            if GUI_MODE:
                if not getattr(self, "reconnecting", False):
                    print(json.dumps({"event": "disconnected"}), flush=True)
            elif not SILENT_MODE:
                print("\n[Info] Disconnecting from server...", flush=True)
            await super().disconnect(allow_autoreconnect)

        async def connection_closed(self):
            if GUI_MODE:
                if not getattr(self, "reconnecting", False):
                    print(json.dumps({"event": "disconnected"}), flush=True)
            elif not SILENT_MODE:
                print("\n[Info] Connection closed.", file=sys.stderr, flush=True)
            await super().connection_closed()

        def on_print(self, args: dict):
            if not GUI_MODE and not SILENT_MODE:
                print(f"[Server] {args['text']}", flush=True)

        def on_print_json(self, args: dict):
            if not GUI_MODE and not SILENT_MODE:
                print(f"[Server] {self.jsontotextparser(args['data'])}", flush=True)

        def handle_connection_loss(self, msg: str) -> None:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": msg}), flush=True)
            else:
                if not SILENT_MODE:
                    import traceback
                    print(f"\n[Connection Loss] {msg}", file=sys.stderr, flush=True)
                    traceback.print_exc()
            self.exit_event.set()

        async def server_auth(self, password_requested: bool = False):
            await self.send_connect(game=self.game)

        def updateTracker(self):
            state = super().updateTracker()
            self.print_accessible_checks(state)
            return state

        def on_package(self, cmd: str, args: dict):
            try:
                super().on_package(cmd, args)
                if cmd == "Connected":
                    if GUI_MODE:
                        print(json.dumps({
                            "event": "connected",
                            "slot": self.selected_slot_name,
                            "game": self.game,
                            "players": {pinfo.name: pinfo.game for pid, pinfo in args["slot_info"].items() if int(pid) != 0}
                        }), flush=True)
                    elif not SILENT_MODE:
                        print("\n[Success] Connected to Archipelago server!", flush=True)
            except Exception as e:
                if GUI_MODE:
                    print(json.dumps({"event": "error", "message": f"Package error: {e}"}), flush=True)
                elif not SILENT_MODE:
                    import traceback
                    print(f"\n[Error processing package {cmd}] {traceback.format_exc()}", file=sys.stderr, flush=True)

        def print_accessible_checks(self, state=None):
            if state is None:
                state = super().updateTracker()
            try:
                if self.server_locations:
                    self.missing_locations = self.server_locations - self.checked_locations
                    checked = len(self.server_locations.intersection(self.checked_locations))
                    total = len(self.server_locations)
                else:
                    checked = len(self.checked_locations)
                    total = self.total_locations if hasattr(self, "total_locations") else 0

                accessible = len(state.in_logic_locations)

                if GUI_MODE:
                    print(json.dumps({
                        "event": "stats",
                        "slot": self.selected_slot_name,
                        "game": self.game,
                        "checked": checked,
                        "total": total,
                        "accessible": accessible
                    }), flush=True)
                elif not SILENT_MODE:
                    print(f"\n==================================================", flush=True)
                    print(f"Slot: {self.selected_slot_name} | Game: {self.game}", flush=True)
                    print(f"Checks: {checked} / {total} checked", flush=True)
                    print(f"Accessible (In Logic): {accessible}", flush=True)
                    print(f"==================================================", flush=True)

                # Export accessible locations and stats to files (useful for OBS overlays)
                try:
                    import re
                    workspace_path = get_workspace_path()
                    
                    # 1. Remaining accessible checks list
                    out_file = os.path.join(workspace_path, "remaining_locations.txt")
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(f"--- {self.selected_slot_name} ({self.game}) - Accessible Checks ({accessible}) ---\n")
                        for loc in state.readable_locations:
                            clean_loc = re.sub(r"\[/?color.*?\]", "", loc)
                            f.write(clean_loc + "\n")
                    
                    # 2. Combined stats file for OBS
                    stats_file = os.path.join(workspace_path, "obs_stats.txt")
                    with open(stats_file, "w", encoding="utf-8") as f:
                        f.write(f"Slot: {self.selected_slot_name} | Game: {self.game}\n")
                        f.write(f"Checks: {checked} / {total}\n")
                        f.write(f"Accessible: {accessible}\n")
                    
                    # 3. Individual files for custom OBS formatting
                    with open(os.path.join(workspace_path, "obs_checks.txt"), "w", encoding="utf-8") as f:
                        f.write(f"{checked} / {total}")
                    with open(os.path.join(workspace_path, "obs_accessible.txt"), "w", encoding="utf-8") as f:
                        f.write(f"{accessible}")
                    with open(os.path.join(workspace_path, "obs_slot.txt"), "w", encoding="utf-8") as f:
                        f.write(f"{self.selected_slot_name} ({self.game})")
                        
                    if not GUI_MODE and not SILENT_MODE:
                        print(f"Updated OBS & remaining checks files.", flush=True)
                except Exception as fe:
                    if not GUI_MODE and not SILENT_MODE:
                        print(f"Error writing files: {fe}", file=sys.stderr, flush=True)

            except Exception as e:
                if GUI_MODE:
                    print(json.dumps({"event": "error", "message": f"Logic error: {e}"}), flush=True)
                elif not SILENT_MODE:
                    import traceback
                    print(f"Error updating tracker logic: {traceback.format_exc()}", file=sys.stderr, flush=True)

    CLITrackerContext = DynamicCLITrackerContext
    if game_name:
        ensure_world_loaded(game_name)
    _context_classes_initialized = True



def get_game_from_yaml(players_dir, slot_name):
    # Find matching YAML file and extract game name
    if not os.path.exists(players_dir):
        return None
    for file_name in os.listdir(players_dir):
        if file_name.endswith((".yaml", ".yml")):
            file_path = os.path.join(players_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                # Parse name
                match_name = re.search(r"^\s*name\s*:\s*[\"']?(.+?)[\"']?\s*$", content, re.MULTILINE)
                if match_name and match_name.group(1).strip().lower() == slot_name.lower():
                    # Parse game
                    match_game = re.search(r"^\s*game\s*:\s*[\"']?(.+?)[\"']?\s*$", content, re.MULTILINE)
                    if match_game:
                        return match_game.group(1).strip(), file_path, file_name
            except Exception:
                pass
    return None


async def main():
    server = "localhost:38281"
    slot_name = "OOT"
    password = None
    game_name = None

    server_resolved = None
    slot_resolved = None
    password_resolved = None
    game_resolved = None

    for flag in ("--server", "-h", "--host"):
        try:
            idx = sys.argv.index(flag)
            server_resolved = sys.argv[idx + 1]
            break
        except (ValueError, IndexError):
            pass
            
    for flag in ("--slot", "-s"):
        try:
            idx = sys.argv.index(flag)
            slot_resolved = sys.argv[idx + 1]
            break
        except (ValueError, IndexError):
            pass
            
    for flag in ("--password", "-p"):
        try:
            idx = sys.argv.index(flag)
            password_resolved = sys.argv[idx + 1]
            break
        except (ValueError, IndexError):
            pass

    for flag in ("--game", "-g"):
        try:
            idx = sys.argv.index(flag)
            game_resolved = sys.argv[idx + 1]
            break
        except (ValueError, IndexError):
            pass

    # Parse positional arguments
    positional_args = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith('-'):
            if arg in ("--server", "-h", "--host", "--slot", "-s", "--password", "-p", "--game", "-g"):
                skip_next = True
            continue
        positional_args.append(arg)

    if len(positional_args) >= 1 and not server_resolved:
        server_resolved = positional_args[0]
    if len(positional_args) >= 2 and not slot_resolved:
        slot_resolved = positional_args[1]
    if len(positional_args) >= 3 and not password_resolved:
        password_resolved = positional_args[2]

    # Map resolved parameters back
    if server_resolved:
        server = server_resolved
    if slot_resolved:
        slot_name = slot_resolved
    if password_resolved:
        password = password_resolved
    if game_resolved:
        game_name = game_resolved

    has_args = bool(server_resolved or slot_resolved)

    if has_args:
        import time
        t_tcp_start = time.time()
        control_port = 38283
        try:
            port_idx = sys.argv.index("--control-port")
            control_port = int(sys.argv[port_idx + 1])
        except (ValueError, IndexError):
            pass

        for port in range(control_port, control_port + 5):
            t_port_start = time.time()
            try:
                # Add a timeout of 0.2 seconds to prevent hanging on closed ports
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection('127.0.0.1', port),
                    timeout=0.2
                )
                server_to_send = server
                if "archipelago.gg" in server_to_send and not server_to_send.startswith(("ws://", "wss://")):
                    server_to_send = f"wss://{server_to_send}"
                elif ":" not in server_to_send and not server_to_send.startswith(("ws://", "wss://")):
                    server_to_send = f"localhost:{server_to_send}"

                game_to_send = game_name
                if not game_to_send:
                    res = get_game_from_yaml(os.path.join(ap_dir, "Players"), slot_name)
                    if res:
                        game_to_send = res[0]

                payload = {
                    "action": "connect",
                    "server": server_to_send,
                    "slot": slot_name,
                    "password": password,
                    "game": game_to_send
                }
                writer.write(json.dumps(payload).encode() + b"\n")
                await writer.drain()
                resp = await reader.readline()
                writer.close()
                await writer.wait_closed()
                if resp.strip() == b"OK":
                    if not SILENT_MODE:
                        print(f"Sent connection command to running instance on port {port} (Server: {server_to_send}, Slot: {slot_name}, Game: {game_to_send}). Exiting.")
                    return
            except Exception:
                pass
            finally:
                t_port_elapsed = time.time() - t_port_start
                if not SILENT_MODE and t_port_elapsed > 0.05:
                    print(f"[Timer] Checked port {port} in {t_port_elapsed:.3f}s", flush=True)

        if not SILENT_MODE:
            print(f"[Timer] Total duplicate instance check took: {time.time() - t_tcp_start:.3f}s", flush=True)

    if not GUI_MODE and not SILENT_MODE and not has_args:
        print("=== Archipelago CLI Universal Tracker ===")
        server = input(f"Server address [{server}]: ").strip() or server
        slot_name = input(f"Slot Name (YAML name) [{slot_name}]: ").strip() or slot_name
        password = input("Password (optional): ").strip() or password

    temp_dir_obj = None
    idle_mode = "--idle" in sys.argv
    players_dir = os.path.join(ap_dir, "Players")
    cli_multiworld_cache = {}

    # Initialize OBS files to default values on startup
    try:
        w_path = get_workspace_path()
        for fname, val in [("obs_stats.txt", "Disconnected"), ("obs_checks.txt", "-- / --"), ("obs_accessible.txt", "--"), ("obs_slot.txt", "Disconnected")]:
            with open(os.path.join(w_path, fname), "w", encoding="utf-8") as f:
                f.write(val)
    except Exception:
        pass

    if idle_mode:
        ctx = IdleContext()
        ctx.game = None
        ctx.temp_dir_obj = None
        ctx.server_task = None
    else:
        import time
        t_start = time.time()
        if "archipelago.gg" in server and not server.startswith(("ws://", "wss://")):
            server = f"wss://{server}"
        elif ":" not in server and not server.startswith(("ws://", "wss://")):
            server = f"localhost:{server}"

        # 1. Resolve game and copy YAML
        t_yaml_start = time.time()
        res = get_game_from_yaml(players_dir, slot_name)
        if res is None:
            if game_name is None:
                if GUI_MODE:
                    print(json.dumps({"event": "error", "message": f"No YAML found for slot '{slot_name}' in '{players_dir}'"}), flush=True)
                    return
                elif not SILENT_MODE:
                    print(f"\n[Warning] No YAML file found for slot '{slot_name}' in '{players_dir}'.")
                    print("A dummy YAML with default options will be used.")
                    game_name = input("Enter Game Name (e.g. 'Ocarina of Time'): ").strip()
                    if not game_name:
                        print("Error: Game name is required to run logic generator.", file=sys.stderr)
                        return
            
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_obj.name
            dummy_data = {
                "name": slot_name,
                "game": game_name,
                game_name: {}
            }
            with open(os.path.join(temp_dir, "dummy.yaml"), "w", encoding="utf-8") as f:
                json.dump(dummy_data, f)
            t_import_start = time.time()
            initialize_dynamic_imports(game_name)
            t_import_end = time.time()
            if not SILENT_MODE:
                print(f"[Timer] Dynamic imports took: {t_import_end - t_import_start:.3f}s", flush=True)
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir
        else:
            game_name, file_path, file_name = res
            if not GUI_MODE and not SILENT_MODE:
                print(f"\n[Info] Found YAML: '{file_name}' (Game: '{game_name}')")
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_obj.name
            
            with open(file_path, "r", encoding="utf-8-sig") as f:
                yaml_content = f.read()
                
            lines = yaml_content.splitlines()
            new_lines = []
            in_requires = False
            for line in lines:
                if line.strip().startswith("requires:"):
                    in_requires = True
                    new_lines.append("# " + line)
                elif in_requires and (line.startswith(" ") or line.startswith("\t") or not line.strip()):
                    if not line.strip():
                        new_lines.append(line)
                    else:
                        new_lines.append("# " + line)
                else:
                    in_requires = False
                    new_lines.append(line)
            yaml_content = "\n".join(new_lines)
            
            with open(os.path.join(temp_dir, file_name), "w", encoding="utf-8") as f:
                f.write(yaml_content)
                
            t_import_start = time.time()
            initialize_dynamic_imports(game_name)
            t_import_end = time.time()
            if not SILENT_MODE:
                print(f"[Timer] Resolving YAML took: {t_import_start - t_yaml_start:.3f}s", flush=True)
                print(f"[Timer] Dynamic imports took: {t_import_end - t_import_start:.3f}s", flush=True)
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir

        # 2. Initialize context
        ctx = CLITrackerContext(server, password, slot_name)
        ctx.game = game_name
        ctx.temp_dir_obj = temp_dir_obj

        # 3. Check game world is installed
        connected_cls = AutoWorldRegister.world_types.get(game_name)
        if connected_cls is None:
            from worlds import failed_world_loads
            error_msg = f"Game '{game_name}' is not installed in the active environment."
            matching_failures = []
            for name, tb in failed_world_loads.items():
                if game_name.lower() in name.lower() or "albw" in name.lower() or name.lower() in game_name.lower():
                    matching_failures.append(f"World '{name}' failed to load:\n{tb}")
            if matching_failures:
                error_msg += "\n\nLoading errors:\n" + "\n".join(matching_failures)

            if GUI_MODE:
                print(json.dumps({"event": "error", "message": error_msg}), flush=True)
            else:
                print(f"Error: {error_msg}", file=sys.stderr)
                print(f"Installed games: {', '.join(sorted(AutoWorldRegister.world_types.keys()))}", file=sys.stderr)
            temp_dir_obj.cleanup()
            return

        # 4. Run generator
        if GUI_MODE:
            print(json.dumps({"event": "generating"}), flush=True)
        elif not SILENT_MODE:
            print("Running Archipelago logic generator...")
        
        try:
            t_gen_start = time.time()
            ctx.run_generator()
            t_gen_end = time.time()
            if not SILENT_MODE:
                print(f"[Timer] Archipelago logic generator took: {t_gen_end - t_gen_start:.3f}s", flush=True)
            cli_multiworld_cache[slot_name] = (
                ctx.tracker_core.multiworld,
                ctx.tracker_core.launch_multiworld,
                ctx.use_split,
                ctx.temp_dir_obj
            )
        except Exception as e:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Generator error: {e}"}), flush=True)
            else:
                print(f"Error running logic generator: {e}", file=sys.stderr)
            if temp_dir_obj:
                try:
                    temp_dir_obj.cleanup()
                except Exception:
                    pass
            return

        # 5. Connect
        if not GUI_MODE and not SILENT_MODE:
            print(f"Connecting to {server}...")
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    # Start background stdin thread (running in all modes)
    import queue
    import threading
    input_queue = queue.Queue()

    def stdin_reader():
        if sys.stdin is None:
            return
        try:
            for line in sys.stdin:
                if not line:
                    break
                line = line.strip()
                if line:
                    input_queue.put(line)
        except Exception:
            pass

    threading.Thread(target=stdin_reader, daemon=True).start()

    async def disconnect_tracker():
        task = getattr(ctx, "server_task", None)
        if task and not task.done():
            try:
                await asyncio.wait_for(ctx.disconnect(allow_autoreconnect=False), timeout=1.0)
            except BaseException:
                pass
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except BaseException:
                pass
        ctx.items_received = []
        ctx.locations_checked = set()
        ctx.checked_locations = set()
        ctx.missing_locations = set()
        ctx.local_items = []
        
        # Reset OBS files to clean default values when offline
        try:
            workspace_path = get_workspace_path()
            for fname, val in [("obs_stats.txt", "Disconnected"), ("obs_checks.txt", "-- / --"), ("obs_accessible.txt", "--"), ("obs_slot.txt", "Disconnected")]:
                with open(os.path.join(workspace_path, fname), "w", encoding="utf-8") as f:
                    f.write(val)
        except Exception:
            pass

        if GUI_MODE:
            print(json.dumps({"event": "disconnected"}), flush=True)
        elif not SILENT_MODE:
            print("[Info] Disconnected.", flush=True)

    async def reconnect_tracker(data):
        nonlocal temp_dir_obj, ctx
        r_server = data.get("server") or server
        r_slot = data.get("slot") or slot_name
        r_password = data.get("password") or password
        r_game = data.get("game") or game_name

        if "archipelago.gg" in r_server and not r_server.startswith(("ws://", "wss://")):
            r_server = f"wss://{r_server}"
        elif ":" not in r_server and not r_server.startswith(("ws://", "wss://")):
            r_server = f"localhost:{r_server}"

        # 1. Disconnect current session
        task = getattr(ctx, "server_task", None)
        if task and not task.done():
            try:
                await asyncio.wait_for(ctx.disconnect(allow_autoreconnect=False), timeout=1.0)
            except BaseException:
                pass
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except BaseException:
                pass

        # Parse game if not set yet (we might need to search the YAML files)
        if not r_game:
            res = get_game_from_yaml(players_dir, r_slot)
            if res:
                r_game = res[0]
            else:
                r_game = "Ocarina of Time"

        # Initialize the heavy dependencies now that we know the game name
        initialize_dynamic_imports(r_game)
        if isinstance(ctx, IdleContext):
            # Transition to a real context
            ctx = CLITrackerContext(r_server, r_password, r_slot)
            ctx.game = r_game

        ctx.reconnecting = True
        ctx.items_received = []
        ctx.locations_checked = set()
        ctx.checked_locations = set()
        ctx.missing_locations = set()
        ctx.local_items = []

        # Check if we have this slot in our hot-cache
        if r_slot in cli_multiworld_cache:
            c_mw, c_lmw, c_use_split, c_temp = cli_multiworld_cache[r_slot]
            ctx.tracker_core.multiworld = c_mw
            ctx.tracker_core.launch_multiworld = c_lmw
            ctx.use_split = c_use_split
            
            if ctx.temp_dir_obj and ctx.temp_dir_obj not in [item[3] for item in cli_multiworld_cache.values()]:
                try:
                    ctx.temp_dir_obj.cleanup()
                except Exception:
                    pass
            ctx.temp_dir_obj = c_temp

            ctx.server_address = r_server
            ctx.auth = r_slot
            ctx.selected_slot_name = r_slot
            ctx.password = r_password
            ctx.game = r_game
            
            ctx.reconnecting = False
            ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
            return

        # Check if we can reuse the existing launch_multiworld
        reuse_multiworld = False
        if ctx.tracker_core.launch_multiworld is not None:
            if r_slot in ctx.tracker_core.launch_multiworld.world_name_lookup:
                internal_id = ctx.tracker_core.launch_multiworld.world_name_lookup[r_slot]
                if ctx.tracker_core.launch_multiworld.worlds[internal_id].game == r_game:
                    reuse_multiworld = True

        if reuse_multiworld:
            ctx.server_address = r_server
            ctx.auth = r_slot
            ctx.selected_slot_name = r_slot
            ctx.password = r_password
            ctx.game = r_game
            
            # Reconnect by spawning new server loop
            ctx.reconnecting = False
            ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
            return

        if ctx.temp_dir_obj:
            try:
                ctx.temp_dir_obj.cleanup()
            except Exception:
                pass
            ctx.temp_dir_obj = None

        ctx.tracker_core.player_folder_override = None

        # 2. Resolve game and copy YAML
        res = get_game_from_yaml(players_dir, r_slot)
        if res is None:
            if r_game is None:
                if GUI_MODE:
                    print(json.dumps({"event": "error", "message": f"No YAML found for slot '{r_slot}'"}), flush=True)
                    return
                elif not SILENT_MODE:
                    print(f"Warning: No YAML found for slot '{r_slot}', defaulting game name.")
                r_game = "Ocarina of Time"
            
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_obj.name
            dummy_data = {
                "name": r_slot,
                "game": r_game,
                r_game: {}
            }
            with open(os.path.join(temp_dir, "dummy.yaml"), "w", encoding="utf-8") as f:
                json.dump(dummy_data, f)
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir
        else:
            r_game, file_path, file_name = res
            temp_dir_obj = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_obj.name
            
            with open(file_path, "r", encoding="utf-8-sig") as f:
                yaml_content = f.read()
                
            lines = yaml_content.splitlines()
            new_lines = []
            in_requires = False
            for line in lines:
                if line.strip().startswith("requires:"):
                    in_requires = True
                    new_lines.append("# " + line)
                elif in_requires and (line.startswith(" ") or line.startswith("\t") or not line.strip()):
                    if not line.strip():
                        new_lines.append(line)
                    else:
                        new_lines.append("# " + line)
                else:
                    in_requires = False
                    new_lines.append(line)
            yaml_content = "\n".join(new_lines)
            
            with open(os.path.join(temp_dir, file_name), "w", encoding="utf-8") as f:
                f.write(yaml_content)
                
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir

        ctx.server_address = r_server
        ctx.auth = r_slot
        ctx.selected_slot_name = r_slot
        ctx.password = r_password
        ctx.game = r_game
        ctx.temp_dir_obj = temp_dir_obj

        # 3. Check game world is installed
        connected_cls = AutoWorldRegister.world_types.get(r_game)
        if connected_cls is None:
            from worlds import failed_world_loads
            error_msg = f"Game '{r_game}' is not installed in the active environment."
            matching_failures = []
            for name, tb in failed_world_loads.items():
                if r_game.lower() in name.lower() or "albw" in name.lower() or name.lower() in r_game.lower():
                    matching_failures.append(f"World '{name}' failed to load:\n{tb}")
            if matching_failures:
                error_msg += "\n\nLoading errors:\n" + "\n".join(matching_failures)

            if GUI_MODE:
                print(json.dumps({"event": "error", "message": error_msg}), flush=True)
            elif not SILENT_MODE:
                print(f"Error: {error_msg}", file=sys.stderr, flush=True)
            ctx.reconnecting = False
            return

        # 4. Run generator
        if GUI_MODE:
            print(json.dumps({"event": "generating"}), flush=True)
        elif not SILENT_MODE:
            print("Running Archipelago logic generator...", flush=True)
        try:
            ctx.run_generator()
            cli_multiworld_cache[r_slot] = (
                ctx.tracker_core.multiworld,
                ctx.tracker_core.launch_multiworld,
                ctx.use_split,
                ctx.temp_dir_obj
            )
        except Exception as e:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Generator error: {e}"}), flush=True)
            elif not SILENT_MODE:
                print(f"Error running logic generator: {e}", file=sys.stderr, flush=True)
            ctx.reconnecting = False
            return

        # 5. Connect
        if not GUI_MODE and not SILENT_MODE:
            print(f"Connecting to {r_server}...", flush=True)
        ctx.reconnecting = False
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    async def process_command_string(line):
        line = line.strip()
        if not line:
            return
        if line.startswith("{"):
            try:
                data = json.loads(line)
                if data.get("action") == "connect":
                    await reconnect_tracker(data)
                elif data.get("action") == "disconnect":
                    await disconnect_tracker()
                elif data.get("action") == "exit":
                    ctx.exit_event.set()
            except Exception as je:
                if not SILENT_MODE:
                    print(json.dumps({"event": "error", "message": f"JSON parse error: {je}"}), flush=True)
        elif line.startswith("/"):
            parts = line.split()
            cmd = parts[0].lower()
            if cmd == "/connect":
                if len(parts) < 3:
                    if not SILENT_MODE:
                        print("Usage: /connect <server> <slot> [password]", flush=True)
                    return
                srv = parts[1]
                slt = parts[2]
                pwd = parts[3] if len(parts) > 3 else None
                await reconnect_tracker({"server": srv, "slot": slt, "password": pwd})
            elif cmd == "/slot":
                if len(parts) < 2:
                    if not SILENT_MODE:
                        print("Usage: /slot <slot_name>", flush=True)
                    return
                slt = parts[1]
                await reconnect_tracker({"server": ctx.server_address, "slot": slt, "password": ctx.password})
            elif cmd == "/server":
                if len(parts) < 2:
                    if not SILENT_MODE:
                        print("Usage: /server <server_address>", flush=True)
                    return
                srv = parts[1]
                await reconnect_tracker({"server": srv, "slot": ctx.auth, "password": ctx.password})
            elif cmd == "/disconnect":
                await disconnect_tracker()
            elif cmd in ("/exit", "/quit"):
                ctx.exit_event.set()
            else:
                if not SILENT_MODE:
                    print(f"Unknown command: {cmd}", flush=True)
        else:
            if not SILENT_MODE:
                print("Commands must start with / or be JSON", flush=True)

    # Start TCP control server
    control_port = 38283
    try:
        port_idx = sys.argv.index("--control-port")
        control_port = int(sys.argv[port_idx + 1])
    except (ValueError, IndexError):
        pass

    async def handle_tcp_command(reader, writer):
        try:
            data = await reader.readline()
            message = data.decode().strip()
            if message:
                await process_command_string(message)
            writer.write(b"OK\n")
            await writer.drain()
        except Exception as e:
            if not SILENT_MODE:
                print(f"[TCP Control] Error: {e}", file=sys.stderr, flush=True)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    tcp_server = None
    for attempt in range(5):
        try:
            tcp_server = await asyncio.start_server(handle_tcp_command, '127.0.0.1', control_port + attempt)
            if not SILENT_MODE and not GUI_MODE:
                print(f"TCP control server listening on 127.0.0.1:{control_port + attempt}", flush=True)
            break
        except Exception as tse:
            if attempt == 4:
                if not SILENT_MODE and not GUI_MODE:
                    print(f"Could not start TCP control server (tried ports {control_port} to {control_port+4}): {tse}", file=sys.stderr, flush=True)

    # Keep CLI running until exit
    try:
        while not ctx.exit_event.is_set():
            try:
                while True:
                    line = input_queue.get_nowait()
                    if line:
                        await process_command_string(line)
            except queue.Empty:
                pass
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        if not GUI_MODE and not SILENT_MODE:
            print("\nStopping...", flush=True)
        ctx.exit_event.set()

    if tcp_server:
        tcp_server.close()
        await tcp_server.wait_closed()

    await ctx.shutdown()
    for cached_vals in cli_multiworld_cache.values():
        c_temp = cached_vals[3]
        if c_temp:
            try:
                c_temp.cleanup()
            except Exception:
                pass
    if temp_dir_obj:
        try:
            temp_dir_obj.cleanup()
        except Exception:
            pass
    if not GUI_MODE and not SILENT_MODE:
        print("Done.", flush=True)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
