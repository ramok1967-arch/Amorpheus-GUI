# -*- coding: utf-8 -*-
"""Dane przykladowe (szklo Ce) z oryginalnego repozytorium Amorpheus - pobierane przy pierwszym uzyciu."""
from __future__ import annotations

import urllib.request
from pathlib import Path
from .i18n import tr  # noqa: E402

RAW = "https://raw.githubusercontent.com/CelluleProjet/Amorpheus/main/Amorpheus/"
FILES = ["Cerium.dat", "background.xy"]
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def ensure_examples(folder: Path = EXAMPLES, log=print) -> Path:
    """Pobiera brakujace pliki danych przykladowych. Zwraca folder."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = folder / name
        if target.exists() and target.stat().st_size > 1000:
            continue
        url = RAW + name
        log(tr('Pobieranie danych przykładowych: {0}').format(url))
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
        except Exception as e:
            raise RuntimeError(
                tr('Nie udało się pobrać {0}\n({1})\n\nPobierz ręcznie pliki {2} z https://github.com/CelluleProjet/Amorpheus/tree/main/Amorpheus do folderu {3}').format(url, e, ', '.join(FILES), folder)) from e
        target.write_bytes(data)
    return folder
