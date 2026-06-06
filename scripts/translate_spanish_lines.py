from __future__ import annotations

import re
import subprocess
import argparse
from pathlib import Path

from deep_translator import GoogleTranslator


SPANISH_RE = re.compile(r"[\u00C0-\u017F]|\b(el|la|los|las|para|con|sin|que|de|del|por|jubilacion|portafolio)\b", re.IGNORECASE)

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".zip",
    ".pdf",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".lock",
}

SKIP_NAMES = {
    "uv.lock",
    "package-lock.json",
    ".terraform.lock.hcl",
}


def tracked_files(root_filter: str | None = None) -> list[Path]:
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    files = [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
    if not root_filter:
        return files
    root = Path(root_filter)
    return [p for p in files if p == root or root in p.parents]


def should_skip(path: Path) -> bool:
    return path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES


def translate_line(translator: GoogleTranslator, line: str, cache: dict[str, str]) -> str:
    if line in cache:
        return cache[line]

    leading = re.match(r"^\s*", line).group(0)
    body = line[len(leading):].rstrip("\n")

    if not body.strip():
        return line

    translated = translator.translate(body)
    if translated is None:
        translated = body

    out = f"{leading}{translated}\n"
    cache[line] = out
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate Spanish lines to English in tracked files")
    parser.add_argument("--path", help="Optional repository-relative path filter", default=None)
    args = parser.parse_args()

    translator = GoogleTranslator(source="es", target="en")
    cache: dict[str, str] = {}
    changed_files = 0
    changed_paths: list[str] = []

    for rel_path in tracked_files(args.path):
        if should_skip(rel_path):
            continue

        abs_path = Path.cwd() / rel_path
        try:
            original = abs_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        updated_lines: list[str] = []
        changed = False

        for line in original.splitlines(keepends=True):
            if SPANISH_RE.search(line):
                new_line = translate_line(translator, line, cache)
                if new_line != line:
                    changed = True
                updated_lines.append(new_line)
            else:
                updated_lines.append(line)

        if changed:
            abs_path.write_text("".join(updated_lines), encoding="utf-8")
            changed_files += 1
            changed_paths.append(str(rel_path))

    print(f"Translated files: {changed_files}")
    for path in changed_paths:
        print(path)


if __name__ == "__main__":
    main()
