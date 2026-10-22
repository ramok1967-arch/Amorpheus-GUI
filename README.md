# Amorpheus-Qt 2.0

Przepisana wersja programu **Amorpheus** (S. Boccato, Y. Garino, G. Morard, C. Sanloup) do obróbki
danych rozpraszania promieniowania X przez materiały amorficzne i ciecze, z interfejsem graficznym PyQt5.

Program liczy czynnik struktury S(q), zredukowaną funkcję rozkładu F(r) i funkcję rozkładu radialnego g(r).
Gęstość atomową ρ i współczynnik skali tła (bkfactor) dobiera metodą Kaplowa/Eggerta: minimalizuje oscylacje
F(r) poniżej r_min.

Oryginał: <https://github.com/CelluleProjet/Amorpheus>
Cytowanie: Boccato i in., *High Pressure Research* (2022), doi:10.1080/08957959.2022.2032032

---

## Instalacja (Windows, Miniconda)

1. Uruchom **`instaluj.bat`**. Tworzy on środowisko conda `amorpheus` z conda-forge i instaluje:
   python, numpy, scipy, matplotlib, pyqt, lmfit, xraylib, pandas, odfpy, openpyxl. Trwa to kilka minut.
2. Uruchom **`uruchom.bat`**, ewentualnie przeciągnij na niego plik `Init.txt`.

Ręcznie:

```
conda create -n amorpheus -c conda-forge python=3.11 numpy scipy matplotlib pyqt lmfit xraylib pandas odfpy openpyxl
conda activate amorpheus
python amorpheus_qt.py [Init.txt]
```

Przez pip: `pip install -r requirements.txt` (xraylib z pip nie na każdej wersji Pythona ma gotowe koło
dla Windows, dlatego zalecana jest conda).

Przy pierwszym uruchomieniu wczytuje się przykład: szkło Ce z oryginału. Pliki `Cerium.dat` i `background.xy` są wtedy pobierane z GitHuba do folderu `examples`; bez internetu skopiuj je tam ręcznie z repozytorium oryginału.
Później program pamięta ostatnio używany `Init.txt` i folder wyników.

---

## Praca z własnymi danymi

1. **Plik → Otwórz dane…** (Ctrl+O), przycisk „Otwórz dane…” w panelu albo przeciągnięcie pliku na okno.
2. Program odczytuje z pliku i pokazuje do zatwierdzenia:
   - jednostkę osi (Q w Å⁻¹ lub nm⁻¹, 2θ) i długość fali z nagłówka pyFAI/Dioptas/Fit2D;
   - zakres danych bez obszarów z I = 0 (brak pokrycia detektora) oraz q_min/q_max dobrane do pierwszego maksimum;
   - skład z nazwy pliku (`Mg61Cu28Gd11…` → Mg 0,61 / Cu 0,28 / Gd 0,11; „wt” w nazwie → przeliczenie z % wag.);
   - ρ z gęstości masowej, jeśli ją podasz (ρ = 602,2·d/M̄);
   - ostrzeżenie o braku korekty polaryzacji;
   - pliki tła z tego samego folderu (nazwy z *empty*, *bkg*, *background*, *gasket*…).
3. „Utwórz projekt” zapisuje obok danych plik **`<nazwa_danych>_Init.txt`** (format zgodny z oryginałem).
   Projekt zapisuje się sam przy każdym uruchomieniu obliczeń i przy zamknięciu programu.
   Wyniki trafiają do folderu danych.
4. Przy ponownym otwarciu tych samych danych program proponuje wczytanie zapisanego projektu.

Pliki `Init.txt` z oryginalnego Amorpheus można nadal otwierać: **Plik → Otwórz projekt** (Ctrl+Shift+O)
albo przeciągając je na okno.

---

## Okno programu

**Panel Parametry (po lewej)** zawiera wszystkie parametry projektu (`Init.txt`). Pliki Init są zgodne z oryginałem
w obie strony. Opcje dodane w tej wersji zapisywane są w osobnej sekcji `[Amorpheus-Qt]`, którą oryginał
ignoruje.

| Parametr | Znaczenie |
|---|---|
| Plik danych / tła | 2 kolumny tekstu. Separator: spacja, tab, średnik lub przecinek. Dozwolony przecinek dziesiętny i nagłówki |
| Format | 1: 2θ bez tła · 2: 2θ + tło · 3: Q bez tła · 4: Q + tło |
| Q w pliku w | Å⁻¹ (jak w oryginale) albo nm⁻¹ (np. pyFAI `q_nm^-1`); tylko formaty 3 i 4 |
| incoherent | 1 = tło mierzone na pustej komórce (od S odejmowane jest rozpraszanie Comptona); 0 = tło mierzone na próbce |
| λ [nm] | tylko dla danych w 2θ |
| q_min, q_max [nm⁻¹] | zakres analizy (uwaga: nm⁻¹, jak w oryginale; 1 Å⁻¹ = 10 nm⁻¹) |
| r_min [nm] | promień odcięcia: dla r < r_min wymagamy F(r) = −4πρr (≤ 0,4 nm) |
| ρ [at/nm³], bkfactor | wartości do normalizacji i start dopasowania (granice: ρ₀ ± 50, bk 0,7–1,2) |
| Skład | udziały atomowe, suma = 1 („Uzupełnij do 1” dopełnia zaznaczony wiersz) |
| S(q) poniżej q_min | 1: stała = S(q_min); 0: zero; 2: lorentzowka (eksperymentalne w oryginale) |
| Normalizacja | 0: standardowa; 1: dodatkowo g(r) z funkcją modyfikującą M(Q,Δ(r)) |
| Iteracje Kaplowa | 4 jak w oryginale |
| r_max wyników | zasięg F(r), g(r) (1 nm = siatka identyczna z oryginałem) |
| Poprawka jednostek | patrz „Zmiany” niżej; odznacz, aby uzyskać wyniki identyczne z v1.0.5 |

**Zakładki:**

- **Dane**: surowe dane i tło. Żółty pas pokazuje analizowany zakres, górna oś to q w nm⁻¹.
- **Normalizacja** (opcja `[n]`): I(q), S(q), F(r) i g(r) dla każdej iteracji; tabela z gęstością
  z nachylenia F(r<r_min) i liczbami koordynacyjnymi CN1/CN2. Przycisk „Dopasuj ρ, bk → normalizuj”
  najpierw minimalizuje χ², a potem normalizuje. Funkcja modyfikująca ma parametry a i b do zmiany
  i przeliczenia.
- **Pętla r_min** (`[r]`) i **Pętla q_max** (`[x]`): dopasowanie ρ (i bk) dla serii wartości. Tabela
  wypełnia się na bieżąco, wiersz z najmniejszym χ² zaznacza się automatycznie i można go przyjąć
  do parametrów.
- **Mapa χ²** (`[c]`): χ²(ρ, bk) na siatce, wersja surowa i znormalizowana z konturami. Minimum można
  przyjąć do parametrów.
- **Batch** (`[b]`): tabela w układzie `Batch.ods` z oryginału (.ods, .xlsx lub .csv; przykład: `examples/Batch.csv`). Każdy wiersz
  przechodzi dopasowanie, a potem normalizację. Wiersze zaczynające się od `#` są pomijane.
- **RPS**: usuwanie pików krystalicznych (Lorentz, Gauss lub Voigt na tle liniowym/wielomianowym),
  zastępowanie zakresu prostą, usuwanie punktów i wygładzanie średnią ruchomą. Zakres zaznacza się
  na wykresie: lewy klik to początek, prawy koniec. Wynik można od razu ustawić jako plik danych.

Obliczenia działają w tle, więc okno nie zamarza. Przycisk **Stop** przerywa pętlę, a wyniki
częściowe zostają zachowane.

---

## Pliki wynikowe

Nazwy i kolumny są takie jak w oryginale. Każdy plik ma dodatkowo nagłówek z parametrami.

| Operacja | Pliki |
|---|---|
| Normalizacja | `Norm_I.txt` (q, Imeas, Ibkg, Isample), `Norm_S.txt` (q, S iteracji 0…n), `Norm_S_lastcolumn.txt`, `Norm_F.txt`, `Norm_gder.txt` (r, g iteracji), `Norm_CN.txt` (nowy: ρ z nachylenia, CN1, CN2, położenia), `*.png`, `Norm_overview.png`; przy funkcji modyfikującej także `Norm_grlast.txt`, `Norm_deltaR.txt` |
| Pętla r_min | `MinRmin_<dane>-<tło>_<od>-<do>.txt` (rmin, ρ, bk, χ²) + `.png` |
| Pętla q_max | `MinQmax_<dane>-<tło>_<od>-<do>.txt` (qmax, ρ, bk, χ²) + `.png` |
| Mapa χ² | `Norm_Chi2.txt` (wiersze = ρ), `Norm_Chi2_norm.txt`, `Norm_Chi2_axes.txt`, `.png` |
| Batch | folder `Batch_RRRRMMDD_HHhMM`: `S_`, `F_`, `gder_`, `grlast_` (.txt i .png) dla każdego wiersza, `Batch_results_*.txt`, `Batch_results.png`, kopia tabeli |

Jeśli plik już istnieje, do nazwy dopisywany jest numer `_0`, `_1`, … (chyba że zaznaczysz „Nadpisuj”).

---

## Zmiany względem oryginału v1.0.5

- **Zgodność**: przy odznaczonej poprawce jednostek wyniki (S, F, g, CN, ρ z nachylenia, χ², dopasowania,
  pętle) są identyczne z oryginałem. Różnice wynoszą ≤ 1e-13; sprawdza to `tests/test_against_original.py`, porównując na żywo z oryginalnym kodem.
- **Poprawka jednostek w normalizacji** (domyślnie włączona): w oryginale całki w regule sum Krogh-Moe
  liczono po dq w nm⁻¹ przy Q² w Å⁻², przez co człon −2π²ρ był 10× za mały. Po poprawce
  ∫q²(S−1)dq = −2π²ρ zgadza się dokładnie. Dla danych Ce ρ się nie zmienia, a bkfactor zmienia się
  z 0,9281 na 0,9259.
- **Wczytywanie danych**: oryginał po cichu pomijał wiersze zaczynające się od „-” lub „.”, czyli
  ujemne intensywności po odjęciu tła. Teraz są wczytywane. Obsługiwane są też różne separatory.
- **Szybkość**: dopasowanie jest ok. 4× szybsze, bo macierz sin(qr) liczona jest raz i tylko dla r < r_min.
- **Działa z NumPy 2.x i SciPy ≥ 1.14** (oryginał używał usuniętych `np.trapz` i `scipy.integrate.trapz`).
  Batch nie wymaga już przestarzałego `ezodf`.
- **Bezpieczeństwo**: zawartość Init.txt nie jest już wykonywana przez `exec`/`eval`.
- **Nowe**: otwieranie danych z autodetekcją parametrów i automatycznym projektem obok danych, Q w nm⁻¹,
  pomijanie obszarów z I = 0 na krańcach danych, `%` w nazwach plików w Init.txt.
- **Drobne poprawki**:
  - brak NaN w funkcji modyfikującej w punkcie r = a;
  - nagłówek pliku pętli q_max;
  - wykres ρ(q_max) zapisywał się pod prefiksem pętli r_min;
  - Erase w RPS gubił ostatni punkt;
  - błąd w jednym wierszu batcha nie przerywa całości;
  - nazwy plików nie zależą od długości rozszerzenia;
  - nazwy plików bez rozróżniania wielkości liter (jak na Windows) na każdym systemie.

Fizyka nie została zmieniona: normalizacja z równania 10 (Morard 2013), 4 iteracje Kaplowa,
χ² = ∫₀^rmin [F(r)+4πρr]² dr, Nelder-Mead (lmfit, 500 wywołań, tol 1e-4).
Program **nie** stosuje korekt na polaryzację, absorpcję ani rozpraszanie wielokrotne. Dane wejściowe
muszą być już poprawione.

---

## Test zgodności

```
python tests/test_against_original.py
```

Test pobiera z GitHuba **oryginalny** `equations.py` i liczy nim wyniki referencyjne
(skrypt `tests/make_reference.py`: normalizacja dla formatów 1–4, SofQ 0/1, QStep, χ², dopasowania,
pętle r_min i q_max). Potem liczy to samo nowym kodem w trybie zgodności i porównuje 43 wielkości
na pełnych tablicach. Trwa to ok. 2–3 min. Przy pierwszym uruchomieniu potrzebny jest internet, potem
oryginał jest w pamięci podręcznej (`tests/_original_equations.py`).

## Struktura

```
amorpheus_qt.py          uruchomienie GUI
amorpheus/physics.py     czynniki rozpraszania (xraylib), normalizacja, Kaplow, χ², CN, f. modyfikująca
amorpheus/data.py        parametry, Init.txt, wczytywanie plików, tabela batch
amorpheus/autodetect.py  odczyt parametrów z pliku danych (nagłówek, zakres, skład z nazwy, gęstość)
amorpheus/analysis.py    normalizacja, dopasowanie, pętle, mapa χ², batch (bez GUI, do użycia w skryptach)
amorpheus/export.py      zapis wyników
amorpheus/plots.py       wykresy
amorpheus/rps.py         usuwanie pików i wygładzanie
amorpheus/gui/           interfejs PyQt5
```

Przykład użycia bez GUI:

```python
from amorpheus.data import load_init
from amorpheus import analysis as an, export as ex
p = load_init("examples/Init.txt")
fit = an.fit_density(p)                       # rho, bkfactor, chi2
res = an.run_normalization(p, rho=fit.rho, bk=fit.bkfactor)
ex.save_normalization(res, "wyniki")
```

Licencja: GNU GPL v3 (jak oryginał, plik LICENSE).
