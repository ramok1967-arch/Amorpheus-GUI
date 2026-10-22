@echo off
chcp 65001 >nul
setlocal
set "CONDA_BAT="
if defined CONDA_EXE for %%I in ("%CONDA_EXE%") do if exist "%%~dpI..\condabin\conda.bat" set "CONDA_BAT=%%~dpI..\condabin\conda.bat"
if not defined CONDA_BAT if exist "C:\ProgramData\Miniconda3\condabin\conda.bat" set "CONDA_BAT=C:\ProgramData\Miniconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
if not defined CONDA_BAT if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
if defined CONDA_BAT call "%CONDA_BAT%" activate amorpheus
python "%~dp0amorpheus_qt.py" %*
if errorlevel 1 pause
