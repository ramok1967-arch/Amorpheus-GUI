# -*- coding: utf-8 -*-
"""Uruchomienie: python amorpheus_qt.py [plik_danych | Init.txt] [--lang pl|en]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amorpheus.gui.main_window import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
