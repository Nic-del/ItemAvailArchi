import kivy
import pathlib
import os

p = pathlib.Path(kivy.__file__)
c = p.read_text(encoding='utf-8')

print(f"Target file: {p}")
print(f"Original start: {repr(c[:100])}")

patch_code = """import os
os.environ["KIVY_WINDOW"] = "dummy"
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "0"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_LOG_LEVEL"] = "debug"
os.environ["SDL_VIDEODRIVER"] = "dummy"
"""

# Normalize newlines for comparison
c_normalized = c.replace("\r\n", "\n")
if not c_normalized.startswith("import os\nos.environ[\"KIVY_WINDOW\"]"):
    p.write_text(patch_code + c, encoding='utf-8')
    print("Kivy patched successfully for headless build.")
    # Verify the write
    c_verify = p.read_text(encoding='utf-8')
    print(f"Patched start: {repr(c_verify[:250])}")
else:
    print("Kivy already patched.")
