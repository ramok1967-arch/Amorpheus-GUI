# -*- coding: utf-8 -*-
"""Glowne okno Amorpheus-Qt."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from .. import __version__
from .widgets import ParamsPanel, Worker
from .tabs import DataTab, NormTab, LoopTab, Chi2Tab, BatchTab, RPSTab
from .opendata import OpenDataDialog, DATA_FILTER
from .. import autodetect as ad
from ..i18n import tr, LANG, LANGUAGES, save_language, strip_lang_args  # noqa: E402

# sciezka skryptu startowego zapamietana przy imporcie (do ponownego uruchomienia po zmianie jezyka)
_SCRIPT = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""

STYLE = """
QWidget { font-size: 9.5pt; }
QMainWindow { background: #f4f6f9; }
QGroupBox { font-weight: 600; border: 1px solid #d5dbe3; border-radius: 6px; margin-top: 10px;
            padding: 8px 6px 6px 6px; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #1f4e79; }
QPushButton { padding: 5px 12px; border: 1px solid #b8c2cf; border-radius: 5px; background: #ffffff; }
QPushButton:hover { background: #eaf1fb; border-color: #1f4e79; }
QPushButton:disabled { color: #9aa4b0; background: #f0f2f5; }
QPushButton#primary { background: #1f4e79; color: white; border: 1px solid #1f4e79; font-weight: 600; }
QPushButton#primary:hover { background: #2a64a0; }
QPushButton#primary:disabled { background: #8aa3bd; border-color: #8aa3bd; }
QPushButton#stop { background: #c62828; color: white; border: 1px solid #c62828; font-weight: 600; }
QPushButton#stop:disabled { background: #e5a3a3; border-color: #e5a3a3; }
QTabWidget::pane { border: 1px solid #d5dbe3; border-radius: 6px; background: #ffffff; top: -1px; }
QTabBar::tab { padding: 7px 16px; border: 1px solid #d5dbe3; border-bottom: none; background: #e9edf2;
               border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:selected { background: #ffffff; color: #1f4e79; font-weight: 600; }
QLabel#hint { color: #5b6773; font-size: 8.5pt; }
QLabel#result { background: #eef6ee; border: 1px solid #b9dcbb; border-radius: 5px; padding: 6px; }
QPlainTextEdit#log { background: #1e2329; color: #d8dee9; font-family: Consolas, "DejaVu Sans Mono", monospace;
                     font-size: 9pt; border-radius: 4px; }
QTableWidget { gridline-color: #e3e7ec; alternate-background-color: #f7f9fb; }
QHeaderView::section { background: #eef1f5; padding: 4px; border: none; border-right: 1px solid #d5dbe3;
                       font-weight: 600; }
QProgressBar { border: 1px solid #b8c2cf; border-radius: 4px; text-align: center; height: 16px; }
QProgressBar::chunk { background: #2e7d32; border-radius: 3px; }
"""

ABOUT = tr("""<h3>Amorpheus-Qt {0}</h3>
<p>Przepisana wersja programu <b>Amorpheus</b> do analizy rozpraszania promieniowania X
przez materiały amorficzne i ciecze: normalizacja, S(q), F(r), g(r), dopasowanie gęstości
i współczynnika tła metodą Kaplowa/Eggerta, pętle po r<sub>min</sub> i q<sub>max</sub>, mapa χ²,
tryb wsadowy oraz narzędzie RPS (usuwanie pików, wygładzanie).</p>
<p><b>Oryginał:</b> S. Boccato i in. (2020–2022),
<a href="https://github.com/CelluleProjet/Amorpheus">github.com/CelluleProjet/Amorpheus</a><br>
<b>Cytowanie:</b> Boccato i in., High Pressure Research (2022),
<a href="https://doi.org/10.1080/08957959.2022.2032032">doi:10.1080/08957959.2022.2032032</a></p>
<p>Licencja: GNU GPL v3 (jak oryginał).</p>""").format(__version__)

CHANGES = tr("""<h3>Zmiany względem oryginału v1.0.5</h3>
<ul>
<li><b>Wyniki</b>: przy wyłączonej „poprawce jednostek” identyczne z oryginałem (test w <i>tests/</i>,
różnice rzędu 1e-14).</li>
<li><b>Poprawka jednostek w normalizacji</b> (domyślnie włączona): w oryginale człon −2π²ρ w regule
sum był 10× za mały (całka po dq w nm⁻¹ przy Q² w Å⁻²). Wpływ na ρ znikomy, bkfactor zmienia się
w trzecim miejscu po przecinku.</li>
<li>Wczytywanie plików: nie gubi wierszy z liczbami ujemnymi lub zaczynającymi się od kropki;
akceptuje przecinek dziesiętny, średnik, tab, przecinek jako separator kolumn; sortuje dane.</li>
<li>Dopasowania ok. 4–5× szybsze (macierz sin(qr) liczona raz, tylko dla r &lt; r<sub>min</sub>).</li>
<li>Funkcja modyfikująca: brak NaN w punkcie r = a.</li>
<li>Działa z aktualnymi NumPy 2.x / SciPy (oryginał używał usuniętych np.trapz / scipy.integrate.trapz).</li>
<li>Batch bez ezodf (pandas + odfpy); obsługuje też .xlsx i .csv; błąd w jednym wierszu nie przerywa całości.</li>
<li>Brak exec/eval na zawartości Init.txt; Init.txt zgodny w obie strony (dodatkowe opcje w osobnej sekcji).</li>
<li><b>Otwieranie danych</b> (Ctrl+O): parametry odczytywane z pliku (jednostka, λ, zakres, skład z nazwy),
projekt &lt;dane&gt;_Init.txt tworzony i zapisywany automatycznie obok danych; obsługa Q w nm⁻¹.</li>
<li>Poprawione drobne błędy: nagłówek pliku pętli q<sub>max</sub>, nazwy plików, wykres ρ(q<sub>max</sub>)
zapisywany pod złym prefiksem, Erase w RPS gubiący ostatni punkt.</li>
</ul>""")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('Amorpheus-Qt {0}').format(__version__))
        self.worker = None
        self.settings = QtCore.QSettings("IMIM-PAN", "Amorpheus-Qt")

        self.params = ParamsPanel()
        self.params.log.connect(self.log)
        self.params.open_data_requested.connect(self.open_data)
        self.setAcceptDrops(True)
        dock = QtWidgets.QDockWidget(tr("Parametry"), self)
        dock.setObjectName("params")
        dock.setWidget(self.params)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        self.tabs = QtWidgets.QTabWidget()
        self.t_data = DataTab(self)
        self.t_norm = NormTab(self)
        self.t_rmin = LoopTab(self, "rmin")
        self.t_qmax = LoopTab(self, "qmax")
        self.t_chi = Chi2Tab(self)
        self.t_batch = BatchTab(self)
        self.t_rps = RPSTab(self)
        for t, name in [(self.t_data, tr("Dane")), (self.t_norm, tr("Normalizacja")), (self.t_rmin, tr("Pętla r_min")),
                        (self.t_qmax, tr("Pętla q_max")), (self.t_chi, tr("Mapa χ²")), (self.t_batch, tr("Batch")),
                        (self.t_rps, tr("RPS – piki i wygładzanie"))]:
            self.tabs.addTab(t, name)
        self.setCentralWidget(self.tabs)

        self.logw = QtWidgets.QPlainTextEdit()
        self.logw.setObjectName("log")
        self.logw.setReadOnly(True)
        self.logw.setMaximumBlockCount(5000)
        ld = QtWidgets.QDockWidget(tr("Dziennik"), self)
        ld.setObjectName("log")
        ld.setWidget(self.logw)
        ld.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, ld)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.resizeDocks([ld], [110], Qt.Vertical)

        sb = self.statusBar()
        self.status = QtWidgets.QLabel(tr("Gotowy"))
        self.pbar = QtWidgets.QProgressBar()
        self.pbar.setMaximumWidth(260)
        self.pbar.setVisible(False)
        self.b_stop = QtWidgets.QPushButton(tr("Stop"))
        self.b_stop.setObjectName("stop")
        self.b_stop.setEnabled(False)
        self.b_stop.clicked.connect(self.stop)
        sb.addWidget(self.status, 1)
        sb.addPermanentWidget(self.pbar)
        sb.addPermanentWidget(self.b_stop)

        self._menus()
        self.setStyleSheet(STYLE)
        self.resize(1500, 950)
        g = self.settings.value("geometry")
        if g is not None:
            self.restoreGeometry(g)
        self.params.loaded.connect(self._sync_tabs)
        self.log(tr('Amorpheus-Qt {0} – Python {1}').format(__version__, sys.version.split()[0]))

    # ------------------------------------------------------------------------------
    def _menus(self):
        m = self.menuBar().addMenu(tr("&Plik"))
        a = m.addAction(tr("Otwórz dane…"), self.open_data)
        a.setShortcut("Ctrl+O")
        a = m.addAction(tr("Otwórz projekt (Init.txt)…"), self.params.load_dialog)
        a.setShortcut("Ctrl+Shift+O")
        a = m.addAction(tr("Zapisz projekt"), lambda: self.params.save_project(quiet=False))
        a.setShortcut("Ctrl+S")
        m.addAction(tr("Zapisz projekt jako…"), self.params.save_dialog)
        m.addSeparator()
        m.addAction(tr("Wczytaj przykład (szkło Ce)"), self.load_example)
        m.addSeparator()
        m.addAction(tr("Otwórz folder wyników"), self.open_out)
        m.addSeparator()
        a = m.addAction(tr("Zakończ"), self.close)
        a.setShortcut("Ctrl+Q")
        h = self.menuBar().addMenu(tr("&Pomoc"))
        h.addAction(tr("O programie"), lambda: QtWidgets.QMessageBox.about(self, tr("O programie"), ABOUT))
        h.addAction(tr("Zmiany względem oryginału"), lambda: QtWidgets.QMessageBox.information(self, tr("Zmiany"), CHANGES))
        h.addAction(tr("Pomoc – opis parametrów"), self.show_help)

        lm = self.menuBar().addMenu("Język / Language")
        grp = QtWidgets.QActionGroup(self)
        for code, name in LANGUAGES.items():
            act = lm.addAction(name, lambda c=code: self.set_language(c))
            act.setCheckable(True)
            act.setChecked(code == LANG)
            grp.addAction(act)

    def show_help(self):
        root = Path(__file__).resolve().parents[2]
        p = root / ("README.pl.md" if LANG == "pl" else "README.md")
        if not p.exists():
            p = root / "README.md"
        txt = p.read_text(encoding="utf-8") if p.exists() else tr("Brak README.md")
        d = QtWidgets.QDialog(self)
        d.setWindowTitle(tr("Pomoc"))
        d.resize(820, 700)
        v = QtWidgets.QVBoxLayout(d)
        t = QtWidgets.QTextBrowser()
        t.setOpenExternalLinks(True)
        if hasattr(t, "setMarkdown"):
            t.setMarkdown(txt)
        else:
            t.setPlainText(txt)
        v.addWidget(t)
        d.exec_()

    def load_example(self):
        from ..examples import ensure_examples
        p = Path(__file__).resolve().parents[2] / "examples" / "Init.txt"
        try:
            ensure_examples(log=self.log)
        except Exception as e:
            self.log(str(e).splitlines()[0])
            QtWidgets.QMessageBox.warning(self, tr("Przykład"), str(e))
            return
        if p.exists():
            self.params.load_init(p)
            self.t_batch.e_file.setText(str(p.with_name("Batch.csv")))
            self.t_data.show_data()

    # ------------------------------------------------------------------------------
    def open_data(self, path=None):
        """Otwarcie pliku danych: istniejacy projekt obok danych albo nowy z autodetekcji."""
        if not path:
            start = self.params.base_dir or str(Path.home())
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, tr("Otwórz dane"), start, DATA_FILTER)
            if not path:
                return
        path = Path(path)
        proj = ad.project_path(path)
        if proj.exists():
            r = QtWidgets.QMessageBox.question(
                self, tr("Projekt istnieje"),
                tr('Dla tych danych jest już zapisany projekt:\n{0}\n\nTak – wczytaj zapisany projekt\nNie – utwórz nowy (parametry odczytane od nowa z pliku)').format(proj.name),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
            if r == QtWidgets.QMessageBox.Cancel:
                return
            if r == QtWidgets.QMessageBox.Yes:
                self._load_project(proj)
                return
        try:
            dlg = OpenDataDialog(path, self.params.params(), self)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Otwórz dane"), tr('Nie udało się odczytać pliku:\n{0}').format(e))
            return
        dlg.setStyleSheet(STYLE)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        p = dlg.result_params()
        self.params.set_params(p)
        self.params.f_out.setText(str(path.parent))
        if self.params.save_project(str(proj)):
            self.params.init_path = str(proj)
            self._load_project(proj, quiet=True)
            self.log(tr('Utworzono projekt {0} dla danych {1}').format(proj.name, path.name))
            for w in dlg.det.warnings:
                self.log(tr("UWAGA: ") + w)
        else:
            self.log(tr("Nie udało się zapisać projektu obok danych – parametry są tylko w panelu."))
        self.tabs.setCurrentWidget(self.t_data)

    def _load_project(self, proj, quiet=False):
        try:
            self.params.load_init(proj)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, tr("Projekt"), tr('Nie udało się wczytać {0}:\n{1}').format(proj, e))
            return
        self.t_data.show_data()
        self.tabs.setCurrentWidget(self.t_data)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dropEvent(self, ev):
        urls = [u.toLocalFile() for u in ev.mimeData().urls() if u.isLocalFile()]
        if urls:
            self.open_path(urls[0])

    def open_path(self, path):
        """Init.txt -> wczytaj projekt, inny plik -> otworz jako dane."""
        path = Path(path)
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:2000]
        except Exception:
            head = ""
        if "[Parameters]" in head:
            self._load_project(path)
        else:
            self.open_data(path)

    def open_out(self):
        d = self.params.out_dir()
        d.mkdir(parents=True, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(d)))

    def _sync_tabs(self):
        p = self.params.params()
        for t in (self.t_rmin, self.t_qmax):
            t.s_rho0.setValue(p.rho)
            t.s_bk0.setValue(min(max(p.bkfactor, 0.7), 1.2))
            t.s_bk0.setEnabled(p.has_bkg)
        self.t_chi.s_rmin.setValue(p.rmin)
        self.t_chi.s_rc.setValue(p.rho)
        self.t_chi.s_bc.setValue(p.bkfactor)

    # ------------------------------------------------------------------------------
    def log(self, txt):
        self.logw.appendPlainText(time.strftime("%H:%M:%S  ") + str(txt))

    def checked_params(self):
        p = self.params.params()
        errs = p.validate()
        if not p.path(p.filename).is_file():
            errs.append(tr('Nie znaleziono pliku danych: {0}').format(p.path(p.filename)))
        if p.has_bkg and not p.path(p.filename_bkg).is_file():
            errs.append(tr('Nie znaleziono pliku tła: {0}').format(p.path(p.filename_bkg)))
        if errs:
            QtWidgets.QMessageBox.warning(self, tr("Parametry"), "\n".join(errs))
            return None
        self.params._files_changed()
        rng = self.params.file_range
        if rng and (p.qmin < rng[0] - 1e-9 or p.qmax > rng[1] + 1e-9):
            r = QtWidgets.QMessageBox.question(
                self, tr("Zakres q"),
                tr('Zakres q_min–q_max ({0:g}–{1:g} nm⁻¹) wychodzi poza dane ({2:.3f}–{3:.3f} nm⁻¹).\nPrzyciąć do zakresu danych?').format(p.qmin, p.qmax, rng[0], rng[1]))
            if r != QtWidgets.QMessageBox.Yes:
                return None
            self.params.s_qmin.setValue(max(p.qmin, rng[0] + 1e-6))
            self.params.s_qmax.setValue(min(p.qmax, rng[1] - 1e-6))
            p = self.params.params()
        self.params.save_project()          # autozapis projektu przy kazdym uruchomieniu obliczen
        return p

    def run_task(self, fn, on_done, label, on_partial=None):
        if self.worker is not None and self.worker.isRunning():
            QtWidgets.QMessageBox.information(self, tr("Zajęty"), tr("Trwają obliczenia – poczekaj lub naciśnij Stop."))
            return
        w = Worker(fn, self)
        self.worker = w
        t0 = time.time()
        w.ctx.progress.connect(self._progress)
        w.ctx.message.connect(self.log)
        if on_partial:
            w.ctx.partial.connect(on_partial)

        def ok(res):
            self._busy(False)
            self.status.setText(tr('{0}: gotowe ({1:.1f} s)').format(label, time.time() - t0))
            on_done(res)

        def bad(msg):
            self._busy(False)
            self.status.setText(tr('{0}: błąd').format(label))
            self.log(tr('BŁĄD ({0}): {1}').format(label, msg.splitlines()[0]))
            box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, label, msg.split("\n\n")[0], parent=self)
            box.setDetailedText(msg)
            box.exec_()

        w.finished_ok.connect(ok)
        w.failed.connect(bad)
        self._busy(True, label)
        w.start()

    def _busy(self, on, label=""):
        self.b_stop.setEnabled(on)
        self.pbar.setVisible(on)
        self.pbar.setRange(0, 0)
        if on:
            self.status.setText(f"{label}…")
            QtWidgets.QApplication.setOverrideCursor(Qt.BusyCursor)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()
        for t in (self.t_norm, self.t_rmin, self.t_qmax, self.t_chi, self.t_batch):
            for b in t.run_buttons():
                b.setEnabled(not on)

    def _progress(self, i, n, txt):
        if n > 0:
            self.pbar.setRange(0, n)
            self.pbar.setValue(i)
        if txt:
            self.status.setText(txt)

    def stop(self):
        if self.worker is not None:
            self.worker.ctx.cancel()
            self.status.setText(tr("Przerywanie… (kończę bieżący krok)"))
            self.log(tr("Przerwano przez użytkownika – wyniki częściowe zostaną zachowane."))

    def set_language(self, code):
        if code == LANG:
            return
        save_language(code)
        # komunikat w JEZYKU DOCELOWYM (uzytkownik moze nie znac biezacego)
        if code == "en":
            title, msg = "Language", ("The interface language will change to English after restarting the program.\n\n"
                                      "Restart now? The current project will be saved.")
        else:
            title, msg = "Język", ("Język interfejsu zmieni się na polski po ponownym uruchomieniu programu.\n\n"
                                   "Uruchomić ponownie teraz? Bieżący projekt zostanie zapisany.")
        r = QtWidgets.QMessageBox.question(self, title, msg)
        if r == QtWidgets.QMessageBox.Yes:
            self._restart = True
            self.close()

    def closeEvent(self, ev):
        if self.worker is not None and self.worker.isRunning():
            self.worker.ctx.cancel()
            self.worker.wait(5000)
        self.params.save_project()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_init", self.params.init_path)
        self.settings.setValue("out_dir", self.params.f_out.text())
        super().closeEvent(ev)
        if getattr(self, "_restart", False):
            # nowy proces bez --lang i bez pliku z wiersza polecen: jezyk z ustawien, projekt = ostatni
            args = [_SCRIPT] if _SCRIPT.endswith(".py") else []
            QtCore.QProcess.startDetached(sys.executable, args)

    def restore_last(self):
        last = self.settings.value("last_init", "")
        if last and Path(last).exists():
            try:
                self.params.load_init(last)
            except Exception as e:
                self.log(tr('Nie wczytano ostatniego Init: {0}').format(e))
        else:
            self.load_example()
        od = self.settings.value("out_dir", "")
        if od:
            self.params.f_out.setText(od)


def main(argv=None):
    argv = strip_lang_args(argv if argv is not None else sys.argv)
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QtWidgets.QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QtWidgets.QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(argv)
    app.setStyle("Fusion")
    app.setApplicationName("Amorpheus-Qt")
    w = MainWindow()
    w.show()
    if len(argv) > 1 and Path(argv[1]).is_file():
        w.restore_last()
        w.open_path(argv[1])
    else:
        w.restore_last()
    return app.exec_()
