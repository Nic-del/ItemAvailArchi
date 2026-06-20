import asyncio
import sys
import os
import logging
import types
import tempfile
import shutil
import re
import json

# Mock ModuleUpdate to bypass Python version checks
mock_module_update = types.ModuleType("ModuleUpdate")
mock_module_update.update = lambda *args, **kwargs: None
sys.modules["ModuleUpdate"] = mock_module_update

# Add paths
tracker_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(tracker_dir))
sys.path.insert(0, tracker_dir)

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

# Patch os.scandir to hide tracker.apworld to avoid duplicate "Universal Tracker" registration
orig_scandir = os.scandir
class PatchedScandirIterator:
    def __init__(self, orig_iterator):
        self.orig_iterator = orig_iterator
    def __iter__(self):
        return self
    def __next__(self):
        while True:
            entry = next(self.orig_iterator)
            if entry.name == "tracker.apworld":
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
    return PatchedScandirIterator(orig_scandir(path))
os.scandir = patched_scandir

# Configure Kivy to run hidden
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_GRAPHICS_WINDOW_STATE"] = "hidden"
os.environ["KIVY_GRAPHICS_HIDDEN"] = "1"
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
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
root_logger.addHandler(console_handler)

from tracker.TrackerClient import TrackerGameContext, server_loop
from worlds.AutoWorld import AutoWorldRegister
from tracker import TrackerWorld

class SettingsDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

# Initialize settings with defaults
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

logger = logging.getLogger("TrackerCLI")

GUI_MODE = "--gui" in sys.argv

class CLITrackerContext(TrackerGameContext):
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
        else:
            print("\n[Info] Disconnecting from server...")
        await super().disconnect(allow_autoreconnect)

    async def connection_closed(self):
        if GUI_MODE:
            if not getattr(self, "reconnecting", False):
                print(json.dumps({"event": "disconnected"}), flush=True)
        else:
            print("\n[Info] Connection closed.", file=sys.stderr)
        await super().connection_closed()

    def on_print(self, args: dict):
        if not GUI_MODE:
            print(f"[Server] {args['text']}")

    def on_print_json(self, args: dict):
        if not GUI_MODE:
            print(f"[Server] {self.jsontotextparser(args['data'])}")

    def handle_connection_loss(self, msg: str) -> None:
        if GUI_MODE:
            print(json.dumps({"event": "error", "message": msg}), flush=True)
        else:
            import traceback
            print(f"\n[Connection Loss] {msg}", file=sys.stderr)
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
                else:
                    print("\n[Success] Connected to Archipelago server!")
        except Exception as e:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Package error: {e}"}), flush=True)
            else:
                import traceback
                print(f"\n[Error processing package {cmd}] {traceback.format_exc()}", file=sys.stderr)

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
            else:
                print(f"\n==================================================")
                print(f"Slot: {self.selected_slot_name} | Game: {self.game}")
                print(f"Checks: {checked} / {total} checked")
                print(f"Accessible (In Logic): {accessible}")
                print(f"==================================================")

            # Export accessible locations and stats to files (useful for OBS overlays)
            try:
                import re
                workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
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
                    
                if not GUI_MODE:
                    print(f"Updated OBS & remaining checks files.")
            except Exception as fe:
                if not GUI_MODE:
                    print(f"Error writing files: {fe}", file=sys.stderr)

        except Exception as e:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Logic error: {e}"}), flush=True)
            else:
                import traceback
                print(f"Error updating tracker logic: {traceback.format_exc()}", file=sys.stderr)


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
    server_resolved = None
    slot_resolved = None
    password_resolved = None

    try:
        if "--server" in sys.argv:
            server_resolved = sys.argv[sys.argv.index("--server") + 1]
        elif "-h" in sys.argv:
            server_resolved = sys.argv[sys.argv.index("-h") + 1]
    except (ValueError, IndexError):
        pass

    try:
        if "--slot" in sys.argv:
            slot_resolved = sys.argv[sys.argv.index("--slot") + 1]
        elif "-s" in sys.argv:
            slot_resolved = sys.argv[sys.argv.index("-s") + 1]
    except (ValueError, IndexError):
        pass

    try:
        if "--password" in sys.argv:
            password_resolved = sys.argv[sys.argv.index("--password") + 1]
        elif "-p" in sys.argv:
            password_resolved = sys.argv[sys.argv.index("-p") + 1]
    except (ValueError, IndexError):
        pass

    # Parse positional arguments as fallbacks
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

    # Map defaults/resolutions
    server = server_resolved or "localhost:38281"
    slot_name = slot_resolved or "OOT"
    password = password_resolved

    if not GUI_MODE and not (server_resolved or slot_resolved):
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
        w_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for fname, val in [("obs_stats.txt", "Disconnected"), ("obs_checks.txt", "-- / --"), ("obs_accessible.txt", "--"), ("obs_slot.txt", "Disconnected")]:
            with open(os.path.join(w_path, fname), "w", encoding="utf-8") as f:
                f.write(val)
    except Exception:
        pass

    if idle_mode:
        ctx = CLITrackerContext("localhost:38281", None, "OOT")
        ctx.game = None
        ctx.temp_dir_obj = None
        ctx.server_task = None
    else:
        if "archipelago.gg" in server and not server.startswith(("ws://", "wss://")):
            server = f"wss://{server}"
        elif ":" not in server and not server.startswith(("ws://", "wss://")):
            server = f"localhost:{server}"

        # 1. Resolve game and copy YAML
        res = get_game_from_yaml(players_dir, slot_name)
        if res is None:
            game_name = None
            try:
                game_idx = sys.argv.index("--game")
                game_name = sys.argv[game_idx + 1]
            except (ValueError, IndexError):
                pass
                
            if game_name is None:
                if GUI_MODE:
                    print(json.dumps({"event": "error", "message": f"No YAML found for slot '{slot_name}' in '{players_dir}'"}), flush=True)
                    return
                else:
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
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir
        else:
            game_name, file_path, file_name = res
            if not GUI_MODE:
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
                
            TrackerWorld._AutoWorldRegister__settings["player_files_path"] = temp_dir

        # 2. Initialize context
        ctx = CLITrackerContext(server, password, slot_name)
        ctx.game = game_name
        ctx.temp_dir_obj = temp_dir_obj

        # 3. Check game world is installed
        connected_cls = AutoWorldRegister.world_types.get(game_name)
        if connected_cls is None:
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Game '{game_name}' is not installed in the active environment."}), flush=True)
            else:
                print(f"Error: Game '{game_name}' is not installed in the active Archipelago environment.", file=sys.stderr)
                print(f"Installed games: {', '.join(sorted(AutoWorldRegister.world_types.keys()))}", file=sys.stderr)
            temp_dir_obj.cleanup()
            return

        # 4. Run generator
        if GUI_MODE:
            print(json.dumps({"event": "generating"}), flush=True)
        else:
            print("Running Archipelago logic generator...")
        
        try:
            ctx.run_generator()
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
        if not GUI_MODE:
            print(f"Connecting to {server}...")
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    # Start background stdin thread in GUI mode
    import queue
    import threading
    input_queue = queue.Queue()

    def stdin_reader():
        try:
            for line in sys.stdin:
                if not line:
                    break
                input_queue.put(line.strip())
        except Exception:
            pass

    if GUI_MODE:
        threading.Thread(target=stdin_reader, daemon=True).start()

    async def disconnect_tracker():
        task = getattr(ctx, "server_task", None)
        if task and not task.done():
            await ctx.disconnect(allow_autoreconnect=False)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        ctx.items_received = []
        ctx.locations_checked = set()
        ctx.checked_locations = set()
        ctx.missing_locations = set()
        ctx.local_items = []
        
        # Reset OBS files to clean default values when offline
        try:
            workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for fname, val in [("obs_stats.txt", "Disconnected"), ("obs_checks.txt", "-- / --"), ("obs_accessible.txt", "--"), ("obs_slot.txt", "Disconnected")]:
                with open(os.path.join(workspace_path, fname), "w", encoding="utf-8") as f:
                    f.write(val)
        except Exception:
            pass

        if GUI_MODE:
            print(json.dumps({"event": "disconnected"}), flush=True)

    async def reconnect_tracker(data):
        nonlocal temp_dir_obj
        ctx.reconnecting = True
        r_server = data.get("server")
        r_slot = data.get("slot")
        r_password = data.get("password")
        r_game = data.get("game")

        # 1. Disconnect current session
        task = getattr(ctx, "server_task", None)
        if task and not task.done():
            await ctx.disconnect(allow_autoreconnect=False)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

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
            if GUI_MODE:
                print(json.dumps({"event": "error", "message": f"Game '{r_game}' is not installed in the active environment."}), flush=True)
            ctx.reconnecting = False
            return

        # 4. Run generator
        if GUI_MODE:
            print(json.dumps({"event": "generating"}), flush=True)
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
            ctx.reconnecting = False
            return

        # 5. Connect
        ctx.reconnecting = False
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    # Keep CLI running until exit
    try:
        while not ctx.exit_event.is_set():
            if GUI_MODE:
                try:
                    while True:
                        line = input_queue.get_nowait()
                        if line:
                            try:
                                data = json.loads(line)
                                if data.get("action") == "connect":
                                    asyncio.create_task(reconnect_tracker(data))
                                elif data.get("action") == "disconnect":
                                    asyncio.create_task(disconnect_tracker())
                            except Exception as je:
                                print(json.dumps({"event": "error", "message": f"JSON parse error: {je}"}), flush=True)
                except queue.Empty:
                    pass
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        if not GUI_MODE:
            print("\nStopping...")
        ctx.exit_event.set()

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
    if not GUI_MODE:
        print("Done.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
