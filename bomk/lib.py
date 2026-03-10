"""
bomk/lib.py – shared utility classes and helpers.
"""

import re
import sys
import base64
import mimetypes
from pathlib import Path

# ── Shebang regex ─────────────────────────────────────────────────────────────
# Matches:  basename_$<N>.ext
SHEBANG_RE = re.compile(r'^(.+)_\$(\d+)(\.[^.]+)$')


# ── Logger ────────────────────────────────────────────────────────────────────

class Logger:
    SILENT  = 0
    NORMAL  = 1
    VERBOSE = 2

    _GREEN = "\033[92m"
    _RED   = "\033[91m"
    _CYAN  = "\033[96m"
    _YELLOW = "\033[93m"
    _BLUE  = "\033[94m"
    _MAGENTA = "\033[95m"
    _WHITE = "\033[97m"
    _DIM   = "\033[2m"
    _BOLD  = "\033[1m"
    _RESET = "\033[0m"

    def __init__(self, level: int = NORMAL):
        self.level = level
        if not sys.stdout.isatty():
            self._GREEN = self._RED = self._CYAN = self._YELLOW = self._BLUE = ""
            self._MAGENTA = self._WHITE = self._DIM = self._BOLD = self._RESET = ""

    def info(self, msg: str) -> None:
        if self.level >= self.NORMAL:
            print(f"{self._CYAN}[bomk]{self._RESET} {msg}")

    def verbose(self, msg: str) -> None:
        if self.level >= self.VERBOSE:
            print(f"{self._DIM}[bomk:verbose]{self._RESET} {msg}")

    def success(self, msg: str) -> None:
        if self.level >= self.NORMAL:
            print(f"{self._GREEN}[bomk:ok]{self._RESET} {msg}")

    def error(self, msg: str) -> None:
        print(f"{self._RED}[bomk:error]{self._RESET} {msg}", file=sys.stderr)

    def step(self, msg: str) -> None:
        """Print a step/action message in bold."""
        if self.level >= self.NORMAL:
            print(f"{self._BOLD}{self._BLUE}[bomk]{self._RESET} {self._BOLD}{msg}{self._RESET}")

    def highlight(self, msg: str) -> None:
        """Print a highlighted message."""
        if self.level >= self.NORMAL:
            print(f"{self._BOLD}{self._YELLOW}[bomk]{self._RESET} {self._BOLD}{msg}{self._RESET}")

    def debug(self, msg: str) -> None:
        """Print a debug message."""
        if self.level >= self.VERBOSE:
            print(f"{self._MAGENTA}[bomk:debug]{self._RESET} {msg}")


# ── File group helpers ────────────────────────────────────────────────────────

def strip_shebang(path: Path) -> str:
    """Return the clean filename without the _$N tag."""
    m = SHEBANG_RE.match(path.name)
    return (m.group(1) + m.group(3)) if m else path.name


def parse_groups(folder: str) -> dict[int, list[Path]]:
    """
    Scan a folder and return {group_number: [Path, ...]} for every
    shebang-tagged file.  Raises ValueError on duplicate shebangs for
    the same group+extension combination.
    """
    groups: dict[int, list[Path]] = {}
    seen: dict[tuple[int, str], Path] = {}   # (group, ext) → first file seen

    for f in Path(folder).iterdir():
        if not f.is_file():
            continue
        m = SHEBANG_RE.match(f.name)
        if not m:
            continue

        n   = int(m.group(2))
        ext = m.group(3).lower()
        key = (n, ext)

        if key in seen:
            raise ValueError(
                f"Duplicate shebang: both '{seen[key].name}' and '{f.name}' "
                f"are tagged _${n} with extension '{ext}'."
            )
        seen[key] = f
        groups.setdefault(n, []).append(f)

    return groups


def validate_groups(groups: dict[int, list[Path]]) -> None:
    """
    Raise ValueError if:
      - no groups were found
      - group $1 (the prime shebang) is missing
      - any group has no HTML file
    """
    if not groups:
        raise ValueError(
            "No shebang-tagged files found.\n"
            "  Rename your files like:  index_$1.html  styles_$1.css  script_$1.js"
        )
    if 1 not in groups:
        raise ValueError(
            "No $1 group found.  The entry-point must be tagged _$1 "
            "(e.g. index_$1.html)."
        )
    for n, files in groups.items():
        html = [f for f in files if f.suffix.lower() == ".html"]
        if not html:
            raise ValueError(f"Group ${n} has no HTML file.")
        if len(html) > 1:
            raise ValueError(
                f"Group ${n} has more than one HTML file: "
                + ", ".join(f.name for f in html)
            )


# ── Asset encoding ────────────────────────────────────────────────────────────

def b64_data_uri(path: Path) -> str | None:
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        return None
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"