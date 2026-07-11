import sys
import os
sys.path.insert(0, 'C:\\Users\\Linksweld\\Downloads\\Archipelago-main\\Archipelago-main')
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./tracker'))
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

a = Analysis(
    ['tracker\\tracker_cli.py'],
    pathex=['C:\\Users\\Linksweld\\Downloads\\Archipelago-main\\Archipelago-main', os.path.abspath('.')],
    binaries=[],
    datas=[
        ('tracker/tracker', 'tracker'),
        ('C:\\Users\\Linksweld\\Downloads\\Archipelago-main\\Archipelago-main\\data', 'data'),
        ('C:\\Users\\Linksweld\\Downloads\\Archipelago-main\\Archipelago-main\\worlds', 'worlds')
    ],
    hiddenimports=collect_submodules('worlds') + ['tracker', 'tracker.TrackerClient', 'tracker.TrackerCore', 'tracker.TrackerKivy', 'bsdiff4', 'bsdiff4.core', 'orjson', 'jinja2', 'requests', 'schema', 'colorama'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pygments', 'kivy', 'kivymd', 'kvui', 'tkinter', 'tcl', 'matplotlib', 'pil', 'Pillow'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AP_CLI_Tracker',
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
