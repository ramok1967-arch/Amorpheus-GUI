# -*- coding: utf-8 -*-
"""Angielskie tlumaczenia tekstow interfejsu (klucz = tekst polski z kodu, patrz i18n.tr)."""

EN = {
    # --- obliczenia, komunikaty ---------------------------------------------------------------
    "gotowe": "done",
    "Krok musi byc dodatni.": "Step must be positive.",
    "Pusty zakres.": "Empty range.",
    "Mapa chi² wymaga danych z tlem (format 2 lub 4).": "The χ² map requires data with background (format 2 or 4).",
    "rmin = {0:.4f} nm": "rmin = {0:.4f} nm",
    "qmax = {0:.3f} nm⁻¹": "qmax = {0:.3f} nm⁻¹",
    "{0}: dopasowanie": "{0}: fitting",
    "[{0}/{1}] {2}: rho = {3:.3f} at/nm³, bk = {4:.4f}, χ² = {5:.4g}  ({6:.1f} s)":
        "[{0}/{1}] {2}: rho = {3:.3f} at/nm³, bk = {4:.4f}, χ² = {5:.4g}  ({6:.1f} s)",
    "{0}: normalizacja": "{0}: normalization",
    "[{0}/{1}] {2}: BLAD - {3}": "[{0}/{1}] {2}: ERROR - {3}",
    "Nie rozpoznano jednostki osi z nagłówka – sprawdź format.":
        "Axis unit not recognized from the header – check the format.",
    "Oś 2θ w radianach nie jest obsługiwana – przelicz na stopnie albo Q.":
        "2θ axis in radians is not supported – convert to degrees or Q.",
    "Brak korekty polaryzacji w integracji (Polarization factor: None).":
        "No polarization correction in the integration (Polarization factor: None).",
    "Dane w 2θ, a w nagłówku nie ma długości fali – podaj λ.":
        "Data in 2θ, but no wavelength in the header – enter λ.",
    "Nie odczytano składu z nazwy pliku – wpisz go ręcznie.":
        "Composition not found in the file name – enter it manually.",
    "Pominięto {0} punktów na krańcach danych (obszar z I = 0 – brak pokrycia detektora; dane do x = {1:.4g}).":
        "Skipped {0} points at the data edges (I = 0 region – no detector coverage; data up to x = {1:.4g}).",
    "Nie ustalono zakresu q: {0}": "Could not determine the q range: {0}",
    "2θ, bez tła": "2θ, no bkg",
    "2θ + tło": "2θ + bkg",
    "Q, bez tła": "Q, no bkg",
    "Q + tło": "Q + bkg",
    "Dane": "Data",
    "Format pliku musi byc 1-4.": "File format must be 1-4.",
    "Wymagane 0 < qmin < qmax.": "Required: 0 < qmin < qmax.",
    "Gestosc musi byc dodatnia.": "Density must be positive.",
    "Podaj sklad (co najmniej jeden pierwiastek).": "Enter the composition (at least one element).",
    "Dla danych w 2θ podaj dlugosc fali λ > 0.": "For 2θ data enter a wavelength λ > 0.",
    "qmax niedostepne dla tej dlugosci fali (q·λ/4π ≥ 1).": "qmax not reachable at this wavelength (q·λ/4π ≥ 1).",
    "Tło": "Background",
    "Plik {0}: za malo wierszy z danymi liczbowymi ({1}).": "File {0}: too few rows with numeric data ({1}).",
    "{0}: zadany zakres wychodzi poza dane w pliku ({1:.4g} - {2:.4g}).":
        "{0}: the requested range is outside the data in the file ({1:.4g} - {2:.4g}).",
    "rmin musi byc w zakresie (0, {0}] nm.": "rmin must be in the range (0, {0}] nm.",
    "Suma udzialow = {0:.4f}, a powinna byc 1.": "Sum of fractions = {0:.4f}, should be 1.",
    "Nieznany pierwiastek: {0}": "Unknown element: {0}",
    "Nieznany pierwiastek: '{0}'": "Unknown element: '{0}'",
    "Pobieranie danych przykładowych: {0}": "Downloading example data: {0}",
    "Nie udało się pobrać {0}\n({1})\n\nPobierz ręcznie pliki {2} z https://github.com/CelluleProjet/Amorpheus/tree/main/Amorpheus do folderu {3}":
        "Could not download {0}\n({1})\n\nDownload the files {2} manually from "
        "https://github.com/CelluleProjet/Amorpheus/tree/main/Amorpheus into the folder {3}",
    "q (nm⁻¹)": "q (nm⁻¹)",
    "r (nm)": "r (nm)",
    "Nie skopiowano tabeli batch: {0}": "Batch table not copied: {0}",
    "Za mało punktów w zakresie (min. 5).": "Too few points in the range (min. 5).",
    "Nie można usunąć wszystkich punktów.": "Cannot remove all points.",

    # --- okno glowne, menu --------------------------------------------------------------------
    "<h3>Amorpheus-Qt {0}</h3>\n<p>Przepisana wersja programu <b>Amorpheus</b> do analizy rozpraszania promieniowania X\nprzez materiały amorficzne i ciecze: normalizacja, S(q), F(r), g(r), dopasowanie gęstości\ni współczynnika tła metodą Kaplowa/Eggerta, pętle po r<sub>min</sub> i q<sub>max</sub>, mapa χ²,\ntryb wsadowy oraz narzędzie RPS (usuwanie pików, wygładzanie).</p>\n<p><b>Oryginał:</b> S. Boccato i in. (2020–2022),\n<a href=\"https://github.com/CelluleProjet/Amorpheus\">github.com/CelluleProjet/Amorpheus</a><br>\n<b>Cytowanie:</b> Boccato i in., High Pressure Research (2022),\n<a href=\"https://doi.org/10.1080/08957959.2022.2032032\">doi:10.1080/08957959.2022.2032032</a></p>\n<p>Licencja: GNU GPL v3 (jak oryginał).</p>":
        "<h3>Amorpheus-Qt {0}</h3>\n<p>A rewritten version of <b>Amorpheus</b> for the analysis of X-ray scattering\n"
        "from amorphous materials and liquids: normalization, S(q), F(r), g(r), fit of density and\n"
        "background factor by the Kaplow/Eggert method, r<sub>min</sub> and q<sub>max</sub> loops, χ² map,\n"
        "batch mode and the RPS tool (peak removal, smoothing).</p>\n"
        "<p><b>Original:</b> S. Boccato et al. (2020–2022),\n"
        "<a href=\"https://github.com/CelluleProjet/Amorpheus\">github.com/CelluleProjet/Amorpheus</a><br>\n"
        "<b>Citation:</b> Boccato et al., High Pressure Research (2022),\n"
        "<a href=\"https://doi.org/10.1080/08957959.2022.2032032\">doi:10.1080/08957959.2022.2032032</a></p>\n"
        "<p>Licence: GNU GPL v3 (as the original).</p>",
    "<h3>Zmiany względem oryginału v1.0.5</h3>\n<ul>\n<li><b>Wyniki</b>: przy wyłączonej „poprawce jednostek” identyczne z oryginałem (test w <i>tests/</i>,\nróżnice rzędu 1e-14).</li>\n<li><b>Poprawka jednostek w normalizacji</b> (domyślnie włączona): w oryginale człon −2π²ρ w regule\nsum był 10× za mały (całka po dq w nm⁻¹ przy Q² w Å⁻²). Wpływ na ρ znikomy, bkfactor zmienia się\nw trzecim miejscu po przecinku.</li>\n<li>Wczytywanie plików: nie gubi wierszy z liczbami ujemnymi lub zaczynającymi się od kropki;\nakceptuje przecinek dziesiętny, średnik, tab, przecinek jako separator kolumn; sortuje dane.</li>\n<li>Dopasowania ok. 4–5× szybsze (macierz sin(qr) liczona raz, tylko dla r &lt; r<sub>min</sub>).</li>\n<li>Funkcja modyfikująca: brak NaN w punkcie r = a.</li>\n<li>Działa z aktualnymi NumPy 2.x / SciPy (oryginał używał usuniętych np.trapz / scipy.integrate.trapz).</li>\n<li>Batch bez ezodf (pandas + odfpy); obsługuje też .xlsx i .csv; błąd w jednym wierszu nie przerywa całości.</li>\n<li>Brak exec/eval na zawartości Init.txt; Init.txt zgodny w obie strony (dodatkowe opcje w osobnej sekcji).</li>\n<li><b>Otwieranie danych</b> (Ctrl+O): parametry odczytywane z pliku (jednostka, λ, zakres, skład z nazwy),\nprojekt &lt;dane&gt;_Init.txt tworzony i zapisywany automatycznie obok danych; obsługa Q w nm⁻¹.</li>\n<li>Poprawione drobne błędy: nagłówek pliku pętli q<sub>max</sub>, nazwy plików, wykres ρ(q<sub>max</sub>)\nzapisywany pod złym prefiksem, Erase w RPS gubiący ostatni punkt.</li>\n</ul>":
        "<h3>Changes from the original v1.0.5</h3>\n<ul>\n"
        "<li><b>Results</b>: with the “unit correction” unchecked, identical to the original (test in <i>tests/</i>,\n"
        "differences of order 1e-14).</li>\n"
        "<li><b>Unit correction in the normalization</b> (on by default): in the original the −2π²ρ term of the sum\n"
        "rule was 10× too small (integral over dq in nm⁻¹ with Q² in Å⁻²). The effect on ρ is negligible; bkfactor\n"
        "changes in the third decimal place.</li>\n"
        "<li>File reading: rows with negative numbers or starting with a dot are no longer lost; decimal comma,\n"
        "semicolon, tab and comma are accepted as column separators; data are sorted.</li>\n"
        "<li>Fits about 4–5× faster (sin(qr) matrix computed once, only for r &lt; r<sub>min</sub>).</li>\n"
        "<li>Modification function: no NaN at r = a.</li>\n"
        "<li>Works with current NumPy 2.x / SciPy (the original used the removed np.trapz / scipy.integrate.trapz).</li>\n"
        "<li>Batch without ezodf (pandas + odfpy); also supports .xlsx and .csv; an error in one row does not stop the batch.</li>\n"
        "<li>No exec/eval on the contents of Init.txt; Init.txt compatible in both directions (extra options in a separate section).</li>\n"
        "<li><b>Open data</b> (Ctrl+O): parameters read from the file (unit, λ, range, composition from the name),\n"
        "project &lt;data&gt;_Init.txt created and saved automatically next to the data; Q in nm⁻¹ supported.</li>\n"
        "<li>Minor bugs fixed: q<sub>max</sub> loop file header, file names, ρ(q<sub>max</sub>) plot\n"
        "saved under the wrong prefix, RPS Erase dropping the last point.</li>\n</ul>",
    "Parametry": "Parameters",
    "Dziennik": "Log",
    "Gotowy": "Ready",
    "Stop": "Stop",
    "&Plik": "&File",
    "Otwórz dane…": "Open data…",
    "Otwórz projekt (Init.txt)…": "Open project (Init.txt)…",
    "Zapisz projekt": "Save project",
    "Zapisz projekt jako…": "Save project as…",
    "Wczytaj przykład (szkło Ce)": "Load example (Ce glass)",
    "Otwórz folder wyników": "Open results folder",
    "Zakończ": "Exit",
    "&Pomoc": "&Help",
    "O programie": "About",
    "Zmiany względem oryginału": "Changes from the original",
    "Pomoc – opis parametrów": "Help – parameter description",
    "Brak README.md": "README.md not found",
    "Pomoc": "Help",
    "Otwórz dane": "Open data",
    "Projekt istnieje": "Project exists",
    "Nie udało się zapisać projektu obok danych – parametry są tylko w panelu.":
        "Could not save the project next to the data – the parameters are only in the panel.",
    "Zakres q": "q range",
    "Zajęty": "Busy",
    "Trwają obliczenia – poczekaj lub naciśnij Stop.": "A calculation is running – wait or press Stop.",
    "Przerywanie… (kończę bieżący krok)": "Stopping… (finishing the current step)",
    "Przerwano przez użytkownika – wyniki częściowe zostaną zachowane.":
        "Stopped by the user – partial results are kept.",
    "Amorpheus-Qt {0}": "Amorpheus-Qt {0}",
    "Amorpheus-Qt {0} – Python {1}": "Amorpheus-Qt {0} – Python {1}",
    "Zmiany": "Changes",
    "Przykład": "Example",
    "Projekt": "Project",
    "Dla tych danych jest już zapisany projekt:\n{0}\n\nTak – wczytaj zapisany projekt\nNie – utwórz nowy (parametry odczytane od nowa z pliku)":
        "A project for these data already exists:\n{0}\n\nYes – load the saved project\n"
        "No – create a new one (parameters read again from the file)",
    "Utworzono projekt {0} dla danych {1}": "Created project {0} for data {1}",
    "UWAGA: ": "WARNING: ",
    "Nie znaleziono pliku danych: {0}": "Data file not found: {0}",
    "Nie znaleziono pliku tła: {0}": "Background file not found: {0}",
    "Zakres q_min–q_max ({0:g}–{1:g} nm⁻¹) wychodzi poza dane ({2:.3f}–{3:.3f} nm⁻¹).\nPrzyciąć do zakresu danych?":
        "The q_min–q_max range ({0:g}–{1:g} nm⁻¹) is outside the data ({2:.3f}–{3:.3f} nm⁻¹).\nTrim to the data range?",
    "{0}: gotowe ({1:.1f} s)": "{0}: done ({1:.1f} s)",
    "{0}: błąd": "{0}: error",
    "BŁĄD ({0}): {1}": "ERROR ({0}): {1}",
    "Nie udało się odczytać pliku:\n{0}": "Could not read the file:\n{0}",
    "Nie udało się wczytać {0}:\n{1}": "Could not load {0}:\n{1}",
    "Nie udało się wczytać pliku:\n{0}": "Could not load the file:\n{0}",
    "Pętla r_min": "r_min loop",
    "Pętla q_max": "q_max loop",
    "RPS – piki i wygładzanie": "RPS – peaks and smoothing",
    "folder": "folder",
    "plik": "file",
    "tło": "background",
    "format": "format",
    "tło st.": "bkg deg.",
    "I (j.u.)": "I (a.u.)",
    "Dane z pliku": "Data from file",
    "Intensywność": "Intensity",
    "S(q) + przesunięcie": "S(q) + offset",
    "g(r) + przesunięcie": "g(r) + offset",
    "Gęstość": "Density",
    "Replace: odcinek prostej {0:.4g} – {1:.4g}": "Replace: straight line {0:.4g} – {1:.4g}",
    "Erase: kliknij 'Zatwierdź', aby usunąć punkty z zakresu.": "Erase: click 'Accept' to remove the points in the range.",
    "Nie wczytano ostatniego Init: {0}": "Last Init not loaded: {0}",

    # --- okno "Otworz dane" ---------------------------------------------------------------------
    "Dane (*.xy *.dat *.txt *.chi *.csv *.xye);;Wszystkie (*)": "Data (*.xy *.dat *.txt *.chi *.csv *.xye);;All files (*)",
    "Q w Å⁻¹": "Q in Å⁻¹",
    "Q w nm⁻¹": "Q in nm⁻¹",
    "2θ w stopniach": "2θ in degrees",
    "Nowa analiza – parametry z pliku danych": "New analysis – parameters from the data file",
    "Pliki": "Files",
    "(brak tła)": "(no background)",
    "Wybierz…": "Browse…",
    "Tło (pusta komórka)": "Background (empty cell)",
    "Parametry (można poprawić)": "Parameters (editable)",
    "1: tło z pustej komórki": "1: empty-cell background",
    "0: tło zmierzone na próbce": "0: background measured on sample",
    "Skład i gęstość": "Composition and density",
    "nieznana": "unknown",
    "Gęstość masowa": "Mass density",
    "ρ startowe": "Initial ρ",
    "Utwórz projekt": "Create project",
    "Anuluj": "Cancel",
    "Plik tła": "Background file",
    "Oś x w pliku": "x axis in file",
    "q_min": "q_min",
    "q_max": "q_max",
    "r_min (start)": "r_min (start)",
    "incoherent": "incoherent",
    "Pierwiastek": "Element",
    "Udział at.": "At. fraction",
    "Bez tła: format bez odejmowania tła, dopasowywana jest tylko ρ. Rozpraszanie od komórki/kapilary/powietrza zostaje w S(q).":
        "No background: a format without background subtraction, only ρ is fitted. "
        "Scattering from the cell/capillary/air remains in S(q).",
    " ✗ (zostanie znormalizowana)": " ✗ (will be normalized)",
    "q_min musi być mniejsze od q_max.": "q_min must be smaller than q_max.",
    "Skład odczytany z nazwy pliku.": "Composition read from the file name.",
    "Nie odczytano składu z nazwy – wpisz pierwiastki i udziały atomowe.":
        "Composition not found in the name – enter the elements and atomic fractions.",
    "Q [nm⁻¹]": "Q [nm⁻¹]",
    "2θ [rad]": "2θ [rad]",
    "<b>Wykryto:</b> {0}, oś: {1}, {2} punktów, x = {3:.4g} – {4:.4g}":
        "<b>Detected:</b> {0}, axis: {1}, {2} points, x = {3:.4g} – {4:.4g}",
    "plik tekstowy": "text file",
    "<br>ρ = 602,2·d/M̄ = <b>{0:.2f} at/nm³</b>": "<br>ρ = 602.2·d/M̄ = <b>{0:.2f} at/nm³</b>",
    "suma udziałów = {0:.4f}": "sum of fractions = {0:.4f}",
    "λ = {0:.6g} nm ({1:.5g} Å, {2:.2f} keV)": "λ = {0:.6g} nm ({1:.5g} Å, {2:.2f} keV)",
    "Pierwsze maksimum przy q ≈ {0:.1f} nm⁻¹ → q_min ustawione poniżej, q_max przed końcem danych.":
        "First maximum at q ≈ {0:.1f} nm⁻¹ → q_min set below it, q_max before the end of the data.",
    "<span style='color:#b45309'>⚠ {0}</span>": "<span style='color:#b45309'>⚠ {0}</span>",
    "<b style='color:#c62828'>Nie udało się odczytać pliku:</b> {0}": "<b style='color:#c62828'>Could not read the file:</b> {0}",

    # --- zakladki ----------------------------------------------------------------------------------
    "Pokaż dane": "Show data",
    "Normalizuj": "Normalize",
    "S(q), F(r), g(r) dla ρ i bkfactor z panelu parametrów (opcja [n] oryginału)":
        "S(q), F(r), g(r) for ρ and bkfactor from the parameter panel (option [n] of the original)",
    "Dopasuj ρ, bk → normalizuj": "Fit ρ, bk → normalize",
    "Najpierw minimalizacja χ² przy r_min z panelu, potem normalizacja\nz dopasowanymi wartościami (jak pojedynczy wiersz batcha).":
        "First minimizes χ² at r_min from the panel, then normalizes\nwith the fitted values (like a single batch row).",
    "Zapisz wyniki": "Save results",
    "zapisuj automatycznie": "save automatically",
    "Funkcja modyfikująca M(Q, Δ(r))": "Modification function M(Q, Δ(r))",
    "Przelicz g(r) z M(Q,Δ)": "Compute g(r) with M(Q,Δ)",
    "Domyślne a, b": "Default a, b",
    "a (pozycja 1. piku)": "a (1st peak position)",
    "b (szerokość)": "b (width)",
    "Przenieś ρ, bk do parametrów": "Copy ρ, bk to parameters",
    "Normalizacja": "Normalization",
    "Funkcja modyfikująca": "Modification function",
    "Przeniesiono ρ i bkfactor do parametrów.": "ρ and bkfactor copied to the parameters.",
    "Zakres pętli i start dopasowania": "Loop range and fit start",
    "Dla każdego r_min: minimalizacja χ² = ∫₀^rmin [F(r)+4πρr]² dr względem ρ (i bkfactor). Wybierz r_min z plateau ρ(r_min). χ² porównuj tylko lokalnie: rośnie z r_min z definicji, więc jego globalne minimum nie wskazuje najlepszego r_min.":
        "For each r_min: minimization of χ² = ∫₀^rmin [F(r)+4πρr]² dr with respect to ρ (and bkfactor). "
        "Choose r_min from the plateau of ρ(r_min). Compare χ² only locally: it grows with r_min by definition, "
        "so its global minimum does not indicate the best r_min.",
    "Dla każdego q_max dane są wczytywane w zakresie q_min–q_max i dopasowywane jest ρ (i bkfactor) przy r_min z parametrów.":
        "For each q_max the data are read in the q_min–q_max range and ρ (and bkfactor) is fitted at r_min "
        "from the parameters.",
    "Pobierz ρ i bkfactor z panelu parametrów": "Take ρ and bkfactor from the parameter panel",
    "Start": "Start",
    "Zapisz": "Save",
    "Przyjmij zaznaczony wiersz do parametrów": "Apply selected row to parameters",
    "zapisz po zakończeniu": "save when finished",
    "r_min (nm)": "r_min (nm)",
    "q_max (nm⁻¹)": "q_max (nm⁻¹)",
    "Siatka (tylko formaty z tłem)": "Grid (background formats only)",
    "Środek z parametrów": "Centre from parameters",
    "Licz mapę": "Compute map",
    "Przyjmij minimum do parametrów": "Apply minimum to parameters",
    "Mapa χ²": "χ² map",
    "Tabela batch (.ods, .xlsx, .csv) w układzie Batch.ods z oryginału":
        "Batch table (.ods, .xlsx, .csv) in the layout of the original Batch.ods",
    "Wczytaj": "Load",
    "Uruchom batch": "Run batch",
    "Tabela batch": "Batch table",
    "Tabele (*.ods *.xlsx *.xls *.csv);;Wszystkie (*)": "Tables (*.ods *.xlsx *.xls *.csv);;All files (*)",
    "Batch": "Batch",
    "Otwórz plik…": "Open file…",
    "Otwórz plik danych z parametrów": "Open data file from parameters",
    "Zapisz jako…": "Save as…",
    "Zapisz i użyj jako plik danych": "Save and use as data file",
    "stała linia bazowa": "fixed baseline",
    "Jak w oryginale: dane − dopasowanie + prosta przez końce zakresu.\nOdznaczone: odejmowana tylko składowa piku.":
        "As in the original: data − fit + straight line through the range ends.\nUnchecked: only the peak component is subtracted.",
    "Stopień wielomianu tła w dopasowaniu (1 = liniowe)": "Degree of the background polynomial in the fit (1 = linear)",
    "Dopasuj": "Fit",
    "Zatwierdź ✔": "Accept ✔",
    "Reset": "Reset",
    "Wygładź": "Smooth",
    "Otwórz plik z danymi (2 kolumny)": "Open a data file (2 columns)",
    "Plik do obróbki": "File to process",
    "Dane (*.dat *.xy *.txt *.chi *.csv);;Wszystkie (*)": "Data (*.dat *.xy *.txt *.chi *.csv);;All files (*)",
    "Tekst (*.txt *.dat *.xy)": "Text (*.txt *.dat *.xy)",
    "Surowe dane i tło w jednostkach z pliku; żółty pas = zakres q_min–q_max używany w analizie. Górna oś: q w nm⁻¹.":
        "Raw data and background in file units; yellow band = q_min–q_max range used in the analysis. Top axis: q in nm⁻¹.",
    "<b>Iteracje Kaplowa</b>": "<b>Kaplow iterations</b>",
    "it.": "it.",
    "ρ(nachyl.)": "ρ(slope)",
    "CN1": "CN1",
    "CN2": "CN2",
    "r₁ (nm)": "r₁ (nm)",
    "r_min₁": "r_min₁",
    "CN1 = 2 × całka do maksimum 1. piku (zakłada symetrię piku); CN2 = całka do 1. minimum za pikiem. Obie przy ρ użytym w normalizacji.":
        "CN1 = 2 × integral up to the 1st peak maximum (assumes a symmetric peak); CN2 = integral up to the "
        "1st minimum after the peak. Both with the ρ used in the normalization.",
    "normalizacja": "normalization",
    "ρ (at/nm³)": "ρ (at/nm³)",
    "bkfactor": "bkfactor",
    "czas (s)": "time (s)",
    "r_min": "r_min",
    "ρ środek": "ρ centre",
    "ρ szerokość": "ρ width",
    "punkty ρ": "ρ points",
    "bk środek": "bk centre",
    "bk szerokość": "bk width",
    "punkty bk": "bk points",
    "Mapa χ² wymaga danych z tłem (format 2 lub 4).": "The χ² map requires data with background (format 2 or 4).",
    "Za mało policzonych punktów": "Too few computed points",
    "Każdy wiersz: dopasowanie ρ i bkfactor przy r_min z wiersza, następnie normalizacja z dopasowanymi wartościami. Opcje obliczeń (poprawka jednostek, iteracje, r_max, DPI) są brane z panelu parametrów. Wyniki: folder Batch_RRRRMMDD_HHhMM w folderze wyników.":
        "Each row: fit of ρ and bkfactor at r_min from the row, then normalization with the fitted values. "
        "Calculation options (unit correction, iterations, r_max, DPI) are taken from the parameter panel. "
        "Results: folder Batch_YYYYMMDD_HHhMM in the results folder.",
    "zapis wyników": "saving results",
    "OK": "OK",
    "Lewy klik na górnym wykresie = początek zakresu, prawy klik = koniec. Dopasuj pik (Lorentz/Gauss/Voigt + tło liniowe) lub zastąp zakres prostą (Replace) albo usuń punkty (Erase), potem Zatwierdź. Wygładzanie: średnia ruchoma N punktów.":
        "Left click on the upper plot = range start, right click = end. Fit a peak (Lorentz/Gauss/Voigt + linear "
        "background), replace the range with a line (Replace) or remove points (Erase), then Accept. "
        "Smoothing: moving average of N points.",
    "dane surowe": "raw data",
    "po obróbce": "processed",
    "RPS": "RPS",
    "RPS: plik ustawiony jako plik danych w parametrach.": "RPS: file set as the data file in the parameters.",
    "dopasowanie ρ, bk": "fitting ρ, bk",
    "CN: nie znaleziono piku": "CN: peak not found",
    "Zapis": "Save",
    "→ zły zakres": "→ invalid range",
    "Zakres": "Range",
    "od": "from",
    "do": "to",
    "krok": "step",
    "Początek pętli musi być większy niż q_min.": "The loop start must be greater than q_min.",
    "Pętla {0}": "{0} loop",
    "  {0} = {1:.4f}: ρ = {2:.4f}, bk = {3:.5f}, χ² = {4:.5g}": "  {0} = {1:.4f}: ρ = {2:.4f}, bk = {3:.5f}, χ² = {4:.5g}",
    "Przyjęto do parametrów: {0} = {1:.4f}, ρ = {2:.4f}, bk = {3:.5f}": "Applied to parameters: {0} = {1:.4f}, ρ = {2:.4f}, bk = {3:.5f}",
    "{0} punktów siatki, szacunkowo {1:.0f}–{2:.0f} s. Lewy panel: χ²; prawy: χ²/χ²min z konturami 1.5, 5, 10, 20, 50, 100; czerwony krzyż = środek, gwiazdka = minimum.":
        "{0} grid points, approx. {1:.0f}–{2:.0f} s. Left panel: χ²; right: χ²/χ²min with contours 1.5, 5, 10, 20, "
        "50, 100; red cross = centre, star = minimum.",
    "  (przerwano)": "  (stopped)",
    "Mapa χ²: minimum ρ = {0:.4f}, bk = {1:.5f}, χ² = {2:.4g}": "χ² map: minimum ρ = {0:.4f}, bk = {1:.5f}, χ² = {2:.4g}",
    "brak pliku danych": "data file missing",
    "gotowy": "ready",
    "Batch: wczytano {0} wierszy z {1}": "Batch: loaded {0} rows from {1}",
    "BŁĄD: ": "ERROR: ",
    "Batch zakończony, wyniki w: {0}": "Batch finished, results in: {0}",
    "{0}\n{1} punktów, x = {2:.4g} – {3:.4g}": "{0}\n{1} points, x = {2:.4g} – {3:.4g}",
    "zakres": "range",
    "wynik (przed zatw.)": "result (not accepted)",
    "\nZatwierdzono: ": "\nAccepted: ",
    "Normalizacja: ρ = {0:.4f} at/nm³, bk = {1:.5f}; ρ z nachylenia F(r<rmin) = {2:.3f}":
        "Normalization: ρ = {0:.4f} at/nm³, bk = {1:.5f}; ρ from the slope of F(r<rmin) = {2:.3f}",
    "<b>ρ</b> = {0:.4f} at/nm³ &nbsp; <b>bk</b> = {1:.5f}<br>ρ z nachylenia F(r&lt;r<sub>min</sub>): {2:.3f}<br>":
        "<b>ρ</b> = {0:.4f} at/nm³ &nbsp; <b>bk</b> = {1:.5f}<br>ρ from the slope of F(r&lt;r<sub>min</sub>): {2:.3f}<br>",
    "Zapisano {0} plików: {1} / {2}_*": "Saved {0} files: {1} / {2}_*",
    "→ {0} dopasowań": "→ {0} fits",
    "Zapisano: {0}": "Saved: {0}",
    "minimum: ρ = {0:.4f} at/nm³, bk = {1:.5f}, χ² = {2:.4g}": "minimum: ρ = {0:.4f} at/nm³, bk = {1:.5f}, χ² = {2:.4g}",
    "dopasowanie": "fit",
    "Zakres obejmuje {0:.0%} danych. Dopasowanie piku na tak szerokim zakresie\nodejmie sygnał amorficzny (np. główne maksimum S(q)).\n\nUstaw wąski zakres wokół piku krystalicznego (lewy/prawy klik albo pola od–do).\nMimo to dopasować?":
        "The range covers {0:.0%} of the data. Fitting a peak over such a wide range\nwill subtract the amorphous signal "
        "(e.g. the main maximum of S(q)).\n\nSet a narrow range around the crystalline peak (left/right click or the "
        "from–to fields).\nFit anyway?",
    "RPS: zapisano {0}": "RPS: saved {0}",
    "Dopasowanie (r_min={0:g} nm): ρ = {1:.4f} at/nm³, bk = {2:.5f}, χ² = {3:.5g}  [{4} wywołań, {5:.1f} s]":
        "Fit (r_min={0:g} nm): ρ = {1:.4f} at/nm³, bk = {2:.5f}, χ² = {3:.5g}  [{4} evaluations, {5:.1f} s]",
    "; CN1 = {0:.2f}, CN2 = {1:.2f}": "; CN1 = {0:.2f}, CN2 = {1:.2f}",
    "<b>CN1</b> = {0:.2f} &nbsp; <b>CN2</b> = {1:.2f} &nbsp; r<sub>1</sub> = {2:.4f} nm":
        "<b>CN1</b> = {0:.2f} &nbsp; <b>CN2</b> = {1:.2f} &nbsp; r<sub>1</sub> = {2:.4f} nm",
    "q_max nie może przekraczać {0:.3f} nm⁻¹ (koniec danych).": "q_max cannot exceed {0:.3f} nm⁻¹ (end of data).",
    "Nie udało się wczytać tabeli:\n{0}": "Could not load the table:\n{0}",
    "wygładzone (N={0})": "smoothed (N={0})",
    "Błąd dopasowania: {0}": "Fit error: {0}",
    "g(r) z funkcją modyfikującą: a = {0:.4f} nm, b = {1:.4f} nm": "g(r) with modification function: a = {0:.4f} nm, b = {1:.4f} nm",
    "Brak danych do wyświetlenia": "No data to display",

    # --- panel parametrow ------------------------------------------------------------------------
    "Wybierz plik danych (i tła) – parametry zostaną odczytane z pliku,\na projekt <dane>_Init.txt utworzony obok danych.":
        "Choose a data file (and background) – parameters will be read from the file\n"
        "and a project <data>_Init.txt created next to the data.",
    "Zapisuje parametry do pliku projektu (zapis odbywa się też automatycznie\nprzy każdym uruchomieniu obliczeń i przy zamknięciu programu).":
        "Saves the parameters to the project file (also saved automatically\n"
        "whenever a calculation starts and when the program closes).",
    "Plik danych": "Data file",
    "1: pusta kom.": "1: empty cell",
    "0: na próbce": "0: on sample",
    "1: tło z pustej komórki (Compton odejmowany)\n0: tło zmierzone na próbce":
        "1: empty-cell background (Compton subtracted)\n0: background measured on the sample",
    "nm⁻¹": "nm⁻¹",
    "Jednostka osi Q w pliku danych (formaty 3 i 4)": "Unit of the Q axis in the data file (formats 3 and 4)",
    "Format": "Format",
    "Jedn. Q": "Q unit",
    "Incoh.": "Incoh.",
    "Zakresy i start": "Ranges and start",
    "q z pliku": "q from file",
    "Ustaw q_min i q_max na pełny zakres danych w pliku": "Set q_min and q_max to the full data range of the file",
    "Skład (ułamki at.)": "Composition (at. fr.)",
    "Do 1": "To 1",
    "Ustawia udział zaznaczonego pierwiastka tak, aby suma = 1": "Sets the fraction of the selected element so that the sum = 1",
    "Opcje obliczeń": "Calculation options",
    "1: = S(q_min)": "1: = S(q_min)",
    "2: lorentz. (niestabilne)": "2: Lorentz. (unstable)",
    "S(q) poniżej q_min.\n1: S(q<q_min) = S(q_min)\n0: S(q<q_min) = 0\n2: lorentzówka – NIESTABILNE, tylko diagnostyka\nZalecane: 1. Opcja 2 jest ukryta w oryginale (dopasowanie lorentzowki z na sztywno\nwpisanym startem); zwykle psuje dopasowanie gęstości.":
        "S(q) below q_min.\n1: S(q<q_min) = S(q_min)\n0: S(q<q_min) = 0\n2: Lorentzian – UNSTABLE, diagnostics only\n"
        "Recommended: 1. Option 2 is hidden in the original (Lorentzian fit with a hard-coded\n"
        "starting point); it usually spoils the density fit.",
    "0: standardowa": "0: standard",
    "1: z funkcją modyfikującą M(Q,Δ(r)) (Lorch, zmienna szerokość)": "1: with the modification function M(Q,Δ(r)) (Lorch, variable width)",
    "Poprawka jedn. (zalec.)": "Unit correction (rec.)",
    "Zalecane. Odznaczenie = wyniki identyczne z oryginałem v1.0.5,\nw którym człon gęstości w regule sum był 10× za mały.":
        "Recommended. Unchecked = results identical to the original v1.0.5,\n"
        "in which the density term of the sum rule was 10× too small.",
    "QStep (2θ)": "QStep (2θ)",
    "Stały krok dq – diagnostyka; tylko dla danych w 2θ": "Constant dq step – diagnostics; 2θ data only",
    "S(q<q_min)": "S(q<q_min)",
    "Iteracje": "Iterations",
    "r_max wyn.": "Output r_max",
    "Zapis wyników": "Saving results",
    "Folder wyników": "Results folder",
    "Nadpisuj pliki": "Overwrite files",
    "Folder": "Folder",
    "Prefiks norm.": "Norm. prefix",
    "Prefiks r_min": "r_min prefix",
    "Prefiks q_max": "q_max prefix",
    "DPI": "DPI",
    "Wczytaj Init.txt": "Load Init.txt",
    "Init (*.txt *.ini);;Wszystkie (*)": "Init (*.txt *.ini);;All files (*)",
    "Zapisz Init.txt": "Save Init.txt",
    "Init (*.txt)": "Init (*.txt)",
    "Pierw.": "Elem.",
    "Udział": "Fraction",
    "suma:": "sum:",
    "UWAGA: SofQ = 2 (lorentzowka) jest niestabilne - dopasowanie rho moze uciec do granicy. Zalecane SofQ = 1.":
        "WARNING: SofQ = 2 (Lorentzian) is unstable - the rho fit may run to its bound. SofQ = 1 is recommended.",
    "Skład": "Composition",
    "Zaznacz wiersz pierwiastka, który ma uzupełnić sumę.": "Select the row of the element that should complete the sum.",
    "Projekt: {0}": "Project: {0}",
    "Wczytano parametry z {0}": "Parameters loaded from {0}",
    "Zapisano parametry do {0}": "Parameters saved to {0}",
    "zakres w pliku: q = {0:.3f} – {1:.3f} nm⁻¹": "range in file: q = {0:.3f} – {1:.3f} nm⁻¹",
    "Init": "Init",
    "Błąd wykresu: {0}": "Plot error: {0}",
    "Zapisano projekt: {0}": "Project saved: {0}",
    "Nie zapisano projektu {0}: {1}": "Project {0} not saved: {1}",

    # --- wykresy ---------------------------------------------------------------------------------------
    "Czynnik struktury S(q)": "Structure factor S(q)",
    "zakres analizy": "analysis range",
    "I$^{meas}$": "I$^{meas}$",
    "I$^{bkg}$": "I$^{bkg}$",
    "I$^{sample}$": "I$^{sample}$",
    "Pętla po {0}": "Loop over {0}",
    "{0} GPa, {1} K": "{0} GPa, {1} K",
    "iter. {0}": "iter. {0}",
    "I$^{{sample}}$ (bk={0:.4f})": "I$^{{sample}}$ (bk={0:.4f})",
    "Δ(r)·{0:.1f}: a={1:.3f} nm, b={2:.3f} nm": "Δ(r)·{0:.1f}: a={1:.3f} nm, b={2:.3f} nm",
}
