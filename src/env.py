from pathlib import Path
import sys

PROJECT_NAME: str = "SBC HTML Config"
VERSION: str = "1.0.1"

BUNDLED: bool = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

MEIPASS_DIR: Path = (
    Path(sys._MEIPASS) if BUNDLED else Path(__file__).parent.absolute()  # type: ignore
)

CONFIG_DIR: Path = (
    Path(sys.executable) if getattr(sys, "frozen", False) else Path(__file__)
).parent.absolute()

CONFIG_PATH: Path = CONFIG_DIR / "cfg.ini"


def get_config() -> dict[str, str]:
    print(CONFIG_PATH)

    if not CONFIG_PATH.is_file():
        # default config
        return {"top-level-items": ""}

    return dict(
        line.strip().split("=")
        for line in open(CONFIG_PATH)
        if not line.startswith("#")
    )
