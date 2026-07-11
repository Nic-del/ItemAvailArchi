import kivy
import pathlib
import os

# 1. Patch kivy/metrics.py to prevent get_dpi() from crashing when headless
metrics_path = pathlib.Path(kivy.__file__).parent / 'metrics.py'
if metrics_path.exists():
    c = metrics_path.read_text(encoding='utf-8')
    target_code = "            from kivy.base import EventLoop\n            EventLoop.ensure_window()\n            value = EventLoop.window.dpi"
    # Also handle CRLF
    target_code_crlf = target_code.replace("\n", "\r\n")
    
    replacement_code = """            try:
                from kivy.base import EventLoop
                if EventLoop.window:
                    value = EventLoop.window.dpi
                else:
                    value = 96.0
            except:
                value = 96.0"""

    if target_code in c:
        metrics_path.write_text(c.replace(target_code, replacement_code), encoding='utf-8')
        print("kivy/metrics.py patched successfully.")
    elif target_code_crlf in c:
        metrics_path.write_text(c.replace(target_code_crlf, replacement_code), encoding='utf-8')
        print("kivy/metrics.py (CRLF) patched successfully.")
    elif "value = 96.0" in c:
        print("kivy/metrics.py already patched.")
    else:
        print("Warning: Could not find target get_dpi code in kivy/metrics.py")
else:
    print("Warning: kivy/metrics.py not found.")

# 2. Patch kivy/__init__.py for environment variables
p = pathlib.Path(kivy.__file__)
c = p.read_text(encoding='utf-8')
patch_code = """import os
os.environ["KIVY_WINDOW"] = "dummy"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "0"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_LOG_LEVEL"] = "debug"
os.environ["SDL_VIDEODRIVER"] = "dummy"
"""

c_normalized = c.replace("\r\n", "\n")
if not c_normalized.startswith("import os\nos.environ[\"KIVY_WINDOW\"]"):
    p.write_text(patch_code + c, encoding='utf-8')
    print("kivy/__init__.py patched successfully.")
else:
    print("kivy/__init__.py already patched.")
