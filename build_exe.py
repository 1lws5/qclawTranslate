# -*- coding: utf-8 -*-
"""打包 qclawTranslate exe"""
import subprocess, sys, os

spec = os.path.join(r"D:\qclawTranslate", "qclawTranslate.spec")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--clean", "--noconfirm",
    "--onefile", "--windowed",
    "--name", "qclawTranslate",
    "--add-data", f"config.py{os.pathsep}.",
    "--hidden-import", "comtypes",
    "--hidden-import", "comtypes.gen",
    "--hidden-import", "comtypes.gen.UIAutomationClient",
    "--hidden-import", "win32clipboard",
    "--hidden-import", "win32con",
    "--hidden-import", "ctypes.wintypes",
    "--icon", "NONE",
    "--distpath", os.path.join(os.path.dirname(os.path.dirname(sys.executable)), ".."),
    "--workpath", r"D:\qclawTranslate\build",
    r"D:\qclawTranslate\main.py"
]
print(" ".join(cmd))
subprocess.run(cmd, cwd=r"D:\qclawTranslate")
