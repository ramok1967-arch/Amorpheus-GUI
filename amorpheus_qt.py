# -*- coding: utf-8 -*-
"""Uruchomienie: python amorpheus_qt.py [Init.txt]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amorpheus.gui.main_window import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
