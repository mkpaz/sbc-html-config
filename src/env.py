from pathlib import Path
import sys

PROJECT_NAME: str = "SBC HTML Config"
VERSION: str = "1.0.0"

BUNDLED: bool = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
ROOT_DIR: Path = (
    Path(sys._MEIPASS) if BUNDLED else Path(__file__).parent.absolute()  # type: ignore
)
