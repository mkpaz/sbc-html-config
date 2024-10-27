import sys
import webbrowser
from pathlib import Path
from tkinter import filedialog
from typing import Any

import acme.renderer as renderer
import customtkinter as ctk
import env
from acme.parser import to_json


def _process_file(source_file: Path, open_file: ctk.StringVar | None = None):
    if not source_file.is_file():
        print(f"File doesn't exist or not readable: {source_file}")
        return

    json_cfg: dict[str, Any] = {}
    with open(source_file, "r") as f:
        json_cfg = to_json(f.read())

    if not json_cfg:
        print(f"Unable to parse config file: {source_file}")
        return

    dest_file: Path = source_file.parent / (source_file.stem + ".html")
    html = renderer.render(json_cfg, dest_file.name)

    # import json
    # _write_file(source_file.parent / (source_file.stem + ".json"), json.dumps(json_cfg, indent=4))

    _write_file(dest_file, html)

    if open_file and open_file.get() == "on":
        webbrowser.open(str(dest_file))


def _write_file(file: Path, content: str) -> None:
    with open(file, "w") as f:
        f.write(content)


class Window:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(f"{env.PROJECT_NAME} v{env.VERSION}")
        self.root.geometry("450x250")
        self.root.resizable(False, False)

        self.last_directory: Path = Path.home()

        frame = ctk.CTkFrame(master=self.root, fg_color=self.root.cget("bg"))
        frame.pack(expand=True)

        label = ctk.CTkLabel(master=frame, text="Select SBC config file:")
        label.pack(pady=(0, 10))

        button = ctk.CTkButton(master=frame, text="Browse", command=self._on_click)
        button.pack(pady=(0, 10))

        self.open_file = ctk.StringVar(value="on")
        checkbox = ctk.CTkCheckBox(
            master=frame,
            text="auto-open HTML",
            variable=self.open_file,
            onvalue="on",
            offvalue="off",
        )
        checkbox.pack()

    def show(self):
        self.root.mainloop()

    def _on_click(self):
        initial_dir: str = (
            str(self.last_directory)
            if self.last_directory
            else filedialog.askdirectory()
        )

        file = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[
                ("Text files", "*.txt *.log"),
                ("All files", "*.*"),
            ],
        )

        if file:
            file_path: Path = Path(file)
            self.last_directory = file_path.parent
            _process_file(file_path, self.open_file)


###############################################################################

if __name__ == "__main__":
    # gui mode
    if len(sys.argv) == 1:
        win = Window()
        win.show()

    # cli mode
    if len(sys.argv) == 2:
        _process_file(Path(sys.argv[1]))
