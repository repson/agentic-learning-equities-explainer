from __future__ import annotations

import re
import subprocess
import unicodedata
from pathlib import Path


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


PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bGuia\b", "Guide"),
    (r"\bguia\b", "guide"),
    (r"\bGuias\b", "Guides"),
    (r"\bguias\b", "guides"),
    (r"\bProyecto\b", "Project"),
    (r"\bproyecto\b", "project"),
    (r"\bProduccion\b", "Production"),
    (r"\bproduccion\b", "production"),
    (r"\bSemana\b", "Week"),
    (r"\bsemana\b", "week"),
    (r"\bSemanas\b", "Weeks"),
    (r"\bsemanas\b", "weeks"),
    (r"\bDia\b", "Day"),
    (r"\bdia\b", "day"),
    (r"\bDias\b", "Days"),
    (r"\bdias\b", "days"),
    (r"\bPermisos\b", "Permissions"),
    (r"\bpermisos\b", "permissions"),
    (r"\bBase de Datos\b", "Database"),
    (r"\bbase de datos\b", "database"),
    (r"\bPortafolio\b", "Portfolio"),
    (r"\bportafolio\b", "portfolio"),
    (r"\bJubilacion\b", "Retirement"),
    (r"\bjubilacion\b", "retirement"),
    (r"\banalisis\b", "analysis"),
    (r"\bAnalisis\b", "Analysis"),
    (r"\bresumen\b", "summary"),
    (r"\bResumen\b", "Summary"),
    (r"\bconfiguracion\b", "configuration"),
    (r"\bConfiguracion\b", "Configuration"),
    (r"\bdespliegue\b", "deployment"),
    (r"\bDespliegue\b", "Deployment"),
    (r"\bprueba\b", "test"),
    (r"\bPrueba\b", "Test"),
    (r"\bpruebas\b", "tests"),
    (r"\bPruebas\b", "Tests"),
    (r"\bfuncion\b", "function"),
    (r"\bFuncion\b", "Function"),
    (r"\bfunciones\b", "functions"),
    (r"\bFunciones\b", "Functions"),
    (r"\busuario\b", "user"),
    (r"\bUsuario\b", "User"),
    (r"\busuarios\b", "users"),
    (r"\bUsuarios\b", "Users"),
    (r"\bcuenta\b", "account"),
    (r"\bCuenta\b", "Account"),
    (r"\bcuentas\b", "accounts"),
    (r"\bCuentas\b", "Accounts"),
    (r"\bdatos de prueba\b", "test data"),
    (r"\bDatos de prueba\b", "Test data"),
    (r"\bNo se pudo\b", "Could not"),
    (r"\bNo se pueden\b", "Cannot"),
    (r"\bNo se encontraron\b", "No ... found"),
    (r"\bError al\b", "Error while"),
    (r"\berror al\b", "error while"),
    (r"\bNo encontrado\b", "Not found"),
    (r"\bno encontrado\b", "not found"),
]


WORD_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bel\b", "the"),
    (r"\bla\b", "the"),
    (r"\blos\b", "the"),
    (r"\blas\b", "the"),
    (r"\bpara\b", "for"),
    (r"\bcon\b", "with"),
    (r"\bsin\b", "without"),
    (r"\bque\b", "that"),
    (r"\bde\b", "of"),
    (r"\bdel\b", "of the"),
    (r"\bpor\b", "by"),
    (r"\ben\b", "in"),
    (r"\by\b", "and"),
    (r"\bo\b", "or"),
    (r"\bsi\b", "if"),
    (r"\bmas\b", "more"),
    (r"\bmenos\b", "less"),
    (r"\bcomo\b", "as"),
    (r"\best\b", "is"),
    (r"\besto\b", "this"),
    (r"\besta\b", "this"),
    (r"\bestan\b", "are"),
    (r"\bestas\b", "these"),
    (r"\beste\b", "this"),
    (r"\bestos\b", "these"),
    (r"\baqui\b", "here"),
    (r"\bahi\b", "there"),
    (r"\basi\b", "thus"),
    (r"\bdesde\b", "from"),
    (r"\bhasta\b", "until"),
    (r"\bantes\b", "before"),
    (r"\bdespues\b", "after"),
    (r"\bcuando\b", "when"),
    (r"\bdonde\b", "where"),
    (r"\bporque\b", "because"),
    (r"\bse\b", ""),
    (r"\buna\b", "a"),
    (r"\bun\b", "a"),
    (r"\buno\b", "one"),
    (r"\bdos\b", "two"),
    (r"\btres\b", "three"),
    (r"\bcuatro\b", "four"),
    (r"\bcinco\b", "five"),
    (r"\bjubilacion\b", "retirement"),
    (r"\bportafolio\b", "portfolio"),
]


def normalize_ascii(text: str) -> str:
    text = (
        text.replace("¿", "")
        .replace("¡", "")
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("`", "`")
    )
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def process_text(text: str) -> str:
    out = normalize_ascii(text)
    for pattern, replacement in PHRASE_REPLACEMENTS:
        out = re.sub(pattern, replacement, out)
    for pattern, replacement in WORD_REPLACEMENTS:
        out = re.sub(pattern, replacement, out)

    out = re.sub(r"\b\s+", " ", out)
    out = re.sub(r" +\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out


def should_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if any(part == ".git" for part in path.parts):
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def main() -> None:
    changed = 0
    for rel in tracked_files():
        if should_skip(rel):
            continue
        path = Path.cwd() / rel
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        updated = process_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    print(f"Updated files: {changed}")


if __name__ == "__main__":
    main()
