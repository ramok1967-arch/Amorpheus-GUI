@echo off
chcp 65001 >nul
rem Tworzy srodowisko conda "amorpheus" dla Amorpheus-Qt
setlocal
set "CONDA_BAT="
if defined CONDA_EXE for %%I in ("%CONDA_EXE%") do if exist "%%~dpI..\condabin\conda.bat" set "CONDA_BAT=%%~dpI..\condabin\conda.bat"
if not defined CONDA_BAT if exist "C:\ProgramData\Miniconda3\condabin\conda.bat" set "CONDA_BAT=C:\ProgramData\Miniconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
if not defined CONDA_BAT (echo Nie znaleziono conda. Zainstaluj Miniconda lub uzyj: pip install -r requirements.txt & pause & exit /b 1)
echo Uzywam: %CONDA_BAT%
call "%CONDA_BAT%" create -y -n amorpheus -c conda-forge python=3.11 numpy scipy matplotlib pyqt lmfit xraylib pandas odfpy openpyxl
if errorlevel 1 (echo. & echo BLAD instalacji. & pause & exit /b 1)
echo.
echo Test zgodnosci z oryginalem:
call "%CONDA_BAT%" activate amorpheus
python "%~dp0tests\test_against_original.py"
echo.
echo Gotowe. Uruchom program plikiem uruchom.bat
pause
