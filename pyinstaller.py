import os
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).parent.absolute()


def install():
    PyInstaller.__main__.run(
        [
            str(ROOT / "src/main.py"),
            "--name",
            (
                "sbc-html-config_x86-64.exe"
                if os.name == "nt"
                else "sbc-html-config_x86-64"
            ),
            "--add-data=src/acme/assets:acme/assets",
            "--icon=NONE",
            "--onefile",
            "--windowed",
            "--collect-all",
            "customtkinter",
        ]
    )
