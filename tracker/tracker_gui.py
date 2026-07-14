import sys
import os

# Disable Kivy window and logs globally at the absolute start of the program
os.environ["KIVY_WINDOW"] = "dummy"
os.environ["KIVY_NO_WINDOW"] = "1"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_GRAPHICS_WINDOW_STATE"] = "hidden"
os.environ["KIVY_GRAPHICS_HIDDEN"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"

import json
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

# --- GUI THREAD COMMUNICATIONS ---
gui_queue = queue.Queue()

def get_settings_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "tracker_settings.json")

# Load and inject saved ap_dir if not specified on the command-line
try:
    _settings_file = get_settings_path()
    if os.path.exists(_settings_file):
        with open(_settings_file, "r", encoding="utf-8") as _f:
            _saved_ap_dir = json.load(_f).get("ap_dir")
            if _saved_ap_dir:
                for c in ['\u202a', '\u202b', '\u202c', '\u202d', '\u202e']:
                    _saved_ap_dir = _saved_ap_dir.replace(c, '')
                _saved_ap_dir = _saved_ap_dir.strip().strip('"').strip("'").strip()
                if _saved_ap_dir and "--ap-dir" not in sys.argv:
                    sys.argv.extend(["--ap-dir", _saved_ap_dir])
except Exception:
    pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AP Mini Tracker")
        self.root.geometry("420x530")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, False)

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Dark Theme settings
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4", insertcolor="#cdd6f4", bordercolor="#45475a")
        self.style.configure("TButton", background="#45475a", foreground="#cdd6f4", bordercolor="#585b70", font=("Segoe UI", 10, "bold"))
        self.style.map("TButton", background=[("active", "#585b70")])

        # Parse command line arguments
        server_arg = None
        slot_arg = None
        self.password_arg = None
        auto_connect = False

        # 1. Parse named flags
        try:
            if "--server" in sys.argv:
                server_arg = sys.argv[sys.argv.index("--server") + 1]
            elif "-h" in sys.argv:
                server_arg = sys.argv[sys.argv.index("-h") + 1]
            elif "--host" in sys.argv:
                server_arg = sys.argv[sys.argv.index("--host") + 1]
        except (ValueError, IndexError):
            pass

        try:
            if "--slot" in sys.argv:
                slot_arg = sys.argv[sys.argv.index("--slot") + 1]
            elif "-s" in sys.argv:
                slot_arg = sys.argv[sys.argv.index("-s") + 1]
        except (ValueError, IndexError):
            pass

        try:
            if "--password" in sys.argv:
                self.password_arg = sys.argv[sys.argv.index("--password") + 1]
            elif "-p" in sys.argv:
                self.password_arg = sys.argv[sys.argv.index("-p") + 1]
        except (ValueError, IndexError):
            pass

        if "--connect" in sys.argv or "-c" in sys.argv:
            auto_connect = True

        # 2. Parse positional arguments as fallbacks
        positional_args = []
        skip_next = False
        for arg in sys.argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if arg.startswith('-'):
                if arg in ("--server", "-h", "--host", "--slot", "-s", "--password", "-p", "--ap-dir"):
                    skip_next = True
                continue
            positional_args.append(arg)

        # Assign positional arguments to unfilled parameters
        if len(positional_args) >= 1 and not server_arg:
            server_arg = positional_args[0]
        if len(positional_args) >= 2 and not slot_arg:
            slot_arg = positional_args[1]
        if len(positional_args) >= 3 and not self.password_arg:
            self.password_arg = positional_args[2]

        # Auto-connect if both server and slot are resolved
        if server_arg and slot_arg:
            auto_connect = True

        # Apply defaults if still unresolved
        saved_server = None
        saved_slot = None
        saved_password = None
        saved_ap_dir = None
        try:
            settings_path = get_settings_path()
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    saved_server = settings.get("server")
                    saved_slot = settings.get("slot")
                    saved_password = settings.get("password")
                    saved_ap_dir = settings.get("ap_dir")
        except Exception:
            pass

        if not server_arg:
            server_arg = saved_server or "localhost:38281"
        if not slot_arg:
            slot_arg = saved_slot or "LADXBeta"
        if not self.password_arg:
            self.password_arg = saved_password or ""

        ap_dir_arg = None
        try:
            if "--ap-dir" in sys.argv:
                ap_dir_arg = sys.argv[sys.argv.index("--ap-dir") + 1]
        except (ValueError, IndexError):
            pass
        if not ap_dir_arg:
            ap_dir_arg = saved_ap_dir or ""

        # State vars
        self.tracking_active = False
        self.slots = {}
        self.proc = None

        # Connection Frame
        self.conn_frame = tk.Frame(root, bg="#1e1e2e")
        self.conn_frame.pack(fill=tk.X, padx=15, pady=10)

        # Server
        tk.Label(self.conn_frame, text="Server:", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, sticky="w", pady=2)
        self.server_entry = ttk.Entry(self.conn_frame, width=22)
        self.server_entry.insert(0, server_arg)
        self.server_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Connect Button
        self.connect_btn = ttk.Button(self.conn_frame, text="Connect", command=self.toggle_connection, width=10)
        self.connect_btn.grid(row=0, column=2, rowspan=3, padx=5, sticky="ns")

        # Slot Name
        tk.Label(self.conn_frame, text="Slot Name:", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, sticky="w", pady=2)
        self.slot_entry = ttk.Entry(self.conn_frame, width=22)
        self.slot_entry.insert(0, slot_arg)
        self.slot_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Password
        tk.Label(self.conn_frame, text="Password:", bg="#1e1e2e", fg="#cdd6f4").grid(row=2, column=0, sticky="w", pady=2)
        self.password_frame = tk.Frame(self.conn_frame, bg="#1e1e2e")
        self.password_frame.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.password_entry = ttk.Entry(self.password_frame, width=22, show="*")
        self.password_entry.insert(0, self.password_arg)
        self.password_entry.pack(side=tk.LEFT)
        
        self.show_pwd_var = tk.BooleanVar(value=False)
        self.show_pwd_cb = tk.Checkbutton(
            self.password_frame, 
            text="👁", 
            variable=self.show_pwd_var, 
            command=self.toggle_password_visibility,
            bg="#1e1e2e", 
            fg="#cdd6f4",
            selectcolor="#313244",
            activebackground="#1e1e2e",
            activeforeground="#cdd6f4",
            bd=0, 
            highlightthickness=0
        )
        self.show_pwd_cb.pack(side=tk.LEFT, padx=(5, 0))

        # Archipelago Path
        tk.Label(self.conn_frame, text="AP Path:", bg="#1e1e2e", fg="#cdd6f4").grid(row=3, column=0, sticky="w", pady=2)
        self.ap_path_frame = tk.Frame(self.conn_frame, bg="#1e1e2e")
        self.ap_path_frame.grid(row=3, column=1, columnspan=2, sticky="we", padx=5, pady=2)
        
        self.ap_path_entry = ttk.Entry(self.ap_path_frame, width=22)
        self.ap_path_entry.insert(0, ap_dir_arg)
        self.ap_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.ap_path_btn = ttk.Button(self.ap_path_frame, text="...", width=3, command=self.browse_ap_dir)
        self.ap_path_btn.pack(side=tk.LEFT, padx=(5, 0))

        # State vars addition
        self.checks_list = []
        self.checks_window = None
        self.checks_listbox = None

        # Stats Area
        self.stats_frame = tk.LabelFrame(root, text=" Tracking Stats ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), bd=1, relief=tk.SOLID)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Large Labels
        self.lbl_slot_game = tk.Label(self.stats_frame, text="Not Connected", font=("Segoe UI", 12, "bold"), bg="#1e1e2e", fg="#cdd6f4")
        self.lbl_slot_game.pack(pady=10)

        self.lbl_checks = tk.Label(self.stats_frame, text="Checks: -- / -- checked", font=("Segoe UI", 11), bg="#1e1e2e", fg="#a6adc8")
        self.lbl_checks.pack(pady=5)

        self.lbl_accessible = tk.Label(self.stats_frame, text="Accessible (In Logic): --", font=("Segoe UI", 14, "bold"), bg="#1e1e2e", fg="#a6e3a1")
        self.lbl_accessible.pack(pady=5)

        self.show_checks_btn = ttk.Button(self.stats_frame, text="Show Checks", command=self.show_checks_window, state="disabled")
        self.show_checks_btn.pack(pady=(5, 10))

        # Slots Buttons Frame
        self.btn_frame_label = tk.Label(root, text="Switch Slot:", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 9, "bold"))
        self.btn_frame_label.pack(anchor="w", padx=15)
        
        # Scrollable buttons canvas (vertical)
        self.canvas_frame = tk.Frame(root, bg="#1e1e2e", height=130)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.canvas_frame.pack_propagate(False)
 
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1e1e2e", bd=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#1e1e2e")
 
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel for easy vertical scrolling (cross-platform)
        def _on_mousewheel(event):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            elif hasattr(event, "delta") and event.delta:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)
 
        # Start queue polling
        self.root.after(100, self.poll_queue)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if auto_connect:
            # Set initial UI states for connecting
            self.tracking_active = True
            self.connect_btn.configure(text="Connecting...", state="disabled")
            self.lbl_slot_game.configure(text="Initializing...")
            self.lbl_checks.configure(text="Please wait...")
            self.lbl_accessible.configure(text="Accessible (In Logic): --")
            self.start_tracker_subprocess(server=server_arg, slot=slot_arg, password=self.password_arg)
        else:
            # Pre-start idle subprocess to make initial connection instant
            self.start_tracker_subprocess()

    def start_tracker_subprocess(self, server=None, slot=None, password=None):
        python_exe = sys.executable or "python"
        if getattr(sys, 'frozen', False):
            # When frozen, spawn the executable itself with CLI arguments
            cmd = [python_exe, "--gui"]
        else:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_cli.py")
            cmd = [python_exe, script_path, "--gui"]

        ap_dir_val = self.ap_path_entry.get().strip() if hasattr(self, 'ap_path_entry') else None
        if ap_dir_val:
            cmd.extend(["--ap-dir", ap_dir_val])
        elif "--ap-dir" in sys.argv:
            try:
                cmd.extend(["--ap-dir", sys.argv[sys.argv.index("--ap-dir") + 1]])
            except IndexError:
                pass

        if server and slot:
            cmd.extend(["--server", server, "--slot", slot])
            if password:
                cmd.extend(["--password", password])
        else:
            cmd.append("--idle")
        
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,  # Print stderr logs straight to parent console
                text=True,
                bufsize=1,  # Line buffered
                startupinfo=startupinfo
            )
            # Start background reader thread
            t = threading.Thread(target=self.read_subprocess_stdout, daemon=True)
            t.start()
        except Exception as e:
            gui_queue.put(("ERROR", f"Failed to start tracker subprocess: {e}"))

    def read_subprocess_stdout(self):
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    event = data.get("event")
                    if event == "generating":
                        gui_queue.put(("GENERATING", None))
                    elif event == "connected":
                        gui_queue.put(("CONNECTED", data))
                    elif event == "stats":
                        gui_queue.put(("STATUS_UPDATE", data))
                    elif event == "error":
                        gui_queue.put(("ERROR", data.get("message")))
                    elif event == "disconnected":
                        gui_queue.put(("DISCONNECTED", None))
                except json.JSONDecodeError:
                    # Print non-JSON warnings and generation logs to the console
                    print(line, flush=True)
            self.proc.wait()
            gui_queue.put(("DISCONNECTED", None))
        except Exception as e:
            gui_queue.put(("ERROR", f"Subprocess reader error: {e}"))

    def toggle_connection(self):
        if self.tracking_active:
            self.stop_tracking()
        else:
            self.start_tracking()

    def start_tracking(self, specific_slot=None):
        server = self.server_entry.get().strip()
        slot = specific_slot if specific_slot else self.slot_entry.get().strip()
        
        if not server or not slot:
            messagebox.showerror("Error", "Server and Slot Name cannot be empty.")
            return

        if specific_slot:
            self.slot_entry.delete(0, tk.END)
            self.slot_entry.insert(0, specific_slot)

        self.connect_btn.configure(text="Connecting...", state="disabled")
        self.lbl_slot_game.configure(text="Initializing...")
        self.lbl_checks.configure(text="Please wait...")
        self.lbl_accessible.configure(text="Accessible (In Logic): --")

        self.tracking_active = True

        cmd_data = {
            "action": "connect",
            "server": server,
            "slot": slot,
            "password": self.password_entry.get().strip() or None,
            "game": self.slots.get(slot)
        }
        try:
            if not self.proc or self.proc.poll() is not None:
                self.start_tracker_subprocess()
            self.proc.stdin.write(json.dumps(cmd_data) + "\n")
            self.proc.stdin.flush()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send connection command: {e}")
            self.stop_tracking()

    def stop_tracking(self, silent=False):
        self.tracking_active = False
        if hasattr(self, 'show_checks_btn'):
            self.show_checks_btn.configure(state="disabled")
        self.checks_list = []
        if self.checks_window and self.checks_window.winfo_exists():
            self.checks_window.destroy()
        self.checks_window = None
        self.checks_listbox = None

        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(json.dumps({"action": "disconnect"}) + "\n")
                self.proc.stdin.flush()
            except Exception:
                pass
            
        if not silent:
            self.lbl_slot_game.configure(text="Not Connected")
            self.lbl_checks.configure(text="Checks: -- / -- checked")
            self.lbl_accessible.configure(text="Accessible (In Logic): --")
            self.connect_btn.configure(text="Connect", state="normal")
            # Clear buttons
            for child in self.scroll_frame.winfo_children():
                child.destroy()

    def toggle_password_visibility(self):
        if self.show_pwd_var.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def show_checks_window(self):
        if self.checks_window and self.checks_window.winfo_exists():
            self.checks_window.lift()
            self.checks_window.focus_force()
            return
            
        self.checks_window = tk.Toplevel(self.root)
        self.checks_window.title(f"Checks to do ({len(self.checks_list)})")
        self.checks_window.geometry("450x500")
        self.checks_window.configure(bg="#1e1e2e")
        self.checks_window.transient(self.root)
        
        # Search Frame
        search_frame = tk.Frame(self.checks_window, bg="#1e1e2e")
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(search_frame, text="Search:", bg="#1e1e2e", fg="#cdd6f4").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.populate_checks_listbox())
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.focus()
        
        frame = tk.Frame(self.checks_window, bg="#1e1e2e")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        
        self.checks_listbox = tk.Listbox(
            frame, 
            bg="#313244", 
            fg="#cdd6f4", 
            selectbackground="#45475a", 
            selectforeground="#cdd6f4",
            highlightthickness=0, 
            bd=0, 
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        
        scrollbar.config(command=self.checks_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.checks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.populate_checks_listbox()

    def populate_checks_listbox(self):
        if not self.checks_window or not self.checks_window.winfo_exists() or not self.checks_listbox:
            return
        query = self.search_var.get().lower().strip() if hasattr(self, 'search_var') else ""
        
        filtered_list = []
        for item in self.checks_list:
            if not query or query in item.lower():
                filtered_list.append(item)
                
        self.checks_window.title(f"Checks to do ({len(filtered_list)} / {len(self.checks_list)})")
        self.checks_listbox.delete(0, tk.END)
        if filtered_list:
            for item in sorted(filtered_list):
                self.checks_listbox.insert(tk.END, f"  •  {item}")
        else:
            if query:
                self.checks_listbox.insert(tk.END, "  No matching checks found.")
            else:
                self.checks_listbox.insert(tk.END, "  No accessible checks remaining.")

    def poll_queue(self):
        while not gui_queue.empty():
            evt, data = gui_queue.get()
            if evt == "GENERATING":
                print("[Tracker GUI] Generating logic...", flush=True)
                self.lbl_slot_game.configure(text="Generating logic...")
            elif evt == "CONNECTED":
                print(f"[Tracker GUI] Connected successfully! Slot: {data['slot']} | Game: {data['game']}", flush=True)
                self.connect_btn.configure(text="Disconnect", state="normal")
                self.lbl_slot_game.configure(text=f"Slot: {data['slot']} | Game: {data['game']}")
                # Render slots buttons
                self.slots = data["players"]
                for child in self.scroll_frame.winfo_children():
                    child.destroy()
                
                # Add slot switch buttons in 3 columns
                for i, sname in enumerate(sorted(self.slots.keys())):
                    row = i // 3
                    col = i % 3
                    btn = tk.Button(
                        self.scroll_frame, 
                        text=sname, 
                        bg="#313244", 
                        fg="#cdd6f4", 
                        activebackground="#45475a",
                        activeforeground="#cdd6f4",
                        relief=tk.FLAT,
                        padx=5,
                        pady=2,
                        width=12,
                        font=("Segoe UI", 9, "bold"),
                        command=lambda s=sname: self.start_tracking(s)
                    )
                    btn.grid(row=row, column=col, padx=4, pady=3, sticky="we")
            elif evt == "STATUS_UPDATE":
                print(f"[Tracker GUI] Update - Checks: {data['checked']}/{data['total']} | Accessible: {data['accessible']}", flush=True)
                self.lbl_slot_game.configure(text=f"Slot: {data['slot']} | Game: {data['game']}")
                self.lbl_checks.configure(text=f"Checks: {data['checked']} / {data['total']} checked")
                self.lbl_accessible.configure(text=f"Accessible (In Logic): {data['accessible']}")
                self.checks_list = data.get("checks_list", [])
                if hasattr(self, 'show_checks_btn'):
                    self.show_checks_btn.configure(state="normal")
                self.populate_checks_listbox()
            elif evt == "DISCONNECTED":
                print("[Tracker GUI] Disconnected.", flush=True)
                if self.tracking_active:
                    self.stop_tracking()
            elif evt == "ERROR":
                print(f"[Tracker GUI] Error: {data}", flush=True)
                messagebox.showerror("Tracker Error", data)
                self.stop_tracking()
        
        self.root.after(100, self.poll_queue)

    def browse_ap_dir(self):
        from tkinter import filedialog
        selected = filedialog.askdirectory(title="Select Archipelago Directory")
        if selected:
            for c in ['\u202a', '\u202b', '\u202c', '\u202d', '\u202e']:
                selected = selected.replace(c, '')
            selected = selected.strip().strip('"').strip("'").strip()
            self.ap_path_entry.delete(0, tk.END)
            self.ap_path_entry.insert(0, selected)

    def on_close(self):
        try:
            settings_path = get_settings_path()
            settings = {
                "server": self.server_entry.get().strip(),
                "slot": self.slot_entry.get().strip(),
                "password": self.password_entry.get().strip(),
                "ap_dir": self.ap_path_entry.get().strip()
            }
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"[Tracker GUI] Failed to save settings: {e}", flush=True)

        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(json.dumps({"action": "exit"}) + "\n")
                self.proc.stdin.flush()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                try:
                    self.proc.kill()
                except Exception:
                    pass
        self.root.destroy()

if __name__ == "__main__":
    import time
    t0 = time.time()
    is_cli_exe = "AP_Mini_Tracker_CLI" in os.path.basename(sys.argv[0])
    if is_cli_exe or any(arg in sys.argv for arg in ("--gui", "--cli", "--silent")):
        import asyncio
        import tracker_cli
        print(f"[Timer] Script imports and CLI initialization took: {time.time() - t0:.3f}s", flush=True)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            asyncio.run(tracker_cli.main())
        except KeyboardInterrupt:
            pass
        except Exception as e:
            import traceback
            try:
                if getattr(sys, 'frozen', False):
                    w_path = os.path.dirname(sys.executable)
                else:
                    w_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                with open(os.path.join(w_path, "tracker_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] FATAL EXCEPTION in CLI Subprocess: {e}\n{traceback.format_exc()}\n")
            except Exception:
                pass
            if "--silent" in sys.argv:
                try:
                    if getattr(sys, 'frozen', False):
                        w_path = os.path.dirname(sys.executable)
                    else:
                        w_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    with open(os.path.join(w_path, "tracker_error.log"), "a", encoding="utf-8") as f:
                        f.write(f"\n[Fatal Error in Main Loop] {e}\n")
                        traceback.print_exc(file=f)
                except Exception:
                    pass
            raise e
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
