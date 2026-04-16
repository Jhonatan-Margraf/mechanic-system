# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

datas = []
binaries = []
hiddenimports = ['google.auth', 'google.auth.oauthlib', 'google.auth.transport.requests',
                 'googleapiclient.discovery', 'googleapiclient.http']

tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('google')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('googleapiclient')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

script_dir = os.path.dirname(os.path.abspath('app.py'))
if os.path.exists(os.path.join(script_dir, 'credentials.json')):
    datas.append((os.path.join(script_dir, 'credentials.json'), '.'))
if os.path.exists(os.path.join(script_dir, 'token.json')):
    datas.append((os.path.join(script_dir, 'token.json'), '.'))

a = Analysis(
    ['app.py'],          # novo entry point
    pathex=['.'],        # garante que src/ é encontrado
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
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
    name='app_mecanica',
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
