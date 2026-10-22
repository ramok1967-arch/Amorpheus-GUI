# -*- coding: utf-8 -*-
"""
Test dwujezycznosci interfejsu:
  1. kazdy tekst przekazany do tr() w kodzie ma tlumaczenie w amorpheus/lang_en.py,
  2. tlumaczenie ma te same pola {0}, {1:.3f}... co tekst polski,
  3. po uruchomieniu GUI po angielsku (bez wyswietlania okna) w zadnym widgecie, menu,
     podpowiedzi ani na wykresie nie zostal tekst po polsku.

Uruchomienie:  python tests/test_i18n.py
"""
import ast
import os
import re
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["AMORPHEUS_LANG"] = "en"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PL_CHARS = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
# polskie slowa bez znakow diakrytycznych, ktore moglyby przemknac
PL_WORDS = re.compile(r"\b(Dane|Plik|Zapisz|Wczytaj|Normalizuj|Normalizacja|Pomoc|Projekt|Parametry|Dziennik|"
                      r"Gotowy|Pokaz|Petla|Mapa|Licz|Uruchom|Dopasuj|Otworz|Zakres|Opcje|Iteracje|Folder wynikow|"
                      r"brak|oraz|tylko|dla|przez|jest|nie|lub|albo|wyniki|danych|pliku|od|do|krok|punkty|srodek)\b")
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


# --- 1 i 2: statycznie ----------------------------------------------------------------------------
from amorpheus.lang_en import EN  # noqa: E402

keys = set()
for f in sorted((ROOT / "amorpheus").rglob("*.py")):
    tree = ast.parse(f.read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "tr" and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                keys.add(a.value)
missing = sorted(k for k in keys if k not in EN)
for k in missing:
    check(False, f"brak tlumaczenia: {k!r}")
unused = sorted(k for k in EN if k not in keys)


def fields(s):
    return sorted((fn, spec) for _, fn, spec, _ in string.Formatter().parse(s) if fn is not None)


for k, v in EN.items():
    if k in keys:
        check(fields(k) == fields(v), f"rozne pola formatowania: {k!r} -> {v!r}")
        check(not PL_CHARS.search(v), f"polskie znaki w tlumaczeniu: {v!r}")
print(f"[1-2] teksty w kodzie: {len(keys)}, brakujace: {len(missing)}, nieuzywane wpisy slownika: {len(unused)} {unused[:5]}")

# --- 3: GUI po angielsku ----------------------------------------------------------------------------
from PyQt5 import QtWidgets  # noqa: E402

app = QtWidgets.QApplication(sys.argv)
from amorpheus import i18n  # noqa: E402
assert i18n.LANG == "en", i18n.LANG
from amorpheus.gui import main_window as mw  # noqa: E402

QtWidgets.QMessageBox.question = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.No)
w = mw.MainWindow()
w.resize(1400, 900)
w.show()
w.params.load_init(str(ROOT / "examples" / "Init.txt"))
app.processEvents()


def wait_worker(timeout=300):
    import time
    t0 = time.time()
    while time.time() - t0 < timeout:
        app.processEvents()
        time.sleep(0.03)
        if w.worker is None or not w.worker.isRunning():
            break
    for _ in range(20):
        app.processEvents()


# uruchom normalizacje, zeby powstaly wykresy i tabela
w.tabs.setCurrentWidget(w.t_norm)
w.t_norm.b_norm.click()
wait_worker()
w.tabs.setCurrentWidget(w.t_data)
w.t_data.btn.click()
app.processEvents()

texts = []


def add(where, t):
    if t:
        texts.append((where, str(t)))


for wid in w.findChildren(QtWidgets.QWidget):
    name = type(wid).__name__
    for attr in ("text", "title", "windowTitle", "toolTip", "placeholderText", "specialValueText"):
        fn = getattr(wid, attr, None)
        if callable(fn):
            try:
                add(f"{name}.{attr}", fn())
            except TypeError:
                pass
    if isinstance(wid, QtWidgets.QComboBox):
        for i in range(wid.count()):
            add(f"{name}.item", wid.itemText(i))
    if isinstance(wid, QtWidgets.QTabWidget):
        for i in range(wid.count()):
            add("tab", wid.tabText(i))
    if isinstance(wid, QtWidgets.QTableWidget):
        for i in range(wid.columnCount()):
            it = wid.horizontalHeaderItem(i)
            add("table.header", it.text() if it else "")
for act in w.findChildren(QtWidgets.QAction):
    add("action", act.text())
for menu in w.menuBar().findChildren(QtWidgets.QMenu):
    add("menu", menu.title())
add("log", w.logw.toPlainText())
# wykresy matplotlib
from matplotlib.figure import Figure  # noqa: E402
from amorpheus.gui.widgets import PlotWidget  # noqa: E402
for pw in w.findChildren(PlotWidget):
    for ax in pw.fig.axes:
        add("plot.title", ax.get_title())
        add("plot.xlabel", ax.get_xlabel())
        add("plot.ylabel", ax.get_ylabel())
        leg = ax.get_legend()
        if leg:
            for t in leg.get_texts():
                add("plot.legend", t.get_text())
        for t in ax.texts:
            add("plot.text", t.get_text())

# zawartosc HELP (README.md) i stalych ABOUT/CHANGES
add("ABOUT", mw.ABOUT)
add("CHANGES", mw.CHANGES)
bad = []
for where, t in texts:
    plain = re.sub(r"<[^>]+>", " ", t)
    plain = re.sub(r"(Init\.txt|Cerium|Background|examples|README)", " ", plain)
    if t == "Język / Language":
        continue  # celowo dwujezyczne
    if PL_CHARS.search(plain) or PL_WORDS.search(plain):
        bad.append((where, t))
seen = set()
for where, t in bad:
    if t in seen:
        continue
    seen.add(t)
    check(False, f"tekst po polsku w GUI ({where}): {t[:150]!r}")
check(not i18n.MISSING, f"tr() bez tlumaczenia w czasie dzialania: {sorted(i18n.MISSING)[:10]}")
print(f"[3] sprawdzone teksty GUI: {len(texts)}, po polsku: {len(seen)}")

w.close()
if failures:
    print("\nBLEDY:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("\nOK – interfejs angielski kompletny.")
