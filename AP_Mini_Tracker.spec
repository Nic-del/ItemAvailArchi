import sys
import os
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

a = Analysis(
    ['tracker\\tracker_gui.py'],
    pathex=[ap_path],
    binaries=[],
    datas=[
        ('tracker/tracker', 'tracker/tracker'),
        (kivy_data_dir, 'data'),
        (os.path.join(ap_path, 'data'), 'data'),
        (os.path.join(ap_path, 'worlds'), 'worlds')
    ] + collect_data_files('kivymd'),
    hiddenimports=collect_submodules('kivymd') + collect_submodules('worlds') + ['bsdiff4', 'bsdiff4.core', 'orjson', 'jinja2', 'requests'],
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

