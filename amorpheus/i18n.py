# -*- coding: utf-8 -*-
"""
Dwujezycznosc interfejsu (PL / EN).

Teksty w kodzie sa po polsku i przechodza przez tr(); w trybie angielskim tr() zwraca
tlumaczenie ze slownika amorpheus/lang_en.py (brak wpisu = tekst polski bez zmian).

Jezyk ustalany jest RAZ, przy imporcie tego modulu (przed zbudowaniem interfejsu), w kolejnosci:
  1. argument wiersza polecen  --lang pl|en  (albo --lang=en),
  2. zmienna srodowiskowa AMORPHEUS_LANG,
  3. zapisane ustawienie programu (QSettings: language),
  4. jezyk systemu: polski -> pl, kazdy inny -> en.
Zmiana jezyka w menu zapisuje ustawienie i dziala po ponownym uruchomieniu programu.
"""
from __future__ import annotations

import os
import sys

LANGUAGES = {"pl": "Polski", "en": "English"}
ORG, APP = "IMIM-PAN", "Amorpheus-Qt"


def _from_argv(argv):
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            return argv[i + 1].lower()
        if a.startswith("--lang="):
            return a.split("=", 1)[1].lower()
    return None


def _from_settings():
    try:
        from PyQt5 import QtCore
        v = QtCore.QSettings(ORG, APP).value("language")
        return str(v).lower() if v else None
    except Exception:
        return None


def _from_system():
    try:
        from PyQt5 import QtCore
        name = QtCore.QLocale.system().name()          # np. "pl_PL"
    except Exception:
        import locale
        name = (locale.getlocale()[0] or "")
    return "pl" if name.lower().startswith(("pl", "polish")) else "en"


def detect_language(argv=None):
    for cand in (_from_argv(argv if argv is not None else sys.argv),
                 os.environ.get("AMORPHEUS_LANG", "").lower() or None,
                 _from_settings()):
        if cand in LANGUAGES:
            return cand
    return _from_system()


LANG = detect_language()
_EN = None
MISSING = set()          # teksty bez tlumaczenia (diagnostyka, patrz tests/test_i18n.py)


def _table():
    global _EN
    if _EN is None:
        from .lang_en import EN
        _EN = EN
    return _EN


def tr(text: str) -> str:
    """Tlumaczenie tekstu interfejsu na biezacy jezyk."""
    if LANG == "pl" or not isinstance(text, str):
        return text
    out = _table().get(text)
    if out is None:
        MISSING.add(text)
        return text
    return out


def save_language(lang: str):
    """Zapisuje wybor jezyka (obowiazuje od nastepnego uruchomienia)."""
    from PyQt5 import QtCore
    QtCore.QSettings(ORG, APP).setValue("language", lang)


def strip_lang_args(argv):
    """argv bez --lang ... (zeby nie byl brany za plik danych)."""
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == "--lang":
            skip = True
            continue
        if a.startswith("--lang="):
            continue
        out.append(a)
    return out
