import sys
import os

# Disable Kivy window provider initialization during PyInstaller build execution on headless runners
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_WINDOW"] = "dummy"

import kivy

# Determine Archipelago source path dynamically
ap_path = os.environ.get('ARCHIPELAGO_PATH')
if not ap_path:
    default_ap = 'C:\\Users\\Linksweld\\Downloads\\Archipelago-main\\Archipelago-main'
    if os.path.exists(default_ap):
        ap_path = default_ap
    else:
        ap_path = os.path.abspath('./Archipelago-main')

sys.path.insert(0, ap_path)

# Dynamically locate Kivy data directory
kivy_data_dir = os.path.join(os.path.dirname(kivy.__file__), 'data')

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

def collect_submodules_no_import(package_name):
    import importlib.util
    import os
    spec = importlib.util.find_spec(package_name)
    if not spec or not spec.submodule_search_locations:
        return []
    package_path = spec.submodule_search_locations[0]
    submodules = []
    for root, dirs, files in os.walk(package_path):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                rel_path = os.path.relpath(os.path.join(root, file[:-3]), package_path)
                mod_name = package_name + '.' + rel_path.replace(os.sep, '.')
                submodules.append(mod_name)
        for d in dirs:
            if os.path.exists(os.path.join(root, d, '__init__.py')):
                rel_path = os.path.relpath(os.path.join(root, d), package_path)
                mod_name = package_name + '.' + rel_path.replace(os.sep, '.')
                submodules.append(mod_name)
    return submodules

a = Analysis(
    ['tracker/tracker_gui.py'],
    pathex=[ap_path, os.path.abspath('.')],
    binaries=[],
    datas=[
        ('tracker/tracker', 'tracker/tracker'),
        (kivy_data_dir, 'data'),
        (os.path.join(ap_path, 'data'), 'data'),
        (os.path.join(ap_path, 'worlds'), 'worlds')
    ] + collect_data_files('kivymd'),
    hiddenimports=collect_submodules_no_import('kivymd') + collect_submodules('worlds') + collect_submodules('pathspec') + collect_submodules('websockets') + collect_submodules('tracker') + ['tracker_cli', 'bsdiff4', 'bsdiff4.core', 'orjson', 'jinja2', 'requests', 'schema'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygments'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='AP_Mini_Tracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

exe_cli = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='AP_Mini_Tracker_CLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    exe_cli,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AP_Mini_Tracker',
)

