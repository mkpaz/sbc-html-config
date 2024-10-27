from pathlib import Path

import main

PROTECTED = Path(__file__).parent.absolute().parent / "protected"


def test():
    main._process_file(PROTECTED / "example.log")
