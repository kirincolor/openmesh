# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "openmesh.desktop",
    "openmesh.server",
    "openmesh.cli",
    "multipart",
]

for pkg in (
    "openmesh",
    "uvicorn",
    "fastapi",
    "starlette",
    "anyio",
    "pydantic",
    "yaml",
    "dotenv",
    "httpx",
    "platformdirs",
):
    try:
        extra_d, extra_b, extra_h = collect_all(pkg)
    except Exception:
        continue
    datas += extra_d
    binaries += extra_b
    hiddenimports += extra_h

try:
    extra_d, extra_b, extra_h = collect_all("webview")
    datas += extra_d
    binaries += extra_b
    hiddenimports += extra_h
except Exception:
    pass

a = Analysis(
    ["src/openmesh/__main__.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OpenMesh",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="OpenMesh",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="OpenMesh.app",
        icon=None,
        bundle_identifier="app.openmesh.desktop",
        info_plist={"NSHighResolutionCapable": True},
    )
